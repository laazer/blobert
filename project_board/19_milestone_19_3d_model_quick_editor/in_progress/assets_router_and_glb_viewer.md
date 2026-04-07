Title:
Assets router and interactive 3D GLB viewer

Description:
Implement `routers/assets.py` (`GET /api/assets` lists all GLBs and JSON files from `animated_exports/`, `exports/`, `player_exports/`, `level_exports/`; `GET /api/assets/{path}` serves them with correct MIME types — `model/gltf-binary` for `.glb`). On the frontend, build `GlbViewer.tsx` (`@react-three/fiber` Canvas + `useGLTF` + `useAnimations` from drei, OrbitControls, Grid, Environment preset="studio", React `ErrorBoundary` around the Canvas). Wire the `done` SSE event to call `refreshAssetsAndAutoSelect(output_file)` which appends `?t=<timestamp>` to bust the GLTF cache, and build `AnimationControls.tsx` (one button per clip name from the 13-clip canonical list; active clip highlighted).

Acceptance Criteria:
- `GET /api/assets` returns a JSON list of assets across all four export dirs
- `GET /api/assets/animated_exports/adhesion_bug_animated_00.glb` responds with `Content-Type: model/gltf-binary`
- `GET /api/assets/../../main.py` returns HTTP 400
- After a successful generation run, the new GLB loads automatically in the 3D canvas without a page reload
- OrbitControls let the user rotate, zoom, and pan the model
- Clicking an animation button (e.g., Walk) plays that clip on the loaded model
- A malformed GLB shows an error message inside the canvas instead of crashing the whole UI

---

## Execution Plan

### Context (scaffold status)

The full file scaffold was committed in `49ba13a`. All source files exist. The pipeline therefore proceeds from gap analysis and spec formalization rather than net-new implementation.

Files already present:
- `asset_generation/web/backend/routers/assets.py` — path-jail list endpoint + serve endpoint
- `asset_generation/web/frontend/src/components/Preview/GlbViewer.tsx` — Canvas + Model + OrbitControls + ErrorBoundary
- `asset_generation/web/frontend/src/components/Preview/AnimationControls.tsx` — 13-clip button row
- `asset_generation/web/frontend/src/store/useAppStore.ts` — `refreshAssetsAndAutoSelect` action wired to SSE `done`
- `asset_generation/web/frontend/src/components/Terminal/useStreamingOutput.ts` — SSE hook calling `refreshAssetsAndAutoSelect`

Known gap (logged as checkpoint M19-ARGLB):
- `GlbViewer.tsx` line 33: `setAvailableClips` is incorrectly aliased to `setActiveAnimation`. The Zustand store lacks a dedicated `availableClips: string[]` slice. `AnimationControls` falls back to the hardcoded 13-clip list via its prop fallback, which satisfies the AC, but the aliasing is architecturally incorrect.
- No backend pytest tests for the assets router or path-traversal guard exist.
- No frontend tests (component or integration) exist for `GlbViewer` or `AnimationControls`.

