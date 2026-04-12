// @vitest-environment jsdom
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import {
  DEFAULT_POWER_TYPES,
  addPowerType,
  generatePowerTypeId,
  loadPlayerPowerTypes,
  loadPowerTypeSlots,
  removePowerType,
  renamePowerType,
  savePlayerPowerTypes,
  savePowerTypeSlots,
  type PlayerPowerType,
} from "./playerPowerTypes";

const LS_KEY = "blobert.player.power_types";
const LS_SLOTS = (id: string) => `blobert.player.pt_slots.${id}`;

describe("playerPowerTypes utilities", () => {
  beforeEach(() => {
    localStorage.clear();
  });
  afterEach(() => {
    localStorage.clear();
  });

  // ── generatePowerTypeId ──────────────────────────────────────────────────
  describe("generatePowerTypeId", () => {
    it("returns a non-empty string starting with pt_", () => {
      expect(generatePowerTypeId()).toMatch(/^pt_/);
    });

    it("returns unique ids on successive calls", () => {
      const ids = new Set(Array.from({ length: 20 }, () => generatePowerTypeId()));
      expect(ids.size).toBe(20);
    });
  });

  // ── loadPlayerPowerTypes ─────────────────────────────────────────────────
  describe("loadPlayerPowerTypes", () => {
    it("returns DEFAULT_POWER_TYPES when localStorage is empty", () => {
      expect(loadPlayerPowerTypes()).toEqual(DEFAULT_POWER_TYPES);
    });

    it("returns DEFAULT_POWER_TYPES when localStorage contains invalid JSON", () => {
      localStorage.setItem(LS_KEY, "{bad json}");
      expect(loadPlayerPowerTypes()).toEqual(DEFAULT_POWER_TYPES);
    });

    it("returns DEFAULT_POWER_TYPES for an empty array", () => {
      localStorage.setItem(LS_KEY, "[]");
      expect(loadPlayerPowerTypes()).toEqual(DEFAULT_POWER_TYPES);
    });

    it("filters out entries missing id or label", () => {
      localStorage.setItem(
        LS_KEY,
        JSON.stringify([
          { id: "a", label: "Alpha" },
          { label: "no-id" },
          { id: "", label: "empty-id" },
          { id: "b" },
        ]),
      );
      const result = loadPlayerPowerTypes();
      expect(result).toHaveLength(1);
      expect(result[0]).toEqual({ id: "a", label: "Alpha" });
    });

    it("round-trips a saved array", () => {
      const types: PlayerPowerType[] = [
        { id: "fire", label: "Fire" },
        { id: "ice", label: "Ice" },
      ];
      savePlayerPowerTypes(types);
      expect(loadPlayerPowerTypes()).toEqual(types);
    });
  });

  // ── savePowerTypeSlots / loadPowerTypeSlots ──────────────────────────────
  describe("slot persistence", () => {
    it("returns empty array when no slots saved", () => {
      expect(loadPowerTypeSlots("fire")).toEqual([]);
    });

    it("round-trips slot ids", () => {
      savePowerTypeSlots("fire", ["v1", "v2", ""]);
      expect(loadPowerTypeSlots("fire")).toEqual(["v1", "v2", ""]);
    });

    it("filters non-string entries from corrupted data", () => {
      localStorage.setItem(LS_SLOTS("x"), JSON.stringify([1, "valid", null, "also_valid"]));
      expect(loadPowerTypeSlots("x")).toEqual(["valid", "also_valid"]);
    });

    it("sections are independent — different ptIds don't bleed", () => {
      savePowerTypeSlots("fire", ["v1"]);
      savePowerTypeSlots("ice", ["v2"]);
      expect(loadPowerTypeSlots("fire")).toEqual(["v1"]);
      expect(loadPowerTypeSlots("ice")).toEqual(["v2"]);
    });
  });

  // ── addPowerType ─────────────────────────────────────────────────────────
  describe("addPowerType", () => {
    it("appends a new entry with a unique id", () => {
      const result = addPowerType(DEFAULT_POWER_TYPES, "Fire");
      expect(result).toHaveLength(2);
      expect(result[1].label).toBe("Fire");
      expect(result[1].id).toMatch(/^pt_/);
    });

    it("does not mutate the input array", () => {
      const original = [...DEFAULT_POWER_TYPES];
      addPowerType(DEFAULT_POWER_TYPES, "New");
      expect(DEFAULT_POWER_TYPES).toEqual(original);
    });

    it("trims the label and falls back to 'New power type' for blank", () => {
      const result = addPowerType(DEFAULT_POWER_TYPES, "  ");
      expect(result[1].label).toBe("New power type");
    });
  });

  // ── renamePowerType ──────────────────────────────────────────────────────
  describe("renamePowerType", () => {
    it("renames matching id", () => {
      const types = DEFAULT_POWER_TYPES;
      const result = renamePowerType(types, "default", "Renamed");
      expect(result[0].label).toBe("Renamed");
    });

    it("is a no-op when id is not found", () => {
      const result = renamePowerType(DEFAULT_POWER_TYPES, "nonexistent", "X");
      expect(result).toEqual(DEFAULT_POWER_TYPES);
    });

    it("ignores blank label (keeps original)", () => {
      const types: PlayerPowerType[] = [{ id: "a", label: "Alpha" }];
      const result = renamePowerType(types, "a", "  ");
      expect(result[0].label).toBe("Alpha");
    });

    it("does not mutate the input array", () => {
      const types: PlayerPowerType[] = [{ id: "a", label: "Alpha" }];
      renamePowerType(types, "a", "Beta");
      expect(types[0].label).toBe("Alpha");
    });
  });

  // ── removePowerType ──────────────────────────────────────────────────────
  describe("removePowerType", () => {
    it("removes entry with matching id", () => {
      const types: PlayerPowerType[] = [
        { id: "a", label: "Alpha" },
        { id: "b", label: "Beta" },
      ];
      const result = removePowerType(types, "a");
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe("b");
    });

    it("returns the original array unchanged when only one entry", () => {
      const result = removePowerType(DEFAULT_POWER_TYPES, DEFAULT_POWER_TYPES[0].id);
      expect(result).toEqual(DEFAULT_POWER_TYPES);
    });

    it("is a no-op when id is not found", () => {
      const types: PlayerPowerType[] = [
        { id: "a", label: "A" },
        { id: "b", label: "B" },
      ];
      expect(removePowerType(types, "zzz")).toEqual(types);
    });

    it("does not mutate the input array", () => {
      const types: PlayerPowerType[] = [
        { id: "a", label: "A" },
        { id: "b", label: "B" },
      ];
      removePowerType(types, "a");
      expect(types).toHaveLength(2);
    });
  });
});
