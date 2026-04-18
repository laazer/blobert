import { describe, it, expect } from "vitest";
import { previewZoneFromMeshName } from "./previewZoneFromMeshName";

describe("previewZoneFromMeshName", () => {
  it("maps typical body / head / limb names", () => {
    expect(previewZoneFromMeshName("Body")).toBe("body");
    expect(previewZoneFromMeshName("Carapace_Main")).toBe("body");
    expect(previewZoneFromMeshName("Head")).toBe("head");
    expect(previewZoneFromMeshName("Eye_L")).toBe("head");
    expect(previewZoneFromMeshName("Leg_0_Segment")).toBe("limbs");
  });

  it("returns null when unknown", () => {
    expect(previewZoneFromMeshName("")).toBeNull();
    expect(previewZoneFromMeshName("Helper")).toBeNull();
  });
});
