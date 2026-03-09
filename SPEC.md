# 85-Store AI Shop Assistant — 現状仕様書

## 1. プロジェクト概要

古着屋「85-Store」向けのAI接客システム。店頭に設置したカメラで来店客の服装を撮影し、Gemini APIで解析、Shopifyの在庫から相性の良い古着を提案する。

### 構成図

```
┌─────────────┐    WebSocket     ┌──────────────┐    WebSocket     ┌─────────────────┐
│  iPad (操作) │ ──────────────→ │  Backend      │ ──────────────→ │ プロジェクター   │
│  port:3000   │  /ws/projection │  FastAPI      │  /ws/projection │ (投影画面)       │
│  page.tsx    │  /control       │  port:8000    │  /display       │ projection/      │
└─────────────┘                  │               │                 │ page.tsx         │
       │                         │  ┌──────────┐ │                 └─────────────────┘
       │  REST API               │  │ Gemini   │ │
       │  POST /api/analyze      │  │ 3.1 Pro  │ │
       │  GET/POST /api/customers│  └──────────┘ │
       └─────────────────────────│               │
                                 │  ┌──────────┐ │     ┌──────────────┐
                                 │  │ Shopify  │ │     │ USBカメラ     │
                                 │  │ GraphQL  │ │     │ (ミラー用)    │
                                 │  └──────────┘ │     └──────┬───────┘
                                 │               │            │
                                 │  Vision/      │←───────────┘
                                 │  MediaPipe    │  OpenCV
                                 └──────────────┘
```

### 技術スタック

| レイヤー | 技術 |
|----------|------|
| バックエンド | FastAPI (Python 3.11+), Uvicorn |
| AI解析 | Google Gemini 3.1 Pro (構造化JSON出力) |
| 商品検索 | Shopify Storefront API (GraphQL, API version `2026-01`) |
| 顧客管理 | Shopify Admin API (GraphQL, API version `2026-01`) |
| 認証 | Client Credentials Grant + 自動トークン更新 |
| ミラー | OpenCV + Apple Vision Framework (Neural Engine) / MediaPipe (フォールバック) |
| フロントエンド | Next.js 16.1.6 (React 19), Tailwind CSS v4, Framer Motion |
| QRコード | qrcode.react |
| コンテナ | Docker Compose |
| テスト | pytest + pytest-asyncio + httpx |

---

## 2. バックエンド API

### 2.1 REST エンドポイント

#### `GET /`
ルートエンドポイント。
```json
{ "message": "Welcome to the Vintage AI Shop Assistant API" }
```

#### `GET /api/health`
各外部APIの設定状況を返す。
```json
{
  "status": "ok",
  "mock_mode": false,
  "gemini_configured": true,
  "shopify_storefront_configured": true,
  "shopify_admin_configured": true
}
```

#### `POST /api/analyze`
画像 + 好みタグを受け取り、Gemini解析 → Shopify商品検索を実行。

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| `file` | UploadFile | 必須 | 解析する画像 |
| `preferences` | Form(string) | 任意 | JSON配列 `["ストリート","90s"]` |
| `customer_id` | Form(string) | 任意 | Shopify顧客ID |

**レスポンス (成功):**
```json
{
  "status": "success",
  "data": {
    "analyzed_outfit": "ダークブルーのストレートデニムに...",
    "detected_style": ["カジュアル", "アメカジ"],
    "box_ymin": 150, "box_xmin": 250,
    "box_ymax": 700, "box_xmax": 750,
    "recommendations": [
      {
        "title": "ストリートMIXスタイル",
        "reason": "シンプルなデニムコーデにストリート感を...",
        "search_keywords": ["コーチジャケット", "ナイロン"],
        "category": "アウター",
        "shopify_products": [
          {
            "id": "gid://shopify/Product/...",
            "title": "90s コーチジャケット ブラック",
            "description": "90年代のコーチジャケット...",
            "price": "3200.0 JPY",
            "image_url": "https://cdn.shopify.com/...",
            "url": "https://shop.85-store.com/..."
          }
        ]
      }
    ]
  },
  "warning": "一部の商品検索に失敗しました: ..."
}
```

