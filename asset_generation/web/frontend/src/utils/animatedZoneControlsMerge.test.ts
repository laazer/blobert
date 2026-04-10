import { describe, expect, it } from "vitest";
import type { AnimatedBuildControlDef } from "../types";
import { mergeCanonicalZoneControls, mergeCanonicalZoneControlsForAllSlugs } from "./animatedZoneControlsMerge";

describe("mergeCanonicalZoneControls", () => {
  it("fills missing spider zones when API only returned body", () => {
    const limb: AnimatedBuildControlDef = {
      key: "feat_limb_leg_0_finish",
      label: "Leg 0 finish",
      type: "select_str",
      options: ["default"],
      default: "default",
    };
    const incoming: AnimatedBuildControlDef[] = [
      {
        key: "eye_count",
        label: "Eyes",
        type: "select",
        options: [4, 6],
        default: 4,
      },
      {
        key: "feat_body_finish",
        label: "Body finish",
        type: "select_str",
        options: ["default", "glossy"],
        default: "default",
      },
      {
        key: "feat_body_hex",
        label: "Body hex",
        type: "str",
        default: "",
      },
      limb,
    ];
    const merged = mergeCanonicalZoneControls("spider", incoming);
    const zoneKeys = merged.filter((d) => /^feat_(body|head|limbs|joints|extra)_(finish|hex)$/.test(d.key));
    expect(zoneKeys.map((d) => d.key)).toEqual([
      "feat_body_finish",
      "feat_body_hex",
      "feat_head_finish",
      "feat_head_hex",
      "feat_limbs_finish",
      "feat_limbs_hex",
      "feat_joints_finish",
      "feat_joints_hex",
      "feat_extra_finish",
      "feat_extra_hex",
    ]);
    const limbIdx = merged.indexOf(limb);
    const headIdx = merged.findIndex((d) => d.key === "feat_head_finish");
    expect(headIdx).toBeGreaterThan(-1);
    expect(headIdx).toBeLessThan(limbIdx);
  });

  it("is a no-op for unknown slug", () => {
    const defs: AnimatedBuildControlDef[] = [
      { key: "feat_body_finish", label: "Body finish", type: "select_str", options: ["a"], default: "a" },
    ];
    expect(mergeCanonicalZoneControls("unknown_enemy", defs)).toEqual(defs);
  });

  it("appends synthetic extra_zone_* controls for slug", () => {
    const merged = mergeCanonicalZoneControls("slug", []);
    const extraKeys = merged.filter((d) => d.key.startsWith("extra_zone_")).map((d) => d.key);
    expect(extraKeys).toContain("extra_zone_body_kind");
    expect(extraKeys).toContain("extra_zone_head_spike_shape");
    expect(extraKeys).toContain("extra_zone_extra_hex");
    expect(extraKeys).toContain("extra_zone_body_place_top");
    expect(extraKeys).toHaveLength(51);
  });
});

describe("mergeCanonicalZoneControlsForAllSlugs", () => {
  it("seeds spider zone controls when API returns empty animated_build_controls", () => {
    const merged = mergeCanonicalZoneControlsForAllSlugs({}, ["spider"]);
    expect(merged.spider).toBeDefined();
    const zoneKeys = (merged.spider ?? []).filter((d) =>
      /^feat_(body|head|limbs|joints|extra)_(finish|hex)$/.test(d.key),
    );
    expect(zoneKeys).toHaveLength(10);
  });

  it("normalizes API slug keys to lowercase", () => {
    const merged = mergeCanonicalZoneControlsForAllSlugs({ Spider: [] }, []);
    expect(merged.spider).toBeDefined();
    expect(merged.Spider).toBeUndefined();
  });
});
