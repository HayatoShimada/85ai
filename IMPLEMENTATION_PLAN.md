# 実装計画 - Ubuntu開発環境での段階的構築

## 現状の把握

### 実装済み
- [x] FastAPI バックエンド (`main.py`, `gemini_service.py`, `shopify_service.py`)
- [x] Next.js フロントエンド（カメラ撮影→解析→結果表示の全画面遷移）
- [x] Gemini 構造化出力（Pydanticスキーマ定義、バウンディングボックス対応）
- [x] Shopify Storefront API連携（GraphQLクエリ）
- [x] Docker / Docker Compose 設定
- [x] 音声読み上げ（Web Speech API）

### 未実装・改善が必要
- [ ] Ubuntu/WSL2環境での動作確認・修正
- [ ] ユーザー好み入力画面（PREFERENCE画面）
- [ ] Shopify顧客管理連携（Admin API）
- [ ] Geminiプロンプトへの好みタグ反映
- [ ] モックモード（APIキーなしでの開発・テスト）
- [ ] ヘルスチェックエンドポイント
- [ ] テスト自動化（pytest）
- [ ] エラーハンドリングの改善
- [ ] フロントエンドのAPI URLの環境変数化
- [ ] 画像アップロードの代替手段（ファイル選択）

---

## Phase 1: Ubuntu環境の基盤整備（最優先）

目標: Ubuntu/WSL2で `docker-compose up` 一発で起動でき、ブラウザからアクセスして動作確認できる状態にする。

### 1-1. バックエンドの環境修正

**対象ファイル:** `backend/requirements.txt`, `backend/Dockerfile`

- `opencv-python` → `opencv-python-headless` に変更
  - Docker / ヘッドレスサーバー環境ではGUI不要。現在 `cv2` は `pc_camera_test.py` でのみ使用しており、コアAPIでは使っていない
- Pillow のバージョン固定
- requirements.txt の全ライブラリバージョン固定（再現性確保）

```diff
# requirements.txt
- opencv-python
+ opencv-python-headless
```

### 1-2. モックモードの実装

**対象ファイル:** `backend/main.py`, `backend/mock_service.py`（新規作成）

APIキーなしでも全フローの動作確認・UI開発ができるモードを追加する。

- 環境変数 `MOCK_MODE=true` で有効化
- `mock_service.py` にモック用の固定レスポンスを定義
- `main.py` の `/api/analyze` 内で `MOCK_MODE` を判定し、モックレスポンスを返す
- モック商品データには画像URL（placeholder画像）も含める

```python
# mock_service.py
MOCK_ANALYSIS = {
    "analyzed_outfit": "ダークブルーのストレートデニムに...",
    "box_ymin": 150, "box_xmin": 200, "box_ymax": 700, "box_xmax": 800,
    "recommendations": [
        {
            "title": "アメカジ風アプローチ",
            "reason": "デニムの色味に合わせて...",
            "search_keywords": ["スウェット", "90s"],
            "category": "トップス",
            "shopify_products": [
                {
                    "id": "mock-1",
                    "title": "90s Champion スウェット ネイビー",
                    "description": "ヴィンテージチャンピオン...",
                    "price": "4,500 JPY",
                    "image_url": "https://placehold.co/400x400/1e293b/94a3b8?text=Mock+Item+1",
                    "url": "#"
                }
            ]
        },
        # ... パターン2, 3
    ]
}
```

### 1-3. ヘルスチェックエンドポイント

**対象ファイル:** `backend/main.py`

```python
@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "mock_mode": os.getenv("MOCK_MODE", "false") == "true",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "shopify_configured": bool(os.getenv("SHOPIFY_STORE_URL")),
    }
```

### 1-4. フロントエンドのAPI URL環境変数化

**対象ファイル:** `frontend/src/app/page.tsx`

