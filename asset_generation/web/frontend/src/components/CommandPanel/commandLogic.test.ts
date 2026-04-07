import { describe, expect, it } from "vitest";
import {
  clampCount,
  formatCommandPreview,
  getEnemyOptions,
  normalizeEnemyForCmd,
  parseCommandPreview,
  PLAYER_COLORS,
} from "./commandLogic";

describe("command logic", () => {
  it("uses player color options for player cmd", () => {
    expect(getEnemyOptions("player", ["tar_slug"])).toEqual(PLAYER_COLORS);
  });

  it("normalizes invalid player enemy to first color", () => {
    expect(normalizeEnemyForCmd("player", "tar_slug", ["adhesion_bug"])).toBe("blue");
  });

  it("keeps valid player color", () => {
    expect(normalizeEnemyForCmd("player", "pink", ["adhesion_bug"])).toBe("pink");
  });

  it("clamps count to bounds", () => {
    expect(clampCount(0)).toBe(1);
    expect(clampCount(999)).toBe(10);
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

  it("formats player command preview with count", () => {
    const preview = formatCommandPreview({
      cmd: "player",
      enemy: "blue",
      count: 2,
      description: "",
      difficulty: "normal",
      finish: "glossy",
      hexColor: "",
    });
    expect(preview).toBe("player blue 2 --finish glossy");
  });

  it("parses player finish and hex color flags", () => {
    const parsed = parseCommandPreview("player blue 1 --finish matte --hex-color #112233");
    expect(parsed.error).toBeNull();
    expect(parsed.next).toEqual({
      cmd: "player",
      enemy: "blue",
      count: 1,
      finish: "matte",
      hexColor: "#112233",
    });
  });

  it("parses animated finish and hex color flags", () => {
    const parsed = parseCommandPreview("animated tar_slug 1 --finish metallic --hex-color #aa8844");
    expect(parsed.error).toBeNull();
    expect(parsed.next).toEqual({
      cmd: "animated",
      enemy: "tar_slug",
      count: 1,
      finish: "metallic",
      hexColor: "#aa8844",
    });
  });
});
