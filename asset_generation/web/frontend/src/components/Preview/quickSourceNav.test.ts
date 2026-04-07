import { describe, expect, it } from "vitest";
import {
  getAnimationCodeExtras,
  getAnimationCodeTarget,
  getMeshPartTree,
  getModelCodeTarget,
} from "./quickSourceNav";

describe("quickSourceNav", () => {
  describe("getModelCodeTarget", () => {
    it("resolves animated all to registry", () => {
      expect(getModelCodeTarget("animated", "all")?.path).toBe("enemies/animated/registry.py");
    });

    it("resolves known animated slug to module", () => {
      expect(getModelCodeTarget("animated", "slug")?.path).toBe("enemies/animated_slug.py");
    });

    it("falls back to base_enemy for unknown animated slug", () => {
      expect(getModelCodeTarget("animated", "unknown_x")?.path).toBe("enemies/base_enemy.py");
    });

    it("resolves player", () => {
      expect(getModelCodeTarget("player", "blue")?.path).toBe("player/player_slime_body.py");
    });

    it("resolves level", () => {
      expect(getModelCodeTarget("level", "crate")?.path).toBe("level/level_object_builder.py");
    });

    it("resolves test to spider mesh module", () => {
      expect(getModelCodeTarget("test", "")?.path).toBe("enemies/animated_spider.py");
    });

    it("resolves stats with known slug", () => {
      expect(getModelCodeTarget("stats", "imp")?.path).toBe("enemies/animated_imp.py");
    });

    it("returns null for smart", () => {
      expect(getModelCodeTarget("smart", "")).toBeNull();
    });
  });

  describe("getAnimationCodeTarget", () => {
    it("uses player_animations for player", () => {
      expect(getAnimationCodeTarget("player", "blue")?.path).toBe("player/player_animations.py");
    });

    it("uses shared animation_system for animated", () => {
      expect(getAnimationCodeTarget("animated", "slug")?.path).toBe("animations/animation_system.py");
    });

    it("returns null for smart", () => {
      expect(getAnimationCodeTarget("smart", "")).toBeNull();
    });
  });

  describe("getAnimationCodeExtras", () => {
    it("lists shared modules for animated enemies", () => {
      const paths = getAnimationCodeExtras("animated").map((x) => x.path);
      expect(paths).toContain("animations/keyframe_system.py");
      expect(paths).toContain("body_families/registry.py");
      expect(paths).toContain("animations/body_types.py");
      expect(paths).toContain("enemies/animated_slug.py");
    });

    it("lists player extras for player cmd", () => {
      const paths = getAnimationCodeExtras("player").map((x) => x.path);
      expect(paths).toContain("player/player_armature.py");
    });

    it("returns empty for smart", () => {
      expect(getAnimationCodeExtras("smart")).toEqual([]);
    });
  });

  describe("getMeshPartTree", () => {
    it("returns player tree for player cmd", () => {
      const tree = getMeshPartTree("player", "blue");
      expect(tree[0]?.label).toContain("Player");
      expect(tree[0]?.children?.some((c) => c.label.includes("Face"))).toBe(true);
    });

    it("lists all enemies under animated all with display labels", () => {
      const tree = getMeshPartTree("animated", "all");
      const labels = tree[0]?.children?.map((c) => c.label) ?? [];
      expect(labels).toContain("Slug");
      expect(labels).toContain("Spider");
    });

    it("enumerates every slug parts[] index", () => {
      const tree = getMeshPartTree("animated", "slug");
      const flat = JSON.stringify(tree);
      for (let i = 0; i <= 5; i += 1) {
        expect(flat).toContain(`parts[${i}]`);
      }
    });

    it("spider parts tree reflects current eye_count only (not both variants)", () => {
      const t2 = getMeshPartTree("animated", "spider", undefined, { eye_count: 2 });
      const flat2 = JSON.stringify(t2);
      expect(flat2).toContain("10 parts");
      expect(flat2).toContain("parts[9]");
      expect(flat2).not.toContain("parts[10]");

      const t4 = getMeshPartTree("animated", "spider", undefined, { eye_count: 4 });
      const flat4 = JSON.stringify(t4);
      expect(flat4).toContain("12 parts");
      expect(flat4).toContain("parts[11]");
      expect(flat4).not.toContain("Variant:");

      const t6 = getMeshPartTree("animated", "spider", undefined, { eye_count: 6 });
      const flat6 = JSON.stringify(t6);
      expect(flat6).toContain("14 parts");
      expect(flat6).toContain("parts[13]");

      const t8 = getMeshPartTree("animated", "spider", undefined, { eye_count: 8 });
      const flat8 = JSON.stringify(t8);
      expect(flat8).toContain("16 parts");
      expect(flat8).toContain("parts[15]");
    });

    it("claw_crawler parts tree includes peripheral eyes only when selected", () => {
      const t0 = getMeshPartTree("animated", "claw_crawler", undefined, { peripheral_eyes: 0 });
      expect(JSON.stringify(t0)).toContain("8 parts");
      expect(JSON.stringify(t0)).not.toContain("peripheral");

      const t2 = getMeshPartTree("animated", "claw_crawler", undefined, { peripheral_eyes: 2 });
      const s = JSON.stringify(t2);
      expect(s).toContain("10 parts");
      expect(s).toContain("peripheral eye");
    });

    it("lists full player join order through [11]", () => {
      const tree = getMeshPartTree("player", "blue");
      const flat = JSON.stringify(tree);
      for (let i = 0; i <= 11; i += 1) {
        expect(flat).toContain(`[${i}]`);
      }
    });
  });
});
