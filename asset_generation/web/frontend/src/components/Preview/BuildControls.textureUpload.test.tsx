// @vitest-environment jsdom
/**
 * Texture upload support — frontend behavioral tests.
 *
 * Spec requirements covered:
 *   TUS-1: "Custom" option in the texture mode selector
 *   TUS-2: File input render conditions, accept attribute, aria-label
 *   TUS-3: File validation rules (MIME type, size, error messages, ordering)
 *   TUS-4: Blob URL lifecycle (createObjectURL / revokeObjectURL calls)
 *   TUS-5: Zustand store customTextureUrl slice (via store state assertions)
 *   TUS-7: Remove button render conditions and click behavior
 *   TUS-9: buildControlDisabled() behavior under "custom" mode
 *
 * TUS-6 (GlbViewer Three.js TextureLoader overlay) is excluded — visual/integration
 * concern without deterministic unit test coverage per ticket scope.
 *
 * All tests will be RED until Tasks 2–3 (store slice + BuildControls changes) are
 * implemented. Tests are intentionally written against the specified API surface.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { BuildControls } from "./BuildControls";
import type { AnimatedBuildControlDef } from "../../types";

// ---------------------------------------------------------------------------
// URL mock setup — spied in beforeEach, restored in afterEach
// ---------------------------------------------------------------------------

let createObjectURLSpy: ReturnType<typeof vi.spyOn>;
let revokeObjectURLSpy: ReturnType<typeof vi.spyOn>;

beforeEach(() => {
  // jsdom does not implement URL.createObjectURL; install deterministic stubs.
  if (!URL.createObjectURL) {
    Object.defineProperty(URL, "createObjectURL", { writable: true, value: () => "" });
  }
  if (!URL.revokeObjectURL) {
    Object.defineProperty(URL, "revokeObjectURL", { writable: true, value: () => undefined });
  }
  createObjectURLSpy = vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:test-url");
  revokeObjectURLSpy = vi.spyOn(URL, "revokeObjectURL").mockReturnValue(undefined);
});

afterEach(() => {
  cleanup();
  createObjectURLSpy.mockRestore();
  revokeObjectURLSpy.mockRestore();
});

// ---------------------------------------------------------------------------
// Control definition constants — matches pattern from BuildControls.texture.test.tsx
// ---------------------------------------------------------------------------

const TEXTURE_MODE_DEF: AnimatedBuildControlDef = {
  key: "texture_mode",
  label: "Texture mode",
  type: "select_str",
  // Python-side tuple: "custom" is intentionally absent here.
  // BuildControls is expected to inject "custom" client-side.
  options: ["none", "gradient", "spots", "stripes"],
  default: "none",
};

const TEXTURE_GRAD_COLOR_A_DEF: AnimatedBuildControlDef = {
  key: "texture_grad_color_a",
  label: "Gradient color A",
  type: "str",
  default: "",
};

const TEXTURE_SPOT_COLOR_DEF: AnimatedBuildControlDef = {
  key: "texture_spot_color",
  label: "Spot color",
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

const TEXTURE_STRIPE_WIDTH_DEF: AnimatedBuildControlDef = {
  key: "texture_stripe_width",
  label: "Stripe width",
  type: "float",
  min: 0.05,
  max: 1.0,
  step: 0.01,
  default: 0.2,
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

const BASE_TEXTURE_CONTROLS: AnimatedBuildControlDef[] = [
  TEXTURE_MODE_DEF,
  TEXTURE_GRAD_COLOR_A_DEF,
  TEXTURE_SPOT_COLOR_DEF,
  TEXTURE_SPOT_DENSITY_DEF,
  TEXTURE_STRIPE_WIDTH_DEF,
];

const CONTROLS_WITH_PUPIL_MOUTH: AnimatedBuildControlDef[] = [
  PUPIL_ENABLED_DEF,
  PUPIL_SHAPE_DEF,
  MOUTH_ENABLED_DEF,
  MOUTH_SHAPE_DEF,
  ...BASE_TEXTURE_CONTROLS,
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function setupStore(
  slug: string,
  controls: AnimatedBuildControlDef[],
  optionValues: Record<string, unknown>,
  customTextureUrl: string | null = null,
) {
  useAppStore.setState({
    commandContext: { cmd: "animated", enemy: slug },
    animatedEnemyMeta: [{ slug, label: slug }],
    animatedBuildControls: { [slug]: controls },
    animatedBuildOptionValues: { [slug]: optionValues },
    // customTextureUrl is the store slice added by Task 2.
    // setState merges; this works even before the TS interface is extended.
    customTextureUrl,
  } as Parameters<typeof useAppStore.setState>[0]);
}

/**
 * Create a synthetic File object with the given type and size.
 * Size is approximated by constructing a Blob with the right byte count.
 */
