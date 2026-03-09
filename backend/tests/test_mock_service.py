"""mock_service のテスト"""

import pytest
from mock_service import (
    get_mock_analysis,
    get_mock_customer,
    create_mock_customer,
    update_mock_customer_preferences,
    MOCK_CUSTOMER_DB,
)


@pytest.fixture(autouse=True)
def reset_mock_db():
    """テストごとに MOCK_CUSTOMER_DB をリセット"""
    MOCK_CUSTOMER_DB.clear()
    yield
    MOCK_CUSTOMER_DB.clear()


@pytest.mark.asyncio
async def test_mock_analysis_without_preferences():
    """好みなしで基本解析結果が返る"""
    result = await get_mock_analysis()
    assert "analyzed_outfit" in result
    assert "recommendations" in result
    assert len(result["recommendations"]) == 3


@pytest.mark.asyncio
async def test_mock_analysis_with_preferences():
    """好みテキストが結果に反映される"""
    result = await get_mock_analysis(["ストリート", "90s"])
    assert "ストリート" in result["analyzed_outfit"]
    assert "90s" in result["analyzed_outfit"]


def test_mock_customer_crud_cycle():
    """作成 → 検索 → 更新のサイクルテスト"""
    customer = create_mock_customer("テスト太郎", "test@example.com", ["カジュアル"])
    assert customer["name"] == "テスト太郎"
    assert customer["is_new"] is True

    found = get_mock_customer("test@example.com")
    assert found is not None
    assert found["email"] == "test@example.com"

    updated = update_mock_customer_preferences("test@example.com", ["ストリート", "90s"])
    assert updated["style_preferences"] == ["ストリート", "90s"]
    assert updated["is_new"] is False


def test_mock_customer_not_found():
    """未登録メールで None が返る"""
    result = get_mock_customer("nonexistent@example.com")
    assert result is None


def test_mock_customer_id_uniqueness():
    """複数作成時に ID がユニーク"""
    c1 = create_mock_customer("A", "a@test.com", [])
    c2 = create_mock_customer("B", "b@test.com", [])
    assert c1["id"] != c2["id"]
