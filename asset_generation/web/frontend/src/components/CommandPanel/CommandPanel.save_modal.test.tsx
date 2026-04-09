// @vitest-environment jsdom
import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { cleanup, render, screen, waitFor, fireEvent } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { CommandPanel } from "./CommandPanel";

const saveModelModalPropsSpy = vi.fn();

vi.mock("./SaveModelModal", () => ({
  SaveModelModal: (props: { open: boolean; family: string; variantIndex?: number }) => {
    saveModelModalPropsSpy(props);
    return props.open ? (
      <div role="dialog" aria-label="Save model stub">
        variant:{props.variantIndex ?? "undef"}
      </div>
    ) : null;
  },
}));

vi.mock("../Terminal/useStreamingOutput", () => ({
  useStreamingOutput: () => ({ start: vi.fn() }),
}));

afterEach(() => {
  cleanup();
  saveModelModalPropsSpy.mockClear();
});

describe("CommandPanel Save script", () => {
  beforeEach(() => {
    useAppStore.setState({
      isSaving: false,
      isRunning: false,
      isDirty: true,
      selectedFile: "blobert/save_modal_test.py",
      fileTree: [],
      activeGlbUrl: null,
    });
  });

  it("opens portaled save dialog when Save script is clicked", async () => {
    render(<CommandPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Save script" }));

    await waitFor(() => {
      expect(document.body.querySelector('[role="dialog"]')).not.toBeNull();
    });
    expect(screen.getByRole("heading", { name: "Save script" })).toBeInTheDocument();
  });

  it("Save script is not disabled when buffer is clean but a file is selected", async () => {
    useAppStore.setState({ isDirty: false, selectedFile: "blobert/open.py" });
    render(<CommandPanel />);
    const btn = screen.getByRole("button", { name: "Save script" });
    expect(btn).not.toBeDisabled();
    fireEvent.click(btn);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
  });

  it("passes variantIndex from preview GLB into SaveModelModal for animated cmd", async () => {
    useAppStore.setState({
      activeGlbUrl: "/api/assets/animated_exports/spider_animated_03.glb?t=1",
    });
    render(<CommandPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Save model" }));

    await waitFor(() => {
      expect(saveModelModalPropsSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          open: true,
          family: "spider",
          variantIndex: 3,
        }),
      );
    });
    expect(screen.getByLabelText("Save model stub")).toHaveTextContent("variant:3");
  });

  it("defaults SaveModelModal variantIndex to 0 when preview is another family", async () => {
    useAppStore.setState({
      activeGlbUrl: "/api/assets/animated_exports/slug_animated_02.glb",
    });
    render(<CommandPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Save model" }));

    await waitFor(() => {
      expect(saveModelModalPropsSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          open: true,
          family: "spider",
          variantIndex: 0,
        }),
      );
    });
  });
});
