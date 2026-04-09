import { useId, type CSSProperties } from "react";
import { createPortal } from "react-dom";
import type { RegistryEnemyVersion } from "../../types";

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
  maxHeight: "min(72vh, 520px)",
  display: "flex",
  flexDirection: "column",
  gap: 10,
  boxShadow: "0 8px 32px rgba(0,0,0,0.45)",
};
const title: CSSProperties = { margin: 0, fontSize: 14, color: "#e0e0e0", fontWeight: 600 };
const btnRow: CSSProperties = { display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end", marginTop: 8 };
const btn: CSSProperties = {
  padding: "6px 14px",
  fontSize: 12,
  borderRadius: 3,
  cursor: "pointer",
  border: "1px solid #555",
  background: "#3c3c3c",
  color: "#d4d4d4",
};
const btnPrimary: CSSProperties = {
  ...btn,
  background: "#0e639c",
  borderColor: "#0e639c",
  color: "#fff",
};
const listWrap: CSSProperties = {
  overflow: "auto",
  flex: 1,
  minHeight: 120,
  border: "1px solid #3c3c3c",
  borderRadius: 4,
  padding: 6,
};
const rowStyle: CSSProperties = {
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "space-between",
  gap: 10,
  padding: "8px 6px",
  borderBottom: "1px solid #2d2d2d",
  fontSize: 11,
};
const mono: CSSProperties = { fontFamily: "ui-monospace, monospace", color: "#d4d4d4", wordBreak: "break-all" };
const hint: CSSProperties = { color: "#8f8f8f", fontSize: 10, margin: 0, lineHeight: 1.4 };

function versionLabel(v: RegistryEnemyVersion): string {
  const n = v.name?.trim();
  return n ? `${v.id} — ${n}` : v.id;
}

export type AddEnemySlotModalProps = {
  open: boolean;
  family: string;
  versions: readonly RegistryEnemyVersion[];
  slotVersionIds: readonly string[];
  preferredVersionId: string | null;
  busy: boolean;
  onClose: () => void;
  onPick: (versionId: string) => void | Promise<void>;
};

export function AddEnemySlotModal({
  open,
  family,
  versions,
  slotVersionIds,
  preferredVersionId,
  busy,
  onClose,
  onPick,
}: AddEnemySlotModalProps) {
  const titleId = useId();
  if (!open) return null;

  const listed = new Set(slotVersionIds);
  const pickable = versions.filter((v) => !v.draft && !listed.has(v.id));
  const ordered = [...pickable].sort((a, b) => {
    if (preferredVersionId) {
      if (a.id === preferredVersionId) return -1;
      if (b.id === preferredVersionId) return 1;
    }
    return a.id.localeCompare(b.id);
  });

  return createPortal(
    <div
      style={overlay}
      role="presentation"
      data-testid="add-enemy-slot-modal-overlay"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !busy) onClose();
      }}
    >
      <div
        style={dialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        data-testid="add-enemy-slot-modal"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h2 id={titleId} style={title}>
          Add spawn slot — {family}
        </h2>
        <p style={hint}>
          Versions already in the slot list are hidden. If a row is not in the spawn pool yet, choosing it turns{" "}
          <strong>In pool</strong> on before you save slots.
        </p>
        {ordered.length === 0 ? (
          <p style={{ color: "#d7ba7d", fontSize: 11, margin: 0 }}>
            No more non-draft versions to add. Export or promote a version, or remove a slot row first.
          </p>
        ) : (
          <div style={listWrap}>
            {ordered.map((v) => (
              <div key={v.id} style={rowStyle}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={mono}>{versionLabel(v)}</div>
                  <div style={{ ...mono, fontSize: 10, color: "#9d9d9d", marginTop: 4 }}>{v.path}</div>
                  {!v.in_use && (
                    <p style={{ ...hint, marginTop: 6, color: "#d7ba7d" }}>Not in pool — will enable when added</p>
                  )}
                </div>
                <button
                  type="button"
                  style={btnPrimary}
                  disabled={busy}
                  data-testid={`registry-add-slot-pick-${v.id}`}
                  onClick={() => void onPick(v.id)}
                >
                  Add
                </button>
              </div>
            ))}
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
