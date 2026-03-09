"""
リアルタイム人物切り抜きミラーサービス
Mac Studio接続カメラからキャプチャ → セグメンテーション → 透過WebP配信

セグメンテーションバックエンド:
  - macOS (Apple Silicon): Apple Vision Framework (Neural Engine 活用)
  - Linux / Docker: MediaPipe Selfie Segmentation (CPU)
"""

import os
import glob
import time
import logging
import cv2
import numpy as np
import base64
import asyncio
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# --- セグメンテーションバックエンド選択 ---
# auto: macOS→Vision, Linux→MediaPipe / vision: 強制Vision / mediapipe: 強制MediaPipe
SEGMENTER_BACKEND = os.getenv("MIRROR_SEGMENTER", "auto")

# カメラデバイスインデックス (環境変数で設定可能)
MIRROR_CAMERA_INDEX = int(os.getenv("MIRROR_CAMERA_INDEX", "0"))
# キャプチャ解像度
CAPTURE_WIDTH = int(os.getenv("MIRROR_WIDTH", "1920"))
CAPTURE_HEIGHT = int(os.getenv("MIRROR_HEIGHT", "1080"))
# ターゲットFPS
TARGET_FPS = int(os.getenv("MIRROR_FPS", "30"))
# セグメンテーション処理用の内部解像度 (MediaPipe用、Vision は内部で自動調整)
SEGMENTATION_WIDTH = int(os.getenv("MIRROR_SEG_WIDTH", "640"))
# WebP品質 (0-100, 低いほど高速・小サイズ)
WEBP_QUALITY = int(os.getenv("MIRROR_WEBP_QUALITY", "80"))
# マスクエッジのぼかし強度 (0=なし, 奇数で指定)
MASK_BLUR = int(os.getenv("MIRROR_MASK_BLUR", "7"))
# マスク閾値 (0.0-1.0, 高いほどタイトなカット)
MASK_THRESHOLD = float(os.getenv("MIRROR_MASK_THRESHOLD", "0.5"))
# Vision Framework 品質レベル (0=fast/GPU, 1=balanced/GPU+NE, 2=accurate/NeuralEngine)
VISION_QUALITY = int(os.getenv("MIRROR_VISION_QUALITY", "2"))