- バウンディングボックス座標: 0〜1000の正規化値
- `recommendations`: 最大3パターン
- `shopify_products`: 各パターンにつき最大5件（`availableForSale: true` のみ）
- `warning`: Shopify検索が部分的に失敗した場合のみ付与

#### `GET /api/customers?email={email}`
メールアドレスで顧客を検索し、保存済みの好みタグを返す。

**レスポンス:**
```json
{
  "status": "success",
  "customer": {
    "id": "gid://shopify/Customer/...",
    "name": "テスト太郎",
    "email": "test@example.com",
    "style_preferences": ["ストリート", "90s", "かっこいい"]
  }
}
```
見つからない場合: `{ "status": "not_found", "customer": null }`

#### `POST /api/customers`
顧客を登録、または既存顧客の好みを更新。

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| `name` | Form(string) | 必須 | 顧客名 |
| `email` | Form(string) | 必須 | メールアドレス |
| `style_preferences` | Form(string) | 任意 | JSON配列 |

レスポンスに `is_new: true/false` で新規/更新を判別可能。

#### `GET /api/mirror/cameras`
バックエンドサーバーに接続されたカメラデバイスの一覧を返す。

```json
{
  "status": "ok",
  "cameras": [
    { "index": 0, "name": "Camera 0 (V4L2)", "device": "/dev/video0", "resolution": "640x480" },
    { "index": 2, "name": "Camera 2 (V4L2)", "device": "/dev/video2", "resolution": "1920x1080" }
  ],
  "current": 0,
  "backend": "vision"
}
```

- `backend`: 現在のセグメンテーションバックエンド (`"vision"` / `"mediapipe"` / `"none"`)

#### `POST /api/mirror/cameras/{index}`
ミラーカメラを指定インデックスに切り替える。稼働中の場合は自動再起動。

#### `POST /api/mirror/start` / `POST /api/mirror/stop`
ミラーカメラの手動起動/停止。

---

### 2.2 WebSocket エンドポイント

#### `WS /ws/mirror`
ミラーカメラのリアルタイム映像を配信。接続時にカメラ自動起動、切断時に停止。

- **送信データ**: base64エンコードされた透過WebP（人物セグメンテーション済み）
- **フレームレート**: `MIRROR_FPS` 環境変数で設定（デフォルト30fps）

#### `WS /ws/projection/control`
iPad（操作画面）からの状態変更を受信。

**受信メッセージ:**
```json
{ "type": "STATE_CHANGE", "state": "CAMERA_ACTIVE", "payload": { ... } }
{ "type": "FLASH" }
```

#### `WS /ws/projection/display`
プロジェクション表示画面にイベントを配信。

**配信データ:**
- JSON: `STATE_CHANGE`、`FLASH` メッセージ
- テキスト: base64ミラーフレーム（`{` で始まらない文字列）

**受信メッセージ:**
```json
{ "type": "REQUEST_STATE" }
```

**ProjectionManager の動作:**
- `CAMERA_ACTIVE` / `ANALYZING` 状態でミラーカメラを自動起動
- その他の状態でミラーカメラを自動停止
- 接続中のdisplay全体にブロードキャスト

---

## 3. バックエンド サービス

### 3.1 gemini_service.py — AI解析

Gemini 3.1 Pro に画像を送信し、構造化JSON（Pydanticスキーマ）で結果を取得。

**Pydanticスキーマ:**
```python
class RecommendationItem(BaseModel):
    title: str        # 提案テーマ
    reason: str       # 提案理由（好み反映の説明含む）
    search_keywords: list[str]  # Shopify検索キーワード
    category: str     # カテゴリ（トップス、アウター等）

class ClothingAnalysis(BaseModel):
    analyzed_outfit: str       # 服装分析テキスト
    detected_style: list[str]  # 推測スタイルタグ
    box_ymin: int              # バウンディングボックス (0-1000)
    box_xmin: int
    box_ymax: int
    box_xmax: int
    recommendations: list[RecommendationItem]  # 最大3パターン
```

