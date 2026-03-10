"""
Shopify商品メタデータ正規化スクリプト (バッチ処理版)

- productType を productCategory.name に統一
- tags を Gemini でバッチ生成
- カスタムメタフィールド (brand, style, era, features) を設定

使い方:
  python3 tag_products.py                # ドライラン (未処理の商品のみ)
  python3 tag_products.py --apply        # 実際に更新 (未処理の商品のみ)
  python3 tag_products.py --apply --id gid://shopify/Product/xxx  # 特定商品
  python3 tag_products.py --apply --force          # 全商品再処理 (処理済みも含む)
  python3 tag_products.py --apply --with-images    # 画像込み (遅い)
  python3 tag_products.py --batch-size 5           # バッチサイズ変更

処理済み判定: custom:tagged_at メタフィールドの有無で判断。
新商品追加後は --apply だけで未処理商品のみ処理される。
"""

import os
import sys
import json
import time
import argparse
import io
from datetime import datetime, timezone
import httpx
from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# --- 設定 ---
ADMIN_API_VERSION = "2026-01"
GEMINI_MODEL = "gemini-2.5-flash"
RATE_LIMIT_DELAY = 2
DEFAULT_BATCH_SIZE = 10

# --- タグ生成用カテゴリ定義 ---
TAG_TAXONOMY = """
## tags用カテゴリ (複数選択可、該当するもの全て付与)

### 詳細カテゴリ
長袖シャツ, 半袖シャツ, ボタンダウン, バンドカラー, オープンカラー, ネルシャツ,
ドレスシャツ, ワークシャツ, ウエスタンシャツ, アロハシャツ, ラガーシャツ,
クルーネック, Vネック, タートルネック, モックネック, ヘンリーネック,
テーラードジャケット, ブレザー, ライダース, MA-1, M-65, コーチジャケット,
トレンチコート, ステンカラーコート, ダッフルコート, ピーコート,
チノパン, カーゴパンツ, スラックス, ジョガーパンツ, ワイドパンツ

### 素材 (日本語+英語の両方)
コットン, Cotton, ウール, Wool, リネン, Linen, ナイロン, Nylon,
ポリエステル, Polyester, フランネル, Flannel, デニム, Denim,
レザー, Leather, スウェード, Suede, フリース, Fleece,
コーデュロイ, Corduroy, ツイード, Tweed, シルク, Silk,
レーヨン, Rayon, ベロア, Velour, ゴアテックス, Gore-Tex

### スタイル
カジュアル, ワーク, ミリタリー, アウトドア, ストリート, ドレス,
クラシック, モード, アメカジ, プレッピー, スポーティ, ナチュラル,
きれいめ, ロック, グランジ, ノームコア

### 色
ブラック, ホワイト, グレー, ネイビー, ブルー, レッド, グリーン,
ブラウン, ベージュ, カーキ, オリーブ, バーガンディ, イエロー,
オレンジ, ピンク, パープル, マルチカラー

### 柄
無地, チェック柄, ストライプ, ボーダー, ドット, 花柄,
カモフラ柄, ペイズリー, アーガイル, ヘリンボーン, 総柄

### 年代
60s, 70s, 80s, 90s, Y2K, ヴィンテージ, レトロ, ミリタリーサープラス

### 特徴
オーバーサイズ, ビッグシルエット, スリムフィット, レギュラーフィット,
ヘビーウェイト, ライトウェイト, 裏起毛, 中綿入り, ライナー付き,
ダブルブレスト, シングルブレスト, ジップアップ
"""


# --- Gemini スキーマ ---
class ProductTagsItem(BaseModel):
    """1商品分のタグ情報"""
    product_index: int = Field(description="商品の番号 (0始まり)")
    category_tags: list[str] = Field(description="詳細カテゴリタグ")
    material_tags: list[str] = Field(description="素材タグ (日本語+英語)")
    style_tags: list[str] = Field(description="スタイルタグ")
    color_tags: list[str] = Field(description="色・柄タグ")
    brand: str = Field(description="ブランド名 (不明なら空文字)")
    era_tags: list[str] = Field(description="年代・時代タグ")
    feature_tags: list[str] = Field(description="特徴タグ")
    size_info: str = Field(description="サイズ情報 (S/M/L/XL/XXL等。不明なら空文字)")


