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

  it("formats player command preview without count", () => {
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

  it("parses player finish and hex color flags", () => {
    const parsed = parseCommandPreview("player blue --finish matte --hex-color #112233");
    expect(parsed.error).toBeNull();
    expect(parsed.next).toEqual({
      cmd: "player",
      enemy: "blue",
      finish: "matte",
      hexColor: "#112233",
    });
  });

  it("parses animated finish and hex color flags", () => {
    const parsed = parseCommandPreview("animated slug --finish metallic --hex-color #aa8844");
    expect(parsed.error).toBeNull();
    expect(parsed.next).toEqual({
      cmd: "animated",
      enemy: "slug",
      finish: "metallic",
      hexColor: "#aa8844",
    });
  });
});
