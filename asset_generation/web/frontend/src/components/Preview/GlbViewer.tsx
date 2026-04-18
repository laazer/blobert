import { Component, Suspense, useCallback, useEffect, useRef, useState } from "react";
import type { CSSProperties } from "react";
import { Canvas } from "@react-three/fiber";
import {
  OrbitControls,
  Grid,
  Environment,
  useGLTF,
  useAnimations,
  GizmoHelper,
  GizmoViewport,
} from "@react-three/drei";
import { useAppStore } from "../../store/useAppStore";
import { previewPathFromAssetsUrl } from "../../utils/previewPathFromAssetsUrl";

type CanvasErrorBoundaryProps = {
  children: React.ReactNode;
  /** Clears preview URL in the store so the user can recover without picking another file first. */
  onClearPreview?: () => void;
};

// Error boundary so a bad GLB doesn't crash the whole app.
// Parent keys by asset path (ignores `?t=` cache-bust) so orbit/zoom survives tab switches and refresh timestamps.
class CanvasErrorBoundary extends Component<CanvasErrorBoundaryProps, { error: string | null }> {
  constructor(props: CanvasErrorBoundaryProps) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error: Error) {
    return { error: error.message };
  }
  render() {
    if (this.state.error) {
      return (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 12,
            height: "100%",
            background: "#1a0000",
            color: "#f88",
            fontSize: 12,
            padding: 16,
            textAlign: "center",
            boxSizing: "border-box",
          }}
        >
          <div style={{ maxWidth: "100%", overflowWrap: "anywhere" }}>GLB error: {this.state.error}</div>
          {this.props.onClearPreview ? (
            <button
              type="button"
              onClick={this.props.onClearPreview}
              style={{
                padding: "6px 12px",
                fontSize: 12,
                border: "1px solid #a44",
                borderRadius: 4,
                background: "#3c2020",
                color: "#fdd",
                cursor: "pointer",
              }}
            >
              Clear preview
            </button>
          ) : null}
        </div>
      );
    }
    return this.props.children;
  }
}

function Model({ url, animation }: { url: string; animation: string | null }) {
  const { scene, animations } = useGLTF(url);
  const { actions, names } = useAnimations(animations, scene);

  const setAvailableClips = useAppStore((s) => s.setAvailableClips);
  const setActiveAnimation = useAppStore((s) => s.setActiveAnimation);
  const isAnimationPaused = useAppStore((s) => s.isAnimationPaused);
  const prevUrl = useRef<string | null>(null);

  useEffect(() => {
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
      if (names.length > 0 && !animation) {
        setActiveAnimation(names[0]);
      }
    }
  }, [url, names, animation, setAvailableClips, setActiveAnimation]);

  return <primitive object={scene} />;
}

/** Stable React key for the GL canvas + error boundary: same GLB path keeps WebGL + orbit state across `?t=` updates. */
function glbViewerSceneKey(url: string | null): string {
  if (!url) return "__none__";
  return previewPathFromAssetsUrl(url) ?? url;
}

/** Inset from bottom-right of the canvas HUD (`GizmoHelper` margin: x = from right, y = from bottom). */
const GIZMO_MARGIN_X = 71;
const GIZMO_MARGIN_Y = 63;

const expandBtnStyle: CSSProperties = {
  position: "absolute",
  top: 8,
  right: 8,
  zIndex: 10,
  padding: "4px 8px",
  fontSize: 11,
  border: "1px solid #555",
  borderRadius: 3,
  background: "#3c3c3c",
  color: "#d4d4d4",
  cursor: "pointer",
};

export function GlbViewer() {
  const activeGlbUrl = useAppStore((s) => s.activeGlbUrl);
  const activeAnimation = useAppStore((s) => s.activeAnimation);
  const setIsAnimationPaused = useAppStore((s) => s.setIsAnimationPaused);
  const setActiveGlbUrl = useAppStore((s) => s.setActiveGlbUrl);
  const setAvailableClips = useAppStore((s) => s.setAvailableClips);
  const setActiveAnimation = useAppStore((s) => s.setActiveAnimation);
  const wrapRef = useRef<HTMLDivElement>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const onClearPreview = useCallback(() => {
    setActiveGlbUrl(null);
    setAvailableClips([]);
    setActiveAnimation(null);
    setIsAnimationPaused(false);
  }, [setActiveGlbUrl, setAvailableClips, setActiveAnimation, setIsAnimationPaused]);

  useEffect(() => {
    setIsAnimationPaused(false);
  }, [activeGlbUrl, setIsAnimationPaused]);

  const onExpandToggle = useCallback(() => {
    setIsExpanded((prev) => {
      requestAnimationFrame(() => window.dispatchEvent(new Event("resize")));
      return !prev;
    });
  }, []);

  const wrapStyle: CSSProperties = isExpanded
    ? { position: "fixed", inset: 0, width: "100vw", height: "100vh", zIndex: 9999, background: "#1a1a2e" }
    : { flex: 1, background: "#1a1a2e", position: "relative", overflow: "hidden" };

  return (
    <div ref={wrapRef} style={wrapStyle}>
      <button
        type="button"
        aria-pressed={isExpanded}
        aria-label={isExpanded ? "Collapse viewer" : "Expand viewer"}
        title={isExpanded ? "Collapse viewer" : "Expand viewer"}
        onClick={onExpandToggle}
        style={expandBtnStyle}
      >
        {isExpanded ? "Exit fullscreen" : "Fullscreen"}
      </button>
      {!activeGlbUrl ? (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center",
          height: "100%", color: "#555", fontSize: 12 }}>
          No model loaded — run a generation command
        </div>
      ) : (
        <CanvasErrorBoundary key={glbViewerSceneKey(activeGlbUrl)} onClearPreview={onClearPreview}>
          <Canvas
            camera={{ position: [0, 1.5, 3], fov: 50 }}
            style={{ height: "100%" }}
            onCreated={({ scene }) => {
              // Default (1) + studio IBL reads as blown-out / flat white on baked baseColor textures.
              // Gradient textures need higher intensity to be visible (0.38 is too dark).
              scene.environmentIntensity = 0.8;
            }}
          >
            <ambientLight intensity={0.35} />
            <directionalLight position={[5, 10, 5]} intensity={0.85} />
            <Suspense fallback={null}>
              <Model key={activeGlbUrl} url={activeGlbUrl} animation={activeAnimation} />
              <Environment preset="studio" />
            </Suspense>
            <Grid args={[10, 10]} cellSize={0.5} cellColor="#444" sectionColor="#666" />
            <OrbitControls makeDefault />
            <GizmoHelper alignment="bottom-right" margin={[GIZMO_MARGIN_X, GIZMO_MARGIN_Y]}>
              <GizmoViewport
                hideNegativeAxes
                axisColors={["#e53935", "#43a047", "#1e88e5"]}
                labelColor="#c8c8c8"
              />
            </GizmoHelper>
          </Canvas>
        </CanvasErrorBoundary>
      )}
    </div>
  );
}
