// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import { replaceAnimatedSlugBuildOptionsRow } from "../api/client";
import type { AnimatedBuildControlDef } from "../types";
import {
  buildOptionSlugFromPreviewGlbRelativePath,
  commandExportPatchFromBuildSnapshot,
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
});
