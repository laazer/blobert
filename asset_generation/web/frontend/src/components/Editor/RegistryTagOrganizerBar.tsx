import type { CSSProperties } from "react";
import { titleCaseSnake } from "../../utils/enemyDisplay";
import { centerPanelTabBtnStyle } from "../layout/centerPanelTabStyles";

const bar: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 8,
  marginBottom: 10,
  padding: "8px 10px",
  border: "1px solid #3c3c3c",
  borderRadius: 4,
  background: "#1e1e1e",
};
const row: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: 6,
  alignItems: "center",
};
const label: CSSProperties = { fontSize: 10, color: "#888", flexShrink: 0 };
const selectStyle: CSSProperties = {
  fontSize: 10,
  color: "#d4d4d4",
  background: "#252526",
  border: "1px solid #555",
  borderRadius: 3,
  padding: "3px 6px",
  maxWidth: "100%",
};

export type RegistryTagOrganizerBarProps = {
  catalog: readonly string[];
  filterTags: ReadonlySet<string>;
  groupByTag: string | null;
  onToggleFilter: (tag: string) => void;
  onClearFilters: () => void;
  onGroupByChange: (tag: string | null) => void;
};

export function RegistryTagOrganizerBar({
  catalog,
  filterTags,
  groupByTag,
  onToggleFilter,
  onClearFilters,
  onGroupByChange,
}: RegistryTagOrganizerBarProps) {
  const filterable = catalog.filter((t) => t !== groupByTag);

  return (
    <div style={bar} data-testid="registry-tag-organizer">
      <div style={row}>
        <span style={label}>Filter families</span>
        {filterable.length === 0 ? (
          <span style={{ fontSize: 10, color: "#666" }}>No tags yet</span>
        ) : (
          filterable.map((tag) => {
            const active = filterTags.has(tag);
            return (
              <button
                key={tag}
                type="button"
                style={centerPanelTabBtnStyle(active)}
                aria-pressed={active}
                data-testid={`registry-tag-filter-${tag}`}
                onClick={() => onToggleFilter(tag)}
              >
                {titleCaseSnake(tag)}
              </button>
            );
          })
        )}
        {filterTags.size > 0 ? (
          <button type="button" style={centerPanelTabBtnStyle(false)} onClick={onClearFilters}>
            Clear
          </button>
        ) : null}
      </div>
      <div style={row}>
        <label style={label} htmlFor="registry-tag-group-by">
          Group tabs by
        </label>
        <select
          id="registry-tag-group-by"
          style={selectStyle}
          value={groupByTag ?? ""}
          data-testid="registry-tag-group-by"
          onChange={(e) => onGroupByChange(e.target.value === "" ? null : e.target.value)}
        >
          <option value="">None</option>
          {catalog.map((tag) => (
            <option key={tag} value={tag}>
              {titleCaseSnake(tag)}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
