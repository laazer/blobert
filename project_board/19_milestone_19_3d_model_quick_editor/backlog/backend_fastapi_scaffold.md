Title:
Backend FastAPI scaffold — file CRUD, config, path guard

Description:
Stand up the FastAPI backend at `asset_generation/web/backend/`. Wire together `core/config.py` (Settings with `python_root`), `core/path_guard.py` (resolve/reject client paths relative to `src/`, `.py`-only jail), and `routers/files.py` (recursive file tree, read, atomic write). Register all routers in `main.py` with CORS middleware. Create `requirements.txt` (fastapi, uvicorn, pydantic-settings, python-multipart, sse-starlette).

Acceptance Criteria:
- `GET /api/files` returns a JSON tree of all `.py` files under `asset_generation/python/src/`
- `GET /api/files/<rel-path>` returns `{ "path": ..., "content": ... }` for a valid `.py` file
- `PUT /api/files/<rel-path>` with `{ "content": "..." }` writes atomically (tmp→rename) and returns `{ "saved": true }`
- `PUT /api/files/../../main.py` returns HTTP 400 (path traversal rejected)
- `PUT /api/files/some_file.txt` returns HTTP 400 (non-.py rejected)
- `uvicorn main:app --reload` starts without errors from `backend/`
