import { useCallback, useMemo } from "react";
import { useAppStore } from "../../store/useAppStore";
import { StudioColorPickerTabs } from "./StudioColorPickerTabs";
import { studioFillPanelStyle } from "./studioFillStyles";
import { StudioPaletteRow } from "./StudioPaletteRow";
import {
  carryColorPaletteOnModeChange,
  carryPatternColorPaletteOnModeChange,
  normalizedColorMode,
  normalizedPatternColorMode,
} from "../Preview/ZoneTextureBlock";
import { STUDIO_INK_PRIMARY } from "../../styles/studioTokens";
import {
  buildColorPickerValue,
  colorPickerValueToStoreUpdates,
  zoneBackgroundColorKeys,
  zonePatternColorKeys,
  type ColorFieldKeys,
} from "../../utils/zoneColorPickerBridge";
import { buildZoneHexUpdates, readZoneHex } from "../../utils/studioLookMaterial";

export type StudioZoneFillRole = "background" | "pattern";

export type ModernFillKind = "zone_color" | "texture_background" | "texture_pattern";

export type StudioZoneFillBindings = {
  values: Readonly<Record<string, unknown>>;
  applyUpdates: (updates: Record<string, unknown>) => void;
  setOption: (key: string, value: unknown) => void;
};

type Props = {
  slug: string;
  zone: string;
  fillRole: StudioZoneFillRole;
  accentHue: string;
  paletteColors?: readonly string[];
  embedded?: boolean;
  /** When set, read/write draft values instead of the app store (element-defaults modal). */
  bindings?: StudioZoneFillBindings;
  knownDefKeys?: ReadonlySet<string>;
};

type LegacyBackground = { kind: "legacy"; hexKey: string };
type ModernFill = {
  kind: "modern";
  keys: ColorFieldKeys;
  modeKey: string;
  fillKind: ModernFillKind;
};
type FillConfig = LegacyBackground | ModernFill;

export function resolveZoneFillConfig(
  zone: string,
  fillRole: StudioZoneFillRole,
  knownDefKeys: ReadonlySet<string>,
): FillConfig | null {
  if (fillRole === "pattern") {
    const keys = zonePatternColorKeys(zone, "pattern");
    if (
      knownDefKeys.has(keys.hexKey) ||
      knownDefKeys.has(keys.colorAKey) ||
      (keys.legacySingleKey !== undefined && knownDefKeys.has(keys.legacySingleKey))
    ) {
      return {
        kind: "modern",
        keys,
        modeKey: `feat_${zone}_texture_pattern_mode`,
        fillKind: "texture_pattern",
      };
    }
    return null;
  }

  const colorKeys = zoneBackgroundColorKeys(zone);
  if (knownDefKeys.has(colorKeys.hexKey) || knownDefKeys.has(colorKeys.colorAKey)) {
    return {
      kind: "modern",
      keys: colorKeys,
      modeKey: `feat_${zone}_color_mode`,
      fillKind: "zone_color",
    };
  }

  const bgKeys = zonePatternColorKeys(zone, "background");
  if (
    knownDefKeys.has(bgKeys.hexKey) ||
    knownDefKeys.has(bgKeys.colorAKey) ||
    (bgKeys.legacySingleKey !== undefined && knownDefKeys.has(bgKeys.legacySingleKey))
  ) {
    return {
      kind: "modern",
      keys: bgKeys,
      modeKey: `feat_${zone}_texture_background_mode`,
      fillKind: "texture_background",
    };
  }

  const legacyHex = `feat_${zone}_hex`;
  if (knownDefKeys.has(legacyHex)) {
    return { kind: "legacy", hexKey: legacyHex };
  }
  return null;
}

function patternColorField(fillKind: ModernFillKind): "pattern" | "background" {
  return fillKind === "texture_pattern" ? "pattern" : "background";
}

function useZoneFillState(
  slug: string,
  bindings: StudioZoneFillBindings | undefined,
) {
  const storeValues = useAppStore((s) => s.animatedBuildOptionValues[slug] ?? {});
  const storeApplyBulk = useAppStore((s) => s.applyAnimatedBuildOptionsForSlug);
  const storeSetOption = useAppStore((s) => s.setAnimatedBuildOption);

  if (bindings) {
    return {
      values: bindings.values,
      applyBulk: (_s: string, updates: Record<string, unknown>) => bindings.applyUpdates(updates),
      setOption: (_s: string, key: string, value: unknown) => bindings.setOption(key, value),
    };
  }

  return {
    values: storeValues,
    applyBulk: storeApplyBulk,
    setOption: storeSetOption,
  };
}

