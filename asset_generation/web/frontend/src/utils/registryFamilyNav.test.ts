// @vitest-environment jsdom
import { describe, it, expect, afterEach } from "vitest";
import {
  REGISTRY_ENEMY_FAMILY_LS,
  parseSavedRegistryFamily,
  pickRegistryEnemyFamily,
  resolveRegistryFamilyFromCommandEnemy,
} from "./registryFamilyNav";

describe("registryFamilyNav", () => {
  const families = ["acid_spitter", "carapace_husk", "spider"] as const;

  afterEach(() => {
    localStorage.removeItem(REGISTRY_ENEMY_FAMILY_LS);
  });

  it("resolveRegistryFamilyFromCommandEnemy maps builder slug aliases", () => {
    expect(resolveRegistryFamilyFromCommandEnemy("spitter", families)).toBe("acid_spitter");
    expect(resolveRegistryFamilyFromCommandEnemy("imp", families)).toBeNull();
    expect(resolveRegistryFamilyFromCommandEnemy("spider", families)).toBe("spider");
  });

  it("pickRegistryEnemyFamily keeps current selection when still valid", () => {
    expect(pickRegistryEnemyFamily(families, "carapace_husk", "spider")).toBe("carapace_husk");
  });

  it("pickRegistryEnemyFamily uses saved localStorage when current invalid", () => {
    localStorage.setItem(REGISTRY_ENEMY_FAMILY_LS, "spider");
    expect(pickRegistryEnemyFamily(families, "missing", undefined)).toBe("spider");
  });

  it("pickRegistryEnemyFamily uses command enemy when no saved value", () => {
    expect(pickRegistryEnemyFamily(families, null, "spitter")).toBe("acid_spitter");
  });

  it("parseSavedRegistryFamily ignores unknown keys", () => {
    localStorage.setItem(REGISTRY_ENEMY_FAMILY_LS, "not_in_registry");
    expect(parseSavedRegistryFamily(families)).toBeNull();
  });
});
