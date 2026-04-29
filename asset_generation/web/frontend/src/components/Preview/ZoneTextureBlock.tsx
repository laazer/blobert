import { useEffect, useState } from "react";
import { useAppStore } from "../../store/useAppStore";
import type { AnimatedBuildControlDef } from "../../types";
import type { GradientDirection } from "../ColorPicker/common/DirectionSelector";
import { ColorPickerTabs, type ColorPickerValue } from "../ColorPicker/ColorPickerTabs";
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

type PickerMode = "single" | "gradient" | "image";

type ColorFieldKeys = {
  hexKey: string;
  colorAKey: string;
  colorBKey: string;
  colorDirKey: string;
  imageIdKey: string;
  imagePreviewKey: string;
  legacySingleKey?: string;
};

function buildColorPickerValue(
  mode: PickerMode,
  values: Readonly<Record<string, unknown>>,
  keys: ColorFieldKeys,
): ColorPickerValue {
  const singleColor =
    typeof values[keys.hexKey] === "string"
      ? values[keys.hexKey]
      : keys.legacySingleKey && typeof values[keys.legacySingleKey] === "string"
        ? values[keys.legacySingleKey]
        : "";
  if (mode === "gradient") {
    return {
      type: "gradient",
      colorA: typeof values[keys.colorAKey] === "string" ? values[keys.colorAKey] : "",
      colorB: typeof values[keys.colorBKey] === "string" ? values[keys.colorBKey] : "",
      direction: gradientDirectionFromStore(values[keys.colorDirKey]),
    };
  }
  if (mode === "image") {
    return {
      type: "image",
      file: null,
      preview: typeof values[keys.imagePreviewKey] === "string" ? values[keys.imagePreviewKey] : undefined,
    };
  }
  return {
    type: "single",
    color: singleColor,
  };
}

type PaletteCarryKeys = {
  hexKey: string;
  colorAKey: string;
  colorBKey: string;
  legacySingleKey?: string;
};

function carryPaletteBetweenSingleAndGradient(
  prevMode: PickerMode,
  nextMode: PickerMode,
  values: Readonly<Record<string, unknown>>,
  keys: PaletteCarryKeys,
): Record<string, unknown> {
  if (prevMode === nextMode || prevMode === "image" || nextMode === "image") {
    return {};
  }
  const out: Record<string, unknown> = {};
  const existingHex = values[keys.hexKey];
  const existingA = values[keys.colorAKey];
  const existingB = values[keys.colorBKey];
  const legacySingle = keys.legacySingleKey ? values[keys.legacySingleKey] : undefined;

  if (nextMode === "single") {
    if (!existingHex || (typeof existingHex === "string" && existingHex.trim() === "")) {
      const fallback =
        (typeof existingA === "string" ? existingA : undefined) ||
        (typeof legacySingle === "string" ? legacySingle : undefined) ||
        "ff0000";
      out[keys.hexKey] = fallback;
    }
    return out;
  }

  if (nextMode === "gradient") {
    const fallbackHex =
      (typeof existingHex === "string" ? existingHex : undefined) ||
      (typeof legacySingle === "string" ? legacySingle : undefined) ||
      "ff0000";
    if (!existingA || (typeof existingA === "string" && existingA.trim() === "")) {
      out[keys.colorAKey] = fallbackHex;
    }
    if (!existingB || (typeof existingB === "string" && existingB.trim() === "")) {
      out[keys.colorBKey] = "0000ff";
    }
  }
  return out;
}

