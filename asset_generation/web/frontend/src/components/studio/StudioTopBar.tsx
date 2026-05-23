import type { CSSProperties } from "react";
import { useAppStore } from "../../store/useAppStore";
import { registryFamilyTabLabel } from "../../utils/registryFamilyNav";
import {
  STUDIO_INK_MUTED,
  STUDIO_INK_PRIMARY,
  STUDIO_INK_SECONDARY,
  STUDIO_SURFACE_BAR,
  STUDIO_TOP_BAR_HEIGHT_PX,
} from "../../styles/studioTokens";

const topBarRoot: CSSProperties = {
  gridColumn: "1 / 4",
  gridRow: 1,
  display: "flex",
  alignItems: "center",
  padding: "0 16px",
  gap: 14,
  height: STUDIO_TOP_BAR_HEIGHT_PX,
  background: STUDIO_SURFACE_BAR,
  borderBottom: "1px solid rgba(255,255,255,0.06)",
  flexShrink: 0,
};

const logoMark: CSSProperties = {
  width: 26,
  height: 26,
  borderRadius: 7,
  background: "conic-gradient(from 180deg, #ff6b3d, #b87dff, #5dc1ff, #9fe830, #ff6b3d)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontWeight: 800,
  color: "#0c0c10",
  fontSize: 13,
};

const breadcrumbMuted: CSSProperties = {
  fontSize: 13,
  color: STUDIO_INK_SECONDARY,
  fontWeight: 600,
};

const breadcrumbActive: CSSProperties = {
  fontSize: 13,
  color: STUDIO_INK_PRIMARY,
  fontWeight: 600,
};

const placeholderBtn: CSSProperties = {
  background: STUDIO_SURFACE_BAR,
  border: "1px solid rgba(255,255,255,0.08)",
  color: STUDIO_INK_MUTED,
  padding: "6px 12px",
  borderRadius: 8,
  fontSize: 12,
  cursor: "default",
};

export function StudioTopBar() {
  const commandContext = useAppStore((s) => s.commandContext);
  const familyLabel =
    commandContext.cmd === "animated" && commandContext.enemy
      ? registryFamilyTabLabel(commandContext.enemy)
      : commandContext.cmd;

  return (
    <header style={topBarRoot} data-testid="studio-top-bar">
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={logoMark} aria-hidden>
          B
        </div>
        <span style={{ fontWeight: 700, fontSize: 13 }}>Blobert</span>
        <span style={{ opacity: 0.4, fontSize: 13 }}>/</span>
        <span style={breadcrumbMuted}>{familyLabel}</span>
        <span style={{ opacity: 0.4, fontSize: 13 }}>/</span>
        <span style={breadcrumbActive}>
          {commandContext.cmd === "animated" && commandContext.enemy ? "Look" : "Studio"}
        </span>
      </div>
      <div style={{ flex: 1 }} />
      <button type="button" style={placeholderBtn} disabled title="Phase 2">
        ⌘K
      </button>
      <button type="button" style={placeholderBtn} disabled title="Phase 2">
        Save
      </button>
      <button type="button" style={placeholderBtn} disabled title="Phase 2">
        Regenerate
      </button>
    </header>
  );
}
