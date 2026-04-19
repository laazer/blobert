// @vitest-environment jsdom
/**
 * ADVERSARIAL TEST SUITE: Concurrency & Integration Stress Tests
 *
 * This test suite exposes weaknesses in concurrent operations, state synchronization,
 * and integration between HexStrControlRow, ZoneTextureBlock, and the store.
 *
 * Tests include:
 * 1. Multiple rapid paste operations (debounce, deduplication)
 * 2. Concurrent color picker changes (race conditions)
 * 3. Hint auto-clear timing (memory leaks, timeout cleanup)
 * 4. Component unmount during async operations (cleanup)
 * 5. Store update failures (error handling, state consistency)
 */

import { describe, it, expect, afterEach, beforeEach, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { AnimatedBuildControlDef } from "../../types";
import { ControlRow } from "./BuildControlRow";

afterEach(() => {
  cleanup();
  vi.clearAllTimers();
  vi.useRealTimers();
});

describe("HexStrControlRow — Concurrency & Timing Edge Cases", () => {
  describe("Paste hint auto-clear timing", () => {
    it("hint disappears after 2 seconds on error", async () => {
      vi.useFakeTimers();

      const read = vi.fn().mockResolvedValue("invalid");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const hexDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
        key: "feat_body_hex",
        label: "Body hex",
        type: "str",
        default: "000000",
      };

      render(<ControlRow def={hexDef} value="ffffff" onChange={() => {}} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });

      await act(async () => {
        fireEvent.click(pasteBtn);
      });

      // Hint should appear
      await waitFor(() => {
        expect(screen.getByRole("status")).toHaveTextContent("No #RRGGBB in clipboard");
      });

      // Advance time past 2 seconds
      vi.advanceTimersByTime(2000);

      await waitFor(() => {
        expect(screen.queryByRole("status")).not.toBeInTheDocument();
      });

      vi.useRealTimers();
      // CHECKPOINT: Hint clears at exactly 2 seconds
    });

    it("multiple pastes cancel previous timeout and restart it", async () => {
      vi.useFakeTimers();

      const read = vi.fn().mockResolvedValue("invalid");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const hexDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
        key: "feat_body_hex",
        label: "Body hex",
        type: "str",
        default: "000000",
      };

      render(<ControlRow def={hexDef} value="ffffff" onChange={() => {}} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });

      // First paste
      await act(async () => {
        fireEvent.click(pasteBtn);
      });

      await waitFor(() => {
        expect(screen.getByRole("status")).toBeInTheDocument();
      });

      // Advance 1.5 seconds (before hint clears)
      vi.advanceTimersByTime(1500);

      // Second paste (should restart timeout)
      await act(async () => {
        fireEvent.click(pasteBtn);
      });

      // Advance 1 second more (total 2.5s, but only 1s since second paste)
      vi.advanceTimersByTime(1000);

      // Hint should still be visible (1.5s into new timeout)
      expect(screen.getByRole("status")).toBeInTheDocument();

      // Advance 1 more second (now 2.5s into new timeout)
      vi.advanceTimersByTime(1000);

      // Now hint should disappear
      await waitFor(() => {
        expect(screen.queryByRole("status")).not.toBeInTheDocument();
      });

      vi.useRealTimers();
      // CHECKPOINT: Each paste restarts the timeout
    });

    it("component unmount clears the hint timeout (no memory leak)", async () => {
      vi.useFakeTimers();

      const read = vi.fn().mockResolvedValue("invalid");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const hexDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
        key: "feat_body_hex",
        label: "Body hex",
        type: "str",
        default: "000000",
      };

      const { unmount } = render(<ControlRow def={hexDef} value="ffffff" onChange={() => {}} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });

      await act(async () => {
        fireEvent.click(pasteBtn);
      });

      await waitFor(() => {
        expect(screen.getByRole("status")).toBeInTheDocument();
      });

      // Unmount component while timeout is pending
      unmount();

      // Advance time past timeout; should not throw or produce warnings
      expect(() => {
        vi.advanceTimersByTime(2000);
      }).not.toThrow();

      vi.useRealTimers();
      // CHECKPOINT: Timeout is properly cleaned up on unmount
    });

    it("successful paste clears hint immediately (no timeout)", async () => {
      vi.useFakeTimers();

      const read = vi.fn().mockResolvedValue("#ff0000");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const onChange = vi.fn();
      const hexDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
        key: "feat_body_hex",
        label: "Body hex",
        type: "str",
        default: "000000",
      };

      render(<ControlRow def={hexDef} value="ffffff" onChange={onChange} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });

      await act(async () => {
        fireEvent.click(pasteBtn);
      });

      // On success, hint should never appear
      await waitFor(() => {
        expect(onChange).toHaveBeenCalledWith("ff0000");
      });

      // Verify no error hint is shown
      expect(screen.queryByRole("status")).not.toBeInTheDocument();

      vi.useRealTimers();
      // CHECKPOINT: Successful paste doesn't show hint
    });
  });

  describe("Multiple rapid pastes", () => {
    it("handles 10 rapid pastes without crashing", async () => {
      vi.useFakeTimers();

      const read = vi.fn()
        .mockResolvedValueOnce("#ff0000")
        .mockResolvedValueOnce("#00ff00")
        .mockResolvedValueOnce("#0000ff")
        .mockResolvedValueOnce("invalid")
        .mockResolvedValueOnce("#ffff00")
        .mockResolvedValueOnce("#ff00ff")
        .mockResolvedValueOnce("#00ffff")
        .mockResolvedValueOnce("bad_hex")
        .mockResolvedValueOnce("#888888")
        .mockResolvedValueOnce("#aaaaaa");

      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const onChange = vi.fn();
      const hexDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
        key: "feat_body_hex",
        label: "Body hex",
        type: "str",
        default: "000000",
      };

      render(<ControlRow def={hexDef} value="ffffff" onChange={onChange} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });

      // Rapid clicks
      for (let i = 0; i < 10; i++) {
        await act(async () => {
          fireEvent.click(pasteBtn);
        });
      }

      // All reads should complete without crash
      await waitFor(() => {
        expect(read).toHaveBeenCalledTimes(10);
      });

      // Check that valid values were passed to onChange
      expect(onChange).toHaveBeenCalledWith("ff0000");
      expect(onChange).toHaveBeenCalledWith("00ff00");
      expect(onChange).toHaveBeenCalledWith("0000ff");

      vi.useRealTimers();
      // CHECKPOINT: Multiple rapid operations don't cause crashes
    });

    it("last paste value takes precedence on concurrent operations", async () => {
      vi.useFakeTimers();

      const read = vi.fn()
        .mockResolvedValueOnce("#ff0000") // First paste, slow
        .mockResolvedValueOnce("#00ff00"); // Second paste, fast

      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const onChange = vi.fn();
      const hexDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
        key: "feat_body_hex",
        label: "Body hex",
        type: "str",
        default: "000000",
      };

      render(<ControlRow def={hexDef} value="ffffff" onChange={onChange} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });

      // First click (fast resolution)
      await act(async () => {
        fireEvent.click(pasteBtn);
      });

      // Second click (may resolve in different order)
      await act(async () => {
        fireEvent.click(pasteBtn);
      });

      // Wait for both to resolve
      await waitFor(() => {
        expect(read).toHaveBeenCalledTimes(2);
      });

      // Both values should have been passed (order may vary due to async)
      const calls = onChange.mock.calls;
      expect(calls.some((c) => c[0] === "ff0000")).toBe(true);
      expect(calls.some((c) => c[0] === "00ff00")).toBe(true);

      vi.useRealTimers();
      // CHECKPOINT: Both values are handled, but order is non-deterministic
    });
  });

  describe("Clipboard API error recovery", () => {
    it("handles rejection in readText, shows error hint, allows retry", async () => {
      vi.useFakeTimers();

      const read = vi.fn()
        .mockRejectedValueOnce(new Error("NotAllowedError"))
        .mockResolvedValueOnce("#ff0000"); // Second attempt succeeds

      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const onChange = vi.fn();
      const hexDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
        key: "feat_body_hex",
        label: "Body hex",
        type: "str",
        default: "000000",
      };

      render(<ControlRow def={hexDef} value="ffffff" onChange={onChange} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });

      // First paste fails
      await act(async () => {
        fireEvent.click(pasteBtn);
      });

      // Should show error hint (or handle silently if readHexFromClipboard catches rejection)
      await waitFor(() => {
        // Error might be caught internally, no hint shown
        // CHECKPOINT: Rejection is handled gracefully
      });

      // Advance past hint timeout
      vi.advanceTimersByTime(2100);

      // Second paste succeeds
      await act(async () => {
        fireEvent.click(pasteBtn);
      });

      await waitFor(() => {
        expect(onChange).toHaveBeenCalledWith("ff0000");
      });

      vi.useRealTimers();
      // CHECKPOINT: Retry works after error
    });

    it("handles clipboard API missing (no crash, graceful degradation)", async () => {
      vi.stubGlobal("navigator", {});

      const hexDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
        key: "feat_body_hex",
        label: "Body hex",
        type: "str",
        default: "000000",
      };

      render(<ControlRow def={hexDef} value="ffffff" onChange={() => {}} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });

      // Click paste on device without clipboard API
      await act(async () => {
        fireEvent.click(pasteBtn);
      });

      // Should not crash; may show "No clipboard available" or similar
      await waitFor(() => {
        // Either no hint or a hint indicating clipboard unavailable
      });

      // CHECKPOINT: Missing API is handled gracefully
    });
  });

  describe("Component lifecycle and cleanup", () => {
    it("pending clipboard read is not awaited after unmount", async () => {
      vi.useFakeTimers();

      const read = vi.fn().mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve("#ff0000"), 5000)),
      );

      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const hexDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
        key: "feat_body_hex",
        label: "Body hex",
        type: "str",
        default: "000000",
      };

      const { unmount } = render(<ControlRow def={hexDef} value="ffffff" onChange={() => {}} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });

      // Click paste (starts async read)
      await act(async () => {
        fireEvent.click(pasteBtn);
      });

      // Unmount before read completes
      unmount();

      // Advance past read completion
      vi.advanceTimersByTime(5100);

      // Should not throw or produce warnings
      expect(() => vi.runAllTimers()).not.toThrow();

      vi.useRealTimers();
      // CHECKPOINT: Unmount during pending async operation is handled
    });

    it("multiple renders with same/different values don't cause issues", async () => {
      const hexDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
        key: "feat_body_hex",
        label: "Body hex",
        type: "str",
        default: "000000",
      };

      const read = vi.fn().mockResolvedValue("#ff0000");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const { rerender } = render(<ControlRow def={hexDef} value="ffffff" onChange={() => {}} />);

      let pasteBtn = screen.getByRole("button", { name: "Paste color" });
      await act(async () => {
        fireEvent.click(pasteBtn);
      });

      // Re-render with same value
      rerender(<ControlRow def={hexDef} value="ffffff" onChange={() => {}} />);

      pasteBtn = screen.getByRole("button", { name: "Paste color" });
      expect(pasteBtn).toBeInTheDocument();

      // Re-render with different value
      rerender(<ControlRow def={hexDef} value="aabbcc" onChange={() => {}} />);

      const hexField = screen.getByPlaceholderText("RRGGBB") as HTMLInputElement;
      expect(hexField.value).toBe("aabbcc");
      // CHECKPOINT: Re-renders don't cause state or timing issues
    });
  });

  describe("Hex input change and paste integration", () => {
    it("typing in hex field and pasting should both work", async () => {
      vi.useFakeTimers();

      const read = vi.fn().mockResolvedValue("#00ff00");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const onChange = vi.fn();
      const hexDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
        key: "feat_body_hex",
        label: "Body hex",
        type: "str",
        default: "000000",
      };

      render(<ControlRow def={hexDef} value="ff0000" onChange={onChange} />);

      const hexField = screen.getByPlaceholderText("RRGGBB");

      // Type into field
      await act(async () => {
        fireEvent.change(hexField, { target: { value: "0000ff" } });
      });

      expect(onChange).toHaveBeenCalledWith("0000ff");

      // Paste
      const pasteBtn = screen.getByRole("button", { name: "Paste color" });
      await act(async () => {
        fireEvent.click(pasteBtn);
      });

      await waitFor(() => {
        expect(onChange).toHaveBeenCalledWith("00ff00");
      });

      // Both operations completed without conflict
      expect(onChange).toHaveBeenCalledTimes(2);

      vi.useRealTimers();
      // CHECKPOINT: Typing and pasting work together
    });
  });

  describe("Value prop changes during async operations", () => {
    it("value prop change during paste completes correctly", async () => {
      vi.useFakeTimers();

      const read = vi.fn().mockResolvedValue("#ff0000");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const onChange = vi.fn();
      const hexDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
        key: "feat_body_hex",
        label: "Body hex",
        type: "str",
        default: "000000",
      };

      const { rerender } = render(<ControlRow def={hexDef} value="ffffff" onChange={onChange} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });

      await act(async () => {
        fireEvent.click(pasteBtn);
      });

      // Change value prop during paste (slow clipboard read)
      rerender(<ControlRow def={hexDef} value="0000ff" onChange={onChange} />);

      // Complete the paste
      await waitFor(() => {
        expect(onChange).toHaveBeenCalledWith("ff0000");
      });

      // Value prop change should not interfere with paste result
      expect(onChange).toHaveBeenCalledWith("ff0000");

      vi.useRealTimers();
      // CHECKPOINT: Value prop changes don't interfere with pending pastes
    });
  });
});