def _select_backend() -> str:
    """使用するセグメンテーションバックエンドを決定する"""
    if SEGMENTER_BACKEND == "vision":
        import vision_segmenter
        if vision_segmenter.is_available():
            return "vision"
        logger.warning("Vision requested but not available, falling back to MediaPipe")
        return "mediapipe"

    if SEGMENTER_BACKEND == "mediapipe":
        return "mediapipe"

    # auto: macOS なら Vision を試行
    try:
        import vision_segmenter
        if vision_segmenter.is_available():
            return "vision"
    except ImportError:
        pass

    return "mediapipe"


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
        self._mp_segmenter = None       # MediaPipe セグメンター
        self._vision_segmenter = None   # Apple Vision セグメンター
        self._backend = "none"
        self._running = False
        self._camera_index = MIRROR_CAMERA_INDEX
        self._seg_size = (SEGMENTATION_WIDTH, 360)  # MediaPipe用デフォルト

    @property
    def camera_index(self) -> int:
        return self._camera_index

    @property
    def backend(self) -> str:
        """現在のセグメンテーションバックエンド名"""
        return self._backend

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
            logger.error(f"Mirror camera {self._camera_index} could not be opened")
            return False

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)
        # バッファ最小化 (最新フレームのみ)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        # MJPEG優先 (USB帯域効率が良い)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)

        # セグメンテーション用縮小サイズを計算 (MediaPipe用)
        seg_scale = SEGMENTATION_WIDTH / actual_w
        self._seg_size = (SEGMENTATION_WIDTH, int(actual_h * seg_scale))

        # セグメンテーションバックエンド初期化
        backend = _select_backend()

        if backend == "vision":
            try:
                import vision_segmenter
                self._vision_segmenter = vision_segmenter.AppleVisionSegmenter(
                    quality=VISION_QUALITY
                )
                self._backend = "vision"
                logger.info(f"Mirror started: camera={self._camera_index}, "
                            f"capture={actual_w}x{actual_h}@{actual_fps:.0f}fps, "
                            f"backend=Apple Vision (Neural Engine)")
            except Exception as e:
                logger.warning(f"Vision init failed: {e}, falling back to MediaPipe")
                backend = "mediapipe"

        if backend == "mediapipe":
            import mediapipe as mp
            self._mp_segmenter = mp.solutions.selfie_segmentation.SelfieSegmentation(
                model_selection=1  # 0=General(128x128), 1=Landscape(256x256, 高精度)
            )
            self._backend = "mediapipe"
            logger.info(f"Mirror started: camera={self._camera_index}, "
                        f"capture={actual_w}x{actual_h}@{actual_fps:.0f}fps, "
                        f"backend=MediaPipe, seg={self._seg_size[0]}x{self._seg_size[1]}")

        logger.info(f"  webp_q={WEBP_QUALITY}, blur={MASK_BLUR}, threshold={MASK_THRESHOLD}")

        self._running = True
        return True

    def stop(self):
        """リソース解放"""
        self._running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        if self._mp_segmenter:
            self._mp_segmenter.close()
            self._mp_segmenter = None
        if self._vision_segmenter:
            self._vision_segmenter.close()
            self._vision_segmenter = None
        self._backend = "none"
        logger.info("Mirror stopped")

    def _get_mask_vision(self, frame: np.ndarray) -> np.ndarray | None:
        """Apple Vision Framework でセグメンテーションマスクを取得"""
        return self._vision_segmenter.process(frame)

    def _get_mask_mediapipe(self, frame: np.ndarray) -> np.ndarray | None:
        """MediaPipe でセグメンテーションマスクを取得 (縮小→拡大)"""
        h, w = frame.shape[:2]

        # セグメンテーション用に縮小 (処理速度向上)
        small = cv2.resize(frame, self._seg_size, interpolation=cv2.INTER_LINEAR)
        small_rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        results = self._mp_segmenter.process(small_rgb)

        if results.segmentation_mask is None:
            return None

        # マスクを元解像度に拡大
        mask = results.segmentation_mask
        if mask.shape[0] != h or mask.shape[1] != w:
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)

        # 0-255 にスケール
        return (mask * 255).astype(np.uint8)

    def get_cutout_frame(self) -> str | None:
        """
        1フレームをキャプチャしてセグメンテーション、
        人物切り抜き(透過WebP)のbase64文字列を返す。
        鏡像(左右反転)にして返す。
        """
        if not self._running or not self.cap:
            return None

        ret, frame = self.cap.read()
        if not ret:
            return None

        # 鏡像にする (左右反転)
        frame = cv2.flip(frame, 1)

        # セグメンテーションマスク取得
        if self._backend == "vision":
            mask_u8 = self._get_mask_vision(frame)
        elif self._backend == "mediapipe":
            mask_u8 = self._get_mask_mediapipe(frame)
        else:
            return None

        if mask_u8 is None:
            return None

        # 閾値適用 (Vision の場合は既に 0-255 なので閾値のみ)
        if self._backend == "mediapipe":
            # MediaPipe: 閾値でソフトマスク
            mask_u8 = ((mask_u8 / 255.0 > MASK_THRESHOLD).astype(np.float32)
                       * mask_u8).astype(np.uint8)
        else:
            # Vision: 閾値でカット
            threshold_val = int(MASK_THRESHOLD * 255)
            mask_u8 = np.where(mask_u8 > threshold_val, mask_u8, 0).astype(np.uint8)

        # マスクエッジをガウシアンブラーで滑らかに
        if MASK_BLUR > 1:
            mask_u8 = cv2.GaussianBlur(mask_u8, (MASK_BLUR, MASK_BLUR), 0)

        # BGRAに変換してアルファチャンネルにマスクを適用
        bgra = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
        bgra[:, :, 3] = mask_u8

        # WebPエンコード (透過対応、PNGより高速)
        _, buf = cv2.imencode(".webp", bgra, [cv2.IMWRITE_WEBP_QUALITY, WEBP_QUALITY])
        return base64.b64encode(buf).decode("ascii")

    async def stream_frames(self) -> AsyncGenerator[str, None]:
        """
        非同期フレームジェネレーター。
        CPU集約処理をスレッドプールにオフロードし、イベントループをブロックしない。
        処理時間を考慮してフレーム間隔を調整し、一定FPSを維持する。
        """
        interval = 1.0 / TARGET_FPS

        while self._running:
            t0 = time.monotonic()
            frame_data = await asyncio.to_thread(self.get_cutout_frame)
            elapsed = time.monotonic() - t0

            if frame_data:
                yield frame_data

            # 処理時間を差し引いた残り時間だけスリープ
            sleep_time = interval - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)


# シングルトンインスタンス
mirror = MirrorSegmenter()
