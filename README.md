# Vintage AI Shop Assistant (次世代古着屋AI店員デバイス)

実店舗（オフライン）とネットショップ（Shopify）のデータ、そして最新のAI（Gemini）を融合させた「次世代の古着屋体験」を提供するAI接客デバイスです。

## プロジェクト概要

お客様がその日に着ている服をカメラで読み取り、AIがそれに合う「一点モノ」の古着をShopifyのリアルタイム在庫から提案します。
Raspberry Pi等のデバイス上でキオスク端末として動作させることを想定して設計・開発されています。

## 主な機能

1. **コーディネート解析**: デバイスのカメラでお客様の服装を撮影し、Gemini APIを用いて現在のコーディネートの特徴やスタイルを解析します。
2. **アイテム提案**: 解析結果をもとに、今の服装に合うおすすめの古着の検索条件（キーワードやスタイル）をAIが推論します。
3. **Shopifyリアルタイム連携**: 推論されたキーワードを用いてShopify Storefront APIを即座に叩き、**現在在庫がある**一点モノの古着の中から最適な商品を複数ピックアップして画面に提案します。

## 技術スタック

デバイス側でのUI表示に特化したフロントエンドと、AI処理・EC検索処理を担うバックエンドのモダンな構成となっています。

### フロントエンド (`frontend/`)
* **フレームワーク**: Next.js 16 (React 19)
* **スタイリング**: Tailwind CSS v4
* **UI/アニメーション**: Framer Motion, Lucide React

### バックエンド (`backend/`)
* **フレームワーク**: FastAPI (Python)
* **AI・推論エンジン**: Google Gemini API (`gemini-2.5-flash`)
* **EC・データ連携**: Shopify Storefront API (GraphQL)

## Dockerを使用したテスト環境の構築 (推奨)

Dockerを利用することで、バックエンドとフロントエンドの両方の環境を簡単に構築し、テストすることができます。

### 前提条件
- Docker および Docker Compose がインストールされていること

### 起動手順

1. `backend/` ディレクトリ内に `.env` ファイルを作成し、必要な環境変数（APIキーなど）を設定してください。（`.env.example` を参考にしてください）

2. プロジェクトのルートディレクトリで以下のコマンドを実行し、コンテナをビルド・起動します。

```bash
docker-compose up -d --build
```

3. 起動が完了すると、以下のURLでアクセス可能になります。
   * **フロントエンド**: `http://localhost:3000`
   * **バックエンド (API/Swagger UI)**: `http://localhost:8000/docs`

4. 終了する場合は、以下のコマンドを実行します。

```bash
docker-compose down
```

---

## ローカル開発環境のセットアップ (Dockerを使用しない場合)

### プロジェクト全体の準備

事前にGemini APIのキーとShopify Storefront APIのアクセストークンを取得しておく必要があります。

### バックエンドの起動

1. `backend` ディレクトリに移動します。
2. 必要なPythonパッケージをインストールします。
3. `backend` フォルダ直下に `.env` ファイルを作成し、必要な環境変数（APIキーなど）を設定します。
4. FastAPIサーバーを起動します。

```bash
cd backend
# 仮想環境の作成とアクティベート (推奨)
python -m venv venv
source venv/bin/activate  # macOS/Linuxの場合

# 依存関係のインストール
pip install fastapi uvicorn python-dotenv python-multipart
# (その他gemini_service, shopify_service内で使用されているライブラリが必要に応じて追加されます)

# 開発サーバーの起動
uvicorn main:app --reload
```
APIサーバーはデフォルトで `http://localhost:8000` で稼働します。

### フロントエンドの起動

1. `frontend` ディレクトリに移動します。
2. npmモジュールをインストールします。
3. 開発サーバーを起動します。

```bash
cd frontend
npm install
npm run dev
```
フロントエンドは `http://localhost:3000` にアクセスして確認できます。

## 設計ドキュメント
全体のシステム構成、ハードウェアの構成案、およびRAG導入のような将来のステップについては `DESIGN.md` をご参照ください。
