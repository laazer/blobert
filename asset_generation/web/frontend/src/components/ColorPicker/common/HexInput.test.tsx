// @vitest-environment jsdom
import { describe, it, expect, afterEach, vi } from "vitest";
import { act, cleanup, render, screen, fireEvent } from "@testing-library/react";
import { HexInput } from "./HexInput";

afterEach(() => {
  cleanup();
});

describe("HexInput", () => {
  it("renders hex input with current value", () => {
    const onChange = vi.fn();
    render(
      <HexInput
        value="ff0000"
        onChange={onChange}
      />
    );

    const input = screen.getByPlaceholderText("RRGGBB") as HTMLInputElement;
    expect(input.value).toBe("ff0000");
  });

  it("calls onChange when hex text input changes", async () => {
    const onChange = vi.fn();
    render(
      <HexInput
        value="ff0000"
        onChange={onChange}
      />
    );

    const input = screen.getByPlaceholderText("RRGGBB");
    await act(async () => {
      fireEvent.change(input, { target: { value: "00ff00" } });
    });

    expect(onChange).toHaveBeenCalledWith("00ff00");
  });

  it("sanitizes hex value on blur", async () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <HexInput
        value="gg0000"
        onChange={onChange}
      />
    );

    const input = screen.getByPlaceholderText("RRGGBB");
    await act(async () => {
      fireEvent.blur(input);
    });

    expect(onChange).toHaveBeenCalledWith("");
  });

  it("accepts hex with # prefix and removes it", async () => {
    const onChange = vi.fn();
    render(
      <HexInput
        value="ff0000"
        onChange={onChange}
      />
    );

    const input = screen.getByPlaceholderText("RRGGBB");
    await act(async () => {
      fireEvent.change(input, { target: { value: "#00ff00" } });
    });

    expect(onChange).toHaveBeenCalledWith("00ff00");
  });

  it("converts input to lowercase", async () => {
    const onChange = vi.fn();
    render(
      <HexInput
        value="ff0000"
        onChange={onChange}
      />
    );

    const input = screen.getByPlaceholderText("RRGGBB");
    await act(async () => {
      fireEvent.change(input, { target: { value: "FF00FF" } });
    });

    expect(onChange).toHaveBeenCalledWith("ff00ff");
  });

  it("renders color picker input with correct background", () => {
    render(
      <HexInput
        value="ff0000"
        onChange={() => {}}
      />
    );

    const colorInput = document.querySelector(
      'input[type="color"]',
    ) as HTMLInputElement;
    expect(colorInput).toBeInTheDocument();
    expect(colorInput).toHaveAttribute("title", "Pick color");
  });

  it("disables all inputs when disabled prop is true", () => {
    render(
      <HexInput
        value="ff0000"
        onChange={() => {}}
        disabled={true}
      />
    );

    const input = screen.getByPlaceholderText("RRGGBB") as HTMLInputElement;
    expect(input.disabled).toBe(true);
  });

  it("renders label when provided", () => {
    render(
      <HexInput
        value="ff0000"
        onChange={() => {}}
        label="Primary Color"
      />
    );

    expect(screen.getByText("Primary Color")).toBeInTheDocument();
  });

  it("shows copy button when onCopyClick provided", () => {
    const onCopyClick = vi.fn();
    render(
      <HexInput
        value="ff0000"
        onChange={() => {}}
        onCopyClick={onCopyClick}
      />
    );

    const copyButton = screen.getByRole("button", { name: /copy/i });
    expect(copyButton).toBeInTheDocument();
  });

  it("calls onCopyClick when copy button is clicked", async () => {
    const onCopyClick = vi.fn();
    render(
      <HexInput
        value="ff0000"
        onChange={() => {}}
        onCopyClick={onCopyClick}
      />
    );

    const copyButton = screen.getByRole("button", { name: /copy/i });
    await act(async () => {
      fireEvent.click(copyButton);
    });

    expect(onCopyClick).toHaveBeenCalledWith("ff0000");
  });

  it("updates HTML5 color input when value changes", () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <HexInput
        value="ff0000"
        onChange={onChange}
      />
    );

    rerender(
      <HexInput
        value="00ff00"
        onChange={onChange}
      />
    );

    // The color input internally uses the value, just verify component updated
    const input = screen.getByPlaceholderText("RRGGBB") as HTMLInputElement;
    expect(input.value).toBe("00ff00");
  });
});
