import { describe, expect, it } from "vitest";
import {
  ENEMY_EMPTY_SLOTS_COPY,
  PLAYER_RESTART_REQUIREMENT_COPY,
} from "./ModelRegistryPane";

describe("ModelRegistryPane UX copy contracts", () => {
  it("documents restart requirement for player visual changes", () => {
    expect(PLAYER_RESTART_REQUIREMENT_COPY).toContain("next game load/restart");
    expect(PLAYER_RESTART_REQUIREMENT_COPY.toLowerCase()).toContain("hot-reload is not guaranteed");
  });

  it("documents fallback behavior when a family has zero slots", () => {
    expect(ENEMY_EMPTY_SLOTS_COPY.toLowerCase()).toContain("falls back");
    expect(ENEMY_EMPTY_SLOTS_COPY.toLowerCase()).toContain("legacy default path");
  });
});
