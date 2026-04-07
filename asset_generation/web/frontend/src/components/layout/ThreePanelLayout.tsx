import { useState, type CSSProperties } from "react";
import { FileTree } from "../FileTree/FileTree";
import { EditorPane } from "../Editor/EditorPane";
import { PreviewSourceBar } from "../Preview/PreviewSourceBar";
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

      {/* Center: Editor */}
      <div
        style={{
          flex: fileTreeVisible ? "0 0 45%" : "1 1 0%",
          minWidth: 0,
          display: "flex",
          flexDirection: "column",
          borderRight: "1px solid #3c3c3c",
        }}
      >
        <EditorPane />
      </div>

      {/* Right: 3D + terminal stack */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <PreviewSourceBar />
        <GlbViewer />
        <AnimationControls />
        <CommandPanel />
        <Terminal />
      </div>
    </div>
  );
}
