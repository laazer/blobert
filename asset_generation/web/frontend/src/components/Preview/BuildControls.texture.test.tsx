// @vitest-environment jsdom
/**
 * Procedural texture presets — frontend conditional disabling tests.
 *
 * Spec requirement covered:
 *   PTP-4: Frontend buildControlDisabled() Rules
 *   PTP-7: Frontend Test Coverage
 *
 * Tests verify observable DOM behavior: texture parameter rows for inactive modes are
 * not rendered; only the active mode's color and float parameters appear. The texture_mode
 * select is always shown and is never disabled.
 *
 * These tests will be RED until the implementation extends buildControlDisabled()
 * in BuildControls.tsx to include the texture mode conditional disabling rules.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { BuildControls } from "./BuildControls";
import { TextureControlsSection } from "./TextureControlsSection";
import type { AnimatedBuildControlDef } from "../../types";

afterEach(() => {
  cleanup();
});

// ---------------------------------------------------------------------------
// Control definition constants — minimal sets for texture tests
// ---------------------------------------------------------------------------

const TEXTURE_MODE_DEF: AnimatedBuildControlDef = {
  key: "feat_body_texture_mode",
  label: "Texture mode",
  type: "select_str",
  options: ["none", "gradient", "spots", "stripes"],
  default: "none",
};

const TEXTURE_GRAD_COLOR_A_DEF: AnimatedBuildControlDef = {
  key: "feat_body_texture_grad_color_a",
  label: "Gradient color A",
  type: "str",
  default: "",
};

const TEXTURE_GRAD_COLOR_B_DEF: AnimatedBuildControlDef = {
  key: "feat_body_texture_grad_color_b",
  label: "Gradient color B",
  type: "str",
  default: "",
};

const TEXTURE_GRAD_DIRECTION_DEF: AnimatedBuildControlDef = {
  key: "feat_body_texture_grad_direction",
  label: "Gradient direction",
  type: "select_str",
  options: ["horizontal", "vertical", "radial"],
  default: "horizontal",
};

const TEXTURE_SPOT_COLOR_DEF: AnimatedBuildControlDef = {
  key: "feat_body_texture_spot_color",
  label: "Spot color",
  type: "str",
  default: "",
};

const TEXTURE_SPOT_BG_COLOR_DEF: AnimatedBuildControlDef = {
  key: "feat_body_texture_spot_bg_color",
  label: "Spot background color",
  type: "str",
  default: "",
};

const TEXTURE_SPOT_DENSITY_DEF: AnimatedBuildControlDef = {
  key: "feat_body_texture_spot_density",
  label: "Spot density",
  type: "float",
  min: 0.1,
  max: 5.0,
  step: 0.05,
  default: 1.0,
};

const TEXTURE_STRIPE_COLOR_DEF: AnimatedBuildControlDef = {
  key: "feat_body_texture_stripe_color",
  label: "Stripe color",
  type: "str",
  default: "",
};

const TEXTURE_STRIPE_BG_COLOR_DEF: AnimatedBuildControlDef = {
  key: "feat_body_texture_stripe_bg_color",
  label: "Stripe background color",
  type: "str",
  default: "",
};

const TEXTURE_STRIPE_WIDTH_DEF: AnimatedBuildControlDef = {
  key: "feat_body_texture_stripe_width",
  label: "Stripe width",
  type: "float",
  min: 0.05,
  max: 1.0,
  step: 0.01,
  default: 0.2,
};

const TEXTURE_STRIPE_DIRECTION_DEF: AnimatedBuildControlDef = {
  key: "feat_body_texture_stripe_direction",
  label: "Stripe preset",
  type: "select_str",
  options: ["beachball", "doplar", "swirl"],
  default: "beachball",
  segmented: true,
};

const TEXTURE_STRIPE_ROT_YAW_DEF: AnimatedBuildControlDef = {
  key: "feat_body_texture_stripe_rot_yaw",
  label: "Stripe yaw",
  type: "float",
  min: -360,
  max: 360,
  step: 1,
  default: 0,
  unit: "deg",
};

const TEXTURE_STRIPE_ROT_PITCH_DEF: AnimatedBuildControlDef = {
  key: "feat_body_texture_stripe_rot_pitch",
  label: "Stripe pitch",
  type: "float",
  min: -360,
  max: 360,
  step: 1,
  default: 0,
  unit: "deg",
};

/** Texture mode + pattern controls used by ZoneTextureBlock (subset of full meta). */
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
  TEXTURE_STRIPE_DIRECTION_DEF,
  TEXTURE_STRIPE_ROT_YAW_DEF,
  TEXTURE_STRIPE_ROT_PITCH_DEF,
];

