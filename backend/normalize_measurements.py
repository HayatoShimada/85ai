"""
商品説明文から採寸データを抽出し、Shopifyメタフィールドに正規化保存するスクリプト。

使い方:
  python3 normalize_measurements.py             # ドライラン（変更なし、抽出結果を表示）
  python3 normalize_measurements.py --apply      # 実際にShopifyメタフィールドを更新

メタフィールド: custom:measurements (JSON)
保存形式:
  トップス: {"肩幅": 49, "身幅": 63, "袖丈": 62, "着丈": 82}
  ボトムス: {"ウエスト": 82, "股下": 78.5, "もも周り": 35, "裾周り": 22, "股上": 34}
  複数サイズ: {"sizes": {"S": {"ウエスト": 56, ...}, "M": {"ウエスト": 62, ...}}}
"""

import asyncio
import os
import re
import json
import logging
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

from shopify_auth import token_manager

ADMIN_API_VERSION = "2026-01"

# --- 採寸キーワード ---
# トップス系
TOP_KEYS = ["肩幅", "身幅", "袖丈", "着丈"]
# ボトムス系
BOTTOM_KEYS = ["ウエスト", "股上", "股下", "ワタリ", "わたり", "もも周り", "裾周り", "裾幅", "総丈"]
# 全キーワード
ALL_KEYS = TOP_KEYS + BOTTOM_KEYS


def extract_measurements_simple(description: str) -> dict | None:
    """
    トップス系・ボトムス(古着)系のシンプルなフォーマットから採寸を抽出。
    例: "肩幅49cm - 身幅63cm - 袖丈62cm - 着丈82cm"
    例: "ウエスト 82cm- 股下 78.5cm- もも周り 35cm"
    """
    result = {}
    for key in ALL_KEYS:
        # "肩幅49cm" or "肩幅 49cm" or "肩幅:49cm" or "肩幅 約68cm" or "肩幅 約 68cm"
        pattern = rf'{key}\s*[:：]?\s*約?\s*(\d+\.?\d*)\s*cm'
        m = re.search(pattern, description)
        if m:
            val = float(m.group(1))
            # 異常値チェック (200cm超は誤記の可能性)
            if val > 200:
                continue
            # 整数なら int にする
            result[key] = int(val) if val == int(val) else val
    return result if result else None


def extract_measurements_table(description: str) -> dict | None:
    """
    自社ブランドのテーブル形式から採寸を抽出。
    例: "ウエスト 股上 股下 ワタリ 裾幅 総丈 size1(S) 56cm～ 44cm 52cm 36cm 21cm 91cm
         size2(M) 62cm～ 47cm 55cm 38cm 23cm 96cm"
    """
    # ヘッダー行を探す (ウエスト 股上 股下 ... が連続)
    header_pattern = r'(ウエスト)\s+(股上)\s+(股下)\s+(ワタリ)\s+(裾幅)\s+((?:総丈|着丈[前後]?))'
    header_match = re.search(header_pattern, description)
    if not header_match:
        # 着丈前/着丈後 のパターンも試す
        header_pattern2 = r'(ウエスト)\s+(股上)\s+(股下)\s+(ワタリ)\s+(裾幅)\s+(着丈前)\s+(着丈後)'
        header_match = re.search(header_pattern2, description)
        if not header_match:
            return None

    headers = [g for g in header_match.groups()]
    after_header = description[header_match.end():]

    # サイズ行を抽出: "size1(S) 56cm～ 44cm 52cm 36cm 21cm 91cm"
    size_pattern = r'size\d*\((\w+)\)\s*'
    sizes = {}

    for size_match in re.finditer(size_pattern, after_header):
        size_label = size_match.group(1)
        remaining = after_header[size_match.end():]

        # 数値を抽出 (cm付き or ～付き)
        values = []
        for num_match in re.finditer(r'(\d+\.?\d*)\s*cm[～~]?', remaining):
            val = float(num_match.group(1))
            values.append(int(val) if val == int(val) else val)
            if len(values) >= len(headers):
                break

        if values:
            size_data = {}
            for i, v in enumerate(values):
                if i < len(headers):
                    size_data[headers[i]] = v
            sizes[size_label] = size_data

    if not sizes:
        return None

    # 単一サイズならフラットに、複数サイズなら sizes キーで
    if len(sizes) == 1:
        return list(sizes.values())[0]
    return {"sizes": sizes}


def extract_measurements(description: str) -> dict | None:
    """商品説明文から採寸データを抽出する統合関数"""
    if not description:
        return None

    # まずテーブル形式を試す
    result = extract_measurements_table(description)
    if result:
        return result

    # シンプル形式を試す
    result = extract_measurements_simple(description)
    return result


