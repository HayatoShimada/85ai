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
- **`main.py`** — FastAPI app init, CORS, router registration, health check
- **`routers/`** — API endpoints: `analyze.py`, `customers.py`, `mirror.py`, `projection.py`
- **`gemini_service.py`** — Gemini API client with Pydantic structured output (`ClothingAnalysis` schema)
- **`shopify_service.py`** — Shopify Storefront API (product search via GraphQL)
- **`customer_service.py`** — Shopify Admin API (customer CRUD + metafields for style preferences)
- **`shopify_auth.py`** — `ShopifyTokenManager` singleton (Client Credentials Grant, auto-renewal)
- **`mirror_service.py`** — Camera capture + person segmentation orchestration
- **`vision_segmenter.py`** — Apple Vision Framework wrapper (macOS only)
- **`mock_service.py`** — Hardcoded responses for development without API keys (`MOCK_MODE=true`)
- **`services/projection_manager.py`** — State sync broadcaster between iPad and Projector
- **`tag_products.py`** — Utility script to auto-tag Shopify products using Gemini + Admin API
- **`tests/`** — pytest + pytest-asyncio, all external calls are mocked

### Frontend Structure (`frontend/src/`)
- **`app/page.tsx`** — Main iPad UI (state machine, camera, image upload, API calls, voice TTS)
- **`app/projection/page.tsx`** — Projector display (animations, mirror overlay, QR codes)
- **`lib/projection-types.ts`** — TypeScript interfaces for app state
- **`components/QRCode.tsx`** — QR code generator component

### Key Patterns
- **Async-first**: `async`/`await` + `httpx.AsyncClient` throughout backend; `asyncio.gather()` for parallel Shopify searches
- **Service-oriented**: Each external integration is a separate module, easily mockable
- **Singletons**: `ShopifyTokenManager`, `MirrorSegmenter`, `ProjectionManager`
- **No database**: All persistence via Shopify APIs (customer metafields for style preferences)

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
- **APIs**: Google Gemini 3.1 Pro, Shopify Storefront/Admin GraphQL (2026-01)
- **Vision**: Apple Vision Framework (macOS) / MediaPipe (Linux fallback)

## Key Documentation

- `DESIGN.md` — System architecture and design decisions
- `SPEC.md` — Detailed API specification
- `PROJECTION_DESIGN.md` — Projector UI/UX design
- `IMPLEMENTATION_PLAN.md` — 6-phase implementation roadmap