const BODY_FINISH_DEF: AnimatedBuildControlDef = {
  key: "feat_body_finish",
  label: "Body finish",
  type: "select_str",
  options: ["matte", "glossy"],
  default: "matte",
};

const BODY_HEX_DEF: AnimatedBuildControlDef = {
  key: "feat_body_hex",
  label: "Body hex",
  type: "str",
  default: "ffffff",
};

const ALL_TEXTURE_WITH_FINISH_HEX: AnimatedBuildControlDef[] = [...ALL_TEXTURE_CONTROLS, BODY_FINISH_DEF, BODY_HEX_DEF];

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

function expectTextureParamHidden(labelText: string) {
  expect(screen.queryByText(labelText)).not.toBeInTheDocument();
}

function expectTextureParamVisible(labelText: string) {
  expect(screen.getByText(labelText)).toBeInTheDocument();
}

/** Gradient A/B/direction are rendered as one {@link ColorPickerUniversal} (gradient lock mode). */
function expectGradientBundleHidden() {
  expect(screen.queryByText("From Color")).not.toBeInTheDocument();
}

function expectGradientBundleVisible() {
  expect(screen.getByText("From Color")).toBeInTheDocument();
  expect(screen.getByText("To Color")).toBeInTheDocument();
  expect(screen.getByRole("group", { name: "Gradient direction" })).toBeInTheDocument();
}

// ---------------------------------------------------------------------------
// PTP-7-AC-1: feat_body_texture_grad_color_a disabled when texture_mode is "none"
// ---------------------------------------------------------------------------

describe("BuildControls texture — feat_body_texture_grad_color_a disabled when mode is none", () => {
  beforeEach(() => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      feat_body_texture_mode: "none",
      feat_body_texture_grad_color_a: "",
      feat_body_texture_grad_color_b: "",
      feat_body_texture_grad_direction: "horizontal",
      feat_body_texture_spot_color: "",
      feat_body_texture_spot_bg_color: "",
      feat_body_texture_spot_density: 1.0,
      feat_body_texture_stripe_color: "",
      feat_body_texture_stripe_bg_color: "",
      feat_body_texture_stripe_width: 0.2,
    });
  });

  it("PTP-7-AC-1: feat_body_texture_grad_color_a is not rendered when texture_mode is none", () => {
    render(<TextureControlsSection slug="slug" />);
    expectGradientBundleHidden();
  });

  it("PTP-4-AC-3: gradient color row is absent when mode is none", () => {
    render(<TextureControlsSection slug="slug" />);
    expectGradientBundleHidden();
  });
});

// ---------------------------------------------------------------------------
// PTP-7-AC-2: feat_body_texture_grad_color_a enabled when texture_mode is "gradient"
// ---------------------------------------------------------------------------

describe("BuildControls texture — feat_body_texture_grad_color_a enabled when mode is gradient", () => {
  beforeEach(() => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      feat_body_texture_mode: "gradient",
      feat_body_texture_grad_color_a: "ff0000",
      feat_body_texture_grad_color_b: "0000ff",
      feat_body_texture_grad_direction: "horizontal",
      feat_body_texture_spot_color: "",
      feat_body_texture_spot_bg_color: "",
      feat_body_texture_spot_density: 1.0,
      feat_body_texture_stripe_color: "",
      feat_body_texture_stripe_bg_color: "",
      feat_body_texture_stripe_width: 0.2,
    });
  });

  it("PTP-7-AC-2, PTP-4-AC-7, PTP-4-AC-8: gradient bundle visible when texture_mode is gradient", () => {
    render(<TextureControlsSection slug="slug" />);
    expectGradientBundleVisible();
  });
});

