import { describe, it, expect } from "vitest";
import {
  classifyBuildControlSection,
  partitionBuildControls,
  summarizeBuildSection,
} from "./buildControlSections";
import type { AnimatedBuildControlDef } from "../types";

describe("buildControlSections", () => {
  it("routes eye and body controls into expected sections", () => {
    expect(classifyBuildControlSection("eye_count", "select")).toBe("eyes");
    expect(classifyBuildControlSection("body_type", "select_str")).toBe("body");
    expect(classifyBuildControlSection("RIG_HEAD_ROT_X", "float")).toBe("rig");
    expect(classifyBuildControlSection("BODY_SCALE_Y_BASE", "float")).toBe("body");
    expect(classifyBuildControlSection("STRIPE_WIDTH", "float")).toBe("pattern");
  });

  it("partitions defs by section", () => {
    const defs: AnimatedBuildControlDef[] = [
      { key: "body_type", label: "Body", type: "select_str", options: ["default"], default: "default" },
      { key: "eye_count", label: "Count", type: "select", options: [1, 2], default: 2 },
      { key: "RIG_HEAD_ROT_X", label: "Head X", type: "float", min: 0, max: 1, step: 0.1, default: 0 },
    ];
    const parts = partitionBuildControls(defs);
    expect(parts.body).toHaveLength(1);
    expect(parts.eyes).toHaveLength(1);
    expect(parts.rig).toHaveLength(1);
  });

  it("summarizes eyes section from values", () => {
    const defs: AnimatedBuildControlDef[] = [
      { key: "eye_count", label: "Count", type: "select", options: [2], default: 2 },
      { key: "eye_shape", label: "Shape", type: "select_str", options: ["circle"], default: "circle" },
      { key: "eye_distribution", label: "Placement", type: "select_str", options: ["uniform"], default: "uniform" },
      { key: "pupil_enabled", label: "Pupil", type: "bool", default: true },
    ];
    const summary = summarizeBuildSection("eyes", defs, {
      eye_count: 2,
      eye_shape: "circle",
      eye_distribution: "uniform",
      pupil_enabled: true,
    });
    expect(summary).toContain("2");
    expect(summary).toContain("pupil");
  });
});