class BatchProductTags(BaseModel):
    """バッチ処理結果"""
    products: list[ProductTagsItem] = Field(description="各商品のタグ情報")


# --- Shopify Admin API ---
def get_shopify_config():
    url = os.getenv("SHOPIFY_STORE_URL")
    token = os.getenv("SHOPIFY_ADMIN_API_ACCESS_TOKEN")
    if not url or not token:
        print("ERROR: SHOPIFY_STORE_URL / SHOPIFY_ADMIN_API_ACCESS_TOKEN が未設定")
        sys.exit(1)
    return (
        f"https://{url}/admin/api/{ADMIN_API_VERSION}/graphql.json",
        {"Content-Type": "application/json", "X-Shopify-Access-Token": token},
    )


def fetch_all_products(endpoint, headers):
    """ページネーションで全商品を取得"""
    products = []
    cursor = None
    while True:
        after = f', after: "{cursor}"' if cursor else ""
        query = f"""
        {{
          products(first: 50{after}) {{
            edges {{
              node {{
                id
                title
                description
                handle
                productType
                tags
                status
                productCategory {{
                  productTaxonomyNode {{ id name fullName }}
                }}
                variants(first: 10) {{
                  edges {{
                    node {{
                      title
                      price
                      selectedOptions {{ name value }}
                    }}
                  }}
                }}
                images(first: 5) {{
                  edges {{
                    node {{ url width height }}
                  }}
                }}
                taggedAt: metafield(namespace: "custom", key: "tagged_at") {{
                  value
                }}
              }}
            }}
            pageInfo {{ hasNextPage endCursor }}
          }}
        }}
        """
        with httpx.Client(timeout=30) as client:
            r = client.post(endpoint, headers=headers, json={"query": query})
        r.raise_for_status()
        data = r.json()
        if "errors" in data:
            print(f"GraphQL errors: {data['errors']}")
            break
        edges = data["data"]["products"]["edges"]
        products.extend([e["node"] for e in edges])
        page_info = data["data"]["products"]["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]
    return products


def update_product_full(endpoint, headers, product_id, product_type, tags, metafields):
    """商品の productType, tags, metafields を更新 (2段階: productUpdate + metafieldsSet)"""
    # 1. productType + tags を productUpdate で更新
    mutation_product = """
    mutation UpdateProduct($input: ProductInput!) {
      productUpdate(input: $input) {
        product { id title productType tags }
        userErrors { field message }
      }
    }
    """
    input_data = {
        "id": product_id,
        "productType": product_type,
        "tags": tags,
    }
    payload = {"query": mutation_product, "variables": {"input": input_data}}
    with httpx.Client(timeout=15) as client:
        r = client.post(endpoint, headers=headers, json=payload)
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        print(f"    ❌ GraphQLエラー: {data['errors']}")
        return False
    errors = data.get("data", {}).get("productUpdate", {}).get("userErrors", [])
    if errors:
        print(f"    ❌ productUpdate エラー: {errors}")
        return False

    # 2. metafields を metafieldsSet で更新 (ownerId方式)
    if not metafields:
        return True

    mutation_mf = """
    mutation metafieldsSet($metafields: [MetafieldsSetInput!]!) {
      metafieldsSet(metafields: $metafields) {
        metafields { id }
        userErrors { field message }
      }
    }
    """
    mf_inputs = []
    for mf in metafields:
        mf_inputs.append({
            "ownerId": product_id,
            "namespace": mf["namespace"],
            "key": mf["key"],
            "type": mf["type"],
            "value": mf["value"],
        })
    payload_mf = {"query": mutation_mf, "variables": {"metafields": mf_inputs}}
    with httpx.Client(timeout=15) as client:
        r = client.post(endpoint, headers=headers, json=payload_mf)
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        print(f"    ❌ metafieldsSet GraphQLエラー: {data['errors']}")
        return False
    errors = data.get("data", {}).get("metafieldsSet", {}).get("userErrors", [])
    if errors:
        print(f"    ❌ metafieldsSet エラー: {errors}")
        return False
    return True


# --- Gemini バッチ解析 ---
def format_product_info(index, product):
    title = product["title"]
    description = product["description"] or "(説明なし)"
    category = ""
    if product.get("productCategory"):
        node = product["productCategory"]["productTaxonomyNode"]
        category = f"Shopifyカテゴリ: {node['fullName']}"
    variants = product["variants"]["edges"]
    variant_info = ""
    for v in variants:
        vn = v["node"]
        opts = ", ".join([f'{o["name"]}:{o["value"]}' for o in vn["selectedOptions"]])
        variant_info += f"    {vn['title']} (¥{vn['price']}) [{opts}]\n"
    return f"""--- 商品 {index} ---
商品名: {title}
{category}
説明文: {description}
バリエーション:
{variant_info}"""


def download_images_for_batch(products, max_images_per_product=1):
    all_images = []
    for product in products:
        image_edges = product["images"]["edges"]
        for img_edge in image_edges[:max_images_per_product]:
            try:
                with httpx.Client(timeout=15) as http:
                    resp = http.get(img_edge["node"]["url"])
                resp.raise_for_status()
                img = Image.open(io.BytesIO(resp.content))
                img.thumbnail((600, 600))
                all_images.append(img)
            except Exception as e:
                print(f"  ⚠ 画像取得失敗: {e}")
    return all_images


def analyze_batch_with_gemini(client, products, with_images=False):
    product_texts = []
    for i, product in enumerate(products):
        product_texts.append(format_product_info(i, product))
    products_block = "\n".join(product_texts)

    prompt = f"""あなたは古着・ヴィンテージ衣料品の専門家です。
以下の{len(products)}件の商品情報を分析し、各商品に対してShopify検索・AI提案用のタグを生成してください。

{TAG_TAXONOMY}

## 入力商品データ

{products_block}

## ルール
1. タグは上記リストを優先的に使い、リストにないものは必要に応じて追加OK。
2. ブランド名は商品名の【】や[]内から抽出。英語のまま。
3. サイズは説明文やバリエーションから判読。S/M/L/XL/XXL等の標準表記。
4. 素材タグは日本語と英語の両方を含める (例: コットン, Cotton)。
5. 色・柄は商品名・説明文・Shopifyカテゴリから推測。
6. product_index は 0 始まりで各商品に対応させてください。
7. 全{len(products)}件分の結果を漏れなく返してください。
"""
    contents = [prompt]
    if with_images:
        images = download_images_for_batch(products)
        if images:
            contents.extend(images)
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=BatchProductTags,
            ),
        )
        result = BatchProductTags.model_validate_json(response.text)
        return result.products
    except Exception as e:
        print(f"  ❌ Gemini バッチエラー: {e}")
        return None


