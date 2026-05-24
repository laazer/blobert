import type { CSSProperties } from "react";
import { versionThumbGradient } from "../../utils/studioVersionUi";

type Props = {
  hue: string;
  title?: string;
};

const box: CSSProperties = {
  width: 32,
  height: 32,
  borderRadius: 7,
  flexShrink: 0,
  boxShadow: "inset -3px -3px 6px rgba(0,0,0,0.35)",
};

export function StudioVersionThumb({ hue, title }: Props) {
  return (
    <div
      title={title}
      aria-hidden
      style={{
        ...box,
        background: versionThumbGradient(hue),
      }}
    />
  );
}
