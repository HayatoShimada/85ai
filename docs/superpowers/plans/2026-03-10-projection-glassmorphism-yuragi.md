# Projection Glassmorphism + Yuragi Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add visionOS-style glassmorphism panels, organic yuragi (fluctuation) animations, and live AI thinking stream to the projection display.

**Architecture:** Three layers — (1) Backend adds `YuragiOutput` to Gemini schema + streaming analyze with thinking broadcast, (2) Frontend creates `GlassPanel` component and `useYuragi` hook, (3) Frontend integrates glass panels into all projection scenes and wires up thinking stream display. Prompt construction is extracted into a shared helper to avoid duplication between streaming and non-streaming paths.

**Tech Stack:** FastAPI, google-genai (streaming + thinking), Framer Motion, SVG feTurbulence/feDisplacementMap, Tailwind CSS backdrop-blur + backdrop-saturate

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `frontend/src/components/projection/GlassPanel.tsx` | Reusable glass panel with breathing animation + SVG edge dissolution |
| Create | `frontend/src/hooks/useYuragi.ts` | Yuragi parameter state machine: state-driven (IDLE→ANALYZING) + AI-driven (RESULT) |
| Modify | `backend/gemini_service.py` | Add `YuragiOutput`, `yuragi` optional field on `ClothingAnalysis`, extract `_build_prompt()`, add `analyze_image_streaming()` |
| Modify | `backend/services/projection_manager.py` | Add `broadcast_thinking()` method |
| Modify | `backend/routers/analyze.py` | Use streaming analyze with fallback, relay thinking chunks |
| Modify | `backend/mock_service.py` | Add `yuragi` to mock data |
| Modify | `frontend/src/lib/projection-types.ts` | Add `YuragiOutput`, update `ClothingAnalysis` and `ProjectionPayload` |
| Modify | `frontend/src/app/projection/page.tsx` | Handle THINKING messages, pass yuragi + thinking to scenes |
| Modify | `frontend/src/components/projection/ProjectionScenes.tsx` | Wrap scenes in GlassPanel, add thinking text display |
| Modify | `frontend/src/components/projection/ProjectionResultScene.tsx` | Wrap sections in GlassPanel |
| Modify | `backend/tests/test_gemini.py` | Test YuragiOutput + optional yuragi on ClothingAnalysis |
| Modify | `backend/tests/test_mock_service.py` | Test mock yuragi data |
| Modify | `backend/tests/test_websocket_projection.py` | Test thinking broadcast |

---

## Task 1: Add YuragiOutput to Backend Schema + Extract Shared Prompt Builder

**Files:**
- Modify: `backend/gemini_service.py`
- Test: `backend/tests/test_gemini.py`

- [ ] **Step 1: Write failing tests**

Add to `backend/tests/test_gemini.py`:

```python
def test_yuragi_output_schema():
    """YuragiOutput が正しくパースできること"""
    from gemini_service import YuragiOutput
    yuragi = YuragiOutput(
        confidence=0.85,
        mood="smooth",
        reasoning="ナチュラルな雰囲気のため",
    )
    assert yuragi.confidence == 0.85
    assert yuragi.mood == "smooth"
    assert yuragi.reasoning == "ナチュラルな雰囲気のため"


def test_clothing_analysis_with_yuragi():
    """ClothingAnalysis に yuragi フィールドが含まれること"""
    data = {
        "analyzed_outfit": "テスト",
        "detected_style": ["カジュアル"],
        "box_ymin": 100, "box_xmin": 200, "box_ymax": 800, "box_xmax": 700,
        "recommendations": [{
            "title": "テスト提案", "reason": "テスト理由",
            "product_ids": [1], "category": "トップス",
        }],
        "yuragi": {
            "confidence": 0.7,
            "mood": "pulse",
            "reasoning": "ミックススタイルのため",
        },
    }
    analysis = ClothingAnalysis(**data)
    assert analysis.yuragi is not None
    assert analysis.yuragi.confidence == 0.7
    assert analysis.yuragi.mood == "pulse"


def test_clothing_analysis_without_yuragi():
    """yuragi なしでも ClothingAnalysis が生成できること（後方互換）"""
    data = {
        "analyzed_outfit": "テスト",
        "detected_style": [],
        "box_ymin": 0, "box_xmin": 0, "box_ymax": 1000, "box_xmax": 1000,
        "recommendations": [],
    }
    analysis = ClothingAnalysis(**data)
    assert analysis.yuragi is None


def test_clothing_analysis_yuragi_json_roundtrip():
    """yuragi を含む ClothingAnalysis の JSON ラウンドトリップ"""
    data = {
        "analyzed_outfit": "テスト",
        "detected_style": [],
        "box_ymin": 0, "box_xmin": 0, "box_ymax": 1000, "box_xmax": 1000,
        "recommendations": [],
        "yuragi": {"confidence": 0.5, "mood": "sharp", "reasoning": "テスト"},
    }
    analysis = ClothingAnalysis(**data)
    json_str = analysis.model_dump_json()
    restored = ClothingAnalysis.model_validate_json(json_str)
    assert restored.yuragi is not None
    assert restored.yuragi.confidence == 0.5
    assert restored.yuragi.mood == "sharp"


def test_build_prompt_contains_yuragi_section():
    """_build_prompt にゆらぎセクションが含まれること"""
    from gemini_service import _build_prompt
    prompt = _build_prompt(user_preferences=["カジュアル"], body_measurements=None, catalog_text="")
    assert "ゆらぎ" in prompt
    assert "confidence" in prompt
    assert "mood" in prompt
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_gemini.py -v`
Expected: FAIL — `YuragiOutput` not defined, `_build_prompt` not defined

- [ ] **Step 3: Add YuragiOutput and make yuragi optional on ClothingAnalysis**

In `backend/gemini_service.py`, after `RecommendationItem` class (line 26), add:

```python
class YuragiOutput(BaseModel):
    confidence: float = Field(description="提案全体への確信度 (0.0-1.0)")
    mood: str = Field(description="スタイルの印象: sharp, smooth, pulse, calm のいずれか")
    reasoning: str = Field(description="この判断の根拠（1文）")
```

In `ClothingAnalysis`, add after `recommendations` field:

```python
    yuragi: YuragiOutput | None = Field(default=None, description="AIの確信度とスタイルの印象（ゆらぎパラメータ生成用）")
```

**Important:** `yuragi` is `Optional` with `default=None` so existing tests and non-streaming path continue to work without it.

- [ ] **Step 4: Extract prompt construction into `_build_prompt()`**