def get_product_type_from_category(product):
    if product.get("productCategory"):
        return product["productCategory"]["productTaxonomyNode"]["name"]
    return ""


def build_tags(result, existing_tags):
    base_tags = []
    if "USED" in existing_tags:
        base_tags.append("USED")
    if "NEW" in existing_tags:
        base_tags.append("NEW")
    all_tags = list(base_tags)
    all_tags.extend(result.category_tags)
    all_tags.extend(result.material_tags)
    all_tags.extend(result.style_tags)
    all_tags.extend(result.color_tags)
    all_tags.extend(result.era_tags)
    all_tags.extend(result.feature_tags)
    if result.brand:
        all_tags.append(result.brand)
    if result.size_info:
        all_tags.append(result.size_info)
    seen = set()
    unique_tags = []
    for tag in all_tags:
        tag_lower = tag.strip().lower()
        if tag_lower and tag_lower not in seen:
            seen.add(tag_lower)
            unique_tags.append(tag.strip())
    return unique_tags


def build_metafields(result):
    """Gemini結果からカスタムメタフィールドを構築"""
    metafields = []
    if result.brand:
        metafields.append({
            "namespace": "custom",
            "key": "brand",
            "type": "single_line_text_field",
            "value": result.brand,
        })
    if result.style_tags:
        metafields.append({
            "namespace": "custom",
            "key": "style",
            "type": "json",
            "value": json.dumps(result.style_tags, ensure_ascii=False),
        })
    era = result.era_tags[0] if result.era_tags else ""
    if era:
        metafields.append({
            "namespace": "custom",
            "key": "era",
            "type": "single_line_text_field",
            "value": era,
        })
    if result.feature_tags:
        metafields.append({
            "namespace": "custom",
            "key": "features",
            "type": "json",
            "value": json.dumps(result.feature_tags, ensure_ascii=False),
        })
    # 処理済みタイムスタンプ
    metafields.append({
        "namespace": "custom",
        "key": "tagged_at",
        "type": "single_line_text_field",
        "value": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    })
    return metafields


