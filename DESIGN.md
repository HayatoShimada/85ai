# 85-Store AI店員システム 設計ドキュメント

## 1. プロジェクト概要

実店舗（オフライン）とネットショップ（Shopify）のデータ、そして最新のAI（Gemini）を融合させた「次世代の古着屋体験」を提供するAI接客システム。
お客様がその日に着ている服をカメラで読み取り、AIがそれに合う「一点モノ」の古着をShopifyのリアルタイム在庫から提案する。

### 本番想定環境
- **中核ハブ:** Mac Studio（カメラ認識・AI通信・映像演出の一括処理）
- **操作端末:** iPad（ブラウザベースのリモートUI）
- **空間デバイス:** 超短焦点プロジェクター + 店舗用スピーカー

### 開発・検証環境
- **Ubuntu (WSL2含む)** 上でバックエンド・フロントエンドの全機能を開発・テスト可能にする
- カメラはUSB Webカメラまたはブラウザ内蔵カメラ（`getUserMedia`）を使用
- プロジェクション演出はブラウザ上でのプレビューで代替

---

## 2. システムアーキテクチャ

```
┌──────────────────────────────────────────────────────────────────┐
│                      フロントエンド (Next.js)                      │
│                     http://localhost:3000                          │
│                                                                   │
│  ┌────────────┐  ┌──────────┐  ┌───────────┐  ┌──────────────┐  │
│  │ 好み入力    │→│ カメラUI  │→│ 撮影・送信  │→│ 結果表示     │  │
│  │ スタイルタグ │  │getUserMedia│  │ FormData  │  │ + 音声読上  │  │
│  │ + 顧客登録  │  └──────────┘  │ + 好みタグ │  │ + 商品提案  │  │
│  └──────┬─────┘                 └─────┬─────┘  └──────────────┘  │
│         │ POST /api/customers          │ POST /api/analyze        │
└─────────┼──────────────────────────────┼─────────────────────────┘
          │                              │
┌─────────┼──────────────────────────────┼─────────────────────────┐
│         │    バックエンド (FastAPI)      │                         │
│         │   http://localhost:8000       │                         │
│         │                              │                         │
│  ┌──────▼──────────┐  ┌───────────────▼──────────────────┐      │
│  │ /api/customers   │  │ /api/analyze エンドポイント       │      │
│  │ 顧客登録/検索    │  │  1. 画像 + 好みタグ受信           │      │
│  │ 好み保存/取得    │  │  2. Gemini API で服装解析          │      │
│  └────────┬────────┘  │     (好みを加味した提案)           │      │
│           │            │  3. Shopify API で在庫商品検索     │      │
│           │            │  4. 統合結果をJSONで返却           │      │
│           │            └──────┬───────────────┬────────────┘      │
│           │                   │               │                   │
│  ┌────────▼─────────┐ ┌──────▼───────┐ ┌─────▼──────────┐       │
│  │customer_service  │ │gemini_service│ │shopify_service │       │
│  │(Shopify Admin    │ │(Gemini 2.5   │ │(Storefront     │       │
│  │ API - 顧客管理)  │ │ Flash API)   │ │ GraphQL API)   │       │
│  └──────────────────┘ └──────────────┘ └────────────────┘       │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. 技術スタック

| レイヤー | 技術 | 用途 |
|---------|------|------|
| フロントエンド | Next.js 16 (React 19) | SPA・カメラUI |
| スタイリング | Tailwind CSS v4 | UIデザイン |
| アニメーション | Framer Motion | 画面遷移・ローディング演出 |
| アイコン | Lucide React | UIアイコン |
| バックエンド | FastAPI (Python 3.11+) | REST API サーバー |
| AI推論 | Google Gemini API (`gemini-2.5-flash`) | 服装解析・提案生成 |
| EC連携（商品検索） | Shopify Storefront API (GraphQL) | 在庫商品検索 |
| EC連携（顧客管理） | Shopify Admin API (GraphQL) | 顧客登録・好み保存 |
| 画像処理 | Pillow | 画像デコード |
| コンテナ | Docker / Docker Compose | 環境統一・デプロイ |

---

## 4. API設計

### `POST /api/analyze`

カメラで撮影した画像とユーザーの好みタグを受け取り、AI解析→商品検索→統合結果を返す。

**リクエスト:**
- Content-Type: `multipart/form-data`
- Body:
  - `file` (JPEG画像)
  - `preferences` (JSON文字列) - ユーザーの好みタグ配列
  - `customer_id` (文字列, optional) - Shopify顧客ID

**レスポンス:**
```json
{
  "status": "success",
  "data": {
    "analyzed_outfit": "ダークウォッシュのストレートデニムに白のベーシックTシャツ...",
    "detected_style": ["カジュアル", "アメカジ"],
    "box_ymin": 120,
    "box_xmin": 250,
    "box_ymax": 650,
    "box_xmax": 750,
    "recommendations": [
      {
        "title": "アメカジ風アプローチ",
        "reason": "デニムの色味と「かっこいい」の好みに合わせて...",
        "search_keywords": ["スウェット", "オーバーサイズ", "90s"],
        "category": "トップス",
        "shopify_products": [
          {
            "id": "gid://shopify/Product/123",
            "title": "90s Champion スウェット",
            "description": "...",
            "price": "4500.0 JPY",
            "image_url": "https://...",
            "url": "https://..."
          }
        ]
      }
    ]
  }
}
```

### `POST /api/customers`

顧客の登録または既存顧客の検索を行い、好みのスタイルタグをShopifyの顧客メタフィールドに保存する。

**リクエスト:**
```json
{
  "name": "田中太郎",
  "email": "tanaka@example.com",
  "style_preferences": ["かっこいい", "ストリート", "90s"]
}
```

**レスポンス:**
```json
{
  "status": "success",
  "customer": {
    "id": "gid://shopify/Customer/123456",
    "name": "田中太郎",
    "email": "tanaka@example.com",
    "style_preferences": ["かっこいい", "ストリート", "90s"],
    "is_new": false
  }
}
```

### `GET /api/customers?email={email}`

メールアドレスで既存顧客を検索し、保存済みの好みタグを取得する。リピーターの好みを即座に復元できる。

**レスポンス:**
```json
{
  "status": "success",
  "customer": {
    "id": "gid://shopify/Customer/123456",
    "name": "田中太郎",
    "email": "tanaka@example.com",
    "style_preferences": ["かっこいい", "ストリート", "90s"]
  }
}
```

### `GET /api/health`

ヘルスチェック用。外部API（Gemini / Shopify）の疎通確認。

---

## 4.1 スタイルタグ定義

ユーザーが選択できるスタイルタグの一覧。UIではタグチップとして表示し、複数選択可能。

| カテゴリ | タグ |
|---------|------|
| テイスト | かっこいい、かわいい、きれいめ、ナチュラル、個性的 |
| スタイル | ストリート、アメカジ、モード、ヴィンテージ、カジュアル、スポーティ |
| 年代感 | 70s、80s、90s、Y2K、ミリタリー |
| その他 | オーバーサイズ、タイト、柄モノ、モノトーン |

これらのタグは:
1. **UI上でユーザーが撮影前に選択** → Geminiプロンプトに含めて提案の方向性を調整
2. **Shopify顧客メタフィールドに保存** → リピーター来店時に好みを即座に復元
3. **提案履歴と合わせて分析** → 将来的に顧客の嗜好データとしてマーケティングに活用

---

## 5. Gemini プロンプト設計

Geminiには構造化出力（`response_schema`）を使い、Pydanticモデルに従ったJSONを返させる。
ユーザーの好みタグをプロンプトに含め、服装解析 + 好みを加味した提案を行う。

### プロンプト構造

```
添付した画像の人物が着ている服を分析してください。

