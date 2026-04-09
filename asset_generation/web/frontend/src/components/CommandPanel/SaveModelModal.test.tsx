// @vitest-environment jsdom
import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { cleanup, render, screen, waitFor, fireEvent } from "@testing-library/react";
import * as client from "../../api/client";
import { SaveModelModal } from "./SaveModelModal";

vi.mock("../../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/client")>();
  return {
    ...actual,
    fetchEnemyFamilySlots: vi.fn(),
    fetchModelRegistry: vi.fn(),
    putEnemyFamilySlots: vi.fn(),
    patchRegistryEnemyVersion: vi.fn(),
  };
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("SaveModelModal", () => {
  const registry = {
    schema_version: 2,
    enemies: {
      spider: {
        versions: [
          {
            id: "spider_animated_00",
            path: "animated_exports/spider_animated_00.glb",
            draft: false,
            in_use: true,
          },
        ],
      },
    },
    player_active_visual: null,
  } as const;

  beforeEach(() => {
    vi.mocked(client.fetchEnemyFamilySlots).mockResolvedValue({
      family: "spider",
      version_ids: ["spider_animated_00"],
      resolved_paths: ["animated_exports/spider_animated_00.glb"],
    });
    vi.mocked(client.fetchModelRegistry).mockResolvedValue(registry as never);
    vi.mocked(client.putEnemyFamilySlots).mockResolvedValue({
      family: "spider",
      version_ids: ["spider_animated_00"],
      resolved_paths: ["animated_exports/spider_animated_00.glb"],
    });
    vi.mocked(client.patchRegistryEnemyVersion).mockResolvedValue(registry as never);
  });

  it("renders portaled dialog and loads slots", async () => {
    const onClose = vi.fn();
    const { container } = render(<SaveModelModal open family="spider" onClose={onClose} />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Save model" })).toBeInTheDocument();
    });
    expect(container.querySelector('[role="dialog"]')).toBeNull();
    expect(document.body.querySelector('[role="dialog"]')).not.toBeNull();
    expect(client.fetchEnemyFamilySlots).toHaveBeenCalledWith("spider");
  });

  it("Save in slot calls putEnemyFamilySlots", async () => {
    const onClose = vi.fn();
    render(<SaveModelModal open family="spider" onClose={onClose} />);

    await waitFor(() => expect(screen.getByLabelText(/Slot to set/i)).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Save in slot" }));

    await waitFor(() => {
      expect(client.putEnemyFamilySlots).toHaveBeenCalledWith("spider", ["spider_animated_00"]);
      expect(onClose).toHaveBeenCalled();
    });
  });

  it("Save as draft calls patchRegistryEnemyVersion", async () => {
    const onClose = vi.fn();
    render(<SaveModelModal open family="spider" onClose={onClose} />);

    await waitFor(() => expect(screen.getByRole("button", { name: "Save as draft" })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Save as draft" }));

    await waitFor(() => {
      expect(client.patchRegistryEnemyVersion).toHaveBeenCalledWith("spider", "spider_animated_00", {
        draft: true,
        in_use: false,
      });
      expect(onClose).toHaveBeenCalled();
    });
    expect(client.putEnemyFamilySlots).not.toHaveBeenCalled();
  });

  it("prefills version name from registry", async () => {
    vi.mocked(client.fetchModelRegistry).mockResolvedValue({
      schema_version: 2,
      enemies: {
        spider: {
          versions: [
            {
              id: "spider_animated_00",
              path: "animated_exports/spider_animated_00.glb",
              draft: false,
              in_use: true,
              name: "Alpha",
            },
          ],
        },
      },
      player_active_visual: null,
    } as never);
    render(<SaveModelModal open family="spider" onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Version name/i)).toHaveValue("Alpha");
    });
  });

  it("Save name calls patch when value changed", async () => {
    const onClose = vi.fn();
    render(<SaveModelModal open family="spider" onClose={onClose} />);

    await waitFor(() => expect(screen.getByLabelText(/Version name/i)).toBeInTheDocument());
    fireEvent.change(screen.getByLabelText(/Version name/i), { target: { value: "New label" } });
    fireEvent.click(screen.getByRole("button", { name: "Save name" }));

    await waitFor(() => {
      expect(client.patchRegistryEnemyVersion).toHaveBeenCalledWith("spider", "spider_animated_00", {
        name: "New label",
      });
      expect(onClose).toHaveBeenCalled();
    });
  });
});
