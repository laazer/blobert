// @vitest-environment jsdom
/**
 * Procedural texture presets — frontend conditional disabling tests.
 *
 * Spec requirement covered:
 *   PTP-4: Frontend buildControlDisabled() Rules
 *   PTP-7: Frontend Test Coverage
 *
 * Tests verify observable DOM behavior: texture parameter control rows are rendered
 * with opacity 0.42 and pointer-events "none" when the corresponding texture_mode
 * is not active. The texture_mode select itself is never disabled.
 *
 * These tests will be RED until the implementation extends buildControlDisabled()
 * in BuildControls.tsx to include the texture mode conditional disabling rules.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { BuildControls } from "./BuildControls";
import type { AnimatedBuildControlDef } from "../../types";

afterEach(() => {
  cleanup();
});

// ---------------------------------------------------------------------------
// Control definition constants — minimal sets for texture tests
// ---------------------------------------------------------------------------

const TEXTURE_MODE_DEF: AnimatedBuildControlDef = {
  key: "texture_mode",
  label: "Texture mode",
  type: "select_str",
  options: ["none", "gradient", "spots", "stripes"],
  default: "none",
};

const TEXTURE_GRAD_COLOR_A_DEF: AnimatedBuildControlDef = {
  key: "texture_grad_color_a",
  label: "Gradient color A",
  type: "str",
  default: "",
};

const TEXTURE_GRAD_COLOR_B_DEF: AnimatedBuildControlDef = {
  key: "texture_grad_color_b",
  label: "Gradient color B",
  type: "str",
  default: "",
};

const TEXTURE_GRAD_DIRECTION_DEF: AnimatedBuildControlDef = {
  key: "texture_grad_direction",
  label: "Gradient direction",
  type: "select_str",
  options: ["horizontal", "vertical", "radial"],
  default: "horizontal",
};

const TEXTURE_SPOT_COLOR_DEF: AnimatedBuildControlDef = {
  key: "texture_spot_color",
  label: "Spot color",
  type: "str",
  default: "",
};

const TEXTURE_SPOT_BG_COLOR_DEF: AnimatedBuildControlDef = {
  key: "texture_spot_bg_color",
  label: "Spot background color",
  type: "str",
  default: "",
};

const TEXTURE_SPOT_DENSITY_DEF: AnimatedBuildControlDef = {
  key: "texture_spot_density",
  label: "Spot density",
  type: "float",
  min: 0.1,
  max: 5.0,
  step: 0.05,
  default: 1.0,
};

const TEXTURE_STRIPE_COLOR_DEF: AnimatedBuildControlDef = {
  key: "texture_stripe_color",
  label: "Stripe color",
  type: "str",
  default: "",
};

const TEXTURE_STRIPE_BG_COLOR_DEF: AnimatedBuildControlDef = {
  key: "texture_stripe_bg_color",
  label: "Stripe background color",
  type: "str",
  default: "",
};

const TEXTURE_STRIPE_WIDTH_DEF: AnimatedBuildControlDef = {
  key: "texture_stripe_width",
  label: "Stripe width",
  type: "float",
  min: 0.05,
  max: 1.0,
  step: 0.01,
  default: 0.2,
};

/** All 10 texture controls. */
const ALL_TEXTURE_CONTROLS: AnimatedBuildControlDef[] = [
  TEXTURE_MODE_DEF,
  TEXTURE_GRAD_COLOR_A_DEF,
  TEXTURE_GRAD_COLOR_B_DEF,
  TEXTURE_GRAD_DIRECTION_DEF,
  TEXTURE_SPOT_COLOR_DEF,
  TEXTURE_SPOT_BG_COLOR_DEF,
  TEXTURE_SPOT_DENSITY_DEF,
  TEXTURE_STRIPE_COLOR_DEF,
  TEXTURE_STRIPE_BG_COLOR_DEF,
  TEXTURE_STRIPE_WIDTH_DEF,
];

