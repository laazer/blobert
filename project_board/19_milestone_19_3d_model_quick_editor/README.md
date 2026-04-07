# Epic: Milestone 19 – 3D Model Quick Editor

**Goal:** Collapse the edit → generate → preview loop for the Python asset generation pipeline into a single browser tab. Edit Python source files in Monaco, run Blender generation commands with a click, stream live output, and preview the resulting GLB in an interactive 3D viewer — all local, no auth.

## Scope

- **FastAPI backend** at `:8000`: file CRUD for `src/` (path-jailed to `.py` files), SSE command runner that streams Blender output, asset listing/serving for all four export dirs, `/api/meta/enemies` and `/api/meta/animations` endpoints, pytest SSE runner
- **React + Vite frontend** at `:5173`: three-panel layout (FileTree / Monaco editor / 3D stack), Zustand store, proxy `/api` → `:8000`
- **3D canvas**: `@react-three/fiber` + `@react-three/drei` GLB viewer with OrbitControls, Grid, Environment, and per-clip AnimationControls
- **CommandPanel**: cmd selector (animated/player/level/smart/stats/test), enemy dropdown from `/api/meta/enemies`, count, description/difficulty for smart mode, Save + Run + Kill + Run pytest buttons
- **Terminal**: ANSI-aware scrollable output panel fed by SSE event stream
- **`start.sh`**: one command bootstraps both servers; `Ctrl+C` kills both

## Out of Scope

- Authentication or multi-user support
- Deploying beyond localhost
- Editing files outside `asset_generation/python/src/` (other dirs are read-only assets)
- Godot integration or in-engine preview

## Dependencies

- M5 (Procedural Enemy Generation) — `asset_generation/python/` pipeline must be functional; Blender must be installed or `BLENDER_PATH` set
- The `src/utils/enemy_slug_registry.py` and `src/utils/constants.py` files are treated as source-of-truth for enemy slugs and animation clip names

## Exit Criteria

From `bash asset_generation/web/start.sh`:
- `GET /api/files` returns a tree of `.py` files from `src/`
- `PUT /api/files/…` with a path traversal attempt returns `400`
- Clicking a file in the FileTree opens it in Monaco with Python syntax highlighting
- Editing + Ctrl+S saves the file (dirty dot disappears)
- Selecting `animated` / `adhesion_bug` / count 1 → Run → terminal streams Blender output → `Done (exit 0)`
- After done, the GLB auto-loads in the 3D canvas; clicking `Walk` plays the Walk animation
- Kill button terminates Blender mid-run
- "Run pytest" streams pytest output into the terminal

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Verified, merged
