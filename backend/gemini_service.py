import os
import io
import google.generativeai as genai
from PIL import Image
from pydantic import BaseModel, Field

# APIキーの設定
# main.py側でload_dotenv()が呼ばれている前提
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Geminiに期待するJSON出力スキーマをPydanticで定義
class RecommendationItem(BaseModel):
    title: str = Field(description="提案のテーマ（例：ストリート風アプローチ）")
    reason: str = Field(description="提案の理由")
    search_keywords: list[str] = Field(description="Shopifyで検索するためのタグやキーワードのリスト")
    category: str = Field(description="提案するアイテムのカテゴリ（トップス、アウターなど）")

class ClothingAnalysis(BaseModel):
    analyzed_outfit: str = Field(description="画像から認識したユーザーの今の服装の特徴（プロンプトの解析結果）")
    box_ymin: int = Field(description="認識した服のY最小値（0〜1000の正規化座標）")
    box_xmin: int = Field(description="認識した服のX最小値（0〜1000の正規化座標）")
    box_ymax: int = Field(description="認識した服のY最大値（0〜1000の正規化座標）")
    box_xmax: int = Field(description="認識した服のX最大値（0〜1000の正規化座標）")
    recommendations: list[RecommendationItem] = Field(description="異なる数パターンのコーディネート提案（最大3つ）")

def analyze_image_and_get_tags(image_bytes: bytes) -> str:
    """
    画像データを受け取り、Gemini 2.5 Flashで解析して
    Shopify検索用のキーワードをJSON文字列として返す関数
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        # モデルの初期化 (高速な2.5 Flashモデルを使用)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        prompt = """
        添付した画像の人物が着ている服を分析し、現在着ているメインの服の特徴と、それに合う「古着」のアイテムを複数パターン（最大3つ）提案してください。
        また、分析対象とした一番特徴的な服の画像内での位置をバウンディングボックス（0〜1000の相対座標）で出力してください。
        出力はJSON形式で行ってください。
        """
        
        response = model.generate_content(
            [prompt, image],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ClothingAnalysis
            )
        )
        
        return response.text
    except Exception as e:
        print(f"Error in Gemini API: {e}")
        return '{"analyzed_outfit": "エラーが発生しました", "box_ymin": 0, "box_xmin": 0, "box_ymax": 1000, "box_xmax": 1000, "recommendations": []}'
