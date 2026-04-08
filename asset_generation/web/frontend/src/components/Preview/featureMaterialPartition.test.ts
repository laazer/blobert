import { describe, expect, it } from "vitest";
import {
  partitionAnimatedFeatureDefs,
  sortZoneFeatureDefs,
  ZONE_FINISH_HEX_RE,
  zoneRowRank,
} from "./featureMaterialPartition";

describe("ZONE_FINISH_HEX_RE", () => {
  it("matches five coarse zones only", () => {
    expect(ZONE_FINISH_HEX_RE.test("feat_body_finish")).toBe(true);
    expect(ZONE_FINISH_HEX_RE.test("feat_joints_hex")).toBe(true);
    expect(ZONE_FINISH_HEX_RE.test("feat_extra_finish")).toBe(true);
    expect(ZONE_FINISH_HEX_RE.test("feat_limb_leg_0_hex")).toBe(false);
    expect(ZONE_FINISH_HEX_RE.test("feat_joint_leg_0_root_hex")).toBe(false);
  });
});

describe("zoneRowRank / sortZoneFeatureDefs", () => {
  it("orders body before head before limbs before joints before extra (finish then hex)", () => {
    const keys = [
      "feat_extra_hex",
      "feat_body_hex",
      "feat_head_finish",
      "feat_limbs_hex",
      "feat_body_finish",
      "feat_joints_finish",
    ];
    const sorted = sortZoneFeatureDefs(keys.map((key) => ({ key }))).map((d) => d.key);
    expect(sorted).toEqual([
      "feat_body_finish",
      "feat_body_hex",
      "feat_head_finish",
      "feat_limbs_hex",
      "feat_joints_finish",
      "feat_extra_hex",
    ]);
  });

  it("ranks unknown feat_ keys after known zones", () => {
    expect(zoneRowRank("feat_body_finish")).toBeLessThan(zoneRowRank("feat_future_zone_hex"));
  });
});

describe("partitionAnimatedFeatureDefs", () => {
  it("isolates all five spider zone rows when mixed with mesh keys and per-part keys", () => {
    const all = [
      { key: "eye_count" },
      { key: "BODY_BASE" },
      { key: "feat_extra_hex" },
      { key: "feat_joint_leg_0_root_hex" },
      { key: "feat_body_finish" },
      { key: "feat_limb_leg_1_hex" },
      { key: "feat_head_hex" },
      { key: "feat_limbs_finish" },
      { key: "feat_joints_finish" },
      { key: "feat_head_finish" },
      { key: "feat_body_hex" },
      { key: "feat_limbs_hex" },
      { key: "feat_joints_hex" },
      { key: "feat_extra_finish" },
    ];
    const { featureDefs, zoneDefs, limbPartDefs, jointPartDefs } = partitionAnimatedFeatureDefs(all);
    expect(featureDefs).toHaveLength(12);
    expect(zoneDefs.map((d) => d.key)).toEqual([
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
    expect(zoneDefs).toHaveLength(10);
    expect(limbPartDefs.map((d) => d.key)).toEqual(["feat_limb_leg_1_hex"]);
    expect(jointPartDefs.map((d) => d.key)).toEqual(["feat_joint_leg_0_root_hex"]);
  });

  it("claw_crawler exposes four zones × two fields when API lists them", () => {
    const all = [
      { key: "peripheral_eyes" },
      { key: "feat_body_finish" },
      { key: "feat_extra_hex" },
      { key: "feat_head_hex" },
      { key: "feat_limbs_finish" },
      { key: "feat_head_finish" },
      { key: "feat_body_hex" },
      { key: "feat_limbs_hex" },
      { key: "feat_extra_finish" },
    ];
    const { zoneDefs, limbPartDefs, jointPartDefs } = partitionAnimatedFeatureDefs(all);
    expect(zoneDefs).toHaveLength(8);
    expect(limbPartDefs).toHaveLength(0);
    expect(jointPartDefs).toHaveLength(0);
  });
});
