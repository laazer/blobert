// @vitest-environment jsdom
/**
 * Studio Build inspector — controls stay in contextual sections (not a flat Rig/Mesh dump).
 */
import { describe, it, expect, afterEach } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import type { AnimatedBuildControlDef } from "../../types";
import { StudioBuildPanel } from "./StudioBuildPanel";

const noop = () => {};

const DEFS: AnimatedBuildControlDef[] = [
  { key: "body_type", label: "Body type", type: "select_str", options: ["default"], default: "default" },
  { key: "BODY_SCALE_Y", label: "Body Y", type: "float", min: 0, max: 2, step: 0.01, default: 1 },
  { key: "eye_count", label: "Count", type: "select", options: [2], default: 2 },
  { key: "eye_clustering", label: "Clustering", type: "float", min: 0, max: 1, step: 0.05, default: 0.5 },
  { key: "tail_enabled", label: "Tail", type: "bool", default: false },
  { key: "tail_length", label: "Length", type: "float", min: 0, max: 1, step: 0.01, default: 0.3 },
  { key: "LEG_COUNT", label: "Leg count", type: "float", min: 0, max: 12, step: 1, default: 8 },
  { key: "RIG_SPINE", label: "Spine", type: "float", min: 0, max: 1, step: 0.01, default: 0 },
];

afterEach(() => cleanup());

describe("StudioBuildPanel grouping", () => {
  it("places sliders inside their section, not a separate mesh bucket", () => {
    render(
      <StudioBuildPanel
        slug="spider"
        defs={DEFS}
        values={{ eye_count: 2, tail_enabled: true }}
        accentHue="#ff6b3d"
        isRowDisabled={() => false}
        onChange={noop}
        meshPartTree={null}
      />,
    );

    expect(screen.queryByTestId("studio-build-float-section-mesh")).toBeNull();
    expect(screen.queryByTestId("studio-build-float-section-rig")).toBeNull();

    expect(within(screen.getByTestId("studio-build-section-body")).getByTestId("studio-build-slider-BODY_SCALE_Y")).toBeInTheDocument();
    expect(within(screen.getByTestId("studio-build-section-eyes")).getByTestId("studio-build-slider-eye_clustering")).toBeInTheDocument();
    expect(within(screen.getByTestId("studio-build-section-tail")).getByTestId("studio-build-slider-tail_length")).toBeInTheDocument();
    expect(within(screen.getByTestId("studio-build-section-limbs")).getByTestId("studio-build-slider-LEG_COUNT")).toBeInTheDocument();
    expect(within(screen.getByTestId("studio-build-section-rig")).getByTestId("studio-build-slider-RIG_SPINE")).toBeInTheDocument();
  });
});
