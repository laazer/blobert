import { describe, expect, it } from "vitest";
import type { AnimatedBuildControlDef } from "../../types";
import {
  formatCommandPreview,
  getEnemyOptions,
  normalizeEnemyForCmd,
  parseCommandPreview,
  partitionAnimatedBuildOptionsForJson,
  PLAYER_COLORS,
} from "./commandLogic";

describe("command logic", () => {
  it("uses player color options for player cmd", () => {
    expect(getEnemyOptions("player", ["slug"])).toEqual(PLAYER_COLORS);
  });

  it("normalizes invalid player enemy to first color", () => {
    expect(normalizeEnemyForCmd("player", "slug", ["spider"])).toBe("blue");
  });

  it("keeps valid player color", () => {
    expect(normalizeEnemyForCmd("player", "pink", ["spider"])).toBe("pink");
  });

  it("returns error for removed 'smart' command", () => {
    const parsed = parseCommandPreview('smart --description "fire slug" --difficulty hard');
    expect(parsed.error).toContain("Unknown cmd 'smart'");
    expect(parsed.next).toBeNull();
  });

  it("formats player command preview with finish before flags", () => {
    const preview = formatCommandPreview({
      cmd: "player",
      enemy: "blue",
      description: "",
      difficulty: "normal",
      finish: "glossy",
      hexColor: "",
    });
    expect(preview).toBe("player blue --finish glossy");
  });

  it("formats animated preview without variant count", () => {
    expect(
      formatCommandPreview({
        cmd: "animated",
        enemy: "spider",
        description: "",
        difficulty: "normal",
        finish: "default",
        hexColor: "",
      }),
    ).toBe("animated spider --finish default");
  });

  it("parses player finish and hex color flags", () => {
    const parsed = parseCommandPreview("player blue 1 --finish matte --hex-color #112233");
    expect(parsed.error).toBeNull();
    expect(parsed.next).toEqual({
      cmd: "player",
      enemy: "blue",
      finish: "matte",
      hexColor: "#112233",
    });
  });

  it("parses animated finish and hex color flags", () => {
    const parsed = parseCommandPreview("animated slug 1 --finish metallic --hex-color #aa8844");
    expect(parsed.error).toBeNull();
    expect(parsed.next).toEqual({
      cmd: "animated",
      enemy: "slug",
      finish: "metallic",
      hexColor: "#aa8844",
    });
  });

  it("accepts legacy optional count token after enemy (ignored)", () => {
    const parsed = parseCommandPreview("animated imp 5 --finish matte");
    expect(parsed.error).toBeNull();
    expect(parsed.next?.enemy).toBe("imp");
    expect(parsed.next?.finish).toBe("matte");
  });

  it("rejects non-integer legacy count token", () => {
    const parsed = parseCommandPreview("animated spider 3.5 --finish default");
    expect(parsed.error).toContain("integer");
  });
});

describe("partitionAnimatedBuildOptionsForJson", () => {
  const defs: AnimatedBuildControlDef[] = [
    { key: "BODY_BASE", label: "Body", type: "float", min: 0.5, max: 2, step: 0.05, default: 1 },
    {
      key: "extra_zone_body_spike_size",
      label: "Spike size",
      type: "float",
      min: 0.25,
      max: 3,
      step: 0.05,
      default: 1,
    },
    {
      key: "extra_zone_body_place_top",
      label: "Top",
      type: "bool",
      default: true,
    },
  ];

  it("puts only uppercase mesh float keys under mesh", () => {
    const out = partitionAnimatedBuildOptionsForJson(
      { BODY_BASE: 1.4, extra_zone_body_spike_size: 2.5, extra_zone_body_place_top: false },
      defs,
    );
    expect(out.mesh).toEqual({ BODY_BASE: 1.4 });
    expect(out.extra_zone_body_spike_size).toBe(2.5);
    expect(out.extra_zone_body_place_top).toBe(false);
  });

  it("omits mesh when no mesh keys are set", () => {
    const out = partitionAnimatedBuildOptionsForJson({ extra_zone_body_spike_size: 1.8 }, defs);
    expect(out.mesh).toBeUndefined();
    expect(out.extra_zone_body_spike_size).toBe(1.8);
  });
});
