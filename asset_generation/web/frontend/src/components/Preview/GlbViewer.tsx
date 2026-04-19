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
import * as THREE from "three";
import { useAppStore } from "../../store/useAppStore";
import { previewPathFromAssetsUrl } from "../../utils/previewPathFromAssetsUrl";
import { normalizedTextureMode } from "./ZoneTextureBlock";

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

/** Parse hex color string to normalized RGB Vector3 */
function parseHexToVector3(hex: string, fallback: THREE.Vector3 = new THREE.Vector3(0, 0, 0)): THREE.Vector3 {
  const h = (hex || "").trim().toLowerCase().replace(/^#/, "");
  if (h.length !== 6) {
    return fallback;
  }
  try {
    const r = parseInt(h.substring(0, 2), 16) / 255;
    const g = parseInt(h.substring(2, 4), 16) / 255;
    const b = parseInt(h.substring(4, 6), 16) / 255;
    return new THREE.Vector3(r, g, b);
  } catch {
    return fallback;
  }
}

/** Spot pattern shader material creator */
function createSpotsMaterial(spotColor: THREE.Vector3, bgColor: THREE.Vector3, density: number): THREE.ShaderMaterial {
  const vertexShader = `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `;

  const fragmentShader = `
    varying vec2 vUv;
    uniform vec3 uSpotColor;
    uniform vec3 uBgColor;
    uniform float uDensity;

    void main() {
      // Scale UV by density to create grid
      vec2 scaledUv = vUv * uDensity;

      // Get fractional part (position within grid cell)
      vec2 cellUv = fract(scaledUv);

      // Distance from cell center (0.5, 0.5)
      vec2 delta = cellUv - vec2(0.5);
      float dist = length(delta);

      // Spot radius in UV space
      float spotRadius = 0.35;

      // Choose color based on distance
      vec3 color = dist < spotRadius ? uSpotColor : uBgColor;

      gl_FragColor = vec4(color, 1.0);
    }
  `;

  return new THREE.ShaderMaterial({
    uniforms: {
      uSpotColor: { value: spotColor },
      uBgColor: { value: bgColor },
      uDensity: { value: density },
    },
    vertexShader,
    fragmentShader,
  });
}

/** Horizontal stripes: period ``uStripeWidth`` in UV space; 50/50 stripe vs gap per period. */
function createStripesMaterial(
  stripeColor: THREE.Vector3,
  bgColor: THREE.Vector3,
  stripeWidth: number,
): THREE.ShaderMaterial {
  const vertexShader = `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `;

  const fragmentShader = `
    varying vec2 vUv;
    uniform vec3 uStripeColor;
    uniform vec3 uBgColor;
    uniform float uStripeWidth;

    void main() {
      float w = max(0.05, min(1.0, uStripeWidth));
      float t = fract(vUv.x * (1.0 / w));
      vec3 color = t < 0.5 ? uStripeColor : uBgColor;
      gl_FragColor = vec4(color, 1.0);
    }
  `;

  return new THREE.ShaderMaterial({
    uniforms: {
      uStripeColor: { value: stripeColor },
      uBgColor: { value: bgColor },
      uStripeWidth: { value: stripeWidth },
    },
    vertexShader,
    fragmentShader,
  });
}

function Model({ url, animation }: { url: string; animation: string | null }) {
  const { scene, animations } = useGLTF(url);
  const { actions, names } = useAnimations(animations, scene);

  const setAvailableClips = useAppStore((s) => s.setAvailableClips);
  const setActiveAnimation = useAppStore((s) => s.setActiveAnimation);
  const isAnimationPaused = useAppStore((s) => s.isAnimationPaused);
  const enemy = useAppStore((s) => s.commandContext.enemy);
  const featVals = useAppStore((s) => s.animatedBuildOptionValues[enemy] ?? {});
  const legacyMode = useAppStore((s) => s.texture_mode);
  const legacySpot = useAppStore((s) => s.texture_spot_color);
  const legacySpotBg = useAppStore((s) => s.texture_spot_bg_color);
  const legacyDensity = useAppStore((s) => s.texture_spot_density);
  const legacyStripe = useAppStore((s) => s.texture_stripe_color);
  const legacyStripeBg = useAppStore((s) => s.texture_stripe_bg_color);
  const legacyStripeW = useAppStore((s) => s.texture_stripe_width);

  const textureMode =
    legacyMode !== undefined && legacyMode !== null
      ? String(legacyMode).trim().toLowerCase()
      : normalizedTextureMode("body", featVals);

  const spotColor =
    legacySpot !== undefined && legacySpot !== null
      ? String(legacySpot)
      : String(featVals.feat_body_texture_spot_color ?? "");
  const bgColor =
    legacySpotBg !== undefined && legacySpotBg !== null
      ? String(legacySpotBg)
      : String(featVals.feat_body_texture_spot_bg_color ?? "");
  const density =
    legacyDensity !== undefined && legacyDensity !== null
      ? Number(legacyDensity)
      : Number(featVals.feat_body_texture_spot_density ?? 1.0);

  const stripeColor =
    legacyStripe !== undefined && legacyStripe !== null
      ? String(legacyStripe)
      : String(featVals.feat_body_texture_stripe_color ?? "");
  const stripeBgColor =
    legacyStripeBg !== undefined && legacyStripeBg !== null
      ? String(legacyStripeBg)
      : String(featVals.feat_body_texture_stripe_bg_color ?? "");
  const stripeWidthRaw =
    legacyStripeW !== undefined && legacyStripeW !== null
      ? Number(legacyStripeW)
      : Number(featVals.feat_body_texture_stripe_width ?? 0.2);
  const stripeWidth = Math.max(
    0.05,
    Math.min(1.0, Number.isFinite(stripeWidthRaw) ? stripeWidthRaw : 0.2),
  );

  const prevUrl = useRef<string | null>(null);
  // Store original materials per mesh for restoration
  const originalMaterialsRef = useRef<Map<THREE.Object3D, THREE.Material | THREE.Material[]>>(new Map());
  // Store current shader material per mesh
  const shaderMaterialsRef = useRef<Map<THREE.Object3D, THREE.ShaderMaterial>>(new Map());

  useEffect(() => {
    scene.traverse((node: any) => {
      if (node.material) {
        if (node.material.metallic === undefined) {
          node.material.metallic = 0.0;
        }
      }
    });
  }, [scene]);

  // Handle texture mode switching and uniform updates
  useEffect(() => {
    if (textureMode === "spots" && spotColor !== undefined && bgColor !== undefined && density !== undefined) {
      const spotColorVec = parseHexToVector3(spotColor, new THREE.Vector3(0, 0, 0));
      const bgColorVec = parseHexToVector3(bgColor, new THREE.Vector3(1, 1, 1));

      scene.traverse((node: any) => {
        if (node.isMesh && node.material) {
          if (!originalMaterialsRef.current.has(node)) {
            originalMaterialsRef.current.set(node, node.material);
          }

          let shaderMat = shaderMaterialsRef.current.get(node);
          const needsSpots = !shaderMat || shaderMat.uniforms.uDensity === undefined;
          if (needsSpots) {
            if (shaderMat) shaderMat.dispose();
            shaderMat = createSpotsMaterial(spotColorVec, bgColorVec, density);
            shaderMaterialsRef.current.set(node, shaderMat);
            node.material = shaderMat;
          } else if (shaderMat) {
            shaderMat.uniforms.uSpotColor.value.copy(spotColorVec);
            shaderMat.uniforms.uBgColor.value.copy(bgColorVec);
            shaderMat.uniforms.uDensity.value = density;
          }
        }
      });
    } else if (textureMode === "stripes") {
      const stripeColorVec = parseHexToVector3(stripeColor, new THREE.Vector3(0, 0, 0));
      const bgColorVec = parseHexToVector3(stripeBgColor, new THREE.Vector3(1, 1, 1));

      scene.traverse((node: any) => {
        if (node.isMesh && node.material) {
          if (!originalMaterialsRef.current.has(node)) {
            originalMaterialsRef.current.set(node, node.material);
          }

          let shaderMat = shaderMaterialsRef.current.get(node);
          const needsStripes = !shaderMat || shaderMat.uniforms.uStripeWidth === undefined;
          if (needsStripes) {
            if (shaderMat) shaderMat.dispose();
            shaderMat = createStripesMaterial(stripeColorVec, bgColorVec, stripeWidth);
            shaderMaterialsRef.current.set(node, shaderMat);
            node.material = shaderMat;
          } else if (shaderMat) {
            shaderMat.uniforms.uStripeColor.value.copy(stripeColorVec);
            shaderMat.uniforms.uBgColor.value.copy(bgColorVec);
            shaderMat.uniforms.uStripeWidth.value = stripeWidth;
          }
        }
      });
    } else {
      scene.traverse((node: any) => {
        if (node.isMesh) {
          const originalMat = originalMaterialsRef.current.get(node);
          if (originalMat) {
            node.material = originalMat;
          }
          const sm = shaderMaterialsRef.current.get(node);
          if (sm) sm.dispose();
          shaderMaterialsRef.current.delete(node);
        }
      });
    }
  }, [
    scene,
    textureMode,
    spotColor,
    bgColor,
    density,
    stripeColor,
    stripeBgColor,
    stripeWidth,
  ]);

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
              scene.environmentIntensity = 2.5;
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
