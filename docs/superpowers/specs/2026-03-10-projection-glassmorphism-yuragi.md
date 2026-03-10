# Projection Glassmorphism + Yuragi Design Spec

> **Design Philosophy**: VISUAL_DESIGN.md — "制御から関係へ。AIは猫のような存在。完全には制御できないけれど、長く付き合うと、なんとなくわかってくる。"

## Goal

プロジェクション表示にvisionOS風グラスモーフィズムと「ゆらぎ」エフェクトを導入し、AIの思考プロセスと不確かさを視覚的に表現する。

## Design Principles

1. **グラスモーフィズム**: visionOSの「背景が透けて見える」window概念。超低opacityの白ベース（3-6%）+ backdrop-blur で、背景グラデーションが透ける
2. **状態連動ゆらぎ**: ANALYZING（最大揺れ）→ RESULT（収束）で、AIの思考プロセスを可視化
3. **有機的境界**: SVG feTurbulence + feDisplacementMap でカードエッジが「溶ける」。固定された矩形ではなく、呼吸する存在

## Color & Material

既存のdark navy palette（#141E2B, #1E2D3D, #2A3D50, #FF6B35）はそのまま維持。
グラスモーフィズム層を上に重ねる:

```css
/* GlassPanel base */
background: rgba(255, 255, 255, 0.03);
backdrop-filter: blur(24px) saturate(1.2);
border: 1px solid rgba(255, 255, 255, 0.06);
box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.04);
border-radius: 24px;
```

## Yuragi System

### Two Sources of Yuragi

ゆらぎは2つのソースから合成される:

1. **状態連動ゆらぎ** (hardcoded) — IDLE〜ANALYZINGの各状態に応じた基本パラメータ
2. **AI生成ゆらぎ** (Gemini output) — RESULT状態でAI自身が返す確信度とムード

ANALYZING → RESULT の遷移で、状態連動パラメータからAI生成パラメータへスムーズに移行する。

### Parameters

```typescript
interface YuragiParams {
  amplitude: number;    // rotation/translation magnitude (deg or px)
  speed: number;        // breathing cycle duration (seconds)
  turbulence: number;   // SVG feDisplacementMap scale (0 = off, 1 = max)
  easing: string;       // "easeInOut" | "easeOut" | "linear"
  jitter: boolean;      // true = add random micro-offsets each cycle
}
```

### State-Driven Config (IDLE → ANALYZING)

```typescript
const YURAGI_STATE: Record<AppState, YuragiParams> = {
  IDLE:          { amplitude: 0.3, speed: 8,   turbulence: 0,   easing: "easeInOut", jitter: false },
  PREFERENCE:    { amplitude: 0.5, speed: 6,   turbulence: 0,   easing: "easeInOut", jitter: false },
  CAMERA_ACTIVE: { amplitude: 0.8, speed: 4,   turbulence: 0.2, easing: "easeInOut", jitter: false },
  ANALYZING:     { amplitude: 2.0, speed: 1.5, turbulence: 1.0, easing: "easeOut",   jitter: true },
  RESULT:        { amplitude: 0.3, speed: 10,  turbulence: 0,   easing: "easeInOut", jitter: false },  // fallback only
};
```

### AI-Driven Yuragi (RESULT state)

Gemini の構造化出力に `yuragi` フィールドを追加。AIが自身の確信度とスタイルの印象を返す:

**Backend Schema** (`backend/gemini_service.py`):
```python
class YuragiOutput(BaseModel):
    confidence: float   # 0.0-1.0 — 提案全体への確信度
    mood: str           # "sharp" | "smooth" | "pulse" | "calm"
    reasoning: str      # なぜこの揺れ方か（デバッグ/ログ用）

class ClothingAnalysis(BaseModel):
    analyzed_outfit: str
    detected_style: list[str]
    recommendations: list[RecommendationItem]
    yuragi: YuragiOutput          # ← NEW
    box_ymin: int
    box_xmin: int
    box_ymax: int
    box_xmax: int
```

**Gemini Prompt Addition** (`backend/gemini_service.py`):
```
【ゆらぎ】
あなたの提案への確信度とムードを返してください。
- confidence: 0.0（まったく自信がない）〜 1.0（完璧にマッチ）
  - 在庫にぴったりの商品があった → 高い
  - サイズが合わない、スタイルの一致度が低い → 低い
  - 入力情報が少ない（タグなし、体型なし） → 低い
- mood: ユーザーのスタイルから感じた雰囲気
  - "sharp": エッジの効いた、鋭い印象（ストリート、モード）
  - "smooth": 流れるような、柔らかい印象（ナチュラル、きれいめ）
  - "pulse": リズミカルで不規則な印象（個性的、ミックス）
  - "calm": 落ち着いた、安定した印象（クラシック、ヴィンテージ）
- reasoning: この判断の根拠（1文）
```

