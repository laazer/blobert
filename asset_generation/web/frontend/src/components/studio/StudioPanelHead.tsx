import type { CSSProperties, ReactNode } from "react";
import { STUDIO_INK_MUTED, STUDIO_INK_PRIMARY } from "../../styles/studioTokens";

type Props = {
  title: string;
  subtitle?: string;
  right?: ReactNode;
};

const titleStyle: CSSProperties = {
  fontSize: 13,
  fontWeight: 700,
  color: STUDIO_INK_PRIMARY,
};

const subtitleStyle: CSSProperties = {
  fontSize: 11,
  color: STUDIO_INK_MUTED,
  marginTop: 2,
  lineHeight: 1.4,
};

export function StudioPanelHead({ title, subtitle, right }: Props) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
        gap: 8,
        marginBottom: 10,
      }}
    >
      <div>
        <div style={titleStyle}>{title}</div>
        {subtitle ? <div style={subtitleStyle}>{subtitle}</div> : null}
      </div>
      {right ?? null}
    </div>
  );
}
