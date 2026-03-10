# CLAUDE.md

85-Store AI Shop Assistant — AI接客システム for a vintage clothing store. Camera → Gemini outfit analysis → Shopify inventory recommendations. Mac Studio + iPad UI + projector display.

## Commands

```bash
# Development
docker compose up --build          # Start services (backend:8000, frontend:3000)
docker compose down                # Stop

# Backend (native)
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000
MOCK_MODE=true uvicorn main:app --port 8000     # Without API keys

# Frontend
cd frontend && npm run dev         # Dev server :3000
cd frontend && npm run build       # Production build
cd frontend && npm run lint        # ESLint

# Tests
cd backend && pytest tests/ -v
```

## Architecture

```
iPad UI (Next.js :3000) ←REST/WS→ FastAPI Backend (:8000) ←→ Gemini API / Shopify APIs
                                        ↕ WebSocket
                              Projector Display (:3000/projection)
```

State Machine: `IDLE → PREFERENCE → CAMERA_ACTIVE → ANALYZING → RESULT → IDLE`

### Backend (`backend/`)
- `main.py` — FastAPI app, CORS, router registration, lifespan
- `routers/` — `analyze.py`, `customers.py`, `mirror.py`, `projection.py`
- `gemini_service.py` — Gemini API client + Pydantic structured output
- `catalog_service.py` — Product catalog cache + TSV builder
- `shopify_service.py` — Storefront API (product search)
- `customer_service.py` — Admin API (customer CRUD + metafields)
- `shopify_auth.py` — Token auto-renewal
- `mirror_service.py` — Camera capture + segmentation
- `vision_segmenter.py` — Apple Vision Framework wrapper
- `mock_service.py` — Dev mode without API keys
- `services/projection_manager.py` — WebSocket state sync + mirror frames
- `tag_products.py` — AI product tagging (`--apply`, `--id`, `--force`)
- `normalize_measurements.py` — Measurement extraction (`--apply`)
- `tests/` — pytest + pytest-asyncio (65+ tests, all external calls mocked)

### Frontend (`frontend/src/`)
- `app/page.tsx` — iPad UI (state machine orchestrator)
- `app/projection/page.tsx` — Projector display
- `hooks/` — `useCamera.ts`, `useBackendAPI.ts`, `useProjectionSync.ts`
- `components/operator/` — iPad scenes: Idle, Preference, Camera, Analyzing, Result
- `components/projection/` — Projector scenes: Background, Scenes, ResultScene
- `components/icons/` — Kare-style pixel art icons: `CatIcon.tsx`, `PixelIcons.tsx`
- `lib/projection-types.ts` — TypeScript interfaces

## Environment Variables

Set in `backend/.env` (see `.env.example`):
- `MOCK_MODE` — `true` to run without API keys
- `GEMINI_API_KEY` — Google AI Studio key
- `SHOPIFY_STORE_URL`, `SHOPIFY_STOREFRONT_ACCESS_TOKEN`, `SHOPIFY_ADMIN_API_ACCESS_TOKEN`
- `SHOPIFY_CLIENT_ID` / `SHOPIFY_CLIENT_SECRET` — For token auto-renewal
- `CORS_ORIGINS` — Allowed origins (default: `*`)

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, google-genai, httpx, OpenCV, Pydantic
- **Frontend**: Next.js 16, React 19, TypeScript 5, Tailwind CSS 4, Framer Motion
- **APIs**: Gemini 3.1 Pro Preview, Shopify Storefront/Admin GraphQL (2026-01)
- **Vision**: Apple Vision Framework (macOS) / MediaPipe (Linux fallback)
- **UI Design**: 85-store brand colors (Orange #FF6B35 × Navy #1E3A5F), Susan Kare pixel art icons

## Domain Reference (read when working on specific areas)

- [`docs/reference/catalog.md`](docs/reference/catalog.md) — Catalog-first recommendation system, tag_products, normalize_measurements
- [`docs/reference/mirror.md`](docs/reference/mirror.md) — Camera, segmentation, MIRROR_* env vars
- [`docs/reference/websocket.md`](docs/reference/websocket.md) — WebSocket state sync, single-WS pattern, projection
- [`docs/reference/shopify.md`](docs/reference/shopify.md) — Storefront/Admin APIs, token management, metafield patterns
- [`docs/reference/testing.md`](docs/reference/testing.md) — pytest conventions, mocking policy, test structure
