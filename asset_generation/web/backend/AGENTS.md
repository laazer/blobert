# WEB BACKEND - FASTAPI KNOWLEDGE BASE

**Generated:** 2026-04-23  
**App:** Blobert Asset Editor API  
**Port:** 8000  
**Purpose:** FastAPI backend for web-based asset editor; imports model_registry from Python project

## OVERVIEW

FastAPI backend for blobert's web asset editor. Route-first structure with clear separation: main.py bootstrap, routers/ endpoints, core/ config, services/ business logic. Imports model_registry from asset_generation/python/src/model_registry/.

## STRUCTURE

```
asset_generation/web/backend/
├── main.py                   # FastAPI app bootstrap; router wiring
├── routers/                  # API endpoint routes
│   ├── __init__.py
│   └── registry.py           # Model registry endpoints (GET, POST, DELETE)
├── core/                     # Core configuration
│   ├── __init__.py
│   └── config.py             # App settings, CORS for frontend port 5173
├── services/                 # Business logic layer
│   └── __init__.py
├── models/                   # Pydantic request/response models
│   └── __init__.py
└── start.sh                  # Startup script (uvicorn entry point)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| App bootstrap | `main.py` | FastAPI app creation; imports routers, registers Python runtime bridge |
| Registry endpoints | `routers/registry.py` | Model registry CRUD; path validation, manifest operations |
| Config/CORS | `core/config.py` | Port 8000; CORS allows frontend port 5173 |
| Python import bridge | `main.py::bootstrap_python_runtime()` | Imports model_registry from asset_generation/python/src/ |
| Request models | `models/*.py` | Pydantic schemas for API payloads |

## CODE MAP

| Symbol | Type | Location | Refs | Role |
|--------|------|----------|------|------|
| `FastAPI` app | instance | `main.py` | Router wiring, Python runtime bootstrap | Main FastAPI application instance |
| `/api/registry` router | module | `routers/registry.py` | Model registry endpoints | CRUD operations for enemy/player models |
| `bootstrap_python_runtime()` | function | `main.py` | Python import bridge | Imports model_registry from Python project |

## CONVENTIONS

- **Route-first structure**: Endpoints defined in routers/ before service layer; clear API surface
- **Pydantic models**: All request/response bodies use Pydantic for validation
- **CORS configured**: Allows frontend port 5173; backend runs on 8000
- **Python import bridge**: `bootstrap_python_runtime()` function imports model_registry from asset_generation/python/src/

## ANTI-PATTERNS (THIS MODULE)

| Pattern | Why Forbidden | Evidence |
|---------|---------------|----------|
| Logic in routers | Business logic should be in services/; keep routes thin | Refactor: extract service calls into services/*.py modules |
| Bare `dict` in payloads | Blocks type safety; use Pydantic models instead | asset_generation/** policy enforced |

## COMMANDS

```bash
# Start backend dev server
cd asset_generation/web/backend && uvicorn main:app --reload --port 8000

# Full editor stack (backend + frontend)
task editor

# Equivalent start script
bash asset_generation/web/start.sh
```

## API contract tests (M902-26)

Contract tests live under `asset_generation/python/tests/api/`. They assert HTTP **shape** (status, JSON schema, SSE/binary headers) against the **live** FastAPI OpenAPI document (`app.openapi()` via ASGI client). They complement unit tests in `tests/web/` and `backend/tests/` (behavior, disk writes, spawn logic).

### Schema authority

| Source | Path / URL | Role |
|--------|------------|------|
| **Live (normative)** | `app.openapi()` at pytest session start | All `jsonschema` validation |
| **Committed cache** | `asset_generation/web/frontend/scripts/fixtures/openapi.cached.json` | Drift detection only (M902-24); regen with frontend `npm run sync-api-types` |
| **Running server (optional)** | `http://127.0.0.1:8000/openapi.json` | Human/debug reference; not required in CI |

Harness: `asset_generation/python/tests/api/openapi_contract.py`. Shared fixtures: `conftest.py`. Per-router modules: `test_*_contract.py`, `test_api_contract_adversarial.py`.

Spec: `project_board/specs/902_26_api_contract_testing_spec.md`. Related: M902-24 (OpenAPI → TypeScript), M902-25 (Pydantic `response_model` pilots).

### When you add or change an endpoint

1. Implement the route in `routers/` (prefer Pydantic `response_model` / request models so OpenAPI is non-empty).
2. Regenerate the frontend cache: `cd asset_generation/web/frontend && npm run sync-api-types`.
3. Add contract tests under `asset_generation/python/tests/api/`:
   - At least one **happy-path** test (expected status + schema validation).
   - At least one **error-path** test (400/404/422/etc. + `detail` or `HTTPValidationError` per spec).
   - Use `contract.validate_response(...)` from the session fixture; do not hand-write JSON Schemas.
4. Run the contract suite:

```bash
cd asset_generation/python && uv run pytest tests/api/ -q
```

5. Run full Python CI locally if needed: `bash .lefthook/scripts/py-tests.sh` (includes `tests/api/` via `pytest tests/`).

Tier **A** routes (pilot GETs + strict OpenAPI) enforce full schema + `additionalProperties: false` when declared. Tier **B** legacy `JSONResponse` routes use status + JSON anchors until models land.

## NOTES

- **Port**: 8000; CORS configured for frontend port 5173
- **Python import bridge**: `bootstrap_python_runtime()` imports model_registry from asset_generation/python/src/model_registry/
- **Frontend proxy**: Vite dev server proxies /api/* requests to backend
- **MCP integration**: Asset pipeline MCP (stdio) proxies HTTP API on :8000; see asset_generation/mcp/README.md
