import { useAppStore } from "../../store/useAppStore";
import { normalizeAnimatedSlug, PLAYER_PROCEDURAL_BUILD_SLUG } from "../../utils/enemyDisplay";
import { PLAYER_COLORS } from "../CommandPanel/commandLogic";
import { ZoneExtraControls } from "./ZoneExtraControls";

/**
 * Center column tab: per-zone geometry extras (``extra_zone_*`` build options).
 */
export function ExtrasPane() {
  const commandContext = useAppStore((s) => s.commandContext);
  const animatedEnemyMeta = useAppStore((s) => s.animatedEnemyMeta);
  const { cmd, enemy } = commandContext;
  const playerColor = (enemy || "").trim().toLowerCase();
  const animatedSlug = normalizeAnimatedSlug(enemy);
  const isAnimatedEnemy =
    cmd === "animated" &&
    Boolean(animatedSlug) &&
    animatedSlug !== "all" &&
    animatedEnemyMeta.some((m) => m.slug === animatedSlug);
  const isPlayerSlimeExtras = cmd === "player" && PLAYER_COLORS.includes(playerColor);
  const slug = isPlayerSlimeExtras ? PLAYER_PROCEDURAL_BUILD_SLUG : animatedSlug;

  if (!isAnimatedEnemy && !isPlayerSlimeExtras) {
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
        &quot;all&quot;) or <code style={{ color: "#bbb" }}>player</code> (color) to edit spikes, bulbs, horns, and related
        geometry extras.
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
        One <strong style={{ color: "#bbb" }}>extra kind</strong> per material zone (none, shell, spikes, horns, bulbs).{" "}
        <strong style={{ color: "#bbb" }}>Horns</strong> apply to the <strong style={{ color: "#bbb" }}>head</strong> zone
        only. Finish + hex here tint the extra geometry; base zone colors stay on the <strong style={{ color: "#bbb" }}>Colors</strong>{" "}
        tab. Re-run preview / export to see changes.
      </p>
      <ZoneExtraControls slug={slug} showEmptyHint />
    </div>
  );
}
