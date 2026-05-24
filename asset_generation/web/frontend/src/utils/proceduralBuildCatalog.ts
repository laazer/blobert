import type { AnimatedBuildControlDef } from "../types";
import { PLAYER_PROCEDURAL_BUILD_SLUG } from "./enemyDisplay";

/** Mesh / rig / mouth controls — excludes Look (feat_*) and Extras (extra_zone_*). */
export function proceduralBuildControlDefs(
  defs: readonly AnimatedBuildControlDef[],
): AnimatedBuildControlDef[] {
  return defs.filter(
    (d) =>
      !d.key.startsWith("feat_") &&
      !d.key.startsWith("extra_zone_") &&
      !d.key.startsWith("texture_"),
  );
}

/**
 * True when the meta API did not supply Python introspection controls (only zone/eye synthetics may remain).
 */
export function isProceduralBuildCatalogIncomplete(
  slug: string,
  buildDefs: readonly AnimatedBuildControlDef[],
  metaBackend: "ok" | "fallback" | null,
): boolean {
  if (metaBackend === "fallback") return true;
  if (buildDefs.length === 0) return true;

  if (slug === PLAYER_PROCEDURAL_BUILD_SLUG) {
    return buildDefs.length < 3;
  }

  const hasRig = buildDefs.some((d) => d.key.startsWith("RIG_"));
  const hasBody =
    buildDefs.some((d) => d.key === "body_type") ||
    buildDefs.some((d) => d.key.startsWith("BODY_"));
  return !hasRig && !hasBody;
}
