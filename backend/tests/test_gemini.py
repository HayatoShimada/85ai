"""
gemini_service のユニットテスト
Pydanticスキーマの検証とプロンプト生成ロジックのテスト
"""

import json
from gemini_service import ClothingAnalysis, RecommendationItem


def test_clothing_analysis_schema_valid():
    """正常なJSONがClothingAnalysisモデルにパースできること"""
    data = {
        "analyzed_outfit": "テスト用の服装説明",
        "detected_style": ["カジュアル", "ストリート"],
        "box_ymin": 100,
        "box_xmin": 200,
        "box_ymax": 800,
        "box_xmax": 700,
        "recommendations": [
            {
                "title": "テスト提案",
                "reason": "テスト理由",
                "product_ids": [1, 2],
                "category": "トップス",
            }
        ],
    }
    analysis = ClothingAnalysis(**data)
    assert analysis.analyzed_outfit == "テスト用の服装説明"
    assert analysis.detected_style == ["カジュアル", "ストリート"]
    assert analysis.box_ymin == 100
    assert len(analysis.recommendations) == 1
    assert analysis.recommendations[0].title == "テスト提案"


def test_clothing_analysis_schema_multiple_recommendations():
    """最大3パターンの提案をパースできること"""
    recs = [
        {
            "title": f"提案{i}",
            "reason": f"理由{i}",
            "product_ids": [i + 1],
            "category": "トップス",
        }
        for i in range(3)
    ]
    data = {
        "analyzed_outfit": "テスト",
        "detected_style": [],
        "box_ymin": 0,
        "box_xmin": 0,
        "box_ymax": 1000,
        "box_xmax": 1000,
        "recommendations": recs,
    }
    analysis = ClothingAnalysis(**data)
    assert len(analysis.recommendations) == 3


def test_recommendation_item_schema():
    """RecommendationItemが正しくパースできること"""
    item = RecommendationItem(
        title="ストリート風",
        reason="かっこいいの好みに合わせて",
        product_ids=[1, 2, 3],
        category="アウター",
    )
    assert item.title == "ストリート風"
    assert len(item.product_ids) == 3
    assert item.category == "アウター"


def test_clothing_analysis_json_roundtrip():
    """ClothingAnalysisをJSON化→復元しても同値であること"""
    data = {
        "analyzed_outfit": "ラウンドトリップテスト",
        "detected_style": ["モード"],
        "box_ymin": 50,
        "box_xmin": 100,
        "box_ymax": 900,
        "box_xmax": 850,
        "recommendations": [
            {
                "title": "テスト",
                "reason": "理由",
                "product_ids": [1],
                "category": "トップス",
            }
        ],
    }
    analysis = ClothingAnalysis(**data)
    json_str = analysis.model_dump_json()
    restored = ClothingAnalysis.model_validate_json(json_str)
    assert restored.analyzed_outfit == analysis.analyzed_outfit
    assert restored.detected_style == analysis.detected_style
    assert restored.box_ymin == analysis.box_ymin


def test_gemini_analysis_error():
    """GeminiAnalysisError が正しく生成されること"""
    from gemini_service import GeminiAnalysisError
    err = GeminiAnalysisError("テストエラー")
    assert str(err) == "テストエラー"
    assert isinstance(err, Exception)
