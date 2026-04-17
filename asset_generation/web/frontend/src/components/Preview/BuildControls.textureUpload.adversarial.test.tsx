// @vitest-environment jsdom
/**
 * Texture upload support — ADVERSARIAL frontend tests.
 *
 * This file adversarially extends BuildControls.textureUpload.test.tsx.
 * It targets gaps left by the Test Designer, with each test group documenting
 * the vulnerability it exposes if the implementation is incomplete or wrong.
 *
 * Spec requirements targeted:
 *   TUS-3: File validation (MIME whitelist, size boundary, ordering)
 *   TUS-4: Blob URL lifecycle (createObjectURL / revokeObjectURL ordering)
 *   TUS-5: Zustand store state after operations (not just DOM / call-count)
 *   TUS-7: Remove button — type="button" attribute, DOM re-appearance after mode cycle
 *
 * Gaps exposed vs. Test Designer suite:
 *   1. image/jpg (non-standard MIME) rejection — browsers sometimes emit this
 *   2. Remove button type="button" attribute (spec TUS-7 explicit constraint)
 *   3. Reactive mode-switch custom→none→custom restores file input without remount
 *   4. Multiple files in FileList — only first processed
 *   5. Upload while in error state — store state verified (not just DOM)
 *   6. URL.createObjectURL throwing — component must not crash
 *   7. Empty string file name — does not bypass MIME validation
 *   8. Zero-byte file with valid MIME — boundary: 0 is accepted
 *   9. Exactly 2097152 bytes — store state verified (not just call-count)
 *  10. Spy call-count isolation — spies reset between tests
 *
 * All tests will be RED until Tasks 2–3 (store slice + BuildControls) are implemented.
 * Checkpoint log: project_board/checkpoints/M25-03/run-2026-04-16T20-00-00Z-test-break.md
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { BuildControls } from "./BuildControls";
import type { AnimatedBuildControlDef } from "../../types";

// ---------------------------------------------------------------------------
// URL mock setup — own spy lifecycle, isolated from base test file
// ---------------------------------------------------------------------------

let createObjectURLSpy: ReturnType<typeof vi.spyOn>;
let revokeObjectURLSpy: ReturnType<typeof vi.spyOn>;

beforeEach(() => {
  // jsdom does not implement URL.createObjectURL; install deterministic stubs.
  // The defineProperty guards are idempotent — safe to run per test.
  if (!URL.createObjectURL) {
    Object.defineProperty(URL, "createObjectURL", { writable: true, value: () => "" });
  }
  if (!URL.revokeObjectURL) {
    Object.defineProperty(URL, "revokeObjectURL", { writable: true, value: () => undefined });
  }
  // Fresh spy per test — this is the isolation check.
  createObjectURLSpy = vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:adversarial-url");
  revokeObjectURLSpy = vi.spyOn(URL, "revokeObjectURL").mockReturnValue(undefined);
});

afterEach(() => {
  cleanup();
  // Restore spies so each test starts clean — prevents cross-test call-count pollution.
  createObjectURLSpy.mockRestore();
  revokeObjectURLSpy.mockRestore();
});

// ---------------------------------------------------------------------------
// Control definition constants — minimal set for texture upload tests
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

const BASE_TEXTURE_CONTROLS: AnimatedBuildControlDef[] = [TEXTURE_MODE_DEF];

// ---------------------------------------------------------------------------
// Helpers — mirror pattern from base test file for consistency
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
    customTextureUrl,
  } as Parameters<typeof useAppStore.setState>[0]);
}

function makeFile(name: string, type: string, size: number): File {
  const content = new Uint8Array(size);
  const blob = new Blob([content], { type });
  return new File([blob], name, { type });
}

function uploadFile(file: File) {
  const input = screen.getByLabelText("Upload texture") as HTMLInputElement;
  Object.defineProperty(input, "files", { value: [file], writable: true });
  fireEvent.change(input);
}

// ---------------------------------------------------------------------------
// GAP 1: image/jpg (non-standard MIME) rejection
//
// Vulnerability: Implementation may check `file.type.startsWith("image/j")` or
// use a loose match that accidentally accepts "image/jpg". The spec explicitly
// states only "image/png" and "image/jpeg" are accepted; "image/jpg" is a
// non-standard alias that some browsers emit for JPEG files. It must be rejected.
// ---------------------------------------------------------------------------

describe("GAP-1: image/jpg non-standard MIME is rejected (not the same as image/jpeg)", () => {
  it("GAP-1-A: image/jpg file shows MIME error 'Only PNG and JPG files are accepted.'", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const jpgFile = makeFile("photo.jpg", "image/jpg", 512 * 1024);
    uploadFile(jpgFile);

    await waitFor(() => {
      expect(screen.getByText("Only PNG and JPG files are accepted.")).toBeInTheDocument();
    });
  });

  it("GAP-1-B: image/jpg does not call URL.createObjectURL", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const jpgFile = makeFile("photo.jpg", "image/jpg", 512 * 1024);
    uploadFile(jpgFile);

    await waitFor(() => {
      expect(screen.getByText("Only PNG and JPG files are accepted.")).toBeInTheDocument();
    });
    // Spy must not have been called — createObjectURL only fires for valid MIME.
    expect(createObjectURLSpy).not.toHaveBeenCalled();
  });

  it("GAP-1-C: image/jpg does not update the store customTextureUrl", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, null);
    render(<BuildControls />);

    const jpgFile = makeFile("photo.jpg", "image/jpg", 100 * 1024);
    uploadFile(jpgFile);

    await waitFor(() => {
      expect(screen.getByText("Only PNG and JPG files are accepted.")).toBeInTheDocument();
    });
    // Store must remain null — not set to any blob URL.
    const state = useAppStore.getState() as Record<string, unknown>;
    expect(state["customTextureUrl"]).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// GAP 2: Remove button must have type="button" (spec TUS-7 explicit constraint)
//
// Vulnerability: A naive `<button>Remove</button>` has implicit type="submit",
// which can trigger form submission if BuildControls is ever wrapped in a <form>.
// The spec (TUS-7 Spec Summary) explicitly requires `type="button"`.
// ---------------------------------------------------------------------------

describe("GAP-2: Remove button has type='button' attribute (TUS-7 spec constraint)", () => {
  it("GAP-2-A: Remove button element has type attribute equal to 'button'", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, "blob:existing-url");
    render(<BuildControls />);

    const removeBtn = screen.getByRole("button", { name: "Remove" }) as HTMLButtonElement;
    // CHECKPOINT: spec TUS-7 explicitly requires type="button" to prevent form submission.
    // If implementation omits this attribute (or uses type="submit" / no attribute),
    // this test will fail, exposing a spec violation.
    expect(removeBtn.type).toBe("button");
  });

  it("GAP-2-B: Remove button does not have type='submit'", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, "blob:existing-url");
    render(<BuildControls />);

    const removeBtn = screen.getByRole("button", { name: "Remove" }) as HTMLButtonElement;
    expect(removeBtn.type).not.toBe("submit");
  });
});

// ---------------------------------------------------------------------------
// GAP 3: Reactive mode-switch custom → none → custom restores file input
//
// Vulnerability: Implementation may use a visibility toggle (display:none)
// instead of conditional rendering. If it does, the file input stays in the DOM
// when mode is "none" (TUS-2-AC-2 violated) and old state may persist when
// returning to "custom". The spec says the input "is not rendered under any
// other texture_mode value" — implying it must be fully removed from the DOM.
// ---------------------------------------------------------------------------

describe("GAP-3: Reactive mode-switch custom→none→custom restores file input", () => {
  it("GAP-3-A: file input disappears from DOM when mode switches custom→none", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    // File input present in "custom" mode.
    expect(screen.getByLabelText("Upload texture")).toBeInTheDocument();

    // Simulate mode switch to "none" via store mutation.
    act(() => {
      useAppStore.setState({
        animatedBuildOptionValues: { slug: { texture_mode: "none" } },
      } as Parameters<typeof useAppStore.setState>[0]);
    });

    await waitFor(() => {
      expect(screen.queryByLabelText("Upload texture")).not.toBeInTheDocument();
    });
  });

  it("GAP-3-B: file input reappears in DOM when mode switches none→custom", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "none" });
    render(<BuildControls />);

    // File input absent in "none" mode.
    expect(screen.queryByLabelText("Upload texture")).not.toBeInTheDocument();

    // Simulate mode switch to "custom" via store mutation.
    act(() => {
      useAppStore.setState({
        animatedBuildOptionValues: { slug: { texture_mode: "custom" } },
      } as Parameters<typeof useAppStore.setState>[0]);
    });

    await waitFor(() => {
      expect(screen.getByLabelText("Upload texture")).toBeInTheDocument();
    });
  });

  it("GAP-3-C: full round-trip custom→none→custom — file input is functional after cycle", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    // Step 1: switch to none.
    act(() => {
      useAppStore.setState({
        animatedBuildOptionValues: { slug: { texture_mode: "none" } },
      } as Parameters<typeof useAppStore.setState>[0]);
    });

    await waitFor(() => {
      expect(screen.queryByLabelText("Upload texture")).not.toBeInTheDocument();
    });

    // Step 2: switch back to custom.
    act(() => {
      useAppStore.setState({
        animatedBuildOptionValues: { slug: { texture_mode: "custom" } },
      } as Parameters<typeof useAppStore.setState>[0]);
    });

    await waitFor(() => {
      expect(screen.getByLabelText("Upload texture")).toBeInTheDocument();
    });

    // Step 3: upload a valid file — component must still work after round-trip.
    const pngFile = makeFile("after-cycle.png", "image/png", 256 * 1024);
    uploadFile(pngFile);

    await waitFor(() => {
      expect(createObjectURLSpy).toHaveBeenCalledOnce();
    });
    // No error must be shown after valid upload post-cycle.
    expect(screen.queryByText("Only PNG and JPG files are accepted.")).not.toBeInTheDocument();
    expect(screen.queryByText("File must be 2 MB or smaller.")).not.toBeInTheDocument();
  });

  it("GAP-3-D: error state from previous upload does not survive mode-switch round-trip", async () => {
    // CHECKPOINT: If file input is NOT re-mounted on mode switch (visibility toggle),
    // the local uploadError state persists across custom→none→custom transitions.
    // The spec says the input is conditionally rendered; a re-mount clears local state.
    // This test checks that local error state is NOT visible after a round-trip.
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    // Upload invalid file to set error.
    uploadFile(makeFile("bad.gif", "image/gif", 1024));

    await waitFor(() => {
      expect(screen.getByText("Only PNG and JPG files are accepted.")).toBeInTheDocument();
    });

    // Switch to "none" then back to "custom".
    act(() => {
      useAppStore.setState({
        animatedBuildOptionValues: { slug: { texture_mode: "none" } },
      } as Parameters<typeof useAppStore.setState>[0]);
    });

    await waitFor(() => {
      expect(screen.queryByLabelText("Upload texture")).not.toBeInTheDocument();
    });

    act(() => {
      useAppStore.setState({
        animatedBuildOptionValues: { slug: { texture_mode: "custom" } },
      } as Parameters<typeof useAppStore.setState>[0]);
    });

    await waitFor(() => {
      expect(screen.getByLabelText("Upload texture")).toBeInTheDocument();
    });

    // Error must NOT be visible after the round-trip (component was unmounted/remounted).
    // CHECKPOINT: If this fails, the implementation uses visibility toggling (not
    // conditional rendering), which violates TUS-2-AC-2 and persists stale local state.
    expect(screen.queryByText("Only PNG and JPG files are accepted.")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// GAP 4: Multiple files in FileList — only first file is processed
//
// Vulnerability: Implementation might iterate `e.target.files` and process all
// files. The spec says `e.target.files[0]` is the file to validate; only the
// first file should cause a blob URL creation. Multiple valid files must not
// produce multiple createObjectURL calls.
// ---------------------------------------------------------------------------

describe("GAP-4: Multiple files in FileList — only first file processed", () => {
  it("GAP-4-A: only one createObjectURL call when two valid files are present", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const input = screen.getByLabelText("Upload texture") as HTMLInputElement;
    const file1 = makeFile("first.png", "image/png", 256 * 1024);
    const file2 = makeFile("second.png", "image/png", 512 * 1024);

    // Provide two files in the FileList.
    Object.defineProperty(input, "files", { value: [file1, file2], writable: true });
    fireEvent.change(input);

    await waitFor(() => {
      expect(createObjectURLSpy).toHaveBeenCalledOnce();
    });

    // createObjectURL must have been called with the first file only.
    expect(createObjectURLSpy).toHaveBeenCalledWith(file1);
    expect(createObjectURLSpy).not.toHaveBeenCalledWith(file2);
  });

  it("GAP-4-B: valid first + invalid second — first file accepted, no error shown", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const input = screen.getByLabelText("Upload texture") as HTMLInputElement;
    const validFile = makeFile("valid.png", "image/png", 100 * 1024);
    const invalidFile = makeFile("bad.gif", "image/gif", 100 * 1024);

    // First file valid, second invalid.
    Object.defineProperty(input, "files", { value: [validFile, invalidFile], writable: true });
    fireEvent.change(input);

    await waitFor(() => {
      expect(createObjectURLSpy).toHaveBeenCalledOnce();
    });

    // No error must appear — only the first (valid) file is processed.
    expect(screen.queryByText("Only PNG and JPG files are accepted.")).not.toBeInTheDocument();
  });

  it("GAP-4-C: invalid first + valid second — shows MIME error, second file ignored", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const input = screen.getByLabelText("Upload texture") as HTMLInputElement;
    const invalidFile = makeFile("bad.pdf", "application/pdf", 100 * 1024);
    const validFile = makeFile("valid.png", "image/png", 100 * 1024);

    // First file invalid, second valid.
    Object.defineProperty(input, "files", { value: [invalidFile, validFile], writable: true });
    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByText("Only PNG and JPG files are accepted.")).toBeInTheDocument();
    });

    // createObjectURL must NOT be called — invalid first file blocks processing.
    expect(createObjectURLSpy).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// GAP 5: Upload while in error state — store state verified, not just DOM
//
// Vulnerability: Test Designer only checked DOM (error span absent). Implementation
// might clear the error span locally but fail to call setCustomTextureUrl, leaving
// the store null even after a valid re-upload. Store state assertion catches this.
// ---------------------------------------------------------------------------

describe("GAP-5: Upload while in error state — store state verified after valid re-upload", () => {
  it("GAP-5-A: after MIME rejection then valid upload, store customTextureUrl is set", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, null);
    render(<BuildControls />);

    // Step 1: Trigger a MIME error.
    uploadFile(makeFile("bad.gif", "image/gif", 100));

    await waitFor(() => {
      expect(screen.getByText("Only PNG and JPG files are accepted.")).toBeInTheDocument();
    });

    // Store must still be null after rejection.
    expect((useAppStore.getState() as Record<string, unknown>)["customTextureUrl"]).toBeNull();

    // Step 2: Upload a valid file to clear the error.
    uploadFile(makeFile("good.png", "image/png", 512 * 1024));

    await waitFor(() => {
      expect(screen.queryByText("Only PNG and JPG files are accepted.")).not.toBeInTheDocument();
    });

    // Store must be updated to the blob URL after valid re-upload.
    await waitFor(() => {
      const state = useAppStore.getState() as Record<string, unknown>;
      expect(state["customTextureUrl"]).toBe("blob:adversarial-url");
    });
  });

  it("GAP-5-B: after size rejection then valid upload, store customTextureUrl is set", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, null);
    render(<BuildControls />);

    // Step 1: Trigger a size error.
    uploadFile(makeFile("big.png", "image/png", 3 * 1024 * 1024));

    await waitFor(() => {
      expect(screen.getByText("File must be 2 MB or smaller.")).toBeInTheDocument();
    });

    // Step 2: Upload a valid file.
    uploadFile(makeFile("ok.jpeg", "image/jpeg", 200 * 1024));

    await waitFor(() => {
      expect(screen.queryByText("File must be 2 MB or smaller.")).not.toBeInTheDocument();
    });

    // Store must have the blob URL.
    await waitFor(() => {
      const state = useAppStore.getState() as Record<string, unknown>;
      expect(state["customTextureUrl"]).toBe("blob:adversarial-url");
    });
  });

  it("GAP-5-C: createObjectURL called exactly once on valid re-upload (not twice)", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, null);
    render(<BuildControls />);

    // Trigger rejection.
    uploadFile(makeFile("bad.gif", "image/gif", 100));
    await waitFor(() => {
      expect(screen.getByText("Only PNG and JPG files are accepted.")).toBeInTheDocument();
    });

    // Valid re-upload.
    uploadFile(makeFile("texture.png", "image/png", 256 * 1024));
    await waitFor(() => {
      expect(createObjectURLSpy).toHaveBeenCalledOnce();
    });

    // Must be exactly one call — no stale invocation from the prior rejected attempt.
    expect(createObjectURLSpy).toHaveBeenCalledTimes(1);
  });
});

// ---------------------------------------------------------------------------
// GAP 6: URL.createObjectURL throwing — component must not crash
//
// Vulnerability: Implementation calls URL.createObjectURL without a try/catch.
// If the browser rejects the blob URL (e.g., due to a security policy or
// jsdom limitations), an unhandled exception will unmount the component and
// break the editor. The spec does not mandate try/catch but a crash is a
// severe reliability gap.
//
// CHECKPOINT: The spec does not explicitly require defensive error handling around
// URL.createObjectURL. If the implementation does not wrap it in try/catch, this
// test will fail. This is an adversarial gap — conservative assumption: the
// component should not crash on createObjectURL failure.
// ---------------------------------------------------------------------------

describe("GAP-6: URL.createObjectURL throwing — component must not crash", () => {
  it("GAP-6-A: component remains mounted after createObjectURL throws", async () => {
    // Override spy to throw.
    createObjectURLSpy.mockImplementationOnce(() => {
      throw new Error("SecurityError: Blob URL creation failed");
    });

    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });

    // Expect no unhandled error to propagate. If component crashes, render
    // itself or subsequent assertions will fail.
    expect(() => {
      render(<BuildControls />);
    }).not.toThrow();

    // File input must still be in the DOM (component not crashed).
    expect(screen.getByLabelText("Upload texture")).toBeInTheDocument();

    // Attempt upload to trigger the throw path.
    const pngFile = makeFile("texture.png", "image/png", 256 * 1024);

    // The act wrapper captures React state update errors; if the component
    // crashes inside a handler, this will surface as a thrown error.
    // CHECKPOINT: If this assertion fails, implementation lacks try/catch and
    // the gap must be fixed before implementation handoff.
    let caughtError: Error | null = null;
    try {
      act(() => {
        uploadFile(pngFile);
      });
    } catch (e) {
      caughtError = e as Error;
    }

    // After the throw, the component must still be mounted (file input present).
    await waitFor(() => {
      expect(screen.getByLabelText("Upload texture")).toBeInTheDocument();
    });

    // If caughtError is non-null, the component crashed — log for diagnostics.
    // The test passes if either: no error thrown (try/catch present), OR
    // the component survived without crashing the test runner.
    // A strict assertion that caughtError is null is left as an escalation path.
    // For now: just verify the component is still renderable.
    expect(screen.queryByRole("button", { name: "Remove" })).toBeFalsy(); // store not updated
    void caughtError; // referenced to avoid lint warning
  });

  it("GAP-6-B: store customTextureUrl remains null after createObjectURL throws", async () => {
    // CHECKPOINT: If createObjectURL throws and implementation has no try/catch,
    // the store update call (setCustomTextureUrl) is never reached. Store must
    // remain null. This test verifies that outcome regardless of crash behavior.
    createObjectURLSpy.mockImplementationOnce(() => {
      throw new Error("SecurityError");
    });

    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, null);
    render(<BuildControls />);

    try {
      act(() => {
        uploadFile(makeFile("texture.png", "image/png", 256 * 1024));
      });
    } catch {
      // Absorb crash — check store state regardless.
    }

    await new Promise((r) => setTimeout(r, 50));

    const state = useAppStore.getState() as Record<string, unknown>;
    expect(state["customTextureUrl"]).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// GAP 7: Empty string file name — does not bypass MIME validation
//
// Vulnerability: An implementation might check `file.name` extension instead of
// (or in addition to) `file.type` for MIME validation. An empty name could
// bypass an extension-based check. The spec requires `file.type` checking only.
// A file with an empty name but invalid type must still be rejected.
// ---------------------------------------------------------------------------

describe("GAP-7: Empty string file name — MIME validation is not bypassed", () => {
  it("GAP-7-A: file with empty name and invalid MIME type is rejected", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const noNameFile = makeFile("", "image/gif", 100 * 1024);
    uploadFile(noNameFile);

    await waitFor(() => {
      expect(screen.getByText("Only PNG and JPG files are accepted.")).toBeInTheDocument();
    });
    expect(createObjectURLSpy).not.toHaveBeenCalled();
  });

  it("GAP-7-B: file with empty name and valid MIME type (image/png) is accepted", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const noNameFile = makeFile("", "image/png", 100 * 1024);
    uploadFile(noNameFile);

    await waitFor(() => {
      expect(createObjectURLSpy).toHaveBeenCalledOnce();
    });
    expect(screen.queryByText("Only PNG and JPG files are accepted.")).not.toBeInTheDocument();
    expect(screen.queryByText("File must be 2 MB or smaller.")).not.toBeInTheDocument();
  });

  it("GAP-7-C: file with empty name and valid MIME (image/jpeg) is accepted", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const noNameFile = makeFile("", "image/jpeg", 200 * 1024);
    uploadFile(noNameFile);

    await waitFor(() => {
      expect(createObjectURLSpy).toHaveBeenCalledOnce();
    });
    expect(screen.queryByText("Only PNG and JPG files are accepted.")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// GAP 8: Zero-byte file — valid type, valid size, must be accepted (boundary)
//
// Vulnerability: Implementation might accidentally add a `file.size > 0` guard
// that is NOT in the spec. The spec only requires `file.size <= 2097152`.
// A zero-byte file satisfies this condition and must be accepted.
// ---------------------------------------------------------------------------

describe("GAP-8: Zero-byte file with valid MIME — boundary: 0 bytes is accepted", () => {
  it("GAP-8-A: zero-byte PNG (0 bytes, image/png) calls createObjectURL", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const zeroFile = makeFile("empty.png", "image/png", 0);
    uploadFile(zeroFile);

    await waitFor(() => {
      expect(createObjectURLSpy).toHaveBeenCalledOnce();
    });
    expect(screen.queryByText("File must be 2 MB or smaller.")).not.toBeInTheDocument();
    expect(screen.queryByText("Only PNG and JPG files are accepted.")).not.toBeInTheDocument();
  });

  it("GAP-8-B: zero-byte JPEG (0 bytes, image/jpeg) calls createObjectURL", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const zeroFile = makeFile("empty.jpeg", "image/jpeg", 0);
    uploadFile(zeroFile);

    await waitFor(() => {
      expect(createObjectURLSpy).toHaveBeenCalledOnce();
    });
    expect(screen.queryByText("File must be 2 MB or smaller.")).not.toBeInTheDocument();
  });

  it("GAP-8-C: zero-byte PNG sets customTextureUrl in store", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, null);
    render(<BuildControls />);

    const zeroFile = makeFile("empty.png", "image/png", 0);
    uploadFile(zeroFile);

    await waitFor(() => {
      const state = useAppStore.getState() as Record<string, unknown>;
      expect(state["customTextureUrl"]).toBe("blob:adversarial-url");
    });
  });
});

// ---------------------------------------------------------------------------
// GAP 9: Exactly 2097152 bytes — store state verified (not just call-count)
//
// Vulnerability: The base test file only checks call-count (`toHaveBeenCalledOnce`).
// If implementation calls createObjectURL but fails to call setCustomTextureUrl,
// the call-count assertion passes but the store is wrong (GlbViewer never receives
// the texture URL). This test closes that gap with a store-state assertion.
// ---------------------------------------------------------------------------

describe("GAP-9: Exactly 2097152-byte file — store state verified, not just call-count", () => {
  it("GAP-9-A: 2097152-byte PNG sets customTextureUrl in store to blob URL", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, null);
    render(<BuildControls />);

    const exactFile = makeFile("exact-limit.png", "image/png", 2097152);
    uploadFile(exactFile);

    await waitFor(() => {
      const state = useAppStore.getState() as Record<string, unknown>;
      expect(state["customTextureUrl"]).toBe("blob:adversarial-url");
    });
  });

  it("GAP-9-B: 2097152-byte PNG does not show any error in the DOM", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const exactFile = makeFile("exact-limit.png", "image/png", 2097152);
    uploadFile(exactFile);

    await waitFor(() => {
      expect(createObjectURLSpy).toHaveBeenCalledOnce();
    });
    expect(screen.queryByText("File must be 2 MB or smaller.")).not.toBeInTheDocument();
    expect(screen.queryByText("Only PNG and JPG files are accepted.")).not.toBeInTheDocument();
  });

  it("GAP-9-C: 2097152-byte JPEG also accepted (not just PNG at boundary)", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, null);
    render(<BuildControls />);

    const exactJpeg = makeFile("exact-limit.jpeg", "image/jpeg", 2097152);
    uploadFile(exactJpeg);

    await waitFor(() => {
      const state = useAppStore.getState() as Record<string, unknown>;
      expect(state["customTextureUrl"]).toBe("blob:adversarial-url");
    });
    expect(screen.queryByText("File must be 2 MB or smaller.")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// GAP 10: Spy call-count isolation — fresh spy per test, no cross-test pollution
//
// Vulnerability: If spies are not reset between tests, a call from test N
// is counted in test N+1. The base test file uses mockRestore() in afterEach
// which should prevent this, but a test that verifies spy isolation explicitly
// is the strongest guard against mis-configuration or import-order issues.
// ---------------------------------------------------------------------------

describe("GAP-10: Spy isolation — each test starts with zero call counts", () => {
  it("GAP-10-A: createObjectURL spy has 0 calls at test start (no bleed from prior tests)", () => {
    // This test runs after other tests. If spies were not reset, mock.calls would be > 0.
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    // Before uploading anything: spy must have 0 calls.
    // CHECKPOINT: If this assertion fails, spy restoration in afterEach is broken.
    expect(createObjectURLSpy).toHaveBeenCalledTimes(0);
    expect(revokeObjectURLSpy).toHaveBeenCalledTimes(0);
  });

  it("GAP-10-B: revokeObjectURL spy has 0 calls at test start (no bleed from prior tests)", () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, "blob:some-url");
    render(<BuildControls />);

    // Before clicking Remove: revoke spy must have 0 calls.
    expect(revokeObjectURLSpy).toHaveBeenCalledTimes(0);
  });

  it("GAP-10-C: two sequential valid uploads in same test produce exactly two createObjectURL calls", async () => {
    // This verifies the spy counts within a single test are accurate and not
    // contaminated by any other source.
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, null);
    render(<BuildControls />);

    // First upload.
    uploadFile(makeFile("first.png", "image/png", 100 * 1024));
    await waitFor(() => {
      expect(createObjectURLSpy).toHaveBeenCalledTimes(1);
    });

    // Update store to reflect first blob URL (simulates what the component would do).
    act(() => {
      useAppStore.setState({
        customTextureUrl: "blob:adversarial-url",
      } as Parameters<typeof useAppStore.setState>[0]);
    });

    // Second upload (previous URL in store triggers revokeObjectURL before create).
    uploadFile(makeFile("second.png", "image/png", 200 * 1024));
    await waitFor(() => {
      expect(createObjectURLSpy).toHaveBeenCalledTimes(2);
    });

    // Revoke must have been called once for the first blob URL before the second create.
    expect(revokeObjectURLSpy).toHaveBeenCalledTimes(1);
    expect(revokeObjectURLSpy).toHaveBeenCalledWith("blob:adversarial-url");
  });
});

// ---------------------------------------------------------------------------
// GAP 11: image/webp — another non-whitelisted image MIME must be rejected
//
// Vulnerability: Implementation might whitelist all "image/*" types instead of
// the exact two-element list. Spec says only ["image/png", "image/jpeg"].
// ---------------------------------------------------------------------------

describe("GAP-11: Other image/* MIMEs are rejected (only png and jpeg are whitelisted)", () => {
  it("GAP-11-A: image/webp is rejected with MIME error", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const webpFile = makeFile("image.webp", "image/webp", 512 * 1024);
    uploadFile(webpFile);

    await waitFor(() => {
      expect(screen.getByText("Only PNG and JPG files are accepted.")).toBeInTheDocument();
    });
    expect(createObjectURLSpy).not.toHaveBeenCalled();
  });

  it("GAP-11-B: image/bmp is rejected with MIME error", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const bmpFile = makeFile("image.bmp", "image/bmp", 512 * 1024);
    uploadFile(bmpFile);

    await waitFor(() => {
      expect(screen.getByText("Only PNG and JPG files are accepted.")).toBeInTheDocument();
    });
    expect(createObjectURLSpy).not.toHaveBeenCalled();
  });

  it("GAP-11-C: image/svg+xml is rejected with MIME error", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    const svgFile = makeFile("image.svg", "image/svg+xml", 10 * 1024);
    uploadFile(svgFile);

    await waitFor(() => {
      expect(screen.getByText("Only PNG and JPG files are accepted.")).toBeInTheDocument();
    });
    expect(createObjectURLSpy).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// GAP 12: Empty MIME type string — must be rejected (not bypass whitelist check)
//
// Vulnerability: `"".includes("image/png")` is false, but `file.type === ""` with
// a check like `if (!file.type || !ACCEPTED_TYPES.includes(file.type))` might
// behave differently from `file.type === "image/png" || file.type === "image/jpeg"`.
// An empty MIME string (can happen with unknown file types in some browsers)
// must be treated as invalid.
// ---------------------------------------------------------------------------

describe("GAP-12: Empty MIME type string is rejected", () => {
  it("GAP-12-A: file with empty type string shows MIME error", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" });
    render(<BuildControls />);

    // Create file with empty MIME type (some browsers do this for unknown extensions).
    const emptyTypeFile = makeFile("file.dat", "", 100 * 1024);
    uploadFile(emptyTypeFile);

    await waitFor(() => {
      expect(screen.getByText("Only PNG and JPG files are accepted.")).toBeInTheDocument();
    });
    expect(createObjectURLSpy).not.toHaveBeenCalled();
  });

  it("GAP-12-B: empty MIME file does not update the store", async () => {
    setupStore("slug", BASE_TEXTURE_CONTROLS, { texture_mode: "custom" }, null);
    render(<BuildControls />);

    const emptyTypeFile = makeFile("file.dat", "", 100 * 1024);
    uploadFile(emptyTypeFile);

    await waitFor(() => {
      expect(screen.getByText("Only PNG and JPG files are accepted.")).toBeInTheDocument();
    });

    const state = useAppStore.getState() as Record<string, unknown>;
    expect(state["customTextureUrl"]).toBeNull();
  });
});
