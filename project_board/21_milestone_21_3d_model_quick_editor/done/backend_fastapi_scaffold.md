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

---

## Execution Plan

Scaffold implementation is already present on disk, so this resume run performed verification-first closure:

1. Validate the scaffold wiring exists (`main.py`, `core/config.py`, `core/path_guard.py`, `routers/files.py`, `requirements.txt`).
2. Execute live API checks against `main.app` with `fastapi.testclient.TestClient`.
3. Smoke-test `uvicorn main:app --reload` startup under a bounded timeout.
4. Record AC evidence and close the ticket through gatekeeper state.

---

## WORKFLOW STATE

- **Stage:** COMPLETE
- **Revision:** 1
- **Last Updated By:** Acceptance Criteria Gatekeeper Agent
- **Next Responsible Agent:** Human
- **Status:** Proceed
- **Validation Status:**
  - AC1 (`GET /api/files` tree): verified via `uv run python` TestClient probe, response `200` with JSON key `tree`.
  - AC2 (`GET /api/files/<rel-path>`): verified using discovered path `animations/__init__.py`; response `200` with `{path, content}`.
  - AC3 (`PUT /api/files/<rel-path>` atomic save): verified with write then immediate revert on same file; both responses `200` and `{saved: true}`.
  - AC4 (traversal reject): encoded traversal probes (`/api/files/%2e%2e/%2e%2e/main.py`, variants) return `400` with `Path outside src/ directory`.
  - AC5 (non-`.py` reject): `PUT /api/files/some_file.txt` returns `400` with `Only .py files are allowed`.
  - AC6 (`uvicorn main:app --reload` startup): `timeout 8 uv run uvicorn main:app --reload --host 127.0.0.1 --port 8011` shows successful startup and clean shutdown on timeout.
- **Blocking Issues:** None

## NEXT ACTION

### Next Responsible Agent
Human

### Required Input Schema
Ticket complete. Optional follow-up: add dedicated backend pytest coverage for `routers/files.py` to preserve these AC checks in CI.

### Status
Proceed

### Reason
All acceptance criteria have direct runtime evidence from this resume run; no additional implementation work is required for the scaffold ticket.