/**
 * When switching ``texture_mode``, copy palette colors into the new mode's fields if they are still empty
 * so users do not lose work across spots / checkerboard / stripes.
 * (Gradient was moved to color_mode, so it's no longer handled here.)
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

  if (nextMode === "spots" || nextMode === "checkerboard") {
    setIfEmpty(`${p}spot_color`, g(`${p}stripe_color`));
    setIfEmpty(`${p}spot_bg_color`, g(`${p}stripe_bg_color`));
  } else if (nextMode === "stripes") {
    setIfEmpty(`${p}stripe_color`, g(`${p}spot_color`));
    setIfEmpty(`${p}stripe_bg_color`, g(`${p}spot_bg_color`));
  }
  return out;
}

export function normalizedTextureMode(
  zone: string,
  values: Readonly<Record<string, unknown>>,
): "none" | "spots" | "checkerboard" | "stripes" {
  const modeKey = `feat_${zone}_texture_mode`;
  const rawMode = values[modeKey];
  const textureMode = typeof rawMode === "string" ? rawMode.trim().toLowerCase() : "none";
  if (textureMode === "spots" || textureMode === "checkerboard" || textureMode === "stripes" || textureMode === "none") {
    return textureMode;
  }
  // Fallback for old data: if user had gradient or assets, default to none
  return "none";
}

/** Normalize color mode (single | gradient | image). Falls back to old texture_mode="gradient" for backward compat. */
export function normalizedColorMode(
  zone: string,
  values: Readonly<Record<string, unknown>>,
): "single" | "gradient" | "image" {
  const colorModeKey = `feat_${zone}_color_mode`;
  const raw = values[colorModeKey];
  if (typeof raw === "string" && (raw === "single" || raw === "gradient" || raw === "image")) {
    return raw;
  }
  // Fallback: if old texture_mode was "gradient" (now converted to "none" by normalizedTextureMode),
  // check original raw value to detect legacy gradient mode
  const modeKey = `feat_${zone}_texture_mode`;
  const rawMode = values[modeKey];
  const textureMode = typeof rawMode === "string" ? rawMode.trim().toLowerCase() : "";
  return textureMode === "gradient" ? "gradient" : "single";
}

/**
 * When switching ``color_mode``, preserve color values across transitions (single ↔ gradient).
 * Ensures users do not lose work when toggling between single color and gradient modes.
 * (Image mode is handled separately and does not use this function.)
 */
export function carryColorPaletteOnModeChange(
  zone: string,
  prevMode: "single" | "gradient" | "image",
  nextMode: "single" | "gradient" | "image",
  values: Readonly<Record<string, unknown>>,
): Record<string, unknown> {
  const p = `feat_${zone}_color_`;
  return carryPaletteBetweenSingleAndGradient(prevMode, nextMode, values, {
    hexKey: `${p}hex`,
    colorAKey: `${p}a`,
    colorBKey: `${p}b`,
  });
}

/**
 * For a pattern color field (e.g., "spot_color"), return its current mode (single | gradient | image).
 * Falls back to "single" for old data with just one key.
 */
export function normalizedPatternColorMode(
  zone: string,
  colorField: string,
  values: Readonly<Record<string, unknown>>,
): "single" | "gradient" | "image" {
  const modeKey = `feat_${zone}_texture_${colorField}_mode`;
  const raw = values[modeKey];
  if (typeof raw === "string" && (raw === "single" || raw === "gradient" || raw === "image")) {
    return raw;
  }
  // Old data: if only the base key exists, default to single mode
  return "single";
}

/**
 * For a pattern color field, carry palette values when switching modes.
 * Similar to carryColorPaletteOnModeChange but for pattern colors.
 */
export function carryPatternColorPaletteOnModeChange(
  zone: string,
  colorField: string,
  prevMode: "single" | "gradient" | "image",
  nextMode: "single" | "gradient" | "image",
  values: Readonly<Record<string, unknown>>,
): Record<string, unknown> {
  const p = `feat_${zone}_texture_${colorField}_`;
  return carryPaletteBetweenSingleAndGradient(prevMode, nextMode, values, {
    hexKey: `${p}hex`,
    colorAKey: `${p}a`,
    colorBKey: `${p}b`,
    legacySingleKey: `feat_${zone}_texture_${colorField}`,
  });
}

