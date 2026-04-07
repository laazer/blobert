Title:
SSE run endpoint, process manager, and terminal panel

Description:
Implement `core/process_manager.py` (asyncio subprocess, `stderr=STDOUT`, `run_id`, kill support) and `routers/run.py` (`GET /api/run/stream` SSE with query params `cmd/enemy/count/description/difficulty`, server-side allowlist for `cmd`, `BLENDER_PATH` forwarded into env, `POST /api/run/kill`, `GET /api/run/status`). On the frontend, implement `useStreamingOutput.ts` (EventSource → store dispatch, `done` triggers `refreshAssetsAndAutoSelect`), `Terminal.tsx` (ansi-to-html, auto-scroll, 5000-line cap), and `CommandPanel.tsx` (cmd/enemy/count/description/difficulty inputs, Save + Run + Kill + Run pytest buttons, `isRunning` guard).

Acceptance Criteria:
- Selecting `cmd=animated`, `enemy=adhesion_bug`, `count=1` and clicking Run opens an EventSource; Blender output lines appear in the terminal panel in real time
- Terminal renders ANSI color codes (green ✅, red ❌) correctly
- `Done (exit 0)` message appears when generation succeeds
- Kill button sends `POST /api/run/kill`; Blender process terminates; terminal shows a termination message
- Run button is disabled while a process is running
- `GET /api/run/stream?cmd=evil` returns an SSE `error` event (allowlist enforced)
- "Run pytest" button streams pytest output into the same terminal via `/api/tests/stream`
