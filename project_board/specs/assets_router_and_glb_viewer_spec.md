# Spec: Assets Router and Interactive 3D GLB Viewer

**Ticket:** `project_board/19_milestone_19_3d_model_quick_editor/in_progress/assets_router_and_glb_viewer.md`
**Spec ID prefix:** ARGLB
**Stage:** SPECIFICATION → TEST_DESIGN
**Last Updated By:** Spec Agent
**Date:** 2026-04-07

---

## Overview

This spec covers two systems:

1. **Backend** — `GET /api/assets` (list) and `GET /api/assets/{path}` (serve) in `asset_generation/web/backend/routers/assets.py`.
2. **Frontend** — The Zustand store `availableClips` slice, `GlbViewer.tsx` clip-exposure fix, `AnimationControls.tsx` active-state rendering, and `ErrorBoundary` behavior.

Source files covered:
- `asset_generation/web/backend/routers/assets.py`
- `asset_generation/web/backend/core/config.py`
- `asset_generation/web/backend/core/path_guard.py`
- `asset_generation/web/frontend/src/store/useAppStore.ts`
- `asset_generation/web/frontend/src/components/Preview/GlbViewer.tsx`
- `asset_generation/web/frontend/src/components/Preview/AnimationControls.tsx`
- `asset_generation/web/frontend/src/components/Terminal/useStreamingOutput.ts`

---

## Requirement ARGLB-1 — Assets List Endpoint Response Schema

### 1. Spec Summary

- **Description:** `GET /api/assets` returns a JSON object with a single key `"assets"` whose value is an array of asset descriptor objects. Each descriptor has exactly four keys: `path`, `name`, `dir`, and `size`. The endpoint scans four canonical export directories under `settings.python_root`: `animated_exports/`, `exports/`, `player_exports/`, and `level_exports/`. Only files with extensions `.glb` or `.json` are included. Directories that do not exist on disk are silently skipped. Files within each directory are sorted by name (ascending, case-sensitive, as returned by `sorted(dir.iterdir())`).
- **Constraints:**
  - Only files at the top level of each export directory are included (no recursive traversal).
  - Subdirectories within an export directory are excluded.
  - The `path` field is the URL-relative path used to construct a serve request: `"<dir>/<filename>"`.
  - The `name` field is the bare filename including extension.
  - The `dir` field is the export directory name (one of the four listed above).
  - The `size` field is the file size in bytes as returned by `stat().st_size` (integer).
