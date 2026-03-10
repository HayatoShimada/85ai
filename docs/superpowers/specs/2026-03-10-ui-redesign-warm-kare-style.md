# UI Redesign: Warm & Approachable Kare-Style Design

## Overview

85-Store AI Shop Assistantの全UI刷新。現在の近未来・ネオン・グラスモーフィズムなデザインから、Susan Kareのピクセルアートに着想を得た、温かみのある親しみやすいデザインへ転換する。

## Design Philosophy

### 3 Principles

1. **親しみやすいAI** — 失敗してもOK、完璧じゃなくていい。エラー時は片耳たれネコで「ごめんね」を表現
2. **店員の相方** — AIは主役ではなく、隣にいるバディ。チャットバブル風UIでカジュアルな対話感
3. **Kareスタイルのピクセルアート** — テクノロジーに温もりを加えるアイコンシステム

### What We're Removing

- グラスモーフィズム (backdrop-blur, 半透明カード)
- ネオンカラー (emerald glow, cyan accents)
- 回転リング、パルスアニメーション等の「近未来」表現
- 「AI」「次世代」を強調するビジュアル
- 暗い配色のiPad UI

### What We're Adding

- Susan Kare「Cat on Gray」にインスパイアされたピクセルアートネコアイコン
- 85-store.comブランドカラー (Orange × Navy)
- チャットバブル風のAIメッセージ表示
- 温かみのあるカードUI (白背景 + 薄いボーダー + 微かなシャドウ)
- ネコ表情によるAI状態の可視化

## Color System

### Brand Colors (from 85-store.com CSS variables)

| Token | Hex | Usage |
|-------|-----|-------|
| `primary` | `#FF6B35` | CTA, アクセント, ネコのほっぺ |
| `primary-light` | `#FF8A5B` | ホバー, サブアクセント |
| `primary-dark` | `#E55A2B` | エラーアクセント, pressed状態 |
| `navy` | `#1E3A5F` | テキスト, アイコンアウトライン, セカンダリCTA |
| `navy-light` | `#2C4A6F` | タグ, サブ要素 |
| `charcoal` | `#36454F` | ボディテキスト |
| `icon-green` | `#6B8B3E` | ネコの目 (Kare Cat on Grayより) |

### iPad (Light Theme)

| Token | Hex | Usage |
|-------|-----|-------|
| `bg` | `#FAFBFC` | ページ背景 |
| `card-bg` | `#FFFFFF` | カード背景 |
| `border` | `#E8EAED` | カード・入力ボーダー |
| `text-primary` | `#1E3A5F` | 見出し, 重要テキスト |
| `text-body` | `#4A5A66` | 本文 |
| `text-muted` | `#8A949E` | プレースホルダ, 補足 |
| `shadow` | `rgba(30,58,95,0.06)` | カードシャドウ |

### Projection (Dark Theme)

| Token | Hex | Usage |
|-------|-----|-------|
| `bg` | `#141E2B` | ページ背景 |
| `card-bg` | `#1E2D3D` | カード背景 |
| `border` | `#2A3D50` | カードボーダー |
| `text-primary` | `#F0F2F5` | 見出し |
| `text-body` | `#8A9AAD` | 本文 |
| `text-muted` | `#6B7B8D` | 補足 |

## Icon System (Kare Style)

### Specification

