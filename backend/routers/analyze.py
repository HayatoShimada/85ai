"""画像解析エンドポイント"""

import os
import json
import logging
from fastapi import APIRouter, UploadFile, File, Form

logger = logging.getLogger(__name__)

from gemini_service import analyze_image_and_get_tags, GeminiAnalysisError
from catalog_service import catalog_cache
from customer_service import search_customer_by_email
from mock_service import get_mock_analysis

router = APIRouter()


def is_mock_mode() -> bool:
    return os.getenv("MOCK_MODE", "false").lower() == "true"


@router.post("/api/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    preferences: str = Form(default="[]"),
    customer_id: str = Form(default=""),
    body_measurements: str = Form(default=""),
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

    # 体型情報をパース
    measurements = None
    if body_measurements and body_measurements.strip():
        try:
            measurements = json.loads(body_measurements)
            if not isinstance(measurements, dict):
                measurements = None
        except json.JSONDecodeError:
            measurements = None

    image_bytes = await file.read()

    # モックモード
    if is_mock_mode():
        result_dict = await get_mock_analysis(user_preferences)
        return {"status": "success", "data": result_dict}

    # カタログテキストを取得 (キャッシュ済み)
    catalog_text = catalog_cache.get_gemini_catalog() if catalog_cache.is_loaded else ""

    # 実API呼び出し
    try:
        json_str_response = analyze_image_and_get_tags(
            image_bytes, user_preferences, measurements, catalog_text
        )
    except GeminiAnalysisError as e:
        return {"status": "error", "message": str(e)}

    try:
        result_dict = json.loads(json_str_response)
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": "AI解析結果の読み取りに失敗しました。もう一度お試しください。",
        }

    # カタログから商品データを参照 (Shopify検索不要)
    recommendations = result_dict.get("recommendations", [])
    for rec in recommendations:
        product_ids = rec.get("product_ids", [])
        rec["shopify_products"] = catalog_cache.get_products_by_ids(product_ids)

    return {"status": "success", "data": result_dict}
