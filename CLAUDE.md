# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

85-Store AI Shop Assistant — an AI-powered retail customer service system for a vintage clothing store. Uses computer vision (Apple Vision / MediaPipe) and Google Gemini to analyze customers' outfits and recommend complementary vintage items from Shopify inventory. Runs on Mac Studio with iPad UI + projector display.

## Commands

### Development (Docker Compose)
```bash
docker compose up --build          # Start both services (backend:8000, frontend:3000)
docker compose down                # Stop containers
docker compose logs -f backend     # View backend logs
docker compose logs -f frontend    # View frontend logs
```

### Backend (native)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000    # Start server
MOCK_MODE=true uvicorn main:app --port 8000     # Start without API keys
```

### Frontend
```bash
cd frontend
npm install
npm run dev       # Dev server on http://localhost:3000
npm run build     # Production build
npm run lint      # ESLint
```

### Testing
```bash
cd backend
pytest tests/ -v                          # All tests
pytest tests/test_api.py -v               # Single test file
pytest tests/test_api.py::test_name -v    # Single test
pytest tests/ --cov=. --cov-report=html   # With coverage
```

## Architecture

```
iPad UI (Next.js :3000) ←REST/WS→ FastAPI Backend (:8000) ←→ Gemini API / Shopify APIs
                                        ↕ WebSocket
                              Projector Display (:3000/projection)
```

### State Machine (synchronized across iPad + Projector via WebSocket)
```
IDLE → PREFERENCE → CAMERA_ACTIVE → ANALYZING → RESULT → IDLE
```

### Backend Structure (`backend/`)
- **`main.py`** — FastAPI app init, CORS, router registration, health check, lifespan (catalog loading)
- **`routers/`** — API endpoints: `analyze.py`, `customers.py`, `mirror.py`, `projection.py`
- **`gemini_service.py`** — Gemini API client (`gemini-3.1-pro-preview`) with Pydantic structured output (`ClothingAnalysis` schema). Recommendations reference catalog product IDs.
- **`catalog_service.py`** — Product catalog cache: loads all Shopify products at startup, builds compact TSV for Gemini prompt injection (~196 products, ~26K chars), resolves product IDs to full data. Background refresh every 30min.
- **`shopify_service.py`** — Shopify Storefront API (product search via GraphQL)
- **`customer_service.py`** — Shopify Admin API (customer CRUD + metafields for style preferences & body measurements)
- **`shopify_auth.py`** — `ShopifyTokenManager` singleton (Client Credentials Grant, auto-renewal)
- **`mirror_service.py`** — Camera capture + person segmentation. Dedicated single-thread executor for AVFoundation thread safety. Art-quality mask refinement (sigmoid threshold, morphology, distance-transform feathering). Output resized to 960px width for WebP encoding performance.
- **`vision_segmenter.py`** — Apple Vision Framework wrapper (macOS only). Input resized to 1024x768 before CGImage conversion for Neural Engine efficiency.
- **`mock_service.py`** — Hardcoded responses for development without API keys (`MOCK_MODE=true`)
- **`services/projection_manager.py`** — State sync + mirror frame broadcaster. Single display WebSocket carries both JSON control messages and base64 mirror frames.
- **`tag_products.py`** — Utility script to auto-tag Shopify products using Gemini + Admin API
- **`normalize_measurements.py`** — Extract garment measurements from product descriptions and save as Shopify metafield `custom:measurements` (JSON). Supports tops (`肩幅49cm - 身幅63cm`), bottoms (`ウエスト 82cm`), and multi-size tables (`size1(S) 56cm～`). Run with `--apply` to write.
- **`tests/`** — pytest + pytest-asyncio, all external calls are mocked

### Frontend Structure (`frontend/src/`)
- **`app/page.tsx`** — Main iPad UI (state machine orchestrator)
- **`app/projection/page.tsx`** — Projector display (single WebSocket for state sync + mirror frames)
- **`hooks/`** — `useCamera.ts`, `useBackendAPI.ts`, `useProjectionSync.ts` (pending message queue for WS)
- **`components/operator/`** — iPad UI scenes: `IdleView`, `PreferenceView`, `CameraView`, `AnalyzingView`, `ResultView` (3 collapsible recommendation cards with horizontal product scroll)
- **`components/projection/`** — Projector scenes: `ProjectionBackground` (SVG noise), `ProjectionScenes`, `ProjectionResultScene`
- **`lib/projection-types.ts`** — TypeScript interfaces (`ClothingAnalysis`, `RecommendationItem` with `product_ids`)
- **`components/QRCode.tsx`** — QR code generator component

## Environment Variables

Set in `backend/.env` (see `.env.example`). Key variables:
- `MOCK_MODE` — `true` to run without API keys
- `GEMINI_API_KEY` — Google AI Studio key
- `SHOPIFY_STORE_URL` — e.g. `store.myshopify.com`
- `SHOPIFY_STOREFRONT_ACCESS_TOKEN` — Public Storefront API token
- `SHOPIFY_ADMIN_API_ACCESS_TOKEN` — Admin API token (`shpat_...`)
- `SHOPIFY_CLIENT_ID` / `SHOPIFY_CLIENT_SECRET` — For auto token renewal

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, google-genai (Gemini), httpx, OpenCV, Pydantic
- **Frontend**: Next.js 16, React 19, TypeScript 5, Tailwind CSS 4, Framer Motion
- **APIs**: Google Gemini 3.1 Pro Preview, Shopify Storefront/Admin GraphQL (2026-01)
- **Vision**: Apple Vision Framework (macOS) / MediaPipe (Linux fallback)

### Key Patterns
- **Catalog-first recommendations**: All 196 products pre-loaded as compact TSV in Gemini prompt. Gemini returns `product_ids` (not search keywords), resolved to full product data from cache. No runtime Shopify search needed.
- **Single WebSocket for projection**: `/ws/projection/display` carries both JSON state messages (`{...}`) and base64 mirror frames. Frontend distinguishes by checking if data starts with `{`.
- **Thread-safe camera**: `MirrorSegmenter` uses a dedicated single-thread `ThreadPoolExecutor` for all OpenCV camera operations (AVFoundation requires same-thread access).

## Environment Variables

### Mirror Configuration (optional)
- `MIRROR_CAMERA_INDEX` — Camera device index (default: 0)
- `MIRROR_OUTPUT_WIDTH` — Output width before WebP encoding (default: 960)
- `MIRROR_WEBP_QUALITY` — WebP quality 0-100 (default: 60)
- `MIRROR_VISION_QUALITY` — Vision Framework quality 0=fast/1=balanced/2=accurate (default: 2)
- `MIRROR_EDGE_FEATHER` — Mask edge feather width in px (default: 15)
- `MIRROR_MORPH_SIZE` — Morphology kernel size (default: 5)

## Key Documentation

- `DESIGN.md` — System architecture and design decisions
- `SPEC.md` — Detailed API specification
- `PROJECTION_DESIGN.md` — Projector UI/UX design
- `IMPLEMENTATION_PLAN.md` — 6-phase implementation roadmap
- `IMPROVEMENT_PLAN.md` — Measurement normalization & body-type matching plan
