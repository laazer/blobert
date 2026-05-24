import { useMemo, useState, type CSSProperties } from "react";
import { ELEMENTS } from "../../constants/elements";
import { useAppStore } from "../../store/useAppStore";
import { inferFamilyElementId } from "../../utils/inferFamilyElement";
import { ColorsPane } from "../Preview/ColorsPane";
import { BuildControls } from "../Preview/BuildControls";
import { StudioCodePanel } from "./StudioCodePanel";
import { StudioVersionsPanel } from "./StudioVersionsPanel";
import {
  STUDIO_INSPECTOR_WIDTH_PX,
  STUDIO_INK_SECONDARY,
  STUDIO_SURFACE_PANEL,
  studioInspectorTabStyle,
} from "../../styles/studioTokens";

export const STUDIO_INSPECTOR_TABS = ["look", "build", "code", "versions"] as const;
export type StudioInspectorTab = (typeof STUDIO_INSPECTOR_TABS)[number];

/** Animate tab hidden until center-rail animation UX is product-ready. */
export const STUDIO_INSPECTOR_TAB_HIDDEN = ["animate"] as const;

const inspectorRoot: CSSProperties = {
  gridColumn: 3,
  gridRow: 2,
  width: STUDIO_INSPECTOR_WIDTH_PX,
  display: "flex",
  flexDirection: "column",
  borderLeft: "1px solid rgba(255,255,255,0.06)",
  background: STUDIO_SURFACE_PANEL,
  overflow: "hidden",
};

const tabStrip: CSSProperties = {
  display: "flex",
  borderBottom: "1px solid rgba(255,255,255,0.06)",
  flexShrink: 0,
};

const panelBody: CSSProperties = {
  flex: 1,
  minHeight: 0,
  overflow: "auto",
  padding: 16,
  fontSize: 12,
  color: STUDIO_INK_SECONDARY,
};

function useInspectorElementHue(): string | undefined {
  const commandContext = useAppStore((s) => s.commandContext);
  return useMemo(() => {
    if (commandContext.cmd !== "animated" || !commandContext.enemy.trim()) {
      return undefined;
    }
    const family = commandContext.enemy.trim();
    return ELEMENTS[inferFamilyElementId(family, [])].hue;
  }, [commandContext.cmd, commandContext.enemy]);
}

export function StudioInspector() {
  const [activeTab, setActiveTab] = useState<StudioInspectorTab>("look");
  const elementHue = useInspectorElementHue();

  return (
    <aside style={inspectorRoot} data-testid="studio-inspector" aria-label="Inspector">
      <div style={tabStrip} role="tablist" aria-label="Inspector sections">
        {STUDIO_INSPECTOR_TABS.map((tab) => {
          const active = activeTab === tab;
          const label = tab.charAt(0).toUpperCase() + tab.slice(1);
          return (
            <button
              key={tab}
              type="button"
              role="tab"
              id={`studio-inspector-tab-${tab}`}
              data-testid={`studio-inspector-tab-${tab}`}
              aria-selected={active}
              aria-controls={active ? `studio-inspector-panel-${tab}` : undefined}
              style={studioInspectorTabStyle(active, elementHue)}
              onClick={() => setActiveTab(tab)}
            >
              {label}
            </button>
          );
        })}
      </div>
      <div
        id={`studio-inspector-panel-${activeTab}`}
        role="tabpanel"
        data-testid={`studio-inspector-panel-${activeTab}`}
        aria-labelledby={`studio-inspector-tab-${activeTab}`}
        style={
          activeTab === "code"
            ? { ...panelBody, display: "flex", flexDirection: "column", padding: 14 }
            : panelBody
        }
      >
        {activeTab === "look" ? (
          <ColorsPane studioSurface />
        ) : activeTab === "build" ? (
          <BuildControls studioSurface />
        ) : activeTab === "code" ? (
          <StudioCodePanel />
        ) : activeTab === "versions" ? (
          <StudioVersionsPanel />
        ) : null}
      </div>
    </aside>
  );
}
