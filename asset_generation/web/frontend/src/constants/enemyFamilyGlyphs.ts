import { normalizeAnimatedSlug } from "../utils/enemyDisplay";

/**
 * Per-family icons from `bot_vault/asset_generation/redesign_v2/shared.jsx` (`ENEMY_FAMILIES`).
 * Keys are normalized registry / meta slugs (`snake_case`).
 */
export const ENEMY_FAMILY_GLYPHS: Readonly<Record<string, string>> = {
  spider: "🕷",
  acid_spitter: "◉",
  adhesion_bug: "◐",
  boss: "★",
  carapace_husk: "⬢",
  claw_crawler: "✦",
  ember_imp: "✦",
  tar_slug: "●",
  /** Legacy / meta aliases */
  slug: "●",
  imp: "✦",
  spitter: "◉",
};

/** Family icon for the studio library row; falls back to element glyph then a neutral mark. */
export function enemyFamilyGlyph(
  familyId: string,
  elementGlyph?: string,
): string {
  const key = normalizeAnimatedSlug(familyId);
  return ENEMY_FAMILY_GLYPHS[key] ?? elementGlyph ?? "◆";
}