def measurements_to_compact(measurements: dict) -> str:
    """
    採寸データをカタログTSV用のコンパクト文字列に変換。
    例: "肩幅49,身幅63,袖丈62,着丈82"
    複数サイズ: "S:ウエスト56/股下52 M:ウエスト62/股下55"
    """
    if "sizes" in measurements:
        parts = []
        for size_label, data in measurements["sizes"].items():
            items = [f"{k}{v}" for k, v in data.items()]
            parts.append(f"{size_label}:{'/'.join(items)}")
        return " ".join(parts)
    else:
        return ",".join(f"{k}{v}" for k, v in measurements.items())


async def fetch_all_products() -> list[dict]:
    """Admin API で全商品を取得"""
    token = await token_manager.get_token()
    store = os.getenv("SHOPIFY_STORE_URL")
    endpoint = f"https://{store}/admin/api/{ADMIN_API_VERSION}/graphql.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": token,
    }

    products = []
    cursor = None
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            after = f', after: "{cursor}"' if cursor else ""
            query = f"""
            {{
              products(first: 50{after}) {{
                edges {{
                  node {{
                    id
                    title
                    description
                    status
                    measurementsMf: metafield(namespace: "custom", key: "measurements") {{ id value }}
                  }}
                }}
                pageInfo {{ hasNextPage endCursor }}
              }}
            }}
            """
            resp = await client.post(endpoint, headers=headers, json={"query": query})
            resp.raise_for_status()
            data = resp.json()
            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                break
            edges = data["data"]["products"]["edges"]
            products.extend([e["node"] for e in edges])
            pi = data["data"]["products"]["pageInfo"]
            if not pi["hasNextPage"]:
                break
            cursor = pi["endCursor"]

    return products


async def save_metafield(product_id: str, measurements: dict):
    """Shopify Admin API でメタフィールドを保存"""
    token = await token_manager.get_token()
    store = os.getenv("SHOPIFY_STORE_URL")
    endpoint = f"https://{store}/admin/api/{ADMIN_API_VERSION}/graphql.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": token,
    }

    mutation = """
    mutation metafieldsSet($metafields: [MetafieldsSetInput!]!) {
      metafieldsSet(metafields: $metafields) {
        metafields { id }
        userErrors { field message }
      }
    }
    """

    variables = {
        "metafields": [{
            "ownerId": product_id,
            "namespace": "custom",
            "key": "measurements",
            "type": "json",
            "value": json.dumps(measurements, ensure_ascii=False),
        }]
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(endpoint, headers=headers,
                                 json={"query": mutation, "variables": variables})
        resp.raise_for_status()
        data = resp.json()
        errors = data.get("data", {}).get("metafieldsSet", {}).get("userErrors", [])
        if errors:
            logger.error(f"  Metafield errors: {errors}")
            return False
        return True


async def main():
    apply = "--apply" in sys.argv

    logger.info("=" * 60)
    logger.info("商品採寸データ正規化スクリプト")
    logger.info(f"モード: {'適用 (Shopifyに書き込み)' if apply else 'ドライラン (確認のみ)'}")
    logger.info("=" * 60)

    products = await fetch_all_products()
    active = [p for p in products if p["status"] == "ACTIVE"]
    logger.info(f"\n全商品: {len(products)}件, ACTIVE: {len(active)}件\n")

    extracted = 0
    skipped_existing = 0
    failed = 0
    no_data = 0
    saved = 0

    for p in active:
        title = p["title"][:60]
        desc = p["description"] or ""
        existing_mf = p.get("measurementsMf")

        measurements = extract_measurements(desc)

        if not measurements:
            no_data += 1
            logger.info(f"  ✗ {title} → 採寸データなし")
            continue

        # 既にメタフィールドがあるか確認
        if existing_mf and existing_mf.get("value"):
            try:
                existing = json.loads(existing_mf["value"])
                if existing == measurements:
                    skipped_existing += 1
                    continue
            except (json.JSONDecodeError, TypeError):
                pass

        extracted += 1
        compact = measurements_to_compact(measurements)
        logger.info(f"  ✓ {title}")
        logger.info(f"    → {compact}")

        if apply:
            ok = await save_metafield(p["id"], measurements)
            if ok:
                saved += 1
            else:
                failed += 1

    logger.info(f"\n{'=' * 60}")
    logger.info(f"結果:")
    logger.info(f"  抽出成功: {extracted}件")
    logger.info(f"  既存スキップ: {skipped_existing}件")
    logger.info(f"  採寸なし: {no_data}件")
    if apply:
        logger.info(f"  保存成功: {saved}件")
        logger.info(f"  保存失敗: {failed}件")
    else:
        logger.info(f"\n  ※ --apply を付けて実行するとShopifyに書き込みます")


if __name__ == "__main__":
    asyncio.run(main())
