import type { CSSProperties } from "react";
import {
  studioBuildRowLabel,
  studioBuildRowStacked,
  studioBuildSegmentButton,
  studioBuildSegmentTrack,
} from "./studioBuildStyles";

const scrollTrack: CSSProperties = {
  ...studioBuildSegmentTrack,
  flexWrap: "nowrap",
  overflowX: "auto",
  flex: 1,
  minWidth: 0,
};

type SegmentOption<T extends string | number | boolean> = {
  value: T;
  label: string;
};

type Props<T extends string | number | boolean> = {
  label: string;
  controlKey: string;
  options: SegmentOption<T>[];
  value: T;
  accentHue: string;
  disabled?: boolean;
  layout?: "inline" | "stacked";
  onChange: (v: T) => void;
};

export function StudioBuildSegmentedRow<T extends string | number | boolean>({
  label,
  controlKey,
  options,
  value,
  accentHue,
  disabled,
  layout = "inline",
  onChange,
}: Props<T>) {
  if (options.length === 0) return null;

  const stacked = layout === "stacked";
  const useScroll = !stacked && options.length > 4;
  const trackCls = useScroll ? "studio-build-segment-scroll" : undefined;
  const trackStyle: CSSProperties = useScroll ? scrollTrack : studioBuildSegmentTrack;

  return (
    <div
      style={{
        ...(stacked ? studioBuildRowStacked : { display: "flex", alignItems: "center", gap: 10 }),
        opacity: disabled ? 0.42 : 1,
        pointerEvents: disabled ? "none" : undefined,
      }}
      data-testid={`studio-build-segmented-${controlKey}`}
    >
      <div style={stacked ? { ...studioBuildRowLabel, minWidth: 0 } : studioBuildRowLabel}>{label}</div>
      <div className={trackCls} style={trackStyle} role="group" aria-label={label}>
        {options.map((opt) => {
          const active = value === opt.value;
          return (
            <button
              key={String(opt.value)}
              type="button"
              aria-pressed={active}
              disabled={disabled}
              style={studioBuildSegmentButton(active, accentHue)}
              onClick={() => onChange(opt.value)}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
