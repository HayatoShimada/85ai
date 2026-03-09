# メタデータ仕様書

## 現状のメタデータ (2026-03-09 時点)

### 商品 (207件)

#### productType (フリーテキスト)
| 値 | 件数 | 備考 |
|----|------|------|
| (空) | 83 | 未設定 |
| USED | 111 | 誤用 (状態をカテゴリに入れている) |
| NEW | 13 | 誤用 |

**問題**: productTypeに商品カテゴリではなく状態 (USED/NEW) が入っている。

#### productCategory (Shopify標準タクソノミー) ✅ 設定済み
| カテゴリ | 件数 |
|---------|------|
| Shirts | 59 |
| Sweaters | 29 |
| Jackets (Activewear) | 27 |
| Sweatshirts | 27 |
| Coats & Jackets | 22 |
| Vests | 10 |
| Sport Jackets | 9 |
| Parkas | 7 |
| Cardigans | 6 |
| Trousers | 5 |
| Trench Coats | 2 |
| Trucker Jackets | 1 |
| Windbreakers | 1 |
| Tank Tops | 1 |
| Print Books | 1 |

#### tags
| 値 | 件数 | 備考 |
|----|------|------|
| USED | 105 | 状態タグのみ |
| NEW | 12 | 状態タグのみ |
| VAN HEUSEN | 1 | ブランド (1件のみ) |

**問題**: 素材・スタイル・色・ブランド等のタグが入っていない。AI検索に使えない。

#### Shopify標準メタフィールド (shopify: namespace)
| メタフィールド | 設定率 | 型 |
|--------------|--------|-----|
| target-gender | 99.0% (205/207) | list.metaobject_reference |
| color-pattern | 98.6% (204/207) | list.metaobject_reference |
| fabric | 98.1% (203/207) | list.metaobject_reference |
| size | 97.6% (202/207) | list.metaobject_reference |
| age-group | 95.2% (197/207) | list.metaobject_reference |
| top-length-type | 70.0% (145/207) | list.metaobject_reference |
| neckline | 44.9% (93/207) | list.metaobject_reference |
| sleeve-length-type | 29.0% (60/207) | list.metaobject_reference |
| outerwear-clothing-features | 23.2% (48/207) | list.metaobject_reference |
| clothing-features | 12.1% (25/207) | list.metaobject_reference |
| fit | 1.9% (4/207) | list.metaobject_reference |
| pants-length-type | 1.9% (4/207) | list.metaobject_reference |

**サンプル値 (解決済み)**:
- fabric: コットン, ウール, リネン, etc.
- color-pattern: ブルー, ネイビー, ブラック, etc.
- size: XL, L, M, etc.
- target-gender: 男性
- age-group: 成人
- top-length-type: ロング
- neckline: クルーネック, Vネック, etc.

#### その他メタフィールド
| メタフィールド | 件数 | 備考 |
|--------------|------|------|
| mc-facebook:google_product_category | 200 | Google Shopping連携用 |
| global:description_tag | 50 | SEO用メタディスクリプション |

---

### 顧客 (14件)

#### 基本フィールド
- firstName, lastName: 大半が未設定 (名前なしが多い)
- email: 全員設定済み
- tags: ほぼ空 (1名のみ `Login with Shop, Shop`)

#### カスタムメタフィールド
| メタフィールド | 設定件数 | 型 | 備考 |
|--------------|---------|-----|------|
| custom:style_preferences | 1/14 | json | テスト顧客のみ |

**サンプル値**: `["ストリート","90s","かっこいい"]`

**問題**: 体型情報なし。スタイル嗜好も1名のみ。

---

## 正規化計画

### 1. productType の修正
productCategory.name をそのまま productType に反映する。

| 修正前 | 修正後 |
|--------|--------|
| "" or "USED" or "NEW" | "Shirts", "Sweaters", "Jackets", etc. |

USED/NEW は tags に残す。

