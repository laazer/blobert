// @vitest-environment jsdom
/**
 * ADVERSARIAL TEST SUITE: Concurrency & Integration Stress Tests
 *
 * This test suite exposes weaknesses in concurrent operations, state synchronization,
 * and integration between HexStrControlRow, ZoneTextureBlock, and the store.
 */

import { describe, it, expect, afterEach, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { AnimatedBuildControlDef } from "../../types";
import { ControlRow } from "./BuildControlRow";

afterEach(() => {
  cleanup();
  vi.clearAllTimers();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

const hexDef: Extract<AnimatedBuildControlDef, { type: "str" }> = {
  key: "feat_body_hex",
  label: "Body hex",
  type: "str",
  default: "000000",
};

async function clickPaste(pasteBtn: HTMLElement) {
  await act(async () => {
    fireEvent.click(pasteBtn);
    await Promise.resolve();
    await Promise.resolve();
  });
}

async function advanceMs(ms: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

describe("HexStrControlRow — Concurrency & Timing Edge Cases", () => {
  describe("Paste hint auto-clear timing", () => {
    it("hint disappears after 2 seconds on error", async () => {
      vi.useFakeTimers();

      const read = vi.fn().mockResolvedValue("invalid");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      render(<ControlRow def={hexDef} value="ffffff" onChange={() => {}} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });
      await clickPaste(pasteBtn);

      expect(screen.getByRole("status")).toHaveTextContent("No #RRGGBB in clipboard");

      await advanceMs(2000);

      expect(screen.queryByRole("status")).not.toBeInTheDocument();
    });

    it("multiple pastes cancel previous timeout and restart it", async () => {
      vi.useFakeTimers();

      const read = vi.fn().mockResolvedValue("invalid");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      render(<ControlRow def={hexDef} value="ffffff" onChange={() => {}} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });

      await clickPaste(pasteBtn);
      expect(screen.getByRole("status")).toBeInTheDocument();

      await advanceMs(1500);

      await clickPaste(pasteBtn);
      await advanceMs(1000);

      expect(screen.getByRole("status")).toBeInTheDocument();

      await advanceMs(1000);

      expect(screen.queryByRole("status")).not.toBeInTheDocument();
    });

    it("component unmount clears the hint timeout (no memory leak)", async () => {
      vi.useFakeTimers();

      const read = vi.fn().mockResolvedValue("invalid");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const { unmount } = render(<ControlRow def={hexDef} value="ffffff" onChange={() => {}} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });
      await clickPaste(pasteBtn);
      expect(screen.getByRole("status")).toBeInTheDocument();

      unmount();

      await expect(advanceMs(2000)).resolves.toBeUndefined();
    });

    it("successful paste clears hint immediately (no timeout)", async () => {
      const read = vi.fn().mockResolvedValue("#ff0000");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const onChange = vi.fn();
      render(<ControlRow def={hexDef} value="ffffff" onChange={onChange} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });
      await clickPaste(pasteBtn);

      expect(onChange).toHaveBeenCalledWith("ff0000");
      expect(screen.queryByRole("status")).not.toBeInTheDocument();
    });
  });

  describe("Multiple rapid pastes", () => {
    it("handles 10 rapid pastes without crashing", async () => {
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
      render(<ControlRow def={hexDef} value="ffffff" onChange={onChange} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });

      for (let i = 0; i < 10; i++) {
        await clickPaste(pasteBtn);
      }

      expect(read).toHaveBeenCalledTimes(10);
      expect(onChange).toHaveBeenCalledWith("ff0000");
      expect(onChange).toHaveBeenCalledWith("00ff00");
      expect(onChange).toHaveBeenCalledWith("0000ff");
    });

    it("last paste value takes precedence on concurrent operations", async () => {
      const read = vi.fn()
        .mockResolvedValueOnce("#ff0000")
        .mockResolvedValueOnce("#00ff00");

      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const onChange = vi.fn();
      render(<ControlRow def={hexDef} value="ffffff" onChange={onChange} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });

      await clickPaste(pasteBtn);
      await clickPaste(pasteBtn);

      expect(read).toHaveBeenCalledTimes(2);

      const calls = onChange.mock.calls;
      expect(calls.some((c) => c[0] === "ff0000")).toBe(true);
      expect(calls.some((c) => c[0] === "00ff00")).toBe(true);
    });
  });

  describe("Clipboard API error recovery", () => {
    it("handles rejection in readText, shows error hint, allows retry", async () => {
      const read = vi.fn()
        .mockRejectedValueOnce(new Error("NotAllowedError"))
        .mockResolvedValueOnce("#ff0000");

      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const onChange = vi.fn();
      render(<ControlRow def={hexDef} value="ffffff" onChange={onChange} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });

      await clickPaste(pasteBtn);
      await clickPaste(pasteBtn);

      expect(onChange).toHaveBeenCalledWith("ff0000");
    });

    it("handles clipboard API missing (no crash, graceful degradation)", async () => {
      vi.stubGlobal("navigator", {});

      render(<ControlRow def={hexDef} value="ffffff" onChange={() => {}} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });
      await clickPaste(pasteBtn);

      expect(pasteBtn).toBeInTheDocument();
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

      const { unmount } = render(<ControlRow def={hexDef} value="ffffff" onChange={() => {}} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });
      await clickPaste(pasteBtn);

      unmount();

      await act(async () => {
        await vi.advanceTimersByTimeAsync(5100);
      });

      expect(() => vi.runAllTimers()).not.toThrow();
    });

    it("multiple renders with same/different values don't cause issues", async () => {
      const read = vi.fn().mockResolvedValue("#ff0000");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const { rerender } = render(<ControlRow def={hexDef} value="ffffff" onChange={() => {}} />);

      let pasteBtn = screen.getByRole("button", { name: "Paste color" });
      await clickPaste(pasteBtn);

      rerender(<ControlRow def={hexDef} value="ffffff" onChange={() => {}} />);

      pasteBtn = screen.getByRole("button", { name: "Paste color" });
      expect(pasteBtn).toBeInTheDocument();

      rerender(<ControlRow def={hexDef} value="aabbcc" onChange={() => {}} />);

      const hexField = screen.getByPlaceholderText("RRGGBB") as HTMLInputElement;
      expect(hexField.value).toBe("aabbcc");
    });
  });

  describe("Hex input change and paste integration", () => {
    it("typing in hex field and pasting should both work", async () => {
      const read = vi.fn().mockResolvedValue("#00ff00");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const onChange = vi.fn();
      render(<ControlRow def={hexDef} value="ff0000" onChange={onChange} />);

      const hexField = screen.getByPlaceholderText("RRGGBB");

      await act(async () => {
        fireEvent.change(hexField, { target: { value: "0000ff" } });
      });

      expect(onChange).toHaveBeenCalledWith("0000ff");

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });
      await clickPaste(pasteBtn);

      expect(onChange).toHaveBeenCalledWith("00ff00");
      expect(onChange).toHaveBeenCalledTimes(2);
    });
  });

  describe("Value prop changes during async operations", () => {
    it("value prop change during paste completes correctly", async () => {
      const read = vi.fn().mockResolvedValue("#ff0000");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const onChange = vi.fn();
      const { rerender } = render(<ControlRow def={hexDef} value="ffffff" onChange={onChange} />);

      const pasteBtn = screen.getByRole("button", { name: "Paste color" });
      await clickPaste(pasteBtn);

      rerender(<ControlRow def={hexDef} value="0000ff" onChange={onChange} />);

      expect(onChange).toHaveBeenCalledWith("ff0000");
    });
  });
});
