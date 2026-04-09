// @vitest-environment jsdom
import { describe, it, expect, vi, afterEach } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import type { RegistryEnemyVersion } from "../../types";
import { AddEnemySlotModal } from "./AddEnemySlotModal";

afterEach(() => {
  cleanup();
});

const versions: RegistryEnemyVersion[] = [
  {
    id: "spider_animated_draft",
    path: "animated_exports/spider_animated_draft.glb",
    draft: true,
    in_use: false,
  },
  {
    id: "spider_animated_00",
    path: "animated_exports/spider_animated_00.glb",
    draft: false,
    in_use: true,
  },
  {
    id: "spider_animated_01",
    path: "animated_exports/spider_animated_01.glb",
    draft: false,
    in_use: false,
  },
];

describe("AddEnemySlotModal", () => {
  it("does not render when closed", () => {
    render(
      <AddEnemySlotModal
        open={false}
        family="spider"
        versions={versions}
        slotVersionIds={["spider_animated_00"]}
        preferredVersionId={null}
        busy={false}
        onClose={vi.fn()}
        onPick={vi.fn()}
      />,
    );
    expect(screen.queryByTestId("add-enemy-slot-modal")).not.toBeInTheDocument();
  });

  it("lists only non-draft versions not already in slots", () => {
    render(
      <AddEnemySlotModal
        open
        family="spider"
        versions={versions}
        slotVersionIds={["spider_animated_00"]}
        preferredVersionId={null}
        busy={false}
        onClose={vi.fn()}
        onPick={vi.fn()}
      />,
    );

    expect(screen.getByRole("dialog", { name: /Add spawn slot — spider/ })).toBeInTheDocument();
    expect(screen.queryByTestId("registry-add-slot-pick-spider_animated_draft")).not.toBeInTheDocument();
    expect(screen.queryByTestId("registry-add-slot-pick-spider_animated_00")).not.toBeInTheDocument();
    expect(screen.getByTestId("registry-add-slot-pick-spider_animated_01")).toBeInTheDocument();
  });

  it("calls onPick when Add is clicked", () => {
    const onPick = vi.fn();
    render(
      <AddEnemySlotModal
        open
        family="spider"
        versions={versions}
        slotVersionIds={["spider_animated_00"]}
        preferredVersionId={null}
        busy={false}
        onClose={vi.fn()}
        onPick={onPick}
      />,
    );

    fireEvent.click(screen.getByTestId("registry-add-slot-pick-spider_animated_01"));
    expect(onPick).toHaveBeenCalledWith("spider_animated_01");
  });

  it("shows empty copy when no versions remain to add", () => {
    render(
      <AddEnemySlotModal
        open
        family="spider"
        versions={versions}
        slotVersionIds={["spider_animated_00", "spider_animated_01"]}
        preferredVersionId={null}
        busy={false}
        onClose={vi.fn()}
        onPick={vi.fn()}
      />,
    );

    expect(screen.getByText(/No more non-draft versions to add/)).toBeInTheDocument();
  });

  it("Cancel calls onClose", () => {
    const onClose = vi.fn();
    render(
      <AddEnemySlotModal
        open
        family="spider"
        versions={versions}
        slotVersionIds={["spider_animated_00"]}
        preferredVersionId={null}
        busy={false}
        onClose={onClose}
        onPick={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onClose).toHaveBeenCalled();
  });
});
