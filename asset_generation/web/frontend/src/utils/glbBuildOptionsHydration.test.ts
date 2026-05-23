// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import { replaceAnimatedSlugBuildOptionsRow } from "../api/client";
import type { AnimatedBuildControlDef } from "../types";
import {
  buildOptionSlugFromPreviewGlbRelativePath,
  commandExportPatchFromBuildSnapshot,
  expandBuildOptionsSnapshotForEditor,
  playerColorFromPlayerSlimeExportRelativePath,
} from "./glbBuildOptionsHydration";

describe("buildOptionSlugFromPreviewGlbRelativePath", () => {
  it("maps animated_exports GLB to enemy slug", () => {
    expect(buildOptionSlugFromPreviewGlbRelativePath("animated_exports/spider_animated_03.glb")).toBe("spider");
    expect(buildOptionSlugFromPreviewGlbRelativePath("animated_exports/draft/slug_animated_01.glb")).toBe("slug");
  });

  it("maps player slime GLB to player_slime build slug", () => {
    expect(buildOptionSlugFromPreviewGlbRelativePath("player_exports/player_slime_blue_00.glb")).toBe("player_slime");
  });

  it("returns null for unrelated paths", () => {
    expect(buildOptionSlugFromPreviewGlbRelativePath("level_exports/foo_00.glb")).toBeNull();
  });
});

describe("playerColorFromPlayerSlimeExportRelativePath", () => {
  it("parses color segment before variant index", () => {
    expect(playerColorFromPlayerSlimeExportRelativePath("player_exports/player_slime_blue_00.glb")).toBe("blue");
    expect(playerColorFromPlayerSlimeExportRelativePath("player_exports/draft/player_slime_orange_01.glb")).toBe(
      "orange",
    );
  });

  it("returns null for non-player GLBs", () => {
    expect(playerColorFromPlayerSlimeExportRelativePath("animated_exports/spider_animated_00.glb")).toBeNull();
  });
});

describe("expandBuildOptionsSnapshotForEditor", () => {
  it("flattens nested features zone colors into feat_* keys", () => {
    const flat = expandBuildOptionsSnapshotForEditor("spider", {
      eye_count: 3,
      features: {
        body: { finish: "glossy", hex: "b83228", color_image: { mode: "single", id: null } },
        head: { finish: "matte", hex: "#e85d2a" },
      },
    });
    expect(flat.eye_count).toBe(3);
    expect(flat.features).toBeUndefined();
    expect(flat.feat_body_finish).toBe("glossy");
    expect(flat.feat_body_hex).toBe("b83228");
    expect(flat.feat_body_color_hex).toBe("b83228");
    expect(flat.feat_body_color_mode).toBe("single");
    expect(flat.feat_head_finish).toBe("matte");
    expect(flat.feat_head_hex).toBe("e85d2a");
  });

  it("merges mesh floats to top level", () => {
    const flat = expandBuildOptionsSnapshotForEditor("spider", {
      mesh: { eye_count: 5 },
      features: {},
    });
    expect(flat.eye_count).toBe(5);
  });

  it("flattens nested zone_geometry_extras into extra_zone_* keys", () => {
    const flat = expandBuildOptionsSnapshotForEditor("spider", {
      zone_geometry_extras: {
        body: { kind: "spikes", spike_count: 12, finish: "metallic", hex: "aabbcc" },
        head: { kind: "none" },
      },
    });
    expect(flat.zone_geometry_extras).toBeUndefined();
    expect(flat.extra_zone_body_kind).toBe("spikes");
    expect(flat.extra_zone_body_spike_count).toBe(12);
    expect(flat.extra_zone_body_finish).toBe("metallic");
    expect(flat.extra_zone_body_hex).toBe("aabbcc");
    expect(flat.extra_zone_head_kind).toBe("none");
  });
});

describe("commandExportPatchFromBuildSnapshot", () => {
  it("reads body finish and hex keys", () => {
    expect(
      commandExportPatchFromBuildSnapshot({
        feat_body_finish: "metallic",
        feat_body_hex: "aabbcc",
      }),
    ).toEqual({ finish: "metallic", hexColor: "#aabbcc" });
  });

  it("accepts picker hex key", () => {
    expect(
      commandExportPatchFromBuildSnapshot({
        feat_body_finish: "glossy",
        feat_body_color_hex: "#010203",
      }),
    ).toEqual({ finish: "glossy", hexColor: "#010203" });
  });

  it("reads nested features.body when flat keys are absent", () => {
    expect(
      commandExportPatchFromBuildSnapshot({
        features: { body: { finish: "metallic", hex: "aabbcc" } },
      }),
    ).toEqual({ finish: "metallic", hexColor: "#aabbcc" });
  });
});

describe("replaceAnimatedSlugBuildOptionsRow", () => {
  it("overlays snapshot on defaults for known def keys", () => {
    const defs: AnimatedBuildControlDef[] = [
      { key: "eye_count", label: "", type: "int", min: 1, max: 8, default: 2 },
      { key: "feat_body_finish", label: "", type: "select_str", options: ["matte"], default: "default" },
    ];
    const controls = { spider: defs };
    const full = replaceAnimatedSlugBuildOptionsRow(controls, { spider: { eye_count: 9 } }, "spider", {
      eye_count: 4,
      feat_body_finish: "matte",
    });
    expect(full.spider?.eye_count).toBe(4);
    expect(full.spider?.feat_body_finish).toBe("matte");
  });

  it("flattens nested features when overlaying snapshot", () => {
    const defs: AnimatedBuildControlDef[] = [
      { key: "feat_body_finish", label: "", type: "select_str", options: ["matte", "glossy"], default: "matte" },
      { key: "feat_body_hex", label: "", type: "text", default: "" },
      { key: "feat_head_hex", label: "", type: "text", default: "" },
    ];
    const controls = { spider: defs };
    const full = replaceAnimatedSlugBuildOptionsRow(controls, { spider: {} }, "spider", {
      features: {
        body: { finish: "glossy", hex: "b83228" },
        head: { hex: "e85d2a" },
      },
    });
    expect(full.spider?.feat_body_finish).toBe("glossy");
    expect(full.spider?.feat_body_hex).toBe("b83228");
    expect(full.spider?.feat_head_hex).toBe("e85d2a");
  });

  it("flattens nested zone_geometry_extras when overlaying snapshot", () => {
    const defs: AnimatedBuildControlDef[] = [
      { key: "extra_zone_body_kind", label: "", type: "select_str", options: ["none", "spikes"], default: "none" },
      { key: "extra_zone_body_hex", label: "", type: "str", default: "" },
    ];
    const controls = { spider: defs };
    const full = replaceAnimatedSlugBuildOptionsRow(controls, { spider: {} }, "spider", {
      zone_geometry_extras: { body: { kind: "spikes", hex: "ff00aa" } },
    });
    expect(full.spider?.extra_zone_body_kind).toBe("spikes");
    expect(full.spider?.extra_zone_body_hex).toBe("ff00aa");
  });
});
