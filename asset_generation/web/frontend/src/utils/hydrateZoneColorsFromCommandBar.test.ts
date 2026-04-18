import { describe, expect, it } from "vitest";
import { mergeCanonicalZoneControlsForAllSlugs } from "./animatedZoneControlsMerge";
import { buildZoneColorHydrationFromCommandBar } from "./hydrateZoneColorsFromCommandBar";

describe("buildZoneColorHydrationFromCommandBar", () => {
  const controls = mergeCanonicalZoneControlsForAllSlugs({}, ["spider"]);
  const defs = controls.spider ?? [];

  it("maps command finish + hex onto zones still at defaults", () => {
    const current = {
      feat_body_finish: "default",
      feat_body_hex: "",
      feat_head_finish: "default",
      feat_head_hex: "",
    };
    const out = buildZoneColorHydrationFromCommandBar(
      "spider",
      defs,
      current,
      "glossy",
      "#112233",
    );
    expect(out.feat_body_finish).toBe("glossy");
    expect(out.feat_head_finish).toBe("glossy");
    expect(out.feat_body_hex).toBe("112233");
    expect(out.feat_head_hex).toBe("112233");
  });

  it("does not override zones the user already changed", () => {
    const current = {
      feat_body_finish: "matte",
      feat_body_hex: "",
      feat_head_finish: "default",
      feat_head_hex: "",
    };
    const out = buildZoneColorHydrationFromCommandBar(
      "spider",
      defs,
      current,
      "glossy",
      "#ffffff",
    );
    expect(out.feat_body_finish).toBeUndefined();
    expect(out.feat_head_finish).toBe("glossy");
  });

  it("skips hex when command bar hex is empty", () => {
    const current = {
      feat_body_finish: "default",
      feat_body_hex: "",
    };
    const out = buildZoneColorHydrationFromCommandBar("spider", defs, current, "default", "");
    expect(out.feat_body_hex).toBeUndefined();
  });

  it("hydrates when defs are empty (no default keys) and feat_* are missing from current", () => {
    const emptyDefs: typeof defs = [];
    const current = {};
    const out = buildZoneColorHydrationFromCommandBar(
      "spider",
      emptyDefs,
      current,
      "glossy",
      "#112233",
    );
    expect(out.feat_body_finish).toBe("glossy");
    expect(out.feat_head_finish).toBe("glossy");
    expect(out.feat_body_hex).toBe("112233");
    expect(out.feat_head_hex).toBe("112233");
  });
});
