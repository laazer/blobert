import { describe, it, expect } from "vitest";
import type { AnimatedBuildControlDef } from "../types";
import {
  isProceduralBuildCatalogIncomplete,
  proceduralBuildControlDefs,
} from "./proceduralBuildCatalog";

const RIG: AnimatedBuildControlDef = {
  key: "RIG_HEAD_ROT_X",
  label: "Head X",
  type: "float",
  min: 0,
  max: 1,
  step: 0.1,
  default: 0,
};

const EYE: AnimatedBuildControlDef = {
  key: "eye_count",
  label: "Count",
  type: "select",
  options: [2],
  default: 2,
};

const FEAT: AnimatedBuildControlDef = {
  key: "feat_body_hex",
  label: "Body hex",
  type: "str",
  default: "",
};

describe("proceduralBuildCatalog", () => {
  it("proceduralBuildControlDefs strips feat and extra_zone keys", () => {
    expect(proceduralBuildControlDefs([RIG, EYE, FEAT]).map((d) => d.key)).toEqual([
      "RIG_HEAD_ROT_X",
      "eye_count",
    ]);
  });

  it("detects incomplete catalog when only eye synthetics remain", () => {
    expect(isProceduralBuildCatalogIncomplete("spider", [EYE], "ok")).toBe(true);
    expect(isProceduralBuildCatalogIncomplete("spider", [EYE, RIG], "ok")).toBe(false);
  });

  it("detects fallback meta backend", () => {
    expect(isProceduralBuildCatalogIncomplete("spider", [RIG], "fallback")).toBe(true);
  });
});
