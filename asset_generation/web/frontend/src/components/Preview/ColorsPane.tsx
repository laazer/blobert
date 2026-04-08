import { useAppStore } from "../../store/useAppStore";
import { normalizeAnimatedSlug } from "../../utils/enemyDisplay";
import { FeatureMaterialControls } from "./FeatureMaterialControls";

/**
 * Center column tab: per-slot finish + hex (feat_* build options).
 */
export function ColorsPane() {
  const commandContext = useAppStore((s) => s.commandContext);
  const animatedEnemyMeta = useAppStore((s) => s.animatedEnemyMeta);
  const { cmd, enemy } = commandContext;
  const slug = normalizeAnimatedSlug(enemy);
  const isAnimatedEnemy =
    cmd === "animated" &&
    Boolean(slug) &&
    slug !== "all" &&
    animatedEnemyMeta.some((m) => m.slug === slug);

  if (!isAnimatedEnemy) {
    return (
      <div
        style={{
          padding: "12px 12px",
          background: "#1e1e1e",
          color: "#9d9d9d",
          fontSize: 12,
          flex: 1,
        }}
      >
        Set <strong style={{ color: "#bbb" }}>cmd</strong> to <code style={{ color: "#bbb" }}>animated</code> and pick an
        enemy (not &quot;all&quot;) to edit per-part colors and finishes.
      </div>
    );
  }

  return (
    <div
      style={{
        flex: 1,
        minHeight: 0,
        overflow: "auto",
        display: "flex",
        flexDirection: "column",
        gap: 8,
        padding: "8px 10px 12px",
        background: "#1e1e1e",
      }}
    >
      <p style={{ color: "#8f8f8f", fontSize: 11, margin: 0, lineHeight: 1.4 }}>
        These apply to themed mesh slots (body, head, limbs, extra). Global tint for export is still set in the command
        bar (finish + hex).
      </p>
      <FeatureMaterialControls slug={slug} showEmptyHint />
    </div>
  );
}
