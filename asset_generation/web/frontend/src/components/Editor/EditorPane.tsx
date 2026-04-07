import MonacoEditor from "@monaco-editor/react";
import { useAppStore } from "../../store/useAppStore";
import { useEffect } from "react";

export function EditorPane() {
  const editorContent = useAppStore((s) => s.editorContent);
  const isDirty = useAppStore((s) => s.isDirty);
  const isSaving = useAppStore((s) => s.isSaving);
  const selectedFile = useAppStore((s) => s.selectedFile);
  const setEditorContent = useAppStore((s) => s.setEditorContent);
  const saveFile = useAppStore((s) => s.saveFile);

  // Ctrl+S to save
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        saveFile();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [saveFile]);

  if (!selectedFile) {
    return (
      <div style={{
        flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
        background: "#1e1e1e", color: "#555", fontSize: 13,
      }}>
        Select a file from the tree
      </div>
    );
  }

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <div style={{
        background: "#252526", padding: "3px 12px", fontSize: 11, color: "#9d9d9d",
        borderBottom: "1px solid #3c3c3c", display: "flex", gap: 8, alignItems: "center",
      }}>
        <span>{selectedFile}</span>
        {isDirty && <span style={{ color: "#e2b714" }}>●</span>}
        {isSaving && <span style={{ color: "#9d9d9d" }}>saving...</span>}
      </div>
      <div style={{ flex: 1, overflow: "hidden" }}>
        <MonacoEditor
          height="100%"
          language="python"
          theme="vs-dark"
          value={editorContent}
          onChange={(v) => setEditorContent(v ?? "")}
          options={{
            minimap: { enabled: false },
            fontSize: 13,
            wordWrap: "on",
            scrollBeyondLastLine: false,
          }}
        />
      </div>
    </div>
  );
}
