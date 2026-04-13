// @vitest-environment jsdom
/** GLB load failure + recovery — mocks R3F so jsdom never touches WebGL. */
import type { ReactNode } from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { cleanup, render, screen, fireEvent, waitFor } from "@testing-library/react";
import { useAppStore } from "../../store/useAppStore";
import { GlbViewer } from "./GlbViewer";

vi.mock("@react-three/fiber", () => ({
  Canvas: function MockCanvas({ children }: { children: ReactNode }) {
    return <div data-testid="mock-canvas">{children}</div>;
  },
}));

vi.mock("@react-three/drei", async () => {
  const THREE = await import("three");
  return {
    useGLTF: (url: string) => {
      if (url.includes("__bad__")) {
        throw new Error('fetch for "http://localhost:5173/api/assets/x" responded with 404: Not Found');
      }
      return { scene: new THREE.Object3D(), animations: [] };
    },
    useAnimations: () => ({ actions: {} as Record<string, unknown>, names: [] as string[] }),
    OrbitControls: () => null,
    Grid: () => null,
    Environment: () => null,
    GizmoHelper: ({ children }: { children: ReactNode }) => <>{children}</>,
    GizmoViewport: () => null,
  };
});

describe("GlbViewer GLB load errors", () => {
  beforeEach(() => {
    useAppStore.setState({
      activeGlbUrl: null,
      activeAnimation: null,
      availableClips: [],
      isAnimationPaused: false,
    });
  });

  afterEach(() => {
    cleanup();
  });

  it("Clear preview resets store after a failed load", async () => {
    useAppStore.setState({
      activeGlbUrl: "/api/assets/animated_exports/__bad__.glb?t=1",
    });
    render(<GlbViewer />);
    await waitFor(() => {
      expect(screen.getByText(/GLB error:/)).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: "Clear preview" }));
    await waitFor(() => {
      expect(screen.getByText(/No model loaded/)).toBeInTheDocument();
    });
    expect(useAppStore.getState().activeGlbUrl).toBeNull();
    expect(useAppStore.getState().availableClips).toEqual([]);
  });

  it("renders the preview canvas when a model URL is active", async () => {
    useAppStore.setState({
      activeGlbUrl: "/api/assets/animated_exports/__ok__.glb?t=0",
    });
    render(<GlbViewer />);
    await waitFor(() => {
      expect(screen.getByTestId("mock-canvas")).toBeInTheDocument();
    });
  });

  it("switching activeGlbUrl remounts the error boundary so a valid URL recovers without Clear preview", async () => {
    useAppStore.setState({
      activeGlbUrl: "/api/assets/animated_exports/__bad__.glb?t=1",
    });
    const { rerender } = render(<GlbViewer />);
    await waitFor(() => {
      expect(screen.getByText(/GLB error:/)).toBeInTheDocument();
    });

    useAppStore.setState({
      activeGlbUrl: "/api/assets/animated_exports/__ok__.glb?t=2",
    });
    rerender(<GlbViewer />);

    await waitFor(() => {
      expect(screen.queryByText(/GLB error:/)).not.toBeInTheDocument();
      expect(screen.getByTestId("mock-canvas")).toBeInTheDocument();
    });
  });
});