- **Assumptions:** `settings.python_root` is resolved at application startup via `core/config.py`. The export directories are flat (no nesting is expected by this spec; nested files' behavior is undefined).
- **Scope:** `GET /api/assets` (no path segment).

### 2. Acceptance Criteria

- **ARGLB-1.1:** A request to `GET /api/assets` returns HTTP 200 with `Content-Type: application/json`.
- **ARGLB-1.2:** The response body is a JSON object `{"assets": [...]}`.
- **ARGLB-1.3:** Each entry in the `"assets"` array contains exactly the keys `path`, `name`, `dir`, `size`. No extra keys are present.
- **ARGLB-1.4:** Given a `.glb` file named `adhesion_bug_animated_00.glb` in `animated_exports/`, the corresponding entry is `{"path": "animated_exports/adhesion_bug_animated_00.glb", "name": "adhesion_bug_animated_00.glb", "dir": "animated_exports", "size": <integer>}`.
- **ARGLB-1.5:** A `.json` file in `animated_exports/` is included in the list; a `.txt` file in the same directory is not included.
- **ARGLB-1.6:** When all four export directories are absent from disk, `GET /api/assets` returns HTTP 200 with body `{"assets": []}`.
- **ARGLB-1.7:** When one export directory exists and two others do not, only files from the existing directory appear in the response.
- **ARGLB-1.8:** Files from `animated_exports/` appear before files from `exports/`, which appear before files from `player_exports/`, which appear before files from `level_exports/` — reflecting the canonical directory order in `_EXPORT_DIRS`.

### 3. Risk & Ambiguity Analysis

- **Risk:** If `settings.python_root` points to a non-existent root, all directories are skipped and the response is `{"assets": []}` — this is correct behavior per ARGLB-1.6 and should be tested as a degenerate case.
- **Edge case:** A file named `.glb` (empty stem, only extension) — `iterdir()` will return it and `suffix` will be `.glb`; it will appear in the list. This is acceptable and not blocked.
- **Edge case:** A symlink file in an export directory pointing to a file outside the python_root — the list endpoint does not resolve symlinks; it uses `f.suffix` and `f.stat()` on the symlink itself. Symlink targets are not validated by the list endpoint. This is acceptable since serve applies path-jail validation.

### 4. Clarifying Questions

None. Scaffold is authoritative.

---

## Requirement ARGLB-2 — MIME Type Contract

### 1. Spec Summary

- **Description:** `GET /api/assets/{path}` serves files with a `Content-Type` header determined by the file's extension. The mapping is:
  - `.glb` → `model/gltf-binary`
  - `.json` → `application/json`
  - Any other extension → `application/octet-stream`
- **Constraints:** The MIME type is determined solely by the resolved file's suffix (lowercase extension including the dot). Case sensitivity of the extension follows Python's `Path.suffix` behavior (case-sensitive on all platforms). Files with extensions not in `{".glb", ".json"}` that pass all path-jail checks are served with `application/octet-stream`.
- **Assumptions:** No assumption is made that only `.glb` and `.json` files will be requested via the serve endpoint. The list endpoint filters to `.glb`/`.json`, but the serve endpoint is a general pass-through within the path jail.
- **Scope:** `GET /api/assets/{path}` only.

### 2. Acceptance Criteria

- **ARGLB-2.1:** `GET /api/assets/animated_exports/adhesion_bug_animated_00.glb` responds with `Content-Type: model/gltf-binary` when the file exists.
- **ARGLB-2.2:** `GET /api/assets/animated_exports/some_config.json` responds with `Content-Type: application/json` when the file exists.
- **ARGLB-2.3:** A file with an extension not in `{".glb", ".json"}` (e.g., `.bin`) that exists inside an export directory and passes path-jail checks is served with `Content-Type: application/octet-stream`.
- **ARGLB-2.4:** The `Content-Type` header value is exact: `model/gltf-binary` (not `model/gltf+binary`, not `application/gltf-binary`).

### 3. Risk & Ambiguity Analysis

- **Risk:** MIME type `model/gltf-binary` is non-standard in some older MIME databases. The implementation explicitly sets this via the `_MIME` dict rather than inferring from the system MIME database — this is correct and must be preserved.
- **Edge case:** A file named `model.GLB` (uppercase extension) — `Path.suffix` returns `.GLB`, which does not match `.glb` in the `_MIME` dict, so `application/octet-stream` is returned. This is intentional and must be documented in tests.

### 4. Clarifying Questions

None.

---

## Requirement ARGLB-3 — Path-Jail Rejection Rules

### 1. Spec Summary

- **Description:** `GET /api/assets/{path}` applies a three-layer path validation before serving any file. The validation layers, in order, are:

  1. **Traversal jail (HTTP 400):** The resolved absolute path of `python_root / asset_path` must be a subpath of `python_root.resolve()`. If `resolved.relative_to(python_root)` raises `ValueError`, the request is rejected with HTTP 400. This catches `..` traversal, null-byte injection (if Python Path rejects it), and any other path that escapes the root.

  2. **Export-directory allowlist (HTTP 403):** The first path component of the resolved relative path (i.e., `resolved.relative_to(python_root).parts[0]`) must be one of: `animated_exports`, `exports`, `player_exports`, `level_exports`. If it is not — including if `parts` is empty — the request is rejected with HTTP 403.

  3. **File existence (HTTP 404):** If the resolved path does not exist on disk, the request is rejected with HTTP 404 with detail `"Asset not found"`.

- **Constraints:**
  - Validation layers execute in the order: 400 → 403 → 404. A request that fails the traversal check never reaches the export-dir check. A request that fails the export-dir check never reaches the existence check.
  - FastAPI decodes percent-encoded path segments before the router handler receives `asset_path`. A request for `../../main.py` URL-encoded as `%2e%2e%2fmain.py` is decoded to `../../main.py` by FastAPI before the guard sees it. The Python path-resolution guard then catches it at layer 1.
  - The resolved path is computed as `(python_root / asset_path).resolve()` where `python_root = settings.python_root.resolve()`.
- **Assumptions:** `settings.python_root` is a real absolute directory on disk. Symbolic links are not specially handled — `Path.resolve()` follows symlinks, so a symlink within the export dir pointing outside python_root will be rejected at layer 1.
- **Scope:** `GET /api/assets/{path}` only.

### 2. Acceptance Criteria

- **ARGLB-3.1:** `GET /api/assets/../../main.py` returns HTTP 400 with a non-empty `detail` string.
- **ARGLB-3.2:** `GET /api/assets/../main.py` returns HTTP 400 (traversal one level up from python_root still escapes).
- **ARGLB-3.3:** `GET /api/assets/some_other_dir/file.glb` (where `some_other_dir` is not in the export-dir allowlist) returns HTTP 403, even if the file exists at that path on disk.
- **ARGLB-3.4:** `GET /api/assets/animated_exports/nonexistent_file.glb` returns HTTP 404.
- **ARGLB-3.5:** `GET /api/assets/animated_exports/` (trailing slash, no filename) — if resolved path is a directory and exists, returns HTTP 404 (the path resolves to a directory, which `resolved.exists()` returns True for, but serving a directory via `FileResponse` raises an error). This is an edge case: the spec requires that the 404 or 500 must not reveal internal server paths. Preferred behavior is HTTP 404 — implementations may assert this or document as manual-verify.
- **ARGLB-3.6:** A URL-encoded traversal `GET /api/assets/%2e%2e%2f%2e%2e%2fmain.py` returns HTTP 400, because FastAPI decodes `%2e` to `.` before the handler receives `asset_path`.
- **ARGLB-3.7:** A deeply nested traversal such as `GET /api/assets/animated_exports/../../../main.py` returns HTTP 400.
- **ARGLB-3.8:** `GET /api/assets/` (empty path segment) returns HTTP 400 or HTTP 403. The spec does not mandate which, but the response must be 4xx and must not be 200.

### 3. Risk & Ambiguity Analysis

- **Risk:** Null-byte injection in URLs (e.g., `animated_exports/file.glb%00.txt`) — Python's `pathlib.Path` raises `ValueError` for embedded null bytes in path strings, which the `relative_to` call will propagate and the `except ValueError` block will catch as HTTP 400. However, if FastAPI strips the null byte during URL decoding before the handler sees it, the null byte test may behave differently. The Test Breaker agent must explicitly test this and document observed behavior.
- **Risk:** Double-encoded traversal (`%252e%252e`) — FastAPI decodes percent-encoding once. `%252e` decodes to `%2e` (literal), not `.`. The path guard will receive `%2e%2e` as a literal string; `Path("%2e%2e")` does not resolve as `..`. This means double-encoded traversal reaches the guard but the path resolves within `python_root` (to a path component named literally `%2e%2e`). The result at layer 2 is HTTP 403 (not in export dirs) or HTTP 404 (if by chance `%2e%2e` is a dir in export list). This edge case must be documented by Test Breaker.
- **Edge case:** Empty `asset_path` string — FastAPI's path parameter with `:path` converter may route an empty suffix to the list endpoint instead. If it does reach the serve handler, `parts` will be empty and layer 2 returns HTTP 403.

### 4. Clarifying Questions

None. Scaffold behavior is authoritative; the spec is locking it.

---

## Requirement ARGLB-4 — GLTF Cache-Bust via `?t=` Query Parameter

### 1. Spec Summary

- **Description:** When a generation run completes with a `done` SSE event containing a non-null `output_file`, the frontend action `refreshAssetsAndAutoSelect(outputFile)` constructs the active GLB URL as `/api/assets/<match.path>?t=<timestamp>` where `<timestamp>` is `Date.now()` (milliseconds since epoch, integer). This URL is set as `activeGlbUrl` in the Zustand store. The `?t=` suffix forces `useGLTF` (drei) to treat the URL as a new resource, bypassing any browser or drei cache for the previous URL.
- **Constraints:**
  - The timestamp must be appended as a query parameter named `t`.
  - `Date.now()` is called at the moment `refreshAssetsAndAutoSelect` executes after the SSE `done` event.
  - The backend `GET /api/assets/{path}` endpoint ignores query parameters — FastAPI strips them before route matching, and the path-jail guard only inspects `asset_path` (the path segment). Query parameters do not affect backend validation.
  - `refreshAssetsAndAutoSelect` also sets `activeAnimation` to `null` (not `"Idle"`) on new model load, so that `GlbViewer.Model` can auto-select the first real clip from the model after it loads. (See ARGLB-5 for `availableClips` and ARGLB-6 for the clip-selection logic.)
- **Assumptions:** The scaffold currently sets `s.activeAnimation = "Idle"` in `refreshAssetsAndAutoSelect`. This is incorrect because "Idle" is not guaranteed to exist in all GLBs. The Implementation agent must change this to `null`.
- **Scope:** `useAppStore.ts` — `refreshAssetsAndAutoSelect` action; `useStreamingOutput.ts` — SSE `done` handler.

### 2. Acceptance Criteria

- **ARGLB-4.1:** After a `done` SSE event with `output_file: "animated_exports/foo.glb"`, `useAppStore.getState().activeGlbUrl` equals `/api/assets/animated_exports/foo.glb?t=<number>` where `<number>` is a positive integer.
- **ARGLB-4.2:** Two successive `done` events with the same `output_file` produce different `activeGlbUrl` values (because `Date.now()` advances between calls).
- **ARGLB-4.3:** After a `done` event that produces a new `activeGlbUrl`, `useAppStore.getState().activeAnimation` is `null`.
- **ARGLB-4.4:** If `output_file` is `null`, `activeGlbUrl` is not changed by `refreshAssetsAndAutoSelect`.
- **ARGLB-4.5:** If `output_file` does not match any asset in the fetched list (by `path` or `name`), `activeGlbUrl` is not changed.
- **ARGLB-4.6:** `refreshAssetsAndAutoSelect` updates `assets` in the store with the freshly fetched list regardless of whether `output_file` matches.

### 3. Risk & Ambiguity Analysis

- **Risk:** `Date.now()` is called during the async action; if the asset fetch (`fetchAssets()`) is slow, the timestamp may lag the actual completion moment. This is acceptable — the timestamp only needs to be unique, not precisely timed.
- **Edge case:** `output_file` matches by `name` but not by `path` (e.g., the asset exists in `exports/` but `output_file` is just the filename `"foo.glb"`). The `find` call checks both `a.path === outputFile || a.name === outputFile`, so name-only matching is supported.

### 4. Clarifying Questions

None.

---

## Requirement ARGLB-5 — Zustand Store `availableClips` Slice

### 1. Spec Summary

- **Description:** The `AppState` interface in `useAppStore.ts` must be extended with a dedicated `availableClips: string[]` slice and a corresponding `setAvailableClips(names: string[]) => void` action. This slice holds the list of animation clip names exposed by the currently loaded GLB model. It is distinct from `activeAnimation: string | null` (which holds the single currently-playing clip name).
- **Constraints:**
  - Initial value of `availableClips` is `[]` (empty array).
  - `setAvailableClips` replaces the entire slice (not appends); calling it with `[]` resets to empty.
  - `setAvailableClips` does not modify `activeAnimation`.
  - `setActiveAnimation` does not modify `availableClips`.
  - No other existing store slice or action is renamed or removed. `setActiveAnimation` continues to exist and operate as before.
- **Assumptions:** The scaffold currently lacks `availableClips` and `setAvailableClips`. The current workaround in `GlbViewer.tsx` aliases `setAvailableClips` to `setActiveAnimation`, which is architecturally incorrect and is fixed by this requirement (see ARGLB-6).
- **Scope:** `asset_generation/web/frontend/src/store/useAppStore.ts`.

### 2. Acceptance Criteria

- **ARGLB-5.1:** `useAppStore.getState().availableClips` is an array (`Array.isArray` returns true).
- **ARGLB-5.2:** Initial value of `availableClips` is `[]`.
- **ARGLB-5.3:** After calling `useAppStore.getState().setAvailableClips(["Walk", "Idle"])`, `useAppStore.getState().availableClips` equals `["Walk", "Idle"]`.
- **ARGLB-5.4:** `setAvailableClips` does not change `activeAnimation`. After setting `activeAnimation` to `"Walk"` and then calling `setAvailableClips(["Run"])`, `activeAnimation` remains `"Walk"`.
- **ARGLB-5.5:** `setActiveAnimation` does not change `availableClips`. After calling `setAvailableClips(["Run"])` then `setActiveAnimation("Walk")`, `availableClips` remains `["Run"]`.
- **ARGLB-5.6:** The `AppState` TypeScript interface includes `availableClips: string[]` and `setAvailableClips: (names: string[]) => void`.

### 3. Risk & Ambiguity Analysis

- **Risk:** Adding a new slice may require updating any consumers that spread or clone `AppState`. The Implementation agent must scan all files importing `useAppStore` to ensure no consumer destructures the full state shape.
- **Edge case:** `setAvailableClips([])` must set `availableClips` to `[]`, not undefined or null.

### 4. Clarifying Questions

None.

---

## Requirement ARGLB-6 — `GlbViewer` Model Component Clip-Exposure Fix

### 1. Spec Summary

- **Description:** The `Model` component inside `GlbViewer.tsx` currently contains an aliasing bug: `const setAvailableClips = useAppStore((s) => s.setActiveAnimation)`. This binds the variable named `setAvailableClips` to the store action `setActiveAnimation`, which means calling `setAvailableClips(names[0])` actually sets the active animation to the first clip name — rather than exposing the full list of clips to the store. The fix has two parts:

  1. Replace the aliased selector with the correct one: `const setAvailableClips = useAppStore((s) => s.setAvailableClips)`.
  2. Change the call from `setAvailableClips(names[0])` (single name) to `setAvailableClips(names)` (full array of names).

- **Constraints:**
  - After the fix, `setAvailableClips` must be called with `names` (the full `string[]`) when the model URL changes and `names.length > 0`.
  - Auto-selection of the first clip must use a separate call: `setActiveAnimation(names[0])` — but only if `activeAnimation` is `null` at the time of model load.
  - If `names` is empty (the GLB has no animations), `setAvailableClips([])` is called to clear the clip list, and `setActiveAnimation` is not called.
  - The `prevUrl` ref pattern (comparing `prevUrl.current !== url`) must be preserved to avoid calling `setAvailableClips` on every render.
- **Assumptions:** After ARGLB-5, `setAvailableClips` exists in the store. This requirement depends on ARGLB-5 being implemented first.
- **Scope:** `asset_generation/web/frontend/src/components/Preview/GlbViewer.tsx` — the `Model` inner component only.

### 2. Acceptance Criteria

- **ARGLB-6.1:** The line `const setAvailableClips = useAppStore((s) => s.setActiveAnimation)` does not appear in the production `GlbViewer.tsx` source.
- **ARGLB-6.2:** `GlbViewer.tsx` contains `const setAvailableClips = useAppStore((s) => s.setAvailableClips)`.
- **ARGLB-6.3:** When a model with animations `["Walk", "Idle", "Attack"]` loads, `useAppStore.getState().availableClips` becomes `["Walk", "Idle", "Attack"]`.
- **ARGLB-6.4:** When a model with animations loads and `activeAnimation` is `null`, `useAppStore.getState().activeAnimation` becomes the first clip name (e.g., `"Walk"`).
- **ARGLB-6.5:** When a model with animations loads and `activeAnimation` is already set to a non-null value (e.g., `"Idle"`), `activeAnimation` is not overwritten by the load event.
- **ARGLB-6.6:** When a model with no animations loads (`names` is `[]`), `useAppStore.getState().availableClips` becomes `[]` and `activeAnimation` is not changed.
- **ARGLB-6.7:** The `prevUrl` tracking logic fires `setAvailableClips` only when the URL changes, not on every render.

### 3. Risk & Ambiguity Analysis

- **Risk:** ARGLB-4.3 requires `refreshAssetsAndAutoSelect` to set `activeAnimation = null`. If this is not implemented, ARGLB-6.4's "if activeAnimation is null" condition will never trigger and the first clip will never auto-select. These two requirements are coupled: ARGLB-4 must be implemented before ARGLB-6 can be validated end-to-end.
- **Risk:** The animation `useEffect` in `Model` (the one that calls `actions[animation]?.play()`) already handles the case where `animation` is null by playing `names[0]` directly via `actions`. This may conflict with or duplicate the auto-select logic. The Implementation agent must ensure there is no double-play: one path (store-driven via `activeAnimation`) takes precedence, and the fallback in the effect handles the first-play case consistently.

### 4. Clarifying Questions

None.

---

## Requirement ARGLB-7 — `ErrorBoundary` Behavior

### 1. Spec Summary

- **Description:** `GlbViewer.tsx` wraps the three.js `Canvas` element in a `CanvasErrorBoundary` React class component. If the `Canvas` subtree throws a JavaScript error (e.g., due to a malformed GLB, a failed `useGLTF` parse, or a WebGL context failure), `CanvasErrorBoundary.getDerivedStateFromError` captures the error message and `render()` replaces the canvas with a fallback `div` displaying the error message. The fallback renders inside the same DOM container as the canvas (same `div` with `flex: 1` and `position: relative`).
- **Constraints:**
  - The fallback div must render within the viewer container — not as a full-page overlay.
  - The fallback must display the error message string (from `error.message`).
  - The fallback background must be visually distinct from the normal canvas background (e.g., dark red `#1a0000` vs. `#1a1a2e`).
  - The `ErrorBoundary` does not reset automatically (no retry button in scope for this ticket).
  - The `ErrorBoundary` does not suppress errors from the Zustand store, the terminal, or other components outside the canvas subtree.
- **Assumptions:** React 18 `Suspense` fallback is `null` (spinner-free), meaning a loading GLB shows nothing until ready. If `useGLTF` throws (corrupt file), the ErrorBoundary catches it because `Suspense` re-throws errors from rejected promises up the component tree.
- **Scope:** `asset_generation/web/frontend/src/components/Preview/GlbViewer.tsx` — `CanvasErrorBoundary` class component.

### 2. Acceptance Criteria

- **ARGLB-7.1:** When the `Canvas` subtree throws an error, the viewer area renders a `div` containing the text `"GLB error: <error.message>"` where `<error.message>` is the thrown error's message property.
- **ARGLB-7.2:** The error fallback div has `background: "#1a0000"` and `color: "#f88"`.
- **ARGLB-7.3:** The error fallback is rendered inside the same container element as the canvas (the outer `div` with `flex: 1`), not as a body-level modal.
- **ARGLB-7.4:** An error inside the canvas does not crash or unmount components outside the `CanvasErrorBoundary` subtree (e.g., the terminal, file tree, and animation controls remain functional).
- **ARGLB-7.5:** `CanvasErrorBoundary` implements `getDerivedStateFromError` (static method) and not only `componentDidCatch`. Both may be present, but `getDerivedStateFromError` is required for the state-driven render fallback.

**Verification note:** ARGLB-7.1 through ARGLB-7.5 require a browser rendering environment. These are **manual verification** acceptance criteria and cannot be automatically tested in the current pipeline. The AC Gatekeeper must explicitly confirm or flag these as deferred.

### 3. Risk & Ambiguity Analysis

- **Risk:** `useGLTF` in drei does not throw synchronously; it throws from a Suspense-compatible promise rejection. React 18's Suspense/ErrorBoundary integration will propagate the rejection as an error to the nearest `ErrorBoundary` above the `Suspense` boundary. The `CanvasErrorBoundary` is outside the `Suspense` component, so it will catch errors thrown by rejected `useGLTF` promises. This is the correct topology — preserved from the scaffold.
- **Edge case:** A WebGL context loss (hardware/driver event) may throw from inside the `Canvas` renderer loop. This is caught by `CanvasErrorBoundary` only if React's error boundary mechanism intercepts it. Native WebGL errors that do not propagate through React's render cycle will not be caught. This is acceptable and out of scope.

### 4. Clarifying Questions

None.

---

## Requirement ARGLB-8 — `AnimationControls` Button Active State

### 1. Spec Summary

- **Description:** `AnimationControls.tsx` renders one button per available clip name. The active clip (matching `useAppStore.getState().activeAnimation`) is visually highlighted. The clip list is determined by the following priority order:
  1. `useAppStore.getState().availableClips` if it is non-empty (post-ARGLB-5 fix).
  2. The `availableClips` prop passed to the component, if non-empty.
  3. The hardcoded 13-clip fallback list: `["Idle", "Walk", "Attack", "Hit", "Death", "Spawn", "SpecialAttack", "DamageHeavy", "DamageFire", "DamageIce", "Stunned", "Celebrate", "Taunt"]`.

  Clicking a button calls `setActiveAnimation(clip)` with that clip's name.

- **Constraints:**
  - The active button style: `background: "#0e639c"`.
  - The inactive button style: `background: "#3c3c3c"`.
  - All buttons share: `color: "#d4d4d4"`, `border: "none"`, `borderRadius: 3`, `padding: "2px 8px"`, `fontSize: 11`, `cursor: "pointer"`.
  - The priority order above is the correct post-fix behavior. Before the ARGLB-5/ARGLB-6 fix, `availableClips` from the store is always `[]`, so the prop-then-hardcoded fallback remains the effective path until those fixes land.
- **Assumptions:** The optional `availableClips` prop remains on the component signature for backward compatibility with any existing callers that pass the prop directly.
- **Scope:** `asset_generation/web/frontend/src/components/Preview/AnimationControls.tsx`.

### 2. Acceptance Criteria

- **ARGLB-8.1:** When `useAppStore.getState().activeAnimation === "Walk"`, the button with label `"Walk"` renders with `background: "#0e639c"` and all other clip buttons render with `background: "#3c3c3c"`.
- **ARGLB-8.2:** When `activeAnimation` is `null`, all buttons render with `background: "#3c3c3c"` (none is highlighted).
- **ARGLB-8.3:** Clicking a button calls `setActiveAnimation` with that button's clip name string.
- **ARGLB-8.4:** When `useAppStore.getState().availableClips` is `["Walk", "Idle"]`, exactly two buttons are rendered with labels "Walk" and "Idle".
- **ARGLB-8.5:** When `availableClips` from the store is `[]` and the prop is `undefined`, the 13-clip hardcoded list is rendered.
- **ARGLB-8.6:** When `availableClips` from the store is `[]` and the prop is `["CustomClip"]`, the prop value `["CustomClip"]` is rendered.
- **ARGLB-8.7:** When `availableClips` from the store is `["StoreClip"]` and the prop is `["PropClip"]`, the store value `["StoreClip"]` takes priority and is rendered.

**Verification note:** ARGLB-8.1, ARGLB-8.3 (click behavior in browser), and ARGLB-8.4 end-to-end (store feeding component via React rendering) are **manual verification** criteria. ARGLB-8.2, ARGLB-8.5, ARGLB-8.6, ARGLB-8.7 can be verified via unit tests with a mocked store.

### 3. Risk & Ambiguity Analysis

- **Risk:** If the store's `availableClips` slice is not yet implemented (pre-ARGLB-5), `useAppStore((s) => s.availableClips)` in `AnimationControls` will return `undefined` at runtime, causing a runtime error when `undefined.length` is checked. The Implementation agent must guard against this: either apply ARGLB-5 first, or add a nullish coalesce `?? []` at the selector call site.
- **Edge case:** Duplicate clip names in the store slice — each button must have a unique React `key`. Using `clip` as the key assumes uniqueness within the list. If the GLB exposes duplicate action names (unusual but possible), only one button will render per unique name because React deduplicates by key; the spec accepts this behavior.

### 4. Clarifying Questions

None.

---

## Cross-Cutting: Manual Verification ACs

The following acceptance criteria from the ticket require a browser rendering environment and cannot be automatically verified in the current pipeline. The AC Gatekeeper must explicitly mark each as "manual verification" or "deferred":

| Ticket AC | Spec Requirement | Reason |
|---|---|---|
| "After a successful generation run, the new GLB loads automatically in the 3D canvas without a page reload" | ARGLB-4 (store logic) — partially automatable; ARGLB-6 (three.js rendering) — manual | Three.js rendering and model load in Canvas is not testable without a browser |
| "OrbitControls let the user rotate, zoom, and pan the model" | Not assigned a numbered requirement — OrbitControls is a drei primitive with no custom logic | Manual only |
| "Clicking an animation button plays that clip on the loaded model" | ARGLB-8 (button click calls `setActiveAnimation`); three.js animation playback — manual | `actions[animation]?.play()` requires a WebGL context |
| "A malformed GLB shows an error message inside the canvas instead of crashing the whole UI" | ARGLB-7 | Requires browser rendering and a corrupt GLB fixture |

---

## Dependency Order for Implementation

Implementations must respect this order to avoid runtime errors:

1. ARGLB-5 (`availableClips` store slice) — no dependencies.
2. ARGLB-4 (`refreshAssetsAndAutoSelect` reset `activeAnimation = null`) — no dependencies, but must land before ARGLB-6 is end-to-end validated.
3. ARGLB-6 (`GlbViewer` clip-exposure fix) — depends on ARGLB-5.
4. ARGLB-8 (`AnimationControls` store-first priority) — depends on ARGLB-5.
5. ARGLB-1, ARGLB-2, ARGLB-3 (backend) — no frontend dependencies; can be verified independently.

---

## Canonical 13-Clip Fallback List

For reference (used in ARGLB-8 and as fallback in `AnimationControls`):

```
Idle, Walk, Attack, Hit, Death, Spawn, SpecialAttack,
DamageHeavy, DamageFire, DamageIce, Stunned, Celebrate, Taunt
```

These are the fallback names only. A loaded GLB may expose different clip names; the store `availableClips` slice will override this list when populated.
