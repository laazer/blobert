import { describe, it, expect } from "vitest";
import { mergeCanonicalZoneControlsForAllSlugs } from "./animatedZoneControlsMerge";
import {
  buildAssetRunOptions,
  canRegenerateAsset,
  validateAssetRun,
  type AssetRunFieldState,
} from "./assetRunOptions";
import type { AnimatedBuildControlDef } from "../types";

const EYE_COUNT: AnimatedBuildControlDef = {
  key: "eye_count",
  label: "Count",
  type: "select",
  options: [1, 2, 3, 4, 5],
  default: 2,
};

const PREVIEW_GLB = "/api/assets/animated_exports/spider_animated_02.glb?t=1";

function baseFields(overrides: Partial<AssetRunFieldState> = {}): AssetRunFieldState {
  return {
    cmd: "animated",
    enemy: "spider",
    description: "",
    difficulty: "normal",
    finish: "glossy",
    hexColor: "#ff5500",
    commandPreviewDirty: false,
    ...overrides,
  };
}

describe("buildAssetRunOptions", () => {
  const controls = mergeCanonicalZoneControlsForAllSlugs({ spider: [EYE_COUNT] }, ["spider"]);
  const values = {
    spider: {
      eye_count: 5,
      feat_body_finish: "matte",
      feat_body_hex: "aabbcc",
    },
  };

  it("Run omits replaceVariantIndex", () => {
    const opts = buildAssetRunOptions(baseFields(), PREVIEW_GLB, controls, values, false);
    expect(opts.replaceVariantIndex).toBeUndefined();
    expect(opts.cmd).toBe("animated");
    expect(opts.enemy).toBe("spider");
    expect(opts.finish).toBe("glossy");
    expect(opts.hexColor).toBe("#ff5500");
    expect(opts.count).toBe(1);
  });

  it("Regenerate pins replaceVariantIndex and outputDraft false for pool exports", () => {
    const opts = buildAssetRunOptions(baseFields(), PREVIEW_GLB, controls, values, true);
    expect(opts).toMatchObject({
      replaceVariantIndex: 2,
      outputDraft: false,
      cmd: "animated",
      enemy: "spider",
    });
  });

  it("includes pruned buildOptionsJson from store values", () => {
    const opts = buildAssetRunOptions(baseFields(), PREVIEW_GLB, controls, values, true);
    expect(opts.buildOptionsJson).toBeDefined();
    const parsed = JSON.parse(opts.buildOptionsJson!) as Record<string, Record<string, unknown>>;
    expect(parsed.spider?.eye_count).toBe(5);
  });

  it("validateAssetRun blocks dirty command preview", () => {
    expect(validateAssetRun(baseFields({ commandPreviewDirty: true }), PREVIEW_GLB)).toMatch(
      /Apply command preview/,
    );
  });
});

describe("canRegenerateAsset", () => {
  it("is false when preview enemy does not match", () => {
    const fields = baseFields();
    const err = validateAssetRun(fields, "/api/assets/animated_exports/slug_animated_00.glb");
    expect(canRegenerateAsset(fields, "/api/assets/animated_exports/slug_animated_00.glb", err)).toBe(
      false,
    );
  });

  it("is true for matching animated export", () => {
    const fields = baseFields();
    expect(canRegenerateAsset(fields, PREVIEW_GLB, null)).toBe(true);
  });
});
