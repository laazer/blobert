// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { mergeCanonicalZoneControlsForAllSlugs } from "../../utils/animatedZoneControlsMerge";
import { ElementPaletteDefaultsModal } from "./ElementPaletteDefaultsModal";

const controls = mergeCanonicalZoneControlsForAllSlugs({}, ["spider"]);
const knownDefKeys = new Set(
  (controls.spider ?? []).map((d) => d.key),
);

afterEach(() => cleanup());

describe("ElementPaletteDefaultsModal", () => {
  it("renders full zone material controls and saves finish changes", () => {
    const onSave = vi.fn();
    render(
      <ElementPaletteDefaultsModal
        open
        slug="spider"
        elementId="fire"
        defs={controls.spider ?? []}
        knownDefKeys={knownDefKeys}
        onClose={vi.fn()}
        onSave={onSave}
        onResetBuiltin={vi.fn()}
      />,
    );

    expect(screen.getByTestId("element-defaults-zone-body")).toBeInTheDocument();
    expect(screen.getByTestId("studio-zone-fill-body-background")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("studio-look-finish-body-metallic"));
    fireEvent.click(screen.getByTestId("element-palette-save"));

    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({
        feat_body_finish: "metallic",
      }),
    );
  });

  it("exposes color / gradient / image tabs on background fill", () => {
    render(
      <ElementPaletteDefaultsModal
        open
        slug="spider"
        elementId="fire"
        defs={controls.spider ?? []}
        knownDefKeys={knownDefKeys}
        onClose={vi.fn()}
        onSave={vi.fn()}
        onResetBuiltin={vi.fn()}
      />,
    );

    const fill = within(screen.getByTestId("studio-zone-fill-body-background"));
    expect(fill.getByRole("tab", { name: "Color" })).toBeInTheDocument();
    expect(fill.getByRole("tab", { name: "Gradient" })).toBeInTheDocument();
    expect(fill.getByRole("tab", { name: "Image" })).toBeInTheDocument();
  });
});
