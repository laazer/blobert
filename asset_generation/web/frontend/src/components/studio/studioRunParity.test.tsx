// @vitest-environment jsdom
/**
 * Studio regenerate/run must send the same SSE payload as CommandPanel for the same store state.
 */
import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { mergeBuildOptionValues } from "../../api/client";
import { useAppStore } from "../../store/useAppStore";
import { mergeCanonicalZoneControlsForAllSlugs } from "../../utils/animatedZoneControlsMerge";
import type { AnimatedBuildControlDef } from "../../types";
import { buildAssetRunOptions } from "../../utils/assetRunOptions";
import { DEFAULT_ELEMENT_PALETTES } from "../../utils/elementColorPalettes";
import { CommandPanel } from "../CommandPanel/CommandPanel";
import { StudioTopBar } from "./StudioTopBar";
import { StudioCodePanel } from "./StudioCodePanel";
import { StudioLookPanel } from "./StudioLookPanel";

const startSpy = vi.fn();

vi.mock("../Terminal/useStreamingOutput", () => ({
  useStreamingOutput: () => ({ start: startSpy }),
}));

vi.mock("../CommandPanel/SaveScriptModal", () => ({
  SaveScriptModal: () => null,
}));

vi.mock("../CommandPanel/SaveModelModal", () => ({
  SaveModelModal: () => null,
}));

vi.mock("@monaco-editor/react", () => ({
  default: () => null,
}));

const EYE_COUNT: AnimatedBuildControlDef = {
  key: "eye_count",
  label: "Count",
  type: "select",
  options: [1, 2, 3, 4, 5],
  default: 2,
};

function seedStore() {
  const controls = mergeCanonicalZoneControlsForAllSlugs({ spider: [EYE_COUNT] }, ["spider"]);
  const values = mergeBuildOptionValues(controls, {
    spider: { eye_count: 5, feat_body_finish: "matte", feat_body_hex: "aabbcc" },
  });
  useAppStore.setState({
    isSaving: false,
    isRunning: false,
    isDirty: false,
    selectedFile: null,
    fileTree: [],
    commandContext: { cmd: "animated", enemy: "spider" },
    commandExportFinish: "glossy",
    commandExportHexColor: "#ff5500",
    activeGlbUrl: "/api/assets/animated_exports/spider_animated_02.glb?t=1",
    animatedEnemyMeta: [{ slug: "spider", label: "Spider" }],
    animatedBuildControls: controls,
    animatedBuildOptionValues: values,
    enemyMetaStatus: "ok",
    terminalLines: [],
  });
}

function lastStartPayload() {
  return startSpy.mock.calls[startSpy.mock.calls.length - 1][0] as Record<string, unknown>;
}

afterEach(() => {
  cleanup();
  startSpy.mockClear();
});

describe("Studio vs CommandPanel run parity", () => {
  beforeEach(seedStore);

  it("CommandPanel Regenerate baseline", () => {
    render(<CommandPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Regenerate" }));
    expect(startSpy).toHaveBeenCalledTimes(1);
    expect(lastStartPayload()).toMatchObject({
      replaceVariantIndex: 2,
      outputDraft: false,
      cmd: "animated",
      enemy: "spider",
      finish: "glossy",
      hexColor: "#ff5500",
    });
    expect(lastStartPayload().buildOptionsJson).toBeDefined();
  });

  it("StudioTopBar Regenerate matches CommandPanel payload", () => {
    render(<CommandPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Regenerate" }));
    const commandPayload = { ...lastStartPayload() };

    startSpy.mockClear();
    cleanup();

    render(<StudioTopBar />);
    fireEvent.click(screen.getByTestId("studio-top-regenerate"));
    expect(startSpy).toHaveBeenCalledTimes(1);
    expect(lastStartPayload()).toEqual(commandPayload);
  });

  it("StudioCodePanel Regenerate matches CommandPanel payload", () => {
    render(<CommandPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Regenerate" }));
    const commandPayload = { ...lastStartPayload() };

    startSpy.mockClear();
    cleanup();

    render(<StudioCodePanel />);
    fireEvent.click(screen.getByTestId("studio-code-regenerate"));
    expect(startSpy).toHaveBeenCalledTimes(1);
    expect(lastStartPayload()).toEqual(commandPayload);
  });

  it("StudioTopBar Run matches CommandPanel Run (no replaceVariantIndex)", () => {
    render(<CommandPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Run" }));
    const commandPayload = { ...lastStartPayload() };

    startSpy.mockClear();
    cleanup();

    render(<StudioCodePanel />);
    fireEvent.click(screen.getByRole("button", { name: "Run" }));
    expect(startSpy).toHaveBeenCalledTimes(1);
    expect(lastStartPayload()).toEqual(commandPayload);
    expect(lastStartPayload().replaceVariantIndex).toBeUndefined();
  });

  it("Regenerate build_options includes lightning hex after element apply (spots + image)", () => {
    const prior = useAppStore.getState().animatedBuildOptionValues.spider ?? {};
    useAppStore.setState({
      animatedBuildOptionValues: {
        spider: {
          ...prior,
          feat_body_texture_mode: "spots",
          feat_body_hex: "#6b3d8f",
          feat_body_color_mode: "image",
          feat_body_color_image_id: "hash_texture",
        },
      },
    });

    render(<StudioLookPanel slug="spider" />);
    fireEvent.click(screen.getByTestId("studio-look-element-lightning"));
    cleanup();

    const st = useAppStore.getState();
    const fields = {
      cmd: st.commandContext.cmd,
      enemy: st.commandContext.enemy,
      description: "",
      difficulty: "normal",
      finish: st.commandExportFinish,
      hexColor: st.commandExportHexColor,
      commandPreviewDirty: false,
    };
    const opts = buildAssetRunOptions(
      fields,
      st.activeGlbUrl,
      st.animatedBuildControls,
      st.animatedBuildOptionValues,
      true,
    );
    expect(opts.hexColor).toBe(DEFAULT_ELEMENT_PALETTES.lightning.body!.hex);
    expect(opts.buildOptionsJson).toContain("e8e0a0");
    const parsed = JSON.parse(opts.buildOptionsJson!) as Record<string, Record<string, unknown>>;
    expect(parsed.spider?.feat_body_hex).toBe("#e8e0a0");
  });

  it("Regenerate disabled when preview path mismatches (studio + command)", () => {
    useAppStore.setState({
      activeGlbUrl: "/api/assets/animated_exports/slug_animated_00.glb",
    });

    render(<CommandPanel />);
    expect(screen.getByRole("button", { name: "Regenerate" })).toBeDisabled();
    cleanup();

    render(<StudioTopBar />);
    expect(screen.getByTestId("studio-top-regenerate")).toBeDisabled();
    cleanup();

    render(<StudioCodePanel />);
    expect(screen.getByTestId("studio-code-regenerate")).toBeDisabled();
  });
});