現在ハードコードされている `http://localhost:8000` を環境変数に切り替える。

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
// ...
const res = await fetch(`${API_URL}/api/analyze`, { ... });
```

### 1-5. ファイル選択による画像アップロード対応

**対象ファイル:** `frontend/src/app/page.tsx`

WSL2やカメラがない環境でもテストできるよう、カメラ撮影に加えて「ファイルから画像を選択」する代替手段を追加する。

- IDLE画面に「画像をアップロード」ボタンを追加
- `<input type="file" accept="image/*">` で画像選択→APIに送信
- カメラと同じ解析フローに合流

### 1-6. 好み入力画面（PREFERENCE画面）の実装

**対象ファイル:** `frontend/src/app/page.tsx`

カメラ起動前にユーザーの好みを入力する画面を追加する。

- 新しいAppState `"PREFERENCE"` を追加（IDLE → PREFERENCE → CAMERA_ACTIVE の遷移）
- スタイルタグをカテゴリ別にチップUIで表示（トグル選択・複数選択可）
  - テイスト: かっこいい、かわいい、きれいめ、ナチュラル、個性的
  - スタイル: ストリート、アメカジ、モード、ヴィンテージ、カジュアル、スポーティ
  - 年代感: 70s、80s、90s、Y2K、ミリタリー
- 名前・メールアドレスの入力フォーム
- 「好みを復元」ボタン（メール入力後、既存顧客の保存済みタグを取得して自動選択）
- 選択されたタグは state で保持し、撮影後のAPI送信時に画像と一緒に送る

### 1-7. Shopify顧客管理API（バックエンド）

**新規ファイル:** `backend/customer_service.py`

Shopify Admin API (GraphQL) を使った顧客登録・検索・好み保存。

```python
# customer_service.py の主な関数
def search_customer_by_email(email: str) -> dict | None
def create_customer(name: str, email: str, preferences: list[str]) -> dict
def update_customer_preferences(customer_id: str, preferences: list[str]) -> dict
```

- Shopify Admin API GraphQLエンドポイント: `https://{store}/admin/api/2025-01/graphql.json`
- 認証: `X-Shopify-Access-Token` ヘッダー
- 好みタグは Customer Metafield (`custom.style_preferences`) に JSON配列で保存
- `.env` に `SHOPIFY_ADMIN_API_ACCESS_TOKEN` を追加

**対象ファイル:** `backend/main.py`

新しいエンドポイントを追加:

```python
@app.post("/api/customers")
async def register_customer(name, email, style_preferences):
    # メールで既存顧客を検索 → なければ新規作成 → あれば好み更新

@app.get("/api/customers")
async def lookup_customer(email: str):
    # メールで顧客検索 → 保存済みの好みタグを返す
```

### 1-8. Geminiプロンプトへの好みタグ反映

**対象ファイル:** `backend/gemini_service.py`, `backend/main.py`

- `analyze_image_and_get_tags()` にユーザーの好みタグ（`list[str]`）を引数追加
- プロンプトに好みタグを埋め込み、提案の方向性を調整

```python
def analyze_image_and_get_tags(image_bytes: bytes, user_preferences: list[str] = None) -> str:
    pref_text = "、".join(user_preferences) if user_preferences else "特になし"
    prompt = f"""
    添付した画像の人物が着ている服を分析してください。

    【ユーザーの好み】
    {pref_text}

    上記の好みを踏まえた上で、...
    """
```

- `/api/analyze` エンドポイントで `preferences` フィールドを受け取り、Geminiに渡す
- Pydanticスキーマに `detected_style: list[str]` を追加（画像から推測されたスタイルタグ）

---

## Phase 2: テスト基盤の構築

目標: `pytest` でバックエンドのAPIと各サービスをテスト可能にする。

### 2-1. pytest セットアップ