In `backend/gemini_service.py`, extract the prompt building logic from `analyze_image_and_get_tags` into a standalone function. Place it before `analyze_image_and_get_tags`:

```python
def _build_prompt(user_preferences: list[str] | None = None, body_measurements: dict | None = None, catalog_text: str = "") -> str:
    """Gemini用プロンプトを構築する（streaming/non-streaming共通）"""
    preference_section = ""
    if user_preferences:
        pref_text = "、".join(user_preferences)
        preference_section = f"""
        【ユーザーの好み】
        {pref_text}

        上記の好みを踏まえた上で、提案はユーザーの好みの方向性に沿ったものにしてください。
        提案理由にはユーザーの好みをどう反映したかを含めてください。"""

    body_section = ""
    if body_measurements:
        parts = []
        if body_measurements.get("height"):
            parts.append(f"身長: {body_measurements['height']}cm")
        if body_measurements.get("shoulder_width"):
            parts.append(f"肩幅: {body_measurements['shoulder_width']}cm")
        if body_measurements.get("chest"):
            parts.append(f"胸囲: {body_measurements['chest']}cm")
        if body_measurements.get("waist"):
            parts.append(f"ウエスト: {body_measurements['waist']}cm")
        if body_measurements.get("weight"):
            parts.append(f"体重: {body_measurements['weight']}kg")
        if parts:
            body_section = f"""
        【体型情報】
        {', '.join(parts)}

        【サイズマッチングルール】
        カタログのSize列に実寸データがある商品については以下の基準で判断:
        - トップス: 肩幅はユーザー+3〜+8cm、身幅はユーザー胸囲÷2+5〜+15cm
        - ボトムス: ウエストはユーザー+2〜+5cm
        - 複数サイズがある商品は最適サイズを選び、提案理由にサイズを明記
        - サイズが合わない商品はproduct_idsに含めない
        - 提案理由にサイズフィットの具体数値を言及"""

    catalog_section = ""
    if catalog_text:
        catalog_section = f"""
        【店舗の商品カタログ】
        以下は当店の全商品リスト（ID\\tカテゴリ\\t商品名\\t属性\\tサイズ実寸）です。
        提案には必ずこのカタログ内の商品IDをproduct_idsに指定してください。
        カタログにない商品は提案しないでください。

        {catalog_text}
        """

    return f"""
        添付した画像の人物が着ている服を分析し、現在着ているメインの服の特徴と、それに合う「古着」のアイテムを複数パターン（最大3つ）提案してください。
        また、画像の服装から推測されるスタイルタグ（カジュアル、ストリート、きれいめ等）を出力してください。
        分析対象とした一番特徴的な服の画像内での位置をバウンディングボックス（0〜1000の相対座標）で出力してください。
        各提案にはカタログから最も合う商品のIDをproduct_idsに最大3つ含めてください。
        {catalog_section}
        {preference_section}
        {body_section}
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
        出力はJSON形式で行ってください。
        """
```

Then update `analyze_image_and_get_tags` to use it:

```python
def analyze_image_and_get_tags(image_bytes, user_preferences=None, body_measurements=None, catalog_text=""):
    # ... (docstring, client check unchanged) ...
    try:
        image = Image.open(io.BytesIO(image_bytes))
        prompt = _build_prompt(user_preferences, body_measurements, catalog_text)

        response = _client.models.generate_content(
            model="gemini-3.1-pro-preview",
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ClothingAnalysis,
            ),
        )
        return response.text
    # ... (error handling unchanged) ...
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_gemini.py -v`
Expected: ALL PASS (existing tests pass because yuragi is optional; new tests pass)

- [ ] **Step 6: Commit**

```bash
git add backend/gemini_service.py backend/tests/test_gemini.py
git commit -m "feat: add YuragiOutput schema, extract _build_prompt helper"
```

---

## Task 2: Add Streaming Analyze + Thinking Broadcast

**Files:**
- Modify: `backend/gemini_service.py` (add `analyze_image_streaming()`)
- Modify: `backend/services/projection_manager.py` (add `broadcast_thinking()`)
- Modify: `backend/routers/analyze.py` (use streaming, relay thinking)
- Test: `backend/tests/test_websocket_projection.py`, `backend/tests/test_gemini.py`

- [ ] **Step 1: Write tests**

Update the `reset_projection_mgr` fixture in `backend/tests/test_websocket_projection.py` to also reset `_thinking_index`:

```python
# In the existing reset_projection_mgr fixture, add:
    projection_mgr._thinking_index = 0
# to both the setup and teardown sections.
```

Add to `backend/tests/test_websocket_projection.py`:

```python
def test_thinking_message_structure():
    """THINKING メッセージの構造テスト (ProjectionManager unit test)"""
    import asyncio
    from services.projection_manager import ProjectionManager

    mgr = ProjectionManager()
    # broadcast_thinking のメッセージ構造を検証（display接続なしでもエラーにならない）
    asyncio.get_event_loop().run_until_complete(
        mgr.broadcast_thinking("test thought", chunk_index=1)
    )
    assert mgr._thinking_index == 0  # chunk_index指定時は自動インクリメントしない

    mgr.reset_thinking_index()
    assert mgr._thinking_index == 0


def test_thinking_auto_increment():
    """思考インデックスの自動インクリメント"""
    import asyncio
    from services.projection_manager import ProjectionManager

    mgr = ProjectionManager()
    asyncio.get_event_loop().run_until_complete(
        mgr.broadcast_thinking("thought 1")
    )
    assert mgr._thinking_index == 1
    asyncio.get_event_loop().run_until_complete(
        mgr.broadcast_thinking("thought 2")
    )
    assert mgr._thinking_index == 2
    mgr.reset_thinking_index()
    assert mgr._thinking_index == 0
```

Add to `backend/tests/test_gemini.py`:

```python
@pytest.mark.asyncio
async def test_analyze_image_streaming_raises_without_api_key():
    """API key なしで GeminiAnalysisError が発生すること"""
    from gemini_service import analyze_image_streaming, GeminiAnalysisError
    import pytest

    # _client is None in test env (MOCK_MODE)
    with pytest.raises(GeminiAnalysisError, match="GEMINI_API_KEY"):
        async for _ in analyze_image_streaming(b"fake_image"):
            pass
```

Add `import pytest` to the top of `backend/tests/test_gemini.py` if not present.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_websocket_projection.py::test_thinking_message_structure tests/test_gemini.py::test_analyze_image_streaming_raises_without_api_key -v`
Expected: FAIL

- [ ] **Step 3: Add `broadcast_thinking()` to ProjectionManager**

In `backend/services/projection_manager.py`, update `__init__` to initialize `_thinking_index`:

```python
    def __init__(self):
        self.displays: list[WebSocket] = []
        self._current_state: dict | None = None
        self._mirror_task: asyncio.Task | None = None
        self._mirror_active = False
        self._thinking_index = 0
