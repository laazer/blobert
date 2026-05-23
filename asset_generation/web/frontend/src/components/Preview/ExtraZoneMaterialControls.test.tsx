// @vitest-environment jsdom
import { describe, it, expect, afterEach, beforeEach } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { mergeCanonicalZoneControlsForAllSlugs } from "../../utils/animatedZoneControlsMerge";
import { ExtraZoneMaterialControls } from "./ExtraZoneMaterialControls";

afterEach(() => {
  cleanup();
});

describe("ExtraZoneMaterialControls", () => {
  beforeEach(() => {
    const controls = mergeCanonicalZoneControlsForAllSlugs({}, ["spider"]);
    useAppStore.setState({
      animatedBuildControls: controls,
      animatedBuildOptionValues: {
        spider: {
          extra_zone_body_finish: "metallic",
          extra_zone_body_hex: "aabbcc",
        },
      },
    });
  });

  it("renders extra geometry color sections on Colors tab", () => {
    render(<ExtraZoneMaterialControls slug="spider" />);
    expect(screen.getByText(/Geometry extra materials/i)).toBeInTheDocument();
    expect(screen.getByText(/Extra geometry — Body/i)).toBeInTheDocument();
  });

  it("renders studio material fill when useStudioPicker", () => {
    render(
      <ExtraZoneMaterialControls slug="spider" useStudioPicker accentHue="210" zoneFilter="body" />,
    );
    expect(screen.getByTestId("studio-extra-material-body")).toBeInTheDocument();
  });
});
