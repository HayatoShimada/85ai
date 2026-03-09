# 85-Store AI店員システム 設計ドキュメント

## 1. プロジェクト概要

実店舗（オフライン）とネットショップ（Shopify）のデータ、そして最新のAI（Gemini）を融合させた「次世代の古着屋体験」を提供するAI接客システム。
お客様がその日に着ている服をカメラで読み取り、AIがそれに合う「一点モノ」の古着をShopifyのリアルタイム在庫から提案する。

### 本番想定環境
- **中核ハブ:** Mac Studio（バックエンド実行・カメラ認識・AI通信・ミラー映像処理）
- **操作端末:** iPad（ブラウザベースのリモートUI）
- **空間デバイス:** 超短焦点プロジェクター + 店舗用スピーカー
- **通信:** iPad ↔ Mac Studio 間はWebSocket経由で状態同期

### 開発・検証環境
- **Ubuntu (WSL2含む)** 上でバックエンド・フロントエンドの全機能を開発・テスト可能
- カメラはUSB Webカメラまたはブラウザ内蔵カメラ（`getUserMedia`）を使用
- プロジェクション演出はブラウザ上のプレビューで代替

---

## 2. システムアーキテクチャ

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

### デバイス間通信

iPad（操作）とプロジェクター（表示）は別デバイス・別ブラウザで動作する。
状態同期はバックエンドのWebSocketリレー（`ProjectionManager`）経由で行う。

- iPad → `WS /ws/projection/control` → Backend → `WS /ws/projection/display` → プロジェクター
- ミラーフレーム: Backend(OpenCV + Vision/MediaPipe) → `WS /ws/projection/display` → プロジェクター

---

## 3. 技術スタック

| レイヤー | 技術 | 用途 |
|---------|------|------|
| フロントエンド | Next.js 16 (React 19) | SPA・カメラUI・演出画面 |
| スタイリング | Tailwind CSS v4 | UIデザイン |
| アニメーション | Framer Motion | 画面遷移・ローディング演出 |
| アイコン | Lucide React | UIアイコン |
| QRコード | qrcode.react | 商品QRコード生成 |
| バックエンド | FastAPI (Python 3.11+) | REST API + WebSocket サーバー |
| AI推論 | Google Gemini API (`gemini-3.1-pro`) | 服装解析・提案生成 |
| EC連携（商品） | Shopify Storefront API (GraphQL, `2026-01`) | 在庫商品検索 |
| EC連携（顧客） | Shopify Admin API (GraphQL, `2026-01`) | 顧客登録・好み保存 |
| 認証 | Client Credentials Grant | Admin APIトークン自動更新（24h） |
| ミラー映像 | OpenCV + Apple Vision (Neural Engine) / MediaPipe | 人物セグメンテーション (1920x1080@30fps) |
| 画像処理 | Pillow | 画像デコード |
| コンテナ | Docker / Docker Compose | 環境統一・開発 |
| テスト | pytest + pytest-asyncio + httpx | 25テスト |

---

## 4. API設計

### REST エンドポイント

#### `POST /api/analyze`

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
    "box_ymin": 120, "box_xmin": 250, "box_ymax": 650, "box_xmax": 750,
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

#### `GET /api/customers?email={email}`

メールアドレスで既存顧客を検索し、保存済みの好みタグを取得する。

#### `POST /api/customers`

顧客の登録または既存顧客の好みを更新。Form: `name`, `email`, `style_preferences`

#### `GET /api/health`

ヘルスチェック。各外部API（Gemini / Shopify）の設定状況を返す。

#### `GET /api/mirror/cameras`

バックエンドサーバーに接続されたカメラデバイスの一覧と現在の選択を返す。

#### `POST /api/mirror/cameras/{index}`

ミラーカメラを指定インデックスに切り替える。

#### `POST /api/mirror/start` / `POST /api/mirror/stop`

ミラーカメラの手動起動/停止。

### WebSocket エンドポイント

#### `WS /ws/mirror`
ミラーカメラの人物切り抜きフレームをbase64 WebPで配信。接続時に自動起動。

#### `WS /ws/projection/control`
iPad（操作画面）から状態変更・フラッシュ指示を受信。

#### `WS /ws/projection/display`
プロジェクション表示画面に状態変更・フラッシュ・ミラーフレームを配信。

---

## 4.1 スタイルタグ定義

