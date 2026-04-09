import { describe, expect, it } from "vitest";
import {
  formatCommandPreview,
  getEnemyOptions,
  normalizeEnemyForCmd,
  parseCommandPreview,
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

  it("parses command preview with flags", () => {
    const parsed = parseCommandPreview('smart --description "fire slug" --difficulty hard');
    expect(parsed.error).toBeNull();
    expect(parsed.next).toEqual({
      cmd: "smart",
      description: "fire slug",
      difficulty: "hard",
    });
  });

  it("formats player command preview with variant count before flags", () => {
    const preview = formatCommandPreview({
      cmd: "player",
      enemy: "blue",
      description: "",
      difficulty: "normal",
      finish: "glossy",
      hexColor: "",
      variantCount: 1,
    });
    expect(preview).toBe("player blue 1 --finish glossy");
  });

  it("formats animated preview with multi-variant count", () => {
    expect(
      formatCommandPreview({
        cmd: "animated",
        enemy: "spider",
        description: "",
        difficulty: "normal",
        finish: "default",
        hexColor: "",
        variantCount: 3,
      }),
    ).toBe("animated spider 3 --finish default");
  });

  it("parses player finish and hex color flags", () => {
    const parsed = parseCommandPreview("player blue 1 --finish matte --hex-color #112233");
    expect(parsed.error).toBeNull();
    expect(parsed.next).toEqual({
      cmd: "player",
      enemy: "blue",
      variantCount: 1,
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
      variantCount: 1,
      finish: "metallic",
      hexColor: "#aa8844",
    });
  });

  it("parses optional variant count for animated", () => {
    const parsed = parseCommandPreview("animated imp 5 --finish matte");
    expect(parsed.error).toBeNull();
    expect(parsed.next?.variantCount).toBe(5);
    expect(parsed.next?.enemy).toBe("imp");
  });

  it("rejects non-integer variant count", () => {
    const parsed = parseCommandPreview("animated spider 3.5 --finish default");
    expect(parsed.error).toContain("integer");
  });
});
