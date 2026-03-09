from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

from logging_config import setup_logging
from routers import analyze, customers, mirror, projection
from catalog_service import catalog_cache

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時: 商品カタログをロード
    logger.info("Loading product catalog...")
    await catalog_cache.load()
    await catalog_cache.start_background_refresh()
    yield
    # 停止時: バックグラウンドリフレッシュを停止
    catalog_cache.stop_background_refresh()


app = FastAPI(title="Vintage AI Shop Assistant API", lifespan=lifespan)

# フロントエンドからのAPIアクセスを許可するCORS設定
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(analyze.router)
app.include_router(customers.router)
app.include_router(mirror.router)
app.include_router(projection.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Vintage AI Shop Assistant API"}


@app.get("/api/health")
def health_check():
    """ヘルスチェック: 各外部APIの設定状況を返す"""
    return {
        "status": "ok",
        "mock_mode": os.getenv("MOCK_MODE", "false").lower() == "true",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "shopify_storefront_configured": bool(os.getenv("SHOPIFY_STORE_URL"))
        and bool(os.getenv("SHOPIFY_STOREFRONT_ACCESS_TOKEN")),
        "shopify_admin_configured": bool(os.getenv("SHOPIFY_ADMIN_API_ACCESS_TOKEN")),
        "catalog_loaded": catalog_cache.is_loaded,
        "catalog_product_count": catalog_cache.product_count,
    }
