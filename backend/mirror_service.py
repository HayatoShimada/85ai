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
import platform
import subprocess
import threading
import concurrent.futures
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
WEBP_QUALITY = int(os.getenv("MIRROR_WEBP_QUALITY", "60"))
# 出力解像度の幅 (エンコード高速化のため、キャプチャ後にリサイズ)
OUTPUT_WIDTH = int(os.getenv("MIRROR_OUTPUT_WIDTH", "960"))
# マスクエッジのぼかし強度 (0=なし, 奇数で指定)
MASK_BLUR = int(os.getenv("MIRROR_MASK_BLUR", "7"))
# マスク閾値 (0.0-1.0, 高いほどタイトなカット)
MASK_THRESHOLD = float(os.getenv("MIRROR_MASK_THRESHOLD", "0.5"))
# エッジリファイン: エッジ周辺のフェザー幅 (px, 0=無効)
EDGE_FEATHER = int(os.getenv("MIRROR_EDGE_FEATHER", "15"))
# モルフォロジー: 小さな穴・突起を除去するカーネルサイズ (0=無効)
MORPH_SIZE = int(os.getenv("MIRROR_MORPH_SIZE", "5"))
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


def _get_macos_camera_names() -> list[str]:
    """macOS: system_profiler でカメラデバイス名を取得"""
    if platform.system() != "Darwin":
        return []
    try:
        import json as _json
        r = subprocess.run(
            ["system_profiler", "SPCameraDataType", "-json"],
            capture_output=True, text=True, timeout=5,
        )
        data = _json.loads(r.stdout)
        return [cam.get("_name", "Unknown") for cam in data.get("SPCameraDataType", [])]
    except Exception:
        return []