**プロンプト構成:**
- 服装の特徴分析
- スタイルタグ推測
- バウンディングボックス出力
- ユーザー好みを加味した提案（好みタグがある場合）
- タイムアウト: 60秒

### 3.2 shopify_service.py — 商品検索

Shopify Storefront API (GraphQL) で在庫商品を検索。

- エンドポイント: `https://{store}/api/2026-01/graphql.json`
- 認証: `X-Shopify-Storefront-Access-Token` ヘッダー
- 検索: キーワードをスペース連結 + `available_for_sale:true` フィルタ
- 取得件数: 最大5件/パターン
- タイムアウト: 15秒

### 3.3 customer_service.py — 顧客管理

Shopify Admin API (GraphQL) で顧客の登録・検索・好みデータの保存。

- エンドポイント: `https://{store}/admin/api/2026-01/graphql.json`
- 認証: `X-Shopify-Access-Token` ヘッダー（`shopify_auth.py` から自動取得）
- 好みデータ: Customer Metafield `custom.style_preferences` (JSON型)
- タイムアウト: 15秒

**関数一覧:**
| 関数 | 説明 |
|---|---|
| `search_customer_by_email(email)` | メールで顧客検索、好みタグ取得 |
| `create_customer(name, email, preferences)` | 新規顧客作成 + 好みメタフィールド保存 |
| `update_customer_preferences(customer_id, preferences)` | 既存顧客の好みタグ更新 |

### 3.4 shopify_auth.py — トークン自動更新

`ShopifyTokenManager` シングルトンがAdmin APIトークンのライフサイクルを管理。

- 24時間で失効するトークンを期限5分前に自動更新
- Client Credentials Grant: `POST /admin/oauth/access_token`
- スレッドセーフ（ダブルチェックロッキング）
- フォールバック: `SHOPIFY_ADMIN_API_ACCESS_TOKEN` 環境変数の静的トークン（`shpat_` prefix）

### 3.5 mirror_service.py — ミラーカメラ

`MirrorSegmenter` シングルトンがカメラキャプチャと人物セグメンテーションを管理。
セグメンテーションバックエンドを自動選択し、macOS では Apple Vision Framework (Neural Engine)、Linux では MediaPipe にフォールバックする。

**セグメンテーションバックエンド:**
| バックエンド | 環境 | ハードウェア | 解像度 |
|---|---|---|---|
| Apple Vision Framework | macOS (Apple Silicon) | **Neural Engine** | 内部 1024x768 マスク |
| MediaPipe Selfie Segmentation | Linux / Docker | CPU | 内部 640x360 マスク (縮小処理) |

**処理フロー:**
1. OpenCVでカメラフレーム取得 (MJPEG優先)
2. 左右反転（鏡像）
3. セグメンテーション:
   - **macOS**: Apple Vision `VNGeneratePersonSegmentationRequest` (Neural Engine, accurate モード)
   - **Linux**: MediaPipe Selfie Segmentation (Landscape モデル, 縮小画像で処理)
4. マスク後処理: 閾値適用 + ガウシアンブラー (エッジ平滑化)
5. BGRAアルファチャンネルにマスク適用
6. WebPエンコード (透過対応、PNG比 3-5倍高速) → base64文字列で返却
7. 処理時間を差し引いた適応スリープで一定FPSを維持

### 3.5.1 vision_segmenter.py — Apple Vision セグメンター

macOS 12+ (Monterey) 上で Apple Vision Framework を PyObjC 経由で呼び出す。

