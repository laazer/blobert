import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { ELEMENTS, type ElementId } from "../../constants/elements";
import { useAppStore } from "../../store/useAppStore";
import {
  DEFAULT_ELEMENT_PALETTES,
  defaultElementForSlug,
  type CoarseZoneKey,
  type ElementId as PaletteElementId,
} from "../../utils/elementColorPalettes";
import { normalizeAnimatedSlug, PLAYER_PROCEDURAL_BUILD_SLUG } from "../../utils/enemyDisplay";
import { buildZoneColorHydrationFromCommandBar } from "../../utils/hydrateZoneColorsFromCommandBar";
import { inferFamilyElementId } from "../../utils/inferFamilyElement";
import { paletteSwatchColors } from "../../utils/studioLookMaterial";
import { PLAYER_COLORS } from "../CommandPanel/commandLogic";
import { StudioLookPanel } from "../studio/StudioLookPanel";
import { ElementPalettesSection } from "./ElementPalettesSection";
import { ExtraZoneMaterialControls } from "./ExtraZoneMaterialControls";
import { FeatureMaterialControls } from "./FeatureMaterialControls";

export type ColorsPaneProps = {
  /**
   * Studio Look inspector: hydration runs while mounted without requiring centerPanel === "colors".
   */
  studioSurface?: boolean;
};

/**
 * Center column tab (legacy) or Studio Look tab: per-zone finish, hex, and surface pattern (feat_* build options).
 */
