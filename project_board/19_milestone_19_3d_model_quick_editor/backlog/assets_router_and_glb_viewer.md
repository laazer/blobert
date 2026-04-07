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
