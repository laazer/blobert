import { useState, type CSSProperties } from "react";
import { useAppStore } from "../../store/useAppStore";
import { FileTree } from "../FileTree/FileTree";
import { EditorPane } from "../Editor/EditorPane";
import { ModelRegistryPane } from "../Editor/ModelRegistryPane";
import { PreviewSourceBar } from "../Preview/PreviewSourceBar";
import { BuildControls } from "../Preview/BuildControls";
import { ColorsPane } from "../Preview/ColorsPane";
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

const tabBtn = (active: boolean): CSSProperties => ({
  padding: "4px 10px",
  fontSize: 11,
  border: "1px solid #555",
  borderRadius: 3,
  cursor: "pointer",
  background: active ? "#0e639c" : "#3c3c3c",
  color: "#d4d4d4",
});

function CenterSwitchBar() {
  const centerPanel = useAppStore((s) => s.centerPanel);
  const setCenterPanel = useAppStore((s) => s.setCenterPanel);

  return (
    <div
      style={{
        display: "flex",
        gap: 6,
        padding: "4px 8px",
        borderBottom: "1px solid #3c3c3c",
        background: "#252526",
        alignItems: "center",
        flexShrink: 0,
      }}
    >
      <button
        type="button"
        style={tabBtn(centerPanel === "code")}
        onClick={() => setCenterPanel("code")}
        title="Show Python editor"
      >
        Code
      </button>
      <button
        type="button"
        style={tabBtn(centerPanel === "build")}
        onClick={() => setCenterPanel("build")}
        title="Procedural build options (eyes, mesh, rig)"
      >
        Build
      </button>
      <button
        type="button"
        style={tabBtn(centerPanel === "colors")}
        onClick={() => setCenterPanel("colors")}
        title="Per-part materials (feat_* slots) for the selected animated enemy"
      >
        Colors
      </button>
      <button
        type="button"
        style={tabBtn(centerPanel === "registry")}
        onClick={() => setCenterPanel("registry")}
        title="Draft / in-use flags for model exports (model_registry.json)"
      >
        Registry
      </button>
      <button
        type="button"
        onClick={() => setCenterPanel("none")}
        style={{
          marginLeft: "auto",
          padding: "4px 10px",
          fontSize: 11,
          border: "1px solid #555",
          borderRadius: 3,
          cursor: "pointer",
          background: "#3c3c3c",
          color: "#d4d4d4",
        }}
        title="Hide center panel"
      >
        Hide
      </button>
    </div>
  );
}

export function ThreePanelLayout() {
  const [fileTreeVisible, setFileTreeVisible] = useState(false);
  const centerPanel = useAppStore((s) => s.centerPanel);
  const setCenterPanel = useAppStore((s) => s.setCenterPanel);

  const centerOpen = centerPanel !== "none";

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>
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

      {centerOpen ? (
        <div
          id="blobert-editor-column"
          style={{
            flex: fileTreeVisible ? "0 0 45%" : "1 1 0%",
            minWidth: 0,
            minHeight: 0,
            display: "flex",
            flexDirection: "column",
            borderRight: "1px solid #3c3c3c",
          }}
        >
          <CenterSwitchBar />
          {centerPanel === "code" && <EditorPane />}
          {centerPanel === "build" && (
            <div
              style={{
                flex: 1,
                minHeight: 0,
                overflow: "auto",
                display: "flex",
                flexDirection: "column",
                background: "#1e1e1e",
              }}
            >
              <BuildControls />
            </div>
          )}
          {centerPanel === "colors" && (
            <div
              style={{
                flex: 1,
                minHeight: 0,
                overflow: "auto",
                display: "flex",
                flexDirection: "column",
                background: "#1e1e1e",
              }}
            >
              <ColorsPane />
            </div>
          )}
          {centerPanel === "registry" && (
            <div
              style={{
                flex: 1,
                minHeight: 0,
                overflow: "hidden",
                display: "flex",
                flexDirection: "column",
                background: "#1e1e1e",
              }}
            >
              <ModelRegistryPane />
            </div>
          )}
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", flexShrink: 0 }}>
          <button
            type="button"
            style={showFilesBtn}
            onClick={() => setCenterPanel("code")}
            title="Show code editor"
          >
            Code
          </button>
          <button
            type="button"
            style={showFilesBtn}
            onClick={() => setCenterPanel("build")}
            title="Show build controls"
          >
            Build
          </button>
          <button
            type="button"
            style={showFilesBtn}
            onClick={() => setCenterPanel("colors")}
            title="Show per-part colors"
          >
            Colors
          </button>
          <button
            type="button"
            style={showFilesBtn}
            onClick={() => setCenterPanel("registry")}
            title="Model registry (draft / in-use)"
          >
            Registry
          </button>
        </div>
      )}

      <div
        style={{
          flex: centerOpen ? 1 : "1 1 0%",
          minWidth: 0,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <PreviewSourceBar />
        <GlbViewer />
        <AnimationControls />
        <CommandPanel />
        <Terminal />
      </div>
    </div>
  );
}
