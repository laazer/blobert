import MonacoEditor from "@monaco-editor/react";
import { useEffect } from "react";
import { useAppStore } from "../../store/useAppStore";
import { STUDIO_INK_MUTED, STUDIO_INK_SECONDARY } from "../../styles/studioTokens";

type Props = {
  accentHue?: string;
};

export function StudioEditorSurface({ accentHue }: Props) {
  const editorContent = useAppStore((s) => s.editorContent);
  const isDirty = useAppStore((s) => s.isDirty);
  const isSaving = useAppStore((s) => s.isSaving);
  const selectedFile = useAppStore((s) => s.selectedFile);
  const setEditorContent = useAppStore((s) => s.setEditorContent);
  const saveFile = useAppStore((s) => s.saveFile);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        void saveFile();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [saveFile]);

  if (!selectedFile) {
    return (
      <div
        style={{
          flex: 1,
          minHeight: 160,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: STUDIO_INK_MUTED,
          fontSize: 11,
          padding: 12,
          textAlign: "center",
        }}
      >
        No file selected for this source.
      </div>
    );
  }

  return (
    <div
      data-testid="studio-code-editor"
      style={{
        flex: 1,
        minHeight: 200,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        borderRadius: 9,
        border: "1px solid rgba(255,255,255,0.06)",
        background: "#08080c",
      }}
    >
      <div
        style={{
          padding: "6px 10px",
          borderBottom: "1px solid rgba(255,255,255,0.05)",
          display: "flex",
          alignItems: "center",
          gap: 8,
          fontSize: 10,
          color: STUDIO_INK_MUTED,
        }}
      >
        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1 }}>
          {selectedFile}
        </span>
        {isDirty ? <span style={{ color: accentHue ?? "#e2b714" }}>●</span> : null}
        {isSaving ? <span style={{ color: STUDIO_INK_SECONDARY }}>saving…</span> : null}
      </div>
      <div style={{ flex: 1, minHeight: 0 }}>
        <MonacoEditor
          height="100%"
          language="python"
          theme="vs-dark"
          value={editorContent}
          onChange={(v) => setEditorContent(v ?? "")}
          options={{
            minimap: { enabled: false },
            fontSize: 12,
            wordWrap: "on",
            scrollBeyondLastLine: false,
            padding: { top: 8 },
          }}
        />
      </div>
    </div>
  );
}
