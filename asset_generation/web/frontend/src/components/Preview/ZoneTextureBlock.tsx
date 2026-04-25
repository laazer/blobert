import { useEffect, useState } from "react";
import { useAppStore } from "../../store/useAppStore";
import type { AnimatedBuildControlDef } from "../../types";
import type { GradientDirection } from "../ColorPicker/common/DirectionSelector";
import { ColorPickerUniversal, type ColorPickerValue } from "../ColorPicker/ColorPickerUniversal";
import { ControlRow, FloatControlsTable } from "./BuildControlRow";
import { fetchTextureAssets, type TextureAsset } from "../../api/client";

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

function gradientDirectionFromStore(raw: unknown): GradientDirection {
  const s = typeof raw === "string" ? raw.trim().toLowerCase() : "";
  if (s === "vertical" || s === "radial" || s === "horizontal") return s;
  return "horizontal";
}

function textureColorEmpty(v: unknown): boolean {
  if (v === undefined || v === null) return true;
  return typeof v === "string" && v.trim() === "";
}

function firstNonEmptyString(...vals: unknown[]): string {
  for (const v of vals) {
    if (typeof v === "string" && v.trim() !== "") return v.trim();
  }
  return "";
}

/**
 * When switching ``texture_mode``, copy palette colors into the new mode's fields if they are still empty
 * so users do not lose work across gradient / spots / checkerboard / stripes.
 */
export function carryTexturePaletteOnModeChange(
  zone: string,
  prevMode: ReturnType<typeof normalizedTextureMode>,
  nextMode: ReturnType<typeof normalizedTextureMode>,
  values: Readonly<Record<string, unknown>>,
): Record<string, unknown> {
  if (prevMode === nextMode) return {};
  const p = `feat_${zone}_texture_`;
  const g = (k: string) => values[k];
  const out: Record<string, unknown> = {};

  const setIfEmpty = (key: string, ...candidates: unknown[]) => {
    if (!textureColorEmpty(g(key))) return;
    const s = firstNonEmptyString(...candidates);
    if (s) out[key] = s;
  };

  if (nextMode === "gradient") {
    setIfEmpty(`${p}grad_color_a`, g(`${p}spot_color`), g(`${p}stripe_color`));
    setIfEmpty(`${p}grad_color_b`, g(`${p}spot_bg_color`), g(`${p}stripe_bg_color`));
  } else if (nextMode === "spots" || nextMode === "checkerboard") {
    setIfEmpty(`${p}spot_color`, g(`${p}grad_color_a`), g(`${p}stripe_color`));
    setIfEmpty(`${p}spot_bg_color`, g(`${p}grad_color_b`), g(`${p}stripe_bg_color`));
  } else if (nextMode === "stripes") {
    setIfEmpty(`${p}stripe_color`, g(`${p}grad_color_a`), g(`${p}spot_color`));
    setIfEmpty(`${p}stripe_bg_color`, g(`${p}grad_color_b`), g(`${p}spot_bg_color`));
  }
  return out;
}

export function normalizedTextureMode(
  zone: string,
  values: Readonly<Record<string, unknown>>,
): "none" | "gradient" | "spots" | "checkerboard" | "stripes" | "assets" {
  const modeKey = `feat_${zone}_texture_mode`;
  const rawMode = values[modeKey];
  const textureMode = typeof rawMode === "string" ? rawMode.trim().toLowerCase() : "none";
  if (
    textureMode === "gradient" ||
    textureMode === "spots" ||
    textureMode === "checkerboard" ||
    textureMode === "stripes" ||
    textureMode === "assets" ||
    textureMode === "none"
  ) {
    return textureMode;
  }
  return "none";
}

