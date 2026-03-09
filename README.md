# 85-Store AI Shop Assistant

実店舗とShopifyのデータ、最新AI（Gemini 1.5 Pro）を融合した「次世代の古着屋体験」を提供するAI接客システムです。

## プロジェクト概要

来店客の服装をカメラで撮影 → AIが解析 → Shopifyのリアルタイム在庫から相性の良い古着を提案します。

### 本番構成
- **Mac Studio**: バックエンド実行 + USBカメラ（ミラー用）
- **iPad**: ブラウザベースの操作UI（タッチスクリーン）
- **プロジェクター**: 演出画面を投影

### 開発構成
- **Ubuntu / WSL2**: Docker Composeで全機能を開発・テスト

## 主な機能

1. **コーディネート解析** — カメラ撮影 or 画像アップロード → Gemini 1.5 Pro で服装を解析
2. **パーソナライズ提案** — ユーザーの好みタグ（スタイル・年代感等）を加味した最大3パターンの提案
3. **Shopifyリアルタイム連携** — Storefront API (GraphQL) で在庫がある商品のみを検索・表示
4. **顧客管理** — Admin API で好みデータをメタフィールドに保存、リピーターの好み自動復元
5. **ミラー演出** — USBカメラ + MediaPipeで人物切り抜き → プロジェクターにリアルタイム投影
6. **プロジェクション同期** — iPad操作とプロジェクター表示をWebSocketで別デバイス間同期
7. **QRコード** — 各商品のShopify URLをQR表示 → スマホで読み取ってEC購入
8. **音声読み上げ** — 解析結果をWeb Speech APIで日本語読み上げ

## 技術スタック

| レイヤー | 技術 |
|----------|------|
| バックエンド | FastAPI (Python 3.11+), Uvicorn |
| AI解析 | Google Gemini 1.5 Pro (構造化JSON出力) |
| 商品検索 | Shopify Storefront API (GraphQL, `2026-01`) |
| 顧客管理 | Shopify Admin API (GraphQL, `2026-01`) |
| 認証 | Client Credentials Grant + 自動トークン更新 |
| ミラー | OpenCV + MediaPipe Selfie Segmentation |
| フロントエンド | Next.js 16 (React 19), Tailwind CSS v4, Framer Motion |
| コンテナ | Docker Compose |
| テスト | pytest (25テスト) |

## 起動方法

### Docker Compose（開発環境）

```bash
# 1. 環境変数を設定
cp backend/.env.example backend/.env
# backend/.env を編集してAPIキー等を設定

# 2. ビルド&起動
docker compose up --build

# フロントエンド: http://localhost:3000
# バックエンドAPI: http://localhost:8000
# プロジェクション: http://localhost:3000/projection
# Swagger UI: http://localhost:8000/docs
```

### ネイティブ起動（本番 / カメラ使用時）

```bash
# バックエンド（カメラ直接アクセスのためネイティブ実行推奨）
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# フロントエンド
cd frontend
npm install
npm run dev
```

### モックモード（APIキー不要）

`backend/.env` で `MOCK_MODE=true` に設定すると、Gemini/Shopify APIなしで全フローの動作確認が可能です。

## 環境変数

`backend/.env` に設定（`backend/.env.example` 参照）:

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `MOCK_MODE` | - | `true` でモックモード |
| `GEMINI_API_KEY` | 実API時 | Google AI Studio APIキー |
| `SHOPIFY_STORE_URL` | 実API時 | `example.myshopify.com` |
| `SHOPIFY_STOREFRONT_ACCESS_TOKEN` | 実API時 | Storefront API公開トークン |
| `SHOPIFY_ADMIN_API_ACCESS_TOKEN` | 実API時 | Admin APIトークン (`shpat_`) |
| `SHOPIFY_CLIENT_ID` | 自動更新時 | Shopify App クライアントID |
| `SHOPIFY_CLIENT_SECRET` | 自動更新時 | Client Secret (`shpss_`) |
| `NEXT_PUBLIC_API_URL` | 別デバイス時 | バックエンドURL (デフォルト: `http://localhost:8000`) |

## テスト

```bash
docker compose exec backend pytest tests/ -v
# 25テスト: API, 顧客管理, Geminiスキーマ, Shopifyパース
```

## ドキュメント

| ファイル | 内容 |
|----------|------|
| [SPEC.md](SPEC.md) | 現状仕様書（API詳細、型定義、全サービス仕様） |
| [DESIGN.md](DESIGN.md) | システム設計ドキュメント |
| [PROJECTION_DESIGN.md](PROJECTION_DESIGN.md) | プロジェクション演出画面の設計 |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | 4段階実装計画（全Phase完了） |

## WSL2 固有の注意点

- **カメラ**: WSL2からUSBカメラを使うには `usbipd-win` が必要。ブラウザカメラ（`getUserMedia`）は問題なく動作
- **ミラーカメラ**: Docker内からホストカメラへのアクセスには `devices:` 設定が必要（Linuxのみ）。Mac StudioではバックエンドをネイティブBash実行推奨