| カテゴリ | タグ |
|---------|------|
| テイスト | かっこいい、かわいい、きれいめ、ナチュラル、個性的 |
| スタイル | ストリート、アメカジ、モード、ヴィンテージ、カジュアル、スポーティ |
| 年代感 | 70s、80s、90s、Y2K、ミリタリー |

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
IDLE（待機）→ PREFERENCE（好み入力）→ CAMERA_ACTIVE（撮影）→ ANALYZING（解析中）→ RESULT（結果）
  ↑                                                                                    │
  └──────────────────────────────── リセット / エラー ←──────────────────────────────────┘
```

| 画面 | iPad操作画面 | プロジェクション画面 |
|------|-------------|-------------------|
| IDLE | スタートボタン | ロゴ + パーティクル演出 |
| PREFERENCE | 好みタグ選択 + 顧客入力 + カメラ選択 | 選択中タグ表示 |
| CAMERA_ACTIVE | カメラプレビュー + 撮影ボタン | スキャングリッド + ミラー映像 |
| ANALYZING | スキャン演出 + タイムアウト表示 | マトリックス風演出 + ミラー映像 |
| RESULT | 分析結果 + 商品カード + QRボタン | 大画面レイアウト + QRコード直接表示 |

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
│  撮影カメラ: [プルダウン] (ブラウザ)   │
│  ミラーカメラ: [プルダウン] (サーバー)  │
│                                     │
│  [カメラで撮影] [画像をアップロード]   │
└─────────────────────────────────────┘
```

---

## 7. ミラーカメラシステム

### アーキテクチャ

```
┌─────────────┐     ┌─────────────────────────────────────┐     ┌──────────────┐
│ USB カメラ   │────→│  Backend (mirror_service.py)          │────→│ プロジェクター│
│ 1920x1080   │     │                                      │     │ WebP表示     │
│ MJPEG       │     │  OpenCV キャプチャ                     │     └──────────────┘
└─────────────┘     │       ↓                              │
                    │  左右反転 (鏡像)                       │
                    │       ↓                              │
                    │  ┌────────────────────────────────┐  │
                    │  │ macOS: Apple Vision Framework   │  │
                    │  │  VNGeneratePersonSegmentation   │  │
                    │  │  Neural Engine (accurate mode)  │  │
                    │  │  内部マスク: 1024x768           │  │
                    │  ├────────────────────────────────┤  │
                    │  │ Linux: MediaPipe Selfie Seg.    │  │
                    │  │  Landscape model (CPU)          │  │
                    │  │  内部マスク: 640x360 → 拡大     │  │
                    │  └────────────────────────────────┘  │
                    │       ↓                              │
                    │  マスク後処理 (閾値 + ガウシアンブラー) │
                    │       ↓                              │
                    │  BGRA合成 → WebPエンコード → base64   │
                    └─────────────────────────────────────┘
```

### セグメンテーションバックエンド

| 環境 | バックエンド | ハードウェア | 処理速度 |
|------|-------------|-------------|---------|
| macOS (Apple Silicon) | Apple Vision Framework | Neural Engine | ~10-15ms/frame |
| Linux / Docker | MediaPipe Selfie Seg. | CPU | ~15-25ms/frame |

`MIRROR_SEGMENTER=auto`（デフォルト）で自動判別。macOS では Vision、Linux では MediaPipe を使用。

### 処理フロー (1920x1080@30fps)

1. OpenCV + MJPEG でカメラフレーム取得 (~2ms)
2. 左右反転（鏡像）(~1ms)
3. セグメンテーション:
   - **Vision**: CGImage変換 → Neural Engine 推論 → CVPixelBuffer からマスク取得 (~10-15ms)
   - **MediaPipe**: 640幅に縮小 → CPU推論 → マスクを元解像度に拡大 (~15-25ms)
4. マスク後処理: 閾値適用 + ガウシアンブラー (~2ms)
5. BGRA合成 + WebPエンコード (~5-10ms)
6. base64 → WebSocket配信
7. 適応スリープ（処理時間を差し引いてFPSを維持）

### カメラ管理

- `GET /api/mirror/cameras`: サーバー接続カメラの一覧 + セグメンテーションバックエンド情報
- `POST /api/mirror/cameras/{index}`: カメラ切り替え（稼働中なら自動再起動）
- iPad UIからプルダウンで選択可能
- Linux: `/dev/video*` 走査、macOS: インデックス0-9試行
- 対応デバイス: USB Webカメラ、内蔵カメラ、USB キャプチャボード

### 自動起動/停止

