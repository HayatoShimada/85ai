import os
import io
import json
import logging
from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Gemini クライアント初期化
_api_key = os.getenv("GEMINI_API_KEY")
_client = genai.Client(api_key=_api_key) if _api_key else None


class GeminiAnalysisError(Exception):
    """Gemini API 解析中のエラー"""
    pass

# Geminiに期待するJSON出力スキーマをPydanticで定義
class RecommendationItem(BaseModel):
    title: str = Field(description="提案のテーマ（例：ストリート風アプローチ）")
    reason: str = Field(description="提案の理由（ユーザーの好みをどう反映したかを含む）")
    search_keywords: list[str] = Field(description="Shopifyで検索するためのタグやキーワードのリスト")
    category: str = Field(description="提案するアイテムのカテゴリ（トップス、アウターなど）")

class ClothingAnalysis(BaseModel):
    analyzed_outfit: str = Field(description="画像から認識したユーザーの今の服装の特徴（プロンプトの解析結果）")
    detected_style: list[str] = Field(description="画像の服装から推測されるスタイルタグ（例：カジュアル、ストリート、きれいめ）")
    box_ymin: int = Field(description="認識した服のY最小値（0〜1000の正規化座標）")
    box_xmin: int = Field(description="認識した服のX最小値（0〜1000の正規化座標）")
    box_ymax: int = Field(description="認識した服のY最大値（0〜1000の正規化座標）")
    box_xmax: int = Field(description="認識した服のX最大値（0〜1000の正規化座標）")
    recommendations: list[RecommendationItem] = Field(description="異なる数パターンのコーディネート提案（最大3つ）")


def analyze_image_and_get_tags(image_bytes: bytes, user_preferences: list[str] | None = None) -> str:
    """
    画像データとユーザーの好みタグを受け取り、Gemini 3.1 Proで解析して
    Shopifyでの検索キーワードや提案の理由などを返す。JSON文字列として返す。

    Raises:
        GeminiAnalysisError: API呼び出しに失敗した場合
    """
    if not _client:
        raise GeminiAnalysisError("GEMINI_API_KEY が設定されていません")

    try:
        image = Image.open(io.BytesIO(image_bytes))

        # ユーザーの好みをプロンプトに組み込む
        if user_preferences:
            pref_text = "、".join(user_preferences)
            preference_section = f"""
        【ユーザーの好み】
        {pref_text}

        上記の好みを踏まえた上で、提案はユーザーの好みの方向性に沿ったものにしてください。
        提案理由にはユーザーの好みをどう反映したかを含めてください。"""
        else:
            preference_section = ""

        prompt = f"""
        添付した画像の人物が着ている服を分析し、現在着ているメインの服の特徴と、それに合う「古着」のアイテムを複数パターン（最大3つ）提案してください。
        また、画像の服装から推測されるスタイルタグ（カジュアル、ストリート、きれいめ等）を出力してください。
        分析対象とした一番特徴的な服の画像内での位置をバウンディングボックス（0〜1000の相対座標）で出力してください。
        {preference_section}
        出力はJSON形式で行ってください。
        """

        response = _client.models.generate_content(
            model="gemini-3.1-pro",
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ClothingAnalysis,
            ),
        )

        return response.text
    except GeminiAnalysisError:
        raise
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        if "timeout" in str(e).lower() or "deadline" in str(e).lower():
            raise GeminiAnalysisError("AI解析がタイムアウトしました。もう一度お試しください。") from e
        raise GeminiAnalysisError(f"AI解析中にエラーが発生しました（{type(e).__name__}）") from e
