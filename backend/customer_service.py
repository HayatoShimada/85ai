"""
Shopify Admin API (GraphQL) を使った顧客管理サービス
顧客の登録・検索・好みタグの保存を行う
"""

import os
import json
import logging
import httpx
from shopify_auth import token_manager

logger = logging.getLogger(__name__)


async def _get_admin_api_config():
    """Shopify Admin API の接続設定を取得（トークン自動更新対応）"""
    store_url = os.getenv("SHOPIFY_STORE_URL")
    admin_token = await token_manager.get_token()
    if not store_url or not admin_token:
        return None, None, None
    endpoint = f"https://{store_url}/admin/api/2026-01/graphql.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": admin_token,
    }
    return endpoint, headers, True


async def search_customer_by_email(email: str) -> dict | None:
    """
    メールアドレスで既存顧客を検索し、保存済みの好みタグを取得する
    """
    endpoint, headers, configured = await _get_admin_api_config()
    if not configured:
        logger.warning("Shopify Admin API credentials missing")
        return None

    query = """
    query SearchCustomer($query: String!) {
      customers(first: 1, query: $query) {
        edges {
          node {
            id
            firstName
            lastName
            email
            metafield(namespace: "custom", key: "style_preferences") {
              value
            }
          }
        }
      }
    }
    """

    payload = {
        "query": query,
        "variables": {"query": f"email:{email}"},
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()

        edges = data.get("data", {}).get("customers", {}).get("edges", [])
        if not edges:
            return None

        node = edges[0]["node"]
        metafield = node.get("metafield")
        preferences = json.loads(metafield["value"]) if metafield and metafield.get("value") else []

        return {
            "id": node["id"],
            "name": f"{node.get('firstName') or ''} {node.get('lastName') or ''}".strip(),
            "email": node["email"],
            "style_preferences": preferences,
        }
    except Exception as e:
        logger.error(f"Customer search error: {e}")
        return None


async def create_customer(name: str, email: str, preferences: list[str]) -> dict | None:
    """
    新規顧客を作成し、好みタグをメタフィールドに保存する
    """
    endpoint, headers, configured = await _get_admin_api_config()
    if not configured:
        logger.warning("Shopify Admin API credentials missing")
        return None

    # 名前をfirstName / lastNameに分割
    name_parts = name.split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    mutation = """
    mutation CreateCustomer($input: CustomerInput!) {
      customerCreate(input: $input) {
        customer {
          id
          firstName
          lastName
          email
        }
        userErrors {
          field
          message
        }
      }
    }
    """

    customer_input = {
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "metafields": [
            {
                "namespace": "custom",
                "key": "style_preferences",
                "type": "json",
                "value": json.dumps(preferences, ensure_ascii=False),
            }
        ],
    }

    payload = {
        "query": mutation,
        "variables": {"input": customer_input},
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()

        result = data.get("data", {}).get("customerCreate", {})
        errors = result.get("userErrors", [])
        if errors:
            logger.error(f"Customer creation errors: {errors}")
            return None

        customer = result.get("customer", {})
        return {
            "id": customer["id"],
            "name": f"{customer.get('firstName') or ''} {customer.get('lastName') or ''}".strip(),
            "email": customer["email"],
            "style_preferences": preferences,
            "is_new": True,
        }
    except Exception as e:
        logger.error(f"Customer creation error: {e}")
        return None


async def update_customer_preferences(customer_id: str, preferences: list[str]) -> dict | None:
    """
    既存顧客の好みタグを更新する
    """
    endpoint, headers, configured = await _get_admin_api_config()
    if not configured:
        logger.warning("Shopify Admin API credentials missing")
        return None

    mutation = """
    mutation UpdateCustomer($input: CustomerInput!) {
      customerUpdate(input: $input) {
        customer {
          id
          firstName
          lastName
          email
        }
        userErrors {
          field
          message
        }
      }
    }
    """

    customer_input = {
        "id": customer_id,
        "metafields": [
            {
                "namespace": "custom",
                "key": "style_preferences",
                "type": "json",
                "value": json.dumps(preferences, ensure_ascii=False),
            }
        ],
    }

    payload = {
        "query": mutation,
        "variables": {"input": customer_input},
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()

        result = data.get("data", {}).get("customerUpdate", {})
        errors = result.get("userErrors", [])
        if errors:
            logger.error(f"Customer update errors: {errors}")
            return None

        customer = result.get("customer", {})
        return {
            "id": customer["id"],
            "name": f"{customer.get('firstName') or ''} {customer.get('lastName') or ''}".strip(),
            "email": customer["email"],
            "style_preferences": preferences,
            "is_new": False,
        }
    except Exception as e:
        logger.error(f"Customer preference update error: {e}")
        return None
