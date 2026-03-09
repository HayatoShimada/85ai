"""ミラー WebSocket のテスト"""

import pytest
from unittest.mock import patch, MagicMock
from starlette.testclient import TestClient

from main import app


def test_mirror_ws_mock_mode_error():
    """モックモードでミラー WebSocket はエラーを返して閉じる"""
    client = TestClient(app)
    with client.websocket_connect("/ws/mirror") as ws:
        data = ws.receive_json()
        assert data["type"] == "error"
        assert "Mock mode" in data["message"]


def test_mirror_ws_camera_not_available():
    """カメラが開けない場合エラーを返す"""
    import os
    client = TestClient(app)

    with patch.dict(os.environ, {"MOCK_MODE": "false"}):
        with patch("routers.mirror.mirror") as mock_mirror:
            mock_mirror.start.return_value = False
            with client.websocket_connect("/ws/mirror") as ws:
                data = ws.receive_json()
                assert data["type"] == "error"
                assert "Camera" in data["message"]


def test_mirror_cameras_mock_mode():
    """モックモードでカメラ一覧が空を返す"""
    client = TestClient(app)
    response = client.get("/api/mirror/cameras")
    data = response.json()
    assert data["status"] == "ok"
    assert data["cameras"] == []