`ProjectionManager` が状態変更を監視:
- `CAMERA_ACTIVE` / `ANALYZING` → ミラー自動起動
- その他の状態 → ミラー自動停止

---

## 8. 認証・トークン管理

### Shopify Admin API トークン

- 24時間で失効するトークンを `ShopifyTokenManager` が自動更新
- Client Credentials Grant: `POST /admin/oauth/access_token`
- スレッドセーフ（ダブルチェックロッキング）
- 期限の5分前に更新
- フォールバック: `.env` の静的トークン（`shpat_` prefix）

### トークンプレフィクス

| プレフィクス | 意味 |
|-------------|------|
| `shpat_` | Admin API アクセストークン |
| `shpss_` | Client Secret |
| `shpca_` | カスタムアプリトークン |

---

## 9. 顧客データ活用（Shopify Admin API連携）

### 顧客管理フロー

```
初回来店:
  メール入力 → Shopify顧客検索 → 見つからない → 新規顧客作成 + 好みタグ保存

リピーター来店:
  メール入力 → Shopify顧客検索 → 見つかった → 保存済み好みタグを復元 → 更新も可能
```

### Shopify顧客メタフィールド

| 項目 | 値 |
|------|------|
| Namespace | `custom` |
| Key | `style_preferences` |
| Type | `json` |
| 例 | `["かっこいい", "ストリート", "90s"]` |

### データ活用の展望

- **来店履歴 x 好みタグ:** リピーターの好みの変化をトラッキング
- **購買データ x 提案データ:** AIの提案が実際の購買にどの程度つながったかを分析
- **顧客セグメント:** Shopifyの顧客グループ機能と連動し、好みベースのマーケティング施策を実施

---

## 10. エラーハンドリング

| 箇所 | 対策 |
|------|------|
| Gemini API | 60秒タイムアウト、UI側30秒で警告・90秒でfetch中断 |
| Shopify 検索失敗 | 部分成功: 解析結果は返し、`warning`フィールドで通知 |
| Admin API トークン | `ShopifyTokenManager` が期限5分前に自動更新 |
| カメラアクセス拒否 | ファイルアップロードへフォールバック |
| 顧客登録失敗 | サイレントキャッチ、登録なしで撮影に進む |
| 不正JSON | 空配列にフォールバック |

---

## 11. 開発環境セットアップ

### 前提条件

- Ubuntu 22.04+ (WSL2でも可)
- Python 3.11+
- Node.js 20+
- Docker / Docker Compose (推奨)

### 環境変数

`backend/.env` に設定（`backend/.env.example` 参照）:

```env
MOCK_MODE="false"
GEMINI_API_KEY="your-gemini-api-key"
SHOPIFY_STORE_URL="your-store.myshopify.com"
SHOPIFY_STOREFRONT_ACCESS_TOKEN="your-storefront-token"
SHOPIFY_ADMIN_API_ACCESS_TOKEN="shpat_your-admin-token"
SHOPIFY_CLIENT_ID="your-client-id"
SHOPIFY_CLIENT_SECRET="shpss_your-client-secret"
NEXT_PUBLIC_API_URL="http://localhost:8000"
```

### WSL2 固有の注意点

- **カメラアクセス:** `usbipd-win` でUSBデバイスをWSL2にアタッチ、またはWindows側ブラウザの `getUserMedia` で代替
- **ミラーカメラ:** Docker内からホストカメラへのアクセスには `devices:` 設定が必要（Linuxのみ）
- **ネットワーク:** WSL2のIPへWindows側からは `localhost` でフォワーディング

---

## 12. テスト

```bash
docker compose exec backend pytest tests/ -v
# 25テスト: API(9), 顧客管理(7), Geminiスキーマ(5), Shopifyパース(4)
```

---

## 13. 将来の拡張ポイント

### RAG（検索拡張生成）
Shopifyの全商品データをベクトルDBに格納し、Geminiに「在庫リストの中から最も合うもの」を選ばせるRAGアプローチ。

### 音声入力
マイクからの音声リクエストをGeminiに渡し、画像+音声のマルチモーダル入力に対応。

### google.genai 移行
`google.generativeai` パッケージが deprecated のため、`google.genai` パッケージへの移行が必要。

### CoreML モデル直接実行
現在の Apple Vision Framework 方式に加え、coremltools で `.mlmodel` を直接ロードする方式も検討可能。
FP16/Int8 量子化モデルを Neural Engine で実行することで、さらなる高速化が期待できる。
