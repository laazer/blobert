import { describe, expect, it } from "vitest";
import type { AnimatedBuildControlDef } from "../../types";
import {
  SUFFIX_ORDER,
  extraZoneFromDefKey,
  kindOptionsForZone,
  partitionZoneExtraDefs,
  suffixRank,
} from "./zoneExtrasPartition";
// rowDisabled must be exported from ZoneExtraControls.tsx as part of implementation (ticket 17 Req 8).
// REQUIRES_EXPORT: `export function rowDisabled` in ZoneExtraControls.tsx
import { rowDisabled } from "./ZoneExtraControls";

describe("zoneExtrasPartition", () => {
  it("parses zone from def key", () => {
    expect(extraZoneFromDefKey("extra_zone_body_kind")).toBe("body");
    expect(extraZoneFromDefKey("feat_body_finish")).toBeNull();
  });

  it("partitions defs by zone in FEATURE_ZONES_BY_SLUG order for slug", () => {
    const defs: AnimatedBuildControlDef[] = [
      {
        key: "extra_zone_extra_kind",
        label: "Extra kind",
        type: "select_str",
        options: ["none"],
        default: "none",
      },
      {
        key: "extra_zone_body_spike_count",
        label: "Spikes",
        type: "int",
        min: 1,
        max: 24,
        default: 8,
      },
      {
        key: "extra_zone_body_kind",
        label: "Body kind",
        type: "select_str",
        options: ["none", "spikes"],
        default: "none",
      },
    ];
    const { zones, byZone, hasAny } = partitionZoneExtraDefs("slug", defs);
    expect(hasAny).toBe(true);
    expect(zones).toEqual(["body", "head", "extra"]);
    expect(byZone.body.map((d) => d.key)).toEqual(["extra_zone_body_kind", "extra_zone_body_spike_count"]);
    expect(byZone.extra.map((d) => d.key)).toEqual(["extra_zone_extra_kind"]);
  });

  it("omits horns from non-head kind options", () => {
    expect(kindOptionsForZone("head")).toContain("horns");
    expect(kindOptionsForZone("body")).not.toContain("horns");
  });
});

// ---------------------------------------------------------------------------
// Requirement 7: SUFFIX_ORDER and suffixRank — offset_x/y/z
// Spec: project_board/specs/zone_extras_offset_xyz_controls_spec.md  Req 7
// Ticket: 17_zone_extras_offset_xyz_controls
// ---------------------------------------------------------------------------

describe("zoneExtrasPartition — offset suffix ordering (ticket 17)", () => {
  // AC-7.1: SUFFIX_ORDER must contain offset_x, offset_y, offset_z as its last three entries.
  it("SUFFIX_ORDER contains offset_x, offset_y, offset_z as the last three entries (AC-7.1)", () => {
    // SUFFIX_ORDER is exported as const — cast to string array for indexing
    const order = SUFFIX_ORDER as readonly string[];
    const n = order.length;
    expect(n).toBeGreaterThanOrEqual(3);
    expect(order[n - 3]).toBe("offset_x");
    expect(order[n - 2]).toBe("offset_y");
    expect(order[n - 1]).toBe("offset_z");
  });

  // AC-7.2: suffixRank for offset keys must be greater than suffixRank for hex.
  it("suffixRank('extra_zone_body_offset_x') > suffixRank('extra_zone_body_hex') (AC-7.2)", () => {
    expect(suffixRank("extra_zone_body_offset_x")).toBeGreaterThan(
      suffixRank("extra_zone_body_hex"),
    );
  });

  it("suffixRank('extra_zone_body_offset_y') > suffixRank('extra_zone_body_hex')", () => {
    expect(suffixRank("extra_zone_body_offset_y")).toBeGreaterThan(
      suffixRank("extra_zone_body_hex"),
    );
  });

  it("suffixRank('extra_zone_body_offset_z') > suffixRank('extra_zone_body_hex')", () => {
    expect(suffixRank("extra_zone_body_offset_z")).toBeGreaterThan(
      suffixRank("extra_zone_body_hex"),
    );
  });

  // AC-7.3: offset suffix rank must be a recognized index (< 99 fallback).
  it("suffixRank for offset_x/y/z returns a defined index, not the 99 fallback (AC-7.3)", () => {
    expect(suffixRank("extra_zone_body_offset_x")).toBeLessThan(99);
    expect(suffixRank("extra_zone_body_offset_y")).toBeLessThan(99);
    expect(suffixRank("extra_zone_body_offset_z")).toBeLessThan(99);
  });

  // AC-7.4: partitionZoneExtraDefs places offset defs after hex in the sorted per-zone list.
  it("partitionZoneExtraDefs places offset_x/y/z defs after hex in sorted zone list (AC-7.4)", () => {
    const defs: AnimatedBuildControlDef[] = [
      {
        key: "extra_zone_body_offset_z",
        label: "Body offset Z",
        type: "float",
        min: -2,
        max: 2,
        step: 0.05,
        default: 0,
      },
      {
        key: "extra_zone_body_hex",
        label: "Body hex",
        type: "str",
        default: "",
      },
      {
        key: "extra_zone_body_offset_x",
        label: "Body offset X",
        type: "float",
        min: -2,
        max: 2,
        step: 0.05,
        default: 0,
      },
      {
        key: "extra_zone_body_kind",
        label: "Body kind",
        type: "select_str",
        options: ["none", "spikes"],
        default: "none",
      },
    ];
    const { byZone } = partitionZoneExtraDefs("slug", defs);
    const bodyKeys = byZone.body.map((d) => d.key);
    const hexIdx = bodyKeys.indexOf("extra_zone_body_hex");
    const oxIdx = bodyKeys.indexOf("extra_zone_body_offset_x");
    const ozIdx = bodyKeys.indexOf("extra_zone_body_offset_z");
    expect(hexIdx).toBeGreaterThanOrEqual(0);
    expect(oxIdx).toBeGreaterThan(hexIdx);
    expect(ozIdx).toBeGreaterThan(hexIdx);
  });

  // AC-7.5: Existing suffix order for pre-existing suffixes is unchanged.
  it("SUFFIX_ORDER preserves existing suffix positions — kind before spike_shape before spike_count (AC-7.5)", () => {
    const order = SUFFIX_ORDER as readonly string[];
    const kindIdx = order.indexOf("kind");
    const spikeShapeIdx = order.indexOf("spike_shape");
    const spikeCountIdx = order.indexOf("spike_count");
    const hexIdx = order.indexOf("hex");
    expect(kindIdx).toBeGreaterThanOrEqual(0);
    expect(spikeShapeIdx).toBeGreaterThan(kindIdx);
    expect(spikeCountIdx).toBeGreaterThan(spikeShapeIdx);
    expect(hexIdx).toBeGreaterThanOrEqual(0);
    // All pre-existing entries must still be present
    for (const suffix of [
      "kind", "spike_shape", "spike_count", "spike_size",
      "bulb_count", "bulb_size", "clustering", "distribution",
      "uniform_shape", "place_top", "place_bottom", "place_front",
      "place_back", "place_right", "place_left", "finish", "hex",
    ]) {
      expect(order).toContain(suffix);
    }
  });
});

