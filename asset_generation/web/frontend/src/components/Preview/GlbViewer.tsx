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
import { normalizeAnimatedSlug, PLAYER_PROCEDURAL_BUILD_SLUG } from "../../utils/enemyDisplay";
import { PLAYER_COLORS } from "../CommandPanel/commandLogic";

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

function parseHexColor(raw: unknown): THREE.Color {
  if (typeof raw !== "string") return new THREE.Color(1, 1, 1);
  const hex = raw.trim().toLowerCase();
  if (!hex) return new THREE.Color(1, 1, 1);
  try {
    return new THREE.Color(`#${hex}`);
  } catch {
    return new THREE.Color(1, 1, 1);
  }
}

function makeTextureShaderMaterial(
  mode: "gradient" | "spots" | "stripes",
  params: {
    gradA: THREE.Color;
    gradB: THREE.Color;
    gradDirection: "horizontal" | "vertical" | "radial";
    spotColor: THREE.Color;
    spotBgColor: THREE.Color;
    spotDensity: number;
    stripeColor: THREE.Color;
    stripeBgColor: THREE.Color;
    stripeWidth: number;
  },
): THREE.ShaderMaterial {
  const uniforms = {
    uMode: { value: mode === "gradient" ? 0 : mode === "spots" ? 1 : 2 },
    uGradA: { value: params.gradA },
    uGradB: { value: params.gradB },
    uGradDirection: {
      value: params.gradDirection === "horizontal" ? 0 : params.gradDirection === "vertical" ? 1 : 2,
    },
    uSpotColor: { value: params.spotColor },
    uSpotBgColor: { value: params.spotBgColor },
    uSpotDensity: { value: params.spotDensity },
    uStripeColor: { value: params.stripeColor },
    uStripeBgColor: { value: params.stripeBgColor },
    uStripeWidth: { value: params.stripeWidth },
  };

  return new THREE.ShaderMaterial({
    uniforms,
    vertexShader: `
varying vec2 vUv;
varying vec3 vPos;
void main() {
  vUv = uv;
  vPos = position;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
    `,
    fragmentShader: `
precision highp float;
varying vec2 vUv;
varying vec3 vPos;

uniform int uMode; // 0 gradient, 1 spots, 2 stripes
uniform vec3 uGradA;
uniform vec3 uGradB;
uniform int uGradDirection; // 0 horiz, 1 vert, 2 radial
uniform vec3 uSpotColor;
uniform vec3 uSpotBgColor;
uniform float uSpotDensity;
uniform vec3 uStripeColor;
uniform vec3 uStripeBgColor;
uniform float uStripeWidth;

float hash21(vec2 p) {
  p = fract(p * vec2(123.34, 345.45));
  p += dot(p, p + 34.345);
  return fract(p.x * p.y);
}

void main() {
  vec2 uv = vUv;
  // UV fallback: if mesh has no UVs, vUv is (0,0) for all fragments. Use position-derived coords then.
  if (uv.x == 0.0 && uv.y == 0.0) {
    uv = vPos.xy * 0.25 + vec2(0.5);
  }

  vec3 color = vec3(1.0);
  if (uMode == 0) {
    float t = 0.0;
    if (uGradDirection == 0) t = uv.x;
    else if (uGradDirection == 1) t = uv.y;
    else {
      vec2 d = uv - vec2(0.5);
      t = clamp(length(d) * 1.41421356, 0.0, 1.0);
    }
    color = mix(uGradA, uGradB, clamp(t, 0.0, 1.0));
  } else if (uMode == 1) {
    float density = max(0.001, uSpotDensity);
    vec2 p = uv * density * 8.0;
    vec2 cell = floor(p);
    vec2 f = fract(p) - 0.5;
    float r = 0.15 + 0.25 * hash21(cell);
    float d = length(f);
    float spot = smoothstep(r, r - 0.02, d);
    color = mix(uSpotBgColor, uSpotColor, spot);
  } else {
    float w = max(0.001, uStripeWidth);
    float x = uv.x / w;
    float stripe = step(0.5, fract(x));
    color = mix(uStripeBgColor, uStripeColor, stripe);
  }

  gl_FragColor = vec4(color, 1.0);
}
    `,
  });
}

