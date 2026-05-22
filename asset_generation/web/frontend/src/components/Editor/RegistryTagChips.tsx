import type { CSSProperties } from "react";
import { titleCaseSnake } from "../../utils/enemyDisplay";

const chip: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 4,
  padding: "1px 6px",
  fontSize: 10,
  borderRadius: 3,
  border: "1px solid #444",
  background: "#2a2a2a",
  color: "#b5b5b5",
  lineHeight: 1.35,
  maxWidth: "100%",
};
const chipFamily: CSSProperties = {
  ...chip,
  borderColor: "#0e639c",
  color: "#9cdcfe",
  background: "#1a2a3a",
};
const chipRemovable: CSSProperties = {
  ...chip,
  paddingRight: 2,
};
const removeBtn: CSSProperties = {
  border: "none",
  background: "transparent",
  color: "#888",
  cursor: "pointer",
  fontSize: 12,
  lineHeight: 1,
  padding: "0 2px",
};

export type RegistryTagChipsProps = {
  tags: readonly string[];
  family: string;
  onRemove?: (tag: string) => void;
  disabled?: boolean;
};

export function RegistryTagChips({ tags, family, onRemove, disabled }: RegistryTagChipsProps) {
  if (tags.length === 0) {
    return <span style={{ fontSize: 10, color: "#666" }}>—</span>;
  }
  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: 4,
        alignItems: "center",
        minWidth: 0,
      }}
    >
      {tags.map((tag) => {
        const isFamily = tag === family;
        const removable = onRemove != null && !isFamily && !disabled;
        return (
          <span
            key={tag}
            style={removable ? chipRemovable : isFamily ? chipFamily : chip}
            title={tag}
            data-testid={`registry-tag-chip-${tag}`}
          >
            {titleCaseSnake(tag)}
            {removable ? (
              <button
                type="button"
                style={removeBtn}
                aria-label={`Remove tag ${tag}`}
                disabled={disabled}
                onClick={() => onRemove(tag)}
              >
                ×
              </button>
            ) : null}
          </span>
        );
      })}
    </div>
  );
}