- `VNGeneratePersonSegmentationRequest` で人物セグメンテーション
- qualityLevel: `0`=fast(GPU), `1`=balanced(GPU+NE), `2`=accurate(Neural Engine, デフォルト)
- 出力: `kCVPixelFormatType_OneComponent8` (8bit グレースケールマスク)
- CGImage ↔ numpy 変換: Quartz + CoreVideo 経由
- Linux/Docker では自動的に無効化、MediaPipe にフォールバック

**カメラ列挙:**
- Linux: `/dev/video*` を走査、OpenCVで開けるデバイスを列挙
- macOS/その他: インデックス0-9を試行
- 外部USB Webカメラ、キャプチャボード等に対応

**設定:**
| 環境変数 | デフォルト | 説明 |
|---|---|---|
| `MIRROR_CAMERA_INDEX` | 0 | カメラデバイスインデックス |
| `MIRROR_WIDTH` | 1920 | キャプチャ幅 |
| `MIRROR_HEIGHT` | 1080 | キャプチャ高さ |
| `MIRROR_FPS` | 30 | 配信フレームレート |
| `MIRROR_SEGMENTER` | auto | バックエンド選択 (`auto` / `vision` / `mediapipe`) |
| `MIRROR_VISION_QUALITY` | 2 | Vision品質 (`0`=fast, `1`=balanced, `2`=accurate) |
| `MIRROR_SEG_WIDTH` | 640 | MediaPipe用セグメンテーション内部解像度 (幅) |
| `MIRROR_WEBP_QUALITY` | 80 | WebP出力品質 (0-100) |
| `MIRROR_MASK_BLUR` | 7 | マスクエッジのガウシアンブラー (0=なし, 奇数) |
| `MIRROR_MASK_THRESHOLD` | 0.5 | マスク閾値 (0.0-1.0, 高いほどタイトなカット) |

### 3.6 mock_service.py — モックモード

`MOCK_MODE=true` で有効化。APIキーなしで全フローの動作確認が可能。

- 固定の解析結果（3パターンの提案 + placeholder画像）
- インメモリ顧客DB（顧客作成・検索・更新）
- 0.5〜1.5秒のランダム遅延でAPI応答をシミュレート

---

## 4. フロントエンド

### 4.1 ページ構成

| パス | ファイル | 説明 |
|------|----------|------|
| `/` | `app/page.tsx` | iPad操作画面（メインUI） |
| `/projection` | `app/projection/page.tsx` | プロジェクション投影画面 |

### 4.2 状態遷移 (AppState)

```
IDLE → PREFERENCE → CAMERA_ACTIVE → ANALYZING → RESULT
  ↑                      │                │          │
  │                      │                │          │
  └──────────────────────┴────────────────┴──────────┘
                    (リセット / エラー)
```

| 状態 | 説明 | 遷移トリガー |
|------|------|-------------|
| `IDLE` | ウェルカム画面 | 「AIスタイリストを呼ぶ」→ PREFERENCE |
| `PREFERENCE` | 好み入力・顧客情報入力 | 「カメラで撮影」→ CAMERA_ACTIVE / ファイルアップロード → ANALYZING |
| `CAMERA_ACTIVE` | カメラプレビュー | 撮影ボタン → ANALYZING |
| `ANALYZING` | AI解析中（ローディング） | 成功 → RESULT / エラー → PREFERENCE |
| `RESULT` | 提案結果表示 | 「最初からやり直す」→ IDLE |

### 4.3 iPad操作画面 (`page.tsx`)

**IDLE画面:**
- ロゴ + キャッチコピー
- 「AIスタイリストを呼ぶ」ボタン
- 演出画面を開くボタン（右上モニターアイコン）

**PREFERENCE画面:**
- 顧客情報入力（名前・メールアドレス、任意）
- 「復元」ボタン: メールで既存顧客の好みを復元
- スタイルタグ選択（トグルチップUI、複数選択可）
  - テイスト: かっこいい / かわいい / きれいめ / ナチュラル / 個性的
  - スタイル: ストリート / アメカジ / モード / ヴィンテージ / カジュアル / スポーティ
  - 年代感: 70s / 80s / 90s / Y2K / ミリタリー
