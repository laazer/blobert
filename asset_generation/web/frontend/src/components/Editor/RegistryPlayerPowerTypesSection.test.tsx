// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { cleanup, render, screen, waitFor, fireEvent } from "@testing-library/react";
import type { RegistryEnemyVersion } from "../../types";
import {
  PLAYER_POWER_TYPES_HEADING,
  RegistryPlayerPowerTypesSection,
} from "./RegistryPlayerPowerTypesSection";
import { savePlayerPowerTypes } from "../../utils/playerPowerTypes";

const noopFlags = vi.fn();
const noopPreview = vi.fn();
const noopScan = vi.fn();

const draftVersion: RegistryEnemyVersion = {
  id: "player_slime_blue_00",
  path: "player_exports/player_slime_blue_00.glb",
  draft: true,
  in_use: false,
};
const inUseVersion: RegistryEnemyVersion = {
  id: "player_slime_green_00",
  path: "player_exports/player_slime_green_00.glb",
  draft: false,
  in_use: true,
};

function renderSection(
  versions: RegistryEnemyVersion[] = [],
  busyKey: string | null = null,
  scanBusy = false,
) {
  return render(
    <RegistryPlayerPowerTypesSection
      playerVersions={versions}
      scanBusy={scanBusy}
      busyKey={busyKey}
      onScanPlayerExports={noopScan}
      onApplyFlags={noopFlags}
      onPreviewVersion={noopPreview}
    />,
  );
}

