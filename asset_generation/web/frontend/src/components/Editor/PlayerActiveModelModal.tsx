import { useEffect, useId, useMemo, useState, type CSSProperties } from "react";
import { createPortal } from "react-dom";
import type { PlayerModelSelectOption } from "../../utils/registryPlayerModelOptions";

const overlay: CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(0,0,0,0.55)",
  zIndex: 10000,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: 16,
};
const dialog: CSSProperties = {
  background: "#252526",
  border: "1px solid #3c3c3c",
  borderRadius: 6,
  padding: 16,
  maxWidth: 560,
  width: "100%",
  maxHeight: "min(80vh, 600px)",
  display: "flex",
  flexDirection: "column",
  gap: 10,
  boxShadow: "0 8px 32px rgba(0,0,0,0.45)",
};
const title: CSSProperties = { margin: 0, fontSize: 14, color: "#e0e0e0", fontWeight: 600 };
const textInput: CSSProperties = {
  width: "100%",
  boxSizing: "border-box",
  background: "#3c3c3c",
  color: "#d4d4d4",
  border: "1px solid #555",
  borderRadius: 3,
  padding: "8px 10px",
  fontSize: 12,
};
const btnRow: CSSProperties = { display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" };
const btn: CSSProperties = {
  padding: "6px 14px",
  fontSize: 12,
  borderRadius: 3,
  cursor: "pointer",
  border: "1px solid #555",
  background: "#3c3c3c",
  color: "#d4d4d4",
};
const listWrap: CSSProperties = {
  overflow: "auto",
  flex: 1,
  minHeight: 160,
  border: "1px solid #3c3c3c",
  borderRadius: 4,
  padding: 4,
};
const rowBtn: CSSProperties = {
  display: "block",
  width: "100%",
  textAlign: "left",
  padding: "8px 10px",
  marginBottom: 4,
  fontSize: 11,
  fontFamily: "ui-monospace, monospace",
  color: "#d4d4d4",
  background: "#2d2d2d",
  border: "1px solid #3c3c3c",
  borderRadius: 4,
  cursor: "pointer",
};
const rowBtnActive: CSSProperties = {
  ...rowBtn,
  borderColor: "#0e639c",
  background: "#1a3d52",
};
const hint: CSSProperties = { color: "#8f8f8f", fontSize: 10, margin: 0, lineHeight: 1.4 };

function normalizeFilter(s: string): string {
  return s.trim().toLowerCase();
}

export type PlayerActiveModelModalProps = {
  open: boolean;
  options: readonly PlayerModelSelectOption[];
  currentPath: string | null;
  busy: boolean;
  onClose: () => void;
  onPick: (path: string) => void | Promise<void>;
};

export function PlayerActiveModelModal({
  open,
  options,
  currentPath,
  busy,
  onClose,
  onPick,
}: PlayerActiveModelModalProps) {
  const titleId = useId();
  const filterId = useId();
  const [filter, setFilter] = useState("");

  useEffect(() => {
    if (open) setFilter("");
  }, [open]);

  const filtered = useMemo(() => {
    const q = normalizeFilter(filter);
    if (!q) return [...options];
    return options.filter((o) => o.path.toLowerCase().includes(q) || o.label.toLowerCase().includes(q));
  }, [options, filter]);

  if (!open) return null;

  return createPortal(
    <div
      style={overlay}
      role="presentation"
      data-testid="player-active-model-modal-overlay"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !busy) onClose();
      }}
    >
      <div
        style={dialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        data-testid="player-active-model-modal"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h2 id={titleId} style={title}>
          Set game active model
        </h2>
        <p style={hint}>Search by path or label. Only allowlisted paths from the registry index and player exports are listed.</p>
        <label htmlFor={filterId} style={{ fontSize: 11, color: "#9d9d9d" }}>
          Filter
        </label>
        <input
          id={filterId}
          type="search"
          style={textInput}
          value={filter}
          placeholder="e.g. player_slime or blobert"
          disabled={busy}
          onChange={(e) => setFilter(e.target.value)}
          autoFocus
        />
        {filtered.length === 0 ? (
          <p style={{ color: "#d7ba7d", fontSize: 11, margin: 0 }}>
            No matches. Run a player export or refresh assets after a build.
          </p>
        ) : (
          <div style={listWrap}>
            {filtered.map((o) => {
              const active = currentPath === o.path;
              return (
                <button
                  key={o.path}
                  type="button"
                  style={active ? rowBtnActive : rowBtn}
                  disabled={busy}
                  data-testid={`player-active-model-pick-${encodeURIComponent(o.path)}`}
                  title={o.label}
                  onClick={() => void onPick(o.path)}
                >
                  <span style={{ display: "block", color: "#b5b5b5", fontSize: 10, marginBottom: 2 }}>{o.label}</span>
                  <span>{o.path}</span>
                </button>
              );
            })}
          </div>
        )}
        <div style={btnRow}>
          <button type="button" style={btn} disabled={busy} onClick={onClose}>
            Cancel
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
