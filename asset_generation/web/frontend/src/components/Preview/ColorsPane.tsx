import { useEffect } from "react";
import { useAppStore } from "../../store/useAppStore";
import { normalizeAnimatedSlug, PLAYER_PROCEDURAL_BUILD_SLUG } from "../../utils/enemyDisplay";
import { buildZoneColorHydrationFromCommandBar } from "../../utils/hydrateZoneColorsFromCommandBar";
import { PLAYER_COLORS } from "../CommandPanel/commandLogic";
import { ElementPalettesSection } from "./ElementPalettesSection";
import { FeatureMaterialControls } from "./FeatureMaterialControls";

/**
 * Center column tab: per-zone finish, hex, and surface pattern (feat_* build options).
 */
export function ColorsPane() {
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

  /**
   * Push command-bar `--finish` / `--hex-color` into per-zone `feat_*` keys for zones still at defaults.
   * Runs whenever the Colors tab is visible and the command export or meta changes — not only on tab entry
   * (otherwise changing finish/hex in the command bar while Colors is open never updates the zones).
   */
  useEffect(() => {
    if (!isAnimatedEnemy && !isPlayerSlimeColors) return;
    if (centerPanel !== "colors") return;

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
    centerPanel,
    slug,
    isAnimatedEnemy,
    isPlayerSlimeColors,
    commandExportFinish,
    commandExportHexColor,
    enemyMetaStatus,
    applyAnimatedBuildOptionsForSlug,
  ]);

  if (!isAnimatedEnemy && !isPlayerSlimeColors) {
    return (
      <div
        style={{
          padding: "12px 12px",
          background: "#1e1e1e",
          color: "#9d9d9d",
          fontSize: 12,
          flexShrink: 0,
        }}
      >
        Set <strong style={{ color: "#bbb" }}>cmd</strong> to <code style={{ color: "#bbb" }}>animated</code> (enemy, not
        &quot;all&quot;) or <code style={{ color: "#bbb" }}>player</code> (color) to edit per-zone finishes, hex colors, and surface patterns.
      </div>
    );
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 8,
        padding: "8px 10px 12px",
        background: "#1e1e1e",
        flexShrink: 0,
      }}
    >
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
      <ElementPalettesSection slug={slug} />
      <FeatureMaterialControls slug={slug} showEmptyHint />
    </div>
  );
}
