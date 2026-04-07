Title:
Frontend React scaffold — three-panel layout and Monaco editor

Description:
Bootstrap the Vite + React + TypeScript frontend at `asset_generation/web/frontend/`. Install all dependencies (react 18, @monaco-editor/react, @react-three/fiber, @react-three/drei, three, zustand + immer, ansi-to-html). Configure `vite.config.ts` to proxy `/api` → `http://localhost:8000`. Implement the Zustand store (`useAppStore`) covering file-tree, editor (content / isDirty / isSaving), run, and assets slices. Build `ThreePanelLayout` (FileTree 18% / Monaco 45% / right column flex), `FileTree` (recursive render, click to open), and `EditorPane` (Monaco `language="python"` `theme="vs-dark"`, controlled, Ctrl+S save, dirty dot).

Acceptance Criteria:
- `npm run dev` starts without errors and the three-panel layout renders at `http://localhost:5173`
- Clicking a `.py` file in the FileTree loads its content into Monaco with Python syntax highlighting
- Editing any character shows a dirty indicator (●)
- Ctrl+S (or Cmd+S) saves the file; dirty indicator disappears and the file on disk is updated
- No CORS errors in the browser console (Vite proxy is active)