**Frontend Conversion** (`frontend/src/hooks/useYuragi.ts`):
```typescript
interface GeminiYuragi {
  confidence: number;
  mood: "sharp" | "smooth" | "pulse" | "calm";
  reasoning: string;
}

const MOOD_PROFILES = {
  sharp:  { speedMult: 0.5, easing: "easeOut",   jitter: true },
  smooth: { speedMult: 1.5, easing: "easeInOut", jitter: false },
  pulse:  { speedMult: 0.8, easing: "linear",    jitter: true },
  calm:   { speedMult: 2.0, easing: "easeInOut", jitter: false },
};

function geminiYuragiToParams(yuragi: GeminiYuragi): YuragiParams {
  const profile = MOOD_PROFILES[yuragi.mood];
  return {
    amplitude: (1 - yuragi.confidence) * 2.5,           // 低確信 = 大きい揺れ
    speed: 10 * profile.speedMult,                       // moodで速度調整
    turbulence: Math.max(0, (1 - yuragi.confidence) * 0.8), // 低確信 = エッジ溶ける
    easing: profile.easing,
    jitter: profile.jitter,
  };
}
```

**Experience Flow**:
```
ANALYZING: 状態連動ゆらぎ（amplitude 2.0, turbulence 1.0）
    ↓ Geminiレスポンス到着
RESULT遷移: AI生成ゆらぎへ 1.5s でスムーズ移行
    ↓
confidence 0.3 + mood "pulse" → まだかなり揺れている（自信ない提案）
confidence 0.9 + mood "calm"  → すぐに収束（確信ある提案）
```

**Data Flow**:
```
Gemini API → ClothingAnalysis.yuragi → WebSocket → ProjectionPayload.yuragi
  → useYuragi hook → geminiYuragiToParams() → GlassPanel animation params
```

### Yuragi Animations (Framer Motion)

**Breathing** (all states):
```typescript
// GlassPanel breathing
animate={{
  scale: [1, 1 + amplitude * 0.01, 1],
  rotate: [-amplitude * 0.5, amplitude * 0.5, -amplitude * 0.5],
}}
transition={{ duration: speed, repeat: Infinity, ease: "easeInOut" }}
```

**Edge Dissolution** (CAMERA_ACTIVE, ANALYZING):
```svg
<filter id="yuragi-edge">
  <feTurbulence type="turbulence" baseFrequency="0.015" numOctaves="3" seed="1">
    <animate attributeName="baseFrequency" values="0.015;0.025;0.015" dur="4s" repeatCount="indefinite" />
  </feTurbulence>
  <feDisplacementMap in="SourceGraphic" scale={turbulence * 12} />
</filter>
```

Applied to GlassPanel via CSS `filter: url(#yuragi-edge)`.

### State Transitions

Yuragi parameters transition smoothly between states using Framer Motion's `animate` with `transition: { duration: 1.5, ease: "easeInOut" }`. No abrupt jumps.

- IDLE → ANALYZING: amplitude ramps up over 1.5s, turbulence fades in
- ANALYZING → RESULT: amplitude drops, turbulence fades to 0 — "the answer has settled"

## Per-State Visual Design

### IDLE
- Center: GlassPanel containing 85 logo + CatIcon + subtitle
- Breathing: `scale [1, 1.003, 1]` over 8s
- No turbulence
- Background gradient slowly shifts through navy palette

### PREFERENCE
- Center: GlassPanel with greeting + tags
- Tags appear inside the glass surface
- Breathing slightly faster (6s)
- Each tag addition triggers a micro-bounce on the panel

### CAMERA_ACTIVE
- Grid lines overlay (existing, unchanged)
- Scan line (existing, unchanged)
- Bottom tag bar: wrapped in GlassPanel
- Edge turbulence begins (scale ~2.4) — subtle boundary wavering
- STANDBY text gets a subtle blur halo

### ANALYZING — Maximum Yuragi + Live Thinking

ANALYZING状態はさらに2つのフェーズに分かれる:

**Phase 1: 思考ストリーミング** (Gemini thinking chunks arriving)
- Captured image: inside a GlassPanel with strong turbulence (scale ~12)
- Panel visibly wobbles: `rotate [-1.5deg, 1.5deg]`, `scale [0.98, 1.02]`
- CatIcon thinking: participates in the wobble
- Scan line on image: kept (orange, existing)
- **思考テキスト**: Geminiの思考チャンクがリアルタイムでグラスパネルに表示される（後述「推論中フィードバック」参照）
- Background gradient: fast cycle (5s, existing)
- Overall feel: "the AI is actively processing, nothing is certain yet"

**Phase 2: JSON出力開始** (structured output chunks arriving)
- 思考テキストがフェードアウト
- ゆらぎが徐々に収束を始める（RESULT遷移への準備）
- 「まもなく結果が出ます」の予感

