import type { CSSProperties } from "react";
import {
  materialSphereBackground,
  type MaterialSphereVariant,
} from "./studioMaterialSphere";

export type StudioMaterialSpherePreviewProps = {
  variant: MaterialSphereVariant;
  /** Base tint for solid / gradient stops fallback */
  color?: string;
  gradientCss?: string;
  accentHue?: string;
  size?: number;
  title?: string;
};

/** Small 3D-style sphere hinting at the active material (no GLB / texture image). */
export function StudioMaterialSpherePreview({
  variant,
  color = "#888888",
  gradientCss,
  accentHue,
  size = 48,
  title,
}: StudioMaterialSpherePreviewProps) {
  const background = materialSphereBackground(variant, { color, gradientCss, accentHue });
  const darker = color.startsWith("#") ? color : `#${color}`;

  const style: CSSProperties = {
    width: size,
    height: size,
    flexShrink: 0,
    borderRadius: "50%",
    background,
    boxShadow: `inset -3px -3px 6px rgba(0,0,0,0.35), 0 0 0 1px rgba(255,255,255,0.08), 0 4px 12px ${darker}33`,
  };

  return (
    <div
      role="img"
      aria-label={title ?? `Material preview (${variant})`}
      data-testid="studio-material-sphere"
      data-variant={variant}
      title={title}
      style={style}
    />
  );
}
