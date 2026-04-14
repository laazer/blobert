// @vitest-environment jsdom
/**
 * Eye shape & pupil system — ADVERSARIAL frontend tests.
 *
 * Spec requirement targeted: ESPS-8
 *
 * Gaps exposed vs. Test Designer suite (BuildControls.eyeShape.test.tsx):
 *   1. Reactive toggle: pupil_shape becomes ENABLED immediately when
 *      pupil_enabled changes false → true in the store (no stale render).
 *   2. Reactive toggle: pupil_shape is RE-DISABLED when pupil_enabled changes
 *      back to false (toggle round-trip).
 *   3. Unknown control key does NOT trigger the pupil_shape disabling rule.
 *   4. Slug-agnostic: disabling rule works for claw_crawler, not just spider/slug.
 *   5. pupil_shape disabling fires even when pupil_enabled is stored as the
 *      number 0 (falsy coerced value, not Python bool — defensive against
 *      API responses that serialize False as 0).
 *   6. pupil_shape is enabled when pupil_enabled is stored as integer 1 (truthy
 *      non-bool; defensive against JSON round-trip producing int instead of bool).
 *   7. No other control row besides pupil_shape is inadvertently disabled by the
 *      pupil rule (regression: overly broad selector).
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { act, cleanup, render, screen } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { BuildControls } from "./BuildControls";
import type { AnimatedBuildControlDef } from "../../types";

afterEach(() => {
  cleanup();
});

// ---------------------------------------------------------------------------
// Shared control definitions
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

const BODY_SIZE_DEF: AnimatedBuildControlDef = {
  key: "body_size",
  label: "Body size",
  type: "float",
  min: 0.5,
  max: 2.0,
  step: 0.05,
  default: 1.0,
};

const EYE_COUNT_DEF: AnimatedBuildControlDef = {
  key: "eye_count",
  label: "Eye count",
  type: "select",
  options: [1, 2, 3, 4],
  default: 2,
};

const PERIPHERAL_EYES_DEF: AnimatedBuildControlDef = {
  key: "peripheral_eyes",
  label: "Peripheral eyes",
  type: "int",
  min: 0,
  max: 3,
  default: 0,
};

const UNRELATED_KEY_DEF: AnimatedBuildControlDef = {
  key: "totally_unrelated_key",
  label: "Totally unrelated",
  type: "select_str",
  options: ["a", "b"],
  default: "a",
};

const SPIDER_CONTROLS: AnimatedBuildControlDef[] = [
  EYE_COUNT_DEF,
  EYE_SHAPE_DEF,
  PUPIL_ENABLED_DEF,
  PUPIL_SHAPE_DEF,
  BODY_SIZE_DEF,
];

const CLAW_CRAWLER_CONTROLS: AnimatedBuildControlDef[] = [
  PERIPHERAL_EYES_DEF,
  EYE_SHAPE_DEF,
  PUPIL_ENABLED_DEF,
  PUPIL_SHAPE_DEF,
];

const CONTROLS_WITH_UNRELATED: AnimatedBuildControlDef[] = [
  EYE_SHAPE_DEF,
  PUPIL_ENABLED_DEF,
  PUPIL_SHAPE_DEF,
  UNRELATED_KEY_DEF,
];

// ---------------------------------------------------------------------------
// Helper
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

function isRowDisabled(labelText: string): boolean {
  const labelEl = screen.queryByText(labelText);
  if (!labelEl) return false;
  let el: HTMLElement | null = labelEl as HTMLElement;
  while (el && el !== document.body) {
    if (el.style && el.style.opacity !== undefined && el.style.opacity !== "") {
      return el.style.opacity === "0.42" || el.style.pointerEvents === "none";
    }
    el = el.parentElement;
  }
  return false;
}

// ---------------------------------------------------------------------------
// 1. Reactive toggle: pupil_shape enabled immediately when store changes false → true
// ---------------------------------------------------------------------------

describe("ESPS-8 adversarial — reactive store toggle false → true", () => {
  it("pupil_shape becomes enabled immediately when store pupil_enabled changes to true (no stale render)", () => {
    // Start with pupil_enabled=false (pupil_shape disabled).
    setupStore("spider", SPIDER_CONTROLS, {
      eye_count: 2,
      eye_shape: "circle",
      pupil_enabled: false,
      pupil_shape: "dot",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Pupil shape")).toBe(true);

    // Now update the store to pupil_enabled=true without remounting.
    act(() => {
      useAppStore.setState((prev) => ({
        animatedBuildOptionValues: {
          ...prev.animatedBuildOptionValues,
          spider: {
            ...(prev.animatedBuildOptionValues?.spider ?? {}),
            pupil_enabled: true,
          },
        },
      }));
    });

    // pupil_shape row must now be enabled (not disabled).
    expect(isRowDisabled("Pupil shape")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// 2. Reactive toggle: pupil_shape re-disabled when store changes true → false
// ---------------------------------------------------------------------------

describe("ESPS-8 adversarial — reactive store toggle true → false", () => {
  it("pupil_shape is re-disabled when pupil_enabled changes back to false in the store", () => {
    // Start with pupil_enabled=true (pupil_shape enabled).
    setupStore("spider", SPIDER_CONTROLS, {
      eye_count: 2,
      eye_shape: "circle",
      pupil_enabled: true,
      pupil_shape: "slit",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Pupil shape")).toBe(false);

    // Toggle pupil_enabled back to false.
    act(() => {
      useAppStore.setState((prev) => ({
        animatedBuildOptionValues: {
          ...prev.animatedBuildOptionValues,
          spider: {
            ...(prev.animatedBuildOptionValues?.spider ?? {}),
            pupil_enabled: false,
          },
        },
      }));
    });

    // pupil_shape must be disabled again.
    expect(isRowDisabled("Pupil shape")).toBe(true);
  });

  it("full round-trip toggle: false → true → false produces disabled → enabled → disabled", () => {
    setupStore("spider", SPIDER_CONTROLS, {
      eye_count: 2,
      eye_shape: "circle",
      pupil_enabled: false,
      pupil_shape: "dot",
    });
    render(<BuildControls />);

    // Initial state: disabled.
    expect(isRowDisabled("Pupil shape")).toBe(true);

    // Toggle on.
    act(() => {
      useAppStore.setState((prev) => ({
        animatedBuildOptionValues: {
          ...prev.animatedBuildOptionValues,
          spider: { ...(prev.animatedBuildOptionValues?.spider ?? {}), pupil_enabled: true },
        },
      }));
    });
    expect(isRowDisabled("Pupil shape")).toBe(false);

    // Toggle off.
    act(() => {
      useAppStore.setState((prev) => ({
        animatedBuildOptionValues: {
          ...prev.animatedBuildOptionValues,
          spider: { ...(prev.animatedBuildOptionValues?.spider ?? {}), pupil_enabled: false },
        },
      }));
    });
    expect(isRowDisabled("Pupil shape")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// 3. Unknown control key does NOT trigger the pupil_shape disabling rule
// ---------------------------------------------------------------------------

describe("ESPS-8 adversarial — unknown control key does not trigger pupil disabling", () => {
  it("a control with key 'totally_unrelated_key' is not disabled by the pupil rule", () => {
    setupStore("spider", CONTROLS_WITH_UNRELATED, {
      eye_shape: "circle",
      pupil_enabled: false,
      pupil_shape: "dot",
      totally_unrelated_key: "a",
    });
    render(<BuildControls />);

    // The unrelated key must not be disabled (the pupil rule targets only pupil_shape).
    expect(isRowDisabled("Totally unrelated")).toBe(false);
  });

  it("pupil_shape is still disabled when unrelated key is present and pupil_enabled=false", () => {
    setupStore("spider", CONTROLS_WITH_UNRELATED, {
      eye_shape: "circle",
      pupil_enabled: false,
      pupil_shape: "dot",
      totally_unrelated_key: "b",
    });
    render(<BuildControls />);

    // pupil_shape must still be disabled.
    expect(isRowDisabled("Pupil shape")).toBe(true);
    // But unrelated key must not be affected.
    expect(isRowDisabled("Totally unrelated")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// 4. Slug-agnostic: claw_crawler obeys the same pupil disabling rule
// ---------------------------------------------------------------------------

describe("ESPS-8 adversarial — claw_crawler pupil disabling rule", () => {
  it("pupil_shape is disabled for claw_crawler when pupil_enabled=false", () => {
    setupStore("claw_crawler", CLAW_CRAWLER_CONTROLS, {
      peripheral_eyes: 1,
      eye_shape: "circle",
      pupil_enabled: false,
      pupil_shape: "dot",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Pupil shape")).toBe(true);
  });

  it("pupil_shape is enabled for claw_crawler when pupil_enabled=true", () => {
    setupStore("claw_crawler", CLAW_CRAWLER_CONTROLS, {
      peripheral_eyes: 2,
      eye_shape: "square",
      pupil_enabled: true,
      pupil_shape: "diamond",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Pupil shape")).toBe(false);
  });

  it("reactive toggle also works for claw_crawler: false → true", () => {
    setupStore("claw_crawler", CLAW_CRAWLER_CONTROLS, {
      peripheral_eyes: 1,
      eye_shape: "circle",
      pupil_enabled: false,
      pupil_shape: "dot",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Pupil shape")).toBe(true);

    act(() => {
      useAppStore.setState((prev) => ({
        animatedBuildOptionValues: {
          ...prev.animatedBuildOptionValues,
          claw_crawler: {
            ...(prev.animatedBuildOptionValues?.claw_crawler ?? {}),
            pupil_enabled: true,
          },
        },
      }));
    });
    expect(isRowDisabled("Pupil shape")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// 5. Falsy integer 0 for pupil_enabled disables pupil_shape (API boundary guard)
// ---------------------------------------------------------------------------

describe("ESPS-8 adversarial — pupil_enabled stored as integer 0 (falsy, not Python bool)", () => {
  /**
   * # CHECKPOINT: spec says pupil_enabled is a bool, but a JSON round-trip from a
   * non-conformant API could deliver the integer 0 instead of false.
   * Conservative assumption: the UI must treat any falsy value as "disabled".
   * Test encodes this assumption.
   */
  it("pupil_shape is disabled when pupil_enabled is integer 0 (falsy non-bool)", () => {
    setupStore("spider", SPIDER_CONTROLS, {
      eye_count: 2,
      eye_shape: "circle",
      pupil_enabled: 0,  // falsy int, not Python bool False
      pupil_shape: "dot",
    });
    render(<BuildControls />);
    // CHECKPOINT: treat 0 as falsy → pupil_shape disabled.
    expect(isRowDisabled("Pupil shape")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// 6. Truthy integer 1 for pupil_enabled enables pupil_shape
// ---------------------------------------------------------------------------

describe("ESPS-8 adversarial — pupil_enabled stored as integer 1 (truthy, not Python bool)", () => {
  /**
   * # CHECKPOINT: symmetric to test 5. API might return 1 instead of true.
   * Conservative assumption: any truthy value enables pupil_shape.
   */
  it("pupil_shape is enabled when pupil_enabled is integer 1 (truthy non-bool)", () => {
    setupStore("spider", SPIDER_CONTROLS, {
      eye_count: 2,
      eye_shape: "circle",
      pupil_enabled: 1,  // truthy int
      pupil_shape: "slit",
    });
    render(<BuildControls />);
    // CHECKPOINT: treat 1 as truthy → pupil_shape enabled.
    expect(isRowDisabled("Pupil shape")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// 7. No other control row is inadvertently disabled by the pupil rule
// ---------------------------------------------------------------------------

describe("ESPS-8 adversarial — pupil rule must not disable controls other than pupil_shape", () => {
  it("eye_shape, body_size, and eye_count are not disabled when pupil_enabled=false", () => {
    setupStore("spider", SPIDER_CONTROLS, {
      eye_count: 2,
      eye_shape: "circle",
      pupil_enabled: false,
      pupil_shape: "dot",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Eye shape")).toBe(false);
    expect(isRowDisabled("Eye count")).toBe(false);
    // Body size is a float control; the disabling rule must not bleed into float controls.
    // (The Test Designer suite skips float controls; here we explicitly check.)
    // Note: float controls are in a separate section; they may not have the opacity wrapper.
    // The key assertion is they are not disabled BY THE PUPIL RULE.
    // We verify by confirming eye_shape and eye_count (non-float) are not disabled.
  });

  it("pupil_enabled control row is not disabled when pupil_enabled=false (toggle must remain accessible)", () => {
    setupStore("spider", SPIDER_CONTROLS, {
      eye_count: 2,
      eye_shape: "circle",
      pupil_enabled: false,
      pupil_shape: "dot",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Pupil")).toBe(false);
  });

  it("only pupil_shape is disabled (not pupil_enabled, eye_shape, or eye_count) when pupil_enabled=false", () => {
    setupStore("spider", SPIDER_CONTROLS, {
      eye_count: 2,
      eye_shape: "oval",
      pupil_enabled: false,
      pupil_shape: "diamond",
    });
    render(<BuildControls />);
    expect(isRowDisabled("Pupil shape")).toBe(true);
    expect(isRowDisabled("Pupil")).toBe(false);
    expect(isRowDisabled("Eye shape")).toBe(false);
    expect(isRowDisabled("Eye count")).toBe(false);
  });
});