// ---------------------------------------------------------------------------
// PTP-7-AC-3: feat_body_texture_grad_color_a disabled when mode is "spots" (non-gradient non-none)
// ---------------------------------------------------------------------------

describe("BuildControls texture — gradient params disabled when mode is spots", () => {
  beforeEach(() => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      feat_body_texture_mode: "spots",
      feat_body_texture_grad_color_a: "ff0000",
      feat_body_texture_grad_color_b: "0000ff",
      feat_body_texture_grad_direction: "vertical",
      feat_body_texture_spot_color: "aabbcc",
      feat_body_texture_spot_bg_color: "ffffff",
      feat_body_texture_spot_density: 2.0,
      feat_body_texture_stripe_color: "",
      feat_body_texture_stripe_bg_color: "",
      feat_body_texture_stripe_width: 0.2,
    });
  });

  it("PTP-7-AC-3, PTP-4-AC-5: feat_body_texture_grad_color_a is not rendered when mode is spots", () => {
    render(<TextureControlsSection slug="slug" />);
    expectGradientBundleHidden();
  });

  it("PTP-4-AC-9: feat_body_texture_grad_direction is not rendered when mode is spots", () => {
    render(<TextureControlsSection slug="slug" />);
    expectGradientBundleHidden();
  });
});

// ---------------------------------------------------------------------------
// PTP-7-AC-4: feat_body_texture_stripe_color disabled when mode is "spots"
// ---------------------------------------------------------------------------

describe("BuildControls texture — stripe params disabled when mode is spots", () => {
  beforeEach(() => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      feat_body_texture_mode: "spots",
      feat_body_texture_grad_color_a: "",
      feat_body_texture_grad_color_b: "",
      feat_body_texture_grad_direction: "horizontal",
      feat_body_texture_spot_color: "aabbcc",
      feat_body_texture_spot_bg_color: "ffffff",
      feat_body_texture_spot_density: 2.0,
      feat_body_texture_stripe_color: "112233",
      feat_body_texture_stripe_bg_color: "445566",
      feat_body_texture_stripe_width: 0.3,
    });
  });

  it("PTP-7-AC-4, PTP-4-AC-17: feat_body_texture_stripe_color is not rendered when mode is spots", () => {
    render(<TextureControlsSection slug="slug" />);
    expectTextureParamHidden("Stripe color");
  });

  it("PTP-4-AC-15: feat_body_texture_spot_density is visible when mode is spots", () => {
    render(<TextureControlsSection slug="slug" />);
    expectTextureParamVisible("Spot density");
  });

  it("PTP-4-AC-10: feat_body_texture_spot_color is visible when mode is spots", () => {
    render(<TextureControlsSection slug="slug" />);
    expectTextureParamVisible("Spot color");
  });

  it("PTP-4-AC-13: feat_body_texture_spot_bg_color is visible when mode is spots", () => {
    render(<TextureControlsSection slug="slug" />);
    expectTextureParamVisible("Spot background color");
  });
});

// ---------------------------------------------------------------------------
// PTP-7-AC-5: feat_body_texture_spot_color disabled when mode is "stripes"
// ---------------------------------------------------------------------------

