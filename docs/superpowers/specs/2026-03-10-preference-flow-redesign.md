# PreferenceView 2ステップ化 + ユーザー情報フロー再設計

## 概要

PreferenceViewを2ステップに分離し、ユーザー情報入力フローを整理する。

- ステップ1: 名前・メール・プライバシーポリシー同意・メールサブスクリプション
- ステップ2: スタイルタグ・体型入力・カメラ設定
- ユーザー情報未入力時はステップ2をスキップして撮影へ直行

## フロー

```
IDLE → PREFERENCE (Step 1 → Step 2) → CAMERA_ACTIVE → ANALYZING → RESULT
```

ステートマシン自体は変更なし。PreferenceView内部に `step` state (1 or 2) を持つ。

## ステップ1: お客様情報

### 表示要素
- お名前（テキスト入力）
- メールアドレス（テキスト入力）+ 「好みを復元」ボタン
- チェックボックス: 「新着・セール情報をメールで受け取る」（Shopify emailMarketingConsent）
- チェックボックス: 「個人情報の取り扱いについてに同意する」（リンク部分クリックでモーダル）
- ボタン: 「次へ」（名前+メール入力済み & ポリシー同意時のみ有効）
- ボタン: 「スキップして撮影へ」→ カメラ/アップロードへ直行

### 復元ボタン押下時
- Shopify検索 → name/email/style_preferences/body_measurements/emailMarketingConsentをセット
- 自動的にステップ2へ遷移（プリフィル済み）

### スキップ時
- customer登録なし、selectedTags=[], bodyMeasurements={} のまま
- カメラ or ファイルアップロードへ

## ステップ2: 好み・体型入力

### 表示要素
- スタイルタグ選択（既存のまま）
- 体型入力フィールド5つ（既存のまま）
- カメラ設定（既存のまま）
- ボタン: 「カメラで撮影に進む」/ 「画像をアップロード」

### カメラ/アップロード押下時
- registerCustomer を呼び出し（name, email, tags, bodyMeasurements, emailMarketingConsent）
- Shopifyに顧客情報を保存/更新してからカメラへ

## プライバシーポリシーモーダル

- `shop.85-store.com/policies/privacy-policy` の全文を表示
- テキストはフロントエンドにハードコード（CORS回避）
- 「閉じる」ボタンで閉じる

## バックエンド変更

### POST /api/customers
- `email_marketing_consent` パラメータ追加（bool）
- `customer_service.py` で Shopify `emailMarketingConsent` フィールドを設定
- 値: `{marketingState: "SUBSCRIBED", consentUpdatedAt: <now>}` or `NOT_SUBSCRIBED`

### GET /api/customers
- レスポンスに `email_marketing_consent` を含める
- GraphQLクエリに `emailMarketingConsent { marketingState }` 追加

## 変更対象ファイル

| ファイル | 変更 |
|---------|------|
| `frontend/src/components/operator/PreferenceView.tsx` | 2ステップ化、ポリシーモーダル追加 |
| `frontend/src/app/page.tsx` | スキップ動線、復元→ステップ2遷移 |
| `frontend/src/hooks/useBackendAPI.ts` | emailMarketingConsent パラメータ追加 |
| `backend/routers/customers.py` | email_marketing_consent パラメータ追加 |
| `backend/customer_service.py` | emailMarketingConsent GraphQL対応 |
| `backend/mock_service.py` | モック対応 |
