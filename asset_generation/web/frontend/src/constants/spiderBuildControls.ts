import type { AnimatedBuildControlDef } from "../types";

/** Mirrors ``AnimatedSpider.ALLOWED_EYE_COUNTS`` (Python single source). */
export const SPIDER_ALLOWED_EYE_COUNTS: readonly number[] = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 99];

export const SPIDER_DEFAULT_EYE_COUNT = 2;

/** Spider eye block for studio Build + offline meta (aligned with ``_spider_eye_control_defs``). */
export function syntheticSpiderEyeBuildDefs(): AnimatedBuildControlDef[] {
  return [
    {
      key: "eye_count",
      label: "Count",
      type: "select",
      options: [...SPIDER_ALLOWED_EYE_COUNTS],
      default: SPIDER_DEFAULT_EYE_COUNT,
    },
    {
      key: "eye_distribution",
      label: "Eye placement",
      type: "select_str",
      options: ["uniform", "random", "separate"],
      default: "uniform",
      segmented: true,
    },
    {
      key: "eye_uniform_shape",
      label: "Eye uniform pattern",
      type: "select_str",
      options: ["arc"],
      default: "arc",
    },
    {
      key: "eye_clustering",
      label: "Eye clustering (multi-eye)",
      type: "float",
      min: 0,
      max: 1,
      step: 0.05,
      default: 0.5,
      unit: "0–1",
    },
  ];
}
