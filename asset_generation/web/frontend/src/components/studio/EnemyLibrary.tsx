import type { CSSProperties } from "react";
import { ELEMENTS } from "../../constants/elements";
import { useStudioEnemyLibrary, type StudioLibrarySegment } from "../../hooks/useStudioEnemyLibrary";
import {
  STUDIO_INK_MUTED,
  STUDIO_INK_PRIMARY,
  STUDIO_INK_SECONDARY,
  STUDIO_LIBRARY_WIDTH_PX,
  STUDIO_SURFACE_PANEL,
} from "../../styles/studioTokens";

const railRoot: CSSProperties = {
  gridColumn: 1,
  gridRow: 2,
  width: STUDIO_LIBRARY_WIDTH_PX,
  display: "flex",
  flexDirection: "column",
  borderRight: "1px solid rgba(255,255,255,0.06)",
  background: STUDIO_SURFACE_PANEL,
  overflow: "hidden",
};

const segmentStrip: CSSProperties = {
  display: "flex",
  gap: 4,
  background: "#16161d",
  padding: 3,
  borderRadius: 8,
};

const familiesHeader: CSSProperties = {
  fontSize: 11,
  color: STUDIO_INK_MUTED,
  fontWeight: 600,
  letterSpacing: 0.6,
  textTransform: "uppercase",
};

const footerNote: CSSProperties = {
  fontSize: 10,
  color: "#5a5a66",
  textAlign: "center",
  fontFamily: "ui-monospace, monospace",
};

const SEGMENTS: { id: StudioLibrarySegment; label: string }[] = [
  { id: "enemies", label: "Enemies" },
  { id: "player", label: "Player" },
  { id: "level", label: "Level" },
];

function segmentButtonStyle(active: boolean): CSSProperties {
  return {
    flex: 1,
    padding: "6px 8px",
    border: 0,
    background: active ? "#23232e" : "transparent",
    color: active ? STUDIO_INK_PRIMARY : "#8a8a96",
    borderRadius: 6,
    cursor: "pointer",
    fontSize: 12,
    fontWeight: 600,
  };
}

function familyRowStyle(active: boolean, accentHue: string): CSSProperties {
  return {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "8px 10px",
    borderRadius: 8,
    border: 0,
    width: "100%",
    background: active ? "#16161d" : "transparent",
    cursor: "pointer",
    textAlign: "left",
    boxShadow: active ? `inset 3px 0 0 ${accentHue}` : "none",
    transition: "background 120ms",
  };
}

export function EnemyLibrary() {
  const {
    segment,
    setSegment,
    data,
    error,
    reload,
    familyRows,
    selectedFamily,
    selectFamily,
    totalVariants,
  } = useStudioEnemyLibrary();

  return (
    <aside style={railRoot} data-testid="studio-enemy-library" aria-label="Enemy library">
      <div style={{ padding: "14px 14px 10px", flexShrink: 0 }}>
        <div style={segmentStrip} role="tablist" aria-label="Asset categories">
          {SEGMENTS.map(({ id, label }) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={segment === id}
              data-testid={`studio-library-segment-${id}`}
              style={segmentButtonStyle(segment === id)}
              onClick={() => setSegment(id)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {segment === "enemies" ? (
        <>
          <div
            style={{
              padding: "4px 14px 0",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexShrink: 0,
            }}
          >
            <div style={familiesHeader}>Families</div>
            <button
              type="button"
              title="Add enemy family (registry pane)"
              disabled
              style={{
                background: "transparent",
                border: 0,
                color: STUDIO_INK_MUTED,
                cursor: "not-allowed",
                fontSize: 16,
                padding: 0,
                lineHeight: 1,
                opacity: 0.5,
              }}
              aria-label="New enemy family (coming soon)"
            >
              ＋
            </button>
          </div>

          {!data && !error ? (
            <p style={{ padding: "12px 14px", margin: 0, fontSize: 12, color: STUDIO_INK_MUTED }}>
              Loading families…
            </p>
          ) : error ? (
            <div style={{ padding: "8px 14px", flex: 1 }}>
              <p style={{ margin: "0 0 8px", fontSize: 11, color: "#f48771" }}>{error}</p>
              <button
                type="button"
                onClick={reload}
                style={{
                  fontSize: 11,
                  padding: "4px 10px",
                  borderRadius: 6,
                  border: "1px solid rgba(255,255,255,0.08)",
                  background: "#23232e",
                  color: STUDIO_INK_SECONDARY,
                  cursor: "pointer",
                }}
              >
                Retry
              </button>
            </div>
          ) : familyRows.length === 0 ? (
            <p style={{ padding: "12px 14px", margin: 0, fontSize: 12, color: STUDIO_INK_MUTED }}>
              No enemy families in registry.
            </p>
          ) : (
            <div
              style={{
                padding: "8px 10px",
                display: "flex",
                flexDirection: "column",
                gap: 2,
                overflowY: "auto",
                flex: 1,
                minHeight: 0,
              }}
              role="list"
              aria-label="Enemy families"
            >
              {familyRows.map((row) => {
                const el = ELEMENTS[row.elementId];
                const active = selectedFamily === row.id;
                return (
                  <button
                    key={row.id}
                    type="button"
                    role="listitem"
                    data-testid={`studio-family-row-${row.id}`}
                    aria-current={active ? "true" : undefined}
                    style={familyRowStyle(active, el.hue)}
                    onClick={() => selectFamily(row.id)}
                  >
                    <div
                      style={{
                        width: 28,
                        height: 28,
                        borderRadius: 7,
                        background: el.soft,
                        border: `1px solid ${el.hue}40`,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: el.ink,
                        fontSize: 14,
                        flexShrink: 0,
                      }}
                      aria-hidden
                    >
                      {el.glyph ?? "◆"}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div
                        style={{
                          fontSize: 13,
                          fontWeight: 600,
                          color: active ? STUDIO_INK_PRIMARY : STUDIO_INK_SECONDARY,
                        }}
                      >
                        {row.label}
                      </div>
                      <div
                        style={{
                          fontSize: 10,
                          color: "#6a6a76",
                          marginTop: 1,
                          fontWeight: 500,
                        }}
                      >
                        {row.versionCount} version{row.versionCount === 1 ? "" : "s"} ·{" "}
                        {el.name.toLowerCase()}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          <div
            style={{
              padding: "12px 14px",
              borderTop: "1px solid rgba(255,255,255,0.06)",
              flexShrink: 0,
            }}
          >
            <p style={{ ...footerNote, margin: 0 }}>
              {familyRows.length} famil{familyRows.length === 1 ? "y" : "ies"} · {totalVariants}{" "}
              variant{totalVariants === 1 ? "" : "s"}
            </p>
          </div>
        </>
      ) : (
        <div style={{ padding: "12px 14px", flex: 1, fontSize: 12, color: STUDIO_INK_MUTED, lineHeight: 1.5 }}>
          {segment === "player"
            ? "Player variants are managed in the Versions inspector tab."
            : "Level assets use cmd: level in the command bar. Full level library navigation is Phase 2."}
        </div>
      )}
    </aside>
  );
}
