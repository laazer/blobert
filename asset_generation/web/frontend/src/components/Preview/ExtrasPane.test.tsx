// @vitest-environment jsdom
import { describe, it, expect, afterEach, beforeEach } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { mergeCanonicalZoneControlsForAllSlugs } from "../../utils/animatedZoneControlsMerge";
import { ExtrasPane } from "./ExtrasPane";

afterEach(() => {
  cleanup();
});

describe("ExtrasPane", () => {
  beforeEach(() => {
    const controls = mergeCanonicalZoneControlsForAllSlugs({}, ["slug"]);
    useAppStore.setState({
      commandContext: { cmd: "animated", enemy: "slug" },
      animatedEnemyMeta: [{ slug: "slug", label: "Slug" }],
      animatedBuildControls: controls,
      animatedBuildOptionValues: {
        slug: { extra_zone_body_kind: "none", extra_zone_body_spike_count: 8 },
      },
      centerPanel: "extras",
    });
  });

  it("shows empty-state copy when not on animated enemy", () => {
    useAppStore.setState({ commandContext: { cmd: "animated", enemy: "all" } });
    render(<ExtrasPane />);
    expect(screen.getByText(/pick an enemy/i)).toBeInTheDocument();
  });

  it("renders Extras tab content with zone sections for slug", () => {
    render(<ExtrasPane />);
    expect(screen.getByText(/Geometry extras \(per zone\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Zone: body/i)).toBeInTheDocument();
  });

  it("updates store when extra kind changes", () => {
    render(<ExtrasPane />);
    const select = screen.getByLabelText("body extra kind");
    fireEvent.change(select, { target: { value: "spikes" } });
    expect(useAppStore.getState().animatedBuildOptionValues.slug?.extra_zone_body_kind).toBe("spikes");
  });
});
