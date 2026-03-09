import os
import requests
import json

def search_products_on_shopify(keywords: list[str]) -> dict:
    """
    Shopify Storefront API (GraphQL) を叩き、
    受け取ったキーワードに合致する「在庫あり」の商品を検索して返す
    """
    shopify_url = os.getenv("SHOPIFY_STORE_URL")
    access_token = os.getenv("SHOPIFY_STOREFRONT_ACCESS_TOKEN")

    if not shopify_url or not access_token:
        print("Shopify API credentials missing.")
        return {"status": "error", "message": "Shopify credentials missing", "products": []}

    # Storefront APIのGraphQLエンドポイント
    endpoint = f"https://{shopify_url}/api/2026-01/graphql.json"
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Storefront-Access-Token": access_token
    }

    # キーワードをAND検索またはOR検索用のクエリ文字列に変換
    # 今回は簡易的に、全キーワードを含む商品を探すイメージ（実運用では調整が必要）
    query_string = " ".join(keywords)

    # GraphQLクエリ: 在庫がある (availableForSale: true) 商品を検索
    graphql_query = """
    query SearchProducts($query: String!) {
      search(query: $query, first: 5, types: PRODUCT) {
        edges {
          node {
            ... on Product {
              id
              title
              description
              availableForSale
              priceRange {
                minVariantPrice {
                  amount
                  currencyCode
                }
              }
              images(first: 1) {
                edges {
                  node {
                    url
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
    
    # query_stringに "available_for_sale:true" などのフィルタを結合することで
    # 確実な絞り込みが可能。ここでは一旦クエリとして渡す。
    search_query = f"{query_string} AND available_for_sale:true"
    
    payload = {
        "query": graphql_query,
        "variables": {
            "query": search_query
        }
    }

    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        edges = data.get("data", {}).get("search", {}).get("edges", [])
        
        products = []
        for edge in edges:
            node = edge.get("node")
            if node and node.get("availableForSale"):
                # 画像URLの抽出
                image_edges = node.get("images", {}).get("edges", [])
                image_url = image_edges[0].get("node", {}).get("url") if image_edges else ""
                
                # 価格の抽出
                price_info = node.get("priceRange", {}).get("minVariantPrice", {})
                price = f"{price_info.get('amount')} {price_info.get('currencyCode')}"
                
                products.append({
                    "id": node.get("id"),
                    "title": node.get("title"),
                    "description": node.get("description", "")[:100] + "...",
                    "price": price,
                    "image_url": image_url,
                    "url": node.get("onlineStoreUrl", "")
                })
                
        return {"status": "success", "products": products}

    except Exception as e:
        print(f"Error querying Shopify API: {e}")
        return {"status": "error", "message": str(e), "products": []}
