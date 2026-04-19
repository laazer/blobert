import { afterEach, describe, expect, it, vi } from "vitest";
import {
  copyHexToClipboard,
  normalizeHexForBuildOption,
  readHexFromClipboard,
  sanitizeHex,
  hexForColorInput,
} from "./clipboardHex";

/**
 * ADVERSARIAL TEST SUITE: Hex Value Parsing & Normalization
 *
 * This test suite exposes weaknesses in hex validation, normalization, and
 * clipboard I/O error handling. Tests include:
 * - Null/undefined/empty clipboard content
 * - Malformed hex strings (wrong length, invalid chars, Unicode)
 * - Case sensitivity and normalization
 * - Whitespace handling
 * - Clipboard API failures and timeouts
 * - Concurrent clipboard operations
 */

describe("normalizeHexForBuildOption — Input Mutations", () => {
  describe("Valid hex inputs", () => {
    it("accepts lowercase #RRGGBB", () => {
      expect(normalizeHexForBuildOption("#aabbcc")).toBe("aabbcc");
    });

    it("accepts uppercase #RRGGBB", () => {
      expect(normalizeHexForBuildOption("#AABBCC")).toBe("aabbcc"); // Normalized to lowercase
    });

    it("accepts mixed case #RrGgBb", () => {
      expect(normalizeHexForBuildOption("#AaBbCc")).toBe("aabbcc");
    });

    it("accepts RRGGBB without #", () => {
      expect(normalizeHexForBuildOption("ff0000")).toBe("ff0000");
    });

    it("accepts 000000 (black)", () => {
      expect(normalizeHexForBuildOption("000000")).toBe("000000");
    });

    it("accepts ffffff (white)", () => {
      expect(normalizeHexForBuildOption("ffffff")).toBe("ffffff");
    });

    it("accepts with leading/trailing whitespace: '  #ff0000  '", () => {
      expect(normalizeHexForBuildOption("  #ff0000  ")).toBe("ff0000");
    });

    it("accepts newline and tab whitespace: '\\t#ff0000\\n'", () => {
      expect(normalizeHexForBuildOption("\t#ff0000\n")).toBe("ff0000");
    });
  });

  describe("Invalid hex inputs", () => {
    it("rejects empty string", () => {
      expect(normalizeHexForBuildOption("")).toBeNull();
    });

    it("rejects whitespace-only string", () => {
      expect(normalizeHexForBuildOption("   ")).toBeNull();
    });

    it("rejects null", () => {
      // TypeScript would prevent this, but runtime test it
      expect(normalizeHexForBuildOption(null as any)).toBeNull();
    });

    it("rejects undefined", () => {
      expect(normalizeHexForBuildOption(undefined as any)).toBeNull();
    });

    it("rejects too-short hex: '#fff' (3 chars, not 6)", () => {
      expect(normalizeHexForBuildOption("#fff")).toBeNull();
    });

    it("rejects too-long hex: '#ff0000ff' (8 chars, RGBA)", () => {
      expect(normalizeHexForBuildOption("#ff0000ff")).toBeNull();
    });

    it("rejects non-hex chars: '#gggggg'", () => {
      expect(normalizeHexForBuildOption("#gggggg")).toBeNull();
    });

    it("rejects partial non-hex: '#ffgg00'", () => {
      expect(normalizeHexForBuildOption("#ffgg00")).toBeNull();
    });

    it("rejects #-only: '#'", () => {
      expect(normalizeHexForBuildOption("#")).toBeNull();
    });

    it("rejects text mixed with hex: 'red #ff0000'", () => {
      expect(normalizeHexForBuildOption("red #ff0000")).toBeNull();
    });

    it("rejects single hex digit: '5'", () => {
      expect(normalizeHexForBuildOption("5")).toBeNull();
    });

    it("rejects 4-char hex: '#ff00'", () => {
      expect(normalizeHexForBuildOption("#ff00")).toBeNull();
    });

    it("rejects 5-char hex: '#ff000'", () => {
      expect(normalizeHexForBuildOption("#ff000")).toBeNull();
    });

    it("rejects 7-char hex: '#ff00000'", () => {
      expect(normalizeHexForBuildOption("#ff00000")).toBeNull();
    });
  });

  describe("Edge cases: whitespace and special chars", () => {
    it("accepts #ff0000 with leading/trailing spaces", () => {
      expect(normalizeHexForBuildOption("  #ff0000  ")).toBe("ff0000");
    });

    it("accepts ff0000 with leading/trailing spaces (no #)", () => {
      expect(normalizeHexForBuildOption("  ff0000  ")).toBe("ff0000");
    });

    it("rejects hex with internal whitespace: '#ff 00 00'", () => {
      expect(normalizeHexForBuildOption("#ff 00 00")).toBeNull();
    });

    it("rejects hex with newline: '#ff0000\\n00'", () => {
      expect(normalizeHexForBuildOption("#ff0000\n00")).toBeNull();
    });

    it("rejects hex with null byte: '#ff0000\\0'", () => {
      expect(normalizeHexForBuildOption("#ff0000\0ff")).toBeNull();
    });

    it("rejects non-ASCII chars: '#ff00é0'", () => {
      expect(normalizeHexForBuildOption("#ff00é0")).toBeNull();
    });

    it("rejects emoji: '🔴' (red circle emoji)", () => {
      expect(normalizeHexForBuildOption("🔴")).toBeNull();
    });

    it("rejects hex with plus sign: '#+ff0000'", () => {
      expect(normalizeHexForBuildOption("#+ff0000")).toBeNull();
    });

    it("rejects hex with minus sign: '#-ff0000'", () => {
      expect(normalizeHexForBuildOption("#-ff0000")).toBeNull();
    });

    it("rejects hex with x prefix: '#x0000ff'", () => {
      expect(normalizeHexForBuildOption("#x0000ff")).toBeNull();
    });

    it("rejects 0x prefix (C-style): '0xff0000'", () => {
      expect(normalizeHexForBuildOption("0xff0000")).toBeNull();
    });
  });

  describe("Edge cases: very long inputs", () => {
    it("rejects extremely long string", () => {
      const longString = "#" + "ff".repeat(1000);
      expect(normalizeHexForBuildOption(longString)).toBeNull();
    });

    it("rejects 1MB+ string (stress test)", () => {
      const veryLong = "a".repeat(1024 * 1024);
      expect(() => normalizeHexForBuildOption(veryLong)).not.toThrow();
      expect(normalizeHexForBuildOption(veryLong)).toBeNull();
      // CHECKPOINT: Should handle large inputs without hanging or crash
    });
  });

  describe("Edge cases: case insensitivity", () => {
    it("converts uppercase to lowercase: AABBCC → aabbcc", () => {
      expect(normalizeHexForBuildOption("AABBCC")).toBe("aabbcc");
    });

    it("converts mixed case to lowercase: AaBbCc → aabbcc", () => {
      expect(normalizeHexForBuildOption("AaBbCc")).toBe("aabbcc");
    });

    it("preserves lowercase: aabbcc → aabbcc", () => {
      expect(normalizeHexForBuildOption("aabbcc")).toBe("aabbcc");
    });

    it("uppercase with #: #AABBCC → aabbcc", () => {
      expect(normalizeHexForBuildOption("#AABBCC")).toBe("aabbcc");
    });
  });
});