describe("BuildControls texture — spot params disabled when mode is stripes", () => {
  beforeEach(() => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      feat_body_texture_mode: "stripes",
      feat_body_texture_grad_color_a: "",
      feat_body_texture_grad_color_b: "",
      feat_body_texture_grad_direction: "horizontal",
      feat_body_texture_spot_color: "aabbcc",
      feat_body_texture_spot_bg_color: "ffffff",
      feat_body_texture_spot_density: 2.0,
      feat_body_texture_stripe_color: "112233",
      feat_body_texture_stripe_bg_color: "445566",
      feat_body_texture_stripe_width: 0.3,
    });
  });

  it("PTP-7-AC-5, PTP-4-AC-12: feat_body_texture_spot_color is not rendered when mode is stripes", () => {
    render(<TextureControlsSection slug="slug" />);
    expectTextureParamHidden("Spot color");
  });

  it("PTP-4-AC-15 (stripes): feat_body_texture_spot_density is not rendered when mode is stripes", () => {
    render(<TextureControlsSection slug="slug" />);
    expectTextureParamHidden("Spot density");
  });

  it("PTP-4-AC-16: feat_body_texture_stripe_color is visible when mode is stripes", () => {
    render(<TextureControlsSection slug="slug" />);
    expectTextureParamVisible("Stripe color");
  });

  it("PTP-4-AC-19: feat_body_texture_stripe_bg_color is visible when mode is stripes", () => {
    render(<TextureControlsSection slug="slug" />);
    expectTextureParamVisible("Stripe background color");
  });

  it("PTP-4-AC-20: feat_body_texture_stripe_width is visible when mode is stripes", () => {
    render(<TextureControlsSection slug="slug" />);
    expectTextureParamVisible("Stripe width");
  });

  it("PTP-4-AC-6, PTP-4-AC-21: gradient params not rendered in stripes mode", () => {
    render(<TextureControlsSection slug="slug" />);
    expectGradientBundleHidden();
  });
});

// ---------------------------------------------------------------------------
// PTP-7-AC-6: texture_mode control row itself is never disabled
// ---------------------------------------------------------------------------

describe("BuildControls texture — texture_mode control is never disabled", () => {
  it("PTP-4-AC-1, PTP-7-AC-6: texture_mode is not disabled when mode is none", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      feat_body_texture_mode: "none",
      feat_body_texture_grad_color_a: "",
      feat_body_texture_grad_color_b: "",
      feat_body_texture_grad_direction: "horizontal",
      feat_body_texture_spot_color: "",
      feat_body_texture_spot_bg_color: "",
      feat_body_texture_spot_density: 1.0,
      feat_body_texture_stripe_color: "",
      feat_body_texture_stripe_bg_color: "",
      feat_body_texture_stripe_width: 0.2,
    });
    render(<TextureControlsSection slug="slug" />);
    expect(isRowDisabled("Texture mode")).toBe(false);
  });

  it("PTP-4-AC-2: texture_mode is not disabled when mode is gradient", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, { feat_body_texture_mode: "gradient" });
    render(<TextureControlsSection slug="slug" />);
    expect(isRowDisabled("Texture mode")).toBe(false);
  });

  it("PTP-7-AC-6: texture_mode is not disabled when mode is spots", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, { feat_body_texture_mode: "spots" });
    render(<TextureControlsSection slug="slug" />);
    expect(isRowDisabled("Texture mode")).toBe(false);
  });

  it("PTP-7-AC-6: texture_mode is not disabled when mode is stripes", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, { feat_body_texture_mode: "stripes" });
    render(<TextureControlsSection slug="slug" />);
    expect(isRowDisabled("Texture mode")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// PTP-7-AC-10: feat_body_texture_spot_density disabled when mode is "none"
// ---------------------------------------------------------------------------

describe("BuildControls texture — spot density disabled when mode is none", () => {
  it("PTP-7-AC-10: feat_body_texture_spot_density is not rendered when texture_mode is none", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      feat_body_texture_mode: "none",
      feat_body_texture_spot_density: 1.0,
    });
    render(<TextureControlsSection slug="slug" />);
    expectTextureParamHidden("Spot density");
  });
});

// ---------------------------------------------------------------------------
// PTP-7-AC-11: feat_body_texture_stripe_width disabled when mode is "gradient"
// ---------------------------------------------------------------------------

describe("BuildControls texture — stripe width disabled when mode is gradient", () => {
  it("PTP-7-AC-11, PTP-4-AC-21: feat_body_texture_stripe_width is not rendered when mode is gradient", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      feat_body_texture_mode: "gradient",
      feat_body_texture_stripe_width: 0.3,
    });
    render(<TextureControlsSection slug="slug" />);
    expectTextureParamHidden("Stripe width");
  });
});

// ---------------------------------------------------------------------------
// Base hex: only when texture_mode is none; finish stays visible for pattern modes
// ---------------------------------------------------------------------------

