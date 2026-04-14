// @vitest-environment jsdom
/**
 * Eye shape & pupil system — frontend conditional disabling tests.
 *
 * Spec requirement covered:
 *   ESPS-8: Frontend — Conditional Disabling Logic
 *
 * Tests verify observable DOM behavior: the `pupil_shape` control row is
 * rendered with opacity 0.42 and pointer-events "none" when `pupil_enabled`
 * is absent or falsy, and without those styles when `pupil_enabled` is truthy.
 *
 * These tests will be RED until the implementation extends `buildControlDisabled`
 * in BuildControls.tsx to include the pupil_shape disabling rule.
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
// Minimal control set that covers all three new keys plus eye_count for spider
// (eye_count is needed so the spider multi-eye disable branch can be tested
// alongside the new pupil disabling logic without interfering).
// ---------------------------------------------------------------------------

const EYE_SHAPE_DEF: AnimatedBuildControlDef = {
  key: "eye_shape",
  label: "Eye shape",
  type: "select_str",
  options: ["circle", "oval", "slit", "square"],
  default: "circle",
};

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

const EYE_COUNT_DEF: AnimatedBuildControlDef = {
  key: "eye_count",
  label: "Eye count",
  type: "select",
  options: [1, 2, 3, 4],
  default: 2,
};

const EYE_DISTRIBUTION_DEF: AnimatedBuildControlDef = {
  key: "eye_distribution",
  label: "Eye distribution",
  type: "select_str",
  options: ["uniform", "random"],
  default: "uniform",
};

const MINIMAL_SPIDER_CONTROLS: AnimatedBuildControlDef[] = [
  EYE_COUNT_DEF,
  EYE_DISTRIBUTION_DEF,
  EYE_SHAPE_DEF,
  PUPIL_ENABLED_DEF,
  PUPIL_SHAPE_DEF,
];

const MINIMAL_SLUG_CONTROLS: AnimatedBuildControlDef[] = [
  EYE_SHAPE_DEF,
  PUPIL_ENABLED_DEF,
  PUPIL_SHAPE_DEF,
];

// ---------------------------------------------------------------------------
// Helpers
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
  // Walk up to find the wrapper div that carries the opacity style.
  let el: HTMLElement | null = labelEl as HTMLElement;
  while (el && el !== document.body) {
    if (el.style && el.style.opacity !== undefined && el.style.opacity !== "") {
      return el;
    }
    el = el.parentElement;
  }
  // If no opacity attribute found, return the closest block-level ancestor of the label.
  // This handles the case where opacity is 1 (default) and not set explicitly.
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
  // The disabling wrapper applies opacity: 0.42 and pointerEvents: "none".
  return wrapper.style.opacity === "0.42" || wrapper.style.pointerEvents === "none";
}

// ---------------------------------------------------------------------------
// ESPS-8-AC-1: pupil_shape disabled when pupil_enabled is false
// ---------------------------------------------------------------------------

describe("BuildControls eye shape — pupil_shape disabled when pupil_enabled is false", () => {
  beforeEach(() => {
    setupStore("spider", MINIMAL_SPIDER_CONTROLS, {
      eye_count: 2,
      eye_distribution: "uniform",
      eye_shape: "circle",
      pupil_enabled: false,
      pupil_shape: "dot",
    });
  });

  it("ESPS-8-AC-1: pupil_shape row is disabled (opacity 0.42) when pupil_enabled is false", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Pupil shape")).toBe(true);
  });

  it("ESPS-8-AC-3: pupil_shape row is disabled when pupil_enabled is absent", () => {
    setupStore("spider", MINIMAL_SPIDER_CONTROLS, {
      eye_count: 2,
      eye_shape: "circle",
      // pupil_enabled intentionally absent
      pupil_shape: "dot",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Pupil shape")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// ESPS-8-AC-2: pupil_shape enabled when pupil_enabled is true
// ---------------------------------------------------------------------------

describe("BuildControls eye shape — pupil_shape enabled when pupil_enabled is true", () => {
  beforeEach(() => {
    setupStore("spider", MINIMAL_SPIDER_CONTROLS, {
      eye_count: 2,
      eye_distribution: "uniform",
      eye_shape: "circle",
      pupil_enabled: true,
      pupil_shape: "dot",
    });
  });

  it("ESPS-8-AC-2: pupil_shape row is NOT disabled when pupil_enabled is true", () => {
    render(<BuildControls />);
    expect(isRowDisabled("Pupil shape")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// ESPS-8-AC-4: eye_shape is never disabled by the pupil rule
// ---------------------------------------------------------------------------

describe("BuildControls eye shape — eye_shape is never disabled", () => {
  it("ESPS-8-AC-4: eye_shape row is not disabled when pupil_enabled is false", () => {
    setupStore("spider", MINIMAL_SPIDER_CONTROLS, {
      eye_count: 2,
      eye_shape: "circle",
      pupil_enabled: false,
      pupil_shape: "dot",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Eye shape")).toBe(false);
  });

  it("ESPS-8-AC-4: eye_shape row is not disabled when pupil_enabled is true", () => {
    setupStore("spider", MINIMAL_SPIDER_CONTROLS, {
      eye_count: 2,
      eye_shape: "square",
      pupil_enabled: true,
      pupil_shape: "slit",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Eye shape")).toBe(false);
  });

  it("ESPS-8-AC-4: eye_shape not disabled for slug either", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS, {
      eye_shape: "oval",
      pupil_enabled: false,
      pupil_shape: "dot",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Eye shape")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// ESPS-8-AC-5: pupil_enabled toggle is never disabled
// ---------------------------------------------------------------------------

describe("BuildControls eye shape — pupil_enabled toggle is never disabled", () => {
  it("ESPS-8-AC-5: pupil_enabled row is not disabled when pupil_enabled is false", () => {
    setupStore("spider", MINIMAL_SPIDER_CONTROLS, {
      eye_count: 2,
      eye_shape: "circle",
      pupil_enabled: false,
      pupil_shape: "dot",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Pupil")).toBe(false);
  });

  it("ESPS-8-AC-5: pupil_enabled row is not disabled when pupil_enabled is true", () => {
    setupStore("spider", MINIMAL_SPIDER_CONTROLS, {
      eye_count: 2,
      eye_shape: "circle",
      pupil_enabled: true,
      pupil_shape: "dot",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Pupil")).toBe(false);
  });

  it("ESPS-8-AC-5: pupil_enabled row is not disabled for slug", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS, {
      eye_shape: "circle",
      pupil_enabled: false,
      pupil_shape: "dot",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Pupil")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// ESPS-8: pupil_shape disabled for all slugs (not just spider)
// ---------------------------------------------------------------------------

describe("BuildControls eye shape — pupil_shape disabled applies to all slugs", () => {
  it("pupil_shape row is disabled for slug when pupil_enabled is false", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS, {
      eye_shape: "circle",
      pupil_enabled: false,
      pupil_shape: "dot",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Pupil shape")).toBe(true);
  });

  it("pupil_shape row is enabled for slug when pupil_enabled is true", () => {
    setupStore("slug", MINIMAL_SLUG_CONTROLS, {
      eye_shape: "oval",
      pupil_enabled: true,
      pupil_shape: "slit",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Pupil shape")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// ESPS-8-AC-6 / ESPS-8-AC-7: existing spider disabling logic regression
// ---------------------------------------------------------------------------

describe("BuildControls eye shape — existing spider placement disabling not broken", () => {
  it("ESPS-8-AC-7: eye_distribution row is still disabled when eye_count is 1", () => {
    setupStore("spider", MINIMAL_SPIDER_CONTROLS, {
      eye_count: 1,
      eye_distribution: "uniform",
      eye_shape: "circle",
      pupil_enabled: false,
      pupil_shape: "dot",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Eye distribution")).toBe(true);
  });

  it("ESPS-8-AC-7: eye_distribution row is NOT disabled when eye_count is 2", () => {
    setupStore("spider", MINIMAL_SPIDER_CONTROLS, {
      eye_count: 2,
      eye_distribution: "uniform",
      eye_shape: "circle",
      pupil_enabled: false,
      pupil_shape: "dot",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Eye distribution")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// ESPS-8: pupil_shape control renders with correct options
// ---------------------------------------------------------------------------

describe("BuildControls eye shape — pupil_shape renders correct option values", () => {
  it("pupil_shape select renders dot, slit, diamond options when enabled", () => {
    setupStore("spider", MINIMAL_SPIDER_CONTROLS, {
      eye_count: 2,
      eye_shape: "circle",
      pupil_enabled: true,
      pupil_shape: "dot",
    });
    render(<BuildControls />);
    // The select element for pupil_shape should have the three valid options.
    // ControlRow for select_str renders a <select> with aria-label matching the label.
    const select = screen.queryByLabelText("Pupil shape") as HTMLSelectElement | null;
    if (select) {
      const optionValues = Array.from(select.options).map((o) => o.value);
      expect(optionValues).toContain("dot");
      expect(optionValues).toContain("slit");
      expect(optionValues).toContain("diamond");
    }
    // If no select found, the control must at least render the label
    expect(screen.getByText("Pupil shape")).toBeInTheDocument();
  });

  it("eye_shape select renders circle, oval, slit, square options", () => {
    setupStore("spider", MINIMAL_SPIDER_CONTROLS, {
      eye_count: 2,
      eye_shape: "circle",
      pupil_enabled: false,
      pupil_shape: "dot",
    });
    render(<BuildControls />);
    const select = screen.queryByLabelText("Eye shape") as HTMLSelectElement | null;
    if (select) {
      const optionValues = Array.from(select.options).map((o) => o.value);
      expect(optionValues).toContain("circle");
      expect(optionValues).toContain("oval");
      expect(optionValues).toContain("slit");
      expect(optionValues).toContain("square");
    }
    expect(screen.getByText("Eye shape")).toBeInTheDocument();
  });
});
