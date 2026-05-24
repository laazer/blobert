import { useMemo } from "react";
import { useAppStore } from "../../store/useAppStore";
import { normalizeAnimatedSlug } from "../../utils/enemyDisplay";
import { registryFamilyTabLabel } from "../../utils/registryFamilyNav";
import { playerColorLabel } from "../../utils/studioPlayerLibrary";
import { PLAYER_COLORS } from "../CommandPanel/commandLogic";
import { ModelRegistryPane } from "../Editor/ModelRegistryPane";
import { STUDIO_INK_MUTED, STUDIO_INK_SECONDARY } from "../../styles/studioTokens";
import { StudioPanelHead } from "./StudioPanelHead";

const emptyStyle = {
  margin: 0,
  color: STUDIO_INK_MUTED,
  fontSize: 12,
  lineHeight: 1.5,
} as const;

/**
 * Studio inspector Versions tab — registry slots and version rows for the active cmd context.
 */
export function StudioVersionsPanel() {
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

  const isPlayerRegistry = cmd === "player" && PLAYER_COLORS.includes(playerColor);

  const subtitle = useMemo(() => {
    if (isAnimatedEnemy) {
      return `${registryFamilyTabLabel(animatedSlug)} — spawn pool and version rows`;
    }
    if (isPlayerRegistry) {
      return `${playerColorLabel(playerColor)} slime — spawn pool and version rows`;
    }
    return "Select an animated enemy or player color in the library";
  }, [isAnimatedEnemy, isPlayerRegistry, animatedSlug]);

  if (!isAnimatedEnemy && !isPlayerRegistry) {
    return (
      <div data-testid="studio-versions-empty">
        <StudioPanelHead title="Versions" subtitle="Registry slots and exports" />
        <p style={emptyStyle}>
          Set <strong style={{ color: STUDIO_INK_SECONDARY }}>cmd</strong> to{" "}
          <code style={{ color: STUDIO_INK_SECONDARY }}>animated</code> (one enemy family, not &quot;all&quot;) or{" "}
          <code style={{ color: STUDIO_INK_SECONDARY }}>player</code> (color) to manage versions here.
        </p>
      </div>
    );
  }

  return (
    <div data-testid="studio-versions-panel">
      <StudioPanelHead title="Versions" subtitle={subtitle} />
      <ModelRegistryPane studioSurface />
    </div>
  );
}
