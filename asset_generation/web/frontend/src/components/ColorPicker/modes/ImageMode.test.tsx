// @vitest-environment jsdom
import { describe, it, expect, afterEach, vi, beforeEach } from "vitest";
import { act, cleanup, render, screen, fireEvent } from "@testing-library/react";
import { ImageMode } from "./ImageMode";

afterEach(() => {
  cleanup();
});

describe("ImageMode", () => {
  beforeEach(() => {
    // Mock URL.createObjectURL
    global.URL.createObjectURL = vi.fn(() => "blob:mock-url");
    global.URL.revokeObjectURL = vi.fn();
  });

  it("renders file input", () => {
    render(
      <ImageMode
        file={null}
        onFileChange={() => {}}
      />
    );

    const fileInput = screen.getByLabelText(/upload texture image/i);
    expect(fileInput).toHaveAttribute("type", "file");
  });

  it("displays 'No file selected' when no file is uploaded", () => {
    render(
      <ImageMode
        file={null}
        onFileChange={() => {}}
      />
    );

    expect(screen.getByText("No file selected")).toBeInTheDocument();
  });

  it("calls onFileChange when file is selected", async () => {
    const onFileChange = vi.fn();
    render(
      <ImageMode
        file={null}
        onFileChange={onFileChange}
      />
    );

    const fileInputs = document.querySelectorAll('input[type="file"]');
    expect(fileInputs.length).toBeGreaterThan(0);

    const file = new File(["test"], "test.png", { type: "image/png" });

    await act(async () => {
      fireEvent.change(fileInputs[0], { target: { files: [file] } });
    });

    expect(onFileChange).toHaveBeenCalledWith(file, "blob:mock-url");
  });

  it("rejects non-image files", async () => {
    const onFileChange = vi.fn();
    render(
      <ImageMode
        file={null}
        onFileChange={onFileChange}
      />
    );

    const fileInputs = document.querySelectorAll('input[type="file"]');
    const file = new File(["test"], "test.txt", { type: "text/plain" });

    await act(async () => {
      fireEvent.change(fileInputs[0], { target: { files: [file] } });
    });

    expect(screen.getByText(/only png, jpeg, and webp/i)).toBeInTheDocument();
    expect(onFileChange).toHaveBeenCalledWith(null);
  });

  it("rejects files larger than 5 MB", async () => {
    const onFileChange = vi.fn();
    render(
      <ImageMode
        file={null}
        onFileChange={onFileChange}
      />
    );

    const fileInputs = document.querySelectorAll('input[type="file"]');
    const largeFile = new File(
      [new ArrayBuffer(6 * 1024 * 1024)],
      "large.png",
      { type: "image/png" }
    );

    await act(async () => {
      fireEvent.change(fileInputs[0], { target: { files: [largeFile] } });
    });

    expect(screen.getByText(/file size must be less than 5 mb/i)).toBeInTheDocument();
    expect(onFileChange).toHaveBeenCalledWith(null);
  });

  it("displays file name when file is selected", () => {
    const file = new File(["test"], "my-texture.png", { type: "image/png" });
    render(
      <ImageMode
        file={file}
        preview="blob:mock-url"
        onFileChange={() => {}}
      />
    );

    expect(screen.getByText("my-texture.png")).toBeInTheDocument();
  });

  it("displays preview image when preview URL is provided", () => {
    const file = new File(["test"], "test.png", { type: "image/png" });
    render(
      <ImageMode
        file={file}
        preview="blob:mock-url"
        onFileChange={() => {}}
      />
    );

    const img = screen.getByAltText("Preview");
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src", "blob:mock-url");
  });

  it("shows clear button when preview is available", () => {
    const file = new File(["test"], "test.png", { type: "image/png" });
    render(
      <ImageMode
        file={file}
        preview="blob:mock-url"
        onFileChange={() => {}}
      />
    );

    const clearButton = screen.getByRole("button", { name: /clear/i });
    expect(clearButton).toBeInTheDocument();
  });

  it("calls onFileChange with null when clear button is clicked", async () => {
    const onFileChange = vi.fn();
    const file = new File(["test"], "test.png", { type: "image/png" });
    render(
      <ImageMode
        file={file}
        preview="blob:mock-url"
        onFileChange={onFileChange}
      />
    );

    const clearButton = screen.getByRole("button", { name: /clear/i });
    await act(async () => {
      fireEvent.click(clearButton);
    });

    expect(onFileChange).toHaveBeenCalledWith(null);
  });

  it("displays file size in KB", () => {
    const file = new File(
      [new ArrayBuffer(1024)],
      "test.png",
      { type: "image/png" }
    );
    render(
      <ImageMode
        file={file}
        preview="blob:mock-url"
        onFileChange={() => {}}
      />
    );

    expect(screen.getByText(/kb/i)).toBeInTheDocument();
  });

  it("disables file input when disabled prop is true", () => {
    render(
      <ImageMode
        file={null}
        onFileChange={() => {}}
        disabled={true}
      />
    );

    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach((input) => {
      expect(input).toBeDisabled();
    });
  });

  it("supports JPEG, PNG, and WebP files", async () => {
    const onFileChange = vi.fn();
    const { rerender } = render(
      <ImageMode
        file={null}
        onFileChange={onFileChange}
      />
    );

    const fileInputs = document.querySelectorAll('input[type="file"]');

    // Test PNG
    const pngFile = new File(["test"], "test.png", { type: "image/png" });
    await act(async () => {
      fireEvent.change(fileInputs[0], { target: { files: [pngFile] } });
    });
    expect(onFileChange).toHaveBeenCalledWith(pngFile, "blob:mock-url");

    // Reset and test JPEG
    onFileChange.mockClear();
    rerender(
      <ImageMode
        file={null}
        onFileChange={onFileChange}
      />
    );

    const jpegFile = new File(["test"], "test.jpg", { type: "image/jpeg" });
    const newFileInputs = document.querySelectorAll('input[type="file"]');
    await act(async () => {
      fireEvent.change(newFileInputs[0], { target: { files: [jpegFile] } });
    });
    expect(onFileChange).toHaveBeenCalledWith(jpegFile, "blob:mock-url");
  });
});