```

Add methods after `_broadcast_text`:

```python
    async def broadcast_thinking(self, text: str, chunk_index: int | None = None):
        """思考チャンクをプロジェクションに配信"""
        if chunk_index is None:
            self._thinking_index += 1
            chunk_index = self._thinking_index
        msg = {
            "type": "THINKING",
            "text": text,
            "chunk_index": chunk_index,
        }
        await self._broadcast_json(msg)

    def reset_thinking_index(self):
        """思考チャンクのインデックスをリセット"""
        self._thinking_index = 0
```

- [ ] **Step 4: Add `analyze_image_streaming()` to gemini_service**

In `backend/gemini_service.py`, add after `analyze_image_and_get_tags`:

```python
async def analyze_image_streaming(image_bytes: bytes, user_preferences: list[str] | None = None, body_measurements: dict | None = None, catalog_text: str = ""):
    """
    Streaming + Thinking で画像解析。思考チャンクと最終結果を yield する。

    Yields:
        {"type": "thought", "text": "..."}
        {"type": "output_started"} — 最初のJSON出力チャンク到着時
        {"type": "result", "data": "..."} — 完全なJSON結果文字列

    Raises:
        GeminiAnalysisError
    """
    if not _client:
        raise GeminiAnalysisError("GEMINI_API_KEY が設定されていません")

    try:
        image = Image.open(io.BytesIO(image_bytes))
        prompt = _build_prompt(user_preferences, body_measurements, catalog_text)

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ClothingAnalysis,
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
                thinking_budget=1024,
            ),
        )

        output_buffer = []
        output_started = False

        async for chunk in await _client.aio.models.generate_content_stream(
            model="gemini-3.1-pro-preview",
            contents=[prompt, image],
            config=config,
        ):
            if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                for part in chunk.candidates[0].content.parts:
                    if part.thought:
                        yield {"type": "thought", "text": part.text or ""}
                    else:
                        if not output_started:
                            output_started = True
                            yield {"type": "output_started"}
                        output_buffer.append(part.text or "")

        full_output = "".join(output_buffer)
        yield {"type": "result", "data": full_output}

    except GeminiAnalysisError:
        raise
    except Exception as e:
        logger.error(f"Gemini streaming API error: {e}")
        raise GeminiAnalysisError(f"AI解析中にエラーが発生しました（{type(e).__name__}）") from e
```

- [ ] **Step 5: Update analyze endpoint with streaming + fallback**

In `backend/routers/analyze.py`, update imports at the top:

```python
from gemini_service import analyze_image_and_get_tags, analyze_image_streaming, GeminiAnalysisError
from services.projection_manager import projection_mgr
```

Replace the real-API section (lines 58-83) with:

```python
    # カタログテキストを取得 (キャッシュ済み)
    catalog_text = catalog_cache.get_gemini_catalog() if catalog_cache.is_loaded else ""

    # Streaming + Thinking → プロジェクションに思考チャンク配信
    try:
        projection_mgr.reset_thinking_index()
        result_dict = None

        try:
            async for event in analyze_image_streaming(
                image_bytes, user_preferences, measurements, catalog_text
            ):
                if event["type"] == "thought":
                    await projection_mgr.broadcast_thinking(event["text"])
                elif event["type"] == "output_started":
                    # プロジェクションに「出力開始」を通知（ゆらぎ収束開始のトリガー）
                    await projection_mgr._broadcast_json({"type": "OUTPUT_STARTED"})
                elif event["type"] == "result":
                    result_dict = json.loads(event["data"])
        except GeminiAnalysisError:
            raise  # API key missing等の根本的エラーはフォールバックせず即座に伝播
        except Exception as streaming_err:
            # Streaming固有の失敗のみ非ストリーミングにフォールバック
            logger.warning(f"Streaming failed, falling back: {streaming_err}")
            json_str_response = analyze_image_and_get_tags(
                image_bytes, user_preferences, measurements, catalog_text
            )
            result_dict = json.loads(json_str_response)

        if result_dict is None:
            return {
                "status": "error",
                "message": "AI解析結果が空でした。もう一度お試しください。",
            }

    except GeminiAnalysisError as e:
        return {"status": "error", "message": str(e)}
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": "AI解析結果の読み取りに失敗しました。もう一度お試しください。",
        }

    # カタログから商品データを参照
    recommendations = result_dict.get("recommendations", [])
    for rec in recommendations:
        product_ids = rec.get("product_ids", [])
        rec["shopify_products"] = catalog_cache.get_products_by_ids(product_ids)

    return {"status": "success", "data": result_dict}