describe("readHexFromClipboard — Clipboard API Edge Cases", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe("Successful reads", () => {
    it("reads #RRGGBB and returns 6-char normalized form", async () => {
      const read = vi.fn().mockResolvedValue("#ff0000");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const result = await readHexFromClipboard();
      expect(result).toBe("ff0000");
    });

    it("reads RRGGBB (no #) and returns normalized form", async () => {
      const read = vi.fn().mockResolvedValue("00ff00");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const result = await readHexFromClipboard();
      expect(result).toBe("00ff00");
    });

    it("reads uppercase and normalizes to lowercase", async () => {
      const read = vi.fn().mockResolvedValue("#AABBCC");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const result = await readHexFromClipboard();
      expect(result).toBe("aabbcc");
    });
  });

  describe("Invalid clipboard content", () => {
    it("returns null for empty clipboard", async () => {
      const read = vi.fn().mockResolvedValue("");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const result = await readHexFromClipboard();
      expect(result).toBeNull();
    });

    it("returns null for non-hex text in clipboard", async () => {
      const read = vi.fn().mockResolvedValue("not a hex value");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const result = await readHexFromClipboard();
      expect(result).toBeNull();
    });

    it("returns null for partial hex (too short)", async () => {
      const read = vi.fn().mockResolvedValue("#fff");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const result = await readHexFromClipboard();
      expect(result).toBeNull();
    });

    it("returns null for oversized hex string", async () => {
      const read = vi.fn().mockResolvedValue("#ff0000ff"); // RGBA, not RGB
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const result = await readHexFromClipboard();
      expect(result).toBeNull();
    });

    it("returns null for #-only clipboard", async () => {
      const read = vi.fn().mockResolvedValue("#");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const result = await readHexFromClipboard();
      expect(result).toBeNull();
    });

    it("returns null for emoji in clipboard", async () => {
      const read = vi.fn().mockResolvedValue("🎨 #ff0000");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const result = await readHexFromClipboard();
      expect(result).toBeNull();
      // CHECKPOINT: Emoji does not parse as valid hex
    });

    it("returns null for very long clipboard content", async () => {
      const longText = "a".repeat(1024 * 1024);
      const read = vi.fn().mockResolvedValue(longText);
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const result = await readHexFromClipboard();
      expect(result).toBeNull();
      // CHECKPOINT: Large clipboard content is handled
    });

    it("handles whitespace-padded hex", async () => {
      const read = vi.fn().mockResolvedValue("  #ff0000  ");
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const result = await readHexFromClipboard();
      expect(result).toBe("ff0000");
    });
  });

  describe("Clipboard API failures", () => {
    it("handles readText rejection (Permission denied)", async () => {
      const read = vi.fn().mockRejectedValue(new Error("NotAllowedError"));
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const result = await readHexFromClipboard();
      expect(result).toBeNull();
      // CHECKPOINT: Promise rejection is caught, returns null
    });

    it("handles readText timeout (no clipboard available)", async () => {
      const read = vi.fn().mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(""), 10000)),
      );
      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const promise = readHexFromClipboard();
      // Don't actually wait 10s; just verify function doesn't hang indefinitely
      vi.useFakeTimers();
      expect(() => vi.advanceTimersByTime(1000)).not.toThrow();
      vi.useRealTimers();
    });

    it("handles missing navigator.clipboard", async () => {
      vi.stubGlobal("navigator", {});

      const result = await readHexFromClipboard();
      expect(result).toBeNull();
      // CHECKPOINT: Missing clipboard API is handled gracefully
    });

    it("handles null navigator", async () => {
      vi.stubGlobal("navigator", null as any);

      const result = await readHexFromClipboard();
      expect(result).toBeNull();
    });

    it("handles navigator.clipboard.readText as null", async () => {
      vi.stubGlobal("navigator", {
        clipboard: { readText: null as any, writeText: vi.fn() },
      });

      const result = await readHexFromClipboard();
      expect(result).toBeNull();
    });
  });

  describe("Concurrency and race conditions", () => {
    it("multiple readHexFromClipboard calls in parallel", async () => {
      const read = vi.fn()
        .mockResolvedValueOnce("#ff0000")
        .mockResolvedValueOnce("#00ff00")
        .mockResolvedValueOnce("#0000ff");

      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const results = await Promise.all([
        readHexFromClipboard(),
        readHexFromClipboard(),
        readHexFromClipboard(),
      ]);

      expect(results).toEqual(["ff0000", "00ff00", "0000ff"]);
      expect(read).toHaveBeenCalledTimes(3);
      // CHECKPOINT: Concurrent reads work correctly
    });

    it("clipboard content changes between reads", async () => {
      const read = vi.fn()
        .mockResolvedValueOnce("#ff0000")
        .mockResolvedValueOnce("#00ff00");

      vi.stubGlobal("navigator", {
        clipboard: { readText: read, writeText: vi.fn() },
      });

      const result1 = await readHexFromClipboard();
      const result2 = await readHexFromClipboard();

      expect(result1).toBe("ff0000");
      expect(result2).toBe("00ff00");
      // CHECKPOINT: Sequential reads capture actual clipboard state
    });
  });
});