### Task Table

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Write formal spec for assets router and GLB viewer | Spec Agent | Ticket description, acceptance criteria, existing scaffold files at `asset_generation/web/backend/routers/assets.py`, `GlbViewer.tsx`, `AnimationControls.tsx`, `useAppStore.ts`, `useStreamingOutput.ts` | `project_board/specs/assets_router_and_glb_viewer_spec.md` with numbered requirements ARGLB-1..N covering: (a) assets list response schema, (b) MIME type contract per extension, (c) path-jail rejection rules (path traversal → 400, non-export-dir → 403, missing → 404), (d) GLTF cache-bust via `?t=` query param, (e) Zustand store `availableClips` slice contract, (f) `GlbViewer` Model component clip-exposure fix, (g) ErrorBoundary behavior, (h) `AnimationControls` button active state | None | Spec document exists and references each AC line item with at least one numbered requirement | Risk: spec may conflict with existing scaffold decisions; Assumption: scaffold is authoritative for structure, spec locks behavior contracts |
| 2 | Write backend pytest tests for assets router (red before gap-fill) | Test Designer Agent | Spec from Task 1; existing `asset_generation/web/backend/routers/assets.py`, `core/config.py`, `requirements.txt` | `asset_generation/web/backend/tests/test_assets_router.py` using `httpx.AsyncClient` + `ASGITransport(app=app)`; tests must cover: list endpoint returns `{"assets": [...]}` with correct keys, `.glb` file served with `Content-Type: model/gltf-binary`, `.json` file served with `application/json`, `../../main.py` traversal returns 400, path to non-export-dir returns 403, missing file returns 404 | Task 1 | Tests exist and pytest reports all as failing before any implementation change (proves the tests are not trivially passing vacuously) | Risk: `httpx` may not be in requirements.txt for backend; Assumption: add `httpx` and `pytest-asyncio` to `asset_generation/web/backend/requirements.txt` if absent |
| 3 | Write adversarial backend pytest tests (test breaker) | Test Breaker Agent | Spec from Task 1; tests from Task 2 | Adversarial extensions appended to `asset_generation/web/backend/tests/test_assets_router.py`: null-byte in path, URL-encoded traversal (`%2e%2e`), deeply nested traversal, empty path, path with trailing slash, file in export dir with unexpected extension served with octet-stream fallback, list when no export dirs exist returns empty list | Task 2 | Adversarial tests run and fail where spec requires rejection; at least 4 distinct adversarial cases added beyond Task 2 | Assumption: FastAPI path parameter decoding normalizes `%2e%2e` to `..` before the Python path guard sees it; if not, the spec must note this and the adversarial test documents the behavior |
| 4 | Fix Zustand store `availableClips` slice and `GlbViewer` clip-exposure | Implementation Backend Agent | Spec from Task 1; `asset_generation/web/frontend/src/store/useAppStore.ts`, `asset_generation/web/frontend/src/components/Preview/GlbViewer.tsx` | (a) `useAppStore.ts`: add `availableClips: string[]` state, `setAvailableClips(names: string[]) => void` action. (b) `GlbViewer.tsx` `Model` component: replace incorrect `setActiveAnimation` alias with `setAvailableClips`; call `setAvailableClips(names)` when model loads; auto-select first clip via `setActiveAnimation` only if `activeAnimation` is null. (c) `AnimationControls.tsx`: read `availableClips` from store instead of relying on a prop fallback | Task 1 | `setActiveAnimation` is no longer aliased as `setAvailableClips`; `useAppStore` has `availableClips` field; `AnimationControls` renders from store `availableClips` | Risk: changing store shape may break `CommandPanel` or `Terminal` if they use `setActiveAnimation` indirectly; scan all consumers before changing |
| 5 | Verify backend path-jail behavior is complete (no gap-fill needed or patch if needed) | Implementation Backend Agent | Spec from Task 1; `asset_generation/web/backend/routers/assets.py`; tests from Tasks 2–3 | Either: (a) confirmation that existing `assets.py` passes all tests, or (b) minimal patch to `assets.py` to make all tests pass. No rewrite; only targeted fixes. Run `cd asset_generation/web/backend && python -m pytest tests/test_assets_router.py -v` and record output | Task 3, Task 1 | All backend pytest tests in `test_assets_router.py` pass; `pytest` exits 0 | Risk: `httpx`/`pytest-asyncio` install may be needed; Assumption: `python -m pytest` resolves from within the backend directory using a local or system environment |
| 6 | Static QA and AC gatekeeper | Implementation Backend Agent (or AC Gatekeeper) | All prior task outputs; ticket acceptance criteria | (a) Run all backend tests and confirm exit 0. (b) Manually trace each AC line item against spec requirements and test IDs. (c) Update ticket WORKFLOW STATE: Stage → COMPLETE (or BLOCKED with precise issue). (d) Move ticket file to `project_board/19_milestone_19_3d_model_quick_editor/done/` via `git mv`. (e) Commit all changes with message `feat(M19-ARGLB): assets router tests, GLB viewer clip-exposure fix, AC gatekeeper` | Tasks 4, 5 | All 7 acceptance criteria have a verifiable test or evidence entry; `pytest tests/test_assets_router.py` exits 0; ticket in `done/` | Risk: frontend acceptance criteria (OrbitControls, animation playback, ErrorBoundary) cannot be automatically tested in this pipeline without a browser; those ACs should be marked as "manual verification required" in the gatekeeper notes |

