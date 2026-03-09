"""ロギング設定"""

import logging
import sys


def setup_logging():
    """アプリケーション全体のログ設定を初期化"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    # 外部ライブラリのログレベルを抑制
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("mediapipe").setLevel(logging.WARNING)
