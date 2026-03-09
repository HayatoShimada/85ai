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
    product_ids: list[int] = Field(description="カタログから選んだ商品のID（最大3つ）")
    category: str = Field(description="提案するアイテムのカテゴリ（トップス、アウターなど）")

class ClothingAnalysis(BaseModel):
    analyzed_outfit: str = Field(description="画像から認識したユーザーの今の服装の特徴（プロンプトの解析結果）")
    detected_style: list[str] = Field(description="画像の服装から推測されるスタイルタグ（例：カジュアル、ストリート、きれいめ）")
    box_ymin: int = Field(description="認識した服のY最小値（0〜1000の正規化座標）")
    box_xmin: int = Field(description="認識した服のX最小値（0〜1000の正規化座標）")
    box_ymax: int = Field(description="認識した服のY最大値（0〜1000の正規化座標）")
    box_xmax: int = Field(description="認識した服のX最大値（0〜1000の正規化座標）")
    recommendations: list[RecommendationItem] = Field(description="異なる数パターンのコーディネート提案（最大3つ）")


def analyze_image_and_get_tags(image_bytes: bytes, user_preferences: list[str] | None = None, body_measurements: dict | None = None, catalog_text: str = "") -> str:
    """
    画像データとユーザーの好みタグ・体型情報を受け取り、Geminiで解析して
    カタログ内の商品IDや提案の理由などを返す。JSON文字列として返す。

    catalog_text が渡された場合、カタログ内の商品IDで提案する。

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

        # 体型情報をプロンプトに組み込む
        if body_measurements:
            parts = []
            if body_measurements.get("height"):
                parts.append(f"身長: {body_measurements['height']}cm")
            if body_measurements.get("shoulder_width"):
                parts.append(f"肩幅: {body_measurements['shoulder_width']}cm")
            if body_measurements.get("chest"):
                parts.append(f"胸囲: {body_measurements['chest']}cm")
            if body_measurements.get("waist"):
                parts.append(f"ウエスト: {body_measurements['waist']}cm")
            if body_measurements.get("weight"):
                parts.append(f"体重: {body_measurements['weight']}kg")
            if parts:
                body_section = f"""
        【体型情報】
        {', '.join(parts)}

        上記の体型に合うサイズ感の商品を優先的に提案してください。
        提案理由にはサイズ適合についても言及してください。"""
            else:
                body_section = ""
        else:
            body_section = ""

        # カタログセクション
        if catalog_text:
            catalog_section = f"""
        【店舗の商品カタログ】
        以下は当店の全商品リスト（ID\\tカテゴリ\\t商品名\\t属性）です。
        提案には必ずこのカタログ内の商品IDをproduct_idsに指定してください。
        カタログにない商品は提案しないでください。

        {catalog_text}
        """
        else:
            catalog_section = ""

        prompt = f"""
        添付した画像の人物が着ている服を分析し、現在着ているメインの服の特徴と、それに合う「古着」のアイテムを複数パターン（最大3つ）提案してください。
        また、画像の服装から推測されるスタイルタグ（カジュアル、ストリート、きれいめ等）を出力してください。
        分析対象とした一番特徴的な服の画像内での位置をバウンディングボックス（0〜1000の相対座標）で出力してください。
        各提案にはカタログから最も合う商品のIDをproduct_idsに最大3つ含めてください。
        {catalog_section}
        {preference_section}
        {body_section}
        出力はJSON形式で行ってください。
        """

        response = _client.models.generate_content(
            model="gemini-3.1-pro-preview",
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
