"""顧客管理エンドポイント"""

import os
import json
from fastapi import APIRouter, Form, Query

from customer_service import (
    search_customer_by_email,
    create_customer,
    update_customer_preferences,
)
from mock_service import (
    get_mock_customer,
    create_mock_customer,
    update_mock_customer_preferences,
)

router = APIRouter()


def is_mock_mode() -> bool:
    return os.getenv("MOCK_MODE", "false").lower() == "true"


@router.get("/api/customers")
async def lookup_customer(email: str = Query(...)):
    """メールアドレスで既存顧客を検索し、保存済みの好みタグを返す"""
    if is_mock_mode():
        customer = get_mock_customer(email)
        if customer:
            return {"status": "success", "customer": customer}
        return {"status": "not_found", "customer": None}

    customer = await search_customer_by_email(email)
    if customer:
        return {"status": "success", "customer": customer}
    return {"status": "not_found", "customer": None}


@router.post("/api/customers")
async def register_customer(
    name: str = Form(...),
    email: str = Form(...),
    style_preferences: str = Form(default="[]"),
    body_measurements: str = Form(default=""),
):
    """顧客を登録（または既存顧客の好みを更新）し、好みタグと体型情報をShopifyに保存する"""
    try:
        preferences = json.loads(style_preferences)
        if not isinstance(preferences, list):
            preferences = []
    except json.JSONDecodeError:
        preferences = []

    # 体型情報をパース（空文字列やnullは None に）
    measurements = None
    if body_measurements and body_measurements.strip():
        try:
            measurements = json.loads(body_measurements)
            if not isinstance(measurements, dict):
                measurements = None
        except json.JSONDecodeError:
            measurements = None

    if is_mock_mode():
        existing = get_mock_customer(email)
        if existing:
            updated = update_mock_customer_preferences(email, preferences)
            return {"status": "success", "customer": updated}
        customer = create_mock_customer(name, email, preferences)
        return {"status": "success", "customer": customer}

    # 既存顧客を検索
    existing = await search_customer_by_email(email)
    if existing:
        updated = await update_customer_preferences(existing["id"], preferences, measurements)
        if updated:
            return {"status": "success", "customer": updated}
        return {"status": "error", "message": "Failed to update customer preferences"}

    # 新規作成
    customer = await create_customer(name, email, preferences, measurements)
    if customer:
        return {"status": "success", "customer": customer}
    return {"status": "error", "message": "Failed to create customer"}
