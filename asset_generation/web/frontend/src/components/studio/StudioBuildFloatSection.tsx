import { useMemo, useState, type CSSProperties } from "react";
import type { AnimatedBuildControlDef } from "../../types";
import { StudioPanelHead } from "./StudioPanelHead";
import { studioBuildFilterInput } from "./studioBuildStyles";
import { StudioBuildSlider } from "./StudioBuildSlider";

type Props = {
  title: string;
  subtitle?: string;
  /** v2 Build tab: section title only (e.g. Pattern parameters). */
  titleOnly?: boolean;
  /** When parent provides a summary (e.g. details), omit duplicate section head. */
  hideHead?: boolean;
  defs: Extract<AnimatedBuildControlDef, { type: "float" }>[];
  values: Readonly<Record<string, unknown>>;
  accentHue: string;
  filterPlaceholder: string;
  filterAria: string;
  onFloatChange: (key: string, v: number) => void;
  isRowDisabled: (key: string) => boolean;
};

const listStyle: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 0,
  maxHeight: 320,
  overflowY: "auto",
  paddingRight: 2,
};

export function StudioBuildFloatSection({
  title,
  subtitle,
  titleOnly = false,
  hideHead = false,
  defs,
  values,
  accentHue,
  filterPlaceholder,
  filterAria,
  onFloatChange,
  isRowDisabled,
}: Props) {
  const [filter, setFilter] = useState("");
  const q = filter.trim().toLowerCase();

  const filtered = useMemo(
    () =>
      q
        ? defs.filter(
            (d) => d.key.toLowerCase().includes(q) || d.label.toLowerCase().includes(q),
          )
        : defs,
    [defs, q],
  );

  if (defs.length === 0) return null;

  return (
    <div style={{ marginTop: titleOnly ? 6 : 0 }} data-testid={`studio-build-float-section-${title.toLowerCase().replace(/\s+/g, "-")}`}>
      {!hideHead ? <StudioPanelHead title={title} subtitle={titleOnly ? undefined : subtitle} /> : null}
      {defs.length > 6 ? (
        <input
          type="search"
          placeholder={filterPlaceholder}
          aria-label={filterAria}
          value={filter}
          style={studioBuildFilterInput}
          onChange={(e) => setFilter(e.target.value)}
        />
      ) : null}
      <div style={listStyle}>
        {filtered.map((def) => (
          <StudioBuildSlider
            key={def.key}
            def={def}
            value={values[def.key]}
            accentHue={accentHue}
            disabled={isRowDisabled(def.key)}
            showHint={false}
            onChange={(v) => onFloatChange(def.key, v)}
          />
        ))}
      </div>
    </div>
  );
}
