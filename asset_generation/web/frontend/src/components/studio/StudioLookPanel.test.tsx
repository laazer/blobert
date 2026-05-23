// @vitest-environment jsdom
import { describe, it, expect, afterEach, beforeEach } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { mergeBuildOptionValues } from "../../api/client";
import { useAppStore } from "../../store/useAppStore";
import { mergeCanonicalZoneControlsForAllSlugs } from "../../utils/animatedZoneControlsMerge";
import { StudioLookPanel } from "./StudioLookPanel";

afterEach(() => {
  cleanup();
});

describe("StudioLookPanel", () => {
  beforeEach(() => {
    const controls = mergeCanonicalZoneControlsForAllSlugs({}, ["spider"]);
    useAppStore.setState({
      animatedBuildControls: controls,
      animatedBuildOptionValues: mergeBuildOptionValues(controls, {}),
    });
  });

  it("renders element grid and applies fire palette on click", () => {
    render(<StudioLookPanel slug="spider" />);

    expect(screen.getByTestId("studio-look-panel")).toBeInTheDocument();
    expect(screen.getByTestId("studio-look-element-fire")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("studio-look-element-fire"));

    const values = useAppStore.getState().animatedBuildOptionValues.spider ?? {};
    expect(values.feat_body_hex).toBe("#b83228");
    expect(values.feat_body_finish).toBe("glossy");
  });

  it("sets body finish and pattern mode from mockup controls", () => {
    render(<StudioLookPanel slug="spider" />);

    fireEvent.click(screen.getByTestId("studio-look-body-finish-metallic"));
    fireEvent.click(screen.getByTestId("studio-look-pattern-stripes"));

    const values = useAppStore.getState().animatedBuildOptionValues.spider ?? {};
    expect(values.feat_body_finish).toBe("metallic");
    expect(values.feat_body_texture_mode).toBe("stripes");
  });
});