function StudioLegacyHexFill({
  slug,
  zone,
  hexKey,
  paletteColors,
  embedded,
  knownDefKeys,
  bindings,
}: {
  slug: string;
  zone: string;
  hexKey: string;
  paletteColors?: readonly string[];
  embedded?: boolean;
  knownDefKeys: ReadonlySet<string>;
  bindings?: StudioZoneFillBindings;
}) {
  const { values, applyBulk } = useZoneFillState(slug, bindings);

  const hex = readZoneHex(values, zone) || "#888888";

  const setHex = useCallback(
    (next: string) => {
      applyBulk(slug, buildZoneHexUpdates(zone, next, knownDefKeys));
    },
    [slug, zone, knownDefKeys, applyBulk],
  );

  const legacyValue = { type: "single" as const, color: hex.replace(/^#/, "") };

  return (
    <div
      data-testid={`studio-zone-fill-${zone}-background`}
      style={studioFillPanelStyle(embedded)}
    >
      {paletteColors && paletteColors.length > 0 ? (
        <StudioPaletteRow
          colors={paletteColors}
          value={legacyValue}
          onPick={(c) => setHex(c.startsWith("#") ? c : `#${c}`)}
        />
      ) : null}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <label
          style={{
            width: 18,
            height: 18,
            borderRadius: 4,
            background: hex,
            boxShadow: "0 0 0 1px rgba(255,255,255,0.1)",
            overflow: "hidden",
            cursor: "pointer",
          }}
        >
          <input
            type="color"
            value={hex.startsWith("#") ? hex : `#${hex.replace(/^#/, "")}`}
            aria-label={`${zone} hex`}
            data-testid={`studio-legacy-hex-input-${zone}`}
            style={{ opacity: 0, width: "100%", height: "100%", border: 0, cursor: "pointer" }}
            onChange={(e) => setHex(e.target.value)}
          />
        </label>
        <span style={{ fontFamily: "var(--font-mono, monospace)", fontSize: 11, color: STUDIO_INK_PRIMARY }}>
          {hex.startsWith("#") ? hex : `#${hex}`}
        </span>
      </div>
      <input type="hidden" data-testid={`studio-legacy-hex-key-${zone}`} value={hexKey} readOnly />
    </div>
  );
}

function StudioModernZoneFill({
  slug,
  zone,
  fillRole,
  accentHue,
  paletteColors,
  embedded,
  config,
  knownDefKeys,
  bindings,
}: Props & { config: ModernFill; knownDefKeys: ReadonlySet<string> }) {
  const { values, setOption, applyBulk } = useZoneFillState(slug, bindings);

  const { keys, modeKey, fillKind } = config;

  const colorMode =
    fillKind === "zone_color"
      ? normalizedColorMode(zone, values)
      : normalizedPatternColorMode(zone, patternColorField(fillKind), values);

  const pickerValue = buildColorPickerValue(colorMode, values, keys);

  const updateMode = useCallback(
    (nextMode: "single" | "gradient" | "image") => {
      if (nextMode !== "image" && colorMode !== "image") {
        const carry =
          fillKind === "zone_color"
            ? carryColorPaletteOnModeChange(zone, colorMode, nextMode, values)
            : carryPatternColorPaletteOnModeChange(
                zone,
                patternColorField(fillKind),
                colorMode,
                nextMode,
                values,
              );
        setOption(slug, modeKey, nextMode);
        if (Object.keys(carry).length > 0) applyBulk(slug, carry);
        return;
      }
      setOption(slug, modeKey, nextMode);
    },
    [slug, zone, fillKind, colorMode, values, setOption, applyBulk, modeKey],
  );

  const onChange = useCallback(
    (v: typeof pickerValue) => {
      const updates = colorPickerValueToStoreUpdates(v, keys);
      if (Object.keys(updates).length > 0) applyBulk(slug, updates);
      if (fillRole === "background" && fillKind !== "zone_color" && v.type === "single") {
        applyBulk(slug, buildZoneHexUpdates(zone, v.color.startsWith("#") ? v.color : `#${v.color}`, knownDefKeys));
      }
    },
    [slug, zone, fillRole, fillKind, keys, applyBulk, knownDefKeys],
  );

  const onPalettePick = useCallback(
    (pickHex: string) => {
      const normalized = pickHex.startsWith("#") ? pickHex : `#${pickHex}`;
      if (fillRole === "background" && fillKind === "zone_color") {
        applyBulk(slug, buildZoneHexUpdates(zone, normalized, knownDefKeys));
        return;
      }
      if (knownDefKeys.has(keys.hexKey)) {
        setOption(slug, keys.hexKey, normalized.replace(/^#/, ""));
      }
      if (fillRole === "background") {
        applyBulk(slug, buildZoneHexUpdates(zone, normalized, knownDefKeys));
      }
    },
    [slug, zone, fillRole, fillKind, knownDefKeys, keys.hexKey, applyBulk, setOption],
  );

  const showPalette =
    paletteColors && paletteColors.length > 0 && (fillRole === "background" || fillRole === "pattern");

  return (
    <div
      data-testid={`studio-zone-fill-${zone}-${fillRole}`}
      style={studioFillPanelStyle(embedded)}
    >
      <StudioColorPickerTabs
        accentHue={accentHue}
        mode={pickerValue.type}
        value={pickerValue}
        paletteColors={showPalette ? paletteColors : undefined}
        onPaletteColorPick={showPalette ? onPalettePick : undefined}
        onModeChange={updateMode}
        onChange={onChange}
      />
    </div>
  );
}

export function StudioZoneFill(props: Props) {
  const defs = useAppStore((s) => s.animatedBuildControls[props.slug] ?? []);
  const knownDefKeys = useMemo(
    () => props.knownDefKeys ?? new Set(defs.map((d) => d.key)),
    [props.knownDefKeys, defs],
  );
  const config = resolveZoneFillConfig(props.zone, props.fillRole, knownDefKeys);

  if (!config) return null;

  if (config.kind === "legacy") {
    return (
      <StudioLegacyHexFill
        slug={props.slug}
        zone={props.zone}
        hexKey={config.hexKey}
        paletteColors={props.paletteColors}
        embedded={props.embedded}
        knownDefKeys={knownDefKeys}
        bindings={props.bindings}
      />
    );
  }

  return (
    <StudioModernZoneFill
      {...props}
      config={config}
      knownDefKeys={knownDefKeys}
      bindings={props.bindings}
    />
  );
}
