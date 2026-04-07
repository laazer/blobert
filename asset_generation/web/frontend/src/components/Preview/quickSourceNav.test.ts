import { describe, expect, it } from "vitest";
import {
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
      expect(getModelCodeTarget("animated", "tar_slug")?.path).toBe("enemies/animated_tar_slug.py");
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

    it("resolves test to adhesion bug module", () => {
      expect(getModelCodeTarget("test", "")?.path).toBe("enemies/animated_adhesion_bug.py");
    });

    it("resolves stats with known slug", () => {
      expect(getModelCodeTarget("stats", "ember_imp")?.path).toBe("enemies/animated_ember_imp.py");
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
      expect(getAnimationCodeTarget("animated", "tar_slug")?.path).toBe("animations/animation_system.py");
    });

    it("returns null for smart", () => {
      expect(getAnimationCodeTarget("smart", "")).toBeNull();
    });
  });

  describe("getMeshPartTree", () => {
    it("returns player tree for player cmd", () => {
      const tree = getMeshPartTree("player", "blue");
      expect(tree[0]?.label).toContain("Player");
      expect(tree[0]?.children?.some((c) => c.label.includes("Face"))).toBe(true);
    });

    it("lists all slugs under animated all", () => {
      const tree = getMeshPartTree("animated", "all");
      const labels = tree[0]?.children?.map((c) => c.label) ?? [];
      expect(labels).toContain("tar_slug");
      expect(labels).toContain("adhesion_bug");
    });

    it("enumerates every tar_slug parts[] index", () => {
      const tree = getMeshPartTree("animated", "tar_slug");
      const flat = JSON.stringify(tree);
      for (let i = 0; i <= 5; i += 1) {
        expect(flat).toContain(`parts[${i}]`);
      }
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
