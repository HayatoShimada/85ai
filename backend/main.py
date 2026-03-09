from fastapi import FastAPI, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

import os
import json
from gemini_service import analyze_image_and_get_tags
from shopify_service import search_products_on_shopify
from customer_service import (
    search_customer_by_email,
    create_customer,
    update_customer_preferences,
)
from mock_service import (
    get_mock_analysis,
    get_mock_customer,
    create_mock_customer,
    update_mock_customer_preferences,
)

load_dotenv()

app = FastAPI(title="Vintage AI Shop Assistant API")

# フロントエンドからのAPIアクセスを許可するCORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def is_mock_mode() -> bool:
    return os.getenv("MOCK_MODE", "false").lower() == "true"


@app.get("/")
def read_root():
    return {"message": "Welcome to the Vintage AI Shop Assistant API"}


@app.get("/api/health")
def health_check():
    """ヘルスチェック: 各外部APIの設定状況を返す"""
    return {
        "status": "ok",
        "mock_mode": is_mock_mode(),
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "shopify_storefront_configured": bool(os.getenv("SHOPIFY_STORE_URL"))
        and bool(os.getenv("SHOPIFY_STOREFRONT_ACCESS_TOKEN")),
        "shopify_admin_configured": bool(os.getenv("SHOPIFY_ADMIN_API_ACCESS_TOKEN")),
    }


@app.post("/api/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    preferences: str = Form(default="[]"),
    customer_id: str = Form(default=""),
):
    """
    アップロードされた画像とユーザーの好みタグを受け取り、
    Geminiを通してShopify検索タグを生成し、商品を検索する
    """
    # 好みタグをパース
    try:
        user_preferences = json.loads(preferences)
        if not isinstance(user_preferences, list):
            user_preferences = []
    except json.JSONDecodeError:
        user_preferences = []

    image_bytes = await file.read()

    # モックモード
    if is_mock_mode():
        result_dict = get_mock_analysis(user_preferences)
        return {"status": "success", "data": result_dict}

    # 実API呼び出し
    json_str_response = analyze_image_and_get_tags(image_bytes, user_preferences)

    try:
        result_dict = json.loads(json_str_response)

        # Shopifyで商品を検索（複数の提案パターンごとに実行）
        recommendations = result_dict.get("recommendations", [])
        for rec in recommendations:
            keywords = rec.get("search_keywords", [])
            if keywords:
                shopify_res = search_products_on_shopify(keywords)
                rec["shopify_products"] = shopify_res.get("products", [])
            else:
                rec["shopify_products"] = []

        return {"status": "success", "data": result_dict}
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": "Failed to parse Gemini response as JSON",
            "raw_response": json_str_response,
        }


@app.get("/api/customers")
async def lookup_customer(email: str = Query(...)):
    """
    メールアドレスで既存顧客を検索し、保存済みの好みタグを返す
    """
    if is_mock_mode():
        customer = get_mock_customer(email)
        if customer:
            return {"status": "success", "customer": customer}
        return {"status": "not_found", "customer": None}

    customer = search_customer_by_email(email)
    if customer:
        return {"status": "success", "customer": customer}
    return {"status": "not_found", "customer": None}


@app.post("/api/customers")
async def register_customer(
    name: str = Form(...),
    email: str = Form(...),
    style_preferences: str = Form(default="[]"),
):
    """
    顧客を登録（または既存顧客の好みを更新）し、好みタグをShopifyに保存する
    """
    try:
        preferences = json.loads(style_preferences)
        if not isinstance(preferences, list):
            preferences = []
    except json.JSONDecodeError:
        preferences = []

    if is_mock_mode():
        existing = get_mock_customer(email)
        if existing:
            updated = update_mock_customer_preferences(email, preferences)
            return {"status": "success", "customer": updated}
        customer = create_mock_customer(name, email, preferences)
        return {"status": "success", "customer": customer}

    # 既存顧客を検索
    existing = search_customer_by_email(email)
    if existing:
        # 好みを更新
        updated = update_customer_preferences(existing["id"], preferences)
        if updated:
            return {"status": "success", "customer": updated}
        return {"status": "error", "message": "Failed to update customer preferences"}

    # 新規作成
    customer = create_customer(name, email, preferences)
    if customer:
        return {"status": "success", "customer": customer}
    return {"status": "error", "message": "Failed to create customer"}
