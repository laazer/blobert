import { useMemo, type CSSProperties, type ReactNode } from "react";
import { ELEMENTS } from "../../constants/elements";
import { usePersistedBoolean } from "../../hooks/usePersistedBoolean";
import { useAppStore } from "../../store/useAppStore";
import { inferFamilyElementId } from "../../utils/inferFamilyElement";
import {
  studioAnimationCollapsibleBar,
  studioAnimationCollapsibleTitle,
  studioAnimationCollapsibleToggle,
} from "../../styles/studioPreviewStyles";
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
      <div style={studioAnimationCollapsibleBar}>
        <span style={studioAnimationCollapsibleTitle}>{title}</span>
        <button
          type="button"
          style={studioAnimationCollapsibleToggle}
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
  const commandContext = useAppStore((s) => s.commandContext);

  const elementId = useMemo(() => {
    if (commandContext.cmd === "animated" && commandContext.enemy.trim()) {
      return inferFamilyElementId(commandContext.enemy.trim(), []);
    }
    return "physical" as const;
  }, [commandContext.cmd, commandContext.enemy]);

  const accentHue = ELEMENTS[elementId].hue;

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
        <AnimationControls appearance="studio" accentHue={accentHue} />
      </CollapsiblePreviewSection>
    </main>
  );
}
