"""
shopify_service のユニットテスト
APIクレデンシャル未設定時の挙動とレスポンスパースのテスト
"""

import os
from unittest.mock import patch, MagicMock
from shopify_service import search_products_on_shopify


def test_missing_credentials_returns_error():
    """Shopifyクレデンシャルが未設定の場合、エラーを返すこと"""
    with patch.dict(os.environ, {}, clear=True):
        result = search_products_on_shopify(["テスト"])
        assert result["status"] == "error"
        assert result["products"] == []


def test_empty_keywords_returns_empty():
    """空のキーワードリストでも落ちないこと"""
    with patch.dict(os.environ, {}, clear=True):
        result = search_products_on_shopify([])
        assert result["products"] == []


def test_successful_response_parsing():
    """正常なShopifyレスポンスをパースできること"""
    mock_shopify_response = {
        "data": {
            "search": {
                "edges": [
                    {
                        "node": {
                            "id": "gid://shopify/Product/1",
                            "title": "テスト商品",
                            "description": "テスト説明文です。" * 10,
                            "availableForSale": True,
                            "priceRange": {
                                "minVariantPrice": {
                                    "amount": "3500.0",
                                    "currencyCode": "JPY",
                                }
                            },
                            "images": {
                                "edges": [
                                    {"node": {"url": "https://example.com/img.jpg"}}
                                ]
                            },
                            "onlineStoreUrl": "https://example.com/products/test",
                        }
                    },
                    {
                        "node": {
                            "id": "gid://shopify/Product/2",
                            "title": "売り切れ商品",
                            "description": "これは売り切れ",
                            "availableForSale": False,
                            "priceRange": {
                                "minVariantPrice": {
                                    "amount": "5000.0",
                                    "currencyCode": "JPY",
                                }
                            },
                            "images": {"edges": []},
                            "onlineStoreUrl": "",
                        }
                    },
                ]
            }
        }
    }

    mock_response = MagicMock()
    mock_response.json.return_value = mock_shopify_response
    mock_response.raise_for_status = MagicMock()

    with patch.dict(
        os.environ,
        {
            "SHOPIFY_STORE_URL": "test.myshopify.com",
            "SHOPIFY_STOREFRONT_ACCESS_TOKEN": "test-token",
        },
    ):
        with patch("shopify_service.requests.post", return_value=mock_response):
            result = search_products_on_shopify(["テスト"])

    assert result["status"] == "success"
    # availableForSale=False の商品はフィルタされること
    assert len(result["products"]) == 1
    product = result["products"][0]
    assert product["title"] == "テスト商品"
    assert product["price"] == "3500.0 JPY"
    assert product["image_url"] == "https://example.com/img.jpg"


def test_api_error_handling():
    """Shopify APIがエラーを返した場合に安全に処理されること"""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("API Error")

    with patch.dict(
        os.environ,
        {
            "SHOPIFY_STORE_URL": "test.myshopify.com",
            "SHOPIFY_STOREFRONT_ACCESS_TOKEN": "test-token",
        },
    ):
        with patch("shopify_service.requests.post", return_value=mock_response):
            result = search_products_on_shopify(["テスト"])

    assert result["status"] == "error"
    assert result["products"] == []
