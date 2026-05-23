import { type CSSProperties, type ReactNode } from "react";
import { usePersistedBoolean } from "../../hooks/usePersistedBoolean";
import { PreviewSourceBar } from "../Preview/PreviewSourceBar";
import { GlbViewer } from "../Preview/GlbViewer";
import { AnimationControls } from "../Preview/AnimationControls";

const LS_PREVIEW_ANIMATION_EXPANDED = "blobert.editor.preview.animationExpanded";

const previewColumnRoot: CSSProperties = {
  gridColumn: 2,
  gridRow: 2,
  minWidth: 0,
  minHeight: 0,
  display: "flex",
  flexDirection: "column",
  overflow: "hidden",
};

const collapsibleBar: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 6,
  padding: "4px 8px",
  background: "#252526",
  borderTop: "1px solid #3c3c3c",
  flexShrink: 0,
};

const collapsibleTitle: CSSProperties = {
  fontSize: 11,
  color: "#9d9d9d",
  flex: 1,
};

const collapsibleToggle: CSSProperties = {
  background: "#3c3c3c",
  color: "#d4d4d4",
  border: "1px solid #555",
  borderRadius: 3,
  padding: "2px 8px",
  cursor: "pointer",
  fontSize: 11,
};

type CollapsiblePreviewSectionProps = {
  panelId: string;
  title: string;
  regionLabel: string;
  expandLabel: string;
  collapseLabel: string;
  expanded: boolean;
  onExpandedChange: (next: boolean) => void;
  children: ReactNode;
};

function CollapsiblePreviewSection({
  panelId,
  title,
  regionLabel,
  expandLabel,
  collapseLabel,
  expanded,
  onExpandedChange,
  children,
}: CollapsiblePreviewSectionProps) {
  return (
    <div style={{ flexShrink: 0, display: "flex", flexDirection: "column" }}>
      <div style={collapsibleBar}>
        <span style={collapsibleTitle}>{title}</span>
        <button
          type="button"
          style={collapsibleToggle}
          aria-expanded={expanded}
          aria-controls={expanded ? panelId : undefined}
          onClick={() => onExpandedChange(!expanded)}
        >
          {expanded ? collapseLabel : expandLabel}
        </button>
      </div>
      {expanded ? (
        <div id={panelId} role="region" aria-label={regionLabel} style={{ flexShrink: 0 }}>
          {children}
        </div>
      ) : null}
    </div>
  );
}

export function StudioPreviewColumn() {
  const [animationExpanded, setAnimationExpanded] = usePersistedBoolean(LS_PREVIEW_ANIMATION_EXPANDED, true);

  return (
    <main style={previewColumnRoot} data-testid="studio-preview-column">
      <div
        style={{
          flex: 1,
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <PreviewSourceBar />
        <GlbViewer />
      </div>
      <CollapsiblePreviewSection
        panelId="blobert-studio-preview-animation-panel"
        title="Animations"
        regionLabel="Animation clips and playback"
        expandLabel="Show animations"
        collapseLabel="Hide animations"
        expanded={animationExpanded}
        onExpandedChange={setAnimationExpanded}
      >
        <AnimationControls />
      </CollapsiblePreviewSection>
    </main>
  );
}