/** Whether a ``feat_*_*`` param applies to the current modes (color_mode and texture_mode). */
function shouldShowTextureParam(
  zone: string,
  defKey: string | null | undefined,
  values: Readonly<Record<string, unknown>>,
): boolean {
  if (!defKey) return false;
  const legacyGradientKeys = new Set([
    `feat_${zone}_texture_grad_color_a`,
    `feat_${zone}_texture_grad_color_b`,
    `feat_${zone}_texture_grad_direction`,
  ]);
  if (legacyGradientKeys.has(defKey)) {
    return false;
  }

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

  // Pattern color mode selectors (spot_color_mode, stripe_color_mode, etc.)
  if (defKey.includes("_texture_") && defKey.endsWith("_mode")) {
    // Show color mode selectors for active patterns
    if (defKey.includes("_spot_") && (textureMode === "spots" || textureMode === "checkerboard")) return true;
    if (defKey.includes("_stripe_") && textureMode === "stripes") return true;
    return false;
  }

  // Pattern fields (spots and checkerboard share pattern settings)
  const isSpotTextureField = defKey.includes("_texture_spot_");
  const isStripeTextureField = defKey.includes("_texture_stripe_");
  const showForSpots = textureMode === "spots" || textureMode === "checkerboard";
  const showForStripes = textureMode === "stripes";

  if (isSpotTextureField) {
    // Color fields are rendered only via renderPatternColorPicker.
    if (defKey === `feat_${zone}_texture_spot_color` || defKey === `feat_${zone}_texture_spot_bg_color`) {
      return showForSpots;
    }
    // Hide image/gradient helper keys from generic rows; picker manages them.
    if (
      defKey.startsWith(`feat_${zone}_texture_spot_color_`) ||
      defKey.startsWith(`feat_${zone}_texture_spot_bg_color_`)
    ) {
      return false;
    }
    // Other fields (density, etc.) are rendered generically
    return showForSpots;
  }

  if (isStripeTextureField) {
    // Color fields are rendered only via renderPatternColorPicker.
    if (defKey === `feat_${zone}_texture_stripe_color` || defKey === `feat_${zone}_texture_stripe_bg_color`) {
      return showForStripes;
    }
    // Hide image/gradient helper keys from generic rows; picker manages them.
    if (
      defKey.startsWith(`feat_${zone}_texture_stripe_color_`) ||
      defKey.startsWith(`feat_${zone}_texture_stripe_bg_color_`)
    ) {
      return false;
    }
    // Other fields (width, etc.)
    return showForStripes;
  }

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

  if (defs.length === 0 && finishHexDefs.length === 0) return null;

  const values = animatedBuildOptionValues[slug] ?? {};

  // Color mode (NEW independent selector)
  const colorModeKey = `feat_${zone}_color_mode`;
  const colorHexKey = `feat_${zone}_color_hex`;
  const colorAKey = `feat_${zone}_color_a`;
  const colorBKey = `feat_${zone}_color_b`;
  const colorDirKey = `feat_${zone}_color_direction`;
  const colorImageIdKey = `feat_${zone}_color_image_id`; // For tracking uploaded image
  const colorImagePreviewKey = `feat_${zone}_color_image_preview`; // For preview URL
  const colorMode = normalizedColorMode(zone, values);

  // Texture mode (pattern overlay)
  const textureModeKey = `feat_${zone}_texture_mode`;
  const textureMode = normalizedTextureMode(zone, values);

  // Base finish/hex controls
  const finishKey = `feat_${zone}_finish`;
  const hexKey = `feat_${zone}_hex`;

  const baseColorKeys: ColorFieldKeys = {
    hexKey: colorHexKey,
    colorAKey,
    colorBKey,
    colorDirKey,
    imageIdKey: colorImageIdKey,
    imagePreviewKey: colorImagePreviewKey,
  };
  const colorPickerValue = buildColorPickerValue(colorMode, values, baseColorKeys);

  const modeDef = defs.find((d) => d.key === textureModeKey);
  const nonFloat = defs.filter((d) => d.type !== "float" && d.key !== textureModeKey && d.key !== colorModeKey);
  const visibleNonFloat = nonFloat.filter((d) => shouldShowTextureParam(zone, d.key, values));

  // Gradient keys are now in color picker (not texture controls)
  // No filtering needed since texture_mode no longer includes "gradient"
  const visibleNonFloatRows = visibleNonFloat;

  const finishDefsOrdered = finishHexDefs.filter((d) => d.key === finishKey);
  const orphanFinishHex = finishHexDefs.filter((d) => d.key !== finishKey && d.key !== hexKey);

  // Show base color controls only when no pattern overlay is active.
  const showBaseColorPicker = textureMode === "none";

  const textureFloats = defs.filter((d) => d.type === "float");
  const textureFloatsVisible = textureFloats.filter((d) => shouldShowTextureParam(zone, d.key, values));
  const tfq = textureFloatFilter.trim().toLowerCase();
  const textureFloatFiltered = tfq
    ? textureFloatsVisible.filter(
        (d) => d.key.toLowerCase().includes(tfq) || d.label.toLowerCase().includes(tfq),
      )
    : textureFloatsVisible;

  const updateColorModeWithCarry = (
    modeKey: string,
    prevMode: PickerMode,
    nextMode: PickerMode,
    carryFactory: (from: "single" | "gradient", to: "single" | "gradient") => Record<string, unknown>,
  ) => {
    if (nextMode !== "image" && prevMode !== "image") {
      const carry = carryFactory(prevMode, nextMode);
      setAnimatedBuildOption(slug, modeKey, nextMode);
      if (Object.keys(carry).length > 0) {
        applyAnimatedBuildOptionsForSlug(slug, carry);
      }
      return;
    }
    setAnimatedBuildOption(slug, modeKey, nextMode);
  };

  const updatePickerValue = (v: ColorPickerValue, keys: ColorFieldKeys) => {
    if (v.type === "single") {
      setAnimatedBuildOption(slug, keys.hexKey, v.color);
      return;
    }
    if (v.type === "gradient") {
      setAnimatedBuildOption(slug, keys.colorAKey, v.colorA);
      setAnimatedBuildOption(slug, keys.colorBKey, v.colorB);
      setAnimatedBuildOption(slug, keys.colorDirKey, v.direction);
      return;
    }
    if (v.preview) {
      setAnimatedBuildOption(slug, keys.imagePreviewKey, v.preview);
    }
    if (v.assetId) {
      setAnimatedBuildOption(slug, keys.imageIdKey, v.assetId);
    }
  };

  /**
   * Helper to render a pattern color field with full 3-mode support (single/gradient/image).
   * Used for spot_color, spot_bg_color, stripe_color, stripe_bg_color, etc.
   */
  const renderPatternColorPicker = (
    colorFieldName: string, // "spot_color", "stripe_color", etc.
    label: string,
  ) => {
    const colorMode = normalizedPatternColorMode(zone, colorFieldName, values);
    const modeKey = `feat_${zone}_texture_${colorFieldName}_mode`;
    const hexKey = `feat_${zone}_texture_${colorFieldName}_hex`;
    const colorAKey = `feat_${zone}_texture_${colorFieldName}_a`;
    const colorBKey = `feat_${zone}_texture_${colorFieldName}_b`;
    const colorDirKey = `feat_${zone}_texture_${colorFieldName}_direction`;
    const imageIdKey = `feat_${zone}_texture_${colorFieldName}_image_id`;
    const imagePreviewKey = `feat_${zone}_texture_${colorFieldName}_image_preview`;
    const pickerKeys: ColorFieldKeys = {
      hexKey,
      colorAKey,
      colorBKey,
      colorDirKey,
      imageIdKey,
      imagePreviewKey,
      legacySingleKey: `feat_${zone}_texture_${colorFieldName}`,
    };

    const pickerValue = buildColorPickerValue(colorMode, values, pickerKeys);

    return (
      <div key={modeKey} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        <ColorPickerTabs
          mode={pickerValue.type}
          value={pickerValue}
          label={label}
          onModeChange={(newColorMode) => {
            updateColorModeWithCarry(
              modeKey,
              colorMode,
              newColorMode,
              (from, to) => carryPatternColorPaletteOnModeChange(zone, colorFieldName, from, to, values),
            );
          }}
          onChange={(v) => updatePickerValue(v, pickerKeys)}
        />
      </div>
    );
  };

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
      ? { ...modeDef, label: "Pattern Setting", options: modeDef.options.filter((o) => !["custom", "gradient", "assets"].includes(o)) }
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

      {/* Finish selection (moved above color picker for clarity) */}
      {finishDefsOrdered.map(row)}

      {showBaseColorPicker ? (
        <ColorPickerTabs
          mode={colorPickerValue.type}
          value={colorPickerValue}
          onModeChange={(newColorMode) => {
            updateColorModeWithCarry(colorModeKey, colorMode, newColorMode, (from, to) =>
              carryColorPaletteOnModeChange(zone, from, to, values),
            );
          }}
          onChange={(v) => updatePickerValue(v, baseColorKeys)}
        />
      ) : null}

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

      {orphanFinishHex.map(row)}
      {visibleNonFloatRows.map((def) => {
        // Detect pattern color fields and render with full 3-mode support
        if (def.key === `feat_${zone}_texture_spot_color`) {
          return renderPatternColorPicker("spot_color", def.label);
        }
        if (def.key === `feat_${zone}_texture_spot_bg_color`) {
          return renderPatternColorPicker("spot_bg_color", def.label);
        }
        if (def.key === `feat_${zone}_texture_stripe_color`) {
          return renderPatternColorPicker("stripe_color", def.label);
        }
        if (def.key === `feat_${zone}_texture_stripe_bg_color`) {
          return renderPatternColorPicker("stripe_bg_color", def.label);
        }
        // For all other controls (pattern density, width, etc.), use generic ControlRow
        return (
          <ControlRow
            key={def.key}
            def={def}
            value={values[def.key]}
            onChange={(v: number | string | boolean) => setAnimatedBuildOption(slug, def.key, v)}
          />
        );
      })}
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
