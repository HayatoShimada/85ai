# Testing Conventions

## Stack

- **pytest** + **pytest-asyncio** for async test support
- 12 test files, 65+ tests in `backend/tests/`

## Commands

```bash
cd backend
pytest tests/ -v                          # All tests
pytest tests/test_api.py -v               # Single test file
pytest tests/test_api.py::test_name -v    # Single test
pytest tests/ --cov=. --cov-report=html   # With coverage
```

In Docker:
```bash
docker compose exec backend pytest tests/ -v
```

## Mocking Policy

**All external API calls are mocked.** No test should make real HTTP requests to:
- Shopify Storefront/Admin APIs
- Google Gemini API
- Any external service

Use `unittest.mock.patch` or `pytest-mock` fixtures. Mock at the service boundary (e.g., mock `httpx.AsyncClient` responses or service functions).

## Test Structure

```
backend/tests/
├── conftest.py          # Shared fixtures (AsyncClient, mock services)
├── test_api.py          # REST endpoint tests
├── test_analyze.py      # /api/analyze endpoint
├── test_catalog.py      # Catalog service
├── test_customers.py    # Customer API
├── test_gemini.py       # Gemini service
├── test_mirror.py       # Mirror/camera service
├── test_mock.py         # Mock mode
├── test_projection.py   # Projection WebSocket
├── test_shopify.py      # Shopify service
├── test_shopify_auth.py # Token manager
├── test_tag_products.py # Product tagging script
└── test_normalize.py    # Measurement normalization
```

## Key Patterns

- Use `httpx.ASGITransport` + `AsyncClient` for testing FastAPI endpoints
- `conftest.py` provides the `client` fixture with `app` mounted
- Async tests use `@pytest.mark.asyncio`
- Mock catalog data in tests that depend on product catalog