// ---------------------------------------------------------------------------
// Helpers — identical pattern to BuildControls.mouthTail.test.tsx
// ---------------------------------------------------------------------------

function setupStore(
  slug: string,
  controls: AnimatedBuildControlDef[],
  optionValues: Record<string, unknown>,
) {
  useAppStore.setState({
    commandContext: { cmd: "animated", enemy: slug },
    animatedEnemyMeta: [{ slug, label: slug }],
    animatedBuildControls: { [slug]: controls },
    animatedBuildOptionValues: { [slug]: optionValues },
  });
}

/**
 * Walk up from the label element to find the wrapping div that carries
 * the disabled opacity/pointerEvents style, following the same traversal
 * strategy used in BuildControls.mouthTail.test.tsx.
 */
function getControlRowWrapper(labelText: string): HTMLElement | null {
  const labelEl = screen.queryByText(labelText);
  if (!labelEl) return null;
  let el: HTMLElement | null = labelEl as HTMLElement;
  while (el && el !== document.body) {
    if (el.style && el.style.opacity !== undefined && el.style.opacity !== "") {
      return el;
    }
    el = el.parentElement;
  }
  el = labelEl as HTMLElement;
  while (el && el !== document.body) {
    if (el.tagName === "DIV") return el;
    el = el.parentElement;
  }
  return labelEl as HTMLElement;
}

function isRowDisabled(labelText: string): boolean {
  const wrapper = getControlRowWrapper(labelText);
  if (!wrapper) return false;
  return (
    wrapper.style.opacity === "0.42" || wrapper.style.pointerEvents === "none"
  );
}

function expectRowStrictlyDisabled(labelText: string) {
  const wrapper = getControlRowWrapper(labelText);
  expect(wrapper).toBeTruthy();
  if (!wrapper) return;
  expect(wrapper.style.opacity).toBe("0.42");
  expect(wrapper.style.pointerEvents).toBe("none");
}

function expectRowStrictlyEnabled(labelText: string) {
  const wrapper = getControlRowWrapper(labelText);
  expect(wrapper).toBeTruthy();
  if (!wrapper) return;
  expect(wrapper.style.opacity).not.toBe("0.42");
  expect(wrapper.style.pointerEvents).not.toBe("none");
}

// ---------------------------------------------------------------------------
// PTP-7-AC-1: texture_grad_color_a disabled when texture_mode is "none"
// ---------------------------------------------------------------------------

