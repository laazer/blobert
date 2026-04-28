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
  if (prevMode === nextMode) return {};
  const p = `feat_${zone}_texture_${colorField}_`;
  const g = (k: string) => values[k];
  const out: Record<string, unknown> = {};

  // When switching to single, preserve hex from gradient or existing single
  if (nextMode === "single") {
    const existingHex = g(`${p}hex`);
    if (!existingHex || (typeof existingHex === "string" && existingHex.trim() === "")) {
      // Fallback: prefer new color_a, then old single-key value, then default red
      const fallback =
        (typeof g(`${p}a`) === "string" ? g(`${p}a`) : undefined) ||
        (typeof g(`feat_${zone}_texture_${colorField}`) === "string" ? g(`feat_${zone}_texture_${colorField}`) : undefined) ||
        "ff0000";
      out[`${p}hex`] = fallback;
    }
  }
  // When switching to gradient, preserve or initialize gradient colors
  else if (nextMode === "gradient") {
    const existingA = g(`${p}a`);
    const existingB = g(`${p}b`);
    const fallbackHex = (typeof g(`${p}hex`) === "string" ? g(`${p}hex`) : undefined) ||
      (typeof g(`feat_${zone}_texture_${colorField}`) === "string" ? g(`feat_${zone}_texture_${colorField}`) : undefined) ||
      "ff0000";
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

  // Pattern color mode selectors (spot_color_mode, stripe_color_mode, etc.)
  if (defKey.includes("_texture_") && defKey.endsWith("_mode")) {
    // Show color mode selectors for active patterns
    if (defKey.includes("_spot_") && (textureMode === "spots" || textureMode === "checkerboard")) return true;
    if (defKey.includes("_stripe_") && textureMode === "stripes") return true;
    return false;
  }

  // Pattern fields (spots and checkerboard share pattern settings)
  if (defKey.includes("_texture_spot_")) {
    const showForSpots = textureMode === "spots" || textureMode === "checkerboard";
    // Color fields will be rendered by renderPatternColorPicker (hide them from generic ControlRow)
    if ((defKey === `feat_${zone}_texture_spot_color` || defKey === `feat_${zone}_texture_spot_bg_color`) && showForSpots) {
      return true; // Signal to render, but renderPatternColorPicker will handle it
    }
    // Other fields (density, etc.) are rendered generically
    return showForSpots;
  }

  if (defKey.includes("_texture_stripe_")) {
    const showForStripes = textureMode === "stripes";
    // Color fields will be rendered by renderPatternColorPicker
    if ((defKey === `feat_${zone}_texture_stripe_color` || defKey === `feat_${zone}_texture_stripe_bg_color`) && showForStripes) {
      return true;
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

  // Construct color picker value based on current color_mode
  const colorPickerValue: ColorPickerValue =
    colorMode === "gradient"
      ? {
          type: "gradient",
          colorA: typeof values[colorAKey] === "string" ? values[colorAKey] : "",
          colorB: typeof values[colorBKey] === "string" ? values[colorBKey] : "",
          direction: gradientDirectionFromStore(values[colorDirKey]),
        }
      : colorMode === "image"
        ? {
            type: "image",
            file: null, // Files aren't stored in store directly; only preview URL
            preview: typeof values[colorImagePreviewKey] === "string" ? values[colorImagePreviewKey] : undefined,
          }
        : {
            type: "single",
            color: typeof values[colorHexKey] === "string" ? values[colorHexKey] : "",
          };

  const modeDef = defs.find((d) => d.key === textureModeKey);
  const nonFloat = defs.filter((d) => d.type !== "float" && d.key !== textureModeKey && d.key !== colorModeKey);
  const visibleNonFloat = nonFloat.filter((d) => shouldShowTextureParam(zone, d.key, values));

  // Gradient keys are now in color picker (not texture controls)
  // No filtering needed since texture_mode no longer includes "gradient"
  const visibleNonFloatRows = visibleNonFloat;

  const finishDefsOrdered = finishHexDefs.filter((d) => d.key === finishKey);
  const hexDefsOrdered = finishHexDefs.filter((d) => d.key === hexKey);
  const orphanFinishHex = finishHexDefs.filter((d) => d.key !== finishKey && d.key !== hexKey);

  // Show base hex only when texture_mode is "none" (no pattern overlay) AND color_mode is "single"
  const showBaseHex = textureMode === "none" && colorMode === "single";

  const textureFloats = defs.filter((d) => d.type === "float");
  const textureFloatsVisible = textureFloats.filter((d) => shouldShowTextureParam(zone, d.key, values));
  const tfq = textureFloatFilter.trim().toLowerCase();
  const textureFloatFiltered = tfq
    ? textureFloatsVisible.filter(
        (d) => d.key.toLowerCase().includes(tfq) || d.label.toLowerCase().includes(tfq),
      )
    : textureFloatsVisible;

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

    // Build single color fallback (backward compat: check old key format)
    const singleColor = typeof values[hexKey] === "string" ? values[hexKey] :
      (typeof values[`feat_${zone}_texture_${colorFieldName}`] === "string" ? (values[`feat_${zone}_texture_${colorFieldName}`] as string) : "");

    const pickerValue: ColorPickerValue =
      colorMode === "gradient"
        ? {
            type: "gradient",
            colorA: typeof values[colorAKey] === "string" ? values[colorAKey] : "",
            colorB: typeof values[colorBKey] === "string" ? values[colorBKey] : "",
            direction: gradientDirectionFromStore(values[colorDirKey]),
          }
        : colorMode === "image"
          ? {
              type: "image",
              file: null,
              preview: typeof values[imagePreviewKey] === "string" ? values[imagePreviewKey] : undefined,
            }
          : {
              type: "single",
              color: singleColor,
            };

    return (
      <div key={modeKey} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        <ColorPickerTabs
          mode={pickerValue.type}
          value={pickerValue}
          label={label}
          onModeChange={(newColorMode) => {
            if (newColorMode !== "image" && colorMode !== "image") {
              const carry = carryPatternColorPaletteOnModeChange(zone, colorFieldName, colorMode as "single" | "gradient", newColorMode as "single" | "gradient", values);
              setAnimatedBuildOption(slug, modeKey, newColorMode);
              if (Object.keys(carry).length > 0) {
                applyAnimatedBuildOptionsForSlug(slug, carry);
              }
            } else {
              setAnimatedBuildOption(slug, modeKey, newColorMode);
            }
          }}
          onChange={(v) => {
            if (v.type === "single") {
              setAnimatedBuildOption(slug, hexKey, v.color);
            } else if (v.type === "gradient") {
              setAnimatedBuildOption(slug, colorAKey, v.colorA);
              setAnimatedBuildOption(slug, colorBKey, v.colorB);
              setAnimatedBuildOption(slug, colorDirKey, v.direction);
            } else if (v.type === "image") {
              if (v.preview) {
                setAnimatedBuildOption(slug, imagePreviewKey, v.preview);
              }
            }
          }}
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

      {/* Color picker (independent, always visible) */}
      <ColorPickerTabs
        mode={colorPickerValue.type}
        value={colorPickerValue}
        onModeChange={(newColorMode) => {
          // Handle color mode transition (single ↔ gradient ↔ image)
          // Only carry palette for single ↔ gradient; image mode is independent
          if (newColorMode !== "image" && colorMode !== "image") {
            const carry = carryColorPaletteOnModeChange(zone, colorMode as "single" | "gradient", newColorMode as "single" | "gradient", values);
            setAnimatedBuildOption(slug, colorModeKey, newColorMode);
            if (Object.keys(carry).length > 0) {
              applyAnimatedBuildOptionsForSlug(slug, carry);
            }
          } else {
            // Switching to/from image mode: no palette carry needed
            setAnimatedBuildOption(slug, colorModeKey, newColorMode);
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
          } else if (v.type === "image") {
            // Store image preview URL and asset ID (for preloaded textures)
            if (v.preview) {
              setAnimatedBuildOption(slug, colorImagePreviewKey, v.preview);
            }
            if (v.assetId) {
              setAnimatedBuildOption(slug, colorImageIdKey, v.assetId);
            }
          }
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

      {showBaseHex ? (
        <>
          {hexDefsOrdered.map(row)}
          {orphanFinishHex.map(row)}
        </>
      ) : null}
      {visibleNonFloatRows.map((def) => {
        // Detect pattern color fields and render with full 3-mode support
        if (def.key.includes("_texture_spot_color") && !def.key.endsWith("_mode")) {
          return renderPatternColorPicker("spot_color", def.label);
        }
        if (def.key.includes("_texture_spot_bg_color") && !def.key.endsWith("_mode")) {
          return renderPatternColorPicker("spot_bg_color", def.label);
        }
        if (def.key.includes("_texture_stripe_color") && !def.key.endsWith("_mode")) {
          return renderPatternColorPicker("stripe_color", def.label);
        }
        if (def.key.includes("_texture_stripe_bg_color") && !def.key.endsWith("_mode")) {
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
