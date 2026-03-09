"""画像解析エンドポイント"""

import os
import json
import asyncio
import logging
from fastapi import APIRouter, UploadFile, File, Form

logger = logging.getLogger(__name__)

from gemini_service import analyze_image_and_get_tags, GeminiAnalysisError
from shopify_service import search_products_on_shopify
from mock_service import get_mock_analysis

router = APIRouter()


def is_mock_mode() -> bool:
    return os.getenv("MOCK_MODE", "false").lower() == "true"


@router.post("/api/analyze")
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
        result_dict = await get_mock_analysis(user_preferences)
        return {"status": "success", "data": result_dict}

    # 実API呼び出し
    try:
        json_str_response = analyze_image_and_get_tags(image_bytes, user_preferences)
    except GeminiAnalysisError as e:
        return {"status": "error", "message": str(e)}

    try:
        result_dict = json.loads(json_str_response)
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": "AI解析結果の読み取りに失敗しました。もう一度お試しください。",
        }

    # Shopifyで商品を検索（複数の提案パターンを並列実行）
    # 部分成功: Shopify検索が失敗しても解析結果は返す
    shopify_errors = []
    recommendations = result_dict.get("recommendations", [])

    async def _search_for_rec(rec):
        keywords = rec.get("search_keywords", [])
        if not keywords:
            rec["shopify_products"] = []
            return
        try:
            shopify_res = await search_products_on_shopify(keywords)
            rec["shopify_products"] = shopify_res.get("products", [])
            if shopify_res.get("status") == "error":
                shopify_errors.append(rec.get("title", "不明"))
        except Exception as e:
            logger.error(f"Shopify search error for {keywords}: {e}")
            rec["shopify_products"] = []
            shopify_errors.append(rec.get("title", "不明"))

    await asyncio.gather(*[_search_for_rec(rec) for rec in recommendations])

    response = {"status": "success", "data": result_dict}
    if shopify_errors:
        response["warning"] = f"一部の商品検索に失敗しました: {', '.join(shopify_errors)}"
    return response
