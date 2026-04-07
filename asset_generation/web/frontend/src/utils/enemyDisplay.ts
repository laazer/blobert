import type { AnimatedEnemyMeta, RunCmd } from "../types";

/** Default slug order when /api/meta/enemies has not loaded (labels are mechanical until then). */
export const DEFAULT_ANIMATED_ENEMY_SLUGS = [
  "spider",
  "slug",
  "imp",
  "spitter",
  "claw_crawler",
  "carapace_husk",
] as const;

/** Lowercase trim for matching API keys in animated_build_controls / store. */
export function normalizeAnimatedSlug(slug: string): string {
  return slug.trim().toLowerCase();
}

export function titleCaseSnake(slug: string): string {
  return slug
    .split("_")
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");
}

/** Fallback meta (mechanical labels) until GET /api/meta/enemies succeeds. */
export const DEFAULT_ANIMATED_ENEMY_META: AnimatedEnemyMeta[] = DEFAULT_ANIMATED_ENEMY_SLUGS.map((slug) => ({
  slug,
  label: titleCaseSnake(slug),
}));

/** Resolve display label using API meta when present; otherwise mechanical title-case. */
export function slugDisplayLabel(slug: string, meta?: readonly AnimatedEnemyMeta[]): string {
  const row = meta?.find((m) => m.slug === slug);
  if (row) return row.label;
  return titleCaseSnake(slug);
}

/** Label for the cmd panel enemy/color &lt;select&gt;: player colors are title-cased; else meta-driven label. */
export function enemySelectOptionLabel(
  cmd: RunCmd,
  value: string,
  animatedMeta?: readonly AnimatedEnemyMeta[],
): string {
  if (cmd === "player") {
    return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
  }
  return slugDisplayLabel(value, animatedMeta);
}
