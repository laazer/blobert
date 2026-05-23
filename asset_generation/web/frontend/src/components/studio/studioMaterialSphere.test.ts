import { describe, it, expect } from "vitest";
import { materialSphereBackground } from "./studioMaterialSphere";

describe("materialSphereBackground", () => {
  it("returns radial shading for solid", () => {
    expect(materialSphereBackground("solid", { color: "#ff0000" })).toContain("radial-gradient");
    expect(materialSphereBackground("solid", { color: "#ff0000" })).toContain("#ff0000");
  });

  it("layers hatch pattern for image without url", () => {
    const bg = materialSphereBackground("image", { accentHue: "#ff6b3d" });
    expect(bg).toContain("repeating-linear-gradient");
    expect(bg).toContain("#ff6b3d");
  });
});
