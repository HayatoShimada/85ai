# Shopify API Integration

## API Versions & Auth

- GraphQL API version: `2026-01`
- Two API surfaces: **Storefront API** (public, product search) and **Admin API** (private, customer management + metafields)

## Key Files

### `backend/shopify_service.py` — Storefront API
- Product search via GraphQL
- Uses `SHOPIFY_STOREFRONT_ACCESS_TOKEN` (public token)
- Async via `httpx.AsyncClient`

### `backend/customer_service.py` — Admin API
- Customer CRUD operations
- Metafields for style preferences (`custom:style_preferences`) and body measurements (`custom:body_measurements`)
- Uses `ShopifyTokenManager` for authenticated requests

### `backend/shopify_auth.py` — Token Management
- `ShopifyTokenManager` singleton
- Client Credentials Grant flow
- Auto-renewal with 24h expiry, `asyncio.Lock` for thread safety
- Falls back to `SHOPIFY_ADMIN_API_ACCESS_TOKEN` if client credentials not configured

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SHOPIFY_STORE_URL` | e.g. `store.myshopify.com` |
| `SHOPIFY_STOREFRONT_ACCESS_TOKEN` | Public Storefront API token |
| `SHOPIFY_ADMIN_API_ACCESS_TOKEN` | Admin API token (`shpat_...`) |
| `SHOPIFY_CLIENT_ID` | For Client Credentials Grant |
| `SHOPIFY_CLIENT_SECRET` | For Client Credentials Grant |

## Metafield Patterns

### Writing Metafields
Use `metafieldsSet` mutation (not `productUpdate` with inline metafields — that doesn't work reliably):

```graphql
mutation metafieldsSet($metafields: [MetafieldsSetInput!]!) {
  metafieldsSet(metafields: $metafields) {
    metafields { key namespace value }
    userErrors { field message }
  }
}
```

Each metafield needs `ownerId` (product/customer GID), `namespace`, `key`, `type`, `value`.

### Custom Metafield Namespaces
- `custom:measurements` — Garment measurements (JSON)
- `custom:brand` / `custom:style` / `custom:era` / `custom:features` — AI-generated product tags
- `custom:tagged_at` — Timestamp of last AI tagging
- `custom:style_preferences` — Customer style preferences (JSON)
- `custom:body_measurements` — Customer body measurements (JSON)
