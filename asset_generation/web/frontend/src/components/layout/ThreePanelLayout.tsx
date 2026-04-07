import { FileTree } from "../FileTree/FileTree";
import { EditorPane } from "../Editor/EditorPane";
import { GlbViewer } from "../Preview/GlbViewer";
import { AnimationControls } from "../Preview/AnimationControls";
import { CommandPanel } from "../CommandPanel/CommandPanel";
import { Terminal } from "../Terminal/Terminal";

export function ThreePanelLayout() {
  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>
      {/* Left: File Tree */}
      <div style={{ width: "18%", minWidth: 160, flexShrink: 0 }}>
        <FileTree />
      </div>

      {/* Center: Editor */}
      <div style={{ width: "45%", display: "flex", flexDirection: "column", borderRight: "1px solid #3c3c3c" }}>
        <EditorPane />
      </div>

      {/* Right: 3D + terminal stack */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <GlbViewer />
        <AnimationControls />
        <CommandPanel />
        <Terminal />
      </div>
    </div>
  );
}