// ---------------------------------------------------------------------------
// Requirement 8: rowDisabled — offset controls always enabled
// Spec: project_board/specs/zone_extras_offset_xyz_controls_spec.md  Req 8
// Ticket: 17_zone_extras_offset_xyz_controls
// REQUIRES_EXPORT: `export function rowDisabled` must be added to ZoneExtraControls.tsx
// ---------------------------------------------------------------------------

describe("ZoneExtraControls rowDisabled — offset keys always enabled (ticket 17)", () => {
  // AC-8.1: offset_x is never disabled, even when kind='none'
  it("rowDisabled('none', 'extra_zone_body_offset_x', 'uniform') === false (AC-8.1)", () => {
    expect(rowDisabled("none", "extra_zone_body_offset_x", "uniform")).toBe(false);
  });

  // AC-8.2: offset_y is never disabled for kind='none'
  it("rowDisabled('none', 'extra_zone_body_offset_y', 'uniform') === false (AC-8.2)", () => {
    expect(rowDisabled("none", "extra_zone_body_offset_y", "uniform")).toBe(false);
  });

  // AC-8.3: offset_z is never disabled for kind='none'
  it("rowDisabled('none', 'extra_zone_body_offset_z', 'uniform') === false (AC-8.3)", () => {
    expect(rowDisabled("none", "extra_zone_body_offset_z", "uniform")).toBe(false);
  });

  // AC-8.4: offset_x is not disabled for kind='shell'
  it("rowDisabled('shell', 'extra_zone_body_offset_x', 'uniform') === false (AC-8.4)", () => {
    expect(rowDisabled("shell", "extra_zone_body_offset_x", "uniform")).toBe(false);
  });

  // AC-8.5: offset_x is not disabled for kind='spikes'
  it("rowDisabled('spikes', 'extra_zone_body_offset_x', 'uniform') === false (AC-8.5)", () => {
    expect(rowDisabled("spikes", "extra_zone_body_offset_x", "uniform")).toBe(false);
  });

  // AC-8.6: offset_z on head zone is not disabled for kind='horns'
  it("rowDisabled('horns', 'extra_zone_head_offset_z', 'uniform') === false (AC-8.6)", () => {
    expect(rowDisabled("horns", "extra_zone_head_offset_z", "uniform")).toBe(false);
  });

  // AC-8.7: existing disable logic for non-offset keys is unaffected
  it("rowDisabled('none', 'extra_zone_body_spike_count', 'uniform') === true (AC-8.7, existing behavior preserved)", () => {
    expect(rowDisabled("none", "extra_zone_body_spike_count", "uniform")).toBe(true);
  });

  it("rowDisabled('none', 'extra_zone_body_clustering', 'uniform') === true (AC-8.7, existing behavior preserved)", () => {
    expect(rowDisabled("none", "extra_zone_body_clustering", "uniform")).toBe(true);
  });
});
