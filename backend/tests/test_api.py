"""
APIエンドポイントの統合テスト（モックモードで実行）
"""

import json
import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.asyncio
async def test_root(client):
    res = await client.get("/")
    assert res.status_code == 200
    assert res.json()["message"] == "Welcome to the Vintage AI Shop Assistant API"


@pytest.mark.asyncio
async def test_health_check(client):
    res = await client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["mock_mode"] is True


@pytest.mark.asyncio
async def test_analyze_returns_success(client, dummy_image_bytes):
    """画像を送信してモック解析結果が返ること"""
    res = await client.post(
        "/api/analyze",
        files={"file": ("test.jpg", dummy_image_bytes, "image/jpeg")},
        data={"preferences": json.dumps(["かっこいい", "ストリート"])},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "analyzed_outfit" in data["data"]
    assert "detected_style" in data["data"]
    assert "recommendations" in data["data"]
    assert len(data["data"]["recommendations"]) == 3


@pytest.mark.asyncio
async def test_analyze_without_preferences(client, dummy_image_bytes):
    """好みタグなしでも正常に動作すること"""
    res = await client.post(
        "/api/analyze",
        files={"file": ("test.jpg", dummy_image_bytes, "image/jpeg")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["data"]["recommendations"]) == 3


@pytest.mark.asyncio
async def test_analyze_recommendations_have_products(client, dummy_image_bytes):
    """各提案パターンに商品データが含まれていること"""
    res = await client.post(
        "/api/analyze",
        files={"file": ("test.jpg", dummy_image_bytes, "image/jpeg")},
    )
    data = res.json()
    for rec in data["data"]["recommendations"]:
        assert "title" in rec
        assert "reason" in rec
        assert "search_keywords" in rec
        assert "category" in rec
        assert "shopify_products" in rec
        for product in rec["shopify_products"]:
            assert "id" in product
            assert "title" in product
            assert "price" in product


@pytest.mark.asyncio
async def test_analyze_bounding_box(client, dummy_image_bytes):
    """バウンディングボックス座標が返ること"""
    res = await client.post(
        "/api/analyze",
        files={"file": ("test.jpg", dummy_image_bytes, "image/jpeg")},
    )
    data = res.json()["data"]
    assert 0 <= data["box_ymin"] <= 1000
    assert 0 <= data["box_xmin"] <= 1000
    assert 0 <= data["box_ymax"] <= 1000
    assert 0 <= data["box_xmax"] <= 1000
    assert data["box_ymax"] > data["box_ymin"]
    assert data["box_xmax"] > data["box_xmin"]


@pytest.mark.asyncio
async def test_analyze_invalid_preferences_json(client, dummy_image_bytes):
    """不正なpreferences JSONでも落ちずに動作すること"""
    res = await client.post(
        "/api/analyze",
        files={"file": ("test.jpg", dummy_image_bytes, "image/jpeg")},
        data={"preferences": "not-json"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"


@pytest.mark.asyncio
async def test_analyze_gemini_error_returns_error(client, dummy_image_bytes):
    """Geminiがエラーを返した場合にerrorステータスが返ること（非モック）"""
    import os
    from gemini_service import GeminiAnalysisError

    with patch.dict(os.environ, {"MOCK_MODE": "false"}):
        with patch(
            "routers.analyze.analyze_image_and_get_tags",
            side_effect=GeminiAnalysisError("AI解析がタイムアウトしました。もう一度お試しください。"),
        ):
            res = await client.post(
                "/api/analyze",
                files={"file": ("test.jpg", dummy_image_bytes, "image/jpeg")},
            )
            data = res.json()
            assert data["status"] == "error"
            assert "タイムアウト" in data["message"]


@pytest.mark.asyncio
async def test_analyze_catalog_product_resolution(client, dummy_image_bytes):
    """カタログから商品IDで解決し、存在しないIDは空リストになること（非モック）"""
    import os

    mock_gemini_result = json.dumps({
        "analyzed_outfit": "テスト服装",
        "detected_style": ["カジュアル"],
        "box_ymin": 100, "box_xmin": 200, "box_ymax": 800, "box_xmax": 700,
        "recommendations": [
            {"title": "パターン1", "reason": "理由1", "product_ids": [9999], "category": "トップス"},
        ],
    })

    with patch.dict(os.environ, {"MOCK_MODE": "false"}):
        with patch("routers.analyze.analyze_image_and_get_tags", return_value=mock_gemini_result):
            res = await client.post(
                "/api/analyze",
                files={"file": ("test.jpg", dummy_image_bytes, "image/jpeg")},
            )
            data = res.json()
            assert data["status"] == "success"
            assert data["data"]["analyzed_outfit"] == "テスト服装"
            # 存在しないproduct_idなのでshopify_productsは空
            assert data["data"]["recommendations"][0]["shopify_products"] == []