/** Whether a ``feat_*_texture_*`` param applies to the current mode (non-mode keys only). */
function shouldShowTextureParam(
  zone: string,
  defKey: string | null | undefined,
  values: Readonly<Record<string, unknown>>,
): boolean {
  if (!defKey) return false;
  const modeKey = `feat_${zone}_texture_mode`;
  if (defKey === modeKey) return true;
  const mode = normalizedTextureMode(zone, values);
  if (defKey.includes("_texture_grad_")) return mode === "gradient";
  if (defKey.includes("_texture_spot_")) return mode === "spots" || mode === "checkerboard";
  if (defKey.includes("_texture_stripe_")) return mode === "stripes";
  if (defKey.includes("_texture_asset_")) return mode === "assets";
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
  const applyAnimatedBuildOptionsForSlug = useAppStore((st) => st.applyAnimatedBuildOptionsForSlug);

  const [textureFloatFilter, setTextureFloatFilter] = useState("");
  const [textureAssets, setTextureAssets] = useState<TextureAsset[]>([]);

  useEffect(() => {
    fetchTextureAssets()
      .then(setTextureAssets)
      .catch((err) => console.error("Failed to fetch texture assets:", err));
  }, []);

  if (defs.length === 0 && finishHexDefs.length === 0) return null;

  const values = animatedBuildOptionValues[slug] ?? {};
  const modeKey = `feat_${zone}_texture_mode`;
  const finishKey = `feat_${zone}_finish`;
  const hexKey = `feat_${zone}_hex`;
  const mode = normalizedTextureMode(zone, values);

  const modeDef = defs.find((d) => d.key === modeKey);
  const nonFloat = defs.filter((d) => d.type !== "float" && d.key !== modeKey);
  const visibleNonFloat = nonFloat.filter((d) => shouldShowTextureParam(zone, d.key, values));

  const gradColorAKey = `feat_${zone}_texture_grad_color_a`;
  const gradColorBKey = `feat_${zone}_texture_grad_color_b`;
  const gradDirKey = `feat_${zone}_texture_grad_direction`;
  const isGradientBundleKey = (k: string) =>
    k === gradColorAKey || k === gradColorBKey || k === gradDirKey;

  const visibleNonFloatRows =
    mode === "gradient"
      ? visibleNonFloat.filter((d) => !isGradientBundleKey(d.key))
      : visibleNonFloat;

  const gradientPickerValue: ColorPickerValue | null =
    mode === "gradient"
      ? {
          type: "gradient",
          colorA: typeof values[gradColorAKey] === "string" ? values[gradColorAKey] : "",
          colorB: typeof values[gradColorBKey] === "string" ? values[gradColorBKey] : "",
          direction: gradientDirectionFromStore(values[gradDirKey]),
        }
      : null;

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
          onChange={(v: number | string | boolean) => {
            if (typeof v !== "string") {
              setAnimatedBuildOption(slug, modeKey, v);
              return;
            }
            const nextMode = normalizedTextureMode(zone, { ...values, [modeKey]: v });
            const carry = carryTexturePaletteOnModeChange(zone, mode, nextMode, values);
            if (Object.keys(carry).length === 0) {
              setAnimatedBuildOption(slug, modeKey, v);
            } else {
              applyAnimatedBuildOptionsForSlug(slug, { [modeKey]: v, ...carry });
            }
          }}
        />
      ) : null}
      {finishDefsOrdered.map(row)}
      {showBaseHex ? (
        <>
          {hexDefsOrdered.map(row)}
          {orphanFinishHex.map(row)}
        </>
      ) : null}
      {gradientPickerValue ? (
        <ColorPickerUniversal
          lockMode="gradient"
          mode="gradient"
          label={`Gradient — ${partTitle}`}
          value={gradientPickerValue}
          onModeChange={() => {}}
          onChange={(v) => {
            if (v.type !== "gradient") return;
            setAnimatedBuildOption(slug, gradColorAKey, v.colorA);
            setAnimatedBuildOption(slug, gradColorBKey, v.colorB);
            setAnimatedBuildOption(slug, gradDirKey, v.direction);
          }}
        />
      ) : null}
      {visibleNonFloatRows.map((def) => (
        <ControlRow
          key={def.key}
          def={def}
          value={values[def.key]}
          onChange={(v: number | string | boolean) => setAnimatedBuildOption(slug, def.key, v)}
        />
      ))}
      {mode === "assets" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div>
            <label style={{ display: "block", fontSize: 11, color: "#9d9d9d", marginBottom: 4 }}>
              Asset texture
            </label>
            <select
              value={String(values[`feat_${zone}_texture_asset_id`] ?? "")}
              onChange={(e) => setAnimatedBuildOption(slug, `feat_${zone}_texture_asset_id`, e.target.value)}
              style={{
                width: "100%",
                padding: "4px 6px",
                backgroundColor: "#2d2d2d",
                color: "#d4d4d4",
                border: "1px solid #555",
                borderRadius: 3,
                fontSize: 11,
              }}
            >
              <option value="">Select a texture...</option>
              {textureAssets.map((asset) => (
                <option key={asset.id} value={asset.id}>
                  {asset.display_name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ display: "block", fontSize: 11, color: "#9d9d9d", marginBottom: 4 }}>
              Tile repeat
            </label>
            <input
              type="number"
              min="0.5"
              max="8.0"
              step="0.5"
              value={Number(values[`feat_${zone}_texture_asset_tile_repeat`] ?? 1.0)}
              onChange={(e) => setAnimatedBuildOption(slug, `feat_${zone}_texture_asset_tile_repeat`, parseFloat(e.target.value))}
              style={{
                width: "100%",
                padding: "4px 6px",
                backgroundColor: "#2d2d2d",
                color: "#d4d4d4",
                border: "1px solid #555",
                borderRadius: 3,
                fontSize: 11,
              }}
            />
          </div>
        </div>
      )}
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
