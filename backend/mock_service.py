"""
モックサービス - APIキーなしで全フローの動作確認・UI開発を行うためのダミーデータ
環境変数 MOCK_MODE=true で有効化
"""

import asyncio
import random

MOCK_ANALYSIS = {
    "analyzed_outfit": "ダークブルーのストレートデニムに、ホワイトの無地Tシャツというシンプルなアメカジスタイル。足元はコンバースのオールスターで、全体的にクリーンで定番的なコーディネートです。",
    "detected_style": ["カジュアル", "アメカジ", "シンプル"],
    "box_ymin": 150,
    "box_xmin": 250,
    "box_ymax": 700,
    "box_xmax": 750,
    "recommendations": [
        {
            "title": "アメカジ王道スタイル",
            "reason": "ストレートデニムに合わせて、オーバーサイズのカレッジロゴスウェットでアメカジ感を強化。「かっこいい」の好みにマッチした力強いスタイリングです。",
            "search_keywords": ["スウェット", "オーバーサイズ", "カレッジ", "90s"],
            "category": "トップス",
            "shopify_products": [
                {
                    "id": "mock-product-1",
                    "title": "90s Champion リバースウィーブ スウェット ネイビー",
                    "description": "90年代のチャンピオン製リバースウィーブ。ややオーバーサイズのシルエットで、カレッジロゴがプリントされた人気のヴィンテージアイテムです。",
                    "price": "4,500 JPY",
                    "image_url": "https://placehold.co/400x400/1e3a5f/ffffff?text=Champion+Sweat",
                    "url": "#"
                },
                {
                    "id": "mock-product-2",
                    "title": "80s USA製 カレッジプリント スウェット グレー",
                    "description": "アメリカの大学名がアーチ状にプリントされたクラシックなカレッジスウェット。程よい色褪せがヴィンテージ感を演出。",
                    "price": "3,800 JPY",
                    "image_url": "https://placehold.co/400x400/374151/ffffff?text=College+Sweat",
                    "url": "#"
                }
            ]
        },
        {
            "title": "ストリートMIXスタイル",
            "reason": "シンプルなデニムコーデにストリート感をプラス。コーチジャケットやナイロンジャケットを羽織ることで、一気にこなれた雰囲気に。",
            "search_keywords": ["コーチジャケット", "ナイロン", "ストリート"],
            "category": "アウター",
            "shopify_products": [
                {
                    "id": "mock-product-3",
                    "title": "90s コーチジャケット ブラック ワンポイント刺繍",
                    "description": "90年代のコーチジャケット。胸元にワンポイント刺繍が入ったシンプルなデザイン。薄手で春秋に最適。",
                    "price": "3,200 JPY",
                    "image_url": "https://placehold.co/400x400/111827/ffffff?text=Coach+Jacket",
                    "url": "#"
                }
            ]
        },
        {
            "title": "きれいめカジュアル",
            "reason": "デニムを活かしつつ、シャツやニットで大人っぽくまとめるアプローチ。ナチュラルな印象を加えたい方におすすめです。",
            "search_keywords": ["シャツ", "チェック", "ネルシャツ"],
            "category": "トップス",
            "shopify_products": [
                {
                    "id": "mock-product-4",
                    "title": "ヴィンテージ ネルシャツ レッド×ブラック チェック",
                    "description": "しっかりとした厚みのあるフランネル生地。赤と黒のチェック柄がアメカジスタイルの定番。",
                    "price": "2,800 JPY",
                    "image_url": "https://placehold.co/400x400/7f1d1d/ffffff?text=Flannel+Shirt",
                    "url": "#"
                },
                {
                    "id": "mock-product-5",
                    "title": "90s コットンニット ベージュ クルーネック",
                    "description": "ざっくりとした編み目が特徴のコットンニット。ナチュラルなベージュカラーで合わせやすい一着。",
                    "price": "3,500 JPY",
                    "image_url": "https://placehold.co/400x400/92400e/ffffff?text=Cotton+Knit",
                    "url": "#"
                }
            ]
        }
    ]
}

MOCK_CUSTOMER_DB = {}


async def get_mock_analysis(preferences: list[str] | None = None) -> dict:
    """モック解析結果を返す。好みタグがあれば結果テキストに反映する。"""
    result = dict(MOCK_ANALYSIS)
    if preferences:
        pref_text = "・".join(preferences)
        result["analyzed_outfit"] = (
            f"{MOCK_ANALYSIS['analyzed_outfit']}\n"
            f"お客様の好み（{pref_text}）を考慮した提案を行います。"
        )
    # 少し待機して実際のAPI呼び出しをシミュレート
    await asyncio.sleep(random.uniform(0.5, 1.5))
    return result


def get_mock_customer(email: str) -> dict | None:
    """モック顧客検索"""
    return MOCK_CUSTOMER_DB.get(email)


def create_mock_customer(name: str, email: str, preferences: list[str]) -> dict:
    """モック顧客作成"""
    customer = {
        "id": f"mock-customer-{len(MOCK_CUSTOMER_DB) + 1}",
        "name": name,
        "email": email,
        "style_preferences": preferences,
        "is_new": True,
    }
    MOCK_CUSTOMER_DB[email] = customer
    return customer


def update_mock_customer_preferences(email: str, preferences: list[str]) -> dict | None:
    """モック顧客の好み更新"""
    customer = MOCK_CUSTOMER_DB.get(email)
    if customer:
        customer["style_preferences"] = preferences
        customer["is_new"] = False
    return customer