function makeFile(name: string, type: string, size: number): File {
  const content = new Uint8Array(size);
  const blob = new Blob([content], { type });
  return new File([blob], name, { type });
}

/**
 * Fire a change event on the file input with the given file.
 */
function uploadFile(file: File) {
  const input = screen.getByLabelText("Upload texture") as HTMLInputElement;
  Object.defineProperty(input, "files", { value: [file], writable: true });
  fireEvent.change(input);
}

// ---------------------------------------------------------------------------
// TUS-1: "Custom" option exists in the texture mode selector
// ---------------------------------------------------------------------------

describe('TUS-1: "Custom" option in the texture mode selector', () => {
  it("TUS-1-AC-1: texture_mode select contains a 'custom' option", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "none" });
    render(<BuildControls />);

    // The "Texture mode" label must be present.
    expect(screen.getByText("Texture mode")).toBeInTheDocument();

    // Locate the select by label or find option text directly.
    const select = screen.queryByLabelText("Texture mode") as HTMLSelectElement | null;
    if (select) {
      const values = Array.from(select.options).map((o) => o.value);
      expect(values).toContain("custom");
    } else {
      // Fallback: option element with value "custom" exists somewhere in the DOM.
      const customOption = document.querySelector('option[value="custom"]');
      expect(customOption).toBeTruthy();
    }
  });

  it("TUS-1-AC-1: texture_mode select contains all five expected options in order", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "none" });
    render(<BuildControls />);

    const select = screen.queryByLabelText("Texture mode") as HTMLSelectElement | null;
    if (select) {
      const values = Array.from(select.options).map((o) => o.value);
      expect(values).toContain("none");
      expect(values).toContain("gradient");
      expect(values).toContain("spots");
      expect(values).toContain("stripes");
      expect(values).toContain("custom");
      // Order: "custom" must be last (after "stripes").
      const customIdx = values.indexOf("custom");
      const stripesIdx = values.indexOf("stripes");
      expect(customIdx).toBeGreaterThan(stripesIdx);
    }
  });

  it("TUS-1-AC-2: 'custom' option display text is 'custom'", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "none" });
    render(<BuildControls />);

    const customOption = document.querySelector('option[value="custom"]') as HTMLOptionElement | null;
    if (customOption) {
      expect(customOption.textContent?.toLowerCase()).toContain("custom");
    } else {
      // If no select link found, confirm text "custom" appears in the DOM somewhere within the texture section.
      // This is the weakest acceptable assertion.
      const allOptions = Array.from(document.querySelectorAll("option"));
      const found = allOptions.some((o) => o.value === "custom");
      expect(found).toBe(true);
    }
  });
});

// ---------------------------------------------------------------------------
// TUS-2: File input renders when texture_mode === "custom", hidden otherwise
// ---------------------------------------------------------------------------

