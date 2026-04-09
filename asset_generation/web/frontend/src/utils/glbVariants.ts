import type { Asset } from "../types";
import { normalizeAnimatedSlug } from "./enemyDisplay";
import { previewPathFromAssetsUrl } from "./previewPathFromAssetsUrl";

/** Matches ``ExportConfig.ANIMATED_DIR`` in Python. */
export const ANIMATED_EXPORT_DIR = "animated_exports";

/**
 * Relative path under the asset server root for a procedural animated export
 * (same stem as Python ``export_naming.animated_export_stem``; no prefab segment).
 */
/** Registry / export stem for variant index (e.g. ``spider_animated_00``). */
export function animatedExportVersionId(enemySlug: string, variantIndex: number): string {
  const v = Math.max(0, Math.min(99, Math.floor(variantIndex)));
  return `${enemySlug}_animated_${String(v).padStart(2, "0")}`;
}

export function animatedExportRelativePath(enemySlug: string, variantIndex: number): string {
  const stem = animatedExportVersionId(enemySlug, variantIndex);
  return `${ANIMATED_EXPORT_DIR}/${stem}.glb`;
}

/** Parse `spider_animated_03.glb` → slug + index (procedural animated exports only). */
export function parseAnimatedEnemyExportFilename(
  name: string,
): { slug: string; variantIndex: number } | null {
  const m = name.match(/^(.+)_animated_(\d{2})\.glb$/i);
  if (!m) return null;
  return { slug: m[1], variantIndex: parseInt(m[2], 10) };
}

/** Match `*_NN.glb` where NN is a two-digit variant index (generic exports e.g. player). */
export function parseVariantFilename(name: string): { base: string; variantIndex: number } | null {
  const m = name.match(/^(.+)_(\d{2})\.glb$/i);
  if (!m) return null;
  return { base: m[1], variantIndex: parseInt(m[2], 10) };
}

export function parseAssetPathFromGlbUrl(url: string | null): string | null {
  if (!url) return null;
  const m = url.match(/\/api\/assets\/(.+?)(?:\?|$)/);
  return m ? m[1] : null;
}

/**
 * Variant index for Save model / registry updates: use the GLB in preview when its stem matches
 * ``{family}_animated_NN`` (same normalized family); otherwise ``0``.
 */
export function animatedVariantIndexFromPreviewGlb(
  normalizedFamily: string | null,
  activeGlbUrl: string | null,
): number {
  if (!normalizedFamily) return 0;
  const rel = previewPathFromAssetsUrl(activeGlbUrl);
  if (!rel || !rel.endsWith(".glb")) return 0;
  const base = rel.split("/").pop() ?? "";
  const parsed = parseAnimatedEnemyExportFilename(base);
  if (!parsed) return 0;
  if (normalizeAnimatedSlug(parsed.slug) !== normalizedFamily) return 0;
  return parsed.variantIndex;
}

/**
 * Registry version id for the animated GLB in preview when its stem matches ``{family}_animated_NN``;
 * otherwise ``null`` (caller picks the first eligible version by manifest order).
 */
export function preferredAnimatedVersionIdFromPreview(
  normalizedFamily: string,
  activeGlbUrl: string | null,
): string | null {
  const fam = normalizeAnimatedSlug(normalizedFamily);
  if (!fam) return null;
  const rel = previewPathFromAssetsUrl(activeGlbUrl);
  if (!rel || !rel.endsWith(".glb")) return null;
  const base = rel.split("/").pop() ?? "";
  const parsed = parseAnimatedEnemyExportFilename(base);
  if (!parsed) return null;
  if (normalizeAnimatedSlug(parsed.slug) !== fam) return null;
  return animatedExportVersionId(fam, parsed.variantIndex);
}

export function assetByPath(assets: Asset[], path: string | null): Asset | null {
  if (!path) return null;
  return assets.find((a) => a.path === path) ?? null;
}
