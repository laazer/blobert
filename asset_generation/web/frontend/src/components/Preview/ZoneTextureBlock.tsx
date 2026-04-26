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

/** Normalize color mode (single | gradient). Falls back to old texture_mode="gradient" for backward compat. */
export function normalizedColorMode(
  zone: string,
  values: Readonly<Record<string, unknown>>,
): "single" | "gradient" {
  const colorModeKey = `feat_${zone}_color_mode`;
  const raw = values[colorModeKey];
  if (typeof raw === "string" && (raw === "single" || raw === "gradient")) {
    return raw;
  }
  // Fallback: if old texture_mode is "gradient" and color_mode not set, treat as gradient
  const textureMode = normalizedTextureMode(zone, values);
  return textureMode === "gradient" ? "gradient" : "single";
}

/**
 * When switching ``color_mode``, preserve color values across transitions (single ↔ gradient).
 * Ensures users do not lose work when toggling between single color and gradient modes.
 */
export function carryColorPaletteOnModeChange(
  zone: string,
  prevMode: "single" | "gradient",
  nextMode: "single" | "gradient",
  values: Readonly<Record<string, unknown>>,
): Record<string, unknown> {
  if (prevMode === nextMode) return {};
  const p = `feat_${zone}_color_`;
  const g = (k: string) => values[k];
  const out: Record<string, unknown> = {};

  // When switching to single, preserve a hex value (prefer _a if present, else fallback)
  if (nextMode === "single") {
    const existingHex = g(`${p}hex`);
    if (!existingHex || (typeof existingHex === "string" && existingHex.trim() === "")) {
      // Fallback: prefer new color_a, then old texture_grad_color_a, then default red
      const fallback =
        (typeof g(`${p}a`) === "string" ? g(`${p}a`) : undefined) ||
        (typeof g(`feat_${zone}_texture_grad_color_a`) === "string" ? g(`feat_${zone}_texture_grad_color_a`) : undefined) ||
        "ff0000";
      out[`${p}hex`] = fallback;
    }
  }
  // When switching to gradient, preserve color values (or use defaults)
  else if (nextMode === "gradient") {
    const existingA = g(`${p}a`);
    const existingB = g(`${p}b`);
    const fallbackHex = (typeof g(`${p}hex`) === "string" ? g(`${p}hex`) : undefined) || "ff0000";
    if (!existingA || (typeof existingA === "string" && existingA.trim() === "")) {
      out[`${p}a`] = fallbackHex;
    }
    if (!existingB || (typeof existingB === "string" && existingB.trim() === "")) {
      out[`${p}b`] = "0000ff";
    }
  }
  return out;
}