【ユーザーの好み】
{user_preferences}  ← UIで選択されたタグ（例: かっこいい, ストリート, 90s）

上記の好みを踏まえた上で、現在着ている服の特徴と、
それに合う「古着」のアイテムを複数パターン（最大3つ）提案してください。
提案はユーザーの好みの方向性に沿ったものにしてください。
```

### 出力スキーマ (Pydantic)

```python
class RecommendationItem(BaseModel):
    title: str          # 提案テーマ名
    reason: str         # 提案理由（好みをどう反映したかを含む）
    search_keywords: list[str]  # Shopify検索キーワード
    category: str       # アイテムカテゴリ

class ClothingAnalysis(BaseModel):
    analyzed_outfit: str    # 服装の解析結果テキスト
    detected_style: list[str]  # 画像から推測されたスタイルタグ
    box_ymin: int           # バウンディングボックス (0-1000正規化座標)
    box_xmin: int
    box_ymax: int
    box_xmax: int
    recommendations: list[RecommendationItem]  # 最大3パターン
```

---

## 6. フロントエンド画面遷移

```
IDLE（待機）→ PREFERENCE（好み入力・顧客登録）→ CAMERA_ACTIVE（カメラ起動）→ ANALYZING → RESULT
  ↑                                                                                     │
  └─────────────────────────────── リセット ←────────────────────────────────────────────┘