- 撮影カメラ選択（ブラウザ `getUserMedia`、複数カメラ時のみ表示）
- ミラーカメラ選択（バックエンド接続カメラ、検出時のみ表示）
- 「カメラで撮影する」/「画像をアップロード」ボタン

**CAMERA_ACTIVE画面:**
- カメラプレビュー（鏡像表示）
- ガイド枠（破線）
- 撮影ボタン（赤い点滅付き）
- カメラ切り替えボタン（複数カメラ時のみ）
- 選択済み好みタグ表示

**ANALYZING画面:**
- 撮影画像プレビュー（半透明）
- スキャンライン演出（緑のライン上下移動）
- 30秒タイムアウトで警告表示 + キャンセルボタン
- 90秒で通信タイムアウト

**RESULT画面:**
- 撮影画像 + バウンディングボックスオーバーレイ
- AI分析テキスト + 検出スタイルタグ + ユーザー好みタグ
- 3パターンの提案カード（タイトル、理由、検索キーワード）
- 各提案に商品カード（画像、タイトル、価格、詳細リンク、QRコードボタン）
- 「最初からやり直す」ボタン
- 音声読み上げ（Web Speech API、日本語）
- 部分成功の警告バナー

**WebSocket連携:**
- バックエンド `/ws/projection/control` に常時接続（2秒間隔で自動再接続）
- 状態変更時に全ペイロードを送信
- 撮影時にFLASHコマンド送信

### 4.4 プロジェクション投影画面 (`projection/page.tsx`)

フルスクリーン表示（1920x1080想定）、カーソル非表示。

**IDLE:** ロゴ + パーティクルアニメーション + ウェルカムメッセージ
**PREFERENCE:** ユーザー名表示 + 選択中の好みタグ表示
**CAMERA_ACTIVE:** スキャングリッド + ビューファインダー枠 + スキャンライン
**ANALYZING:** マトリックス風カタカナ演出 + 撮影画像 + 回転リング + スキャンライン
**RESULT:** 分析結果 + 提案パターン + 商品カード + QRコード（SVG直接表示）

**ミラーオーバーレイ:**
- `CAMERA_ACTIVE` / `ANALYZING` 状態でバックエンドから受信した人物セグメンテーション画像を前面に重ねて表示
- z-index: 30 で全画面要素の上に表示

**フラッシュ演出:**
- 撮影時に白い全画面オーバーレイを表示（1.2秒でフェードアウト）

**WebSocket連携:**
- バックエンド `/ws/projection/display` に常時接続（2秒間隔で自動再接続）
- JSON (`STATE_CHANGE`, `FLASH`) と base64テキスト（ミラーフレーム）を同一接続で受信

### 4.5 コンポーネント

#### `QRCodeButton` (`components/QRCode.tsx`)
商品URLのQRコードをモーダル表示するボタン。
- `url` が空または `#` の場合は非表示
- 200x200px SVGQRコード
- モーダル: 商品タイトル + QRコード + 説明テキスト

### 4.6 型定義 (`lib/projection-types.ts`)

```typescript
type AppState = "IDLE" | "PREFERENCE" | "CAMERA_ACTIVE" | "ANALYZING" | "RESULT"

type ProjectionPayload = {
  selectedTags: string[]
  userName: string
  capturedImage: string | null       // base64 data URL
  recommendation: RecommendationData | null
  analyzeTimedOut: boolean
}

type ProjectionMessage =
  | { type: "STATE_CHANGE"; state: AppState; payload: ProjectionPayload }
  | { type: "FLASH" }
  | { type: "REQUEST_STATE" }
  | { type: "MIRROR_FRAME"; frame: string }
```

---

## 5. 環境変数

