"""
商品カタログキャッシュサービス

起動時に Shopify Admin API から全商品を取得し、2つの形式で保持する:
  1. Gemini 用のコンパクトなTSV文字列 (トークン最小化)
  2. フロントエンド用のフル商品データ (画像・価格・URL)

Gemini が返す short_id を使って直接商品を参照できるため、
Shopify 検索API呼び出しが不要になる。
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timezone
import httpx

from shopify_auth import token_manager

logger = logging.getLogger(__name__)

ADMIN_API_VERSION = "2026-01"
REFRESH_INTERVAL = 1800  # 30分


class ProductCatalogCache:
    def __init__(self):
        self._catalog_for_gemini: str = ""
        self._catalog_full: dict[int, dict] = {}
        self._product_count: int = 0
        self._loaded: bool = False
        self._last_refreshed: datetime | None = None
        self._lock = asyncio.Lock()
        self._refresh_task: asyncio.Task | None = None

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def product_count(self) -> int:
        return self._product_count

    @property
    def last_refreshed(self) -> datetime | None:
        return self._last_refreshed

    def get_gemini_catalog(self) -> str:
        """Gemini プロンプトに注入するコンパクトなカタログ文字列"""
        return self._catalog_for_gemini

    def get_products_by_ids(self, short_ids: list[int]) -> list[dict]:
        """short_id リストからフロントエンド用の商品データを返す"""
        products = []
        for sid in short_ids:
            product = self._catalog_full.get(sid)
            if product:
                products.append(product)
        return products

    async def load(self):
        """Admin API から全商品を取得してキャッシュを構築"""
        async with self._lock:
            try:
                raw_products = await self._fetch_all_products()
                if not raw_products:
                    logger.warning("No products fetched from Shopify")
                    return

                gemini_lines = ["ID\tType\tTitle\tAttributes"]
                full_map: dict[int, dict] = {}

                idx = 0
                for p in raw_products:
                    if p.get("status") != "ACTIVE":
                        continue

                    # Gemini 用コンパクト行
                    line = self._build_compact_line(idx, p)
                    gemini_lines.append(line)

                    # フロントエンド用フルデータ
                    full_map[idx] = self._build_full_product(idx, p)

                    idx += 1

                self._catalog_for_gemini = "\n".join(gemini_lines)
                self._catalog_full = full_map
                self._product_count = idx
                self._loaded = True
                self._last_refreshed = datetime.now(timezone.utc)

                logger.info(f"Product catalog loaded: {idx} products "
                            f"({len(self._catalog_for_gemini)} chars)")

            except Exception as e:
                logger.error(f"Failed to load product catalog: {e}")

    async def start_background_refresh(self):
        """定期的にカタログを更新するバックグラウンドタスクを開始"""
        async def _refresh_loop():
            while True:
                await asyncio.sleep(REFRESH_INTERVAL)
                logger.info("Refreshing product catalog...")
                await self.load()

        self._refresh_task = asyncio.create_task(_refresh_loop())

    def stop_background_refresh(self):
        if self._refresh_task:
            self._refresh_task.cancel()
            self._refresh_task = None

    async def _fetch_all_products(self) -> list[dict]:
        """Admin API でページネーションしながら全商品を取得"""
        token = await token_manager.get_token()
        if not token:
            logger.error("No Shopify Admin API token available")
            return []

        store_url = os.getenv("SHOPIFY_STORE_URL")
        if not store_url:
            logger.error("SHOPIFY_STORE_URL not set")
            return []

        endpoint = f"https://{store_url}/admin/api/{ADMIN_API_VERSION}/graphql.json"
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
                        handle
                        productType
                        tags
                        status
                        priceRange {{
                          minVariantPrice {{ amount currencyCode }}
                        }}
                        images(first: 2) {{
                          edges {{
                            node {{ url altText }}
                          }}
                        }}
                        onlineStoreUrl
                        brandMf: metafield(namespace: "custom", key: "brand") {{ value }}
                        styleMf: metafield(namespace: "custom", key: "style") {{ value }}
                        eraMf: metafield(namespace: "custom", key: "era") {{ value }}
                        featuresMf: metafield(namespace: "custom", key: "features") {{ value }}
                      }}
                    }}
                    pageInfo {{ hasNextPage endCursor }}
                  }}
                }}
                """
                resp = await client.post(endpoint, headers=headers,
                                         json={"query": query})
                resp.raise_for_status()
                data = resp.json()

                if "errors" in data:
                    logger.error(f"GraphQL errors: {data['errors']}")
                    break

                edges = data["data"]["products"]["edges"]
                products.extend([e["node"] for e in edges])

                page_info = data["data"]["products"]["pageInfo"]
                if not page_info["hasNextPage"]:
                    break
                cursor = page_info["endCursor"]

        return products

    @staticmethod
    def _build_compact_line(idx: int, product: dict) -> str:
        """1商品をTSV1行にまとめる (Gemini用, トークン最小化)"""
        ptype = product.get("productType", "")
        title = product["title"]

        # カスタムメタフィールドからキー属性を収集
        attrs = []

        brand = (product.get("brandMf") or {}).get("value", "")
        if brand:
            attrs.append(brand)

        era = (product.get("eraMf") or {}).get("value", "")
        if era:
            attrs.append(era)

        style_raw = (product.get("styleMf") or {}).get("value", "")
        if style_raw:
            try:
                styles = json.loads(style_raw)
                attrs.extend(styles)
            except (json.JSONDecodeError, TypeError):
                pass

        features_raw = (product.get("featuresMf") or {}).get("value", "")
        if features_raw:
            try:
                features = json.loads(features_raw)
                attrs.extend(features)
            except (json.JSONDecodeError, TypeError):
                pass

        # タグから素材・色をいくつか補完 (重複は許容、Geminiが理解できればOK)
        tags = product.get("tags", [])
        if isinstance(tags, list):
            for tag in tags:
                if tag not in ("USED", "NEW") and tag not in attrs:
                    attrs.append(tag)

        return f"{idx}\t{ptype}\t{title}\t{','.join(attrs)}"

    @staticmethod
    def _build_full_product(idx: int, product: dict) -> dict:
        """フロントエンド用のフル商品データを構築 (shopify_service互換)"""
        image_edges = product.get("images", {}).get("edges", [])
        image_url = (image_edges[0].get("node", {}).get("url", "")
                     if image_edges else "")
        images = [
            img.get("node", {}).get("url", "")
            for img in image_edges
            if img.get("node", {}).get("url")
        ]

        price_info = product.get("priceRange", {}).get("minVariantPrice", {})
        price = f"{price_info.get('amount', '0')} {price_info.get('currencyCode', 'JPY')}"

        compare_at_price = "0"

        desc = product.get("description", "")
        if len(desc) > 100:
            desc = desc[:100] + "..."

        store_url = os.getenv("SHOPIFY_STORE_URL", "")
        handle = product.get("handle", "")
        online_url = product.get("onlineStoreUrl") or ""
        if not online_url and handle and store_url:
            online_url = f"https://{store_url}/products/{handle}"

        return {
            "id": product.get("id"),
            "title": product.get("title"),
            "description": desc,
            "handle": handle,
            "price": price,
            "compare_at_price": compare_at_price,
            "image_url": image_url,
            "images": images,
            "url": online_url,
        }


# シングルトン
catalog_cache = ProductCatalogCache()
