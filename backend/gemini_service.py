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
class ClothingRecommendation(BaseModel):
    reason: str = Field(description="提案の理由")
    search_keywords: list[str] = Field(description="Shopifyで検索するためのタグやキーワードのリスト")
    category: str = Field(description="提案するアイテムのカテゴリ（トップス、ボトムス、アウターなど）")

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
        添付した画像の人物が着ている服を分析し、それに合う「古着」のアイテムを1つ提案してください。
        以下のJSON形式で、Shopifyで検索するためのキーワードを出力してください。
        
        {
          "reason": "今のパンツが太めのデニムなので、オーバーサイズのカレッジロゴスウェットでアメカジ風に合わせるのがおすすめです。",
          "search_keywords": ["スウェット", "オーバーサイズ", "ネイビー", "90s"],
          "category": "トップス"
        }
        """
        
        response = model.generate_content(
            [prompt, image],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ClothingRecommendation
            )
        )
        
        return response.text
    except Exception as e:
        print(f"Error in Gemini API: {e}")
        return '{"reason": "エラーが発生しました", "search_keywords": [], "category": ""}'