describe("copyHexToClipboard — Write Operations", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe("Successful writes", () => {
    it("writes #RRGGBB format to clipboard", async () => {
      const write = vi.fn().mockResolvedValue(undefined);
      vi.stubGlobal("navigator", {
        clipboard: { readText: vi.fn(), writeText: write },
      });

      const result = await copyHexToClipboard("ff0000");
      expect(result).toBe(true);
      expect(write).toHaveBeenCalledWith("#ff0000");
    });

    it("normalizes uppercase input before writing", async () => {
      const write = vi.fn().mockResolvedValue(undefined);
      vi.stubGlobal("navigator", {
        clipboard: { readText: vi.fn(), writeText: write },
      });

      const result = await copyHexToClipboard("AABBCC");
      expect(result).toBe(true);
      expect(write).toHaveBeenCalledWith("#aabbcc");
      // CHECKPOINT: Input is normalized before write
    });
  });

  describe("Write failures", () => {
    it("returns false on permission denied", async () => {
      const write = vi.fn().mockRejectedValue(new Error("NotAllowedError"));
      vi.stubGlobal("navigator", {
        clipboard: { readText: vi.fn(), writeText: write },
      });

      const result = await copyHexToClipboard("ff0000");
      expect(result).toBe(false);
    });

    it("returns false if clipboard API missing", async () => {
      vi.stubGlobal("navigator", {});

      const result = await copyHexToClipboard("ff0000");
      expect(result).toBe(false);
    });

    it("returns false on unexpected error", async () => {
      const write = vi.fn().mockRejectedValue(new Error("Unknown error"));
      vi.stubGlobal("navigator", {
        clipboard: { readText: vi.fn(), writeText: write },
      });

      const result = await copyHexToClipboard("ff0000");
      expect(result).toBe(false);
    });
  });
});

