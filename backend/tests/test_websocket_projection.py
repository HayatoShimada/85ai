"""プロジェクション WebSocket のテスト"""

import pytest
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


def test_control_ws_connect():
    """control WebSocket に接続できる"""
    client = TestClient(app)
    with client.websocket_connect("/ws/projection/control") as ws:
        ws.send_json({"type": "STATE_CHANGE", "state": "IDLE"})
        # 送信できれば成功（control はレスポンスを返さない）


def test_display_ws_connect():
    """display WebSocket に接続できる"""
    client = TestClient(app)
    with client.websocket_connect("/ws/projection/display") as ws:
        # 接続直後に初期状態がないので何も来ない → REQUEST_STATE を送って応答なしを確認
        ws.send_json({"type": "REQUEST_STATE"})
        # current_state=None なのでレスポンスなし


def test_state_propagation_control_to_display():
    """control → display への状態伝播"""
    client = TestClient(app)
    with client.websocket_connect("/ws/projection/display") as display_ws:
        with client.websocket_connect("/ws/projection/control") as control_ws:
            state_msg = {"type": "STATE_CHANGE", "state": "PREFERENCE"}
            control_ws.send_json(state_msg)

        # display が STATE_CHANGE を受信
        data = display_ws.receive_json()
        assert data["type"] == "STATE_CHANGE"
        assert data["state"] == "PREFERENCE"


def test_flash_broadcast():
    """FLASH メッセージが display にブロードキャストされる"""
    client = TestClient(app)
    with client.websocket_connect("/ws/projection/display") as display_ws:
        with client.websocket_connect("/ws/projection/control") as control_ws:
            flash_msg = {"type": "FLASH"}
            control_ws.send_json(flash_msg)

        data = display_ws.receive_json()
        assert data["type"] == "FLASH"


def test_disconnect_cleanup():
    """display 切断後に displays リストからクリーンアップされる"""
    from services.projection_manager import projection_mgr
    client = TestClient(app)

    with client.websocket_connect("/ws/projection/display"):
        assert len(projection_mgr.displays) == 1

    # 切断後
    assert len(projection_mgr.displays) == 0


def test_request_state_returns_current():
    """REQUEST_STATE で最新状態が返却される"""
    from services.projection_manager import projection_mgr
    client = TestClient(app)

    # まず状態をセット
    with client.websocket_connect("/ws/projection/control") as control_ws:
        control_ws.send_json({"type": "STATE_CHANGE", "state": "RESULT", "data": {"foo": "bar"}})

    # display 接続時に current_state が送信される
    with client.websocket_connect("/ws/projection/display") as display_ws:
        data = display_ws.receive_json()
        assert data["type"] == "STATE_CHANGE"
        assert data["state"] == "RESULT"

        # REQUEST_STATE でも返る
        display_ws.send_json({"type": "REQUEST_STATE"})
        data2 = display_ws.receive_json()
        assert data2["state"] == "RESULT"
