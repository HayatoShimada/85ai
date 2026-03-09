"""
プロジェクション状態同期マネージャー
iPad (タッチUI) → Backend → プロジェクション画面の状態中継
"""

import asyncio
from fastapi import WebSocket


class ProjectionManager:
    """iPad (タッチUI) → Backend → プロジェクション画面の状態中継"""

    def __init__(self):
        self.displays: list[WebSocket] = []
        self._current_state: dict | None = None
        self._mirror_task: asyncio.Task | None = None
        self._mirror_active = False

    async def connect_display(self, ws: WebSocket):
        await ws.accept()
        self.displays.append(ws)
        if self._current_state:
            await ws.send_json(self._current_state)

    def disconnect_display(self, ws: WebSocket):
        if ws in self.displays:
            self.displays.remove(ws)
        if not self.displays and self._mirror_active:
            self._stop_mirror()

    async def handle_message(self, data: dict):
        msg_type = data.get("type")
        if msg_type == "STATE_CHANGE":
            self._current_state = data
            await self._broadcast_json(data)
            state = data.get("state", "")
            if state in ("CAMERA_ACTIVE", "ANALYZING"):
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
            return
        self._mirror_active = True
        self._mirror_task = asyncio.create_task(self._stream_mirror_loop())

    def _stop_mirror(self):
        from mirror_service import mirror

        self._mirror_active = False
        if self._mirror_task:
            self._mirror_task.cancel()
            self._mirror_task = None
        mirror.stop()

    async def _stream_mirror_loop(self):
        from mirror_service import mirror

        try:
            async for frame_data in mirror.stream_frames():
                if not self._mirror_active:
                    break
                if self.displays:
                    await self._broadcast_text(frame_data)
        except asyncio.CancelledError:
            pass
        finally:
            self._mirror_active = False


projection_mgr = ProjectionManager()
