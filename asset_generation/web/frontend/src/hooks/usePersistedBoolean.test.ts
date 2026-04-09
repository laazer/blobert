// @vitest-environment jsdom
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { usePersistedBoolean } from "./usePersistedBoolean";

describe("usePersistedBoolean", () => {
  const key = "blobert.test.flag";

  beforeEach(() => localStorage.clear());
  afterEach(() => localStorage.clear());

  it("persists true and false to localStorage", () => {
    const { result, rerender } = renderHook(
      ({ k }: { k: string }) => usePersistedBoolean(k, true),
      { initialProps: { k: key } },
    );
    expect(result.current[0]).toBe(true);
    expect(localStorage.getItem(key)).toBe("1");

    act(() => {
      result.current[1](false);
    });
    expect(result.current[0]).toBe(false);
    expect(localStorage.getItem(key)).toBe("0");

    rerender({ k: key });
    expect(result.current[0]).toBe(false);
  });

  it("reads initial value from localStorage when present", () => {
    localStorage.setItem(key, "0");
    const { result } = renderHook(() => usePersistedBoolean(key, true));
    expect(result.current[0]).toBe(false);
  });
});
