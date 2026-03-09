"""
リアルタイム人物切り抜きミラーサービス
Mac Studio接続カメラからキャプチャ → MediaPipeセグメンテーション → 透過PNG配信
"""

import os
import glob
import cv2
import numpy as np
import mediapipe as mp
import base64
import asyncio
from typing import AsyncGenerator

# カメラデバイスインデックス (環境変数で設定可能)
MIRROR_CAMERA_INDEX = int(os.getenv("MIRROR_CAMERA_INDEX", "0"))
# キャプチャ解像度 (低めで応答性優先)
CAPTURE_WIDTH = int(os.getenv("MIRROR_WIDTH", "640"))
CAPTURE_HEIGHT = int(os.getenv("MIRROR_HEIGHT", "480"))
# ターゲットFPS
TARGET_FPS = int(os.getenv("MIRROR_FPS", "15"))


def list_cameras(max_index: int = 10) -> list[dict]:
    """
    利用可能なカメラデバイスを列挙する。
    Linux: /dev/video* を走査、macOS/その他: インデックス0-max_indexを試行。
    """
    cameras: list[dict] = []

    # Linux: /dev/video* から物理デバイスを検出
    video_devs = sorted(glob.glob("/dev/video*"))
    if video_devs:
        seen_indices: set[int] = set()
        for dev in video_devs:
            try:
                idx = int(dev.replace("/dev/video", ""))
            except ValueError:
                continue
            if idx in seen_indices:
                continue
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                name = cap.getBackendName()
                cap.release()
                seen_indices.add(idx)
                cameras.append({
                    "index": idx,
                    "name": f"Camera {idx} ({name})",
                    "device": dev,
                    "resolution": f"{w}x{h}",
                })
        return cameras

    # macOS / その他: インデックスを順に試行
    for idx in range(max_index):
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            cameras.append({
                "index": idx,
                "name": f"Camera {idx}",
                "resolution": f"{w}x{h}",
            })
    return cameras


class MirrorSegmenter:
    """カメラキャプチャ + 人物セグメンテーションを管理するクラス"""

    def __init__(self):
        self.cap: cv2.VideoCapture | None = None
        self.segmenter = None
        self._running = False
        self._camera_index = MIRROR_CAMERA_INDEX

    @property
    def camera_index(self) -> int:
        return self._camera_index

    def set_camera(self, index: int) -> bool:
        """カメラを切り替える。稼働中なら再起動する。"""
        was_running = self._running
        if was_running:
            self.stop()
        self._camera_index = index
        if was_running:
            return self.start()
        return True

    def start(self) -> bool:
        """カメラとセグメンターを初期化"""
        if self._running:
            return True

        # カメラ起動
        self.cap = cv2.VideoCapture(self._camera_index)
        if not self.cap.isOpened():
            print(f"Mirror camera {self._camera_index} could not be opened")
            return False

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        # バッファ最小化 (最新フレームのみ)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # MediaPipe Selfie Segmentation (軽量モデル: model_selection=0)
        self.segmenter = mp.solutions.selfie_segmentation.SelfieSegmentation(
            model_selection=0  # 0=General, 1=Landscape (0のほうが軽量)
        )

        self._running = True
        print(f"Mirror started: camera={self._camera_index}, {CAPTURE_WIDTH}x{CAPTURE_HEIGHT}")
        return True

    def stop(self):
        """リソース解放"""
        self._running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.segmenter:
            self.segmenter.close()
            self.segmenter = None
        print("Mirror stopped")

    def get_cutout_frame(self) -> str | None:
        """
        1フレームをキャプチャしてセグメンテーション、
        人物切り抜き(透過PNG)のbase64文字列を返す。
        鏡像(左右反転)にして返す。
        """
        if not self._running or not self.cap or not self.segmenter:
            return None

        ret, frame = self.cap.read()
        if not ret:
            return None

        # 鏡像にする (左右反転)
        frame = cv2.flip(frame, 1)

        # MediaPipeはRGBを期待
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.segmenter.process(rgb)

        if results.segmentation_mask is None:
            return None

        # マスクを0-255にスケール
        mask = (results.segmentation_mask * 255).astype(np.uint8)

        # BGRAに変換してアルファチャンネルにマスクを適用
        bgra = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
        bgra[:, :, 3] = mask

        # PNGエンコード (透過)
        _, buf = cv2.imencode(".png", bgra, [cv2.IMWRITE_PNG_COMPRESSION, 1])
        return base64.b64encode(buf).decode("ascii")

    async def stream_frames(self) -> AsyncGenerator[str, None]:
        """非同期フレームジェネレーター"""
        interval = 1.0 / TARGET_FPS

        while self._running:
            frame_data = self.get_cutout_frame()
            if frame_data:
                yield frame_data
            await asyncio.sleep(interval)


# シングルトンインスタンス
mirror = MirrorSegmenter()