### バックエンド (`backend/.env`)

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `MOCK_MODE` | - | `true` でモックモード（デフォルト: `false`） |
| `GEMINI_API_KEY` | 実API時 | Google AI Studio のAPIキー |
| `SHOPIFY_STORE_URL` | 実API時 | `example.myshopify.com`（カスタムドメイン不可） |
| `SHOPIFY_STOREFRONT_ACCESS_TOKEN` | 実API時 | Storefront API公開トークン |
| `SHOPIFY_ADMIN_API_ACCESS_TOKEN` | 実API時 | Admin APIトークン（`shpat_` prefix） |
| `SHOPIFY_CLIENT_ID` | 自動更新時 | Shopify App のクライアントID |
| `SHOPIFY_CLIENT_SECRET` | 自動更新時 | Shopify App のクライアントシークレット（`shpss_` prefix） |
| `MIRROR_CAMERA_INDEX` | - | カメラデバイスインデックス（デフォルト: `0`） |
| `MIRROR_WIDTH` | - | キャプチャ幅（デフォルト: `1920`） |
| `MIRROR_HEIGHT` | - | キャプチャ高さ（デフォルト: `1080`） |
| `MIRROR_FPS` | - | 配信フレームレート（デフォルト: `30`） |
| `MIRROR_SEGMENTER` | - | セグメンテーションバックエンド（`auto`/`vision`/`mediapipe`、デフォルト: `auto`） |
| `MIRROR_VISION_QUALITY` | - | Vision品質レベル（`0`=fast, `1`=balanced, `2`=accurate、デフォルト: `2`） |
| `MIRROR_SEG_WIDTH` | - | MediaPipe用内部解像度幅（デフォルト: `640`） |
| `MIRROR_WEBP_QUALITY` | - | WebP出力品質 0-100（デフォルト: `80`） |
| `MIRROR_MASK_BLUR` | - | マスクエッジのぼかし強度（デフォルト: `7`） |
| `MIRROR_MASK_THRESHOLD` | - | マスク閾値 0.0-1.0（デフォルト: `0.5`） |

### フロントエンド

| 変数名 | 説明 |
|--------|------|
| `NEXT_PUBLIC_API_URL` | バックエンドURL（デフォルト: `http://localhost:8000`） |

---

## 6. Docker構成

### docker-compose.yml

```yaml
services:
  backend:
    build: ./backend               # python:3.11-slim
    ports: ["8000:8000"]
    volumes: ["./backend:/app"]     # ホットリロード
    env_file: ./backend/.env
    # カメラ使用時 (Linux): devices: ["/dev/video0:/dev/video0"]

  frontend:
    build: ./frontend              # node:20-alpine
    ports: ["3000:3000"]
    volumes: ["./frontend:/app"]   # ホットリロード
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on: [backend]
```

### カメラアクセス

| 環境 | 方法 |
|------|------|
| Linux ネイティブ | `docker-compose.yml` に `devices:` 追加 |
| Mac Studio (本番) | バックエンドをネイティブ実行 (`uvicorn main:app`) |
| WSL2 (開発) | `usbipd-win` でUSBデバイスをアタッチ |

---

## 7. テスト

### 構成

```
backend/tests/
├── conftest.py            # TestClient + ダミー画像フィクスチャ (MOCK_MODE=true)
├── test_api.py            # APIエンドポイント (9テスト)
├── test_customers.py      # 顧客管理 (7テスト)
├── test_gemini.py         # Geminiスキーマ検証 (5テスト)
└── test_shopify.py        # Shopifyレスポンスパース (4テスト)
                            合計: 25テスト
```

### 実行方法

```bash
# Docker内
docker compose exec backend pytest tests/ -v

# 個別テスト
docker compose exec backend pytest tests/test_api.py::test_analyze_returns_success -v
```

### テストカバレッジ

| ファイル | テスト内容 |
|----------|-----------|
| `test_api.py` | ルート、ヘルスチェック、画像解析（成功/エラー/タイムアウト/部分成功）、バウンディングボックス |
| `test_customers.py` | 顧客検索/作成/更新、バリデーション（必須パラメータ、不正JSON） |
| `test_gemini.py` | Pydanticスキーマ検証、JSONラウンドトリップ、エラーレスポンス構造 |
| `test_shopify.py` | 認証情報不足、空キーワード、レスポンスパース、APIエラーハンドリング |

