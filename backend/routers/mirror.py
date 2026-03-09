"""ミラーカメラ（リアルタイム人物切り抜き）エンドポイント"""

import os
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

from mirror_service import mirror, list_cameras

router = APIRouter()


def is_mock_mode() -> bool:
    return os.getenv("MOCK_MODE", "false").lower() == "true"


@router.get("/api/mirror/cameras")
async def get_mirror_cameras():
    """利用可能なミラーカメラの一覧と現在の選択を返す"""
    if is_mock_mode():
        return {"status": "ok", "cameras": [], "current": 0}
    cameras = list_cameras()
    return {"status": "ok", "cameras": cameras, "current": mirror.camera_index, "backend": mirror.backend}


@router.post("/api/mirror/cameras/{index}")
async def set_mirror_camera(index: int):
    """ミラーカメラを切り替える"""
    if is_mock_mode():
        return {"status": "ok", "message": "Mock mode: mirror not available"}
    ok = mirror.set_camera(index)
    if ok:
        return {"status": "ok", "current": mirror.camera_index}
    return {"status": "error", "message": f"Camera {index} could not be opened"}


@router.post("/api/mirror/start")
async def start_mirror():
    """ミラーカメラを起動"""
    if is_mock_mode():
        return {"status": "ok", "message": "Mock mode: mirror not available"}
    ok = mirror.start()
    if ok:
        return {"status": "ok"}
    return {"status": "error", "message": "Camera could not be opened"}


@router.post("/api/mirror/stop")
async def stop_mirror():
    """ミラーカメラを停止"""
    mirror.stop()
    return {"status": "ok"}


@router.websocket("/ws/mirror")
async def mirror_ws(websocket: WebSocket):
    """
    ミラーカメラのリアルタイム切り抜きフレームを配信するWebSocket。
    接続時に自動でカメラを起動し、切断時に停止する。
    """
    await websocket.accept()

    if is_mock_mode():
        await websocket.send_json({"type": "error", "message": "Mock mode: mirror not available"})
        await websocket.close()
        return

    if not mirror.start():
        await websocket.send_json({"type": "error", "message": "Camera could not be opened"})
        await websocket.close()
        return

    try:
        async for frame_data in mirror.stream_frames():
            await websocket.send_text(frame_data)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Mirror WebSocket error: {e}")
    finally:
        mirror.stop()
