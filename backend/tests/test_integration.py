"""統合テスト"""

import json
import pytest
from unittest.mock import patch
from starlette.testclient import TestClient
from services.projection_manager import ProjectionManager

from main import app


@pytest.fixture(autouse=True)
def reset_projection_mgr():
    """テストごとに ProjectionManager をリセット"""
    from services.projection_manager import projection_mgr
    projection_mgr.displays.clear()
    projection_mgr._current_state = None
    projection_mgr._mirror_active = False
    projection_mgr._mirror_task = None
    yield
    projection_mgr.displays.clear()
    projection_mgr._current_state = None


def test_full_flow_idle_to_result():
    """IDLE → PREFERENCE → CAMERA → ANALYZING → RESULT のフルフロー（モック）"""
    client = TestClient(app)

    with client.websocket_connect("/ws/projection/display") as display_ws:
        with client.websocket_connect("/ws/projection/control") as control_ws:
            states = ["IDLE", "PREFERENCE", "CAMERA_ACTIVE", "ANALYZING", "RESULT"]
            for state in states:
                control_ws.send_json({"type": "STATE_CHANGE", "state": state})

        # display が全状態を受信
        received_states = []
        for _ in range(len(states)):
            data = display_ws.receive_json()
            received_states.append(data["state"])

        assert received_states == states


@pytest.mark.asyncio
async def test_analyze_with_customer_id():
    """顧客 ID 付き解析リクエストがモックで成功する"""
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        from PIL import Image
        import io
        img = Image.new("RGB", (100, 100), color="red")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        res = await client.post(
            "/api/analyze",
            files={"file": ("test.jpg", buf.getvalue(), "image/jpeg")},
            data={
                "preferences": json.dumps(["かっこいい"]),
                "customer_id": "gid://shopify/Customer/123",
            },
        )
        data = res.json()
        assert data["status"] == "success"
        assert "recommendations" in data["data"]


def test_health_check_all_configured():
    """全 API 設定済みヘルスチェック"""
    import os

    env = {
        "MOCK_MODE": "false",
        "GEMINI_API_KEY": "test-key",
        "SHOPIFY_STORE_URL": "test.myshopify.com",
        "SHOPIFY_STOREFRONT_ACCESS_TOKEN": "test-token",
        "SHOPIFY_ADMIN_API_ACCESS_TOKEN": "shpat_test",
    }
    client = TestClient(app)
    with patch.dict(os.environ, env, clear=False):
        response = client.get("/api/health")
        data = response.json()
        assert data["status"] == "ok"
        assert data["mock_mode"] is False
        assert data["gemini_configured"] is True
        assert data["shopify_storefront_configured"] is True
        assert data["shopify_admin_configured"] is True