```

| 画面 | 説明 |
|------|------|
| IDLE | スタートボタン。体験の開始を促す |
| PREFERENCE | 名前・メール入力 + スタイルタグ選択（かっこいい/かわいい/ナチュラル等）。リピーターはメール入力で好みを自動復元 |
| CAMERA_ACTIVE | カメラプレビュー + 撮影ボタン |
| ANALYZING | スキャン演出アニメーション |
| RESULT | AI分析結果 + バウンディングボックス + 好みを加味した最大3パターンの商品提案 |

### PREFERENCE画面の詳細

```
┌─────────────────────────────────────┐
│  あなたの好みを教えてください          │
│                                     │
│  名前: [________]                   │
│  メール: [________] [復元ボタン]      │
│                                     │
│  ── テイスト ──                      │
│  [かっこいい] [かわいい] [きれいめ]    │
│  [ナチュラル] [個性的]               │
│                                     │
│  ── スタイル ──                      │
│  [ストリート] [アメカジ] [モード]      │
│  [ヴィンテージ] [カジュアル]          │
│                                     │
│  ── 年代感 ──                        │
│  [70s] [80s] [90s] [Y2K]           │
│                                     │
│        [ 次へ → カメラ起動 ]          │
└─────────────────────────────────────┘
```

- タグはトグル選択（複数選択可）
- メールアドレス入力後「復元」を押すと既存顧客の好みタグが自動選択される
- 「次へ」で顧客情報をShopifyに保存（または更新）し、カメラ画面へ遷移

---

## 7. Ubuntu 開発環境セットアップ

### 7.1 前提条件

- Ubuntu 22.04+ (WSL2でも可)
- Python 3.11+
- Node.js 20+
- Docker / Docker Compose (オプション)

### 7.2 環境変数

`backend/.env` に以下を設定:

```env
GEMINI_API_KEY="your-gemini-api-key"
SHOPIFY_STORE_URL="your-store.myshopify.com"
SHOPIFY_STOREFRONT_ACCESS_TOKEN="your-storefront-token"
SHOPIFY_ADMIN_API_ACCESS_TOKEN="your-admin-api-token"
```

**注:** Shopify Admin APIトークンは顧客管理（登録・好み保存）に使用。Shopify管理画面 → 設定 → アプリと販売チャネル → アプリを開発 から `write_customers`, `read_customers` スコープ付きで取得する。

### 7.3 バックエンド起動

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 7.4 フロントエンド起動

```bash
cd frontend
npm install
npm run dev
```

### 7.5 Docker Compose 起動

```bash
docker-compose up -d --build
# フロントエンド: http://localhost:3000
# バックエンドAPI: http://localhost:8000/docs
```

### 7.6 WSL2 固有の注意点

- **カメラアクセス:** WSL2から直接USBカメラにアクセスするには `usbipd-win` でUSBデバイスをアタッチするか、ブラウザ側（Windows側のChrome等）の `getUserMedia` で代替する。フロントエンドのカメラ機能はブラウザAPIを使っているため、Windows側のブラウザからWSL2上のサーバーにアクセスすれば問題なく動作する。
- **ネットワーク:** WSL2のIPへWindows側からアクセスする場合、`localhost` でフォワーディングされるか、WSL2のIPアドレスを直接使用する。

---

## 8. テスト戦略

### 8.1 モックモード（API不要テスト）

外部API（Gemini / Shopify）のキーがなくても開発・UIテストできるよう、モックレスポンスを返すモードを用意する。

- `MOCK_MODE=true` 環境変数でモック有効化
- Gemini解析: 固定のJSON結果を返す
- Shopify検索: ダミー商品データを返す

### 8.2 単体テスト

- バックエンド: `pytest` でAPIエンドポイント・サービス関数をテスト
- フロントエンド: ブラウザE2Eは後のフェーズ

### 8.3 統合テスト

- `test_client.py`: ダミー画像をAPIに送信して正常レスポンスを確認
- `pc_camera_test.py`: 実カメラからの撮影→API送信を確認

---

## 9. 顧客データ活用（Shopify Admin API連携）

### 9.1 顧客管理フロー

```
初回来店:
  メール入力 → Shopify顧客検索 → 見つからない → 新規顧客作成 + 好みタグ保存

リピーター来店:
  メール入力 → Shopify顧客検索 → 見つかった → 保存済み好みタグを復元 → 更新も可能
```

### 9.2 Shopify顧客メタフィールド設計

顧客の好みタグはShopifyの **Customer Metafield** に保存する。

| 項目 | 値 |
|------|------|
| Namespace | `custom` |
| Key | `style_preferences` |
| Type | `list.single_line_text_field` |
| 例 | `["かっこいい", "ストリート", "90s"]` |

これにより:
- Shopify管理画面からも顧客の好みが確認・編集できる
- Shopifyの顧客セグメント機能で「ストリート好き」などのグループ化が可能
- 将来的にメールマーケティング（好みに合った新商品入荷通知）に活用

### 9.3 データ活用の展望

- **来店履歴 × 好みタグ:** リピーターの好みの変化をトラッキング
- **購買データ × 提案データ:** AIの提案が実際の購買にどの程度つながったかを分析
- **顧客セグメント:** Shopifyの顧客グループ機能と連動し、好みベースのマーケティング施策を実施

---

## 10. 将来の拡張ポイント

### RAG（検索拡張生成）
キーワード検索だけでマッチしづらい場合、Shopifyの全商品データをベクトルDBに格納し、Geminiに「在庫リストの中から最も合うもの」を選ばせるRAGアプローチを導入する。

### 音声入力
マイクからの音声リクエスト（例：「このデニムに合う服を探して」）をGeminiに渡し、画像+音声のマルチモーダル入力に対応する。

### プロジェクションマッピング連携
Mac Studio + TouchDesigner等で提案商品のビジュアルを壁面投影する空間演出機能。開発環境ではブラウザ上のプレビューで代替する。