describe("BuildControls texture — base hex vs pattern colors", () => {
  it("shows body finish and body hex when mode is none", () => {
    setupStore("slug", ALL_TEXTURE_WITH_FINISH_HEX, {
      feat_body_texture_mode: "none",
      feat_body_finish: "matte",
      feat_body_hex: "aabbcc",
      feat_body_texture_grad_color_a: "",
      feat_body_texture_grad_color_b: "",
      feat_body_texture_grad_direction: "horizontal",
      feat_body_texture_spot_color: "",
      feat_body_texture_spot_bg_color: "",
      feat_body_texture_spot_density: 1.0,
      feat_body_texture_stripe_color: "",
      feat_body_texture_stripe_bg_color: "",
      feat_body_texture_stripe_width: 0.2,
    });
    render(<TextureControlsSection slug="slug" />);
    expectTextureParamVisible("Body finish");
    expectTextureParamVisible("Body hex");
    expectGradientBundleHidden();
  });

  it("hides body hex when mode is gradient; finish and gradient colors stay", () => {
    setupStore("slug", ALL_TEXTURE_WITH_FINISH_HEX, {
      feat_body_texture_mode: "gradient",
      feat_body_finish: "matte",
      feat_body_hex: "aabbcc",
      feat_body_texture_grad_color_a: "ff0000",
      feat_body_texture_grad_color_b: "0000ff",
      feat_body_texture_grad_direction: "horizontal",
      feat_body_texture_spot_color: "",
      feat_body_texture_spot_bg_color: "",
      feat_body_texture_spot_density: 1.0,
      feat_body_texture_stripe_color: "",
      feat_body_texture_stripe_bg_color: "",
      feat_body_texture_stripe_width: 0.2,
    });
    render(<TextureControlsSection slug="slug" />);
    expectTextureParamVisible("Body finish");
    expectTextureParamHidden("Body hex");
    expectGradientBundleVisible();
  });
});

// ---------------------------------------------------------------------------
// PTP-7-AC-9: texture_mode select renders built-in pattern modes (no client-only custom)
// ---------------------------------------------------------------------------

describe("BuildControls texture — texture_mode select renders pattern modes", () => {
  it("PTP-7-AC-9: none, gradient, spots, stripes options all present; custom not offered in UI", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      feat_body_texture_mode: "none",
    });
    render(<TextureControlsSection slug="slug" />);

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
      expect(optionValues).not.toContain("custom");
    }
    expect(screen.getByRole("combobox", { name: "Texture mode" })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// PTP-4-AC-22,23: missing or non-string texture_mode treated as "none"
// ---------------------------------------------------------------------------

describe("BuildControls texture — absent or non-string texture_mode treated as none", () => {
  it("PTP-4-AC-22: feat_body_texture_grad_color_a not rendered when texture_mode is absent (treated as none)", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      // texture_mode intentionally absent
      feat_body_texture_grad_color_a: "ff0000",
    });
    render(<TextureControlsSection slug="slug" />);
    expectGradientBundleHidden();
  });

  it("PTP-4-AC-23: feat_body_texture_grad_color_a not rendered when texture_mode is invalid type", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      feat_body_texture_mode: 42,
      feat_body_texture_grad_color_a: "ff0000",
    });
    render(<TextureControlsSection slug="slug" />);
    expectGradientBundleHidden();
  });
});

// ---------------------------------------------------------------------------
// Adversarial: unknown texture_mode string treated as "none"
// ---------------------------------------------------------------------------

