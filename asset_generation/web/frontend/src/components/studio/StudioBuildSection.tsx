import { useState, type CSSProperties, type ReactNode } from "react";
import type { BuildSectionId } from "../../utils/buildControlSections";
import { STUDIO_INK_MUTED } from "../../styles/studioTokens";

type Props = {
  sectionId: BuildSectionId;
  title: string;
  summary: string;
  defaultOpen?: boolean;
  badge?: string | number;
  headerToggle?: ReactNode;
  children: ReactNode;
};

const sectionShell: CSSProperties = {
  borderRadius: 8,
  border: "1px solid rgba(255,255,255,0.04)",
  background: "#121218",
  overflow: "hidden",
};

const headerRow: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  padding: "10px 10px",
  cursor: "pointer",
  userSelect: "none",
  listStyle: "none",
};

const bodyPad: CSSProperties = {
  padding: "0 10px 12px",
  display: "flex",
  flexDirection: "column",
  gap: 12,
};

export function StudioBuildSection({
  sectionId,
  title,
  summary,
  defaultOpen = false,
  badge,
  headerToggle,
  children,
}: Props) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <details
      data-testid={`studio-build-section-${sectionId}`}
      style={sectionShell}
      defaultOpen={defaultOpen}
      onToggle={(e) => setOpen(e.currentTarget.open)}
    >
      <summary style={headerRow}>
        <span style={{ color: STUDIO_INK_MUTED, fontSize: 10, width: 12 }} aria-hidden>
          {open ? "▼" : "▶"}
        </span>
        {headerToggle ?? null}
        <span style={{ flex: 1, fontSize: 12, fontWeight: 700, color: "#ededf0" }}>{title}</span>
        {badge !== undefined ? (
          <span
            style={{
              fontSize: 10,
              fontWeight: 700,
              color: "#8a8a96",
              background: "#23232e",
              borderRadius: 10,
              padding: "2px 7px",
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
            }}
          >
            {badge}
          </span>
        ) : null}
        <span
          style={{
            fontSize: 10,
            color: STUDIO_INK_MUTED,
            maxWidth: 140,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            textAlign: "right",
          }}
        >
          {summary}
        </span>
      </summary>
      <div style={bodyPad}>{children}</div>
    </details>
  );
}
