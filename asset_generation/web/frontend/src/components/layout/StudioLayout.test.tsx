// @vitest-environment jsdom
/**
 * STUDIO-01 — studio_editor_redesign_spec.md §8 (T-1..T-6), §11 invalid-flag taxonomy.
 * Red contracts until StudioLayout, elements.ts, and App flag wiring land.
 * Adversarial cases extended by Test Breaker (invalid flags, hydration on interaction).
 */
import { describe, it, expect, afterEach, beforeEach, vi } from "vitest";
import { cleanup, render, screen, fireEvent, within } from "@testing-library/react";
import * as client from "../../api/client";
import { useAppStore } from "../../store/useAppStore";
import { StudioLayout } from "./StudioLayout";
import { StudioPreviewColumn } from "../studio/StudioPreviewColumn";
import { ELEMENTS, type ElementId } from "../../constants/elements";

vi.mock("../../api/client", async (importOriginal) => {
  const mod = await importOriginal<typeof import("../../api/client")>();
  return {
    ...mod,
    fetchBuildOptionsSidecarForGlbPath: vi.fn(),
  };
});

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

const INSPECTOR_TABS = ["look", "build", "code", "versions"] as const;

/** §11: only exact `"1"` enables studio; all other values → legacy. */
const INVALID_STUDIO_FLAGS = [
  "",
  " ",
  " 1",
  "1 ",
  "01",
  "10",
  "0",
  "false",
  "TRUE",
  "yes",
  "\t",
  "\n1",
  "1\n",
] as const;

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
      expect(within(previewColumn).queryByTestId("preview-source-bar")).toBeNull();
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
      expect(screen.queryByText(/BuildControls \(Phase 2\)/)).toBeNull();
    });

    it("exposes all four visible inspector tab triggers", () => {
      render(<StudioLayout />);
      for (const tab of INSPECTOR_TABS) {
        expect(screen.getByTestId(`studio-inspector-tab-${tab}`)).toBeInTheDocument();
      }
      expect(screen.queryByTestId("studio-inspector-tab-animate")).toBeNull();
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

  describe("§11 adversarial — invalid VITE_STUDIO_LAYOUT → legacy", () => {
    it.each(INVALID_STUDIO_FLAGS)(
      "renders legacy-layout and not studio-layout when flag is %j",
      async (flag) => {
        await renderAppWithStudioFlag(flag);
        expect(screen.getByTestId("legacy-layout")).toBeInTheDocument();
        expect(screen.queryByTestId("studio-layout")).toBeNull();
      },
    );

    it("re-reads App flag after resetModules when toggling from on to invalid", async () => {
      await renderAppWithStudioFlag("1");
      expect(screen.getByTestId("studio-layout")).toBeInTheDocument();
      cleanup();
      vi.resetModules();
      await renderAppWithStudioFlag("true");
      expect(screen.getByTestId("legacy-layout")).toBeInTheDocument();
      expect(screen.queryByTestId("studio-layout")).toBeNull();
    });
  });

  describe("T-3 adversarial — inspector tab edge cases", () => {
    it("uses lowercase slug test ids (not PascalCase)", () => {
      render(<StudioLayout />);
      expect(screen.queryByTestId("studio-inspector-tab-Look")).toBeNull();
      expect(screen.getByTestId("studio-inspector-tab-look")).toBeInTheDocument();
    });

    it("shows exactly one inspector panel while cycling all tabs", () => {
      render(<StudioLayout />);
      for (const tab of INSPECTOR_TABS) {
        fireEvent.click(screen.getByTestId(`studio-inspector-tab-${tab}`));
        const visiblePanels = INSPECTOR_TABS.filter(
          (t) => screen.queryByTestId(`studio-inspector-panel-${t}`) !== null,
        );
        expect(visiblePanels).toEqual([tab]);
      }
    });

    it("rapid double-click on a tab leaves a single active panel without throw", () => {
      render(<StudioLayout />);
      const buildTab = screen.getByTestId("studio-inspector-tab-build");
      fireEvent.click(buildTab);
      fireEvent.click(buildTab);
      expect(buildTab).toHaveAttribute("aria-selected", "true");
      expect(screen.getByTestId("studio-inspector-panel-build")).toBeVisible();
      expect(screen.queryByTestId("studio-inspector-panel-look")).toBeNull();
    });
  });

  describe("T-4 adversarial — element token shape", () => {
    // CHECKPOINT: spec §14 requires hue/soft/ink strings only; hex shape is conservative for shared.jsx parity.
    const HEX_COLOR = /^#[0-9a-f]{6}$/i;

    it("uses six-digit hex colors for hue, soft, and ink on every element", () => {
      for (const id of NINE_ELEMENT_IDS) {
        const entry = ELEMENTS[id];
        expect(entry.hue).toMatch(HEX_COLOR);
        expect(entry.soft).toMatch(HEX_COLOR);
        expect(entry.ink).toMatch(HEX_COLOR);
      }
    });

    it("does not export stray element keys beyond the nine spec ids", () => {
      const keys = Object.keys(ELEMENTS).sort();
      expect(keys).toEqual([...NINE_ELEMENT_IDS].sort());
      expect(keys).toHaveLength(9);
    });
  });

  describe("T-5 adversarial — hydration guard on interaction", () => {
    beforeEach(() => {
      vi.mocked(client.fetchBuildOptionsSidecarForGlbPath).mockReset();
      vi.mocked(client.fetchBuildOptionsSidecarForGlbPath).mockResolvedValue({
        eye_count: 99,
      });
    });

    function assertNoImportBuildOptions(selectSpy: ReturnType<typeof vi.spyOn>) {
      for (const [, options] of selectSpy.mock.calls) {
        expect(options?.importBuildOptions).not.toBe(true);
      }
    }

    it("does not call selectAssetByPath with importBuildOptions true after cycling inspector tabs", () => {
      const selectSpy = vi.spyOn(useAppStore.getState(), "selectAssetByPath");
      render(<StudioLayout />);
      for (const tab of INSPECTOR_TABS) {
        fireEvent.click(screen.getByTestId(`studio-inspector-tab-${tab}`));
      }
      fireEvent.click(screen.getByTestId("studio-inspector-tab-look"));
      assertNoImportBuildOptions(selectSpy);
    });

    it("does not fetch build options sidecar on StudioLayout mount", () => {
      render(<StudioLayout />);
      expect(client.fetchBuildOptionsSidecarForGlbPath).not.toHaveBeenCalled();
    });

    it("does not fetch build options sidecar after inspector tab interaction", () => {
      render(<StudioLayout />);
      for (const tab of INSPECTOR_TABS) {
        fireEvent.click(screen.getByTestId(`studio-inspector-tab-${tab}`));
      }
      expect(client.fetchBuildOptionsSidecarForGlbPath).not.toHaveBeenCalled();
    });

    it("does not pass importBuildOptions true when StudioPreviewColumn mounts under App flag on", async () => {
      const selectSpy = vi.spyOn(useAppStore.getState(), "selectAssetByPath");
      await renderAppWithStudioFlag("1");
      assertNoImportBuildOptions(selectSpy);
      expect(client.fetchBuildOptionsSidecarForGlbPath).not.toHaveBeenCalled();
    });
  });
});
