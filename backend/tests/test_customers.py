"""
顧客API（/api/customers）のテスト（モックモードで実行）
"""

import json
import pytest


@pytest.mark.asyncio
async def test_lookup_not_found(client):
    """存在しないメールで検索すると not_found が返ること"""
    res = await client.get("/api/customers", params={"email": "notexist@example.com"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "not_found"
    assert data["customer"] is None


@pytest.mark.asyncio
async def test_create_customer(client):
    """新規顧客を登録できること"""
    res = await client.post(
        "/api/customers",
        data={
            "name": "テスト花子",
            "email": "hanako@example.com",
            "style_preferences": json.dumps(["かわいい", "Y2K"]),
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    customer = data["customer"]
    assert customer["name"] == "テスト花子"
    assert customer["email"] == "hanako@example.com"
    assert customer["style_preferences"] == ["かわいい", "Y2K"]
    assert customer["is_new"] is True


@pytest.mark.asyncio
async def test_lookup_existing_customer(client):
    """登録済み顧客をメールで検索できること"""
    # まず登録
    await client.post(
        "/api/customers",
        data={
            "name": "検索テスト",
            "email": "lookup@example.com",
            "style_preferences": json.dumps(["ストリート"]),
        },
    )
    # 検索
    res = await client.get("/api/customers", params={"email": "lookup@example.com"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["customer"]["email"] == "lookup@example.com"
    assert data["customer"]["style_preferences"] == ["ストリート"]


@pytest.mark.asyncio
async def test_update_preferences(client):
    """既存顧客の好みタグを更新できること"""
    # 登録
    await client.post(
        "/api/customers",
        data={
            "name": "更新テスト",
            "email": "update@example.com",
            "style_preferences": json.dumps(["アメカジ"]),
        },
    )
    # 好みを更新
    res = await client.post(
        "/api/customers",
        data={
            "name": "更新テスト",
            "email": "update@example.com",
            "style_preferences": json.dumps(["モード", "きれいめ", "80s"]),
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["customer"]["style_preferences"] == ["モード", "きれいめ", "80s"]


@pytest.mark.asyncio
async def test_create_customer_empty_preferences(client):
    """好みタグが空でも登録できること"""
    res = await client.post(
        "/api/customers",
        data={
            "name": "空タグテスト",
            "email": "empty@example.com",
            "style_preferences": "[]",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["customer"]["style_preferences"] == []


@pytest.mark.asyncio
async def test_create_customer_invalid_json_preferences(client):
    """不正なJSON文字列でも落ちずに空配列として扱うこと"""
    res = await client.post(
        "/api/customers",
        data={
            "name": "不正JSON",
            "email": "invalid@example.com",
            "style_preferences": "not-a-json",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["customer"]["style_preferences"] == []


@pytest.mark.asyncio
async def test_lookup_requires_email(client):
    """emailパラメータなしだと422エラーになること"""
    res = await client.get("/api/customers")
    assert res.status_code == 422
