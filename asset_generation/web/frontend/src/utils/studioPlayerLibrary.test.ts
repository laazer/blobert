// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import type { RegistryEnemyVersion } from "../types";
import {
  filterVersionsByPlayerColor,
  playerColorFromVersionId,
  versionMatchesPlayerColor,
} from "./studioPlayerLibrary";

const blue: RegistryEnemyVersion = {
  id: "player_slime_blue_00",
  path: "player_exports/player_slime_blue_00.glb",
  draft: false,
  in_use: true,
};

const green: RegistryEnemyVersion = {
  id: "player_slime_green_01",
  path: "player_exports/draft/player_slime_green_01.glb",
  draft: true,
  in_use: false,
};

describe("studioPlayerLibrary", () => {
  it("parses color from version id", () => {
    expect(playerColorFromVersionId("player_slime_blue_00")).toBe("blue");
  });

  it("filters versions by slime color", () => {
    const rows = filterVersionsByPlayerColor([blue, green], "blue");
    expect(rows).toHaveLength(1);
    expect(rows[0].id).toBe("player_slime_blue_00");
  });

  it("matches color from export path when id is unexpected", () => {
    expect(
      versionMatchesPlayerColor(
        { id: "legacy", path: "player_exports/player_slime_red_02.glb" },
        "red",
      ),
    ).toBe(true);
  });
});
