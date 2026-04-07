import { Component, Suspense, useEffect, useRef } from "react";
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

export function GlbViewer() {
  const activeGlbUrl = useAppStore((s) => s.activeGlbUrl);
  const activeAnimation = useAppStore((s) => s.activeAnimation);

  return (
    <div style={{ flex: 1, background: "#1a1a2e", position: "relative", overflow: "hidden" }}>
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
