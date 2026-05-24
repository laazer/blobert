import type { AnimatedBuildControlDef } from "../../types";
import {
  SPIDER_ALLOWED_EYE_COUNTS,
  SPIDER_DEFAULT_EYE_COUNT,
} from "../../constants/spiderBuildControls";
import { StudioBuildSegmentedRow } from "./StudioBuildSegmentedRow";

type Props = {
  def: AnimatedBuildControlDef;
  value: unknown;
  accentHue: string;
  disabled?: boolean;
  onChange: (v: number) => void;
};

function coerceEyeCount(value: unknown, fallback: number): number {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const n = Number(value);
    if (Number.isFinite(n)) return n;
  }
  return fallback;
}

/** Spider eye count — always segmented pills (never slider / dropdown / stepper). */
export function StudioBuildEyeCountRow({ def, value, accentHue, disabled, onChange }: Props) {
  const fallback =
    def.type === "select" || def.type === "int" ? def.default : SPIDER_DEFAULT_EYE_COUNT;
  const n = coerceEyeCount(value, fallback);
  const fromDef =
    def.type === "select" && def.options.length > 0
      ? [...def.options].sort((a, b) => a - b)
      : [...SPIDER_ALLOWED_EYE_COUNTS];

  return (
    <StudioBuildSegmentedRow
      label="Count"
      controlKey="eye_count"
      layout="inline"
      accentHue={accentHue}
      disabled={disabled}
      value={n}
      options={fromDef.map((opt) => ({ value: opt, label: String(opt) }))}
      onChange={(v) => onChange(v)}
    />
  );
}