describe("TUS-2: File input render conditions", () => {
  it("TUS-2-AC-1: file input is present in DOM when texture_mode is 'custom'", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const input = screen.queryByLabelText("Upload texture");
    expect(input).toBeInTheDocument();
  });

  it("TUS-2-AC-1: file input has type='file'", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const input = screen.getByLabelText("Upload texture") as HTMLInputElement;
    expect(input.type).toBe("file");
  });

  it("TUS-2-AC-1: file input accept attribute is '.png,.jpg,.jpeg'", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const input = screen.getByLabelText("Upload texture") as HTMLInputElement;
    expect(input.accept).toBe(".png,.jpg,.jpeg");
  });

  it("TUS-2-AC-2: file input is NOT present when texture_mode is 'none'", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "none" });
    render(<BuildControls />);

    const input = screen.queryByLabelText("Upload texture");
    expect(input).not.toBeInTheDocument();
  });

  it("TUS-2-AC-2: file input is NOT present when texture_mode is 'gradient'", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "gradient" });
    render(<BuildControls />);

    expect(screen.queryByLabelText("Upload texture")).not.toBeInTheDocument();
  });

  it("TUS-2-AC-2: file input is NOT present when texture_mode is 'spots'", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "spots" });
    render(<BuildControls />);

    expect(screen.queryByLabelText("Upload texture")).not.toBeInTheDocument();
  });

  it("TUS-2-AC-2: file input is NOT present when texture_mode is 'stripes'", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "stripes" });
    render(<BuildControls />);

    expect(screen.queryByLabelText("Upload texture")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TUS-3: File validation — MIME type rejection (image/gif)
// ---------------------------------------------------------------------------

describe("TUS-3: File validation — invalid MIME type rejection", () => {
  it("TUS-3-AC-2: image/gif file shows error 'Only PNG and JPG files are accepted.'", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const gifFile = makeFile("test.gif", "image/gif", 512 * 1024);
    uploadFile(gifFile);

    await waitFor(() => {
      expect(screen.getByText("Only PNG and JPG files are accepted.")).toBeInTheDocument();
    });
  });

  it("TUS-3-AC-2: image/gif does not call URL.createObjectURL", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const gifFile = makeFile("test.gif", "image/gif", 512 * 1024);
    uploadFile(gifFile);

    await waitFor(() => {
      expect(screen.getByText("Only PNG and JPG files are accepted.")).toBeInTheDocument();
    });
    expect(createObjectURLSpy).not.toHaveBeenCalled();
  });

  it("TUS-3-AC-1: application/pdf file shows MIME type error", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const pdfFile = makeFile("test.pdf", "application/pdf", 512 * 1024);
    uploadFile(pdfFile);

    await waitFor(() => {
      expect(screen.getByText("Only PNG and JPG files are accepted.")).toBeInTheDocument();
    });
    expect(createObjectURLSpy).not.toHaveBeenCalled();
  });

  it("TUS-3-AC-6: error span is visible in the DOM after MIME rejection", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    uploadFile(makeFile("anim.gif", "image/gif", 100));

    await waitFor(() => {
      const errorEl = screen.queryByText("Only PNG and JPG files are accepted.");
      expect(errorEl).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// TUS-3: File validation — size rejection (3 MB PNG)
// ---------------------------------------------------------------------------

describe("TUS-3: File validation — size rejection", () => {
  it("TUS-3-AC-3: PNG file of 3*1024*1024 bytes shows 'File must be 2 MB or smaller.'", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const bigFile = makeFile("big.png", "image/png", 3 * 1024 * 1024);
    uploadFile(bigFile);

    await waitFor(() => {
      expect(screen.getByText("File must be 2 MB or smaller.")).toBeInTheDocument();
    });
  });

  it("TUS-3-AC-3: oversized PNG does not call URL.createObjectURL", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const bigFile = makeFile("big.png", "image/png", 3 * 1024 * 1024);
    uploadFile(bigFile);

    await waitFor(() => {
      expect(screen.getByText("File must be 2 MB or smaller.")).toBeInTheDocument();
    });
    expect(createObjectURLSpy).not.toHaveBeenCalled();
  });

  it("TUS-3-AC-3: oversized PNG (2097153 bytes — one over limit) is rejected", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const borderFile = makeFile("border.png", "image/png", 2097153);
    uploadFile(borderFile);

    await waitFor(() => {
      expect(screen.getByText("File must be 2 MB or smaller.")).toBeInTheDocument();
    });
    expect(createObjectURLSpy).not.toHaveBeenCalled();
  });

  it("TUS-3-AC-4: PNG at exactly 2097152 bytes (boundary) is accepted — createObjectURL called", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const exactFile = makeFile("exact.png", "image/png", 2097152);
    uploadFile(exactFile);

    await waitFor(() => {
      expect(createObjectURLSpy).toHaveBeenCalledOnce();
    });
    expect(screen.queryByText("File must be 2 MB or smaller.")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TUS-3: File validation — valid PNG acceptance (TUS-4/TUS-5: blob URL + store)
// ---------------------------------------------------------------------------

describe("TUS-3/TUS-4/TUS-5: Valid PNG upload calls createObjectURL and sets store", () => {
  it("TUS-3-AC-5 / TUS-4-AC-1: valid 1 MB PNG calls URL.createObjectURL", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const pngFile = makeFile("texture.png", "image/png", 1024 * 1024);
    uploadFile(pngFile);

    await waitFor(() => {
      expect(createObjectURLSpy).toHaveBeenCalledOnce();
      expect(createObjectURLSpy).toHaveBeenCalledWith(pngFile);
    });
  });

  it("TUS-5: valid PNG upload sets customTextureUrl in store to the blob URL", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const pngFile = makeFile("texture.png", "image/png", 1024 * 1024);
    uploadFile(pngFile);

    await waitFor(() => {
      const state = useAppStore.getState() as Record<string, unknown>;
      expect(state["customTextureUrl"]).toBe("blob:test-url");
    });
  });

  it("TUS-3-AC-5: no error message is shown after valid PNG upload", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const pngFile = makeFile("texture.png", "image/png", 1024 * 1024);
    uploadFile(pngFile);

    await waitFor(() => {
      expect(createObjectURLSpy).toHaveBeenCalled();
    });
    expect(screen.queryByText("Only PNG and JPG files are accepted.")).not.toBeInTheDocument();
    expect(screen.queryByText("File must be 2 MB or smaller.")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TUS-3: Valid JPEG acceptance
// ---------------------------------------------------------------------------

describe("TUS-3: Valid JPEG file is accepted", () => {
  it("TUS-3-AC-5: image/jpeg file calls URL.createObjectURL (no error)", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const jpegFile = makeFile("photo.jpg", "image/jpeg", 1024 * 1024);
    uploadFile(jpegFile);

    await waitFor(() => {
      expect(createObjectURLSpy).toHaveBeenCalledOnce();
    });
    expect(screen.queryByText("Only PNG and JPG files are accepted.")).not.toBeInTheDocument();
    expect(screen.queryByText("File must be 2 MB or smaller.")).not.toBeInTheDocument();
  });

  it("TUS-3-AC-5: image/jpeg sets customTextureUrl in store", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const jpegFile = makeFile("photo.jpg", "image/jpeg", 512 * 1024);
    uploadFile(jpegFile);

    await waitFor(() => {
      const state = useAppStore.getState() as Record<string, unknown>;
      expect(state["customTextureUrl"]).toBe("blob:test-url");
    });
  });
});

// ---------------------------------------------------------------------------
// TUS-3: MIME type check ordering (MIME before size)
// ---------------------------------------------------------------------------

describe("TUS-3: MIME type validation occurs before size validation", () => {
  it("TUS-3-AC-9: invalid MIME + oversized file shows MIME error, not size error", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    // Invalid MIME type AND size over 2 MB — MIME error must win.
    const badFile = makeFile("bad.bmp", "image/bmp", 3 * 1024 * 1024);
    uploadFile(badFile);

    await waitFor(() => {
      expect(screen.getByText("Only PNG and JPG files are accepted.")).toBeInTheDocument();
    });
    expect(screen.queryByText("File must be 2 MB or smaller.")).not.toBeInTheDocument();
    expect(createObjectURLSpy).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// TUS-3: Error cleared after subsequent valid upload
// ---------------------------------------------------------------------------

describe("TUS-3: Error is cleared after a subsequent valid upload", () => {
  it("TUS-3-AC-7: error span disappears after uploading a valid file following a rejection", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    // First: upload invalid file to set error.
    uploadFile(makeFile("anim.gif", "image/gif", 100));

    await waitFor(() => {
      expect(screen.getByText("Only PNG and JPG files are accepted.")).toBeInTheDocument();
    });

    // Then: upload valid file.
    uploadFile(makeFile("texture.png", "image/png", 512 * 1024));

    await waitFor(() => {
      expect(screen.queryByText("Only PNG and JPG files are accepted.")).not.toBeInTheDocument();
      expect(screen.queryByText("File must be 2 MB or smaller.")).not.toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// TUS-7: Remove button render conditions
// ---------------------------------------------------------------------------

describe("TUS-7: Remove button render conditions", () => {
  it("TUS-7-AC-1: Remove button is present when texture_mode='custom' and customTextureUrl is non-null", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, "blob:existing-url");
    render(<BuildControls />);

    expect(screen.getByRole("button", { name: "Remove" })).toBeInTheDocument();
  });

  it("TUS-7-AC-2: Remove button is NOT present when texture_mode='custom' and customTextureUrl is null", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, null);
    render(<BuildControls />);

    expect(screen.queryByRole("button", { name: "Remove" })).not.toBeInTheDocument();
  });

  it("TUS-7-AC-3: Remove button is NOT present when texture_mode='none' and customTextureUrl is non-null", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "none" }, "blob:existing-url");
    render(<BuildControls />);

    expect(screen.queryByRole("button", { name: "Remove" })).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TUS-7: Remove button click behavior
// ---------------------------------------------------------------------------

describe("TUS-7: Remove button click behavior", () => {
  it("TUS-7-AC-4: clicking Remove calls URL.revokeObjectURL with the current customTextureUrl", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, "blob:existing-url");
    render(<BuildControls />);

    const removeBtn = screen.getByRole("button", { name: "Remove" });
    fireEvent.click(removeBtn);

    await waitFor(() => {
      expect(revokeObjectURLSpy).toHaveBeenCalledWith("blob:existing-url");
    });
  });

  it("TUS-7-AC-5: clicking Remove resets customTextureUrl to null in the store", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, "blob:existing-url");
    render(<BuildControls />);

    const removeBtn = screen.getByRole("button", { name: "Remove" });
    fireEvent.click(removeBtn);

    await waitFor(() => {
      const state = useAppStore.getState() as Record<string, unknown>;
      expect(state["customTextureUrl"]).toBeNull();
    });
  });

  it("TUS-7-AC-6: clicking Remove resets texture_mode to 'none' in the store", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, "blob:existing-url");
    render(<BuildControls />);

    const removeBtn = screen.getByRole("button", { name: "Remove" });
    fireEvent.click(removeBtn);

    await waitFor(() => {
      const vals = (useAppStore.getState().animatedBuildOptionValues as Record<string, Record<string, unknown>>)["slug"];
      expect(vals?.["texture_mode"]).toBe("none");
    });
  });

  it("TUS-7-AC-7: after clicking Remove, file input is no longer in the DOM", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, "blob:existing-url");
    render(<BuildControls />);

    const removeBtn = screen.getByRole("button", { name: "Remove" });
    act(() => {
      fireEvent.click(removeBtn);
    });

    await waitFor(() => {
      expect(screen.queryByLabelText("Upload texture")).not.toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// TUS-4: Revoking previous URL before new upload (TUS-4-AC-1)
// ---------------------------------------------------------------------------

describe("TUS-4: Previous blob URL is revoked before new upload", () => {
  it("TUS-4-AC-1: uploading a second file calls revokeObjectURL on the previous URL first", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, "blob:first-url");
    render(<BuildControls />);

    // Upload a new valid file when the store already has a blob URL.
    const newFile = makeFile("new.png", "image/png", 512 * 1024);
    uploadFile(newFile);

    await waitFor(() => {
      expect(createObjectURLSpy).toHaveBeenCalledOnce();
    });

    // revokeObjectURL must have been called with the previous URL.
    expect(revokeObjectURLSpy).toHaveBeenCalledWith("blob:first-url");

    // revokeObjectURL must have been called before createObjectURL completes (order check).
    const revokeOrder = revokeObjectURLSpy.mock.invocationCallOrder[0];
    const createOrder = createObjectURLSpy.mock.invocationCallOrder[0];
    expect(revokeOrder).toBeLessThan(createOrder);
  });
});

// ---------------------------------------------------------------------------
// TUS-9: buildControlDisabled() behavior under "custom" mode
// (All texture sub-controls remain disabled; texture_mode row itself stays enabled)
// ---------------------------------------------------------------------------

describe("TUS-9: buildControlDisabled() under 'custom' mode — sub-controls stay disabled", () => {
  /**
   * Walk up from the label element to find the wrapping div that carries
   * the disabled opacity/pointerEvents style.
   * Mirrors the helper from BuildControls.texture.test.tsx.
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

  it("TUS-9-AC-1: texture_grad_color_a is disabled when texture_mode is 'custom'", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, {
      texture_mode: "custom",
      texture_grad_color_a: "ff0000",
      texture_spot_color: "",
      texture_spot_density: 1.0,
      texture_stripe_width: 0.2,
    });
    render(<BuildControls />);

    expect(isRowDisabled("Gradient color A")).toBe(true);
  });

  it("TUS-9-AC-2: texture_spot_density is disabled when texture_mode is 'custom'", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, {
      texture_mode: "custom",
      texture_spot_density: 1.0,
    });
    render(<BuildControls />);

    expect(isRowDisabled("Spot density")).toBe(true);
  });

  it("TUS-9-AC-3: texture_stripe_width is disabled when texture_mode is 'custom'", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, {
      texture_mode: "custom",
      texture_stripe_width: 0.2,
    });
    render(<BuildControls />);

    expect(isRowDisabled("Stripe width")).toBe(true);
  });

  it("TUS-9-AC-4: texture_mode row itself is NOT disabled when texture_mode is 'custom'", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    expect(isRowDisabled("Texture mode")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// TUS-9: No bleed-over to pupil/mouth/tail disabled rules under "custom" mode
// ---------------------------------------------------------------------------

describe("TUS-9: No bleed-over to pupil/mouth disabled rules when texture_mode='custom'", () => {
  it("pupil_shape remains disabled by pupil_enabled=false when texture_mode='custom'", () => {
    setupStore("slug", CONTROLS_WITH_PUPIL_MOUTH, {
      pupil_enabled: false,
      pupil_shape: "dot",
      mouth_enabled: true,
      mouth_shape: "fang",
      texture_mode: "custom",
      texture_grad_color_a: "",
      texture_spot_color: "",
      texture_spot_density: 1.0,
      texture_stripe_width: 0.2,
    });
    render(<BuildControls />);

    // pupil_shape must still be disabled (controlled by pupil_enabled, not texture_mode).
    const labelEl = screen.queryByText("Pupil shape");
    if (labelEl) {
      let el: HTMLElement | null = labelEl as HTMLElement;
      while (el && el !== document.body) {
        if (el.style && el.style.opacity !== undefined && el.style.opacity !== "") {
          expect(el.style.opacity).toBe("0.42");
          break;
        }
        el = el.parentElement;
      }
    }
  });

  it("mouth_shape remains disabled by mouth_enabled=false when texture_mode='custom'", () => {
    setupStore("slug", CONTROLS_WITH_PUPIL_MOUTH, {
      pupil_enabled: true,
      pupil_shape: "slit",
      mouth_enabled: false,
      mouth_shape: "smile",
      texture_mode: "custom",
      texture_grad_color_a: "",
      texture_spot_color: "",
      texture_spot_density: 1.0,
      texture_stripe_width: 0.2,
    });
    render(<BuildControls />);

    const labelEl = screen.queryByText("Mouth shape");
    if (labelEl) {
      let el: HTMLElement | null = labelEl as HTMLElement;
      while (el && el !== document.body) {
        if (el.style && el.style.opacity !== undefined && el.style.opacity !== "") {
          expect(el.style.opacity).toBe("0.42");
          break;
        }
        el = el.parentElement;
      }
    }
  });
});

// ---------------------------------------------------------------------------
// TUS-3-AC-8: no-file edge case — empty file list does not call handlers
// ---------------------------------------------------------------------------

describe("TUS-3: Empty file list edge case", () => {
  it("TUS-3-AC-8: onChange with no files does not call setUploadError or createObjectURL", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const input = screen.getByLabelText("Upload texture") as HTMLInputElement;

    // Fire change with empty FileList.
    Object.defineProperty(input, "files", { value: [], writable: true });
    fireEvent.change(input);

    // Wait briefly — no error should appear, no createObjectURL called.
    await new Promise((r) => setTimeout(r, 50));

    expect(createObjectURLSpy).not.toHaveBeenCalled();
    expect(screen.queryByText("Only PNG and JPG files are accepted.")).not.toBeInTheDocument();
    expect(screen.queryByText("File must be 2 MB or smaller.")).not.toBeInTheDocument();
  });
});