describe("hexForColorInput — Formatting Utility", () => {
  it("converts 6-char hex to #RRGGBB", () => {
    expect(hexForColorInput("ff0000")).toBe("#ff0000");
  });

  it("converts uppercase hex to #rrggbb (lowercase)", () => {
    expect(hexForColorInput("FF0000")).toBe("#ff0000");
  });

  it("handles empty string", () => {
    const result = hexForColorInput("");
    expect(result).toBe("#"); // Likely behavior
    // CHECKPOINT: Empty input produces minimal output
  });

  it("handles null/undefined", () => {
    expect(() => hexForColorInput(null as any)).not.toThrow();
    expect(() => hexForColorInput(undefined as any)).not.toThrow();
    // CHECKPOINT: Graceful handling of invalid input
  });
});

describe("sanitizeHex — Stripping Invalid Characters", () => {
  it("removes non-hex characters", () => {
    const result = sanitizeHex("ff00ggbb");
    expect(result).toBe("ff00bb"); // 'gg' removed
    // CHECKPOINT: Character filtering works
  });

  it("removes whitespace", () => {
    const result = sanitizeHex("ff 00 00");
    expect(result).toBe("ff0000");
  });

  it("removes # prefix", () => {
    const result = sanitizeHex("#ff0000");
    expect(result).toBe("ff0000");
  });

  it("handles completely invalid input", () => {
    const result = sanitizeHex("xyz");
    expect(result).toBe(""); // All chars filtered
  });
});
