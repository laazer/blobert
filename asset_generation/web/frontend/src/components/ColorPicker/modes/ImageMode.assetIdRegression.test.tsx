// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ImageMode } from "./ImageMode";

vi.mock("../../../api/client", () => ({
  fetchTextureAssets: vi.fn(async () => [
    {
      id: "demo_textures3",
      filename: "demo textures3.png",
      display_name: "Demo Textures 3",
      description: "",
      layout: "single",
      url: "/api/assets/textures/file/demo%20textures3.png",
      width: 512,
      height: 512,
      tiling_supported: true,
    },
  ]),
}));

describe("ImageMode asset id carryover", () => {
  beforeEach(() => {
    window.URL.createObjectURL = vi.fn(() => "blob:mock-url");
    window.URL.revokeObjectURL = vi.fn();
  });

  it("preserves asset id when clearing uv rect from a known preview url", async () => {
    const onFileChange = vi.fn();
    render(
      <ImageMode
        file={null}
        preview="/api/assets/textures/file/demo%20textures3.png"
        assetId={undefined}
        uvRect={{ u0: 0.1, v0: 0.2, u1: 0.7, v1: 0.8 }}
        onFileChange={onFileChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Use full image" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Use full image" }));

    expect(onFileChange).toHaveBeenCalledWith(
      null,
      "/api/assets/textures/file/demo%20textures3.png",
      "demo_textures3",
      null,
    );
  });
});
