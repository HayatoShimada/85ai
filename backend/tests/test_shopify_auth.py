"""ShopifyTokenManager のテスト"""

import time
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


def _fresh_manager():
    """テストごとに新しい ShopifyTokenManager を生成"""
    from shopify_auth import ShopifyTokenManager
    return ShopifyTokenManager()


@pytest.mark.asyncio
async def test_static_token_fallback():
    """Client ID/Secret 未設定時に shpat_ 静的トークンにフォールバック"""
    mgr = _fresh_manager()
    env = {
        "SHOPIFY_STORE_URL": "",
        "SHOPIFY_CLIENT_ID": "",
        "SHOPIFY_CLIENT_SECRET": "",
        "SHOPIFY_ADMIN_API_ACCESS_TOKEN": "shpat_test_static_token",
    }
    with patch.dict("os.environ", env, clear=False):
        token = await mgr.get_token()
    assert token == "shpat_test_static_token"


@pytest.mark.asyncio
async def test_static_token_rejects_non_shpat():
    """shpat_ で始まらないトークンは静的フォールバックで拒否"""
    mgr = _fresh_manager()
    env = {
        "SHOPIFY_STORE_URL": "",
        "SHOPIFY_CLIENT_ID": "",
        "SHOPIFY_CLIENT_SECRET": "",
        "SHOPIFY_ADMIN_API_ACCESS_TOKEN": "invalid_token",
    }
    with patch.dict("os.environ", env, clear=False):
        token = await mgr.get_token()
    assert token is None


@pytest.mark.asyncio
async def test_token_refresh_success():
    """Client Credentials Grant 成功時にトークンが更新される"""
    mgr = _fresh_manager()
    env = {
        "SHOPIFY_STORE_URL": "test.myshopify.com",
        "SHOPIFY_CLIENT_ID": "client_id",
        "SHOPIFY_CLIENT_SECRET": "client_secret",
    }
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "access_token": "shpat_new_token",
        "expires_in": 86399,
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch.dict("os.environ", env, clear=False):
        with patch("shopify_auth.httpx.AsyncClient", return_value=mock_client):
            token = await mgr.get_token()
    assert token == "shpat_new_token"


@pytest.mark.asyncio
async def test_token_cached_within_expiry():
    """期限内はキャッシュされたトークンを返す"""
    mgr = _fresh_manager()
    mgr._token = "shpat_cached"
    mgr._expires_at = time.time() + 3600  # 1時間後
    token = await mgr.get_token()
    assert token == "shpat_cached"


@pytest.mark.asyncio
async def test_token_refresh_near_expiry():
    """期限5分以内のトークンはリフレッシュが発火する"""
    mgr = _fresh_manager()
    mgr._token = "shpat_old"
    mgr._expires_at = time.time() + 200  # 5分(300秒)未満

    env = {
        "SHOPIFY_STORE_URL": "test.myshopify.com",
        "SHOPIFY_CLIENT_ID": "client_id",
        "SHOPIFY_CLIENT_SECRET": "client_secret",
    }
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "access_token": "shpat_refreshed",
        "expires_in": 86399,
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch.dict("os.environ", env, clear=False):
        with patch("shopify_auth.httpx.AsyncClient", return_value=mock_client):
            token = await mgr.get_token()
    assert token == "shpat_refreshed"
