import { parseAnimatedEnemyExportFilename, parseVariantFilename } from "./glbVariants";
import { normalizeAnimatedSlug, PLAYER_PROCEDURAL_BUILD_SLUG } from "./enemyDisplay";

/**
 * Map a preview GLB path (under ``animated_exports`` or ``player_exports``) to the
 * ``animatedBuildControls`` / ``animatedBuildOptionValues`` slug, or null if unknown.
 */
export function buildOptionSlugFromPreviewGlbRelativePath(relativePath: string): string | null {
  const base = relativePath.split("/").pop() ?? "";
  const anim = parseAnimatedEnemyExportFilename(base);
  if (anim) return normalizeAnimatedSlug(anim.slug);
  const pv = parseVariantFilename(base);
  if (!pv) return null;
  if (pv.base.toLowerCase().startsWith("player_slime_")) {
    return PLAYER_PROCEDURAL_BUILD_SLUG;
  }
  return null;
}

/** ``player_exports/player_slime_blue_00.glb`` → ``blue``; unknown stem → null. */
export function playerColorFromPlayerSlimeExportRelativePath(relativePath: string): string | null {
  const base = relativePath.split("/").pop() ?? "";
  const pv = parseVariantFilename(base);
  if (!pv) return null;
  if (!pv.base.toLowerCase().startsWith("player_slime_")) return null;
  const rest = pv.base.slice("player_slime_".length);
  const c = rest.trim().toLowerCase();
  return c.length > 0 ? c : null;
}

/** Derive command-bar finish / hex from a build-options snapshot (body zone). */
export function commandExportPatchFromBuildSnapshot(
  snapshot: Record<string, unknown>,
): { finish?: string; hexColor?: string } {
  const out: { finish?: string; hexColor?: string } = {};
  const rawF = snapshot.feat_body_finish;
  if (typeof rawF === "string" && rawF.trim() !== "") {
    out.finish = rawF.trim();
  }
  const rawH = snapshot.feat_body_hex ?? snapshot.feat_body_color_hex;
  if (typeof rawH === "string") {
    const t = rawH.trim();
    if (/^#[0-9a-fA-F]{6}$/.test(t)) {
      out.hexColor = t;
    } else if (/^[0-9a-fA-F]{6}$/i.test(t)) {
      out.hexColor = `#${t}`;
    }
  }
  return out;
}
