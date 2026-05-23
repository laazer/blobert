import type { CSSProperties, ReactNode } from "react";

type Props = {
  color: string;
  size?: number;
  selected?: boolean;
  onClick?: () => void;
  title?: string;
  "data-testid"?: string;
  children?: ReactNode;
};

export function StudioSwatch({
  color,
  size = 26,
  selected = false,
  onClick,
  title,
  "data-testid": testId,
  children,
}: Props) {
  const style: CSSProperties = {
    width: size,
    height: size,
    borderRadius: "50%",
    background: color,
    border: selected ? "2px solid #ededf0" : "1px solid rgba(255,255,255,0.12)",
    boxShadow: selected ? `0 0 0 2px ${color}55` : "none",
    cursor: onClick ? "pointer" : "default",
    padding: 0,
    flexShrink: 0,
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
  };

  if (onClick) {
    return (
      <button
        type="button"
        title={title ?? color}
        aria-label={title ?? color}
        aria-pressed={selected}
        data-testid={testId}
        style={style}
        onClick={onClick}
      >
        {children}
      </button>
    );
  }

  return (
    <span title={title ?? color} data-testid={testId} style={style}>
      {children}
    </span>
  );
}
