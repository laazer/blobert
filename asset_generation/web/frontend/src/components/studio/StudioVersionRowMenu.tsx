import type { CSSProperties } from "react";
import type { VersionPoolKind } from "../../utils/studioVersionUi";
import { STUDIO_INK_PRIMARY } from "../../styles/studioTokens";

type MenuItem = {
  label: string;
  glyph: string;
  run: () => void;
  disabled?: boolean;
  danger?: boolean;
};

type Props = {
  poolKind: VersionPoolKind;
  onClose: () => void;
  onDuplicate: () => void;
  onCompare: () => void;
  onTogglePool: () => void;
  onDelete: () => void;
  canDelete: boolean;
};

const overlay: CSSProperties = {
  position: "fixed",
  inset: 0,
  zIndex: 4,
  background: "transparent",
};

const panel: CSSProperties = {
  position: "absolute",
  top: 36,
  right: 10,
  zIndex: 5,
  background: "#1d1d26",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 8,
  padding: 4,
  minWidth: 168,
  boxShadow: "0 12px 32px rgba(0,0,0,0.5)",
};

const itemBtn: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  width: "100%",
  padding: "7px 9px",
  borderRadius: 5,
  border: 0,
  background: "transparent",
  color: STUDIO_INK_PRIMARY,
  fontSize: 12,
  fontWeight: 500,
  cursor: "pointer",
  textAlign: "left",
};

export function StudioVersionRowMenu({
  poolKind,
  onClose,
  onDuplicate,
  onCompare,
  onTogglePool,
  onDelete,
  canDelete,
}: Props) {
  const promoteLabel = poolKind === "pool" ? "Move to draft" : "Promote to pool";
  const promoteGlyph = poolKind === "pool" ? "↓" : "↑";

  const items: MenuItem[] = [
    { label: "Duplicate", glyph: "⧉", run: onDuplicate, disabled: true },
    { label: "Compare with…", glyph: "▥", run: onCompare },
    { label: promoteLabel, glyph: promoteGlyph, run: onTogglePool },
    { label: "Delete", glyph: "✕", run: onDelete, disabled: !canDelete, danger: true },
  ];

  return (
    <>
      <div role="presentation" onClick={onClose} style={overlay} />
      <div role="menu" style={panel} data-testid="studio-version-row-menu">
        {items.map((opt) => (
          <button
            key={opt.label}
            type="button"
            role="menuitem"
            disabled={opt.disabled}
            title={opt.disabled && opt.label === "Duplicate" ? "Duplicate API coming soon" : undefined}
            style={{
              ...itemBtn,
              color: opt.danger ? "#f48771" : STUDIO_INK_PRIMARY,
              opacity: opt.disabled ? 0.45 : 1,
              cursor: opt.disabled ? "not-allowed" : "pointer",
            }}
            onClick={() => {
              if (opt.disabled) return;
              opt.run();
            }}
          >
            <span style={{ width: 14, textAlign: "center", opacity: 0.7 }}>{opt.glyph}</span>
            {opt.label}
          </button>
        ))}
      </div>
    </>
  );
}
