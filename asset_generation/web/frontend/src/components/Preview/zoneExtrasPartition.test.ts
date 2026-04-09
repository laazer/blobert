import { describe, expect, it } from "vitest";
import type { AnimatedBuildControlDef } from "../../types";
import {
  extraZoneFromDefKey,
  kindOptionsForZone,
  partitionZoneExtraDefs,
} from "./zoneExtrasPartition";

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
