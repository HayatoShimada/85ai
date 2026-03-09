"""プロジェクション状態同期 WebSocket エンドポイント"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services.projection_manager import projection_mgr

router = APIRouter()


@router.websocket("/ws/projection/control")
async def projection_control_ws(websocket: WebSocket):
    """iPad (タッチUI) から状態変更・フラッシュ指示を受信"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            await projection_mgr.handle_message(data)
    except WebSocketDisconnect:
        pass


@router.websocket("/ws/projection/display")
async def projection_display_ws(websocket: WebSocket):
    """プロジェクション表示画面にイベント(状態・フラッシュ・ミラーフレーム)を配信"""
    await projection_mgr.connect_display(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "REQUEST_STATE" and projection_mgr._current_state:
                await websocket.send_json(projection_mgr._current_state)
    except WebSocketDisconnect:
        pass
    finally:
        projection_mgr.disconnect_display(websocket)
