"""customer_service のユニットテスト（パッチで Shopify API をモック）"""

import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


def test_search_customer_missing_credentials():
    """Admin API 未設定で None が返る"""
    import asyncio
    env = {
        "SHOPIFY_STORE_URL": "",
        "SHOPIFY_ADMIN_API_ACCESS_TOKEN": "",
        "SHOPIFY_CLIENT_ID": "",
        "SHOPIFY_CLIENT_SECRET": "",
    }
    with patch.dict("os.environ", env, clear=False):
        from customer_service import search_customer_by_email
        result = asyncio.get_event_loop().run_until_complete(
            search_customer_by_email("test@example.com")
        )
    assert result is None


@pytest.mark.asyncio
async def test_search_customer_success():
    """正常な GraphQL レスポンスをパースできる"""
    mock_graphql_response = {
        "data": {
            "customers": {
                "edges": [
                    {
                        "node": {
                            "id": "gid://shopify/Customer/123",
                            "firstName": "太郎",
                            "lastName": "テスト",
                            "email": "test@example.com",
                            "metafield": {
                                "value": json.dumps(["ストリート", "90s"]),
                            },
                        }
                    }
                ]
            }
        }
    }

    mock_response = MagicMock()
    mock_response.json.return_value = mock_graphql_response
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("customer_service.token_manager") as mock_tm:
        mock_tm.get_token = AsyncMock(return_value="shpat_test")
        with patch.dict("os.environ", {"SHOPIFY_STORE_URL": "test.myshopify.com"}):
            with patch("customer_service.httpx.AsyncClient", return_value=mock_client):
                from customer_service import search_customer_by_email
                result = await search_customer_by_email("test@example.com")

    assert result is not None
    assert result["id"] == "gid://shopify/Customer/123"
    assert result["name"] == "太郎 テスト"
    assert result["style_preferences"] == ["ストリート", "90s"]


@pytest.mark.asyncio
async def test_create_customer_with_user_errors():
    """Shopify userErrors 時に None が返る"""
    mock_graphql_response = {
        "data": {
            "customerCreate": {
                "customer": None,
                "userErrors": [{"field": ["email"], "message": "Email has already been taken"}],
            }
        }
    }

    mock_response = MagicMock()
    mock_response.json.return_value = mock_graphql_response
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("customer_service.token_manager") as mock_tm:
        mock_tm.get_token = AsyncMock(return_value="shpat_test")
        with patch.dict("os.environ", {"SHOPIFY_STORE_URL": "test.myshopify.com"}):
            with patch("customer_service.httpx.AsyncClient", return_value=mock_client):
                from customer_service import create_customer
                result = await create_customer("テスト太郎", "test@example.com", ["カジュアル"])

    assert result is None


@pytest.mark.asyncio
async def test_create_customer_name_split():
    """「田中 太郎」が firstName/lastName に正しく分割される"""
    mock_graphql_response = {
        "data": {
            "customerCreate": {
                "customer": {
                    "id": "gid://shopify/Customer/456",
                    "firstName": "田中",
                    "lastName": "太郎",
                    "email": "tanaka@example.com",
                },
                "userErrors": [],
            }
        }
    }

    mock_response = MagicMock()
    mock_response.json.return_value = mock_graphql_response
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("customer_service.token_manager") as mock_tm:
        mock_tm.get_token = AsyncMock(return_value="shpat_test")
        with patch.dict("os.environ", {"SHOPIFY_STORE_URL": "test.myshopify.com"}):
            with patch("customer_service.httpx.AsyncClient", return_value=mock_client) as mock_cls:
                from customer_service import create_customer
                result = await create_customer("田中 太郎", "tanaka@example.com", [])

    # API に送信された input を検証
    call_payload = mock_client.post.call_args[1]["json"]
    input_data = call_payload["variables"]["input"]
    assert input_data["firstName"] == "田中"
    assert input_data["lastName"] == "太郎"
    assert result["name"] == "田中 太郎"


@pytest.mark.asyncio
async def test_update_preferences_metafield_value():
    """メタフィールド更新で正しい JSON が送信される"""
    mock_graphql_response = {
        "data": {
            "customerUpdate": {
                "customer": {
                    "id": "gid://shopify/Customer/789",
                    "firstName": "テスト",
                    "lastName": None,
                    "email": "test@example.com",
                },
                "userErrors": [],
            }
        }
    }

    mock_response = MagicMock()
    mock_response.json.return_value = mock_graphql_response
    mock_response.raise_for_status = MagicMock()

    prefs = ["ストリート", "90s", "かっこいい"]

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("customer_service.token_manager") as mock_tm:
        mock_tm.get_token = AsyncMock(return_value="shpat_test")
        with patch.dict("os.environ", {"SHOPIFY_STORE_URL": "test.myshopify.com"}):
            with patch("customer_service.httpx.AsyncClient", return_value=mock_client):
                from customer_service import update_customer_preferences
                result = await update_customer_preferences("gid://shopify/Customer/789", prefs)

    call_payload = mock_client.post.call_args[1]["json"]
    metafield = call_payload["variables"]["input"]["metafields"][0]
    assert metafield["namespace"] == "custom"
    assert metafield["key"] == "style_preferences"
    assert json.loads(metafield["value"]) == prefs
    assert result["style_preferences"] == prefs
    assert result["is_new"] is False
