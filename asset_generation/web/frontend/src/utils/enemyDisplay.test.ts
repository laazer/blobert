import { describe, expect, it } from "vitest";
import { enemySelectOptionLabel, normalizeAnimatedSlug, slugDisplayLabel } from "./enemyDisplay";

describe("slugDisplayLabel", () => {
  it("title-cases snake_case when meta is absent", () => {
    expect(slugDisplayLabel("spider")).toBe("Spider");
    expect(slugDisplayLabel("future_creep")).toBe("Future Creep");
  });

  it("uses backend meta label when provided", () => {
    expect(
      slugDisplayLabel("claw_crawler", [{ slug: "claw_crawler", label: "Claw crawler" }]),
    ).toBe("Claw crawler");
  });
});

describe("normalizeAnimatedSlug", () => {
  it("lowercases and trims for API key lookup", () => {
    expect(normalizeAnimatedSlug("Spider")).toBe("spider");
    expect(normalizeAnimatedSlug("  claw_crawler  ")).toBe("claw_crawler");
  });
});

describe("enemySelectOptionLabel", () => {
  it("title-cases player colors", () => {
    expect(enemySelectOptionLabel("player", "blue")).toBe("Blue");
  });

  it("uses animated meta for non-player when provided", () => {
    expect(
      enemySelectOptionLabel("animated", "imp", [{ slug: "imp", label: "Imp" }]),
    ).toBe("Imp");
  });
});
