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

## NOTES

- **Port**: 8000; CORS configured for frontend port 5173
- **Python import bridge**: `bootstrap_python_runtime()` imports model_registry from asset_generation/python/src/model_registry/
- **Frontend proxy**: Vite dev server proxies /api/* requests to backend
- **MCP integration**: Asset pipeline MCP (stdio) proxies HTTP API on :8000; see asset_generation/mcp/README.md
