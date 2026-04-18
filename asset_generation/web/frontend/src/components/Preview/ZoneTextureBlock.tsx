import { useState } from "react";
import { useAppStore } from "../../store/useAppStore";
import type { AnimatedBuildControlDef } from "../../types";
import { ControlRow, FloatControlsTable } from "./BuildControlRow";

const meshFloatScrollWrap = {
  flex: 1,
  minHeight: 0,
  overflowY: "auto" as const,
  overflowX: "auto" as const,
  minWidth: 0,
  maxWidth: "100%",
  paddingTop: 2,
};

const sectionHeaderRow = {
  display: "flex",
  alignItems: "center",
  gap: 10,
  flexWrap: "wrap" as const,
};

const sectionTitle = { color: "#9d9d9d", fontSize: 11, fontWeight: 600 } as const;

const filterInput = {
  background: "#2d2d2d",
  color: "#d4d4d4",
  border: "1px solid #555",
  borderRadius: 3,
  padding: "2px 6px",
  fontSize: 11,
  width: 128,
  flex: "0 0 auto",
};

/** Human label for material zone keys (e.g. ``body`` → "Body", ``eye_left`` → "Eye Left"). */
export function zonePartDisplayName(zone: string): string {
  return zone
    .split("_")
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");
}

function normalizedTextureMode(
  zone: string,
  values: Readonly<Record<string, unknown>>,
): "none" | "gradient" | "spots" | "stripes" {
  const modeKey = `feat_${zone}_texture_mode`;
  const rawMode = values[modeKey];
  const textureMode = typeof rawMode === "string" ? rawMode.trim().toLowerCase() : "none";
  if (
    textureMode === "gradient" ||
    textureMode === "spots" ||
    textureMode === "stripes" ||
    textureMode === "none"
  ) {
    return textureMode;
  }
  return "none";
}

/** Whether a ``feat_*_texture_*`` param applies to the current mode (non-mode keys only). */
function shouldShowTextureParam(
  zone: string,
  defKey: string,
  values: Readonly<Record<string, unknown>>,
): boolean {
  const modeKey = `feat_${zone}_texture_mode`;
  if (defKey === modeKey) return true;
  const mode = normalizedTextureMode(zone, values);
  if (defKey.includes("_texture_grad_")) return mode === "gradient";
  if (defKey.includes("_texture_spot_")) return mode === "spots";
  if (defKey.includes("_texture_stripe_")) return mode === "stripes";
  return false;
}

type Props = {
  zone: string;
  slug: string;
  defs: readonly AnimatedBuildControlDef[];
  /** Per-zone finish + hex (``feat_{zone}_finish`` / ``feat_{zone}_hex``). */
  finishHexDefs?: readonly AnimatedBuildControlDef[];
};

/**
 * Per-zone surface: texture mode first, then base finish/hex when mode is ``none``, else pattern colors for the selected mode.
 * Preview shows the loaded GLB; values apply on regeneration.
 */
export function ZoneTextureBlock({ zone, slug, defs, finishHexDefs = [] }: Props) {
  const animatedBuildOptionValues = useAppStore((st) => st.animatedBuildOptionValues);
  const setAnimatedBuildOption = useAppStore((st) => st.setAnimatedBuildOption);

  const [textureFloatFilter, setTextureFloatFilter] = useState("");

  if (defs.length === 0 && finishHexDefs.length === 0) return null;

  const values = animatedBuildOptionValues[slug] ?? {};
  const modeKey = `feat_${zone}_texture_mode`;
  const finishKey = `feat_${zone}_finish`;
  const hexKey = `feat_${zone}_hex`;
  const mode = normalizedTextureMode(zone, values);

  const modeDef = defs.find((d) => d.key === modeKey);
  const nonFloat = defs.filter((d) => d.type !== "float" && d.key !== modeKey);
  const visibleNonFloat = nonFloat.filter((d) => shouldShowTextureParam(zone, d.key, values));

  const finishDefsOrdered = finishHexDefs.filter((d) => d.key === finishKey);
  const hexDefsOrdered = finishHexDefs.filter((d) => d.key === hexKey);
  const orphanFinishHex = finishHexDefs.filter((d) => d.key !== finishKey && d.key !== hexKey);

  const showBaseHex = mode === "none";

  const textureFloats = defs.filter((d) => d.type === "float");
  const textureFloatsVisible = textureFloats.filter((d) => shouldShowTextureParam(zone, d.key, values));
  const tfq = textureFloatFilter.trim().toLowerCase();
  const textureFloatFiltered = tfq
    ? textureFloatsVisible.filter(
        (d) => d.key.toLowerCase().includes(tfq) || d.label.toLowerCase().includes(tfq),
      )
    : textureFloatsVisible;

  const row = (def: AnimatedBuildControlDef) => (
    <ControlRow
      key={def.key}
      def={def}
      value={values[def.key]}
      onChange={(v: number | string | boolean) => setAnimatedBuildOption(slug, def.key, v)}
    />
  );

  const modeSelectDef: AnimatedBuildControlDef | undefined =
    modeDef && modeDef.type === "select_str"
      ? { ...modeDef, options: modeDef.options.filter((o) => o !== "custom") }
      : modeDef;

  const partTitle = zonePartDisplayName(zone);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 8,
        marginTop: 6,
        paddingTop: 8,
        borderTop: "1px solid #2d2d2d",
      }}
    >
      <span style={sectionTitle}>
        Surface &amp; pattern — {partTitle}
      </span>
      <p style={{ color: "#8f8f8f", fontSize: 11, margin: 0, lineHeight: 1.4 }}>
        Choose <strong style={{ color: "#bbb" }}>texture mode</strong> first. With <strong style={{ color: "#bbb" }}>no pattern</strong>, set
        finish and base hex; with a pattern mode, set that mode&apos;s colors. Values apply when you regenerate the asset.
      </p>
      {modeSelectDef ? (
        <ControlRow
          key={modeKey}
          def={modeSelectDef}
          value={values[modeKey]}
          onChange={(v: number | string | boolean) => setAnimatedBuildOption(slug, modeKey, v)}
        />
      ) : null}
      {finishDefsOrdered.map(row)}
      {showBaseHex ? (
        <>
          {hexDefsOrdered.map(row)}
          {orphanFinishHex.map(row)}
        </>
      ) : null}
      {visibleNonFloat.map((def) => (
        <ControlRow
          key={def.key}
          def={def}
          value={values[def.key]}
          onChange={(v: number | string | boolean) => setAnimatedBuildOption(slug, def.key, v)}
        />
      ))}
      {textureFloatsVisible.length > 0 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 2, flex: 1, minHeight: 0 }}>
          <div style={sectionHeaderRow}>
            <span style={sectionTitle}>Pattern parameters — {partTitle}</span>
            <input
              type="search"
              placeholder="Filter…"
              aria-label="Filter pattern numeric parameters"
              value={textureFloatFilter}
              onChange={(e) => setTextureFloatFilter(e.target.value)}
              style={filterInput}
            />
          </div>
          <FloatControlsTable
            defs={textureFloatFiltered}
            values={values}
            scrollWrapStyle={meshFloatScrollWrap}
            onFloatChange={(key, v) => setAnimatedBuildOption(slug, key, v)}
            isRowDisabled={() => false}
          />
        </div>
      ) : null}
    </div>
  );
}