# --- メイン ---
def main():
    parser = argparse.ArgumentParser(description="Shopify商品メタデータ正規化 (バッチ処理)")
    parser.add_argument("--apply", action="store_true", help="実際にShopifyを更新")
    parser.add_argument("--id", type=str, help="特定の商品IDだけ処理")
    parser.add_argument("--force", action="store_true", help="既にタグ済みの商品も再処理")
    parser.add_argument("--with-images", action="store_true", help="画像も含めて解析")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY が未設定")
        sys.exit(1)
    gemini_client = genai.Client(api_key=api_key)
    endpoint, headers = get_shopify_config()

    print("📦 商品を取得中...")
    products = fetch_all_products(endpoint, headers)
    print(f"   {len(products)}件の商品を取得\n")

    if args.id:
        products = [p for p in products if p["id"] == args.id]
        if not products:
            print(f"ERROR: 商品 {args.id} が見つかりません")
            sys.exit(1)

    if not args.force:
        total_before = len(products)
        products = [p for p in products if not p.get("taggedAt")]
        skipped = total_before - len(products)
        print(f"   未処理の商品: {len(products)}件 (処理済みスキップ: {skipped}件)\n")

    if not products:
        print("✅ 処理対象の商品がありません")
        return

    mode = "🔧 更新モード" if args.apply else "👀 ドライラン (--apply で実際に更新)"
    img_mode = "📷 画像あり" if args.with_images else "📝 テキストのみ"
    batch_count = (len(products) + args.batch_size - 1) // args.batch_size
    print(f"   {mode}")
    print(f"   {img_mode}")
    print(f"   バッチサイズ: {args.batch_size}件 × {batch_count}バッチ\n")
    print("=" * 70)

    success = 0
    errors = 0
    start_time = time.time()

    for batch_idx in range(0, len(products), args.batch_size):
        batch = products[batch_idx:batch_idx + args.batch_size]
        batch_num = batch_idx // args.batch_size + 1
        print(f"\n📋 バッチ {batch_num}/{batch_count} ({len(batch)}件)")
        print("-" * 70)

        for i, p in enumerate(batch):
            cat_name = get_product_type_from_category(p)
            print(f"  [{batch_idx + i + 1}] {p['title']}  [{cat_name}]")

        print(f"\n  🤖 Gemini 解析中...")
        results = analyze_batch_with_gemini(
            gemini_client, batch, with_images=args.with_images
        )
        if not results:
            errors += len(batch)
            print(f"  ❌ バッチ全体がエラー")
            continue

        result_map = {r.product_index: r for r in results}

        for i, product in enumerate(batch):
            result = result_map.get(i)
            product_type = get_product_type_from_category(product)

            if not result:
                print(f"\n  [{batch_idx + i + 1}] {product['title']}")
                print(f"    ❌ 結果なし")
                errors += 1
                continue

            tags = build_tags(result, product["tags"])
            metafields = build_metafields(result)

            print(f"\n  [{batch_idx + i + 1}] {product['title']}")
            print(f"    productType: '{product['productType']}' → '{product_type}'")
            print(f"    tags ({len(tags)}): {tags}")
            for mf in metafields:
                print(f"    metafield: {mf['namespace']}:{mf['key']} = {mf['value']}")

            if args.apply:
                ok = update_product_full(
                    endpoint, headers,
                    product["id"], product_type, tags, metafields
                )
                if ok:
                    print(f"    ✅ 更新完了")
                    success += 1
                else:
                    errors += 1
            else:
                success += 1

        if batch_idx + args.batch_size < len(products):
            time.sleep(RATE_LIMIT_DELAY)

    elapsed = time.time() - start_time
    print(f"\n{'='*70}")
    print(f"完了: {success}件成功, {errors}件エラー ({elapsed:.1f}秒)")
    if not args.apply:
        print("→ 実際に更新するには --apply オプションを付けてください")


if __name__ == "__main__":
    main()
