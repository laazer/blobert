import type { GradientDirection } from "../ColorPicker/common/DirectionSelector";
import { shadeHex, tintHex } from "../../utils/studioLookMaterial";

export type MaterialSphereVariant = "solid" | "gradient" | "image";

function normalizeHex(hex: string): string {
  const t = hex.trim().replace(/^#/, "");
  if (!t) return "#888888";
  return `#${t.slice(0, 6)}`;
}

function sphereShading(base: string): string {
  const color = normalizeHex(base);
  const lighter = tintHex(color, 0.35);
  const darker = shadeHex(color, 0.42);
  return `radial-gradient(circle at 30% 25%, ${lighter}, ${color} 58%, ${darker})`;
}

export function gradientPreviewCss(
  colorA: string,
  colorB: string,
  direction: GradientDirection,
): string {
  const a = normalizeHex(colorA);
  const b = normalizeHex(colorB);
  if (direction === "vertical") return `linear-gradient(180deg, ${a}, ${b})`;
  if (direction === "radial") return `radial-gradient(circle at center, ${a}, ${b})`;
  return `linear-gradient(135deg, ${a}, ${b})`;
}

/** CSS ``background`` layers for the studio material preview sphere (no texture image). */
export function materialSphereBackground(
  variant: MaterialSphereVariant,
  options: {
    color?: string;
    gradientCss?: string;
    accentHue?: string;
  },
): string {
  const base = normalizeHex(options.color ?? "#888888");
  const sphere = sphereShading(base);

  if (variant === "gradient" && options.gradientCss) {
    return `${options.gradientCss}, ${sphere}`;
  }

  if (variant === "image") {
    const tint = normalizeHex(options.accentHue ?? base);
    const lighter = tintHex(tint, 0.25);
    const darker = shadeHex(tint, 0.38);
    const hatchA =
      "repeating-linear-gradient(135deg, rgba(255,255,255,0.11) 0 1px, transparent 1px 5px)";
    const hatchB =
      "repeating-linear-gradient(45deg, rgba(0,0,0,0.18) 0 1px, transparent 1px 4px)";
    const tintedSphere = `radial-gradient(circle at 30% 25%, ${lighter}, ${tint}88 55%, ${darker})`;
    return `${hatchA}, ${hatchB}, ${tintedSphere}`;
  }

  return sphere;
}
