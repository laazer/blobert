// @vitest-environment jsdom
/**
 * STUDIO-01 — studio_editor_redesign_spec.md §8 (T-1..T-6).
 * Red contracts until StudioLayout, elements.ts, and App flag wiring land.
 */
import { describe, it, expect, afterEach, beforeEach, vi } from "vitest";
import { cleanup, render, screen, fireEvent, within } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { StudioLayout } from "./StudioLayout";
import { StudioPreviewColumn } from "../studio/StudioPreviewColumn";
import { ELEMENTS, type ElementId } from "../../constants/elements";

vi.mock("../Editor/EditorPane", () => ({ EditorPane: () => <div data-testid="editor" /> }));
vi.mock("../FileTree/FileTree", () => ({ FileTree: () => <div /> }));
vi.mock("../Editor/ModelRegistryPane", () => ({ ModelRegistryPane: () => <div /> }));
vi.mock("../Preview/PreviewSourceBar", () => ({
  PreviewSourceBar: () => <div data-testid="preview-source-bar" />,
}));
vi.mock("../Preview/GlbViewer", () => ({ GlbViewer: () => <div data-testid="glb-viewer" /> }));
vi.mock("../Preview/AnimationControls", () => ({
  AnimationControls: () => <div data-testid="animation-controls" />,
}));
vi.mock("../CommandPanel/CommandPanel", () => ({
  CommandPanel: () => <div data-testid="command-panel" />,
}));
vi.mock("../Terminal/Terminal", () => ({
  Terminal: () => <div data-testid="preview-terminal" />,
}));

const NINE_ELEMENT_IDS: ElementId[] = [
  "fire",
  "ice",
  "poison",
  "acid",
  "earth",
  "forest",
  "water",
  "lightning",
  "physical",
];

const INSPECTOR_TABS = ["look", "build", "animate", "code", "versions"] as const;

afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
  vi.restoreAllMocks();
  vi.resetModules();
});

function seedStudioStore() {
  useAppStore.setState({
    centerPanel: "none",
    commandContext: { cmd: "animated", enemy: "spider" },
    animatedEnemyMeta: [{ slug: "spider", label: "Spider" }],
    terminalLines: [],
    loadAnimatedEnemyMeta: vi.fn().mockResolvedValue(undefined),
  });
}

async function renderAppWithStudioFlag(value: string | undefined) {
  if (value === undefined) {
    vi.unstubAllEnvs();
  } else {
    vi.stubEnv("VITE_STUDIO_LAYOUT", value);
  }
  vi.resetModules();
  const appModule = await import("../../App");
  seedStudioStore();
  return render(<appModule.default />);
}

