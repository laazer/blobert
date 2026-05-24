/** Fraction of the preview column allocated to the 3D viewport (1 = full area). */
export const STUDIO_PREVIEW_SCALE_LEVELS = [0.65, 0.8, 1, 1.15] as const;

export const STUDIO_PREVIEW_SCALE_DEFAULT_INDEX = 1;

export const STUDIO_PREVIEW_SCALE_LS = "blobert.studio.previewScaleIndex";

export type StudioPreviewScaleLevel = (typeof STUDIO_PREVIEW_SCALE_LEVELS)[number];

export function studioPreviewScaleLabel(scale: StudioPreviewScaleLevel): string {
  return `${Math.round(scale * 100)}%`;
}

export function clampPreviewScaleIndex(index: number): number {
  if (!Number.isFinite(index)) return STUDIO_PREVIEW_SCALE_DEFAULT_INDEX;
  return Math.max(0, Math.min(STUDIO_PREVIEW_SCALE_LEVELS.length - 1, Math.round(index)));
}

export function readStoredPreviewScaleIndex(): number {
  try {
    const raw = localStorage.getItem(STUDIO_PREVIEW_SCALE_LS);
    if (raw === null) return STUDIO_PREVIEW_SCALE_DEFAULT_INDEX;
    return clampPreviewScaleIndex(Number.parseInt(raw, 10));
  } catch {
    return STUDIO_PREVIEW_SCALE_DEFAULT_INDEX;
  }
}

export function writeStoredPreviewScaleIndex(index: number): void {
  try {
    localStorage.setItem(STUDIO_PREVIEW_SCALE_LS, String(clampPreviewScaleIndex(index)));
  } catch {
    /* quota / private mode */
  }
}