### RESULT — AI-Driven Convergence
- ANALYZING → RESULT: 状態連動パラメータからAI生成パラメータへ1.5sで遷移
- **confidence高い** (0.8+): 素早く安定。turbulence → 0、amplitude → 0.2。「答えが定まった」
- **confidence低い** (0.3-): 揺れが残る。turbulence → 0.3+、amplitude → 1.5+。「正直自信ない」
- **mood**: 揺れの質感が変わる — sharp=鋭いジッター、smooth=滑らかなうねり、pulse=不規則、calm=静穏
- Top summary: GlassPanel
- 3 recommendation cards: each a GlassPanel
- Cards slide in from bottom (existing) with glass effect
- CatIcon happy: 微かな呼吸のみ

## 推論中フィードバック (Live Thinking Stream)

### 技術検証結果

google-genai SDK で以下の3機能の組み合わせが動作確認済み:

1. **Streaming** (`generate_content_stream`) — レスポンスがチャンクで届く
2. **Thinking Mode** (`ThinkingConfig(include_thoughts=True)`) — AIの思考過程が `part.thought` で取得可能
3. **構造化出力** (`response_schema`) — Pydanticスキーマ準拠のJSON出力

3つの組み合わせも `gemini-3.1-pro-preview` で動作確認済み。

### チャンク構成（実測）

```
chunk[1] 💭 thought: "Extracting User Intent..."        ← 思考が複数チャンクで届く
chunk[2] 💭 thought: "Refining Output Parameters..."
chunk[3] 💭 thought: "Determining JSON Values..."
chunk[4] 📝 output: "{"                                 ← JSON出力開始
chunk[5] 📝 output: "summary": "..."                    ← JSON完了
```

思考チャンクは英語で届く（Geminiの内部思考言語）。プロジェクション表示では翻訳不要 — 「AIが考えている」雰囲気が伝わればよい。

### Backend 実装

**`backend/gemini_service.py`** — `analyze_image_streaming()` 新規追加:

```python
async def analyze_image_streaming(image_bytes, user_preferences, body_measurements, catalog_text):
    """
    Streaming + Thinking で解析。思考チャンクと最終結果を yield する。
    """
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ClothingAnalysis,
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=1024,
        ),
    )

    thought_buffer = []
    output_buffer = []

    async for chunk in await client.aio.models.generate_content_stream(
        model="gemini-3.1-pro-preview",
        contents=[prompt, image],
        config=config,
    ):
        for part in chunk.candidates[0].content.parts:
            if part.thought:
                thought_buffer.append(part.text)
                yield {"type": "thought", "text": part.text}
            else:
                output_buffer.append(part.text)

    full_output = "".join(output_buffer)
    yield {"type": "result", "data": full_output}
```

**`backend/routers/analyze.py`** — 既存の `/api/analyze` はそのまま維持（iPad用）。新規に内部で streaming 版を使い、WebSocket 経由で思考チャンクをプロジェクションに中継:

```python
# analyze endpoint 内部
async for event in analyze_image_streaming(...):
    if event["type"] == "thought":
        # ProjectionManager 経由でプロジェクションに思考テキストを送信
        await projection_manager.broadcast_thinking(event["text"])
    elif event["type"] == "result":
        # 通常の結果処理（既存フロー）
        result = json.loads(event["data"])
```

### WebSocket プロトコル拡張

プロジェクション用 WebSocket に新しいメッセージタイプを追加:

```typescript
// 思考チャンク（ANALYZING中に複数回届く）
{
  "type": "thinking",
  "text": "Analyzing the jacket style...",
  "chunk_index": 2
}

// 既存の状態更新メッセージはそのまま
{
  "type": "state",
  "appState": "RESULT",
  ...
}
```

### Frontend 表示

**`ProjectionScenes.tsx` — ProjectionAnalyzingScene**:

思考テキストをグラスパネル内に表示。チャンクが届くたびにフェードで切り替わる:

```typescript
// 思考テキスト表示（AnalyzingScene内）
const [thinkingText, setThinkingText] = useState<string>("");
const [thinkingIndex, setThinkingIndex] = useState(0);

// WebSocketから思考チャンクを受信
useEffect(() => {
  // onThinkingChunk callback
  setThinkingText(chunk.text);
  setThinkingIndex(prev => prev + 1);
}, [/* thinking events */]);
```

```tsx
{/* 思考テキスト — グラスパネル内、フェードアニメーション */}
<AnimatePresence mode="wait">
  <motion.div
    key={thinkingIndex}
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 0.6, y: 0 }}
    exit={{ opacity: 0, y: -8 }}
    transition={{ duration: 0.5 }}
    className="text-[#8A9AAD] text-lg font-light italic max-w-md text-center"
  >
    {thinkingText}
  </motion.div>
</AnimatePresence>
```

