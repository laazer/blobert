// @vitest-environment jsdom
import { describe, it, expect, vi, afterEach } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { RegistryVersionNameInput } from "./RegistryVersionNameInput";

afterEach(() => {
  cleanup();
});

describe("RegistryVersionNameInput", () => {
  it("calls onCommit when blurred value differs from stored", () => {
    const onCommit = vi.fn();
    render(
      <RegistryVersionNameInput versionId="v0" storedName="Alpha" disabled={false} onCommit={onCommit} />,
    );
    const el = screen.getByLabelText("Display name for v0");
    fireEvent.change(el, { target: { value: "Beta" } });
    fireEvent.blur(el);
    expect(onCommit).toHaveBeenCalledWith("Beta");
  });

  it("does not call onCommit when unchanged after trim", () => {
    const onCommit = vi.fn();
    render(
      <RegistryVersionNameInput versionId="v0" storedName="  Alpha  " disabled={false} onCommit={onCommit} />,
    );
    const el = screen.getByLabelText("Display name for v0");
    fireEvent.blur(el);
    expect(onCommit).not.toHaveBeenCalled();
  });
});
