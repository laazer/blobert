# API Contract Index

This index points to the active backend API contract surfaces in code.

## App entry

- `asset_generation/web/backend/main.py`
  - FastAPI app creation
  - CORS policy wiring
  - Router inclusion order
  - Health endpoint (`/api/health`)

## Router modules

- `asset_generation/web/backend/routers/files.py`
- `asset_generation/web/backend/routers/run.py`
- `asset_generation/web/backend/routers/assets.py`
- `asset_generation/web/backend/routers/meta.py`
- `asset_generation/web/backend/routers/registry.py`

## Registry integration path

- Router: `asset_generation/web/backend/routers/registry.py`
- Service module: `asset_generation/python/src/model_registry/service.py`

## Contract maintenance rule

When endpoint behavior changes, update this index if:

- a router is added/removed/renamed
- integration path changes (for example, registry service import path)
- health or global middleware entry points change