### 2. tags の拡充 (Geminiバッチ生成)
| タグカテゴリ | 例 | 用途 |
|-------------|-----|------|
| 詳細カテゴリ | 長袖シャツ, ボタンダウン, ネルシャツ | 検索絞り込み |
| 素材 (日英) | コットン, Cotton | 検索・AI提案 |
| スタイル | カジュアル, ミリタリー, アメカジ | AI提案マッチング |
| 色・柄 | ネイビー, チェック柄 | 検索・ビジュアル提案 |
| ブランド | Claiborne, Eddie Bauer | 検索 |
| 年代 | 90s, ヴィンテージ | AI提案マッチング |
| 特徴 | オーバーサイズ, ヘビーウェイト | AI提案 |
| サイズ | L, XL | 体型マッチング |
| 状態 | USED, NEW | フィルタ |

### 3. 商品カスタムメタフィールド (新規追加)
Shopify標準メタフィールドでカバーできない、AI提案専用の構造化データ。

| namespace:key | 型 | 用途 | 値の例 |
|--------------|-----|------|--------|
| custom:brand | single_line_text_field | ブランド名 | "Eddie Bauer" |
| custom:style | json | スタイルタグ配列 | ["カジュアル","アメカジ","アウトドア"] |
| custom:era | single_line_text_field | 年代 | "90s" |
| custom:features | json | 特徴タグ配列 | ["オーバーサイズ","ヘビーウェイト"] |
| custom:measurements | json | 実寸情報 (cm) | {"shoulder":52,"chest":60,"length":75,"sleeve":62} |

**Shopify標準との役割分担**:
- 素材 → shopify:fabric (98%設定済み)
- 色・柄 → shopify:color-pattern (99%設定済み)
- サイズ表記 → shopify:size (98%設定済み)
- 性別 → shopify:target-gender (99%設定済み)
- ネックライン → shopify:neckline (45%、要補完)
- 袖丈 → shopify:sleeve-length-type (29%、要補完)
- ブランド → **custom:brand** (Shopify標準にブランドフィールドなし)
- スタイル → **custom:style** (Shopify標準にスタイルフィールドなし)
- 年代 → **custom:era** (Shopify標準にないフィールド)
- 特徴 → **custom:features** (clothing-featuresより自由度高い)
- 実寸 → **custom:measurements** (Shopify標準にないフィールド)

### 4. 顧客カスタムメタフィールド (拡張)

| namespace:key | 型 | 用途 | 値の例 |
|--------------|-----|------|--------|
| custom:style_preferences | json | スタイル嗜好 (既存) | ["ストリート","90s","かっこいい"] |
| custom:body_measurements | json | 体型情報 | {"height":175,"shoulder_width":45,"chest":95,"waist":80,"weight":70} |

**body_measurements フィールド定義**:
| フィールド | 単位 | 説明 |
|-----------|------|------|
| height | cm | 身長 |
| shoulder_width | cm | 肩幅 |
| chest | cm | 胸囲 |
| waist | cm | ウエスト |
| weight | kg | 体重 (任意) |

---

## AI提案フロー (拡張後)

```
1. 顧客情報取得
   ├─ custom:style_preferences → スタイル嗜好
   └─ custom:body_measurements → 体型情報

2. 画像解析 (Gemini)
   ├─ 服装分析 → detected_style, recommendations
   └─ 体型情報を加味 → サイズ適合を考慮した提案

3. 商品検索 (Storefront API)
   ├─ search_keywords → テキスト検索
   └─ tags でフィルタリング可能

4. 商品マッチング強化 (将来)
   ├─ custom:style × customer:style_preferences → スタイル適合度
   ├─ custom:measurements × customer:body_measurements → サイズ適合度
   ├─ shopify:fabric, shopify:color-pattern → 素材・色の多様性
   └─ custom:era × customer:style_preferences → 年代感マッチ
```

---

## APIスコープ (85ai_ver2)

```
read_products, write_products
read_customers, write_customers
read_metaobjects, write_metaobjects
```

Shopify API version: 2026-01
Webhook API version: 2026-04
