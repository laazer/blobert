import { Component, Suspense, useCallback, useEffect, useRef, useState } from "react";
import type { CSSProperties } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Grid, Environment, useGLTF, useAnimations } from "@react-three/drei";
import { useAppStore } from "../../store/useAppStore";

// Error boundary so a bad GLB doesn't crash the whole app
class CanvasErrorBoundary extends Component<{ children: React.ReactNode }, { error: string | null }> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error: Error) {
    return { error: error.message };
  }
  render() {
    if (this.state.error) {
      return (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center",
          height: "100%", background: "#1a0000", color: "#f88", fontSize: 12, padding: 16 }}>
          GLB error: {this.state.error}
        </div>
      );
    }
    return this.props.children;
  }
}

function Model({ url, animation }: { url: string; animation: string | null }) {
  const { scene, animations } = useGLTF(url);
  const { actions, names } = useAnimations(animations, scene);

  // Expose clip names upward so AnimationControls can show real clips
  const setAvailableClips = useAppStore((s) => s.setAvailableClips);
  const setActiveAnimation = useAppStore((s) => s.setActiveAnimation);
  const isAnimationPaused = useAppStore((s) => s.isAnimationPaused);
  const prevUrl = useRef<string | null>(null);

  useEffect(() => {
    // Stop all on url change
    Object.values(actions).forEach((a) => a?.stop());
    if (animation && actions[animation]) {
      actions[animation]?.reset().fadeIn(0.3).play();
    } else if (names.length > 0) {
      actions[names[0]]?.reset().fadeIn(0.3).play();
    }
  }, [animation, url, actions, names]);

  useEffect(() => {
    Object.values(actions).forEach((a) => {
      if (!a) return;
      a.paused = isAnimationPaused;
    });
  }, [actions, isAnimationPaused]);

  useEffect(() => {
    if (prevUrl.current !== url) {
      prevUrl.current = url;
      setAvailableClips(names);
      // Auto-select first clip on new model
      if (names.length > 0 && !animation) {
        setActiveAnimation(names[0]);
      }
    }
  }, [url, names, animation, setAvailableClips, setActiveAnimation]);

  return <primitive object={scene} />;
}

function useFullscreenApiSupported(): boolean {
  const [supported, setSupported] = useState(false);
  useEffect(() => {
    if (typeof document === "undefined") return;
    const probe = document.createElement("div");
    setSupported(Boolean(document.fullscreenEnabled && typeof probe.requestFullscreen === "function"));
  }, []);
  return supported;
}

const fullscreenBtnStyle: CSSProperties = {
  position: "absolute",
  top: 8,
  right: 8,
  zIndex: 5,
  padding: "4px 8px",
  fontSize: 11,
  border: "1px solid #555",
  borderRadius: 3,
  background: "#3c3c3c",
  color: "#d4d4d4",
};

export function GlbViewer() {
  const activeGlbUrl = useAppStore((s) => s.activeGlbUrl);
  const activeAnimation = useAppStore((s) => s.activeAnimation);
  const setIsAnimationPaused = useAppStore((s) => s.setIsAnimationPaused);
  const wrapRef = useRef<HTMLDivElement>(null);
  const fsSupported = useFullscreenApiSupported();
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    // Reset pause on model swap for predictable playback
    setIsAnimationPaused(false);
  }, [activeGlbUrl, setIsAnimationPaused]);

  useEffect(() => {
    const sync = () => {
      const el = wrapRef.current;
      setIsFullscreen(Boolean(el && document.fullscreenElement === el));
    };
    document.addEventListener("fullscreenchange", sync);
    return () => document.removeEventListener("fullscreenchange", sync);
  }, []);

  useEffect(() => {
    const bumpResize = () => {
      requestAnimationFrame(() => window.dispatchEvent(new Event("resize")));
    };
    document.addEventListener("fullscreenchange", bumpResize);
    return () => document.removeEventListener("fullscreenchange", bumpResize);
  }, []);

  const onFullscreenToggle = useCallback(async () => {
    const el = wrapRef.current;
    if (!el || !fsSupported) return;
    try {
      if (document.fullscreenElement === el) {
        await document.exitFullscreen();
      } else {
        await el.requestFullscreen();
      }
    } catch {
      /* user gesture / policy — ignore */
    }
  }, [fsSupported]);

  return (
    <div ref={wrapRef} style={{ flex: 1, background: "#1a1a2e", position: "relative", overflow: "hidden" }}>
      <button
        type="button"
        aria-pressed={isFullscreen}
        aria-label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
        disabled={!fsSupported}
        title={
          fsSupported ? (isFullscreen ? "Exit fullscreen" : "Enter fullscreen") : "Fullscreen not supported"
        }
        onClick={onFullscreenToggle}
        style={{
          ...fullscreenBtnStyle,
          cursor: fsSupported ? "pointer" : "not-allowed",
          opacity: fsSupported ? 1 : 0.5,
        }}
      >
        {isFullscreen ? "Exit fullscreen" : "Fullscreen"}
      </button>
      {!activeGlbUrl ? (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center",
          height: "100%", color: "#555", fontSize: 12 }}>
          No model loaded — run a generation command
        </div>
      ) : (
        <CanvasErrorBoundary>
          <Canvas camera={{ position: [0, 1.5, 3], fov: 50 }} style={{ height: "100%" }}>
            <ambientLight intensity={0.5} />
            <directionalLight position={[5, 10, 5]} intensity={1} />
            <Suspense fallback={null}>
              <Model key={activeGlbUrl} url={activeGlbUrl} animation={activeAnimation} />
              <Environment preset="studio" />
            </Suspense>
            <Grid args={[10, 10]} cellSize={0.5} cellColor="#444" sectionColor="#666" />
            <OrbitControls makeDefault />
          </Canvas>
        </CanvasErrorBoundary>
      )}
    </div>
  );
}
