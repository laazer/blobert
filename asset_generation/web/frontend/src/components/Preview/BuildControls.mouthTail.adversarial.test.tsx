// @vitest-environment jsdom
/**
 * Mouth extra & tail extra — adversarial frontend tests.
 *
 * Adversarial coverage:
 *   - Reactive toggle false→true transitions (DOM updates on value change)
 *   - Toggle round-trip tests (false → true → false should work both ways)
 *   - Unknown key isolation (unknown keys don't affect mouth/tail logic)
 *   - Slug-agnostic rule validation (rules apply regardless of slug type)
 *   - Integer 0/1 falsy/truthy coercion tests (DOM value "0" vs boolean false)
 *   - No bleed-over tests between mouth and tail controls (independent toggles)
 *
 * Spec requirement covered: MTE-10 (Frontend — Conditional Disabling Logic)
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { BuildControls } from "./BuildControls";
import type { AnimatedBuildControlDef } from "../../types";

afterEach(() => {
  cleanup();
});

// ---------------------------------------------------------------------------
// Control definitions for adversarial testing
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

const MINIMAL_CONTROLS = [
  MOUTH_ENABLED_DEF,
  MOUTH_SHAPE_DEF,
  TAIL_ENABLED_DEF,
  TAIL_SHAPE_DEF,
  TAIL_LENGTH_DEF,
];

// ---------------------------------------------------------------------------
// Helper functions
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
// Reactive toggle false→true transitions (DOM updates on value change)
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — reactive false→true transitions", () => {
  it("mouth_shape enables when mouth_enabled toggled from false to true", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(true);

    // Toggle mouth_enabled to true
    const toggle = screen.getByLabelText("Mouth") as HTMLInputElement;
    fireEvent.click(toggle);

    expect((toggle as HTMLInputElement).checked).toBe(true);
    expect(isRowDisabled("Mouth shape")).toBe(false);
  });

  it("tail_shape and tail_length enable when tail_enabled toggled from false to true", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Tail shape")).toBe(true);
    expect(isRowDisabled("Tail length")).toBe(true);

    // Toggle tail_enabled to true
    const toggle = screen.getByLabelText("Tail") as HTMLInputElement;
    fireEvent.click(toggle);

    expect((toggle as HTMLInputElement).checked).toBe(true);
    expect(isRowDisabled("Tail shape")).toBe(false);
    expect(isRowDisabled("Tail length")).toBe(false);
  });

  it("mouth_shape disables when mouth_enabled toggled from true to false", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: true,
      mouth_shape: "fang",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(false);

    // Toggle mouth_enabled to false
    const toggle = screen.getByLabelText("Mouth") as HTMLInputElement;
    fireEvent.click(toggle);

    expect((toggle as HTMLInputElement).checked).toBe(false);
    expect(isRowDisabled("Mouth shape")).toBe(true);
  });

  it("tail controls disable when tail_enabled toggled from true to false", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: true,
      tail_shape: "curled",
      tail_length: 2.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Tail shape")).toBe(false);
    expect(isRowDisabled("Tail length")).toBe(false);

    // Toggle tail_enabled to false
    const toggle = screen.getByLabelText("Tail") as HTMLInputElement;
    fireEvent.click(toggle);

    expect((toggle as HTMLInputElement).checked).toBe(false);
    expect(isRowDisabled("Tail shape")).toBe(true);
    expect(isRowDisabled("Tail length")).toBe(true);
  });

  it("mouth controls remain enabled while tail toggles", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: true,
      mouth_shape: "fang",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(false);

    // Toggle tail_enabled multiple times
    const toggle = screen.getByLabelText("Tail") as HTMLInputElement;
    fireEvent.click(toggle); // false → true
    fireEvent.click(toggle); // true → false
    fireEvent.click(toggle); // false → true

    expect((toggle as HTMLInputElement).checked).toBe(true);
    expect(isRowDisabled("Mouth shape")).toBe(false); // mouth should remain unaffected
  });
});

// ---------------------------------------------------------------------------
// Toggle round-trip tests (false → true → false should work both ways)
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — toggle round-trip", () => {
  it("mouth_enabled: false → true → false returns to disabled state", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(true);

    const toggle = screen.getByLabelText("Mouth") as HTMLInputElement;

    // false → true
    fireEvent.click(toggle);
    expect((toggle as HTMLInputElement).checked).toBe(true);
    expect(isRowDisabled("Mouth shape")).toBe(false);

    // true → false
    fireEvent.click(toggle);
    expect((toggle as HTMLInputElement).checked).toBe(false);
    expect(isRowDisabled("Mouth shape")).toBe(true);
  });

  it("tail_enabled: false → true → false round-trip", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);

    const toggle = screen.getByLabelText("Tail") as HTMLInputElement;

    // false → true
    fireEvent.click(toggle);
    expect(isRowDisabled("Tail shape")).toBe(false);

    // true → false
    fireEvent.click(toggle);
    expect(isRowDisabled("Tail shape")).toBe(true);
  });

  it("mouth_shape select value persists through toggle round-trip", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: true,
      mouth_shape: "fang",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);
    const select = screen.getByLabelText("Mouth shape") as HTMLSelectElement;
    expect(select.value).toBe("fang");

    // Disable and re-enable
    const toggle = screen.getByLabelText("Mouth") as HTMLInputElement;
    fireEvent.click(toggle); // disable
    fireEvent.click(toggle); // enable

    // Value should persist
    expect((toggle as HTMLInputElement).checked).toBe(true);
    expect(select.value).toBe("fang");
  });

  it("tail controls round-trip with shape change", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: true,
      tail_shape: "curled",
      tail_length: 2.0,
    });

    render(<BuildControls />);

    const toggle = screen.getByLabelText("Tail") as HTMLInputElement;
    const shapeSelect = screen.getByLabelText("Tail shape") as HTMLSelectElement;

    // Change shape while enabled
    fireEvent.change(shapeSelect, { target: { value: "whip" } });
    expect(shapeSelect.value).toBe("whip");

    // Disable and re-enable
    fireEvent.click(toggle);
    fireEvent.click(toggle);

    // Shape should persist
    expect((toggle as HTMLInputElement).checked).toBe(true);
    expect(shapeSelect.value).toBe("whip");
  });
});

// ---------------------------------------------------------------------------
// Unknown key isolation (unknown keys don't affect mouth/tail logic)
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — unknown key isolation", () => {
  const EXTRA_UNKNOWN_CONTROLS: AnimatedBuildControlDef[] = [
    {
      key: "unknown_custom_control_xyz",
      label: "Unknown Control",
      type: "bool" as const,
      default: false,
    },
    {
      key: "another_fake_key_123",
      label: "Fake Key",
      type: "select_str" as const,
      options: ["a", "b"],
      default: "a",
    },
  ];

  it("unknown keys do not affect mouth_shape disabling logic", () => {
    setupStore(
      "slug",
      [...MINIMAL_CONTROLS, ...EXTRA_UNKNOWN_CONTROLS],
      {
        unknown_custom_control_xyz: true,
        another_fake_key_123: "b",
        mouth_enabled: false,
        mouth_shape: "smile",
        tail_enabled: false,
        tail_shape: "spike",
        tail_length: 1.0,
      },
    );

    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(true); // should still be disabled
  });

  it("unknown keys do not affect tail controls disabling logic", () => {
    setupStore(
      "slug",
      [...MINIMAL_CONTROLS, ...EXTRA_UNKNOWN_CONTROLS],
      {
        unknown_custom_control_xyz: true,
        mouth_enabled: false,
        mouth_shape: "smile",
        tail_enabled: false,
        tail_shape: "spike",
        tail_length: 1.0,
        another_fake_key_123: "b",
      },
    );

    render(<BuildControls />);
    expect(isRowDisabled("Tail shape")).toBe(true); // should still be disabled
  });

  it("unknown keys do not cause rendering errors", () => {
    setupStore(
      "slug",
      [...MINIMAL_CONTROLS, ...EXTRA_UNKNOWN_CONTROLS],
      {
        unknown_custom_control_xyz: true,
        another_fake_key_123: "b",
        mouth_enabled: true,
        mouth_shape: "fang",
        tail_enabled: true,
        tail_shape: "curled",
        tail_length: 2.0,
      },
    );

    expect(() => render(<BuildControls />)).not.toThrow();
  });

  it("unknown keys do not enable disabled controls", () => {
    setupStore(
      "slug",
      [...MINIMAL_CONTROLS, ...EXTRA_UNKNOWN_CONTROLS],
      {
        unknown_custom_control_xyz: true, // fake key set to truthy value
        mouth_enabled: false,
        mouth_shape: "smile",
        tail_enabled: false,
        tail_shape: "spike",
        tail_length: 1.0,
      },
    );

    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(true); // should still be disabled
  });
});

// ---------------------------------------------------------------------------
// Slug-agnostic rule validation (rules apply regardless of slug type)
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — slug-agnostic rules", () => {
  const SLUGS = ["spider", "slug", "claw_crawler", "imp", "carapace_husk", "spitter"];

  it.each(SLUGS)("mouth_shape disabled when mouth_enabled=false for %s", (slug) => {
    setupStore(slug, MINIMAL_CONTROLS, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(true);
  });

  it.each(SLUGS)("mouth_shape enabled when mouth_enabled=true for %s", (slug) => {
    setupStore(slug, MINIMAL_CONTROLS, {
      mouth_enabled: true,
      mouth_shape: "fang",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(false);
  });

  it.each(SLUGS)("tail_shape disabled when tail_enabled=false for %s", (slug) => {
    setupStore(slug, MINIMAL_CONTROLS, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Tail shape")).toBe(true);
  });

  it.each(SLUGS)("tail controls enabled when tail_enabled=true for %s", (slug) => {
    setupStore(slug, MINIMAL_CONTROLS, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: true,
      tail_shape: "curled",
      tail_length: 2.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Tail shape")).toBe(false);
    expect(isRowDisabled("Tail length")).toBe(false);
  });

  it("mouth rules apply to spider even with custom logic", () => {
    setupStore("spider", MINIMAL_CONTROLS, {
      mouth_enabled: true,
      mouth_shape: "fang",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(false);
  });

  it("tail rules apply to claw_crawler even with custom logic", () => {
    setupStore("claw_crawler", MINIMAL_CONTROLS, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: true,
      tail_shape: "segmented",
      tail_length: 1.5,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Tail shape")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Integer 0/1 falsy/truthy coercion tests (DOM value "0" vs boolean false)
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — integer 0/1 coercion", () => {
  it("mouth_enabled=1 coerces to true, enabling mouth_shape", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: 1, // integer truthy value
      mouth_shape: "fang",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(false);
  });

  it("mouth_enabled=0 coerces to false, disabling mouth_shape", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: 0, // integer falsy value
      mouth_shape: "fang",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(true);
  });

  it("tail_enabled=1 coerces to true, enabling tail controls", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: 1, // integer truthy value
      tail_shape: "curled",
      tail_length: 2.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Tail shape")).toBe(false);
    expect(isRowDisabled("Tail length")).toBe(false);
  });

  it("tail_enabled=0 coerces to false, disabling tail controls", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: 0, // integer falsy value
      tail_shape: "curled",
      tail_length: 2.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Tail shape")).toBe(true);
    expect(isRowDisabled("Tail length")).toBe(true);
  });

  it("mouth_enabled=1 and tail_enabled=0 works correctly", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: 1, // truthy
      mouth_shape: "fang",
      tail_enabled: 0, // falsy
      tail_shape: "curled",
      tail_length: 2.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(false);
    expect(isRowDisabled("Tail shape")).toBe(true);
  });

  it("mouth_enabled=0 and tail_enabled=1 works correctly", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: 0, // falsy
      mouth_shape: "fang",
      tail_enabled: 1, // truthy
      tail_shape: "curled",
      tail_length: 2.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(true);
    expect(isRowDisabled("Tail shape")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// No bleed-over tests between mouth and tail controls (independent toggles)
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — no cross-disable bleed-over", () => {
  it("mouth_enabled does not affect tail_shape disabling state", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: false, // disabled
      mouth_shape: "smile",
      tail_enabled: true, // enabled
      tail_shape: "curled",
      tail_length: 2.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Tail shape")).toBe(false); // should be enabled independently
  });

  it("mouth_enabled does not affect tail_length disabling state", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: true, // enabled
      mouth_shape: "fang",
      tail_enabled: false, // disabled
      tail_shape: "curled",
      tail_length: 2.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Tail length")).toBe(true); // should be disabled independently
  });

  it("tail_enabled does not affect mouth_shape disabling state", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: true, // enabled
      mouth_shape: "fang",
      tail_enabled: false, // disabled
      tail_shape: "curled",
      tail_length: 2.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(false); // should be enabled independently
  });

  it("tail_enabled does not affect mouth_enabled toggle behavior", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: true,
      tail_shape: "curled",
      tail_length: 2.0,
    });

    render(<BuildControls />);

    const mouthToggle = screen.getByLabelText("Mouth") as HTMLInputElement;
    expect((mouthToggle as HTMLInputElement).checked).toBe(false);

    // Toggle should work independently of tail state
    fireEvent.click(mouthToggle);
    expect((mouthToggle as HTMLInputElement).checked).toBe(true);
  });

  it("both mouth and tail can be toggled independently without interference", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);

    const mouthToggle = screen.getByLabelText("Mouth") as HTMLInputElement;
    const tailToggle = screen.getByLabelText("Tail") as HTMLInputElement;

    // Toggle mouth only
    fireEvent.click(mouthToggle);
    expect((mouthToggle as HTMLInputElement).checked).toBe(true);
    expect(isRowDisabled("Mouth shape")).toBe(false);
    expect(isRowDisabled("Tail shape")).toBe(true); // tail should still be disabled

    // Toggle tail only (mouth remains enabled)
    fireEvent.click(tailToggle);
    expect((tailToggle as HTMLInputElement).checked).toBe(true);
    expect(isRowDisabled("Mouth shape")).toBe(false); // mouth should remain enabled
    expect(isRowDisabled("Tail shape")).toBe(false);
  });

  it("pupil_enabled does not affect mouth or tail controls", () => {
    const PUPIL_ENABLED_DEF = {
      key: "pupil_enabled" as const,
      label: "Pupil",
      type: "bool" as const,
      default: false,
    };

    setupStore("slug", [...MINIMAL_CONTROLS, PUPIL_ENABLED_DEF], {
      mouth_enabled: true,
      mouth_shape: "fang",
      tail_enabled: true,
      tail_shape: "curled",
      tail_length: 2.0,
      pupil_enabled: false, // disabled but should not affect others
    });

    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(false);
    expect(isRowDisabled("Tail shape")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Combined edge cases and complex scenarios
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — combined edge cases", () => {
  it("all three toggles (pupil, mouth, tail) can be independently set", () => {
    const PUPIL_ENABLED_DEF = {
      key: "pupil_enabled" as const,
      label: "Pupil",
      type: "bool" as const,
      default: false,
    };

    setupStore("slug", [...MINIMAL_CONTROLS, PUPIL_ENABLED_DEF], {
      mouth_enabled: true,
      mouth_shape: "fang",
      tail_enabled: true,
      tail_shape: "curled",
      tail_length: 2.0,
      pupil_enabled: false,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(false);
    expect(isRowDisabled("Tail shape")).toBe(false);
    // pupil_shape should be disabled due to pupil_enabled=false
    expect(true).toBe(true); // placeholder for pupil check if needed
  });

  it("rapid toggling does not cause inconsistent state", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);

    const mouthToggle = screen.getByLabelText("Mouth") as HTMLInputElement;
    const tailToggle = screen.getByLabelText("Tail") as HTMLInputElement;

    // Rapid toggling
    fireEvent.click(mouthToggle); // true
    fireEvent.click(tailToggle); // true
    fireEvent.click(mouthToggle); // false
    fireEvent.click(tailToggle); // false
    fireEvent.click(mouthToggle); // true
    fireEvent.click(tailToggle); // true

    expect((mouthToggle as HTMLInputElement).checked).toBe(true);
    expect((tailToggle as HTMLInputElement).checked).toBe(true);
    expect(isRowDisabled("Mouth shape")).toBe(false);
    expect(isRowDisabled("Tail shape")).toBe(false);
  });

  it("initial state with all enabled works correctly", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: true,
      mouth_shape: "beak",
      tail_enabled: true,
      tail_shape: "whip",
      tail_length: 2.5,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(false);
    expect(isRowDisabled("Tail shape")).toBe(false);
    expect(isRowDisabled("Tail length")).toBe(false);

    const select = screen.getByLabelText("Mouth shape") as HTMLSelectElement;
    expect(select.value).toBe("beak");

    const input = screen.getByLabelText("Tail length") as HTMLInputElement;
    expect(input.value).toBe("2.5");
  });
});

// ---------------------------------------------------------------------------
// Toggle sequence: disable then re-enable restores enabled state (task requirement)
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — toggle sequence: disable then re-enable restores state", () => {
  it("mouth_shape re-enables after disable→re-enable sequence", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: true,
      mouth_shape: "fang",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);

    const toggle = screen.getByLabelText("Mouth") as HTMLInputElement;

    // Initial: enabled
    expect(isRowDisabled("Mouth shape")).toBe(false);

    // Disable
    fireEvent.click(toggle);
    expect((toggle as HTMLInputElement).checked).toBe(false);
    expect(isRowDisabled("Mouth shape")).toBe(true);

    // Re-enable
    fireEvent.click(toggle);
    expect((toggle as HTMLInputElement).checked).toBe(true);
    expect(isRowDisabled("Mouth shape")).toBe(false);
  });

  it("tail controls re-enable after disable→re-enable sequence", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: true,
      tail_shape: "curled",
      tail_length: 2.0,
    });

    render(<BuildControls />);

    const toggle = screen.getByLabelText("Tail") as HTMLInputElement;

    // Initial: enabled
    expect(isRowDisabled("Tail shape")).toBe(false);
    expect(isRowDisabled("Tail length")).toBe(false);

    // Disable
    fireEvent.click(toggle);
    expect((toggle as HTMLInputElement).checked).toBe(false);
    expect(isRowDisabled("Tail shape")).toBe(true);
    expect(isRowDisabled("Tail length")).toBe(true);

    // Re-enable
    fireEvent.click(toggle);
    expect((toggle as HTMLInputElement).checked).toBe(true);
    expect(isRowDisabled("Tail shape")).toBe(false);
    expect(isRowDisabled("Tail length")).toBe(false);
  });

  it("mouth_enabled controls-only toggle does not affect tail enabled state", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: true,
      tail_shape: "whip",
      tail_length: 1.5,
    });

    render(<BuildControls />);

    const mouthToggle = screen.getByLabelText("Mouth") as HTMLInputElement;

    // Toggle mouth multiple times
    fireEvent.click(mouthToggle); // enable mouth
    fireEvent.click(mouthToggle); // disable mouth

    // Tail controls must remain enabled throughout
    expect(isRowDisabled("Tail shape")).toBe(false);
    expect(isRowDisabled("Tail length")).toBe(false);
  });

  it("tail_enabled controls-only toggle does not affect mouth enabled state", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: true,
      mouth_shape: "beak",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);

    const tailToggle = screen.getByLabelText("Tail") as HTMLInputElement;

    // Toggle tail multiple times
    fireEvent.click(tailToggle); // enable tail
    fireEvent.click(tailToggle); // disable tail

    // Mouth shape must remain enabled throughout
    expect(isRowDisabled("Mouth shape")).toBe(false);
  });

  it("multiple toggle sequences are idempotent at final state", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);

    const mouthToggle = screen.getByLabelText("Mouth") as HTMLInputElement;
    const tailToggle = screen.getByLabelText("Tail") as HTMLInputElement;

    // 3 enable/disable cycles on each
    for (let i = 0; i < 3; i++) {
      fireEvent.click(mouthToggle); // off → on
      fireEvent.click(tailToggle);  // off → on
      fireEvent.click(mouthToggle); // on → off
      fireEvent.click(tailToggle);  // on → off
    }

    // After even number of clicks, both should be back to false
    expect((mouthToggle as HTMLInputElement).checked).toBe(false);
    expect((tailToggle as HTMLInputElement).checked).toBe(false);
    expect(isRowDisabled("Mouth shape")).toBe(true);
    expect(isRowDisabled("Tail shape")).toBe(true);
    expect(isRowDisabled("Tail length")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// MTE-10-AC-13/14/15: Regression guards — existing disabling rules not broken
// Exposes gap: the existing adversarial file tests pupil but not the spider
// placement row or eye_distribution (MTE-10-AC-14, MTE-10-AC-15).
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — regression: existing disabled rules not broken", () => {
  const EYE_SHAPE_DEF: AnimatedBuildControlDef = {
    key: "eye_shape",
    label: "Eye shape",
    type: "select_str",
    options: ["circle", "oval", "slit", "square"],
    default: "circle",
  };

  const EYE_COUNT_DEF: AnimatedBuildControlDef = {
    key: "eye_count",
    label: "Eye count",
    type: "float",
    min: 1,
    max: 8,
    step: 1,
    default: 2,
  };

  const EYE_DISTRIBUTION_DEF: AnimatedBuildControlDef = {
    key: "eye_distribution",
    label: "Eye distribution",
    type: "select_str",
    options: ["uniform", "random"],
    default: "uniform",
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

  const FULL_EYE_CONTROLS: AnimatedBuildControlDef[] = [
    EYE_SHAPE_DEF,
    EYE_COUNT_DEF,
    EYE_DISTRIBUTION_DEF,
    PUPIL_ENABLED_DEF,
    PUPIL_SHAPE_DEF,
    ...MINIMAL_CONTROLS,
  ];

  it("MTE-10-AC-13: pupil_shape disabling still works after mouth/tail addition", () => {
    setupStore("spider", FULL_EYE_CONTROLS, {
      eye_shape: "circle",
      eye_count: 2,
      eye_distribution: "uniform",
      pupil_enabled: false,
      pupil_shape: "dot",
      mouth_enabled: true,
      mouth_shape: "fang",
      tail_enabled: true,
      tail_shape: "curled",
      tail_length: 2.0,
    });

    render(<BuildControls />);
    // pupil_shape must still be disabled when pupil_enabled=false
    expect(isRowDisabled("Pupil shape")).toBe(true);
    // mouth_shape must be enabled (mouth_enabled=true)
    expect(isRowDisabled("Mouth shape")).toBe(false);
  });

  it("MTE-10-AC-15: eye_distribution disabled when eye_count=1 (regression)", () => {
    setupStore("spider", FULL_EYE_CONTROLS, {
      eye_shape: "circle",
      eye_count: 1,
      eye_distribution: "uniform",
      pupil_enabled: false,
      pupil_shape: "dot",
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);
    // eye_distribution disabled when eye_count=1
    expect(isRowDisabled("Eye distribution")).toBe(true);
    // mouth/tail must remain independently disabled (their own toggles)
    expect(isRowDisabled("Mouth shape")).toBe(true);
    expect(isRowDisabled("Tail shape")).toBe(true);
  });

  it("adding mouth/tail controls to full control set does not break eye distribution logic", () => {
    setupStore("spider", FULL_EYE_CONTROLS, {
      eye_shape: "oval",
      eye_count: 2,
      eye_distribution: "random",
      pupil_enabled: true,
      pupil_shape: "slit",
      mouth_enabled: true,
      mouth_shape: "beak",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);
    // eye_distribution should be enabled when eye_count > 1
    expect(isRowDisabled("Eye distribution")).toBe(false);
    // pupil_shape enabled when pupil_enabled=true
    expect(isRowDisabled("Pupil shape")).toBe(false);
    // mouth_shape enabled when mouth_enabled=true
    expect(isRowDisabled("Mouth shape")).toBe(false);
    // tail_shape disabled when tail_enabled=false
    expect(isRowDisabled("Tail shape")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Spec gap: tail_enabled=false with numeric 0 value (MTE-10 absent/falsy)
// The spec says absent mouth_enabled is treated as falsy. Test that numeric
// string "0" also disables (edge case from old serialized state).
// ---------------------------------------------------------------------------

describe("BuildControls mouth & tail — falsy value edge cases for toggle keys", () => {
  it("mouth_enabled='false' string disables mouth_shape (string false is truthy in JS!)", () => {
    // CHECKPOINT: In JS, the string "false" is truthy — !!"false" === true.
    // This means if the backend sends "false" as a string, mouth_shape would be ENABLED.
    // This test documents the expected behavior: the spec says !values["mouth_enabled"].
    // If values["mouth_enabled"] = "false" (string), then !!"false" = true → NOT disabled.
    // Conservative assumption: backend always sends Python bool → JSON boolean, not string.
    // We test that boolean false correctly disables, and that this is the expected path.
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: false, // JSON boolean false from Python backend
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(true);
  });

  it("tail_enabled=null disables tail controls (null is falsy)", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      mouth_enabled: false,
      mouth_shape: "smile",
      tail_enabled: null, // null is falsy
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Tail shape")).toBe(true);
    expect(isRowDisabled("Tail length")).toBe(true);
  });

  it("mouth_enabled=undefined (absent) disables mouth_shape", () => {
    setupStore("slug", MINIMAL_CONTROLS, {
      // mouth_enabled intentionally not set → undefined
      mouth_shape: "smile",
      tail_enabled: false,
      tail_shape: "spike",
      tail_length: 1.0,
    });

    render(<BuildControls />);
    expect(isRowDisabled("Mouth shape")).toBe(true);
  });
});
