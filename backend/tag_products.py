"""
Shopify商品の自動タグ付けスクリプト

Admin API で全商品を取得し、Gemini に画像+説明文を送って
productType と tags を自動生成・更新する。

使い方:
  # ドライラン (変更を表示するだけ)
  python tag_products.py

  # 実際に更新
  python tag_products.py --apply

  # 特定商品だけ (商品ID指定)
  python tag_products.py --apply --id gid://shopify/Product/8115713736819

  # 既にタグ済み(USEDのみでない)の商品もやり直す
  python tag_products.py --apply --force
"""

import os
import sys
import json
import time
import argparse
import io
import httpx
from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# --- 設定 ---
ADMIN_API_VERSION = "2026-01"
GEMINI_MODEL = "gemini-2.5-flash"
RATE_LIMIT_DELAY = 2  # Gemini API 間隔 (秒)


# --- Gemini スキーマ ---
class ProductTags(BaseModel):
    product_type: str = Field(description="商品カテゴリ (例: シャツ, ジャケット, ニット, パンツ, ベスト, コート)")
    category_tags: list[str] = Field(description="カテゴリタグ (例: シャツ, 長袖シャツ, ボタンダウンシャツ)")
    material_tags: list[str] = Field(description="素材タグ (例: コットン, フランネル, ナイロン, ウール, リネン, フリース)")
    style_tags: list[str] = Field(description="スタイルタグ (例: カジュアル, ワーク, ミリタリー, アウトドア, ドレス, ストリート, クラシック)")
    color_tags: list[str] = Field(description="色タグ (例: ブルー, ネイビー, ブラック, チェック柄, ストライプ)")
    brand: str = Field(description="ブランド名 (不明なら空文字)")
    era_tags: list[str] = Field(description="年代・時代タグ (例: 90s, ヴィンテージ, ミリタリーサープラス)")
    feature_tags: list[str] = Field(description="特徴タグ (例: オーバーサイズ, ヘビーウェイト, ゴアテックス, 裏起毛)")
    size_info: str = Field(description="サイズ情報 (例: L, XL, フリーサイズ。説明文から判読)")


# --- Shopify Admin API ---
def get_shopify_config():
    url = os.getenv("SHOPIFY_STORE_URL")
    token = os.getenv("SHOPIFY_ADMIN_API_ACCESS_TOKEN")
    if not url or not token:
        print("ERROR: SHOPIFY_STORE_URL / SHOPIFY_ADMIN_API_ACCESS_TOKEN が未設定")
        sys.exit(1)
    return (
        f"https://{url}/admin/api/{ADMIN_API_VERSION}/graphql.json",
        {"Content-Type": "application/json", "X-Shopify-Access-Token": token},
    )


def fetch_all_products(endpoint, headers):
    """ページネーションで全商品を取得"""
    products = []
    cursor = None

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
                handle
                productType
                tags
                status
                variants(first: 10) {{
                  edges {{
                    node {{
                      title
                      price
                      selectedOptions {{ name value }}
                    }}
                  }}
                }}
                images(first: 5) {{
                  edges {{
                    node {{
                      url
                      width
                      height
                    }}
                  }}
                }}
              }}
            }}
            pageInfo {{ hasNextPage endCursor }}
          }}
        }}
        """
        with httpx.Client(timeout=30) as client:
            r = client.post(endpoint, headers=headers, json={"query": query})
        r.raise_for_status()
        data = r.json()

        if "errors" in data:
            print(f"GraphQL errors: {data['errors']}")
            break

        edges = data["data"]["products"]["edges"]
        products.extend([e["node"] for e in edges])

        page_info = data["data"]["products"]["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]

    return products


def update_product_tags(endpoint, headers, product_id, product_type, tags):
    """商品のproductTypeとtagsを更新"""
    mutation = """
    mutation UpdateProduct($input: ProductInput!) {
      productUpdate(input: $input) {
        product { id title productType tags }
        userErrors { field message }
      }
    }
    """
    payload = {
        "query": mutation,
        "variables": {
            "input": {
                "id": product_id,
                "productType": product_type,
                "tags": tags,
            }
        },
    }
    with httpx.Client(timeout=15) as client:
        r = client.post(endpoint, headers=headers, json=payload)
    r.raise_for_status()
    data = r.json()

    errors = data.get("data", {}).get("productUpdate", {}).get("userErrors", [])
    if errors:
        print(f"  ❌ 更新エラー: {errors}")
        return False
    return True


# --- Gemini 解析 ---
def analyze_product_with_gemini(client, product):
    """商品情報をGeminiに送ってタグを生成"""
    title = product["title"]
    description = product["description"] or ""
    variants = product["variants"]["edges"]
    variant_info = ""
    for v in variants:
        vn = v["node"]
        opts = ", ".join([f'{o["name"]}:{o["value"]}' for o in vn["selectedOptions"]])
        variant_info += f"  {vn['title']} (¥{vn['price']}) [{opts}]\n"

    # 画像をダウンロード (最大2枚、リサイズして軽量化)
    images = []
    image_edges = product["images"]["edges"]
    for img_edge in image_edges[:2]:
        img_url = img_edge["node"]["url"]
        try:
            with httpx.Client(timeout=15) as http:
                resp = http.get(img_url)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content))
            img.thumbnail((800, 800))
            images.append(img)
        except Exception as e:
            print(f"  ⚠ 画像取得失敗: {e}")

    prompt = f"""以下の古着商品の情報を分析し、Shopify検索用のタグを日本語と英語の両方で生成してください。

