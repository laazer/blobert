// @vitest-environment jsdom
import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { cleanup, render, screen, waitFor, fireEvent } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { CommandPanel } from "./CommandPanel";

vi.mock("../Terminal/useStreamingOutput", () => ({
  useStreamingOutput: () => ({ start: vi.fn() }),
}));

afterEach(() => {
  cleanup();
});

describe("CommandPanel Save script", () => {
  beforeEach(() => {
    useAppStore.setState({
      isSaving: false,
      isRunning: false,
      isDirty: true,
      selectedFile: "blobert/save_modal_test.py",
      fileTree: [],
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
});
