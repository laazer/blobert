import { afterEach, describe, expect, it, vi } from "vitest";
import { copyHexToClipboard, normalizeHexForBuildOption, readHexFromClipboard } from "./clipboardHex";

describe("normalizeHexForBuildOption", () => {
  it("accepts #RRGGBB and RRGGBB", () => {
    expect(normalizeHexForBuildOption("#aABBcc")).toBe("aabbcc");
    expect(normalizeHexForBuildOption("00ff00")).toBe("00ff00");
  });

  it("trims and rejects invalid", () => {
    expect(normalizeHexForBuildOption("  #010203  ")).toBe("010203");
    expect(normalizeHexForBuildOption("bad")).toBeNull();
    expect(normalizeHexForBuildOption("#fff")).toBeNull();
  });
});

describe("clipboard round-trip", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("copy writes #form; read returns 6-char form", async () => {
    const write = vi.fn().mockResolvedValue(undefined);
    const read = vi.fn().mockResolvedValue("#c0ffee");
    vi.stubGlobal("navigator", {
      clipboard: { writeText: write, readText: read },
    });

    await expect(copyHexToClipboard("c0ffee")).resolves.toBe(true);
    expect(write).toHaveBeenCalledWith("#c0ffee");

    await expect(readHexFromClipboard()).resolves.toBe("c0ffee");
    read.mockResolvedValue("#bada55");
    await expect(readHexFromClipboard()).resolves.toBe("bada55");
  });
});
