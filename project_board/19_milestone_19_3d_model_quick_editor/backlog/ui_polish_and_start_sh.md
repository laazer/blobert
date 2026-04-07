Title:
UI polish, start.sh launcher, and smoke verification

Description:
Wire up `start.sh` (bootstraps backend `.venv`, installs frontend `node_modules`, launches both servers, `Ctrl+C` kills both). Polish pass: unsaved-file dot is visible in the editor tab bar, ANSI stripping works for all color codes from `main.py`'s `Colors` class, Kill button is only visible while a process is running, loading states (spinner or disabled state) during save and asset fetch, `ErrorBoundary` on the 3D Canvas shows a readable error message. Run the full smoke verification from the plan against a live local environment.

Acceptance Criteria:
- `bash asset_generation/web/start.sh` brings up both servers; `http://localhost:5173` loads
- If `.venv` or `node_modules` don't exist, `start.sh` creates them automatically on first run
- `Ctrl+C` in the terminal running `start.sh` kills both the backend and frontend processes
- Unsaved changes show a `●` dot in the editor tab; dot disappears after Ctrl+S
- All 13 animation buttons render; active one is visually highlighted
- ANSI color escape codes from Blender output render as colored text, not raw escape sequences
- Smoke checklist from the plan README passes end-to-end (file edit → run → GLB preview → animation playback)
