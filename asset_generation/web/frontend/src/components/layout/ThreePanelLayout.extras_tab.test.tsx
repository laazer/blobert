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
vi.mock("../Preview/AnimationControls", () => ({ AnimationControls: () => <div /> }));
vi.mock("../CommandPanel/CommandPanel", () => ({ CommandPanel: () => <div /> }));
vi.mock("../Terminal/Terminal", () => ({ Terminal: () => <div /> }));

afterEach(() => {
  cleanup();
});

describe("ThreePanelLayout Extras tab", () => {
  beforeEach(() => {
    useAppStore.setState({
      centerPanel: "code",
      commandContext: { cmd: "animated", enemy: "slug" },
      animatedEnemyMeta: [{ slug: "slug", label: "Slug" }],
    });
  });

  it("switches center panel to extras when Extras is clicked", () => {
    render(<ThreePanelLayout />);
    fireEvent.click(screen.getByRole("button", { name: "Extras" }));
    expect(useAppStore.getState().centerPanel).toBe("extras");
  });
});