### Notes on frontend AC coverage

AC items 4–7 (auto-load after generation, OrbitControls interaction, animation playback, ErrorBoundary display) are not unit-testable without a browser rendering environment. The pipeline does not include Playwright or Vitest component tests in this scope. The Spec Agent should note these as "manual verification" ACs in the spec and the AC Gatekeeper must explicitly call them out. The store logic for `refreshAssetsAndAutoSelect` (Task 4 fix) provides the closest automated coverage for AC-4.

---

## WORKFLOW STATE

- **Stage:** IMPLEMENTATION_ENGINE_INTEGRATION
- **Revision:** 5
- **Last Updated By:** Test Breaker Agent
- **Next Responsible Agent:** Engine Integration Agent
- **Status:** Proceed
- **Validation Status:** 33/38 tests pass; 5 red tests document implementation gaps
- **Blocking Issues:** None

## NEXT ACTION

### Next Responsible Agent
Engine Integration Agent

### Required Input Schema
```json
{
  "ticket_path": "project_board/19_milestone_19_3d_model_quick_editor/in_progress/assets_router_and_glb_viewer.md",
  "spec_path": "project_board/specs/assets_router_and_glb_viewer_spec.md",
  "test_file": "asset_generation/web/backend/tests/test_assets_router.py",
  "backend_router": "asset_generation/web/backend/routers/assets.py"
}
```

### Status
Proceed

### Reason
Adversarial test suite extended to 38 tests (15 new). 33 pass / 5 red. Red tests document 3 confirmed implementation gaps requiring fixes in `assets.py`:

1. **Null-byte unhandled exception** (`test_null_byte_in_path_should_return_400_not_raise`): `pathlib.Path.resolve()` raises `ValueError` for embedded null bytes, but the `try/except ValueError` in `serve_asset` only wraps `relative_to()` — not `resolve()`. Fix: extend the try block to cover `resolved = (python_root / asset_path).resolve()`.

2. **Directory path returns 500 not 404** (`test_directory_path_returns_non_200`, `test_directory_as_path_returns_404_strict`): `FileResponse` raises `RuntimeError` when called on a directory. Fix: add `if not resolved.is_file(): raise HTTPException(status_code=404, detail="Asset not found")` before constructing `FileResponse`.

3. **Literal `..` traversal tests** (`test_double_dot_traversal_literal_returns_non_200`, `test_single_dot_dot_traversal_literal_returns_non_200`): httpx normalizes literal `..` in URLs before sending; path guard never fires. These tests are pre-existing documentation tests that require either (a) server-side raw URL inspection or (b) accepting that percent-encoded `%2e%2e` tests cover the security requirement. See `test_url_encoded_traversal_returns_400` which passes and is the canonical security test.

Adversarial coverage added:
- Null-byte injection (security gap confirmed)
- Double-encoded traversal `%252e%252e` → 403 (passes — correctly blocked at layer 2)
- Directory-as-path strict 404 assertion (confirms implementation gap)
- Within-jail traversal via encoded dots (passes — documents resolve() semantics)
- Dotfile `.glb` excluded by Python 3.9 suffix behavior (passes — documents spec inaccuracy)
- Export dirs with no .glb/.json files → empty list (passes)
- 50-file stress test (passes — no truncation)
- Sort invariant test (passes)
- Multi-dir sort vs canonical order conflict test (passes)
- Uppercase extension `.GLB`/`.JSON` → octet-stream (passes)
- Double extension `.tar.gz` → octet-stream (passes)
- GLB content-type has no charset (passes)