function Model({ url, animation }: { url: string; animation: string | null }) {
  const { scene, animations } = useGLTF(url);
  const { actions, names } = useAnimations(animations, scene);

  // Expose clip names upward so AnimationControls can show real clips
  const setAvailableClips = useAppStore((s) => s.setAvailableClips);
  const setActiveAnimation = useAppStore((s) => s.setActiveAnimation);
  const isAnimationPaused = useAppStore((s) => s.isAnimationPaused);
  const prevUrl = useRef<string | null>(null);
  const commandContext = useAppStore((s) => s.commandContext);
  const animatedBuildOptionValues = useAppStore((s) => s.animatedBuildOptionValues);
  const originalMaterialsRef = useRef<Map<string, THREE.Material | THREE.Material[]>>(new Map());
  const appliedMaterialRef = useRef<THREE.ShaderMaterial | null>(null);

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
      // New model: clear captured materials and dispose any previous shader.
      originalMaterialsRef.current.clear();
      appliedMaterialRef.current?.dispose();
      appliedMaterialRef.current = null;
      prevUrl.current = url;
      setAvailableClips(names);
      // Auto-select first clip on new model
      if (names.length > 0 && !animation) {
        setActiveAnimation(names[0]);
      }
    }
  }, [url, names, animation, setAvailableClips, setActiveAnimation]);

  useEffect(() => {
    const { cmd, enemy } = commandContext;
    const playerColor = (enemy || "").trim().toLowerCase();
    const slug =
      cmd === "player" && PLAYER_COLORS.includes(playerColor)
        ? PLAYER_PROCEDURAL_BUILD_SLUG
        : normalizeAnimatedSlug(enemy);

    const opts = animatedBuildOptionValues[slug] ?? {};
    const rawMode = opts.texture_mode;
    const modeStr = typeof rawMode === "string" ? rawMode.trim().toLowerCase() : "none";
    const mode =
      modeStr === "gradient" || modeStr === "spots" || modeStr === "stripes" || modeStr === "none"
        ? modeStr
        : "none";

    // Capture original materials once per url.
    scene.traverse((obj) => {
      if (!(obj instanceof THREE.Mesh)) return;
      if (!originalMaterialsRef.current.has(obj.uuid)) {
        originalMaterialsRef.current.set(obj.uuid, obj.material);
      }
    });

    if (mode === "none") {
      // Restore.
      scene.traverse((obj) => {
        if (!(obj instanceof THREE.Mesh)) return;
        const orig = originalMaterialsRef.current.get(obj.uuid);
        if (orig) obj.material = orig;
      });
      appliedMaterialRef.current?.dispose();
      appliedMaterialRef.current = null;
      return;
    }

    const shader = makeTextureShaderMaterial(mode, {
      gradA: parseHexColor(opts.texture_grad_color_a),
      gradB: parseHexColor(opts.texture_grad_color_b),
      gradDirection:
        typeof opts.texture_grad_direction === "string" &&
        (opts.texture_grad_direction === "horizontal" ||
          opts.texture_grad_direction === "vertical" ||
          opts.texture_grad_direction === "radial")
          ? opts.texture_grad_direction
          : "horizontal",
      spotColor: parseHexColor(opts.texture_spot_color),
      spotBgColor: parseHexColor(opts.texture_spot_bg_color),
      spotDensity: typeof opts.texture_spot_density === "number" ? opts.texture_spot_density : 1.0,
      stripeColor: parseHexColor(opts.texture_stripe_color),
      stripeBgColor: parseHexColor(opts.texture_stripe_bg_color),
      stripeWidth: typeof opts.texture_stripe_width === "number" ? opts.texture_stripe_width : 0.2,
    });

    appliedMaterialRef.current?.dispose();
    appliedMaterialRef.current = shader;

    scene.traverse((obj) => {
      if (!(obj instanceof THREE.Mesh)) return;
      obj.material = shader;
    });
  }, [scene, commandContext, animatedBuildOptionValues, url]);

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
    // Reset pause on model swap for predictable playback
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
          <Canvas camera={{ position: [0, 1.5, 3], fov: 50 }} style={{ height: "100%" }}>
            <ambientLight intensity={0.5} />
            <directionalLight position={[5, 10, 5]} intensity={1} />
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