【商品名】
{title}

【説明文】
{description}

【バリエーション】
{variant_info}

タグの生成ルール:
- カテゴリ: 商品の種類 (シャツ, ジャケット, ニット, パンツ, ベスト, コート 等)
- 素材: 説明文や画像から判断 (コットン, フランネル, ウール, ナイロン, リネン 等)
- スタイル: 服のスタイル (カジュアル, ワーク, ミリタリー, アウトドア, ドレス 等)
- 色・柄: 画像と説明文から判断 (ブルー, チェック柄, 無地 等)
- ブランド: 商品名や説明文から判別
- 年代: 古着の年代感 (90s, ヴィンテージ 等)
- 特徴: 特筆すべき特徴 (オーバーサイズ, ヘビーウェイト, ゴアテックス 等)
- サイズ: 説明文からサイズ情報を読み取る

product_type には日本語のメインカテゴリを1つだけ入れてください。
タグは日本語を基本とし、ブランド名や素材名は英語も含めてください。
"""

    contents = [prompt] + images

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ProductTags,
            ),
        )
        return ProductTags.model_validate_json(response.text)
    except Exception as e:
        print(f"  ❌ Gemini エラー: {e}")
        return None


# --- メイン ---
def main():
    parser = argparse.ArgumentParser(description="Shopify商品の自動タグ付け")
    parser.add_argument("--apply", action="store_true", help="実際にShopifyを更新する (省略時はドライラン)")
    parser.add_argument("--id", type=str, help="特定の商品IDだけ処理する")
    parser.add_argument("--force", action="store_true", help="既にタグ済みの商品も再処理する")
    args = parser.parse_args()

    # Gemini 初期化
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY が未設定")
        sys.exit(1)
    gemini_client = genai.Client(api_key=api_key)

    # Shopify 設定
    endpoint, headers = get_shopify_config()

    # 商品取得
    print("📦 商品を取得中...")
    products = fetch_all_products(endpoint, headers)
    print(f"   {len(products)}件の商品を取得\n")

    # フィルタ
    if args.id:
        products = [p for p in products if p["id"] == args.id]
        if not products:
            print(f"ERROR: 商品 {args.id} が見つかりません")
            sys.exit(1)

    if not args.force:
        # tags が ['USED'] のみ or 空 の商品だけ処理
        products = [p for p in products if set(p["tags"]) <= {"USED"}]
        print(f"   タグ未設定の商品: {len(products)}件\n")

    if not products:
        print("✅ 処理対象の商品がありません")
        return

    mode = "🔧 更新モード" if args.apply else "👀 ドライラン (--apply で実際に更新)"
    print(f"   {mode}\n")
    print("=" * 70)

    success = 0
    errors = 0

    for i, product in enumerate(products):
        title = product["title"]
        print(f"\n[{i+1}/{len(products)}] {title}")
        print(f"  現在: type='{product['productType']}' tags={product['tags']}")

        # Gemini 解析
        result = analyze_product_with_gemini(gemini_client, product)
        if not result:
            errors += 1
            continue

        # タグをフラットに結合 (USED は常に保持)
        all_tags = ["USED"]
        all_tags.extend(result.category_tags)
        all_tags.extend(result.material_tags)
        all_tags.extend(result.style_tags)
        all_tags.extend(result.color_tags)
        all_tags.extend(result.era_tags)
        all_tags.extend(result.feature_tags)
        if result.brand:
            all_tags.append(result.brand)
        if result.size_info:
            all_tags.append(result.size_info)
        # 重複排除 (順序保持)
        seen = set()
        unique_tags = []
        for tag in all_tags:
            tag_lower = tag.lower()
            if tag_lower not in seen:
                seen.add(tag_lower)
                unique_tags.append(tag)

        print(f"  → productType: '{result.product_type}'")
        print(f"  → tags ({len(unique_tags)}): {unique_tags}")
        print(f"  → brand: '{result.brand}' / size: '{result.size_info}'")

        if args.apply:
            ok = update_product_tags(endpoint, headers, product["id"], result.product_type, unique_tags)
            if ok:
                print(f"  ✅ 更新完了")
                success += 1
            else:
                errors += 1
        else:
            success += 1

        # Gemini レート制限対策
        if i < len(products) - 1:
            time.sleep(RATE_LIMIT_DELAY)

    print("\n" + "=" * 70)
    print(f"完了: {success}件成功, {errors}件エラー")
    if not args.apply:
        print("→ 実際に更新するには --apply オプションを付けてください")


if __name__ == "__main__":
    main()
