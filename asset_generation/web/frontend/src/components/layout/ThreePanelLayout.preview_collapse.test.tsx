// @vitest-environment jsdom
import { describe, it, expect, afterEach, beforeEach, vi } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { ThreePanelLayout } from "./ThreePanelLayout";

vi.mock("../Editor/EditorPane", () => ({ EditorPane: () => <div data-testid="editor" /> }));
vi.mock("../FileTree/FileTree", () => ({ FileTree: () => <div /> }));
vi.mock("../Editor/ModelRegistryPane", () => ({ ModelRegistryPane: () => <div /> }));
vi.mock("../Preview/PreviewSourceBar", () => ({ PreviewSourceBar: () => <div /> }));
vi.mock("../Preview/GlbViewer", () => ({ GlbViewer: () => <div /> }));
vi.mock("../Preview/BuildControls", () => ({ BuildControls: () => <div /> }));
vi.mock("../Preview/ColorsPane", () => ({ ColorsPane: () => <div /> }));
vi.mock("../Preview/ExtrasPane", () => ({ ExtrasPane: () => <div /> }));
vi.mock("../CommandPanel/CommandPanel", () => ({ CommandPanel: () => <div data-testid="command-panel" /> }));

afterEach(() => {
  cleanup();
  localStorage.clear();
});

describe("ThreePanelLayout preview collapse", () => {
  beforeEach(() => {
    useAppStore.setState({
      centerPanel: "none",
      commandContext: { cmd: "animated", enemy: "slug" },
      animatedEnemyMeta: [{ slug: "slug", label: "Slug" }],
      terminalLines: [],
    });
  });

  it("hides and shows animation controls with stable toggle name and aria-expanded", () => {
    render(<ThreePanelLayout />);

    const hideAnim = screen.getByRole("button", { name: "Hide animations" });
    expect(hideAnim).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("region", { name: "Animation clips and playback" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Pause" })).toBeTruthy();

    fireEvent.click(hideAnim);
    expect(screen.queryByRole("region", { name: "Animation clips and playback" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Pause" })).toBeNull();

    const showAnim = screen.getByRole("button", { name: "Show animations" });
    expect(showAnim).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(showAnim);
    expect(screen.getByRole("button", { name: "Pause" })).toBeTruthy();
  });

  it("hides and shows terminal log region without removing command panel", () => {
    render(<ThreePanelLayout />);

    expect(screen.getByTestId("command-panel")).toBeTruthy();
    const hideLog = screen.getByRole("button", { name: "Hide log" });
    expect(hideLog).toHaveAttribute("aria-expanded", "true");

    fireEvent.click(hideLog);
    expect(screen.queryByRole("region", { name: "Run output log" })).toBeNull();
    expect(screen.getByTestId("command-panel")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Show log" }));
    expect(screen.getByRole("region", { name: "Run output log" })).toBeTruthy();
  });

  it("restores terminal collapsed state from localStorage", () => {
    localStorage.setItem("blobert.editor.preview.terminalExpanded", "0");
    render(<ThreePanelLayout />);
    expect(screen.queryByRole("region", { name: "Run output log" })).toBeNull();
    expect(screen.getByRole("button", { name: "Show log" })).toHaveAttribute("aria-expanded", "false");
  });
});