describe("RegistryPlayerPowerTypesSection", () => {
  afterEach(() => {
    cleanup();
    localStorage.clear();
    vi.clearAllMocks();
  });

  beforeEach(() => {
    localStorage.clear();
  });

  // ── Heading ──────────────────────────────────────────────────────────────
  it("renders the section heading", () => {
    renderSection();
    expect(screen.getByRole("heading", { name: PLAYER_POWER_TYPES_HEADING })).toBeInTheDocument();
  });

  // ── Default section ──────────────────────────────────────────────────────
  it("shows one Default section on first render", () => {
    renderSection();
    expect(screen.getByTestId("player-pt-name-btn-default")).toHaveTextContent("Default");
  });

  // ── Versions table ───────────────────────────────────────────────────────
  it("shows all versions in the table with draft radio selected", () => {
    renderSection([draftVersion]);
    expect(screen.getByText("player_slime_blue_00")).toBeInTheDocument();
    const draftRadio = screen.getByTestId("player-version-spawn-player_slime_blue_00-draft");
    expect((draftRadio as HTMLInputElement).checked).toBe(true);
  });

  it("shows in-use version with pool radio selected", () => {
    renderSection([inUseVersion]);
    const poolRadio = screen.getByTestId("player-version-spawn-player_slime_green_00-pool");
    expect((poolRadio as HTMLInputElement).checked).toBe(true);
  });

  it("shows empty-state message when no versions are registered", () => {
    renderSection([]);
    expect(screen.getByText(/no player versions registered/i)).toBeInTheDocument();
  });

  it("bulk Set selected → Draft calls onApplyFlags for each checked version", async () => {
    noopFlags.mockImplementation(() => Promise.resolve());
    renderSection([draftVersion, inUseVersion]);
    fireEvent.click(screen.getByTestId(`player-version-select-${draftVersion.id}`));
    fireEvent.click(screen.getByTestId(`player-version-select-${inUseVersion.id}`));
    fireEvent.click(screen.getByTestId("player-version-bulk-draft"));
    await waitFor(() => {
      expect(noopFlags).toHaveBeenCalledTimes(2);
    });
    expect(noopFlags).toHaveBeenCalledWith(draftVersion, true, false);
    expect(noopFlags).toHaveBeenCalledWith(inUseVersion, true, false);
  });

  // ── Apply flags callback ─────────────────────────────────────────────────
  it("calls onApplyFlags(v, false, true) when In pool radio is clicked", () => {
    renderSection([draftVersion]);
    fireEvent.click(screen.getByTestId("player-version-spawn-player_slime_blue_00-pool"));
    expect(noopFlags).toHaveBeenCalledWith(draftVersion, false, true);
  });

  it("calls onApplyFlags(v, true, false) when Draft radio is clicked", () => {
    renderSection([inUseVersion]);
    fireEvent.click(screen.getByTestId("player-version-spawn-player_slime_green_00-draft"));
    expect(noopFlags).toHaveBeenCalledWith(inUseVersion, true, false);
  });

  it("radio inputs are disabled while busyKey matches the version", () => {
    renderSection([draftVersion], "player:player_slime_blue_00");
    expect(screen.getByTestId("player-version-spawn-player_slime_blue_00-draft")).toBeDisabled();
    expect(screen.getByTestId("player-version-spawn-player_slime_blue_00-pool")).toBeDisabled();
  });

  // ── Preview callback ─────────────────────────────────────────────────────
  it("calls onPreviewVersion when Preview button is clicked", () => {
    renderSection([draftVersion]);
    fireEvent.click(screen.getAllByRole("button", { name: /preview/i })[0]);
    expect(noopPreview).toHaveBeenCalledWith(draftVersion);
  });

  // ── Scan exports button ──────────────────────────────────────────────────
  it("shows Scan player exports button and calls onScanPlayerExports", () => {
    renderSection();
    const btn = screen.getByTestId("player-scan-exports");
    expect(btn).toHaveTextContent("Scan player exports");
    fireEvent.click(btn);
    expect(noopScan).toHaveBeenCalled();
  });

  it("scan button shows Scanning… and is disabled while scanBusy", () => {
    renderSection([], null, true);
    const btn = screen.getByTestId("player-scan-exports");
    expect(btn).toHaveTextContent("Scanning…");
    expect(btn).toBeDisabled();
  });

  // ── Add power type ───────────────────────────────────────────────────────
  it("adds a new power type section when Add power type is clicked", async () => {
    renderSection();
    fireEvent.click(screen.getByTestId("player-add-power-type"));
    // New section auto-opens inline rename mode; default section still shows its button
    await waitFor(() => {
      expect(screen.getByTestId("player-pt-name-btn-default")).toBeInTheDocument();
      const inputs = screen.getAllByRole("textbox");
      expect(inputs).toHaveLength(1);
    });
  });

  it("immediately opens inline rename input after adding a section", async () => {
    renderSection();
    fireEvent.click(screen.getByTestId("player-add-power-type"));
    // The newly added section starts in edit mode
    await waitFor(() => {
      const inputs = screen.getAllByRole("textbox");
      expect(inputs.length).toBeGreaterThan(0);
    });
  });

  // ── Rename section ───────────────────────────────────────────────────────
  it("clicking name button switches it to an editable input", () => {
    renderSection();
    fireEvent.click(screen.getByTestId("player-pt-name-btn-default"));
    expect(screen.getByTestId("player-pt-name-input-default")).toBeInTheDocument();
  });

  it("saves renamed label when Save is clicked", async () => {
    renderSection();
    fireEvent.click(screen.getByTestId("player-pt-name-btn-default"));
    fireEvent.change(screen.getByTestId("player-pt-name-input-default"), {
      target: { value: "Fire Type" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => {
      expect(screen.getByTestId("player-pt-name-btn-default")).toHaveTextContent("Fire Type");
    });
  });

  it("saves renamed label on Enter key", async () => {
    renderSection();
    fireEvent.click(screen.getByTestId("player-pt-name-btn-default"));
    const input = screen.getByTestId("player-pt-name-input-default");
    fireEvent.change(input, { target: { value: "Water Type" } });
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() => {
      expect(screen.getByTestId("player-pt-name-btn-default")).toHaveTextContent("Water Type");
    });
  });

  it("cancels rename on Escape key", async () => {
    renderSection();
    fireEvent.click(screen.getByTestId("player-pt-name-btn-default"));
    const input = screen.getByTestId("player-pt-name-input-default");
    fireEvent.change(input, { target: { value: "XYZ" } });
    fireEvent.keyDown(input, { key: "Escape" });
    await waitFor(() => {
      expect(screen.getByTestId("player-pt-name-btn-default")).toHaveTextContent("Default");
    });
  });

  // ── Remove section ───────────────────────────────────────────────────────
  it("does not show Remove section button when only one section exists", () => {
    renderSection();
    expect(screen.queryByTestId("player-pt-remove-default")).not.toBeInTheDocument();
  });

  it("shows Remove section button when two sections exist", () => {
    renderSection();
    fireEvent.click(screen.getByTestId("player-add-power-type"));
    expect(screen.getAllByText("Remove section")).toHaveLength(2);
  });

  it("removing a section brings count back to one", async () => {
    renderSection();
    fireEvent.click(screen.getByTestId("player-add-power-type"));

    // New section auto-opens edit mode; cancel it first so both name buttons are visible
    await waitFor(() => {
      const inputs = screen.queryAllByRole("textbox");
      expect(inputs.length).toBeGreaterThan(0);
      fireEvent.keyDown(inputs[0], { key: "Escape" });
    });

    await waitFor(() => {
      expect(screen.getAllByTitle("Click to rename")).toHaveLength(2);
    });

    await waitFor(() => {
      const removeBtns = screen.getAllByText("Remove section");
      fireEvent.click(removeBtns[removeBtns.length - 1]);
    });

    await waitFor(() => {
      expect(screen.getAllByTitle("Click to rename")).toHaveLength(1);
    });
  });

  // ── Slots ────────────────────────────────────────────────────────────────
  it("Add slot button adds an Unassigned dropdown row", () => {
    renderSection([inUseVersion]);
    fireEvent.click(screen.getByTestId("player-pt-add-slot-default"));
    expect(screen.getByTestId("player-pt-slot-select-default-0")).toBeInTheDocument();
  });

  it("slot dropdown lists only non-draft in-use versions", () => {
    renderSection([draftVersion, inUseVersion]);
    fireEvent.click(screen.getByTestId("player-pt-add-slot-default"));
    const select = screen.getByTestId("player-pt-slot-select-default-0") as HTMLSelectElement;
    const options = Array.from(select.options).map((o) => o.value);
    expect(options).toContain("player_slime_green_00");
    expect(options).not.toContain("player_slime_blue_00");
  });

  it("Add slot is disabled when no in-use versions exist", () => {
    renderSection([draftVersion]);
    expect(screen.getByTestId("player-pt-add-slot-default")).toBeDisabled();
  });

  it("Save slots button persists slots to localStorage", () => {
    renderSection([inUseVersion]);
    fireEvent.click(screen.getByTestId("player-pt-add-slot-default"));
    const select = screen.getByTestId("player-pt-slot-select-default-0") as HTMLSelectElement;
    fireEvent.change(select, { target: { value: "player_slime_green_00" } });
    fireEvent.click(screen.getByTestId("player-pt-save-slots-default"));
    const stored = JSON.parse(localStorage.getItem("blobert.player.pt_slots.default") ?? "[]") as string[];
    expect(stored).toContain("player_slime_green_00");
  });

  // ── Persistence across mount ─────────────────────────────────────────────
  it("restores saved power types from localStorage on mount", () => {
    savePlayerPowerTypes([
      { id: "fire", label: "Fire" },
      { id: "ice", label: "Ice" },
    ]);
    renderSection();
    expect(screen.getByTestId("player-pt-name-btn-fire")).toHaveTextContent("Fire");
    expect(screen.getByTestId("player-pt-name-btn-ice")).toHaveTextContent("Ice");
  });
});
