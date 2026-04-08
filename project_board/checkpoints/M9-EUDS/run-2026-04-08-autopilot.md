# M9-EUDS — 04_editor_ui_draft_status_for_exports

**Run:** 2026-04-08 autopilot (single ticket)

## Summary

Implemented MRVC-backed model registry I/O in `src/model_registry/service.py`, FastAPI `routers/registry.py` (canonical python tree on import path; manifest path from `settings.python_root`), React **Registry** tab with draft / in-pool toggles, and ASGI tests under `asset_generation/python/tests/web/test_registry_api.py` (dev extra: fastapi, httpx, pydantic-settings, sse-starlette).

## Checkpoint

**Assumption made:** Enemy registry keys match `ANIMATED_SLUGS` / meta API slugs (`spitter`, not `acid_spitter`) for MRVC-7 default migration.

**Confidence:** High
