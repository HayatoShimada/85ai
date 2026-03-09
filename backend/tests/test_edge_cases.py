"""エッジケーステスト"""

import io
import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import ASGITransport, AsyncClient
from starlette.testclient import TestClient

from main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_large_image_handling(client):
    """大画像 (1MB級) でも正常にハンドリングされる"""
    from PIL import Image
    img = Image.new("RGB", (3000, 3000), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    res = await client.post(
        "/api/analyze",
        files={"file": ("large.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"


@pytest.mark.asyncio
async def test_non_image_file(client):
    """非画像ファイル送信でもクラッシュしない"""
    fake_data = b"This is not an image file at all"
    res = await client.post(
        "/api/analyze",
        files={"file": ("test.txt", fake_data, "text/plain")},
    )
    # モックモードでは画像を実際に解析しないため成功する
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_invalid_email_customer_lookup(client):
    """不正メールアドレスでもクラッシュしない"""
    res = await client.get("/api/customers", params={"email": "not-an-email"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "not_found"


@pytest.mark.asyncio
async def test_single_char_name_customer_create(client):
    """1文字名前での顧客登録が成功する"""
    res = await client.post(
        "/api/customers",
        data={"name": "A", "email": "a@test.com", "style_preferences": "[]"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["customer"]["name"] == "A"


def test_multiple_display_connections():
    """複数 display が同時接続できる"""
    from services.projection_manager import projection_mgr
    projection_mgr.displays.clear()
    projection_mgr._current_state = None

    sync_client = TestClient(app)
    with sync_client.websocket_connect("/ws/projection/display") as d1:
        with sync_client.websocket_connect("/ws/projection/display") as d2:
            assert len(projection_mgr.displays) == 2

            # 両方に STATE_CHANGE がブロードキャストされる
            with sync_client.websocket_connect("/ws/projection/control") as ctrl:
                ctrl.send_json({"type": "STATE_CHANGE", "state": "IDLE"})

            msg1 = d1.receive_json()
            msg2 = d2.receive_json()
            assert msg1["state"] == "IDLE"
            assert msg2["state"] == "IDLE"

    projection_mgr.displays.clear()


@pytest.mark.asyncio
async def test_shopify_empty_response():
    """Shopify が空の検索結果を返した場合"""
    import os
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": {"search": {"edges": []}}}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch.dict(os.environ, {
        "SHOPIFY_STORE_URL": "test.myshopify.com",
        "SHOPIFY_STOREFRONT_ACCESS_TOKEN": "test-token",
    }):
        with patch("shopify_service.httpx.AsyncClient", return_value=mock_client):
            from shopify_service import search_products_on_shopify
            result = await search_products_on_shopify(["存在しない商品"])

    assert result["status"] == "success"
    assert result["products"] == []


@pytest.mark.asyncio
async def test_gemini_non_json_response(client):
    """Gemini が非 JSON レスポンスを返した場合"""
    import os

    with patch.dict(os.environ, {"MOCK_MODE": "false"}):
        with patch(
            "routers.analyze.analyze_image_and_get_tags",
            return_value="This is not valid JSON",
        ):
            from PIL import Image
            img = Image.new("RGB", (100, 100), color="blue")
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            buf.seek(0)

            res = await client.post(
                "/api/analyze",
                files={"file": ("test.jpg", buf.getvalue(), "image/jpeg")},
            )
            data = res.json()
            assert data["status"] == "error"
            assert "読み取りに失敗" in data["message"]


@pytest.mark.asyncio
async def test_description_truncation_short_text():
    """短い説明文に ... が付かない (L-01修正の確認)"""
    import os
    mock_response_data = {
        "data": {
            "search": {
                "edges": [
                    {
                        "node": {
                            "id": "gid://shopify/Product/1",
                            "title": "短い商品",
                            "description": "短い説明",
                            "availableForSale": True,
                            "priceRange": {"minVariantPrice": {"amount": "1000", "currencyCode": "JPY"}},
                            "images": {"edges": []},
                            "onlineStoreUrl": "",
                        }
                    }
                ]
            }
        }
    }

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch.dict(os.environ, {
        "SHOPIFY_STORE_URL": "test.myshopify.com",
        "SHOPIFY_STOREFRONT_ACCESS_TOKEN": "test-token",
    }):
        with patch("shopify_service.httpx.AsyncClient", return_value=mock_client):
            from shopify_service import search_products_on_shopify
            result = await search_products_on_shopify(["テスト"])

    # 短い説明文に "..." が付加されないこと
    assert result["products"][0]["description"] == "短い説明"