```

- [ ] **Step 6: Run tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 7: Commit**

```bash
git add backend/gemini_service.py backend/services/projection_manager.py backend/routers/analyze.py backend/tests/test_websocket_projection.py backend/tests/test_gemini.py
git commit -m "feat: add streaming analyze with thinking broadcast to projection"
```

---

## Task 3: Update Mock Service + TypeScript Types

**Files:**
- Modify: `backend/mock_service.py`
- Modify: `frontend/src/lib/projection-types.ts`
- Test: `backend/tests/test_mock_service.py`

- [ ] **Step 1: Write failing test for mock yuragi**

Add to `backend/tests/test_mock_service.py`:

```python
@pytest.mark.asyncio
async def test_mock_analysis_has_yuragi():
    """モック結果に yuragi が含まれる"""
    result = await get_mock_analysis()
    assert "yuragi" in result
    assert "confidence" in result["yuragi"]
    assert "mood" in result["yuragi"]
    assert "reasoning" in result["yuragi"]
    assert 0.0 <= result["yuragi"]["confidence"] <= 1.0
    assert result["yuragi"]["mood"] in ["sharp", "smooth", "pulse", "calm"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_mock_service.py::test_mock_analysis_has_yuragi -v`
Expected: FAIL

- [ ] **Step 3: Add yuragi to MOCK_ANALYSIS**

In `backend/mock_service.py`, add to `MOCK_ANALYSIS` dict (after `"recommendations": [...]`):

```python
    "yuragi": {
        "confidence": 0.78,
        "mood": "calm",
        "reasoning": "アメカジ定番のクリーンなスタイルで、在庫との相性も良い",
    }
```

- [ ] **Step 4: Run tests**

Run: `cd backend && python -m pytest tests/test_mock_service.py -v`
Expected: ALL PASS

- [ ] **Step 5: Update TypeScript types**

Replace `frontend/src/lib/projection-types.ts`:

```typescript
export type AppState =
  | "IDLE"
  | "PREFERENCE"
  | "CAMERA_ACTIVE"
  | "ANALYZING"
  | "RESULT";

export interface ShopifyProduct {
  id: string;
  title: string;
  description: string;
  price: string;
  image_url: string;
  url: string;
}

export interface RecommendationItem {
  title: string;
  reason: string;
  product_ids: number[];
  category: string;
  shopify_products: ShopifyProduct[];
}

export interface YuragiOutput {
  confidence: number;
  mood: "sharp" | "smooth" | "pulse" | "calm";
  reasoning: string;
}

export interface ClothingAnalysis {
  analyzed_outfit: string;
  detected_style: string[];
  box_ymin: number;
  box_xmin: number;
  box_ymax: number;
  box_xmax: number;
  recommendations: RecommendationItem[];
  yuragi?: YuragiOutput;
}

export interface ProjectionPayload {
  selectedTags: string[];
  userName: string;
  capturedImage: string | null;
  recommendation: ClothingAnalysis | null;
  analyzeTimedOut: boolean;
  yuragi?: YuragiOutput;
}
```

- [ ] **Step 6: Commit**

```bash
git add backend/mock_service.py backend/tests/test_mock_service.py frontend/src/lib/projection-types.ts
git commit -m "feat: add yuragi to mock data and TypeScript types"
```

---

## Task 4: Create useYuragi Hook

**Files:**
- Create: `frontend/src/hooks/useYuragi.ts`

- [ ] **Step 1: Create the hook**

Create `frontend/src/hooks/useYuragi.ts`:

```typescript
"use client";

import { useMemo, useCallback, useRef } from "react";
import { useMotionValue, useSpring, MotionValue } from "framer-motion";
import { useEffect } from "react";
import { AppState, YuragiOutput } from "@/lib/projection-types";

export interface YuragiParams {
  amplitude: number;
  speed: number;
  turbulence: number;
  easing: string;
  jitter: boolean;
}

const YURAGI_STATE: Record<AppState, YuragiParams> = {
  IDLE:          { amplitude: 0.3, speed: 8,   turbulence: 0,   easing: "easeInOut", jitter: false },
  PREFERENCE:    { amplitude: 0.5, speed: 6,   turbulence: 0,   easing: "easeInOut", jitter: false },
  CAMERA_ACTIVE: { amplitude: 0.8, speed: 4,   turbulence: 0.2, easing: "easeInOut", jitter: false },
  ANALYZING:     { amplitude: 2.0, speed: 1.5, turbulence: 1.0, easing: "easeOut",   jitter: true },
  RESULT:        { amplitude: 0.3, speed: 10,  turbulence: 0,   easing: "easeInOut", jitter: false },
};

const MOOD_PROFILES: Record<string, { speedMult: number; easing: string; jitter: boolean }> = {
  sharp:  { speedMult: 0.5, easing: "easeOut",   jitter: true },
  smooth: { speedMult: 1.5, easing: "easeInOut", jitter: false },
  pulse:  { speedMult: 0.8, easing: "linear",    jitter: true },
  calm:   { speedMult: 2.0, easing: "easeInOut", jitter: false },
};

function geminiYuragiToParams(yuragi: YuragiOutput): YuragiParams {
  const profile = MOOD_PROFILES[yuragi.mood] || MOOD_PROFILES.calm;
  return {
    amplitude: (1 - yuragi.confidence) * 2.5,
    speed: 10 * profile.speedMult,
    turbulence: Math.max(0, (1 - yuragi.confidence) * 0.8),
    easing: profile.easing,
    jitter: profile.jitter,
  };
}

export interface UseYuragiReturn {
  params: YuragiParams;
  amplitudeSpring: MotionValue<number>;
  turbulenceSpring: MotionValue<number>;
  applyThinkingBoost: (textLength?: number) => void;
  beginConverging: () => void;
}

export function useYuragi(
  appState: AppState,
  geminiYuragi?: YuragiOutput | null,
): UseYuragiReturn {
  const targetParams = useMemo(() => {
    if (appState === "RESULT" && geminiYuragi) {
      return geminiYuragiToParams(geminiYuragi);
    }
    return YURAGI_STATE[appState];
  }, [appState, geminiYuragi]);

  // Spring-animated values for smooth transitions
  const amplitudeMotion = useMotionValue(targetParams.amplitude);
  const turbulenceMotion = useMotionValue(targetParams.turbulence);
  const amplitudeSpring = useSpring(amplitudeMotion, { stiffness: 50, damping: 20 });
  const turbulenceSpring = useSpring(turbulenceMotion, { stiffness: 50, damping: 20 });

  const targetRef = useRef(targetParams);
  targetRef.current = targetParams;

  useEffect(() => {
    amplitudeMotion.set(targetParams.amplitude);
    turbulenceMotion.set(targetParams.turbulence);
  }, [targetParams, amplitudeMotion, turbulenceMotion]);

  // Thinking chunk boost: temporarily increase amplitude + turbulence
  const applyThinkingBoost = useCallback((textLength?: number) => {
    const currentAmp = targetRef.current.amplitude;
    amplitudeMotion.set(currentAmp + 0.5);
    setTimeout(() => amplitudeMotion.set(targetRef.current.amplitude), 500);

    // Turbulence boost proportional to text length
    if (textLength) {
      const currentTurb = targetRef.current.turbulence;
      const boost = Math.min(0.3, textLength / 500);
      turbulenceMotion.set(currentTurb + boost);
      setTimeout(() => turbulenceMotion.set(targetRef.current.turbulence), 800);
    }
  }, [amplitudeMotion, turbulenceMotion]);

  // Begin converging (called when JSON output starts during ANALYZING)
  const beginConverging = useCallback(() => {
    // Ease toward RESULT-like values to signal "answer is coming"
    amplitudeMotion.set(0.8);
    turbulenceMotion.set(0.3);
  }, [amplitudeMotion, turbulenceMotion]);

  return {
    params: targetParams,
    amplitudeSpring,
    turbulenceSpring,
    applyThinkingBoost,
    beginConverging,
  };
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx next build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useYuragi.ts
git commit -m "feat: create useYuragi hook with state-driven and AI-driven parameters"
```

---

## Task 5: Create GlassPanel Component

**Files:**
- Create: `frontend/src/components/projection/GlassPanel.tsx`

- [ ] **Step 1: Create the component**

Create `frontend/src/components/projection/GlassPanel.tsx`:

```tsx
"use client";

import { motion, useTransform, MotionValue, useMotionValue } from "framer-motion";
import { useId, useRef, useEffect } from "react";

interface GlassPanelProps {
  children: React.ReactNode;
  className?: string;
  amplitudeSpring?: MotionValue<number>;
  turbulenceSpring?: MotionValue<number>;
  speed?: number;
  enableTurbulence?: boolean;
}

export function GlassPanel({
  children,
  className = "",
  amplitudeSpring,
  turbulenceSpring,
  speed = 8,
  enableTurbulence = false,
}: GlassPanelProps) {
  const filterId = useId().replace(/:/g, "_");

  // Always call hooks unconditionally (React Rules of Hooks)
  const defaultAmplitude = useMotionValue(0.3);
  const defaultTurbulence = useMotionValue(0);

  const activeAmplitude = amplitudeSpring ?? defaultAmplitude;
  const activeTurbulence = turbulenceSpring ?? defaultTurbulence;

  // Breathing animation: use a time-based MotionValue that cycles
  // The scale and rotate are derived from amplitude spring, so they react to state changes
  const breathPhase = useMotionValue(0);

  useEffect(() => {
    let frame: number;
    let start: number | null = null;
    const animate = (timestamp: number) => {
      if (start === null) start = timestamp;
      const elapsed = (timestamp - start) / 1000;
      // Sine wave: 0 → 1 → 0 → -1 → 0 over `speed` seconds
      const phase = Math.sin((elapsed / speed) * Math.PI * 2);
      breathPhase.set(phase);
      frame = requestAnimationFrame(animate);
    };
    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [speed, breathPhase]);

  // Derive reactive scale and rotate from amplitude × breathing phase
  const scale = useTransform(
    [activeAmplitude, breathPhase] as MotionValue[],
    ([amp, phase]: number[]) => 1 + amp * 0.01 * Math.abs(phase)
  );
  const rotate = useTransform(
    [activeAmplitude, breathPhase] as MotionValue[],
    ([amp, phase]: number[]) => amp * 0.5 * phase
  );

  // Update SVG displacement scale reactively via ref
  const displacementRef = useRef<SVGFEDisplacementMapElement>(null);
  const displacementScale = useTransform(activeTurbulence, (t) => t * 12);

  useEffect(() => {
    const unsubscribe = displacementScale.on("change", (v) => {
      if (displacementRef.current) {
        displacementRef.current.setAttribute("scale", String(v));
      }
    });
    return unsubscribe;
  }, [displacementScale]);

  return (
    <>
      {/* SVG filter for edge dissolution */}
      {enableTurbulence && (
        <svg className="absolute w-0 h-0" aria-hidden="true">
          <defs>
            <filter id={`yuragi-${filterId}`}>
              <feTurbulence
                type="turbulence"
                baseFrequency="0.015"
                numOctaves={3}
                seed={1}
              >
                <animate
                  attributeName="baseFrequency"
                  values="0.015;0.025;0.015"
                  dur="4s"
                  repeatCount="indefinite"
                />
              </feTurbulence>
              <feDisplacementMap
                ref={displacementRef}
                in="SourceGraphic"
                scale="0"
              />
            </filter>
          </defs>
        </svg>
      )}

      <motion.div
        className={`
          bg-white/[0.03]
          backdrop-blur-xl backdrop-saturate-[1.2]
          border border-white/[0.06]
          shadow-[0_8px_32px_rgba(0,0,0,0.3),inset_0_1px_0_rgba(255,255,255,0.04)]
          rounded-3xl
          ${className}
        `}
        style={{
          scale,
          rotate,
          willChange: "transform",
          ...(enableTurbulence
            ? { filter: `url(#yuragi-${filterId})` }
            : {}),
        }}
      >
        {children}
      </motion.div>
    </>
  );
}
```

**Key design decisions:**
- Breathing is driven by `requestAnimationFrame` loop writing to a `breathPhase` MotionValue, not by Framer Motion `animate` keyframes. This ensures the animation reacts to spring changes (amplitude) in real-time.
- `scale` and `rotate` are derived via `useTransform` from `[amplitude, breathPhase]` — fully reactive, no `.get()` snapshots.
- SVG `feDisplacementMap scale` is updated via `ref` + `on("change")` listener since SVG attributes can't be directly driven by MotionValues.
- The `easing` prop is removed — the sine wave provides natural easing. The spring damping on the amplitude value handles transition smoothness.

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx next build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/projection/GlassPanel.tsx
git commit -m "feat: create GlassPanel component with glassmorphism and SVG turbulence"
```

---

## Task 6: Integrate into All Projection Components (Single Atomic Change)

This task modifies `projection/page.tsx`, `ProjectionScenes.tsx`, and `ProjectionResultScene.tsx` as a single atomic change so the build never breaks.

**Files:**
- Modify: `frontend/src/app/projection/page.tsx`
- Modify: `frontend/src/components/projection/ProjectionScenes.tsx`
- Modify: `frontend/src/components/projection/ProjectionResultScene.tsx`

- [ ] **Step 1: Update projection page**

Replace `frontend/src/app/projection/page.tsx`:

```tsx
"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { AnimatePresence } from "framer-motion";
import { AppState, ProjectionPayload, YuragiOutput } from "@/lib/projection-types";
import { useYuragi } from "@/hooks/useYuragi";

import { ProjectionBackground } from "@/components/projection/ProjectionBackground";
import { MirrorOverlay, ProjectionIdleScene, ProjectionPreferenceScene, ProjectionCameraScene, ProjectionAnalyzingScene } from "@/components/projection/ProjectionScenes";
import { ProjectionResultScene } from "@/components/projection/ProjectionResultScene";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_URL = API_URL.replace(/^http/, "ws") + "/ws/projection/display";

const defaultPayload: ProjectionPayload = {
  selectedTags: [],
  userName: "",
  capturedImage: null,
  recommendation: null,
  analyzeTimedOut: false,
};

export default function ProjectionPage() {
  const [appState, setAppState] = useState<AppState>("IDLE");
  const [payload, setPayload] = useState<ProjectionPayload>(defaultPayload);

  // フラッシュエフェクト用
  const [flash, setFlash] = useState(false);

  // ミラーカメラフレーム
  const [mirrorFrame, setMirrorFrame] = useState<string | null>(null);

  // ゆらぎ & 思考ストリーム
  const [geminiYuragi, setGeminiYuragi] = useState<YuragiOutput | null>(null);
  const [thinkingText, setThinkingText] = useState<string>("");
  const [thinkingIndex, setThinkingIndex] = useState(0);

  const yuragi = useYuragi(appState, geminiYuragi);

  // Store yuragi callbacks in refs to avoid stale closures in WebSocket handler
  const yuragiRef = useRef(yuragi);
  yuragiRef.current = yuragi;

  const wsRef = useRef<WebSocket | null>(null);

  const connectDisplay = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("[Projection WS] Connected (Display)");
      ws.send(JSON.stringify({ type: "REQUEST_STATE" }));
    };

    ws.onmessage = (e) => {
      if (typeof e.data !== "string") return;

      if (e.data.startsWith("{")) {
        try {
          const data = JSON.parse(e.data);
          if (data.type === "STATE_CHANGE" && data.state) {
            setAppState(data.state as AppState);
            if (data.payload) {
              setPayload((prev) => ({ ...prev, ...data.payload }));
            }
            // Extract yuragi from recommendation on RESULT
            if (data.state === "RESULT" && data.payload?.recommendation?.yuragi) {
              setGeminiYuragi(data.payload.recommendation.yuragi);
            }
            // Reset thinking state on new analysis
            if (data.state === "ANALYZING") {
              setThinkingText("");
              setThinkingIndex(0);
              setGeminiYuragi(null);
            }
          } else if (data.type === "FLASH") {
            setFlash(true);
            setTimeout(() => setFlash(false), 1200);
          } else if (data.type === "THINKING") {
            setThinkingText(data.text);
            setThinkingIndex(data.chunk_index);
            yuragiRef.current.applyThinkingBoost(data.text?.length);
          } else if (data.type === "OUTPUT_STARTED") {
            // JSON出力開始 → ゆらぎ収束開始（ANALYZING Phase 2）
            yuragiRef.current.beginConverging();
            setThinkingText(""); // 思考テキストをフェードアウト
          }
        } catch (err) {
          console.error("Failed to parse projection WS message", err);
        }
      } else {
        setMirrorFrame(e.data);
      }
    };

    ws.onclose = () => {
      console.log("[Projection WS] Disconnected. Reconnect in 3s...");
      setMirrorFrame(null);
      setTimeout(connectDisplay, 3000);
    };

    ws.onerror = (err) => {
      console.error("[Projection WS] Error:", err);
    };
  }, []);

  useEffect(() => {
    connectDisplay();
    return () => { wsRef.current?.close(); };
  }, [connectDisplay]);

  const showMirror = appState === "IDLE" || appState === "PREFERENCE" || appState === "CAMERA_ACTIVE" || appState === "ANALYZING";

  return (
    <main className="w-screen h-screen overflow-hidden bg-[#141E2B] text-[#F0F2F5] font-sans cursor-none relative">

      <ProjectionBackground appState={appState} selectedTags={payload.selectedTags} />

      <AnimatePresence>
        {flash && (
          <div className="absolute inset-0 bg-white z-[9999] pointer-events-none transition-opacity duration-[1200ms] ease-out opacity-0 starting:opacity-100" />
        )}
      </AnimatePresence>

      <AnimatePresence mode="wait">
        {appState === "IDLE" && <ProjectionIdleScene key="idle" yuragi={yuragi} />}
        {appState === "PREFERENCE" && <ProjectionPreferenceScene key="pref" payload={payload} yuragi={yuragi} />}
        {appState === "CAMERA_ACTIVE" && <ProjectionCameraScene key="camera" payload={payload} yuragi={yuragi} />}
        {appState === "ANALYZING" && <ProjectionAnalyzingScene key="analyzing" payload={payload} yuragi={yuragi} thinkingText={thinkingText} thinkingIndex={thinkingIndex} />}
        {appState === "RESULT" && <ProjectionResultScene key="result" payload={payload} yuragi={yuragi} />}
      </AnimatePresence>

      <AnimatePresence>
        {showMirror && <MirrorOverlay key="mirror" frame={mirrorFrame} />}
      </AnimatePresence>
    </main>
  );
}
```

- [ ] **Step 2: Update ProjectionScenes**

Replace `frontend/src/components/projection/ProjectionScenes.tsx`:

```tsx
"use client";

import { motion, AnimatePresence } from "framer-motion";
import { ProjectionPayload } from "@/lib/projection-types";
import { UseYuragiReturn } from "@/hooks/useYuragi";
import { GlassPanel } from "./GlassPanel";
import CatIcon from "@/components/icons/CatIcon";

// ============================================
// IDLE SCENE
// ============================================
export function ProjectionIdleScene({ yuragi }: { yuragi: UseYuragiReturn }) {
  return (
    <motion.div
      key="idle"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 1 }}
      className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none overflow-hidden"
    >
      <GlassPanel
        className="flex flex-col items-center gap-6 p-12 z-10"
        amplitudeSpring={yuragi.amplitudeSpring}
        speed={yuragi.params.speed}

      >
        <div className="flex items-center gap-6 mb-6">
          <div className="w-24 h-24 bg-[#FF6B35] rounded-3xl flex items-center justify-center shadow-lg">
            <span className="text-[#141E2B] text-4xl font-extrabold">85</span>
          </div>
          <span className="text-6xl font-black text-[#FF8A5B] tracking-[0.15em]">STORE</span>
        </div>
        <CatIcon variant="default" size={80} theme="dark" />
        <p className="text-3xl text-[#8A9AAD] font-light tracking-wide mt-4">
          AIがあなたにぴったりの一点モノを見つけます
        </p>
      </GlassPanel>
    </motion.div>
  );
}

// ============================================
// PREFERENCE SCENE
// ============================================
export function ProjectionPreferenceScene({ payload, yuragi }: { payload: ProjectionPayload; yuragi: UseYuragiReturn }) {
  return (
    <motion.div
      key="pref"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 flex flex-col items-center justify-center p-12 text-center"
    >
      <GlassPanel
        className="flex flex-col items-center p-12 max-w-4xl"
        amplitudeSpring={yuragi.amplitudeSpring}
        speed={yuragi.params.speed}

      >
        <div className="flex items-center gap-4 mb-8">
          <CatIcon variant="thinking" size={48} theme="dark" />
          <h2 className="text-4xl text-[#8A9AAD] font-light">
            好みを入力中...
          </h2>
        </div>

        {payload.userName && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-6xl font-bold text-[#FF6B35] mb-12 drop-shadow-lg"
          >
            ようこそ、{payload.userName} さん
          </motion.div>
        )}

        <div className="flex flex-wrap justify-center gap-4">
          {payload.selectedTags.map((tag, i) => (
            <motion.div
              key={tag}
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
              className="px-6 py-3 rounded-full border-2 border-[#FF6B35]/50 bg-[#FF6B35]/10 text-[#FF8A5B] text-2xl font-bold shadow-[0_0_15px_rgba(255,107,53,0.2)]"
            >
              {tag}
            </motion.div>
          ))}
        </div>
      </GlassPanel>
    </motion.div>
  );
}

// ============================================
// CAMERA SCENE
// ============================================
export function ProjectionCameraScene({ payload, yuragi }: { payload: ProjectionPayload; yuragi: UseYuragiReturn }) {
  const hLines = Array.from({ length: 10 });
  const vLines = Array.from({ length: 10 });

  return (
    <motion.div
      key="camera"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
    >
      <div className="absolute inset-0 opacity-20">
        <div className="absolute inset-0 flex flex-col justify-evenly">
          {hLines.map((_, i) => (
            <div key={`h-${i}`} className="w-full h-[1px] bg-[#FF6B35]/30 shadow-[0_0_5px_rgba(255,107,53,0.3)]" />
          ))}
        </div>
        <div className="absolute inset-0 flex justify-evenly">
          {vLines.map((_, i) => (
            <div key={`v-${i}`} className="h-full w-[1px] bg-[#FF6B35]/30 shadow-[0_0_5px_rgba(255,107,53,0.3)]" />
          ))}
        </div>
      </div>

      <motion.div
        animate={{ top: ["-10%", "110%"] }}
        transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
        className="absolute left-0 right-0 h-4 bg-[#FF6B35]/40 shadow-[0_0_40px_rgba(255,107,53,0.8)]"
      />

      {/* STANDBY with blur halo */}
      <div className="absolute top-16 left-1/2 -translate-x-1/2 text-center z-20 mix-blend-plus-lighter">
        <h2 className="text-4xl font-mono text-[#FF6B35] tracking-[0.5em] opacity-80 drop-shadow-[0_0_20px_rgba(255,107,53,0.4)]">
          STANDBY
        </h2>
      </div>

      <GlassPanel
        className="absolute bottom-16 left-1/2 -translate-x-1/2 flex flex-wrap justify-center gap-3 w-full max-w-3xl px-8 py-4 z-20"
        amplitudeSpring={yuragi.amplitudeSpring}
        turbulenceSpring={yuragi.turbulenceSpring}
        speed={yuragi.params.speed}

        enableTurbulence={yuragi.params.turbulence > 0}
      >
        {payload.selectedTags.map((tag) => (
          <div key={tag} className="px-4 py-1.5 border border-white/[0.08] bg-white/[0.03] text-[#8A9AAD] text-lg rounded font-mono">
            {tag}
          </div>
        ))}
      </GlassPanel>
    </motion.div>
  );
}

// ============================================
// ANALYZING SCENE
// ============================================
interface AnalyzingSceneProps {
  payload: ProjectionPayload;
  yuragi: UseYuragiReturn;
  thinkingText: string;
  thinkingIndex: number;
}

export function ProjectionAnalyzingScene({ payload, yuragi, thinkingText, thinkingIndex }: AnalyzingSceneProps) {
  return (
    <motion.div
       key="analyze"
       initial={{ opacity: 0, scale: 0.9 }}
       animate={{ opacity: 1, scale: 1 }}
       exit={{ opacity: 0, scale: 1.1 }}
       transition={{ duration: 0.8 }}
       className="absolute inset-0 flex flex-col items-center justify-center"
     >
       {/* 撮影画像 — GlassPanel with turbulence */}
       {payload.capturedImage && (
         <GlassPanel
           className="relative w-1/3 aspect-[3/4] overflow-hidden z-10"
           amplitudeSpring={yuragi.amplitudeSpring}
           turbulenceSpring={yuragi.turbulenceSpring}
           speed={yuragi.params.speed}
   
           enableTurbulence={true}
         >
           <img src={payload.capturedImage} className="w-full h-full object-cover rounded-3xl" alt="Captured" />

           <motion.div
             animate={{ top: ['0%', '100%', '0%'] }}
             transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
             className="absolute left-0 right-0 h-2 bg-[#FF6B35] shadow-[0_0_20px_rgba(255,107,53,1)] opacity-70"
           />
         </GlassPanel>
       )}

       {/* CatIcon thinking */}
       <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-0">
         <CatIcon variant="thinking" size={96} theme="dark" />
       </div>

       {/* 思考テキスト + ステータス */}
       <div className="absolute bottom-20 left-1/2 -translate-x-1/2 text-center z-20 flex flex-col items-center gap-4">
         {/* 思考ストリーム表示 */}
         <AnimatePresence mode="wait">
           {thinkingText && (
             <motion.div
               key={thinkingIndex}
               initial={{ opacity: 0, y: 8 }}
               animate={{ opacity: 0.6, y: 0 }}
               exit={{ opacity: 0, y: -8 }}
               transition={{ duration: 0.5 }}
               className="text-[#8A9AAD] text-lg font-light italic max-w-md text-center"
             >
               {thinkingText.length > 100 ? thinkingText.slice(0, 100) + "..." : thinkingText}
             </motion.div>
           )}
         </AnimatePresence>

         <motion.h2
           animate={{ opacity: [0.5, 1, 0.5] }}
           transition={{ duration: 2, repeat: Infinity }}
           className="text-4xl text-[#F0F2F5] font-bold tracking-widest bg-[#141E2B]/70 px-8 py-4 rounded-full"
         >
           AI CONNECTING...
         </motion.h2>
         {payload.analyzeTimedOut && (
           <p className="text-xl text-[#FF8A5B] mt-4 bg-[#141E2B]/70 px-6 py-2 rounded-full inline-block">
             膨大なデーターベースから探索中です。少々お待ちください…
           </p>
         )}
       </div>
    </motion.div>
  );
}

// ============================================
// MIRROR OVERLAY
// ============================================
export function MirrorOverlay({ frame }: { frame: string | null }) {
  if (!frame) return null;
  return (
    <div className="absolute inset-0 z-30 pointer-events-none flex items-center justify-center opacity-80 mix-blend-screen">
      <img
        src={`data:image/webp;base64,${frame}`}
        className="w-full h-full object-cover scale-x-[-1]"
        alt="mirror stream"
      />
    </div>
  );
}
```

- [ ] **Step 3: Update ProjectionResultScene**

Replace `frontend/src/components/projection/ProjectionResultScene.tsx`:

```tsx
"use client";

import { motion } from "framer-motion";
import Image from "next/image";
import QRCode from "../QRCode";
import { ProjectionPayload } from "@/lib/projection-types";
import { UseYuragiReturn } from "@/hooks/useYuragi";
import { GlassPanel } from "./GlassPanel";
import CatIcon from "@/components/icons/CatIcon";
import { FishIcon } from "@/components/icons/PixelIcons";

export function ProjectionResultScene({ payload, yuragi }: { payload: ProjectionPayload; yuragi: UseYuragiReturn }) {
  const rec = payload.recommendation;
  if (!rec) return null;

  const ymin = rec.box_ymin / 10;
  const xmin = rec.box_xmin / 10;
  const ymax = rec.box_ymax / 10;
  const xmax = rec.box_xmax / 10;

  return (
    <motion.div
      key="result"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.8 }}
      className="absolute inset-0 p-12 flex flex-col z-20"
    >
      {/* 画面上部: 解析結果とタグ */}
      <GlassPanel
        className="flex gap-12 h-[35%] w-full mb-8 p-8"
        amplitudeSpring={yuragi.amplitudeSpring}
        speed={yuragi.params.speed}

      >
        <div className="relative h-full aspect-[4/3] bg-[#141E2B] rounded-2xl overflow-hidden border border-white/[0.06] shadow-[0_0_20px_rgba(0,0,0,0.5)]">
          {payload.capturedImage && (
             <img src={payload.capturedImage} className="w-full h-full object-contain" alt="Captured" />
          )}
          {rec.box_ymin > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="absolute pointer-events-none border-4 border-[#FF6B35] bg-[#FF6B35]/20"
              style={{
                top: `${Math.max(0, Math.min(100, ymin))}%`,
                left: `${Math.max(0, Math.min(100, xmin))}%`,
                height: `${Math.max(0, Math.min(100, ymax - ymin))}%`,
                width: `${Math.max(0, Math.min(100, xmax - xmin))}%`,
              }}
            >
              <div className="absolute -top-6 left-1/2 -translate-x-1/2 bg-[#FF6B35] text-white text-sm px-4 py-1 rounded-full font-bold shadow-lg">
                DETECTED
              </div>
            </motion.div>
          )}
        </div>

        <div className="flex-1 flex flex-col justify-center space-y-6">
          <h2 className="text-4xl font-bold text-[#F0F2F5] drop-shadow-lg flex items-center gap-3">
            <CatIcon variant="happy" size={48} theme="dark" />
            AI STYLING ANALYSIS
          </h2>
          <p className="text-2xl text-[#8A9AAD] leading-relaxed font-light drop-shadow-md">
            {rec.analyzed_outfit}
          </p>
          <div className="flex flex-wrap gap-3">
            {rec.detected_style.map((tag, i) => (
              <span key={`detected-${i}`} className="px-5 py-2 bg-white/[0.03] border border-white/[0.06] text-[#8A9AAD] rounded-full text-lg">
                {tag}
              </span>
            ))}
            {payload.selectedTags.map((tag, i) => (
              <span key={`sel-${i}`} className="px-5 py-2 bg-[#FF6B35]/20 border border-[#FF6B35]/50 text-[#FF8A5B] rounded-full text-lg">
                {tag}
              </span>
            ))}
          </div>
        </div>
      </GlassPanel>

      {/* 提案カード */}
      <div className="flex-1 flex gap-8 w-full">
        {rec.recommendations.map((recommendation, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + i * 0.2 }}
            className="flex-1"
          >
            <GlassPanel
              className="h-full p-6 flex flex-col relative overflow-hidden"
              speed={yuragi.params.speed + i * 0.5}
      
            >
              <div className="absolute top-0 right-0 text-[10rem] font-black text-white/[0.03] leading-none -mt-4 mr-2 pointer-events-none">
                {i + 1}
              </div>

              <h3 className="text-2xl font-bold text-[#F0F2F5] mb-2 border-b border-white/[0.06] pb-3 flex items-center justify-between z-10">
                <span className="flex items-center gap-2">
                  <FishIcon size={24} theme="dark" />
                  {recommendation.title}
                </span>
                <span className="text-sm px-3 py-1 bg-[#FF6B35]/20 text-[#FF6B35] rounded-full border border-[#FF6B35]/30">
                  {recommendation.category}
                </span>
              </h3>

              <p className="text-[#8A9AAD] text-lg my-4 flex-1 line-clamp-3 z-10 drop-shadow">
                {recommendation.reason}
              </p>

              {recommendation.shopify_products?.length > 0 ? (
                <div className="grid grid-cols-2 gap-4 h-56 z-10">
                  {recommendation.shopify_products.slice(0, 2).map((product) => (
                    <div key={product.id} className="relative bg-[#141E2B] rounded-xl overflow-hidden shadow-lg border border-white/[0.06] group">
                      {product.image_url && (
                         <Image
                           src={product.image_url}
                           alt={product.title}
                           fill
                           className="object-cover"
                           sizes="200px"
                         />
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-[#141E2B]/90 via-[#141E2B]/40 to-transparent flex flex-col justify-end p-3">
                        <p className="text-white text-xs font-bold line-clamp-2 leading-tight drop-shadow-md">
                          {product.title}
                        </p>
                        <p className="text-[#FF6B35] text-sm font-black mt-1 drop-shadow-md">
                          ¥{parseInt(product.price).toLocaleString()}
                        </p>
                      </div>
                      <div className="absolute top-2 right-2 bg-white p-1 rounded-md shadow-lg opacity-90 scale-75 origin-top-right">
                         <QRCode url={product.url} productTitle={product.title} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                  <div className="h-48 flex items-center justify-center text-[#6B7B8D] bg-white/[0.02] rounded-xl border border-dashed border-white/[0.06]">
                    NO ITEM
                  </div>
              )}
            </GlassPanel>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
```

- [ ] **Step 4: Verify frontend builds**

Run: `cd frontend && npx next build`
Expected: Build succeeds with no errors

- [ ] **Step 5: Run frontend lint**

Run: `cd frontend && npx next lint`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/projection/page.tsx frontend/src/components/projection/ProjectionScenes.tsx frontend/src/components/projection/ProjectionResultScene.tsx
git commit -m "feat: integrate GlassPanel, yuragi, and thinking stream into all projection scenes"
```

---

## Task 7: Final Verification

- [ ] **Step 1: Run backend tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 2: Run frontend build**

Run: `cd frontend && npx next build`
Expected: Build succeeds

- [ ] **Step 3: Run frontend lint**

Run: `cd frontend && npx next lint`
Expected: No errors

- [ ] **Step 4: Fix any issues found and commit fixes**

```bash
git add -A
git commit -m "fix: resolve issues from glassmorphism integration"
```