- **Grid**: 16×16 SVG
- **Rendering**: `image-rendering: pixelated`
- **Outline**: 1px, ネイビー (#1E3A5F) / ダークモードは白 (#F0F2F5)
- **Fill**: 白 / ダークモードは背景色
- **Accent**: オレンジ (#FF6B35) を差し色に
- **Reference**: Susan Kare「Cat on Gray」— 太い輪郭線、白い塗りつぶし、オリーブグリーンの目、ヒゲ

### Cat Face Variants (AI State)

| Variant | Eyes | Mouth | Special | Usage |
|---------|------|-------|---------|-------|
| Default | Green (#6B8B3E) squares | Neutral corners | Whiskers | 通常状態 |
| Thinking | Orange (#FF6B35) spirals | Wavy | Whiskers | 解析中・ローディング |
| Happy | ^_^ (closed arcs) | Wide smile | Orange blush cheeks | 推薦成功・マッチ |
| Error | × marks (#E55A2B) | Wavy/sad | Left ear drooped, droopy whiskers | エラー・やり直し |

### Functional Icons

| Icon | Description | Usage |
|------|-------------|-------|
| Camera | Classic pixel camera, orange lens + flash | 撮影ボタン |
| Fish | Orange fish with tail | おすすめ・レコメンド |
| Paw | Cat paw with orange toe beans | いいね・確認 |
| Hanger | Wire hanger silhouette | 服・アイテム |

### Dark Mode Adaptation

全アイコンはライト/ダーク反転版を持つ:
- ライト: ネイビーアウトライン + 白塗り
- ダーク: 白アウトライン + 暗い塗り (#141E2B)
- アクセントカラー (オレンジ, グリーン) は両モード共通

## Component Patterns

### iPad UI

**Cards:**
- 白背景 + 1.5px solid #E8EAED ボーダー + border-radius: 16px
- box-shadow: 0 1px 3px rgba(30,58,95,0.06)

**AI Message (Chat Bubble):**
- 左にネコアバター (36×36, 角丸8px, #F0F4F8背景)
- 右にチャットバブル (白背景, ボーダー, 角丸14px)
- AI状態に応じてネコの表情が変化

**Primary CTA:**
- background: #FF6B35, color: white
- border-radius: 12px, font-weight: 700
- box-shadow: 0 2px 8px rgba(255,107,53,0.3)

**Secondary CTA:**
- background: white, color: #1E3A5F
- border: 1.5px solid #D0D5DA
- border-radius: 12px, font-weight: 600

**Style Tags:**
- Pill shape (border-radius: 20px)
- Selected: オレンジ or ネイビー背景 + 白テキスト
- Add: 透明 + dashed border (#CCD0D5)

**AI Hint Box:**
- background: #FFF5F0
- border-left: 3px solid #FF6B35
- border-radius: 12px
- text color: #E55A2B

### Projection UI

**Layout:**
- 大きめフォントサイズ (見出し24-28px, 本文14-16px)
- 十分な余白 — 遠くから読める

**Cards:**
- background: #1E2D3D
- border: 1px solid #2A3D50
- border-radius: 14px

**Recommendation Cards:**
- 魚アイコン + "RECOMMENDATION 01" ラベル (#FF6B35)
- 商品サムネイルは60×60, 角丸10px

**AI Avatar:**
- 48×48サイズ (iPadより大きめ)
- #1E2D3D背景, 角丸10px
- 解析中 = Thinking cat, 結果 = Happy cat

### Header

**iPad:**
- 85ロゴ: 32×32, ネイビー背景, オレンジ "85" テキスト, 角丸8px
- "STORE" テキスト: 12px, #36454F, letter-spacing: 1.5px

**Projection:**
- 85ロゴ: 40×40, オレンジ背景, ダーク "85" テキスト, 角丸10px
- "STORE" テキスト: 14px, #FF8A5B, letter-spacing: 2px

## Scope

### In Scope

- **operator/ コンポーネント**: IdleView, PreferenceView, CameraView, AnalyzingView, ResultView
- **projection/ コンポーネント**: ProjectionScenes, ProjectionResultScene, ProjectionBackground
- **共通**: カラーCSS変数, アイコンコンポーネント, ヘッダー

### Out of Scope (Future)

- キャラクター設計 (将来計画あり — デザインはキャラ追加に対応可能な構造にする)
- アニメーション詳細設計 (Framer Motionの使い方は実装計画で詰める)
- サウンドデザイン

## Design Assets

Visual mockups created during brainstorming:
- `.superpowers/brainstorm/57118-1773116266/design-direction-v3.html` — iPad + Projection カラーシステム
- `.superpowers/brainstorm/57118-1773116266/pixel-icons-cat-v3.html` — Kareスタイルネコアイコン + UIモックアップ

## Typography

### Font Family

- **Geist Sans** を継続使用 (`--font-geist-sans`) — Vercel製のクリーンなサンセリフ。ピクセルアートアイコンとの対比で現代的な読みやすさを確保
- **Geist Mono** はCameraViewのステータス表示等で継続使用

### iPad Scale

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Page title (Idle) | 28px | 800 | #1E3A5F |
| Section heading | 18px | 700 | #1E3A5F |
| Card heading | 16px | 700 | #1E3A5F |
| Body text | 14px | 400 | #4A5A66 |
| Button text | 14px | 700 | white / #1E3A5F |
| Caption / muted | 12px | 400-600 | #8A949E |
| Tag text | 12px | 600 | white |

### Projection Scale

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Main heading | 28px | 700 | #F0F2F5 |
| Sub heading | 18px | 700 | #F0F2F5 |
| Body text | 14-16px | 400 | #8A9AAD |
| Label | 11px | 700 | #FF6B35 (letter-spacing: 1.5px) |
| Muted | 13px | 400 | #6B7B8D |

## CSS Integration (Tailwind v4)

### globals.css

```css
@import "tailwindcss";

:root {
  /* Brand */
  --color-primary: #FF6B35;
  --color-primary-light: #FF8A5B;
  --color-primary-dark: #E55A2B;
  --color-navy: #1E3A5F;
  --color-navy-light: #2C4A6F;
  --color-charcoal: #36454F;
  --color-icon-green: #6B8B3E;

  /* iPad (Light) - default */
  --color-bg: #FAFBFC;
  --color-card: #FFFFFF;
  --color-border: #E8EAED;
  --color-text: #1E3A5F;
  --color-text-body: #4A5A66;
  --color-text-muted: #8A949E;
  --color-shadow: rgba(30,58,95,0.06);
}

@theme inline {
  --color-primary: var(--color-primary);
  --color-primary-light: var(--color-primary-light);
  --color-primary-dark: var(--color-primary-dark);
  --color-navy: var(--color-navy);
  --color-navy-light: var(--color-navy-light);
  --color-charcoal: var(--color-charcoal);
  --color-icon-green: var(--color-icon-green);
  --color-bg: var(--color-bg);
  --color-card: var(--color-card);
  --color-border: var(--color-border);
  --color-text: var(--color-text);
  --color-text-body: var(--color-text-body);
  --color-text-muted: var(--color-text-muted);
  --font-sans: var(--font-geist-sans);
  --font-mono: var(--font-geist-mono);
}
```

### Usage

iPad コンポーネントは CSS変数経由の Tailwind クラスを使用:
- `bg-bg`, `bg-card`, `bg-primary`, `text-text`, `text-text-body`, `border-border` 等

Projection コンポーネントはハードコードされた暗い色を直接使用 (CSS dark mode切替は使わない):
- `bg-[#141E2B]`, `text-[#F0F2F5]`, `bg-[#1E2D3D]`, `border-[#2A3D50]` 等
- ブランドカラー (`bg-primary`, `text-primary`) は共通で使える

### Input Fields

- background: white (iPad)
- border: 1.5px solid #E8EAED
- border-radius: 10px
- focus ring: `focus:ring-2 focus:ring-primary/50 focus:outline-none`
- placeholder: #8A949E

## Page-Level Changes

### iPad (`page.tsx`)

```
Before: <main className="min-h-screen bg-slate-950 font-sans selection:bg-emerald-500/30 text-slate-200">
After:  <main className="min-h-screen bg-bg font-sans selection:bg-primary/30 text-text">
```

### Projection (`projection/page.tsx`)

```
Before: <main className="w-screen h-screen overflow-hidden bg-black text-slate-100 font-sans cursor-none relative">
After:  <main className="w-screen h-screen overflow-hidden bg-[#141E2B] text-[#F0F2F5] font-sans cursor-none relative">
```

## Branding

### Title Text

| Location | Before | After |
|----------|--------|-------|
| IdleView | "VINTAGE.AI" | "85 STORE" (85ロゴ + STOREテキスト) |
| ProjectionIdleScene | "VINTAGE.AI" | "85 STORE" (大サイズ版) |
| CameraView header | なし | 85ロゴ小 (任意) |

### Idle Screen

iPad: 中央に85ロゴ (大) + "STORE" + ネコアイコン (Default) + 「タップして始めましょう」テキスト
Projection: 中央に85ロゴ (特大) + "STORE" + ゆったりしたフェードイン/アウト

## Animation Guidelines

### Remove

- 回転リング (AnalyzingView) — `animate-spin` の輪アニメーション
- スキャンラインバー (AnalyzingView) — 上下に動くグラデーションバー
- パーティクルシステム (ProjectionIdleScene) — 浮遊する光の粒子
- ネオングロー効果 — `shadow-[0_0_Xpx_rgba(emerald)]` 系

### Keep / Adapt

- **AnimatePresence** ページ遷移 — opacity + 軽いy移動。そのまま維持
- **ResultView** カード展開/折りたたみ — そのまま維持
- **Framer Motion** の基本的なfade/slide — 継続使用

### New / Replace

- **AnalyzingView ローディング**: Thinking catアイコン (大サイズ) + テキスト「スタイルを解析中...」+ ドット省略アニメ (`...` が点滅)。シンプルなフェードインでOK
- **ProjectionIdleScene**: 85ロゴ + ネコアイコンのゆったりしたpulse (opacity 0.8→1.0, 3秒周期)。パーティクルなし
- **ProjectionAnalyzing**: Thinking cat (大) + プログレス風のテキスト更新

## Error & Edge Case States

### Error UI

エラー時は **Error cat** (×目 + 片耳たれ) を表示:

**iPad AnalyzingView エラー:**
- Error catアイコン (64×64)
- 背景: #FFF5F0 (AI Hint Box風)
- テキスト: 「うまくいかなかったみたい...」(#E55A2B)
- リトライ: Primary CTA「もう一度試す」
- リセット: Secondary CTA「最初から」

**Projection エラー:**
- Error catアイコン (反転版, 96×96)
- テキスト: #F0F2F5、「もう一度試してみるね」
- 背景: #1E2D3D カード

### Warning / Timeout

- iPadの `warningMessage` 表示: AI Hint Boxパターン (左ボーダーオレンジ + #FFF5F0背景)
- タイムアウト: Error catではなく Thinking cat + 「もうちょっと待ってね...」

### ResultView フォールバック

- 「解析データが見つかりません」→ Error catアイコン + テキスト + リセットボタン

## Projection-Specific Components

### ProjectionBackground

現在: 状態に応じた動的グラデーション + SVGノイズオーバーレイ

変更: ベース背景を `#141E2B` に統一。状態ごとのグラデーションは新パレットで再テーマ:
- Idle: `#141E2B` → `#1E2D3D` (微かなグラデーション)
- Analyzing: `#141E2B` ベース + navy-light方向のグラデーション
- Result: `#141E2B` ベース

SVGノイズオーバーレイは継続使用 (テクスチャとして有効)。

### MirrorOverlay

現在: `mix-blend-screen` + `opacity-80`

変更: `mix-blend-screen` は暗い背景で正しく機能するため継続。#141E2B背景でのコントラストは十分。変更不要。

### QR Code

QRコードのスタイリングは変更なし。モーダル背景のみ更新:
- Before: `bg-black/70 backdrop-blur-sm`
- After: `bg-navy/70 backdrop-blur-sm` (ネイビー系に統一)

## Modal Styling

プライバシーポリシーモーダル等のオーバーレイ:
- オーバーレイ: `bg-[#1E3A5F]/60 backdrop-blur-sm`
- モーダル本体: `bg-white border border-[#E8EAED] rounded-2xl shadow-xl`
- ヘッダー: `text-[#1E3A5F] font-bold`
- 本文: `text-[#4A5A66]`
- 閉じるボタン: Secondary CTAパターン

## Technical Notes

- アイコンは全てインラインSVG (16×16 viewBox) — 外部ファイル不要
- SVGは `shape-rendering="crispEdges"` を使用してピクセルアートの鮮明さを保つ (大きいサイズにスケールしても)
- ダークモードはプロジェクション専用 (iPadは常にライト)。`prefers-color-scheme` は使用しない
- ネコアバターは `CatIcon` コンポーネントとして抽出: `variant: "default" | "thinking" | "happy" | "error"`, `size?: number` (デフォルト36), `theme?: "light" | "dark"` (デフォルト"light")