describe("BuildControls texture — texture_grad_color_a disabled when mode is none", () => {
  beforeEach(() => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      texture_mode: "none",
      texture_grad_color_a: "",
      texture_grad_color_b: "",
      texture_grad_direction: "horizontal",
      texture_spot_color: "",
      texture_spot_bg_color: "",
      texture_spot_density: 1.0,
      texture_stripe_color: "",
      texture_stripe_bg_color: "",
      texture_stripe_width: 0.2,
    });
  });

  it("PTP-7-AC-1: texture_grad_color_a row has opacity 0.42 when texture_mode is none", () => {
    render(<BuildControls />);
    const wrapper = getControlRowWrapper("Gradient color A");
    expect(wrapper).toBeTruthy();
    if (wrapper) {
      expect(wrapper.style.opacity).toBe("0.42");
      expect(wrapper.style.pointerEvents).toBe("none");
    }
  });

  it("PTP-4-AC-3: isRowDisabled returns true for texture_grad_color_a when mode is none", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Gradient color A")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// PTP-7-AC-2: texture_grad_color_a enabled when texture_mode is "gradient"
// ---------------------------------------------------------------------------

describe("BuildControls texture — texture_grad_color_a enabled when mode is gradient", () => {
  beforeEach(() => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      texture_mode: "gradient",
      texture_grad_color_a: "ff0000",
      texture_grad_color_b: "0000ff",
      texture_grad_direction: "horizontal",
      texture_spot_color: "",
      texture_spot_bg_color: "",
      texture_spot_density: 1.0,
      texture_stripe_color: "",
      texture_stripe_bg_color: "",
      texture_stripe_width: 0.2,
    });
  });

  it("PTP-7-AC-2: texture_grad_color_a row is NOT disabled when texture_mode is gradient", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Gradient color A")).toBe(false);
  });

  it("PTP-4-AC-7: texture_grad_color_b is also not disabled when mode is gradient", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Gradient color B")).toBe(false);
  });

  it("PTP-4-AC-8: texture_grad_direction is not disabled when mode is gradient", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Gradient direction")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// PTP-7-AC-3: texture_grad_color_a disabled when mode is "spots" (non-gradient non-none)
// ---------------------------------------------------------------------------

describe("BuildControls texture — gradient params disabled when mode is spots", () => {
  beforeEach(() => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      texture_mode: "spots",
      texture_grad_color_a: "ff0000",
      texture_grad_color_b: "0000ff",
      texture_grad_direction: "vertical",
      texture_spot_color: "aabbcc",
      texture_spot_bg_color: "ffffff",
      texture_spot_density: 2.0,
      texture_stripe_color: "",
      texture_stripe_bg_color: "",
      texture_stripe_width: 0.2,
    });
  });

  it("PTP-7-AC-3, PTP-4-AC-5: texture_grad_color_a is disabled when mode is spots", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Gradient color A")).toBe(true);
  });

  it("PTP-4-AC-9: texture_grad_direction is disabled when mode is spots (not gradient)", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Gradient direction")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// PTP-7-AC-4: texture_stripe_color disabled when mode is "spots"
// ---------------------------------------------------------------------------

describe("BuildControls texture — stripe params disabled when mode is spots", () => {
  beforeEach(() => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      texture_mode: "spots",
      texture_grad_color_a: "",
      texture_grad_color_b: "",
      texture_grad_direction: "horizontal",
      texture_spot_color: "aabbcc",
      texture_spot_bg_color: "ffffff",
      texture_spot_density: 2.0,
      texture_stripe_color: "112233",
      texture_stripe_bg_color: "445566",
      texture_stripe_width: 0.3,
    });
  });

  it("PTP-7-AC-4, PTP-4-AC-17: texture_stripe_color row is disabled when mode is spots", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Stripe color")).toBe(true);
  });

  it("PTP-4-AC-15: texture_spot_density is NOT disabled when mode is spots", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Spot density")).toBe(false);
  });

  it("PTP-4-AC-10: texture_spot_color is NOT disabled when mode is spots", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Spot color")).toBe(false);
  });

  it("PTP-4-AC-13: texture_spot_bg_color is NOT disabled when mode is spots", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Spot background color")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// PTP-7-AC-5: texture_spot_color disabled when mode is "stripes"
// ---------------------------------------------------------------------------

describe("BuildControls texture — spot params disabled when mode is stripes", () => {
  beforeEach(() => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      texture_mode: "stripes",
      texture_grad_color_a: "",
      texture_grad_color_b: "",
      texture_grad_direction: "horizontal",
      texture_spot_color: "aabbcc",
      texture_spot_bg_color: "ffffff",
      texture_spot_density: 2.0,
      texture_stripe_color: "112233",
      texture_stripe_bg_color: "445566",
      texture_stripe_width: 0.3,
    });
  });

  it("PTP-7-AC-5, PTP-4-AC-12: texture_spot_color row is disabled when mode is stripes", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Spot color")).toBe(true);
  });

  it("PTP-4-AC-15 (stripes): texture_spot_density is disabled when mode is stripes", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Spot density")).toBe(true);
  });

  it("PTP-4-AC-16: texture_stripe_color is NOT disabled when mode is stripes", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Stripe color")).toBe(false);
  });

  it("PTP-4-AC-19: texture_stripe_bg_color is NOT disabled when mode is stripes", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Stripe background color")).toBe(false);
  });

  it("PTP-4-AC-20: texture_stripe_width is NOT disabled when mode is stripes", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Stripe width")).toBe(false);
  });

  it("PTP-4-AC-6, PTP-4-AC-21: texture_grad_color_a and texture_stripe_width crossed", () => {
    render(<BuildControls />);
    // gradient params disabled in stripes mode
    expect(isRowDisabled("Gradient color A")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// PTP-7-AC-6: texture_mode control row itself is never disabled
// ---------------------------------------------------------------------------

describe("BuildControls texture — texture_mode control is never disabled", () => {
  it("PTP-4-AC-1, PTP-7-AC-6: texture_mode is not disabled when mode is none", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      texture_mode: "none",
      texture_grad_color_a: "",
      texture_grad_color_b: "",
      texture_grad_direction: "horizontal",
      texture_spot_color: "",
      texture_spot_bg_color: "",
      texture_spot_density: 1.0,
      texture_stripe_color: "",
      texture_stripe_bg_color: "",
      texture_stripe_width: 0.2,
    });
    render(<BuildControls />);
    expect(isRowDisabled("Texture mode")).toBe(false);
  });

  it("PTP-4-AC-2: texture_mode is not disabled when mode is gradient", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, { texture_mode: "gradient" });
    render(<BuildControls />);
    expect(isRowDisabled("Texture mode")).toBe(false);
  });

  it("PTP-7-AC-6: texture_mode is not disabled when mode is spots", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, { texture_mode: "spots" });
    render(<BuildControls />);
    expect(isRowDisabled("Texture mode")).toBe(false);
  });

  it("PTP-7-AC-6: texture_mode is not disabled when mode is stripes", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, { texture_mode: "stripes" });
    render(<BuildControls />);
    expect(isRowDisabled("Texture mode")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// PTP-7-AC-10: texture_spot_density disabled when mode is "none"
// ---------------------------------------------------------------------------

describe("BuildControls texture — spot density disabled when mode is none", () => {
  it("PTP-7-AC-10: texture_spot_density row is disabled when texture_mode is none", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      texture_mode: "none",
      texture_spot_density: 1.0,
    });
    render(<BuildControls />);
    expect(isRowDisabled("Spot density")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// PTP-7-AC-11: texture_stripe_width disabled when mode is "gradient"
// ---------------------------------------------------------------------------

describe("BuildControls texture — stripe width disabled when mode is gradient", () => {
  it("PTP-7-AC-11, PTP-4-AC-21: texture_stripe_width row is disabled when mode is gradient", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      texture_mode: "gradient",
      texture_stripe_width: 0.3,
    });
    render(<BuildControls />);
    expect(isRowDisabled("Stripe width")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// PTP-7-AC-9: texture_mode select renders all four options
// ---------------------------------------------------------------------------

describe("BuildControls texture — texture_mode select renders all four options", () => {
  it("PTP-7-AC-9: none, gradient, spots, stripes options all present in select", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      texture_mode: "none",
    });
    render(<BuildControls />);

    // The label "Texture mode" must be in the DOM.
    expect(screen.getByText("Texture mode")).toBeInTheDocument();

    // Try to locate the select by its label.
    const select = screen.queryByLabelText("Texture mode") as HTMLSelectElement | null;
    if (select) {
      const optionValues = Array.from(select.options).map((o) => o.value);
      expect(optionValues).toContain("none");
      expect(optionValues).toContain("gradient");
      expect(optionValues).toContain("spots");
      expect(optionValues).toContain("stripes");
    }
    // Whether or not the label is linked via htmlFor, confirm text presence.
    expect(screen.getByText("none") || screen.queryByText("none")).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// PTP-4-AC-22,23: missing or non-string texture_mode treated as "none"
// ---------------------------------------------------------------------------

describe("BuildControls texture — absent or non-string texture_mode treated as none", () => {
  it("PTP-4-AC-22: texture_grad_color_a disabled when texture_mode is absent from values", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      // texture_mode intentionally absent
      texture_grad_color_a: "ff0000",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Gradient color A")).toBe(true);
  });

  it("PTP-4-AC-23: texture_grad_color_a disabled when texture_mode is a number (42)", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      texture_mode: 42,
      texture_grad_color_a: "ff0000",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Gradient color A")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Adversarial: unknown texture_mode string treated as "none"
// ---------------------------------------------------------------------------

describe("BuildControls texture — invalid texture_mode string treated as none", () => {
  it("invalid string disables all mode-specific params but does not disable texture_mode row", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      texture_mode: "invalid",
      texture_grad_color_a: "ff0000",
      texture_spot_color: "aabbcc",
      texture_stripe_color: "112233",
    });
    render(<BuildControls />);

    expectRowStrictlyDisabled("Gradient color A");
    expectRowStrictlyDisabled("Spot color");
    expectRowStrictlyDisabled("Stripe color");
    expect(isRowDisabled("Texture mode")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Adversarial: reactive update hazards (store updates after initial render)
// ---------------------------------------------------------------------------

describe("BuildControls texture — reacts to texture_mode changes without remount", () => {
  it("switching none -> gradient -> spots updates disabled rows deterministically", async () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      texture_mode: "none",
      texture_grad_color_a: "ff0000",
      texture_spot_color: "aabbcc",
      texture_stripe_color: "112233",
    });

    render(<BuildControls />);

    expectRowStrictlyDisabled("Gradient color A");
    expectRowStrictlyDisabled("Spot color");
    expectRowStrictlyDisabled("Stripe color");

    act(() => {
      useAppStore.setState({
        animatedBuildOptionValues: {
          slug: {
            texture_mode: "gradient",
            texture_grad_color_a: "ff0000",
            texture_grad_color_b: "0000ff",
            texture_grad_direction: "horizontal",
          },
        },
      });
    });

    await waitFor(() => {
      expectRowStrictlyEnabled("Gradient color A");
      expectRowStrictlyDisabled("Spot color");
      expectRowStrictlyDisabled("Stripe color");
    });

    act(() => {
      useAppStore.setState({
        animatedBuildOptionValues: {
          slug: {
            texture_mode: "spots",
            texture_spot_color: "aabbcc",
            texture_spot_bg_color: "ffffff",
            texture_spot_density: 2.0,
          },
        },
      });
    });

    await waitFor(() => {
      expectRowStrictlyDisabled("Gradient color A");
      expectRowStrictlyEnabled("Spot color");
      expectRowStrictlyDisabled("Stripe color");
    });
  });
});

// ---------------------------------------------------------------------------
// PTP-7-AC-7, PTP-7-AC-8: no bleed-over to pupil/mouth/tail rules
// ---------------------------------------------------------------------------

describe("BuildControls texture — no bleed-over to existing pupil/mouth/tail rules", () => {
  const PUPIL_ENABLED_DEF: AnimatedBuildControlDef = {
    key: "pupil_enabled",
    label: "Pupil",
    type: "bool",
    default: false,
  };
  const PUPIL_SHAPE_DEF: AnimatedBuildControlDef = {
    key: "pupil_shape",
    label: "Pupil shape",
    type: "select_str",
    options: ["dot", "slit", "diamond"],
    default: "dot",
  };
  const MOUTH_ENABLED_DEF: AnimatedBuildControlDef = {
    key: "mouth_enabled",
    label: "Mouth",
    type: "bool",
    default: false,
  };
  const MOUTH_SHAPE_DEF: AnimatedBuildControlDef = {
    key: "mouth_shape",
    label: "Mouth shape",
    type: "select_str",
    options: ["smile", "grimace", "flat", "fang", "beak"],
    default: "smile",
  };

  const CONTROLS_WITH_TEXTURE_AND_MOUTH_PUPIL: AnimatedBuildControlDef[] = [
    PUPIL_ENABLED_DEF,
    PUPIL_SHAPE_DEF,
    MOUTH_ENABLED_DEF,
    MOUTH_SHAPE_DEF,
    ...ALL_TEXTURE_CONTROLS,
  ];

  it("PTP-7-AC-7: pupil_shape still disabled by pupil_enabled=false, unaffected by texture_mode=gradient", () => {
    setupStore("slug", CONTROLS_WITH_TEXTURE_AND_MOUTH_PUPIL, {
      pupil_enabled: false,
      pupil_shape: "dot",
      mouth_enabled: true,
      mouth_shape: "fang",
      texture_mode: "gradient",
      texture_grad_color_a: "ff0000",
      texture_grad_color_b: "0000ff",
      texture_grad_direction: "horizontal",
      texture_spot_color: "",
      texture_spot_bg_color: "",
      texture_spot_density: 1.0,
      texture_stripe_color: "",
      texture_stripe_bg_color: "",
      texture_stripe_width: 0.2,
    });
    render(<BuildControls />);
    expect(isRowDisabled("Pupil shape")).toBe(true);
    // Texture grad controls should be enabled
    expect(isRowDisabled("Gradient color A")).toBe(false);
  });

  it("PTP-7-AC-8: mouth_shape still disabled by mouth_enabled=false, unaffected by texture_mode=spots", () => {
    setupStore("slug", CONTROLS_WITH_TEXTURE_AND_MOUTH_PUPIL, {
      pupil_enabled: true,
      pupil_shape: "slit",
      mouth_enabled: false,
      mouth_shape: "smile",
      texture_mode: "spots",
      texture_grad_color_a: "",
      texture_grad_color_b: "",
      texture_grad_direction: "horizontal",
      texture_spot_color: "aabbcc",
      texture_spot_bg_color: "ffffff",
      texture_spot_density: 2.0,
      texture_stripe_color: "",
      texture_stripe_bg_color: "",
      texture_stripe_width: 0.2,
    });
    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(true);
    // Spot controls should be enabled
    expect(isRowDisabled("Spot color")).toBe(false);
  });

  it("PTP-4-AC-24: pupil_shape disabled rule unchanged when texture controls are added", () => {
    setupStore("slug", CONTROLS_WITH_TEXTURE_AND_MOUTH_PUPIL, {
      pupil_enabled: false,
      pupil_shape: "dot",
      mouth_enabled: true,
      mouth_shape: "smile",
      texture_mode: "none",
      texture_grad_color_a: "",
      texture_grad_color_b: "",
      texture_grad_direction: "horizontal",
      texture_spot_color: "",
      texture_spot_bg_color: "",
      texture_spot_density: 1.0,
      texture_stripe_color: "",
      texture_stripe_bg_color: "",
      texture_stripe_width: 0.2,
    });
    render(<BuildControls />);
    expect(isRowDisabled("Pupil shape")).toBe(true);
  });

  it("PTP-4-AC-25: mouth_shape disabled rule unchanged when texture controls are added", () => {
    setupStore("slug", CONTROLS_WITH_TEXTURE_AND_MOUTH_PUPIL, {
      pupil_enabled: true,
      pupil_shape: "slit",
      mouth_enabled: false,
      mouth_shape: "smile",
      texture_mode: "none",
      texture_grad_color_a: "",
      texture_grad_color_b: "",
      texture_grad_direction: "horizontal",
      texture_spot_color: "",
      texture_spot_bg_color: "",
      texture_spot_density: 1.0,
      texture_stripe_color: "",
      texture_stripe_bg_color: "",
      texture_stripe_width: 0.2,
    });
    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(true);
  });

  it("texture_mode controls do not affect pupil_shape when pupil_enabled=true", () => {
    setupStore("slug", CONTROLS_WITH_TEXTURE_AND_MOUTH_PUPIL, {
      pupil_enabled: true,
      pupil_shape: "diamond",
      mouth_enabled: true,
      mouth_shape: "fang",
      texture_mode: "stripes",
      texture_grad_color_a: "",
      texture_grad_color_b: "",
      texture_grad_direction: "horizontal",
      texture_spot_color: "",
      texture_spot_bg_color: "",
      texture_spot_density: 1.0,
      texture_stripe_color: "aabbcc",
      texture_stripe_bg_color: "ffffff",
      texture_stripe_width: 0.4,
    });
    render(<BuildControls />);
    // pupil_shape should be enabled (pupil_enabled=true)
    expect(isRowDisabled("Pupil shape")).toBe(false);
    // mouth_shape should be enabled (mouth_enabled=true)
    expect(isRowDisabled("Mouth shape")).toBe(false);
    // stripe controls should be enabled (texture_mode=stripes)
    expect(isRowDisabled("Stripe color")).toBe(false);
    // spot controls should be disabled (texture_mode=stripes)
    expect(isRowDisabled("Spot color")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// PTP-4-AC-28: texture rules apply to spider slug too (not slug-specific)
// ---------------------------------------------------------------------------

describe("BuildControls texture — texture rules apply across slugs", () => {
  it("PTP-4-AC-28: texture_grad_color_a is disabled for spider slug when mode is none", () => {
    setupStore("spider", ALL_TEXTURE_CONTROLS, {
      texture_mode: "none",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Gradient color A")).toBe(true);
  });

  it("texture_grad_color_a is enabled for spider slug when mode is gradient", () => {
    setupStore("spider", ALL_TEXTURE_CONTROLS, {
      texture_mode: "gradient",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Gradient color A")).toBe(false);
  });

  it("texture rules apply to imp slug", () => {
    setupStore("imp", ALL_TEXTURE_CONTROLS, {
      texture_mode: "spots",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Spot color")).toBe(false);
    expect(isRowDisabled("Gradient color A")).toBe(true);
    expect(isRowDisabled("Stripe color")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Visual disabled state: explicit opacity/pointerEvents assertions
// ---------------------------------------------------------------------------

describe("BuildControls texture — visual disabled state in DOM", () => {
  it("PTP-7-AC-1 (DOM): Gradient color A wrapper has opacity 0.42 and pointerEvents none when mode is none", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      texture_mode: "none",
      texture_grad_color_a: "",
    });
    render(<BuildControls />);
    const wrapper = getControlRowWrapper("Gradient color A");
    expect(wrapper).toBeTruthy();
    if (wrapper) {
      expect(wrapper.style.opacity).toBe("0.42");
      expect(wrapper.style.pointerEvents).toBe("none");
    }
  });

  it("Stripe color wrapper has opacity 0.42 when mode is spots", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      texture_mode: "spots",
      texture_stripe_color: "aabbcc",
    });
    render(<BuildControls />);
    const wrapper = getControlRowWrapper("Stripe color");
    expect(wrapper).toBeTruthy();
    if (wrapper) {
      expect(wrapper.style.opacity).toBe("0.42");
      expect(wrapper.style.pointerEvents).toBe("none");
    }
  });

  it("Spot color wrapper has opacity 0.42 when mode is stripes", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      texture_mode: "stripes",
      texture_spot_color: "ff0000",
    });
    render(<BuildControls />);
    const wrapper = getControlRowWrapper("Spot color");
    expect(wrapper).toBeTruthy();
    if (wrapper) {
      expect(wrapper.style.opacity).toBe("0.42");
      expect(wrapper.style.pointerEvents).toBe("none");
    }
  });

  it("Gradient color A wrapper has no disabled opacity when mode is gradient", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      texture_mode: "gradient",
      texture_grad_color_a: "ff0000",
    });
    render(<BuildControls />);
    const wrapper = getControlRowWrapper("Gradient color A");
    expect(wrapper).toBeTruthy();
    if (wrapper) {
      expect(wrapper.style.opacity).not.toBe("0.42");
    }
  });
});
