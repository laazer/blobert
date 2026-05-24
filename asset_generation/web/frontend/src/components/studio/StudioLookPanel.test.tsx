// @vitest-environment jsdom
import { describe, it, expect, afterEach, beforeEach, vi } from "vitest";
import { cleanup, render, screen, fireEvent, within } from "@testing-library/react";
import { mergeBuildOptionValues } from "../../api/client";
import { useAppStore } from "../../store/useAppStore";
import { mergeCanonicalZoneControlsForAllSlugs } from "../../utils/animatedZoneControlsMerge";
import { StudioLookPanel } from "./StudioLookPanel";

afterEach(() => {
  cleanup();
});

describe("StudioLookPanel (redesign_v2 IA)", () => {
  beforeEach(() => {
    const controls = mergeCanonicalZoneControlsForAllSlugs({}, ["spider"]);
    useAppStore.setState({
      animatedBuildControls: controls,
      animatedBuildOptionValues: mergeBuildOptionValues(controls, {}),
    });
  });

  it("renders v2 sections: element, part picker, background", () => {
    render(<StudioLookPanel slug="spider" />);

    expect(screen.getByTestId("studio-look-panel")).toBeInTheDocument();
    expect(screen.getByTestId("studio-look-element-grid")).toBeInTheDocument();
    expect(screen.getByTestId("studio-look-part-picker")).toBeInTheDocument();
    expect(screen.getByTestId("studio-look-background")).toBeInTheDocument();
    expect(screen.getByTestId("studio-zone-fill-body-background")).toBeInTheDocument();
  });

  it("applies fire palette from element grid", () => {
    render(<StudioLookPanel slug="spider" />);
    fireEvent.click(screen.getByTestId("studio-look-element-fire"));

    const values = useAppStore.getState().animatedBuildOptionValues.spider ?? {};
    expect(values.feat_body_hex).toBe("#b83228");
    expect(values.feat_body_finish).toBe("glossy");
    expect(useAppStore.getState().commandExportFinish).toBe("glossy");
    expect(useAppStore.getState().commandExportHexColor).toBe("#b83228");
  });

  it("applies lightning palette when body already uses spots texture", () => {
    useAppStore.setState({
      animatedBuildOptionValues: mergeBuildOptionValues(useAppStore.getState().animatedBuildControls, {
        spider: {
          feat_body_texture_mode: "spots",
          feat_body_hex: "#6b3d8f",
          feat_body_finish: "matte",
          feat_body_color_mode: "image",
          feat_body_color_image_id: "hash_texture",
        },
      }),
    });
    render(<StudioLookPanel slug="spider" />);
    fireEvent.click(screen.getByTestId("studio-look-element-lightning"));

    const values = useAppStore.getState().animatedBuildOptionValues.spider ?? {};
    expect(values.feat_body_hex).toBe("#e8e0a0");
    expect(values.feat_body_finish).toBe("metallic");
    expect(values.feat_body_color_mode).toBe("single");
    expect(values.feat_body_color_image_id).toBe("");
    expect(useAppStore.getState().commandExportHexColor).toBe("#e8e0a0");
  });

  it("sets finish and pattern mode for active zone", () => {
    render(<StudioLookPanel slug="spider" />);

    fireEvent.click(screen.getByTestId("studio-look-finish-body-metallic"));
    fireEvent.click(screen.getByTestId("studio-look-pattern-body-stripes"));

    const values = useAppStore.getState().animatedBuildOptionValues.spider ?? {};
    expect(values.feat_body_finish).toBe("metallic");
    expect(values.feat_body_texture_mode).toBe("stripes");
  });

  it("shows only pipeline texture modes as pattern tiles", () => {
    render(<StudioLookPanel slug="spider" />);
    expect(screen.getByTestId("studio-look-pattern-body-plain")).toBeInTheDocument();
    expect(screen.getByTestId("studio-look-pattern-body-dots")).toBeInTheDocument();
    expect(screen.getByTestId("studio-look-pattern-body-stripes")).toBeInTheDocument();
    expect(screen.getByTestId("studio-look-pattern-body-checkerboard")).toBeInTheDocument();
    expect(screen.queryByTestId("studio-look-pattern-body-swirl")).not.toBeInTheDocument();
    expect(screen.queryByTestId("studio-look-pattern-body-cracks")).not.toBeInTheDocument();
    expect(screen.queryByTestId("studio-look-pattern-body-assets")).not.toBeInTheDocument();
  });

  it("exposes Color / Gradient / Image tabs on background fill", () => {
    render(<StudioLookPanel slug="spider" />);
    const fill = within(screen.getByTestId("studio-zone-fill-body-background"));
    expect(fill.getByRole("tab", { name: "Color" })).toBeInTheDocument();
    expect(fill.getByRole("tab", { name: "Gradient" })).toBeInTheDocument();
    expect(fill.getByRole("tab", { name: "Image" })).toBeInTheDocument();
  });

  it("switches active part via part picker", () => {
    render(<StudioLookPanel slug="spider" />);

    fireEvent.click(screen.getByTestId("studio-look-part-chip-head"));
    expect(screen.getByTestId("studio-zone-fill-head-background")).toBeInTheDocument();
    expect(screen.getByText(/Background · Head/)).toBeInTheDocument();
  });

  it("supports controlled activeZone from parent", () => {
    const onZone = vi.fn();
    render(<StudioLookPanel slug="spider" activeZone="head" onActiveZoneChange={onZone} />);
    expect(screen.getByTestId("studio-zone-fill-head-background")).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("studio-look-part-chip-body"));
    expect(onZone).toHaveBeenCalledWith("body");
  });
});
