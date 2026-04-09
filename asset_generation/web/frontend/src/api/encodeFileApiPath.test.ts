import { describe, expect, it } from "vitest";
import { encodeFileApiPath } from "./client";

describe("encodeFileApiPath", () => {
  it("encodes spaces and hash per segment", () => {
    expect(encodeFileApiPath("src/a b.py")).toBe("src/a%20b.py");
    expect(encodeFileApiPath("src/foo#bar.py")).toBe("src/foo%23bar.py");
  });

  it("drops empty segments from doubled slashes", () => {
    expect(encodeFileApiPath("src//x.py")).toBe("src/x.py");
  });
});
