# Catalog & AI Recommendation System

## Catalog-First Pattern

All ~196 Shopify products are pre-loaded at startup as a compact TSV string injected into the Gemini prompt. Gemini returns `product_ids` (not search keywords), which are resolved to full product data from the in-memory cache. No runtime Shopify search needed for recommendations.

## Key Files

### `backend/catalog_service.py`
- `load_catalog()` — Fetches all products via Shopify Storefront GraphQL at startup
- `_build_compact_line()` — Converts product to TSV row: `ID\tType\tTitle\tAttributes`
- `get_catalog_tsv()` — Returns full TSV string for Gemini prompt injection (~26K chars)
- `resolve_products(product_ids)` — Maps Gemini-returned IDs to full product data (title, price, image_url, url)
- Background refresh every 30 minutes via `asyncio.create_task`

### `backend/gemini_service.py`
- Uses `gemini-3.1-pro-preview` model via `google-genai` SDK
- Pydantic structured output schema: `ClothingAnalysis`
  - `analyzed_outfit` — Description of customer's current outfit
  - `detected_style` — Style tags detected from outfit
  - `recommendations[]` — 3 recommendations, each with `title`, `category`, `reason`, `product_ids[]`
  - `box_*` — Bounding box coordinates for detected person
- Catalog TSV injected as context in the system prompt
- Body measurements (if provided) used for size matching rules

### `backend/tag_products.py`
Auto-tag + metafield enrichment via Gemini multimodal analysis.

```bash
python tag_products.py                    # Dry run (preview only)
python tag_products.py --apply            # Write to Shopify (all products)
python tag_products.py --apply --id <gid> # Single product
python tag_products.py --apply --force    # Re-tag already tagged
```

Generates: `productType`, tags, and metafields (`custom:brand`, `custom:style`, `custom:era`, `custom:features`, `custom:tagged_at`).

Uses `metafieldsSet` mutation (not `productUpdate`) for reliable metafield writes.

### `backend/normalize_measurements.py`
Extract garment measurements from product descriptions → Shopify metafield `custom:measurements` (JSON).

```bash
python normalize_measurements.py          # Dry run
python normalize_measurements.py --apply  # Write to Shopify
```

Supports:
- Tops: `肩幅49cm - 身幅63cm`
- Bottoms: `ウエスト 82cm`
- Multi-size tables: `size1(S) 56cm～`

## Data Flow

```
Startup: Shopify → catalog_service (in-memory cache + TSV)
Request: Image + tags + body → gemini_service (TSV context) → product_ids → catalog_service.resolve → full product data
```
