import { describe, it, expect } from "vitest";
import { regeneratePreviewParams } from "./regeneratePreviewParams";

describe("regeneratePreviewParams", () => {
  it("returns animated variant and draft flag when path matches enemy", () => {
    expect(
      regeneratePreviewParams(
        "animated",
        "spider",
        "/api/assets/animated_exports/draft/spider_animated_02.glb?t=1",
      ),
    ).toEqual({ replaceVariantIndex: 2, outputDraft: true });
    expect(
      regeneratePreviewParams(
        "animated",
        "spider",
        "/api/assets/animated_exports/spider_animated_00.glb",
      ),
    ).toEqual({ replaceVariantIndex: 0, outputDraft: false });
  });

  it("returns null when animated enemy mismatches filename slug", () => {
    expect(
      regeneratePreviewParams(
        "animated",
        "slug",
        "/api/assets/animated_exports/spider_animated_00.glb",
      ),
    ).toBeNull();
  });

  it("returns null for animated all or empty enemy", () => {
    expect(
      regeneratePreviewParams("animated", "all", "/api/assets/animated_exports/spider_animated_00.glb"),
    ).toBeNull();
    expect(regeneratePreviewParams("animated", "", "/api/assets/animated_exports/spider_animated_00.glb")).toBeNull();
  });

  it("returns player params when stem matches player_slime_{color}_NN", () => {
    expect(
      regeneratePreviewParams(
        "player",
        "blue",
        "/api/assets/player_exports/draft/player_slime_blue_01.glb",
      ),
    ).toEqual({ replaceVariantIndex: 1, outputDraft: true });
  });

  it("returns null when player color mismatches", () => {
    expect(
      regeneratePreviewParams(
        "player",
        "green",
        "/api/assets/player_exports/player_slime_blue_00.glb",
      ),
    ).toBeNull();
  });

  it("returns level params when stem matches object_NN", () => {
    expect(
      regeneratePreviewParams(
        "level",
        "spike_trap",
        "/api/assets/level_exports/spike_trap_03.glb",
      ),
    ).toEqual({ replaceVariantIndex: 3, outputDraft: false });
  });

  it("returns null when URL is not an assets GLB", () => {
    expect(regeneratePreviewParams("animated", "spider", null)).toBeNull();
    expect(regeneratePreviewParams("animated", "spider", "/other")).toBeNull();
  });
});
