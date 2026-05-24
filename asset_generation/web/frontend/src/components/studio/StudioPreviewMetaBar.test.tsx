// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import * as client from "../../api/client";
import { useAppStore } from "../../store/useAppStore";
import type { ModelRegistryPayload } from "../../types";
import { StudioPreviewMetaBar } from "./StudioPreviewMetaBar";

vi.mock("../../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/client")>();
  return { ...actual, fetchModelRegistry: vi.fn(), patchRegistryEnemyVersion: vi.fn() };
});

const registry: ModelRegistryPayload = {
  schema_version: 1,
  enemies: {
    spider: {
      versions: [
        {
          id: "spider_animated_05",
          path: "animated_exports/spider_animated_05.glb",
          draft: false,
          in_use: true,
          name: null,
          tags: ["spider", "fire"],
        },
      ],
    },
  },
  player: null,
  player_active_visual: null,
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("StudioPreviewMetaBar", () => {
  beforeEach(() => {
    vi.mocked(client.fetchModelRegistry).mockResolvedValue(registry);
    vi.mocked(client.patchRegistryEnemyVersion).mockResolvedValue(registry);
    useAppStore.setState({
      commandContext: { cmd: "animated", enemy: "spider" },
      activeGlbUrl: "/api/assets/animated_exports/spider_animated_05.glb",
      registryReloadSeq: 0,
      bumpRegistryReload: vi.fn(),
    });
  });

  it("renders read-only filename chip, editable name chip, and tag chips", async () => {
    render(<StudioPreviewMetaBar embedded />);
    await waitFor(() => {
      expect(screen.getByTestId("studio-preview-meta-filename")).toBeInTheDocument();
    });
    expect(screen.getByTestId("studio-preview-meta-filename")).toHaveTextContent("spider_animated_05.glb");
    const nameInput = screen.getByTestId("studio-preview-meta-name");
    expect(nameInput).toHaveAttribute("placeholder", "Untitled");
    expect(screen.getByText("fire")).toBeInTheDocument();
    expect(screen.queryByText("spider")).toBeNull();
  });

  it("patches display name on blur", async () => {
    render(<StudioPreviewMetaBar />);
    await waitFor(() => screen.getByTestId("studio-preview-meta-name"));
    const nameInput = screen.getByTestId("studio-preview-meta-name");
    fireEvent.change(nameInput, { target: { value: "Ash Widow" } });
    fireEvent.blur(nameInput);
    await waitFor(() => {
      expect(client.patchRegistryEnemyVersion).toHaveBeenCalledWith("spider", "spider_animated_05", {
        name: "Ash Widow",
      });
    });
  });

  it("adds a tag from the inline adder", async () => {
    render(<StudioPreviewMetaBar />);
    await waitFor(() => screen.getByTestId("studio-version-tag-add-spider_animated_05"));
    fireEvent.click(screen.getByTestId("studio-version-tag-add-spider_animated_05"));
    const input = screen.getByTestId("studio-version-tag-input-spider_animated_05");
    fireEvent.change(input, { target: { value: "boss" } });
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() => {
      expect(client.patchRegistryEnemyVersion).toHaveBeenCalledWith("spider", "spider_animated_05", {
        tags: ["spider", "fire", "boss"],
      });
    });
  });
});
