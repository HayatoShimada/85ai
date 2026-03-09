from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

import os

from logging_config import setup_logging
from routers import analyze, customers, mirror, projection

load_dotenv()
setup_logging()

app = FastAPI(title="Vintage AI Shop Assistant API")

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
    }
