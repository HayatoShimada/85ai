from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

import json
from gemini_service import analyze_image_and_get_tags
from shopify_service import search_products_on_shopify
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Vintage AI Shop Assistant API")

# フロントエンドからのAPIアクセスを許可するCORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Vintage AI Shop Assistant API"}

@app.post("/api/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """
    アップロードされた画像を受け取り、Geminiを通してShopify検索タグを生成する
    """
    image_bytes = await file.read()
    json_str_response = analyze_image_and_get_tags(image_bytes)
    
    try:
        # 文字列として返ってきたJSONを辞書型に変換
        result_dict = json.loads(json_str_response)
        
        # Shopifyで商品を検索（複数の提案パターンごとに実行）
        recommendations = result_dict.get("recommendations", [])
        for rec in recommendations:
            keywords = rec.get("search_keywords", [])
            if keywords:
                shopify_res = search_products_on_shopify(keywords)
                rec["shopify_products"] = shopify_res.get("products", [])
            else:
                rec["shopify_products"] = []
            
        return {"status": "success", "data": result_dict}
    except json.JSONDecodeError:
        return {"status": "error", "message": "Failed to parse Gemini response as JSON", "raw_response": json_str_response}

