"""
技術検証: google-genai SDK の3機能
1. Streaming + 構造化出力の組み合わせ
2. Thinking Mode (include_thoughts)
3. Streaming + Thinking の組み合わせ
"""
import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY not set")
    sys.exit(1)

client = genai.Client(api_key=api_key)

# --- Simple structured output schema ---
class SimpleAnalysis(BaseModel):
    summary: str = Field(description="1文の要約")
    confidence: float = Field(description="0.0-1.0の確信度")
    mood: str = Field(description="sharp, smooth, pulse, calm のいずれか")

PROMPT = "「ストリート系のジャケットを着た20代男性に似合う古着」について1文で要約し、提案への確信度(0-1)とムード(sharp/smooth/pulse/calm)を返してください。"

# ============================================
# Test 1: Streaming + Structured Output
# ============================================
print("=" * 60)
print("TEST 1: Streaming + Structured Output (response_schema)")
print("=" * 60)
try:
    chunks = []
    for chunk in client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=PROMPT,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SimpleAnalysis,
        ),
    ):
        text = chunk.text if chunk.text else ""
        chunks.append(text)
        print(f"  chunk[{len(chunks)}]: {repr(text[:80])}")

    full = "".join(chunks)
    print(f"\n  Full response: {full}")
    parsed = json.loads(full)
    print(f"  Parsed: {parsed}")
    print("  ✅ PASS: Streaming + Structured Output works")
except Exception as e:
    print(f"  ❌ FAIL: {type(e).__name__}: {e}")

# ============================================
# Test 2: Thinking Mode (include_thoughts)
# ============================================
print("\n" + "=" * 60)
print("TEST 2: Thinking Mode (include_thoughts=True)")
print("=" * 60)
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=PROMPT,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SimpleAnalysis,
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
                thinking_budget=512,
            ),
        ),
    )

    thoughts = []
    output = []
    for part in response.candidates[0].content.parts:
        if part.thought:
            thoughts.append(part.text)
            print(f"  💭 Thought: {part.text[:120]}...")
        else:
            output.append(part.text)
            print(f"  📝 Output: {part.text[:120]}")

    print(f"\n  Thought parts: {len(thoughts)}")
    print(f"  Output parts: {len(output)}")
    if output:
        parsed = json.loads("".join(output))
        print(f"  Parsed output: {parsed}")
    print("  ✅ PASS: Thinking Mode works")
except Exception as e:
    print(f"  ❌ FAIL: {type(e).__name__}: {e}")

# ============================================
# Test 3: Streaming + Thinking
# ============================================
print("\n" + "=" * 60)
print("TEST 3: Streaming + Thinking + Structured Output")
print("=" * 60)
try:
    thought_chunks = []
    output_chunks = []
    chunk_count = 0

    for chunk in client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=PROMPT,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SimpleAnalysis,
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
                thinking_budget=512,
            ),
        ),
    ):
        chunk_count += 1
        if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
            for part in chunk.candidates[0].content.parts:
                if part.thought:
                    thought_chunks.append(part.text or "")
                    print(f"  💭 chunk[{chunk_count}] thought: {(part.text or '')[:80]}")
                else:
                    output_chunks.append(part.text or "")
                    print(f"  📝 chunk[{chunk_count}] output: {(part.text or '')[:80]}")
        else:
            print(f"  ⏳ chunk[{chunk_count}]: (no content)")

    print(f"\n  Total chunks: {chunk_count}")
    print(f"  Thought chunks: {len(thought_chunks)}")
    print(f"  Output chunks: {len(output_chunks)}")

    if thought_chunks:
        full_thought = "".join(thought_chunks)
        print(f"  Full thought: {full_thought[:200]}")
    if output_chunks:
        full_output = "".join(output_chunks)
        parsed = json.loads(full_output)
        print(f"  Parsed output: {parsed}")

    print("  ✅ PASS: Streaming + Thinking + Structured Output works")
except Exception as e:
    print(f"  ❌ FAIL: {type(e).__name__}: {e}")

# ============================================
# Test 4: Check gemini-3.1-pro-preview thinking support
# ============================================
print("\n" + "=" * 60)
print("TEST 4: gemini-3.1-pro-preview + Thinking")
print("=" * 60)
try:
    response = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents=PROMPT,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SimpleAnalysis,
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
                thinking_budget=512,
            ),
        ),
    )

    for part in response.candidates[0].content.parts:
        if part.thought:
            print(f"  💭 Thought: {part.text[:120]}...")
        else:
            print(f"  📝 Output: {part.text[:120]}")
    print("  ✅ PASS: gemini-3.1-pro-preview supports thinking")
except Exception as e:
    print(f"  ❌ FAIL: {type(e).__name__}: {e}")
    print("  → gemini-3.1-pro-previewはthinking非対応の可能性。2.5系にフォールバック必要。")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