/** Whether a ``feat_*_*`` param applies to the current modes (color_mode and texture_mode). */
function shouldShowTextureParam(
  zone: string,
  defKey: string | null | undefined,
  values: Readonly<Record<string, unknown>>,
): boolean {
  if (!defKey) return false;

  // Color mode controls (new)
  const colorModeKey = `feat_${zone}_color_mode`;
  if (defKey === colorModeKey) return true;
  const colorMode = normalizedColorMode(zone, values);
  if (defKey.includes("_color_")) {
    // Show single color hex only when color_mode is "single"
    if (defKey === `feat_${zone}_color_hex`) return colorMode === "single";
    // Show gradient colors and direction only when color_mode is "gradient"
    if (
      defKey.includes("_color_a") ||
      defKey.includes("_color_b") ||
      defKey.includes("_color_direction")
    ) {
      return colorMode === "gradient";
    }
  }

  // Texture mode controls (existing)
  const textureMode = normalizedTextureMode(zone, values);
  const textureModeKey = `feat_${zone}_texture_mode`;
  if (defKey === textureModeKey) return true;
  if (defKey.includes("_texture_grad_")) return textureMode === "gradient";
  if (defKey.includes("_texture_spot_")) return textureMode === "spots" || textureMode === "checkerboard";
  if (defKey.includes("_texture_stripe_")) return textureMode === "stripes";
  if (defKey.includes("_texture_asset_")) return textureMode === "assets";
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

  // Color mode (NEW independent selector)
  const colorModeKey = `feat_${zone}_color_mode`;
  const colorHexKey = `feat_${zone}_color_hex`;
  const colorAKey = `feat_${zone}_color_a`;
  const colorBKey = `feat_${zone}_color_b`;
  const colorDirKey = `feat_${zone}_color_direction`;
  const colorMode = normalizedColorMode(zone, values);

  // Texture mode (pattern overlay)
  const textureModeKey = `feat_${zone}_texture_mode`;
  const textureMode = normalizedTextureMode(zone, values);

  // Base finish/hex controls
  const finishKey = `feat_${zone}_finish`;
  const hexKey = `feat_${zone}_hex`;

  // Construct color picker value based on current color_mode
  const colorPickerValue: ColorPickerValue =
    colorMode === "gradient"
      ? {
          type: "gradient",
          colorA: typeof values[colorAKey] === "string" ? values[colorAKey] : "",
          colorB: typeof values[colorBKey] === "string" ? values[colorBKey] : "",
          direction: gradientDirectionFromStore(values[colorDirKey]),
        }
      : {
          type: "single",
          color: typeof values[colorHexKey] === "string" ? values[colorHexKey] : "",
        };

  const modeDef = defs.find((d) => d.key === textureModeKey);
  const nonFloat = defs.filter((d) => d.type !== "float" && d.key !== textureModeKey && d.key !== colorModeKey);
  const visibleNonFloat = nonFloat.filter((d) => shouldShowTextureParam(zone, d.key, values));

  // Old gradient bundle keys (for backward compat filtering)
  const gradColorAKey = `feat_${zone}_texture_grad_color_a`;
  const gradColorBKey = `feat_${zone}_texture_grad_color_b`;
  const gradDirKey = `feat_${zone}_texture_grad_direction`;
  const isGradientBundleKey = (k: string) =>
    k === gradColorAKey || k === gradColorBKey || k === gradDirKey;

  // Filter out old gradient keys from visible rows (they're now in color picker)
  const visibleNonFloatRows =
    textureMode === "gradient"
      ? visibleNonFloat.filter((d) => !isGradientBundleKey(d.key))
      : visibleNonFloat;

  const finishDefsOrdered = finishHexDefs.filter((d) => d.key === finishKey);
  const hexDefsOrdered = finishHexDefs.filter((d) => d.key === hexKey);
  const orphanFinishHex = finishHexDefs.filter((d) => d.key !== finishKey && d.key !== hexKey);

  // Show base hex only when texture_mode is "none" (no pattern overlay)
  const showBaseHex = textureMode === "none";

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
        Surface &amp; color — {partTitle}
      </span>
      <p style={{ color: "#8f8f8f", fontSize: 11, margin: 0, lineHeight: 1.4 }}>
        Choose <strong style={{ color: "#bbb" }}>color mode</strong> first (single or gradient). Then optionally add a <strong style={{ color: "#bbb" }}>pattern</strong> overlay.
        Both are independent. Values apply when you regenerate the asset.
      </p>

      {/* Color picker (independent, always visible) */}
      <ColorPickerUniversal
        mode={colorPickerValue.type}
        value={colorPickerValue}
        onModeChange={(newColorMode) => {
          // Handle color mode transition (single ↔ gradient)
          const carry = carryColorPaletteOnModeChange(zone, colorMode, newColorMode as "single" | "gradient", values);
          setAnimatedBuildOption(slug, colorModeKey, newColorMode);
          if (Object.keys(carry).length > 0) {
            applyAnimatedBuildOptionsForSlug(slug, carry);
          }
        }}
        onChange={(v) => {
          // Handle color value changes within current mode
          if (v.type === "single") {
            setAnimatedBuildOption(slug, colorHexKey, v.color);
          } else if (v.type === "gradient") {
            setAnimatedBuildOption(slug, colorAKey, v.colorA);
            setAnimatedBuildOption(slug, colorBKey, v.colorB);
            setAnimatedBuildOption(slug, colorDirKey, v.direction);
          }
          // Image mode not currently used in texture controls
        }}
      />

      {/* Texture mode selector (independent) */}
      {modeSelectDef ? (
        <ControlRow
          key={textureModeKey}
          def={modeSelectDef}
          value={values[textureModeKey]}
          onChange={(v: number | string | boolean) => {
            if (typeof v !== "string") {
              setAnimatedBuildOption(slug, textureModeKey, v);
              return;
            }
            const nextMode = normalizedTextureMode(zone, { ...values, [textureModeKey]: v });
            const carry = carryTexturePaletteOnModeChange(zone, textureMode, nextMode, values);
            if (Object.keys(carry).length === 0) {
              setAnimatedBuildOption(slug, textureModeKey, v);
            } else {
              applyAnimatedBuildOptionsForSlug(slug, { [textureModeKey]: v, ...carry });
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
      {visibleNonFloatRows.map((def) => (
        <ControlRow
          key={def.key}
          def={def}
          value={values[def.key]}
          onChange={(v: number | string | boolean) => setAnimatedBuildOption(slug, def.key, v)}
        />
      ))}
      {textureMode === "assets" && (
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
