import { useMemo, type CSSProperties, type ReactNode } from "react";
import { ELEMENTS } from "../../constants/elements";
import { usePersistedBoolean } from "../../hooks/usePersistedBoolean";
import { useAppStore } from "../../store/useAppStore";
import { inferFamilyElementId } from "../../utils/inferFamilyElement";
import { useStudioPreviewScale } from "../../hooks/useStudioPreviewScale";
import {
  studioAnimationCollapsibleBar,
  studioAnimationCollapsibleTitle,
  studioAnimationCollapsibleToggle,
  studioPreviewMetaBarRoot,
  studioPreviewViewportFrameStyle,
  studioPreviewViewportShellStyle,
} from "../../styles/studioPreviewStyles";
import { GlbViewer } from "../Preview/GlbViewer";
import { AnimationControls } from "../Preview/AnimationControls";
import { StudioPreviewMetaBar } from "./StudioPreviewMetaBar";
import { StudioPreviewSizeChips } from "./StudioPreviewSizeChips";

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
  const { scale, canShrink, canEnlarge, shrink, enlarge } = useStudioPreviewScale();
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
        <div style={studioPreviewMetaBarRoot} data-testid="studio-preview-header">
          <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 6, flex: 1, minWidth: 0 }}>
            <StudioPreviewMetaBar embedded />
          </div>
          <StudioPreviewSizeChips
            scale={scale}
            canShrink={canShrink}
            canEnlarge={canEnlarge}
            onShrink={shrink}
            onEnlarge={enlarge}
          />
        </div>
        <div
          style={studioPreviewViewportFrameStyle(accentHue)}
          data-testid="studio-preview-viewport-frame"
        >
          <div
            data-testid="studio-preview-viewport"
            style={{
              width: `${scale * 100}%`,
              height: `${scale * 100}%`,
              maxWidth: "100%",
              maxHeight: "100%",
              minHeight: 0,
              display: "flex",
              flexDirection: "column",
              flexShrink: 0,
              ...studioPreviewViewportShellStyle(accentHue),
            }}
          >
            <GlbViewer />
          </div>
        </div>
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
