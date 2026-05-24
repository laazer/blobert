import type { CSSProperties } from "react";
import { enemyFamilyGlyph } from "../../constants/enemyFamilyGlyphs";

type Props = {
  familyId: string;
  elementGlyph?: string;
  hue: string;
  soft: string;
  ink: string;
  size?: number;
};

const boxBase = (size: number, soft: string, hue: string): CSSProperties => ({
  width: size,
  height: size,
  borderRadius: 7,
  background: soft,
  border: `1px solid ${hue}40`,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  flexShrink: 0,
  lineHeight: 1,
});

export function StudioFamilyGlyph({
  familyId,
  elementGlyph,
  hue,
  soft,
  ink,
  size = 28,
}: Props) {
  const glyph = enemyFamilyGlyph(familyId, elementGlyph);
  const fontSize = glyph.length > 1 ? 14 : 15;

  return (
    <div
      style={{ ...boxBase(size, soft, hue), fontSize, color: ink }}
      data-testid={`studio-family-glyph-${familyId}`}
      aria-hidden
    >
      {glyph}
    </div>
  );
}
