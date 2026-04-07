import { useState, type CSSProperties } from "react";
import { useAppStore } from "../../store/useAppStore";
import { FileTree } from "../FileTree/FileTree";
import { EditorPane } from "../Editor/EditorPane";
import { PreviewSourceBar } from "../Preview/PreviewSourceBar";
import { BuildControls } from "../Preview/BuildControls";
import { GlbViewer } from "../Preview/GlbViewer";
import { AnimationControls } from "../Preview/AnimationControls";
import { CommandPanel } from "../CommandPanel/CommandPanel";
import { Terminal } from "../Terminal/Terminal";

const showFilesBtn: CSSProperties = {
  writingMode: "vertical-rl",
  transform: "rotate(180deg)",
  background: "#252526",
  color: "#9d9d9d",
  border: "none",
  borderRight: "1px solid #3c3c3c",
  cursor: "pointer",
  fontSize: 11,
  padding: "8px 4px",
  flexShrink: 0,
};

export function ThreePanelLayout() {
  const [fileTreeVisible, setFileTreeVisible] = useState(false);
  const editorPaneVisible = useAppStore((s) => s.editorPaneVisible);
  const setEditorPaneVisible = useAppStore((s) => s.setEditorPaneVisible);

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>
      {/* Left: File Tree (hidden by default) */}
      {fileTreeVisible ? (
        <div style={{ width: "18%", minWidth: 160, flexShrink: 0, display: "flex", flexDirection: "column" }}>
          <FileTree onRequestHide={() => setFileTreeVisible(false)} />
        </div>
      ) : (
        <button
          type="button"
          style={showFilesBtn}
          onClick={() => setFileTreeVisible(true)}
          title="Show file tree"
        >
          Files
        </button>
      )}

      {/* Center: Editor (collapsible) */}
      {editorPaneVisible ? (
        <div
          id="blobert-editor-column"
          style={{
            flex: fileTreeVisible ? "0 0 45%" : "1 1 0%",
            minWidth: 0,
            display: "flex",
            flexDirection: "column",
            borderRight: "1px solid #3c3c3c",
          }}
        >
          <EditorPane onRequestHide={() => setEditorPaneVisible(false)} />
        </div>
      ) : (
        <button
          type="button"
          style={showFilesBtn}
          onClick={() => setEditorPaneVisible(true)}
          title="Show code editor"
        >
          Code
        </button>
      )}

      {/* Right: 3D + terminal stack (grows when editor hidden) */}
      <div
        style={{
          flex: editorPaneVisible ? 1 : "1 1 0%",
          minWidth: 0,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <PreviewSourceBar />
        <BuildControls />
        <GlbViewer />
        <AnimationControls />
        <CommandPanel />
        <Terminal />
      </div>
    </div>
  );
}