---

## 8. 依存パッケージ

### バックエンド (`requirements.txt`)

| パッケージ | 用途 |
|-----------|------|
| fastapi | Webフレームワーク |
| uvicorn | ASGIサーバー |
| google-generativeai | Gemini API クライアント |
| requests | HTTP通信（Shopify API） |
| python-dotenv | .env読み込み |
| pydantic | スキーマ定義・バリデーション |
| python-multipart | ファイルアップロード |
| Pillow | 画像処理 |
| opencv-python-headless | カメラキャプチャ・画像処理 |
| mediapipe | 人物セグメンテーション (Linux/Docker フォールバック) |
| pyobjc-framework-Vision | Apple Vision Framework (macOS のみ) |
| pyobjc-framework-Quartz | CGImage/CVPixelBuffer 変換 (macOS のみ) |
| websockets | WebSocket対応 |
| pytest, pytest-asyncio, httpx | テスト |

### フロントエンド (`package.json`)

| パッケージ | 用途 |
|-----------|------|
| next 16.1.6 | Reactフレームワーク |
| react / react-dom 19.2.3 | UI |
| framer-motion | アニメーション |
| lucide-react | アイコン |
| qrcode.react | QRコード生成 |
| clsx / tailwind-merge | CSS ユーティリティ |
| tailwindcss v4 | スタイリング |

---

## 9. Shopify App 設定

### `85ai/shopify.app.toml`

```toml
client_id = "d144ba4ce2d9ff8a6e3fde24565d23df"
name = "85ai"
application_url = "http://localhost:3000"
embedded = true

[access_scopes]
scopes = "read_customers,write_customers,read_products,unauthenticated_read_product_listings"

[webhooks]
api_version = "2026-01"
```

### トークンプレフィクス一覧

| プレフィクス | 意味 |
|-------------|------|
| `shpat_` | Admin API アクセストークン |
| `shpss_` | Client Secret（トークンではない） |
| `shpca_` | カスタムアプリトークン |

### Shopify顧客メタフィールド

| フィールド | 値 |
|-----------|-----|
| Namespace | `custom` |
| Key | `style_preferences` |
| Type | `json` |
| Value | `["ストリート", "90s", "かっこいい"]` |

---

## 10. エラーハンドリング

| 箇所 | 対策 |
|------|------|
| Gemini API タイムアウト | 60秒タイムアウト設定、UI側30秒で警告・90秒でfetch中断 |
| Gemini API エラー | `_error: true` フラグ付きJSON返却、フロントで検知 |
| Shopify 検索失敗 | 部分成功: 解析結果は返し、`warning`フィールドで通知 |
| Shopify 認証情報不足 | エラーステータス返却 |
| Admin API トークン失効 | `ShopifyTokenManager` が期限5分前に自動更新 |
| カメラアクセス拒否 | エラーメッセージ表示 + ファイルアップロードへフォールバック |
| 顧客登録失敗 | サイレントキャッチ、登録なしで撮影に進む |
| 不正JSON (preferences) | 空配列にフォールバック |

---

## 11. 起動方法

### 開発環境 (Docker)

```bash
cd /home/u256003/repos/85ai
docker compose up --build

# バックエンド: http://localhost:8000
# フロントエンド: http://localhost:3000
# プロジェクション: http://localhost:3000/projection
```

### 本番環境 (Mac Studio)

```bash
# バックエンド（カメラ直接アクセスのためネイティブ実行）
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# フロントエンド
cd frontend
npm install && npm run build && npm start
```

### 別デバイスからのアクセス

iPad等からアクセスする場合、`NEXT_PUBLIC_API_URL` をサーバーのIPアドレスに設定:
```
NEXT_PUBLIC_API_URL=http://192.168.x.x:8000
```
