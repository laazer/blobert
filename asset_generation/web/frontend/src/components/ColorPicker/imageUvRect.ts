/** Normalized atlas rectangle (Blender UV: u across, v up, origin bottom-left). */

export type ImageUvRect = { u0: number; v0: number; u1: number; v1: number };

function clamp01(x: number): number {
  return Math.max(0, Math.min(1, x));
}

/** Parse JSON stored in ``feat_*_color_image_uv_rect`` / pattern ``*_image_uv_rect``. */
export function parseImageUvRect(raw: unknown): ImageUvRect | null {
  if (typeof raw !== "string" || !raw.trim()) return null;
  try {
    const o = JSON.parse(raw) as Record<string, unknown>;
    const u0 = Number(o.u0);
    const v0 = Number(o.v0);
    const u1 = Number(o.u1);
    const v1 = Number(o.v1);
    if ([u0, v0, u1, v1].some((n) => Number.isNaN(n))) return null;
    return {
      u0: clamp01(Math.min(u0, u1)),
      v0: clamp01(Math.min(v0, v1)),
      u1: clamp01(Math.max(u0, u1)),
      v1: clamp01(Math.max(v0, v1)),
    };
  } catch {
    return null;
  }
}

export function stringifyImageUvRect(r: ImageUvRect): string {
  return JSON.stringify({
    u0: r.u0,
    v0: r.v0,
    u1: r.u1,
    v1: r.v1,
  });
}

/**
 * Convert canvas pixel selection (origin top-left, y down) to UV rect (v up).
 * cw/ch are canvas width/height.
 */
export function canvasDragToUvRect(
  x0: number,
  y0: number,
  x1: number,
  y1: number,
  cw: number,
  ch: number,
): ImageUvRect {
  const minX = clamp01(Math.min(x0, x1) / cw);
  const maxX = clamp01(Math.max(x0, x1) / cw);
  const minY = Math.min(y0, y1);
  const maxY = Math.max(y0, y1);
  const vTop = 1 - minY / ch;
  const vBottom = 1 - maxY / ch;
  return {
    u0: minX,
    v0: Math.min(vBottom, vTop),
    u1: maxX,
    v1: Math.max(vBottom, vTop),
  };
}