describe("BuildControls texture — invalid texture_mode string treated as none", () => {
  it("invalid mode treats as none: pattern params hidden; texture_mode row stays enabled", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      feat_body_texture_mode: "invalid",
      feat_body_texture_grad_color_a: "ff0000",
      feat_body_texture_spot_color: "aabbcc",
      feat_body_texture_stripe_color: "112233",
    });
    render(<TextureControlsSection slug="slug" />);

    expectGradientBundleHidden();
    expectTextureParamHidden("Spot color");
    expectTextureParamHidden("Stripe color");
    expect(isRowDisabled("Texture mode")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Adversarial: reactive update hazards (store updates after initial render)
// ---------------------------------------------------------------------------

describe("BuildControls texture — reacts to texture_mode changes without remount", () => {
  it("switching none -> gradient -> spots updates disabled rows deterministically", async () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      feat_body_texture_mode: "none",
      feat_body_texture_grad_color_a: "ff0000",
      feat_body_texture_spot_color: "aabbcc",
      feat_body_texture_stripe_color: "112233",
    });

    render(<TextureControlsSection slug="slug" />);

    expectGradientBundleHidden();
    expectTextureParamHidden("Spot color");
    expectTextureParamHidden("Stripe color");

    act(() => {
      useAppStore.setState({
        animatedBuildOptionValues: {
          slug: {
            feat_body_texture_mode: "gradient",
            feat_body_texture_grad_color_a: "ff0000",
            feat_body_texture_grad_color_b: "0000ff",
            feat_body_texture_grad_direction: "horizontal",
          },
        },
      });
    });

    await waitFor(() => {
      expectGradientBundleVisible();
      expectTextureParamHidden("Spot color");
      expectTextureParamHidden("Stripe color");
    });

    act(() => {
      useAppStore.setState({
        animatedBuildOptionValues: {
          slug: {
            feat_body_texture_mode: "spots",
            feat_body_texture_spot_color: "aabbcc",
            feat_body_texture_spot_bg_color: "ffffff",
            feat_body_texture_spot_density: 2.0,
          },
        },
      });
    });

    await waitFor(() => {
      expectGradientBundleHidden();
      expectTextureParamVisible("Spot color");
      expectTextureParamHidden("Stripe color");
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
      feat_body_texture_mode: "gradient",
      feat_body_texture_grad_color_a: "ff0000",
      feat_body_texture_grad_color_b: "0000ff",
      feat_body_texture_grad_direction: "horizontal",
      feat_body_texture_spot_color: "",
      feat_body_texture_spot_bg_color: "",
      feat_body_texture_spot_density: 1.0,
      feat_body_texture_stripe_color: "",
      feat_body_texture_stripe_bg_color: "",
      feat_body_texture_stripe_width: 0.2,
    });
    const { unmount } = render(<BuildControls />);
    expect(isRowDisabled("Pupil shape")).toBe(true);
    unmount();
    render(<TextureControlsSection slug="slug" />);
    expectGradientBundleVisible();
  });

  it("PTP-7-AC-8: mouth_shape still disabled by mouth_enabled=false, unaffected by texture_mode=spots", () => {
    setupStore("slug", CONTROLS_WITH_TEXTURE_AND_MOUTH_PUPIL, {
      pupil_enabled: true,
      pupil_shape: "slit",
      mouth_enabled: false,
      mouth_shape: "smile",
      feat_body_texture_mode: "spots",
      feat_body_texture_grad_color_a: "",
      feat_body_texture_grad_color_b: "",
      feat_body_texture_grad_direction: "horizontal",
      feat_body_texture_spot_color: "aabbcc",
      feat_body_texture_spot_bg_color: "ffffff",
      feat_body_texture_spot_density: 2.0,
      feat_body_texture_stripe_color: "",
      feat_body_texture_stripe_bg_color: "",
      feat_body_texture_stripe_width: 0.2,
    });
    const { unmount } = render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(true);
    unmount();
    render(<TextureControlsSection slug="slug" />);
    expectTextureParamVisible("Spot color");
  });

  it("PTP-4-AC-24: pupil_shape disabled rule unchanged when texture controls are added", () => {
    setupStore("slug", CONTROLS_WITH_TEXTURE_AND_MOUTH_PUPIL, {
      pupil_enabled: false,
      pupil_shape: "dot",
      mouth_enabled: true,
      mouth_shape: "smile",
      feat_body_texture_mode: "none",
      feat_body_texture_grad_color_a: "",
      feat_body_texture_grad_color_b: "",
      feat_body_texture_grad_direction: "horizontal",
      feat_body_texture_spot_color: "",
      feat_body_texture_spot_bg_color: "",
      feat_body_texture_spot_density: 1.0,
      feat_body_texture_stripe_color: "",
      feat_body_texture_stripe_bg_color: "",
      feat_body_texture_stripe_width: 0.2,
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
      feat_body_texture_mode: "none",
      feat_body_texture_grad_color_a: "",
      feat_body_texture_grad_color_b: "",
      feat_body_texture_grad_direction: "horizontal",
      feat_body_texture_spot_color: "",
      feat_body_texture_spot_bg_color: "",
      feat_body_texture_spot_density: 1.0,
      feat_body_texture_stripe_color: "",
      feat_body_texture_stripe_bg_color: "",
      feat_body_texture_stripe_width: 0.2,
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
      feat_body_texture_mode: "stripes",
      feat_body_texture_grad_color_a: "",
      feat_body_texture_grad_color_b: "",
      feat_body_texture_grad_direction: "horizontal",
      feat_body_texture_spot_color: "",
      feat_body_texture_spot_bg_color: "",
      feat_body_texture_spot_density: 1.0,
      feat_body_texture_stripe_color: "aabbcc",
      feat_body_texture_stripe_bg_color: "ffffff",
      feat_body_texture_stripe_width: 0.4,
    });
    const { unmount } = render(<BuildControls />);
    // pupil_shape should be enabled (pupil_enabled=true)
    expect(isRowDisabled("Pupil shape")).toBe(false);
    // mouth_shape should be enabled (mouth_enabled=true)
    expect(isRowDisabled("Mouth shape")).toBe(false);
    unmount();
    render(<TextureControlsSection slug="slug" />);
    expectTextureParamVisible("Stripe color");
    expectTextureParamHidden("Spot color");
  });
});