### ゆらぎとの連動

思考チャンクの到着がゆらぎパラメータに影響する:

```typescript
// チャンクが届くたびにゆらぎに微振動を加える
const onThinkingChunk = (chunk: ThinkingChunk) => {
  // 一時的にamplitudeを跳ね上げる（0.5秒で戻る）
  setAmplitudeBoost(0.5);
  setTimeout(() => setAmplitudeBoost(0), 500);

  // チャンクの長さに応じてturbulenceを微調整
  const textLength = chunk.text.length;
  setTurbulenceBoost(Math.min(0.3, textLength / 500));
};
```

**体験の流れ:**
```
ANALYZING開始
  ↓ ゆらぎ最大（状態連動: amplitude 2.0, turbulence 1.0）
  ↓
chunk[1] 💭 "Analyzing the outfit..."
  → テキストがふわっと現れる
  → ゆらぎに微振動（amplitude一瞬+0.5）
  ↓
chunk[2] 💭 "Matching with inventory..."
  → テキストがフェードで切り替わる
  → ゆらぎに微振動
  ↓
chunk[3] 💭 "Found 3 strong matches..."
  → テキストがフェードで切り替わる
  → ゆらぎに微振動
  ↓
chunk[4] 📝 JSON出力開始
  → 思考テキストがフェードアウト
  → ゆらぎが収束を開始
  ↓
chunk[5] 📝 JSON完了
  → RESULT状態へ遷移
  → AI生成ゆらぎ（confidence + mood）で最終パラメータ決定
```

### Fallback

Streaming/Thinking が何らかの理由で失敗した場合:
- 既存の非ストリーミング `generate_content()` にフォールバック
- 思考テキストなし、ゆらぎは状態連動のみ（現行動作と同じ）
- `yuragi` フィールドが返らない場合は RESULT のデフォルトパラメータを使用

## Technical Architecture

### New Files

**`frontend/src/hooks/useYuragi.ts`**
```typescript
// Input: appState, geminiYuragi? (from recommendation response)
// Output: YuragiParams with smooth transitions
// IDLE-ANALYZING: uses YURAGI_STATE config
// RESULT: converts GeminiYuragi → YuragiParams via geminiYuragiToParams()
// Uses Framer Motion useSpring for interpolation between states
```

**`frontend/src/components/projection/GlassPanel.tsx`**
```typescript
// Props: children, className, yuragi?: YuragiParams, enableTurbulence?: boolean
// Renders: motion.div with glass styles + breathing animation
// Conditionally applies SVG displacement filter when turbulence > 0
// SVG filter is defined inline (unique ID per instance)
```

### Modified Files

**`ProjectionScenes.tsx`**
- Import GlassPanel and useYuragi
- Wrap content sections in GlassPanel
- Pass yuragi params from useYuragi hook
- IdleScene: single centered GlassPanel
- PreferenceScene: GlassPanel for main content
- CameraScene: GlassPanel for bottom tag bar only
- AnalyzingScene: GlassPanel for image container + text, with turbulence

**`ProjectionResultScene.tsx`**
- Top summary section: GlassPanel (replaces current bg-[#1E2D3D]/60)
- Each recommendation card: GlassPanel (replaces current bg-[#1E2D3D])
- Product items inside cards: keep current styling (solid bg for image contrast)

**`ProjectionBackground.tsx`**
- No changes required — existing gradient animation serves as the "environment" that shows through glass panels

### Modified Backend Files

**`backend/gemini_service.py`**
- Add `YuragiOutput` Pydantic model (confidence, mood, reasoning)
- Add `yuragi` field to `ClothingAnalysis` schema
- Add yuragi instructions to Gemini prompt

**`backend/mock_service.py`**
- Add mock `yuragi` data to mock response

**`frontend/src/lib/projection-types.ts`**
- Add `YuragiOutput` TypeScript interface
- Add `yuragi?` to `ClothingAnalysis` type
- Add `yuragi?` to `ProjectionPayload` type

**`frontend/src/app/projection/page.tsx`**
- Pass `yuragi` from payload to ProjectionResultScene

## Performance Considerations

- SVG feTurbulence with animation: GPU-accelerated in modern browsers
- feDisplacementMap: only applied when turbulence > 0 (CAMERA_ACTIVE, ANALYZING)
- backdrop-filter blur: hardware-accelerated, but limit to ~5 concurrent panels max
- All animations use `will-change: transform` for compositor-layer promotion
- Projector runs at 1080p — well within performance budget

## Out of Scope

- Canvas/WebGL fluid simulation (too heavy for projector)
- Mirror camera as glass background (separate feature)
- Per-recommendation confidence (current design uses a single confidence for the entire analysis)
- iPad operator UI yuragi (this spec is projection-only; iPad remains static light theme)
