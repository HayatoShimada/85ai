"""
Apple Vision Framework を使った人物セグメンテーション
macOS 12+ (Monterey) + Apple Silicon で Neural Engine を活用

qualityLevel:
  0 = fast     — GPU, マスク 128x96
  1 = balanced — GPU + Neural Engine, マスク 256x192
  2 = accurate — Neural Engine, マスク 1024x768 (最高品質)
"""

import platform
import logging
import numpy as np
import cv2

logger = logging.getLogger(__name__)

VISION_AVAILABLE = False

if platform.system() == "Darwin":
    try:
        import Vision
        import Quartz
        from Quartz import CoreVideo
        from Foundation import NSData
        import ctypes

        VISION_AVAILABLE = True
    except ImportError:
        pass


def is_available() -> bool:
    """Apple Vision Framework が利用可能か"""
    return VISION_AVAILABLE


class AppleVisionSegmenter:
    """
    VNGeneratePersonSegmentationRequest を使った人物セグメンテーション。
    Neural Engine を活用して高速・高精度に処理する。
    """

    FAST = 0
    BALANCED = 1
    ACCURATE = 2

    _QUALITY_NAMES = {
        0: "fast (GPU, 128x96)",
        1: "balanced (GPU+NE, 256x192)",
        2: "accurate (Neural Engine, 1024x768)",
    }

    def __init__(self, quality: int = ACCURATE):
        if not VISION_AVAILABLE:
            raise RuntimeError("Apple Vision Framework is not available (macOS 12+ required)")

        self._quality = quality

        # セグメンテーションリクエストを作成
        self._request = Vision.VNGeneratePersonSegmentationRequest.alloc().initWithCompletionHandler_(None)
        self._request.setQualityLevel_(quality)

        # 出力フォーマット: 8bit グレースケール (kCVPixelFormatType_OneComponent8)
        try:
            fmt = CoreVideo.kCVPixelFormatType_OneComponent8
        except AttributeError:
            fmt = 0x4C303038  # 'L008' in FourCC
        self._request.setOutputPixelFormat_(fmt)

        logger.info(f"AppleVisionSegmenter: quality={self._QUALITY_NAMES.get(quality, quality)}")

    def process(self, frame_bgr: np.ndarray) -> np.ndarray | None:
        """
        BGR 画像からセグメンテーションマスク (0-255, uint8) を返す。
        マスクは入力画像と同じ解像度にリサイズされる。
        """
        h, w = frame_bgr.shape[:2]

        # BGR → RGB → CGImage
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        cg_image = self._numpy_rgb_to_cgimage(rgb)
        if cg_image is None:
            return None

        # Vision request 実行
        handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(
            cg_image, None
        )
        success, error = handler.performRequests_error_([self._request], None)
        if not success:
            logger.error(f"Vision segmentation error: {error}")
            return None

        results = self._request.results()
        if not results or len(results) == 0:
            return None

        # マスクを CVPixelBuffer から numpy に変換
        observation = results[0]
        pixel_buffer = observation.pixelBuffer()
        mask = self._pixelbuffer_to_numpy(pixel_buffer)
        if mask is None:
            return None

        # マスクを入力解像度にリサイズ
        if mask.shape[0] != h or mask.shape[1] != w:
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)

        return mask

    def close(self):
        """リソース解放"""
        self._request = None

    @staticmethod
    def _numpy_rgb_to_cgimage(rgb: np.ndarray):
        """RGB numpy 配列 → CGImage"""
        h, w, c = rgb.shape
        bytes_per_row = w * c
        raw_bytes = rgb.tobytes()

        # NSData 経由で CGDataProvider を作成 (メモリ安全)
        ns_data = NSData.dataWithBytes_length_(raw_bytes, len(raw_bytes))
        data_provider = Quartz.CGDataProviderCreateWithCFData(ns_data)
        color_space = Quartz.CGColorSpaceCreateDeviceRGB()

        cg_image = Quartz.CGImageCreate(
            w, h,
            8,              # bits per component
            24,             # bits per pixel (8 * 3 channels)
            bytes_per_row,
            color_space,
            Quartz.kCGBitmapByteOrderDefault,
            data_provider,
            None,           # decode array
            False,          # should interpolate
            Quartz.kCGRenderingIntentDefault,
        )
        return cg_image

    @staticmethod
    def _pixelbuffer_to_numpy(pixel_buffer) -> np.ndarray | None:
        """CVPixelBuffer (OneComponent8) → numpy uint8 配列"""
        try:
            # バッファメモリをロック (読み取り専用)
            status = CoreVideo.CVPixelBufferLockBaseAddress(pixel_buffer, 0x00000001)
            if status != 0:
                logger.error(f"CVPixelBufferLockBaseAddress failed: {status}")
                return None

            try:
                width = CoreVideo.CVPixelBufferGetWidth(pixel_buffer)
                height = CoreVideo.CVPixelBufferGetHeight(pixel_buffer)
                bytes_per_row = CoreVideo.CVPixelBufferGetBytesPerRow(pixel_buffer)
                base_address = CoreVideo.CVPixelBufferGetBaseAddress(pixel_buffer)

                if base_address is None:
                    return None

                buf_size = height * bytes_per_row

                # PyObjC ポインタ → Python bytes への変換
                try:
                    # 方法1: as_buffer (新しい PyObjC)
                    buf = base_address.as_buffer(buf_size)
                except (AttributeError, TypeError):
                    # 方法2: ctypes 経由
                    ptr_int = int(base_address)
                    buf = ctypes.string_at(ptr_int, buf_size)

                arr = np.frombuffer(buf, dtype=np.uint8).reshape(height, bytes_per_row)
                # bytes_per_row にはパディングが含まれる場合がある
                mask = arr[:, :width].copy()
                return mask
            finally:
                CoreVideo.CVPixelBufferUnlockBaseAddress(pixel_buffer, 0x00000001)

        except Exception as e:
            logger.error(f"CVPixelBuffer → numpy conversion error: {e}")
            return None
