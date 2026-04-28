// @vitest-environment jsdom
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ColorPickerTabs, type ColorPickerValue } from "./ColorPickerTabs";

vi.mock("./modes/ImageMode", () => ({
  ImageMode: ({
    onFileChange,
  }: {
    onFileChange: (file: File | null, preview?: string, assetId?: string) => void;
  }) => (
    <button
      type="button"
      onClick={() => onFileChange(null, "/assets/textures/body.png", "texture-body-01")}
    >
      Select mocked texture
    </button>
  ),
}));

describe("ColorPickerTabs image asset serialization regression", () => {
  it("BUG-body-part-image-not-applied-01 preserves assetId from image selection", () => {
    const onChange = vi.fn();
    const value: ColorPickerValue = { type: "image", file: null, preview: undefined };

    render(
      <ColorPickerTabs
        mode="image"
        onModeChange={() => {}}
        value={value}
        onChange={onChange}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "Select mocked texture" }));

    expect(onChange).toHaveBeenCalledWith({
      type: "image",
      file: null,
      preview: "/assets/textures/body.png",
      assetId: "texture-body-01",
    });
  });
});
