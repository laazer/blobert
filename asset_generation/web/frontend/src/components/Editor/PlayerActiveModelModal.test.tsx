// @vitest-environment jsdom
import { describe, it, expect, vi, afterEach } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { PlayerActiveModelModal } from "./PlayerActiveModelModal";

function pickTestId(path: string): string {
  return `player-active-model-pick-${encodeURIComponent(path)}`;
}

afterEach(() => {
  cleanup();
});

describe("PlayerActiveModelModal", () => {
  const options = [
    { path: "player_exports/player_slime_blue_00.glb", label: "player_exports/player_slime_blue_00.glb (player_exports)" },
    { path: "animated_exports/spider_animated_00.glb", label: "animated_exports/spider_animated_00.glb" },
  ] as const;

  it("renders nothing when closed", () => {
    render(
      <PlayerActiveModelModal
        open={false}
        options={options}
        currentPath={null}
        busy={false}
        onClose={vi.fn()}
        onPick={vi.fn()}
      />,
    );
    expect(screen.queryByTestId("player-active-model-modal")).not.toBeInTheDocument();
  });

  it("lists options and calls onPick with the chosen path", async () => {
    const onPick = vi.fn().mockResolvedValue(undefined);
    render(
      <PlayerActiveModelModal
        open
        options={options}
        currentPath={null}
        busy={false}
        onClose={vi.fn()}
        onPick={onPick}
      />,
    );

    expect(screen.getByRole("dialog", { name: "Set game active model" })).toBeInTheDocument();
    fireEvent.click(screen.getByTestId(pickTestId("player_exports/player_slime_blue_00.glb")));
    expect(onPick).toHaveBeenCalledWith("player_exports/player_slime_blue_00.glb");
  });

  it("filters options by substring on path or label", () => {
    render(
      <PlayerActiveModelModal
        open
        options={options}
        currentPath={null}
        busy={false}
        onClose={vi.fn()}
        onPick={vi.fn()}
      />,
    );

    const input = screen.getByPlaceholderText(/player_slime or blobert/i);
    fireEvent.change(input, { target: { value: "spider_animated" } });

    expect(screen.queryByTestId(pickTestId("player_exports/player_slime_blue_00.glb"))).not.toBeInTheDocument();
    expect(screen.getByTestId(pickTestId("animated_exports/spider_animated_00.glb"))).toBeInTheDocument();
  });

  it("shows empty state when filter matches nothing", () => {
    render(
      <PlayerActiveModelModal
        open
        options={options}
        currentPath={null}
        busy={false}
        onClose={vi.fn()}
        onPick={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "zzznomatch" } });
    expect(screen.getByText(/No matches/)).toBeInTheDocument();
  });

  it("Cancel calls onClose", () => {
    const onClose = vi.fn();
    render(
      <PlayerActiveModelModal
        open
        options={options}
        currentPath={null}
        busy={false}
        onClose={onClose}
        onPick={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onClose).toHaveBeenCalled();
  });

  it("clicking overlay backdrop closes when not busy", () => {
    const onClose = vi.fn();
    render(
      <PlayerActiveModelModal
        open
        options={options}
        currentPath={null}
        busy={false}
        onClose={onClose}
        onPick={vi.fn()}
      />,
    );

    fireEvent.mouseDown(screen.getByTestId("player-active-model-modal-overlay"));
    expect(onClose).toHaveBeenCalled();
  });

  it("disables pick rows and Cancel when busy", () => {
    render(
      <PlayerActiveModelModal
        open
        options={options}
        currentPath={null}
        busy
        onClose={vi.fn()}
        onPick={vi.fn()}
      />,
    );

    expect(screen.getByTestId(pickTestId("player_exports/player_slime_blue_00.glb"))).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
  });
});