def list_cameras(max_index: int = 3) -> list[dict]:
    """
    利用可能なカメラデバイスを列挙する。
    Linux: /dev/video* を走査、macOS/その他: インデックス0-max_indexを試行。
    macOS では system_profiler からデバイス名を取得して表示する。
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
    macos_names = _get_macos_camera_names()
    name_idx = 0
    for idx in range(max_index):
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            if name_idx < len(macos_names):
                name = macos_names[name_idx]
                name_idx += 1
            else:
                name = f"Camera {idx}"
            cameras.append({
                "index": idx,
                "name": name,
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
        # カメラアクセスは常に同一スレッドから行う (AVFoundation スレッド安全性対策)
        self._camera_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="mirror-cam"
        )
        self._lock = threading.Lock()

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
                logger.warning(f"Vision init failed ({e}), falling back to MediaPipe")
                backend = "mediapipe"

        if backend == "mediapipe":
            try:
                import mediapipe as mp
                self._mp_segmenter = mp.solutions.selfie_segmentation.SelfieSegmentation(
                    model_selection=1  # 0=General(128x128), 1=Landscape(256x256, 高精度)
                )
                self._backend = "mediapipe"
                logger.info(f"Mirror started: camera={self._camera_index}, "
                            f"capture={actual_w}x{actual_h}@{actual_fps:.0f}fps, "
                            f"backend=MediaPipe, seg={self._seg_size[0]}x{self._seg_size[1]}")
            except Exception as e:
                logger.error(f"MediaPipe init failed: {e}")
                # カメラを開放してエラーを返す
                if self.cap:
                    self.cap.release()
                    self.cap = None
                return False

        if self._backend == "none":
            logger.error("No segmentation backend available")
            if self.cap:
                self.cap.release()
                self.cap = None
            return False

        logger.info(f"  webp_q={WEBP_QUALITY}, blur={MASK_BLUR}, threshold={MASK_THRESHOLD}")

        self._running = True
        return True

    def stop(self):
        """リソース解放"""
        with self._lock:
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

    @staticmethod
    def _refine_mask(mask_u8: np.ndarray, frame_bgr: np.ndarray) -> np.ndarray:
        """
        アート品質のマスクリファイン処理。
        映像作品・インスタレーション向けの滑らかな切り抜きを実現する。

        1. 閾値で確信度の低い領域を除去
        2. モルフォロジー処理で小さな穴・突起を除去 (close → open)
        3. エッジ検出 + 距離変換ベースのソフトフェザー
        4. 元画像のエッジを考慮した局所的なブレンド
        """
        mask_f = mask_u8.astype(np.float32) / 255.0

        # 1. ソフト閾値: シグモイド風のカーブで滑らかにカット
        #    threshold 付近を急峻にしつつ、完全なバイナリにはしない
        steepness = 12.0  # 大きいほどシャープ
        mask_f = 1.0 / (1.0 + np.exp(-steepness * (mask_f - MASK_THRESHOLD)))

        # 2. モルフォロジー: 穴埋め + ノイズ除去
        if MORPH_SIZE > 1:
            mask_bin = (mask_f * 255).astype(np.uint8)
            kernel = cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE, (MORPH_SIZE, MORPH_SIZE)
            )
            # close: 小さな穴を埋める
            mask_bin = cv2.morphologyEx(mask_bin, cv2.MORPH_CLOSE, kernel)
            # open: 小さな突起を除去
            mask_bin = cv2.morphologyEx(mask_bin, cv2.MORPH_OPEN, kernel)
            mask_f = mask_bin.astype(np.float32) / 255.0

        # 3. エッジフェザー: マスク境界を距離変換で滑らかにグラデーション
        if EDGE_FEATHER > 0:
            # バイナリマスクからエッジ領域を特定
            hard = (mask_f > 0.5).astype(np.uint8)

            # 前景からの距離 (内側へのフェザー)
            dist_fg = cv2.distanceTransform(hard, cv2.DIST_L2, 5)
            # 背景からの距離 (外側へのフェザー)
            dist_bg = cv2.distanceTransform(1 - hard, cv2.DIST_L2, 5)

            # フェザー幅内でグラデーション (0→1)
            feather = EDGE_FEATHER
            alpha = np.clip(dist_fg / feather, 0, 1).astype(np.float32)
            # 外側にも薄く広げる (自然な透け感)
            outer_blend = np.clip(1.0 - dist_bg / (feather * 0.5), 0, 1)
            alpha = np.maximum(alpha, outer_blend * 0.3)

            # 元のソフトマスクとブレンド (エッジ以外は元マスクを尊重)
            edge_zone = (dist_fg < feather) | (dist_bg < feather * 0.5)
            mask_f = np.where(edge_zone, alpha, mask_f)

        # 4. 最終ガウシアンブラー (微細なジャギー除去)
        if MASK_BLUR > 1:
            mask_f = cv2.GaussianBlur(mask_f, (MASK_BLUR, MASK_BLUR), 0)

        return (np.clip(mask_f, 0, 1) * 255).astype(np.uint8)

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
        t_start = time.monotonic()

        with self._lock:
            if not self._running or not self.cap:
                return None

            ret, frame = self.cap.read()
        if not ret:
            return None

        t_cap = time.monotonic()

        # 鏡像にする (左右反転)
        frame = cv2.flip(frame, 1)

        # セグメンテーションマスク取得
        if self._backend == "vision":
            mask_u8 = self._get_mask_vision(frame)
        elif self._backend == "mediapipe":
            mask_u8 = self._get_mask_mediapipe(frame)
        else:
            return None

        t_seg = time.monotonic()

        if mask_u8 is None:
            return None

        # --- アート品質マスクリファイン ---
        mask_u8 = self._refine_mask(mask_u8, frame)

        # BGRAに変換してアルファチャンネルにマスクを適用
        bgra = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
        bgra[:, :, 3] = mask_u8

        # 出力用にリサイズ (エンコード高速化)
        h, w = bgra.shape[:2]
        if w > OUTPUT_WIDTH:
            scale = OUTPUT_WIDTH / w
            out_size = (OUTPUT_WIDTH, int(h * scale))
            bgra = cv2.resize(bgra, out_size, interpolation=cv2.INTER_AREA)

        t_mask = time.monotonic()

        # WebPエンコード (透過対応、PNGより高速)
        _, buf = cv2.imencode(".webp", bgra, [cv2.IMWRITE_WEBP_QUALITY, WEBP_QUALITY])
        result = base64.b64encode(buf).decode("ascii")

        t_enc = time.monotonic()

        # パフォーマンスログ (100フレームに1回)
        if not hasattr(self, '_frame_count'):
            self._frame_count = 0
        self._frame_count += 1
        if self._frame_count % 100 == 1:
            total = (t_enc - t_start) * 1000
            logger.info(
                f"Mirror frame perf: total={total:.0f}ms "
                f"(capture={((t_cap - t_start) * 1000):.0f}ms, "
                f"seg={((t_seg - t_cap) * 1000):.0f}ms, "
                f"mask={((t_mask - t_seg) * 1000):.0f}ms, "
                f"encode={((t_enc - t_mask) * 1000):.0f}ms) "
                f"size={len(result)//1024}KB"
            )

        return result

    async def stream_frames(self) -> AsyncGenerator[str, None]:
        """
        非同期フレームジェネレーター。
        専用の単一スレッドでカメラアクセスを行い、AVFoundation のスレッド安全性を保証する。
        処理時間を考慮してフレーム間隔を調整し、一定FPSを維持する。
        """
        interval = 1.0 / TARGET_FPS
        loop = asyncio.get_running_loop()

        while self._running:
            t0 = time.monotonic()
            frame_data = await loop.run_in_executor(
                self._camera_executor, self.get_cutout_frame
            )
            elapsed = time.monotonic() - t0

            if frame_data:
                yield frame_data

            # 処理時間を差し引いた残り時間だけスリープ
            sleep_time = interval - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)


# シングルトンインスタンス
mirror = MirrorSegmenter()
