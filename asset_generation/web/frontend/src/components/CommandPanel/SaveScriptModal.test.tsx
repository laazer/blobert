// @vitest-environment jsdom
import { describe, it, expect, vi, afterEach } from "vitest";
import { cleanup, render, screen, waitFor, fireEvent } from "@testing-library/react";
import { SaveScriptModal, formatSaveScriptError } from "./SaveScriptModal";

afterEach(() => {
  cleanup();
});

describe("formatSaveScriptError", () => {
  it("formats Error, string, and unknown", () => {
    expect(formatSaveScriptError(new Error("boom"))).toBe("boom");
    expect(formatSaveScriptError("plain")).toBe("plain");
    expect(formatSaveScriptError(null)).toBe("null");
  });
});

describe("SaveScriptModal", () => {
  const onClose = vi.fn();
  const onLoadFileTree = vi.fn().mockResolvedValue(undefined);
  const onSave = vi.fn().mockResolvedValue(undefined);

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders dialog in document.body via portal when open", async () => {
    const { container } = render(
      <div id="app-root">
        <SaveScriptModal
          open
          onClose={onClose}
          initialPath="src/blobert/a.py"
          fileTree={[]}
          onLoadFileTree={onLoadFileTree}
          isSaving={false}
          onSave={onSave}
        />
      </div>,
    );

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(container.querySelector('[role="dialog"]')).toBeNull();
    expect(document.body.querySelector('[role="dialog"]')).not.toBeNull();
    expect(screen.getByRole("heading", { name: "Save script" })).toBeInTheDocument();
    expect(document.getElementById("save-script-path-input")).toHaveValue("src/blobert/a.py");
  });

  it("does not mount dialog when open is false", () => {
    render(
      <SaveScriptModal
        open={false}
        onClose={onClose}
        initialPath={null}
        fileTree={[]}
        onLoadFileTree={onLoadFileTree}
        isSaving={false}
        onSave={onSave}
      />,
    );
    expect(document.body.querySelector('[role="dialog"]')).toBeNull();
  });

  it("requires confirm step before onSave for Save", async () => {
    render(
      <SaveScriptModal
        open
        onClose={onClose}
        initialPath="x.py"
        fileTree={[]}
        onLoadFileTree={onLoadFileTree}
        isSaving={false}
        onSave={onSave}
      />,
    );
    await waitFor(() => expect(screen.getByRole("heading", { name: "Save script" })).toBeInTheDocument());

    const input = document.getElementById("save-script-path-input") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "  src/out.py  " } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Confirm save" })).toBeInTheDocument();
      expect(screen.getByRole("status")).toHaveTextContent("src/out.py");
    });
    expect(onSave).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Confirm save" }));

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith("src/out.py");
      expect(onClose).toHaveBeenCalled();
    });
  });

  it("Override current is disabled without initialPath", async () => {
    render(
      <SaveScriptModal
        open
        onClose={onClose}
        initialPath={null}
        fileTree={[]}
        onLoadFileTree={onLoadFileTree}
        isSaving={false}
        onSave={onSave}
      />,
    );
    await waitFor(() => expect(screen.getByRole("dialog")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Override current" })).toBeDisabled();
  });

  it("Override current uses confirm overwrite then onSave", async () => {
    render(
      <SaveScriptModal
        open
        onClose={onClose}
        initialPath="  open/current.py  "
        fileTree={[]}
        onLoadFileTree={onLoadFileTree}
        isSaving={false}
        onSave={onSave}
      />,
    );
    await waitFor(() => expect(screen.getByRole("dialog")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Override current" }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Confirm save" })).toBeInTheDocument();
      expect(screen.getByRole("status")).toHaveTextContent("open/current.py");
    });

    fireEvent.click(screen.getByRole("button", { name: "Confirm overwrite" }));

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith("open/current.py");
      expect(onClose).toHaveBeenCalled();
    });
  });
});
