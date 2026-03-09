import os
import pytest
from httpx import ASGITransport, AsyncClient

# テスト実行時は常にモックモードを有効化
os.environ["MOCK_MODE"] = "true"

from main import app


@pytest.fixture
def client():
    """同期テスト用: httpx AsyncClient を返す"""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
def dummy_image_bytes():
    """テスト用のダミーJPEG画像バイト列を生成"""
    from PIL import Image
    import io

    img = Image.new("RGB", (200, 300), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.getvalue()
