// @vitest-environment jsdom
/**
 * Mouth extra & tail extra — frontend conditional disabling tests.
 *
 * Spec requirement covered:
 *   MTE-10: Frontend — Conditional Disabling Logic
 *
 * Tests verify observable DOM behavior: the `mouth_shape` control row is
 * rendered with opacity 0.42 and pointer-events "none" when `mouth_enabled`
 * is absent or falsy, similarly for `tail_shape` and `tail_length` with `tail_enabled`.
 *
 * These tests will be RED until the implementation extends `buildControlDisabled`
 * in BuildControls.tsx to include the mouth/tail disabling rules.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { BuildControls } from "./BuildControls";
import type { AnimatedBuildControlDef } from "../../types";

afterEach(() => {
  cleanup();
});

// ---------------------------------------------------------------------------
// Minimal control sets covering mouth and tail controls
// ---------------------------------------------------------------------------

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

const TAIL_ENABLED_DEF: AnimatedBuildControlDef = {
  key: "tail_enabled",
  label: "Tail",
  type: "bool",
  default: false,
};

const TAIL_SHAPE_DEF: AnimatedBuildControlDef = {
  key: "tail_shape",
  label: "Tail shape",
  type: "select_str",
  options: ["spike", "whip", "club", "segmented", "curled"],
  default: "spike",
};

const TAIL_LENGTH_DEF: AnimatedBuildControlDef = {
  key: "tail_length",
  label: "Tail length",
  type: "float",
  min: 0.5,
  max: 3.0,
  step: 0.05,
  default: 1.0,
};

const MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL: AnimatedBuildControlDef[] = [
  MOUTH_ENABLED_DEF,
  MOUTH_SHAPE_DEF,
  TAIL_ENABLED_DEF,
  TAIL_SHAPE_DEF,
  TAIL_LENGTH_DEF,
];

// ---------------------------------------------------------------------------
// Helpers (same pattern as BuildControls.eyeShape.test.tsx)
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
 * Returns the wrapping div for a specific control row identified by its label text.
 * The `BuildControls` nonFloat block renders:
 *   <div style={{ opacity: dis ? 0.42 : 1, pointerEvents: dis ? "none" : undefined }}>
 *     <ControlRow def={...} ... />
 *   </div>
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
  return wrapper.style.opacity === "0.42" || wrapper.style.pointerEvents === "none";
}

// ---------------------------------------------------------------------------
// MTE-10-AC-1, MTE-10-AC-3: mouth_shape disabled when mouth_enabled is false/absent
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — mouth_shape disabled when mouth_enabled is false", () => {
  beforeEach(() => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });
  });

  it("MTE-10-AC-1: mouth_shape row is disabled (opacity 0.42) when mouth_enabled is false", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(true);
  });

  it("MTE-10-AC-3: mouth_shape row is disabled when mouth_enabled is absent", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
      // mouth_enabled intentionally absent
    });
    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// MTE-10-AC-2: mouth_shape enabled when mouth_enabled is true
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — mouth_shape enabled when mouth_enabled is true", () => {
  beforeEach(() => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: true,
      mouth_shape: "fang",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });
  });

  it("MTE-10-AC-2: mouth_shape row is NOT disabled when mouth_enabled is true", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// MTE-10-AC-4: mouth_enabled toggle itself is never disabled
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — mouth_enabled toggle is never disabled", () => {
  it("mouth_enabled row is not disabled when mouth_enabled is false", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });
    render(<BuildControls />);
    expect(isRowDisabled("Mouth")).toBe(false);
  });

  it("mouth_enabled row is not disabled when mouth_enabled is true", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: true,
      mouth_shape: "fang",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });
    render(<BuildControls />);
    expect(isRowDisabled("Mouth")).toBe(false);
  });

  it("mouth_enabled row is not disabled for spider either", () => {
    setupStore("spider", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });
    render(<BuildControls />);
    expect(isRowDisabled("Mouth")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// MTE-10-AC-5, MTE-10-AC-9: tail_shape disabled when tail_enabled is false/absent
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — tail_shape disabled when tail_enabled is false", () => {
  beforeEach(() => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });
  });

  it("MTE-10-AC-5: tail_shape row is disabled (opacity 0.42) when tail_enabled is false", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Tail shape")).toBe(true);
  });

  it("MTE-10-AC-9: tail_shape row is disabled when tail_enabled is absent", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_shape: "spike",
      tail_length: 1.0,
      // tail_enabled intentionally absent
    });
    render(<BuildControls />);
    expect(isRowDisabled("Tail shape")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// MTE-10-AC-6, MTE-10-AC-8: tail_shape and tail_length enabled when tail_enabled is true
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — tail controls enabled when tail_enabled is true", () => {
  beforeEach(() => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: true,
      tail_shape: "curled",
      tail_length: 2.0,
    });
  });

  it("MTE-10-AC-6: tail_shape row is NOT disabled when tail_enabled is true", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Tail shape")).toBe(false);
  });

  it("MTE-10-AC-8: tail_length row is NOT disabled when tail_enabled is true", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Tail length")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// MTE-10-AC-7, MTE-10-AC-10: tail_length disabled when tail_enabled is false/absent
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — tail_length disabled when tail_enabled is false", () => {
  beforeEach(() => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });
  });

  it("MTE-10-AC-7: tail_length row is disabled (opacity 0.42) when tail_enabled is false", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Tail length")).toBe(true);
  });

  it("MTE-10-AC-10: tail_length row is disabled when tail_enabled is absent", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_shape: "spike",
      tail_length: 1.0,
      // tail_enabled intentionally absent
    });
    render(<BuildControls />);
    expect(isRowDisabled("Tail length")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// MTE-10-AC-11, MTE-10-AC-12: no bleed-over between mouth and tail controls
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — no cross-disable bleed-over", () => {
  it("MTE-10-AC-11: mouth_shape is NOT disabled when tail_enabled is false", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: true,
      mouth_shape: "fang",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });
    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(false);
  });

  it("MTE-10-AC-12: tail_shape is NOT disabled when mouth_enabled is false", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: true,
      tail_shape: "whip",
      tail_length: 1.5,
    });
    render(<BuildControls />);
    expect(isRowDisabled("Tail shape")).toBe(false);
  });

  it("mouth_enabled does not affect tail controls", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: true,
      tail_shape: "club",
      tail_length: 2.0,
    });
    render(<BuildControls />);
    expect(isRowDisabled("Tail shape")).toBe(false);
    expect(isRowDisabled("Tail length")).toBe(false);
  });

  it("tail_enabled does not affect mouth controls", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: true,
      mouth_shape: "beak",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });
    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// MTE-10-AC-16: visual disabled state in DOM
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — visual disabled state in DOM", () => {
  it("tail_length row has opacity 0.42 when tail_enabled=false", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });
    render(<BuildControls />);
    const wrapper = getControlRowWrapper("Tail length");
    expect(wrapper).toBeTruthy();
    if (wrapper) {
      expect(wrapper.style.opacity).toBe("0.42");
      expect(wrapper.style.pointerEvents).toBe("none");
    }
  });

  it("tail_shape row has opacity 0.42 when tail_enabled=false", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });
    render(<BuildControls />);
    const wrapper = getControlRowWrapper("Tail shape");
    expect(wrapper).toBeTruthy();
    if (wrapper) {
      expect(wrapper.style.opacity).toBe("0.42");
      expect(wrapper.style.pointerEvents).toBe("none");
    }
  });

  it("mouth_shape row has opacity 0.42 when mouth_enabled=false", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });
    render(<BuildControls />);
    const wrapper = getControlRowWrapper("Mouth shape");
    expect(wrapper).toBeTruthy();
    if (wrapper) {
      expect(wrapper.style.opacity).toBe("0.42");
      expect(wrapper.style.pointerEvents).toBe("none");
    }
  });

  it("mouth_shape row has opacity 1 when mouth_enabled=true", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: true,
      mouth_shape: "fang",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });
    render(<BuildControls />);
    const wrapper = getControlRowWrapper("Mouth shape");
    expect(wrapper).toBeTruthy();
    if (wrapper) {
      // When enabled, opacity should not be 0.42
      expect(wrapper.style.opacity).not.toBe("0.42");
    }
  });
});

// ---------------------------------------------------------------------------
// MTE-10: mouth_shape renders correct options when enabled
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — control option rendering", () => {
  it("mouth_shape select renders smile, grimace, flat, fang, beak options when enabled", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: true,
      mouth_shape: "fang",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });
    render(<BuildControls />);
    const select = screen.queryByLabelText("Mouth shape") as HTMLSelectElement | null;
    if (select) {
      const optionValues = Array.from(select.options).map((o) => o.value);
      expect(optionValues).toContain("smile");
      expect(optionValues).toContain("grimace");
      expect(optionValues).toContain("flat");
      expect(optionValues).toContain("fang");
      expect(optionValues).toContain("beak");
    }
    expect(screen.getByText("Mouth shape")).toBeInTheDocument();
  });

  it("tail_shape select renders spike, whip, club, segmented, curled options when enabled", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: true,
      tail_shape: "curled",
      tail_length: 1.0,
    });
    render(<BuildControls />);
    const select = screen.queryByLabelText("Tail shape") as HTMLSelectElement | null;
    if (select) {
      const optionValues = Array.from(select.options).map((o) => o.value);
      expect(optionValues).toContain("spike");
      expect(optionValues).toContain("whip");
      expect(optionValues).toContain("club");
      expect(optionValues).toContain("segmented");
      expect(optionValues).toContain("curled");
    }
    expect(screen.getByText("Tail shape")).toBeInTheDocument();
  });

  it("tail_length input renders with correct min/max/step when enabled", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS_WITH_MOUTH_TAIL, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: true,
      tail_shape: "spike",
      tail_length: 1.5,
    });
    render(<BuildControls />);
    const input = screen.queryByLabelText("Tail length") as HTMLInputElement | null;
    if (input) {
      expect(input.min).toBe("0.5");
      expect(input.max).toBe("3"); // JS renders 3.0 as "3" in HTML attribute
      expect(input.step).toBe("0.05");
      expect(input.value).toBe("1.5");
    }
    expect(screen.getByText("Tail length")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Regression: existing pupil_shape disabling not broken
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — existing pupil_shape logic not broken", () => {
  const EYE_SHAPE_DEF = {
    key: "eye_shape" as const,
    label: "Eye shape",
    type: "select_str" as const,
    options: ["circle", "oval", "slit", "square"],
    default: "circle",
  };

  const PUPIL_ENABLED_DEF = {
    key: "pupil_enabled" as const,
    label: "Pupil",
    type: "bool" as const,
    default: false,
  };

  const PUPIL_SHAPE_DEF = {
    key: "pupil_shape" as const,
    label: "Pupil shape",
    type: "select_str" as const,
    options: ["dot", "slit", "diamond"],
    default: "dot",
  };

  const MINIMAL_CONTROLS_WITH_PUPIL: AnimatedBuildControlDef[] = [
    EYE_SHAPE_DEF,
    PUPIL_ENABLED_DEF,
    PUPIL_SHAPE_DEF,
    MOUTH_ENABLED_DEF,
    MOUTH_SHAPE_DEF,
    TAIL_ENABLED_DEF,
    TAIL_SHAPE_DEF,
    TAIL_LENGTH_DEF,
  ];

  it("pupil_shape row is still disabled when pupil_enabled=false", () => {
    setupStore("slug", MINIMAL_CONTROLS_WITH_PUPIL, {
      eye_shape: "circle",
      pupil_enabled: false,
      pupil_shape: "dot",
      mouth_enabled: true,
      mouth_shape: "fang",
      tail_enabled: true,
      tail_shape: "curled",
      tail_length: 2.0,
    });
    render(<BuildControls />);
    expect(isRowDisabled("Pupil shape")).toBe(true);
  });

  it("pupil_shape row is still enabled when pupil_enabled=true", () => {
    setupStore("slug", MINIMAL_CONTROLS_WITH_PUPIL, {
      eye_shape: "circle",
      pupil_enabled: true,
      pupil_shape: "slit",
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });
    render(<BuildControls />);
    expect(isRowDisabled("Pupil shape")).toBe(false);
  });

  it("all three toggles (pupil, mouth, tail) can coexist without interference", () => {
    setupStore("slug", MINIMAL_CONTROLS_WITH_PUPIL, {
      eye_shape: "circle",
      pupil_enabled: true,
      pupil_shape: "slit",
      mouth_enabled: true,
      mouth_shape: "fang",
      tail_enabled: true,
      tail_shape: "curled",
      tail_length: 2.0,
    });
    render(<BuildControls />);
    expect(isRowDisabled("Pupil shape")).toBe(false);
    expect(isRowDisabled("Mouth shape")).toBe(false);
    expect(isRowDisabled("Tail shape")).toBe(false);
    expect(isRowDisabled("Tail length")).toBe(false);
  });
});
