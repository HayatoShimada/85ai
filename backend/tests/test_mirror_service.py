"""mirror_service のユニットテスト（カメラ・セグメンターをモック）"""

import pytest
from unittest.mock import patch, MagicMock
import numpy as np


def _fresh_mirror():
    """テストごとに新しい MirrorSegmenter を生成"""
    from mirror_service import MirrorSegmenter
    return MirrorSegmenter()


def test_initial_state():
    """初期状態: カメラ未接続、backend=none"""
    ms = _fresh_mirror()
    assert ms.cap is None
    assert ms.backend == "none"
    assert ms._running is False
    assert ms.camera_index == 0  # デフォルト


def test_set_camera_updates_index():
    """set_camera() でインデックスが更新される（停止中）"""
    ms = _fresh_mirror()
    result = ms.set_camera(2)
    assert result is True
    assert ms.camera_index == 2


def test_start_fails_without_camera():
    """カメラが開けない場合 start() は False"""
    ms = _fresh_mirror()
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False

    with patch("mirror_service.cv2.VideoCapture", return_value=mock_cap):
        result = ms.start()
    assert result is False
    assert ms._running is False


def test_select_backend_auto_mediapipe():
    """auto モードで Vision が利用不可なら mediapipe を返す"""
    with patch.dict("os.environ", {"MIRROR_SEGMENTER": "auto"}):
        with patch("mirror_service.SEGMENTER_BACKEND", "auto"):
            with patch.dict("sys.modules", {"vision_segmenter": None}):
                from mirror_service import _select_backend
                # vision_segmenter が import できない場合
                with patch("builtins.__import__", side_effect=_import_no_vision):
                    result = _select_backend()
    assert result == "mediapipe"


def _import_no_vision(name, *args, **kwargs):
    """vision_segmenter を ImportError にする import フック"""
    if name == "vision_segmenter":
        raise ImportError("No Vision Framework")
    return original_import(name, *args, **kwargs)


import builtins
original_import = builtins.__import__


def test_env_configures_parameters():
    """環境変数でキャプチャパラメータが設定される"""
    env = {
        "MIRROR_WIDTH": "1280",
        "MIRROR_HEIGHT": "720",
        "MIRROR_FPS": "24",
        "MIRROR_WEBP_QUALITY": "60",
        "MIRROR_MASK_BLUR": "5",
        "MIRROR_MASK_THRESHOLD": "0.7",
    }
    with patch.dict("os.environ", env, clear=False):
        # モジュールを再読み込みして環境変数を反映
        import importlib
        import mirror_service
        importlib.reload(mirror_service)

        assert mirror_service.CAPTURE_WIDTH == 1280
        assert mirror_service.CAPTURE_HEIGHT == 720
        assert mirror_service.TARGET_FPS == 24
        assert mirror_service.WEBP_QUALITY == 60
        assert mirror_service.MASK_BLUR == 5
        assert mirror_service.MASK_THRESHOLD == 0.7

        # デフォルトに戻す
        for key in env:
            import os
            os.environ.pop(key, None)
        importlib.reload(mirror_service)