export function ColorsPane({ studioSurface = false }: ColorsPaneProps) {
  const commandContext = useAppStore((s) => s.commandContext);
  const animatedEnemyMeta = useAppStore((s) => s.animatedEnemyMeta);
  const centerPanel = useAppStore((s) => s.centerPanel);
  const commandExportFinish = useAppStore((s) => s.commandExportFinish);
  const commandExportHexColor = useAppStore((s) => s.commandExportHexColor);
  const enemyMetaStatus = useAppStore((s) => s.enemyMetaStatus);
  const applyAnimatedBuildOptionsForSlug = useAppStore((s) => s.applyAnimatedBuildOptionsForSlug);
  const { cmd, enemy } = commandContext;
  const playerColor = (enemy || "").trim().toLowerCase();
  const animatedSlug = normalizeAnimatedSlug(enemy);
  const isAnimatedEnemy =
    cmd === "animated" &&
    Boolean(animatedSlug) &&
    animatedSlug !== "all" &&
    animatedEnemyMeta.some((m) => m.slug === animatedSlug);
  const isPlayerSlimeColors = cmd === "player" && PLAYER_COLORS.includes(playerColor);
  const slug = isPlayerSlimeColors ? PLAYER_PROCEDURAL_BUILD_SLUG : animatedSlug;
  const [activeZone, setActiveZone] = useState<CoarseZoneKey>("body");

  const studioAccent = useMemo(() => {
    const suggested = defaultElementForSlug(slug);
    const elementId: ElementId = suggested
      ? (suggested as ElementId)
      : enemy.trim()
        ? inferFamilyElementId(enemy, [])
        : "physical";
    const token = ELEMENTS[elementId];
    const palette = DEFAULT_ELEMENT_PALETTES[elementId as PaletteElementId];
    return { hue: token.hue, paletteColors: paletteSwatchColors(palette) };
  }, [slug, enemy]);

  /**
   * Push command-bar `--finish` / `--hex-color` into per-zone `feat_*` keys for zones still at defaults.
   * Runs whenever the Colors tab is visible and the command export or meta changes — not only on tab entry
   * (otherwise changing finish/hex in the command bar while Colors is open never updates the zones).
   */
  useEffect(() => {
    if (!isAnimatedEnemy && !isPlayerSlimeColors) return;
    const surfaceOpen = studioSurface || centerPanel === "colors";
    if (!surfaceOpen) return;

    // Defer past other useEffects in the same commit. Sibling CommandPanel syncs local UI → store;
    // microtasks run after all passive effects so we read the latest commandExport* values.
    queueMicrotask(() => {
      const st = useAppStore.getState();
      const { commandExportFinish: fin, commandExportHexColor: hx } = st;
      const defs = st.animatedBuildControls[slug] ?? [];
      const current = st.animatedBuildOptionValues[slug] ?? {};
      const updates = buildZoneColorHydrationFromCommandBar(slug, defs, current, fin, hx);
      if (Object.keys(updates).length === 0) return;
      applyAnimatedBuildOptionsForSlug(slug, updates);
    });
  }, [
    studioSurface,
    centerPanel,
    slug,
    isAnimatedEnemy,
    isPlayerSlimeColors,
    commandExportFinish,
    commandExportHexColor,
    enemyMetaStatus,
    applyAnimatedBuildOptionsForSlug,
  ]);

  const emptyShellStyle: CSSProperties = {
    padding: studioSurface ? 0 : "12px 12px",
    background: studioSurface ? "transparent" : "#1e1e1e",
    color: studioSurface ? "#7a7a86" : "#9d9d9d",
    fontSize: 12,
    flexShrink: 0,
    lineHeight: 1.5,
  };

  if (!isAnimatedEnemy && !isPlayerSlimeColors) {
    return (
      <div style={emptyShellStyle} data-testid={studioSurface ? "studio-look-empty" : undefined}>
        Set <strong style={{ color: "#bbb" }}>cmd</strong> to <code style={{ color: "#bbb" }}>animated</code> (enemy, not
        &quot;all&quot;) or <code style={{ color: "#bbb" }}>player</code> (color) to edit per-zone finishes, hex colors, geometry-extra tints, and surface patterns.
      </div>
    );
  }

  return (
    <div
      data-testid={studioSurface ? "studio-look-controls" : undefined}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: studioSurface ? 12 : 8,
        padding: studioSurface ? 0 : "8px 10px 12px",
        background: studioSurface ? "transparent" : "#1e1e1e",
        flexShrink: 0,
      }}
    >
      {!studioSurface ? (
      <p style={{ color: "#8f8f8f", fontSize: 11, margin: 0, lineHeight: 1.4 }}>
        Each coarse zone groups <strong style={{ color: "#bbb" }}>finish</strong>, <strong style={{ color: "#bbb" }}>base color</strong>, and{" "}
        <strong style={{ color: "#bbb" }}>pattern</strong> build options (GLB preview shows the last export)
        {isPlayerSlimeColors ? (
          <>
            . For <strong style={{ color: "#bbb" }}>player</strong>, <strong style={{ color: "#bbb" }}>body</strong> is the main
            slime + arms; <strong style={{ color: "#bbb" }}>head</strong> is the cheek blush (eyes stay sclera / pupil / highlight).
            Global tint stays in the command bar.
          </>
        ) : (
          <>
            {" "}
            (body, head, limbs, joints, extra on spider). Click a palette swatch to copy{" "}
            <code style={{ color: "#ccc" }}>#RRGGBB</code>; use <strong style={{ color: "#bbb" }}>Paste color</strong> on any hex
            row (including limb / joint overrides). Global export tint stays in the command bar.
          </>
        )}
      </p>
      ) : null}
      {studioSurface ? (
        <>
          <StudioLookPanel slug={slug} activeZone={activeZone} onActiveZoneChange={setActiveZone} />
          <details data-testid="studio-look-advanced" style={{ marginTop: 4 }}>
            <summary
              style={{
                cursor: "pointer",
                fontSize: 11,
                fontWeight: 600,
                color: "#8a8a96",
                userSelect: "none",
              }}
            >
              Advanced zone controls
            </summary>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 10 }}>
              <FeatureMaterialControls
                slug={slug}
                showEmptyHint
                compactTitle
                zoneFilter={activeZone}
                studioAdvanced={{
                  accentHue: studioAccent.hue,
                  paletteColors: studioAccent.paletteColors,
                }}
              />
              <ExtraZoneMaterialControls
                slug={slug}
                zoneFilter={activeZone}
                useStudioPicker
                accentHue={studioAccent.hue}
                paletteColors={studioAccent.paletteColors}
              />
            </div>
          </details>
        </>
      ) : (
        <>
          <ElementPalettesSection slug={slug} />
          <FeatureMaterialControls slug={slug} showEmptyHint />
          <ExtraZoneMaterialControls slug={slug} />
        </>
      )}
    </div>
  );
}
