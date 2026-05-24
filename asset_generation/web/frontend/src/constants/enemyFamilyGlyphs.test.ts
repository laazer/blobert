import { describe, it, expect } from "vitest";
import { enemyFamilyGlyph, ENEMY_FAMILY_GLYPHS } from "./enemyFamilyGlyphs";

describe("enemyFamilyGlyphs", () => {
  it("maps registry slugs from redesign ENEMY_FAMILIES", () => {
    expect(ENEMY_FAMILY_GLYPHS.spider).toBe("🕷");
    expect(ENEMY_FAMILY_GLYPHS.tar_slug).toBe("●");
    expect(ENEMY_FAMILY_GLYPHS.carapace_husk).toBe("⬢");
  });

  it("falls back to element glyph then default", () => {
    expect(enemyFamilyGlyph("unknown_family", "⚡")).toBe("⚡");
    expect(enemyFamilyGlyph("unknown_family")).toBe("◆");
  });

  it("normalizes slug before lookup", () => {
    expect(enemyFamilyGlyph("  SPIDER  ")).toBe("🕷");
  });
});
