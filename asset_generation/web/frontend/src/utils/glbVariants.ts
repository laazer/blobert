import type { Asset } from "../types";

/** Match `*_NN.glb` where NN is a two-digit variant index (export naming). */
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

/** All GLB variants in the same export family as `active` (same dir + same basename before `_NN`). */
export function variantsInSameFamily(assets: Asset[], active: Asset | null): Asset[] {
  if (!active || !active.name.toLowerCase().endsWith(".glb")) return [];
  const p = parseVariantFilename(active.name);
  if (!p) return [active];
  const key = `${active.dir}/${p.base}`;
  const glbs = assets.filter((a) => a.name.toLowerCase().endsWith(".glb"));
  const out = glbs.filter((a) => {
    if (a.dir !== active.dir) return false;
    const q = parseVariantFilename(a.name);
    if (!q) return false;
    return `${a.dir}/${q.base}` === key;
  });
  out.sort((a, b) => {
    const va = parseVariantFilename(a.name)!;
    const vb = parseVariantFilename(b.name)!;
    return va.variantIndex - vb.variantIndex;
  });
  return out;
}

export function assetByPath(assets: Asset[], path: string | null): Asset | null {
  if (!path) return null;
  return assets.find((a) => a.path === path) ?? null;
}