**対象ファイル:** `backend/tests/` ディレクトリ（新規作成）

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py       # テスト用フィクスチャ
│   ├── test_api.py       # APIエンドポイントテスト
│   ├── test_gemini.py    # gemini_service 単体テスト
│   └── test_shopify.py   # shopify_service 単体テスト
```

- `conftest.py`: FastAPI TestClient のセットアップ、モック用フィクスチャ
- `test_api.py`: `/api/analyze` のリクエスト/レスポンス検証（モックモード使用）
- `test_gemini.py`: Gemini APIのモック/レスポンスパース検証
- `test_shopify.py`: Shopify APIのモック/レスポンスパース検証

### 2-2. requirements に pytest 追加

```diff
# requirements.txt に追加
+ pytest
+ httpx  # FastAPI TestClient 用
```

### 2-3. docker-compose へのテスト実行コマンド

```bash
# テスト実行（Docker内）
docker-compose exec backend pytest tests/ -v
```

---

## Phase 3: UX改善とエラーハンドリング

目標: 実利用を想定したUIの堅牢性向上。

### 3-1. バックエンドのエラーハンドリング強化

**対象ファイル:** `backend/main.py`, `backend/gemini_service.py`

- Gemini API タイムアウト対応（リクエストに `timeout` 設定）
- Gemini API レートリミット時のリトライ or ユーザーへの適切なエラーメッセージ
- Shopify API 接続エラー時の部分成功レスポンス（解析結果は返すが商品は「検索できませんでした」）

### 3-2. フロントエンドのエラー表示改善

**対象ファイル:** `frontend/src/app/page.tsx`

- API通信エラー時のリトライボタン
- 解析結果は取得できたが商品が0件の場合の表示改善
- ローディング中のタイムアウト検知（30秒でメッセージ表示）

### 3-3. layout.tsx のメタデータ修正

**対象ファイル:** `frontend/src/app/layout.tsx`

- `title` を `"85-Store AI Stylist"` に変更
- `description` を適切な内容に変更
- `lang` を `"ja"` に変更

---

## Phase 4: 実店舗連携の準備

目標: 実際のShopify在庫データとの連携テスト。

### 4-1. Shopify APIバージョンの更新

**対象ファイル:** `backend/shopify_service.py`

- APIバージョンを `2024-01` → `2025-01` に更新
- 検索クエリの最適化（タグベース検索の改善）

### 4-2. 商品画像のプリロード最適化

**対象ファイル:** `frontend/src/app/page.tsx`

- 結果表示時の商品画像を `next/image` で最適化
- 画像の遅延読み込み（lazy loading）

### 4-3. QRコード生成

**新規ファイル:** `frontend/src/components/QRCode.tsx`

- 各商品のShopify URLからQRコードを生成
- 店頭でiPadに表示→スマホで読み取ってEC購入、のフローを実現

---

## 実装の優先順位まとめ

| 順序 | 内容 | 目的 |
|------|------|------|
| **Phase 1** | 環境整備・モック・好み入力・顧客連携 | Ubuntu/WSL2で全機能を動かせる |
| **Phase 2** | pytest テスト基盤 | 変更時の品質担保 |
| **Phase 3** | エラーハンドリング・UX改善 | 実利用に耐える堅牢性 |
| **Phase 4** | Shopify連携強化・QRコード | 実店舗デプロイ準備 |

---

## Phase 1 の実装順序

基盤系（1-1〜1-4）を先に固め、その上に好み・顧客機能（1-6〜1-8）を構築する。

```
1-1 requirements修正  ─┐
1-2 モックモード実装   ─┤── 基盤整備（並行可能）
1-3 ヘルスチェック     ─┤
1-4 API URL環境変数化  ─┘
         │
1-5 ファイルアップロード対応
         │
1-7 顧客管理API (バックエンド)  ← Shopify Admin API連携
         │
1-6 好み入力画面 (フロントエンド) ← 1-7のAPIを使う
         │
1-8 Geminiプロンプト好み反映     ← 1-6で渡された好みをGeminiに送る
```

## Phase 1 完了時の到達状態

`docker-compose up --build` で全体が起動し、ブラウザから `http://localhost:3000` にアクセスして以下が確認できる:

1. **好み入力:** 名前・メール入力 + スタイルタグ選択
2. **顧客復元:** メール入力で既存顧客の好みが自動復元される
3. **撮影・解析:** カメラ撮影 or ファイルアップロードで画像送信
4. **好み反映:** 選択した好みタグを加味したAI提案が表示される
5. **モック動作:** `MOCK_MODE=true` 時はAPIキーなしで全フローが動く
