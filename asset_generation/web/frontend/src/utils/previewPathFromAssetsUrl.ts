/**
 * Inverse of {@link useAppStore.selectAssetByPath}: `/api/assets/{path}?t=…` → server-relative GLB path.
 */
export function previewPathFromAssetsUrl(url: string | null): string | null {
  if (!url || !url.trim()) return null;
  try {
    const base = typeof window !== "undefined" ? window.location.origin : "http://local";
    const u = new URL(url, base);
    const m = u.pathname.match(/^\/api\/assets\/(.+)$/);
    if (!m) return null;
    return decodeURIComponent(m[1]);
  } catch {
    return null;
  }
}