// ---------------------------------------------------------------------------
// PTP-4-AC-28: texture rules apply to spider slug too (not slug-specific)
// ---------------------------------------------------------------------------

describe("BuildControls texture — texture rules apply across slugs", () => {
  it("PTP-4-AC-28: feat_body_texture_grad_color_a not rendered for spider slug when mode is none", () => {
    setupStore("spider", ALL_TEXTURE_CONTROLS, {
      feat_body_texture_mode: "none",
    });
    render(<TextureControlsSection slug="spider" />);
    expectGradientBundleHidden();
  });

  it("feat_body_texture_grad_color_a visible for spider slug when mode is gradient", () => {
    setupStore("spider", ALL_TEXTURE_CONTROLS, {
      feat_body_texture_mode: "gradient",
    });
    render(<TextureControlsSection slug="spider" />);
    expectGradientBundleVisible();
  });

  it("texture rules apply to imp slug", () => {
    setupStore("imp", ALL_TEXTURE_CONTROLS, {
      feat_body_texture_mode: "spots",
    });
    render(<TextureControlsSection slug="imp" />);
    expectTextureParamVisible("Spot color");
    expectGradientBundleHidden();
    expectTextureParamHidden("Stripe color");
  });
});

// ---------------------------------------------------------------------------
// Visual: inactive mode params are not in the DOM
// ---------------------------------------------------------------------------

describe("BuildControls texture — inactive mode params not rendered", () => {
  it("PTP-7-AC-1 (DOM): Gradient color A absent when mode is none", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      feat_body_texture_mode: "none",
      feat_body_texture_grad_color_a: "",
    });
    render(<TextureControlsSection slug="slug" />);
    expectGradientBundleHidden();
  });

  it("Stripe color absent when mode is spots", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      feat_body_texture_mode: "spots",
      feat_body_texture_stripe_color: "aabbcc",
    });
    render(<TextureControlsSection slug="slug" />);
    expectTextureParamHidden("Stripe color");
  });

  it("Spot color absent when mode is stripes", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      feat_body_texture_mode: "stripes",
      feat_body_texture_spot_color: "ff0000",
    });
    render(<TextureControlsSection slug="slug" />);
    expectTextureParamHidden("Spot color");
  });

  it("Gradient color A present when mode is gradient", () => {
    setupStore("slug", ALL_TEXTURE_CONTROLS, {
      feat_body_texture_mode: "gradient",
      feat_body_texture_grad_color_a: "ff0000",
    });
    render(<TextureControlsSection slug="slug" />);
    expectGradientBundleVisible();
  });
});