describe("STUDIO-01 StudioLayout (spec §8)", () => {
  beforeEach(() => {
    seedStudioStore();
  });

  describe("T-1 feature flag off → legacy layout", () => {
    it("renders legacy-layout and not studio-layout when VITE_STUDIO_LAYOUT is unset", async () => {
      await renderAppWithStudioFlag(undefined);
      expect(screen.getByTestId("legacy-layout")).toBeInTheDocument();
      expect(screen.queryByTestId("studio-layout")).toBeNull();
    });

    it("renders legacy-layout when VITE_STUDIO_LAYOUT is not exactly 1", async () => {
      await renderAppWithStudioFlag("true");
      expect(screen.getByTestId("legacy-layout")).toBeInTheDocument();
      expect(screen.queryByTestId("studio-layout")).toBeNull();
    });
  });

  describe("T-2 feature flag on → studio preview stack", () => {
    beforeEach(() => {
      vi.stubEnv("VITE_STUDIO_LAYOUT", "1");
    });

    it("renders studio-layout, studio-preview-column, and preview stack children via App", async () => {
      await renderAppWithStudioFlag("1");
      expect(screen.getByTestId("studio-layout")).toBeInTheDocument();
      const previewColumn = screen.getByTestId("studio-preview-column");
      expect(previewColumn).toBeInTheDocument();
      expect(within(previewColumn).getByTestId("preview-source-bar")).toBeInTheDocument();
      expect(within(previewColumn).getByTestId("glb-viewer")).toBeInTheDocument();
      expect(within(previewColumn).getByTestId("animation-controls")).toBeInTheDocument();
      expect(screen.queryByTestId("legacy-layout")).toBeNull();
    });

    it("StudioLayout root uses 256px 1fr 360px grid columns", () => {
      render(<StudioLayout />);
      const root = screen.getByTestId("studio-layout");
      expect(root).toHaveStyle({ gridTemplateColumns: "256px 1fr 360px" });
    });
  });

  describe("T-3 inspector tab switch", () => {
    it("updates active tab aria-selected and panel test id without throwing", () => {
      render(<StudioLayout />);
      const lookTab = screen.getByTestId("studio-inspector-tab-look");
      expect(lookTab).toHaveAttribute("aria-selected", "true");
      expect(screen.getByTestId("studio-inspector-panel-look")).toBeVisible();

      const buildTab = screen.getByTestId("studio-inspector-tab-build");
      fireEvent.click(buildTab);

      expect(buildTab).toHaveAttribute("aria-selected", "true");
      expect(lookTab).toHaveAttribute("aria-selected", "false");
      expect(screen.getByTestId("studio-inspector-panel-build")).toBeVisible();
      expect(screen.queryByTestId("studio-inspector-panel-look")).toBeNull();
    });

    it("exposes all five inspector tab triggers", () => {
      render(<StudioLayout />);
      for (const tab of INSPECTOR_TABS) {
        expect(screen.getByTestId(`studio-inspector-tab-${tab}`)).toBeInTheDocument();
      }
    });
  });

  describe("T-4 elements.ts nine element tokens", () => {
    it("exports hue, soft, and ink strings for every element id", () => {
      expect(Object.keys(ELEMENTS).sort()).toEqual([...NINE_ELEMENT_IDS].sort());
      for (const id of NINE_ELEMENT_IDS) {
        const entry = ELEMENTS[id];
        expect(typeof entry.hue).toBe("string");
        expect(entry.hue.length).toBeGreaterThan(0);
        expect(typeof entry.soft).toBe("string");
        expect(entry.soft.length).toBeGreaterThan(0);
        expect(typeof entry.ink).toBe("string");
        expect(entry.ink.length).toBeGreaterThan(0);
      }
    });
  });

  describe("T-5 preview hydration guard on Studio mount", () => {
    it("does not call selectAssetByPath with importBuildOptions true when StudioLayout mounts", () => {
      const selectSpy = vi.spyOn(useAppStore.getState(), "selectAssetByPath");
      render(<StudioLayout />);
      for (const [, options] of selectSpy.mock.calls) {
        expect(options?.importBuildOptions).not.toBe(true);
      }
      selectSpy.mockClear();
    });

    it("does not call selectAssetByPath with importBuildOptions true when StudioPreviewColumn mounts", () => {
      const selectSpy = vi.spyOn(useAppStore.getState(), "selectAssetByPath");
      render(<StudioPreviewColumn />);
      for (const [, options] of selectSpy.mock.calls) {
        expect(options?.importBuildOptions).not.toBe(true);
      }
    });
  });

  describe("T-6 Phase 1 center omission (CommandPanel / Terminal)", () => {
    beforeEach(() => {
      vi.stubEnv("VITE_STUDIO_LAYOUT", "1");
    });

    it("keeps command-panel and preview-terminal outside the studio-layout subtree", async () => {
      await renderAppWithStudioFlag("1");
      const studio = screen.getByTestId("studio-layout");
      expect(within(studio).queryByTestId("command-panel")).toBeNull();
      expect(within(studio).queryByTestId("preview-terminal")).toBeNull();
      expect(within(studio).queryByRole("region", { name: "Run output log" })).toBeNull();
    });

    it("StudioPreviewColumn does not mount command-panel or preview-terminal", () => {
      render(<StudioPreviewColumn />);
      const column = screen.getByTestId("studio-preview-column");
      expect(within(column).queryByTestId("command-panel")).toBeNull();
      expect(within(column).queryByTestId("preview-terminal")).toBeNull();
    });
  });
});
