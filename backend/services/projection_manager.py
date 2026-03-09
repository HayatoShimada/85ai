"""
プロジェクション状態同期マネージャー
iPad (タッチUI) → Backend → プロジェクション画面の状態中継
"""

import asyncio
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)

# ミラーを配信する状態
_MIRROR_STATES = {"IDLE", "PREFERENCE", "CAMERA_ACTIVE", "ANALYZING"}


class ProjectionManager:
    """iPad (タッチUI) → Backend → プロジェクション画面の状態中継"""

    def __init__(self):
        self.displays: list[WebSocket] = []
        self._current_state: dict | None = None
        self._mirror_task: asyncio.Task | None = None
        self._mirror_active = False

    def _should_mirror(self) -> bool:
        """現在の状態でミラー配信が必要か"""
        if not self._current_state:
            return False
        return self._current_state.get("state", "") in _MIRROR_STATES

    async def connect_display(self, ws: WebSocket):
        await ws.accept()
        self.displays.append(ws)
        logger.info(f"Display connected (total={len(self.displays)})")
        if self._current_state:
            await ws.send_json(self._current_state)
        # ミラーを起動 (状態未設定ならIDLE扱い = ミラー必要)
        if not self._mirror_active:
            self._start_mirror()

    def disconnect_display(self, ws: WebSocket):
        if ws in self.displays:
            self.displays.remove(ws)
        logger.info(f"Display disconnected (total={len(self.displays)})")
        if not self.displays and self._mirror_active:
            self._stop_mirror()

    async def handle_message(self, data: dict):
        msg_type = data.get("type")
        if msg_type == "STATE_CHANGE":
            self._current_state = data
            await self._broadcast_json(data)
            state = data.get("state", "")
            if state in _MIRROR_STATES:
                if not self._mirror_active and self.displays:
                    self._start_mirror()
            else:
                if self._mirror_active:
                    self._stop_mirror()
        elif msg_type == "FLASH":
            await self._broadcast_json(data)

    async def _broadcast_json(self, data: dict):
        dead: list[WebSocket] = []
        for ws in self.displays:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.displays.remove(ws)

    async def _broadcast_text(self, text: str):
        dead: list[WebSocket] = []
        for ws in self.displays:
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.displays.remove(ws)

    def _start_mirror(self):
        from mirror_service import mirror
        import os

        if os.getenv("MOCK_MODE", "false").lower() == "true":
            return
        if not mirror.start():
            logger.warning("Mirror failed to start")
            return
        self._mirror_active = True
        self._mirror_task = asyncio.create_task(self._stream_mirror_loop())
        logger.info("Mirror stream started for display clients")

    def _stop_mirror(self):
        from mirror_service import mirror

        self._mirror_active = False
        if self._mirror_task:
            self._mirror_task.cancel()
            self._mirror_task = None
        mirror.stop()
        logger.info("Mirror stream stopped")

    async def _stream_mirror_loop(self):
        from mirror_service import mirror

        frame_count = 0
        try:
            async for frame_data in mirror.stream_frames():
                if not self._mirror_active:
                    break
                if self.displays:
                    await self._broadcast_text(frame_data)
                    frame_count += 1
                    if frame_count == 1:
                        logger.info(f"First mirror frame broadcast to {len(self.displays)} display(s), size={len(frame_data)}B")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Mirror stream loop error: {e}")
        finally:
            self._mirror_active = False
            logger.info(f"Mirror stream loop ended after {frame_count} frames")


projection_mgr = ProjectionManager()
