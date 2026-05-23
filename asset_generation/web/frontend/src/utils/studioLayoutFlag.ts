/** Studio shell is enabled only when VITE_STUDIO_LAYOUT is exactly "1" (§11). */
export function isStudioLayoutEnabled(): boolean {
  return import.meta.env.VITE_STUDIO_LAYOUT === "1";
}
