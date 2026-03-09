import os
import logging
import httpx

logger = logging.getLogger(__name__)

async def search_products_on_shopify(keywords: list[str]) -> dict:
    """
    Shopify Storefront API (GraphQL) を叩き、
    受け取ったキーワードに合致する「在庫あり」の商品を検索して返す
    """
    shopify_url = os.getenv("SHOPIFY_STORE_URL")
    access_token = os.getenv("SHOPIFY_STOREFRONT_ACCESS_TOKEN")

    if not shopify_url or not access_token:
        logger.warning("Shopify API credentials missing")
        return {"status": "error", "message": "Shopify credentials missing", "products": []}

    # Storefront APIのGraphQLエンドポイント
    endpoint = f"https://{shopify_url}/api/2026-01/graphql.json"

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Storefront-Access-Token": access_token
    }

    # キーワードをスペース結合（Storefront search はフルテキスト検索）
    query_string = " ".join(keywords)

    # GraphQLクエリ
    # NOTE: Storefront API の search では "AND available_for_sale:true" フィルタ構文は
    #       使用不可（0件になる）。代わりに availableForSale フィールドで取得後フィルタする。
    #       検索件数を多めに取得(10件)し、在庫ありのみを最大5件返す。
    graphql_query = """
    query SearchProducts($query: String!) {
      search(query: $query, first: 10, types: PRODUCT) {
        edges {
          node {
            ... on Product {
              id
              title
              description
              handle
              availableForSale
              priceRange {
                minVariantPrice {
                  amount
                  currencyCode
                }
              }
              compareAtPriceRange {
                minVariantPrice {
                  amount
                  currencyCode
                }
              }
              images(first: 2) {
                edges {
                  node {
                    url
                    altText
                  }
                }
              }
              onlineStoreUrl
            }
          }
        }
      }
    }
    """

    payload = {
        "query": graphql_query,
        "variables": {
            "query": query_string
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()

        edges = data.get("data", {}).get("search", {}).get("edges", [])

        products = []
        for edge in edges:
            node = edge.get("node")
            if not node or not node.get("availableForSale"):
                continue
            if len(products) >= 5:
                break

            # 画像URLの抽出（最大2枚）
            image_edges = node.get("images", {}).get("edges", [])
            image_url = image_edges[0].get("node", {}).get("url", "") if image_edges else ""
            images = [
                img.get("node", {}).get("url", "")
                for img in image_edges
                if img.get("node", {}).get("url")
            ]

            # 価格の抽出
            price_info = node.get("priceRange", {}).get("minVariantPrice", {})
            price = f"{price_info.get('amount')} {price_info.get('currencyCode')}"

            # 元値（セール判定用）
            compare_info = node.get("compareAtPriceRange", {}).get("minVariantPrice", {})
            compare_at_price = compare_info.get("amount", "0")

            # 説明文の切り詰め（100文字以下ならそのまま）
            desc = node.get("description", "")
            if len(desc) > 100:
                desc = desc[:100] + "..."

            products.append({
                "id": node.get("id"),
                "title": node.get("title"),
                "description": desc,
                "handle": node.get("handle", ""),
                "price": price,
                "compare_at_price": compare_at_price,
                "image_url": image_url,
                "images": images,
                "url": node.get("onlineStoreUrl", "")
            })

        return {"status": "success", "products": products}

    except Exception as e:
        logger.error(f"Shopify API error: {e}")
        return {"status": "error", "message": str(e), "products": []}
