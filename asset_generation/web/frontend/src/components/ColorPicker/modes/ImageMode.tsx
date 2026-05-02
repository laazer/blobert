import { useCallback, useEffect, useRef, useState } from "react";
import { colorPickerStyles } from "../colorPickerStyles";
import { fetchTextureAssets, type TextureAsset } from "../../../api/client";
import {
  canvasDragToUvRect,
  type ImageUvRect,
  stringifyImageUvRect,
} from "../imageUvRect";

export interface ImageModeProps {
  file: File | null;
  preview?: string;
  assetId?: string;
  /** Normalized atlas bounds; null = full texture. */
  uvRect?: ImageUvRect | null;
  onFileChange: (
    file: File | null,
    preview?: string,
    assetId?: string,
    uvRect?: ImageUvRect | null,
  ) => void;
  disabled?: boolean;
}

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB
const ALLOWED_TYPES = ["image/png", "image/jpeg", "image/jpg", "image/webp"];

const atlasHint = {
  color: "#9d9d9d",
  fontSize: 11,
  marginTop: 4,
  lineHeight: 1.35,
} as const;

const MIN_ZOOM = 1;
const MAX_ZOOM = 12;
const WHEEL_ZOOM_FACTOR = 1.12;
const BTN_ZOOM_FACTOR = 1.25;

function clampNum(n: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, n));
}

/** Viewport-space px → image-space px (same coordinate system as UV mapping). */
function clientToImagePx(
  clientX: number,
  clientY: number,
  viewportEl: HTMLElement,
  pan: { x: number; y: number },
  zoom: number,
): { u: number; v: number } {
  const vr = viewportEl.getBoundingClientRect();
  const vx = clientX - vr.left;
  const vy = clientY - vr.top;
  const u = (vx - pan.x) / zoom;
  const v = (vy - pan.y) / zoom;
  return { u, v };
}

function AtlasOverlay(props: {
  previewUrl: string;
  uvRect: ImageUvRect | null | undefined;
  onUvRectChange: (r: ImageUvRect | null) => void;
  disabled: boolean;
}) {
  const { previewUrl, uvRect, onUvRectChange, disabled } = props;
  const viewportRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const applyZoomAtClientRef = useRef<(cx: number, cy: number, factor: number) => void>(() => {});
  const [size, setSize] = useState<{ w: number; h: number }>({ w: 0, h: 0 });
  const sizeRef = useRef(size);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const zoomRef = useRef(1);
  const panRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    zoomRef.current = zoom;
  }, [zoom]);
  useEffect(() => {
    panRef.current = pan;
  }, [pan]);
  useEffect(() => {
    sizeRef.current = size;
  }, [size]);

  const dragRef = useRef<{ u0: number; v0: number; u1: number; v1: number } | null>(null);
  const panDragRef = useRef<{
    startClientX: number;
    startClientY: number;
    startPanX: number;
    startPanY: number;
  } | null>(null);

  useEffect(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    zoomRef.current = 1;
    panRef.current = { x: 0, y: 0 };
  }, [previewUrl]);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || size.w === 0 || size.h === 0) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const active = dragRef.current;
    let x0: number;
    let y0: number;
    let x1: number;
    let y1: number;
    if (active) {
      const au0 = clampNum(active.u0, 0, size.w);
      const au1 = clampNum(active.u1, 0, size.w);
      const av0 = clampNum(active.v0, 0, size.h);
      const av1 = clampNum(active.v1, 0, size.h);
      x0 = Math.min(au0, au1);
      y0 = Math.min(av0, av1);
      x1 = Math.max(au0, au1);
      y1 = Math.max(av0, av1);
    } else if (uvRect) {
      x0 = uvRect.u0 * size.w;
      x1 = uvRect.u1 * size.w;
      y0 = (1 - uvRect.v1) * size.h;
      y1 = (1 - uvRect.v0) * size.h;
    } else {
      return;
    }
    ctx.fillStyle = "rgba(79, 195, 247, 0.15)";
    ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
    ctx.strokeStyle = "#4fc3f7";
    ctx.lineWidth = 2;
    ctx.strokeRect(x0, y0, x1 - x0, y1 - y0);
  }, [size.h, size.w, uvRect]);

  useEffect(() => {
    draw();
  }, [draw, previewUrl, zoom, pan]);

  const onImgLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    const maxW = 280;
    const scale = Math.min(1, maxW / img.naturalWidth);
    const w = Math.round(img.naturalWidth * scale);
    const h = Math.round(img.naturalHeight * scale);
    setSize({ w, h });
    const canvas = canvasRef.current;
    if (canvas) {
      canvas.width = w;
      canvas.height = h;
    }
    requestAnimationFrame(draw);
  };

  /** Multiply current zoom by ``factor``, keeping image px under (clientX, clientY) fixed. */
  const applyZoomAtClient = (clientX: number, clientY: number, factor: number) => {
    const el = viewportRef.current;
    if (!el || sizeRef.current.w === 0) return;
    const prevZ = zoomRef.current;
    const prevPan = panRef.current;
    const newZ = clampNum(prevZ * factor, MIN_ZOOM, MAX_ZOOM);
    const vr = el.getBoundingClientRect();
    const vx = clientX - vr.left;
    const vy = clientY - vr.top;
    const worldU = (vx - prevPan.x) / prevZ;
    const worldV = (vy - prevPan.y) / prevZ;
    let nx = vx - worldU * newZ;
    let ny = vy - worldV * newZ;
    if (newZ <= MIN_ZOOM) {
      nx = 0;
      ny = 0;
    }
    zoomRef.current = newZ;
    panRef.current = { x: nx, y: ny };
    setZoom(newZ);
    setPan({ x: nx, y: ny });
  };

  applyZoomAtClientRef.current = applyZoomAtClient;

  useEffect(() => {
    const el = viewportRef.current;
    if (!el) return;
    const onWheelNative = (e: WheelEvent) => {
      if (disabled || sizeRef.current.w === 0) return;
      e.preventDefault();
      e.stopPropagation();
      const factor = e.deltaY > 0 ? 1 / WHEEL_ZOOM_FACTOR : WHEEL_ZOOM_FACTOR;
      applyZoomAtClientRef.current(e.clientX, e.clientY, factor);
    };
    el.addEventListener("wheel", onWheelNative, { passive: false });
    return () => el.removeEventListener("wheel", onWheelNative);
  }, [disabled, previewUrl]);

  const zoomAroundViewportCenter = (mult: number) => {
    const el = viewportRef.current;
    if (!el || sizeRef.current.w === 0) return;
    const vr = el.getBoundingClientRect();
    applyZoomAtClient(vr.left + vr.width / 2, vr.top + vr.height / 2, mult);
  };

  const resetView = () => {
    zoomRef.current = 1;
    panRef.current = { x: 0, y: 0 };
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const onPointerDown = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (disabled) return;
    const vp = viewportRef.current;
    if (!vp || size.w === 0) return;
    const panMode = e.altKey || e.button === 1;
    if (panMode) {
      e.preventDefault();
      panDragRef.current = {
        startClientX: e.clientX,
        startClientY: e.clientY,
        startPanX: panRef.current.x,
        startPanY: panRef.current.y,
      };
      e.currentTarget.setPointerCapture(e.pointerId);
      return;
    }
    if (e.button !== 0) return;
    e.preventDefault();
    const { u, v } = clientToImagePx(e.clientX, e.clientY, vp, panRef.current, zoomRef.current);
    const cu = clampNum(u, 0, size.w);
    const cv = clampNum(v, 0, size.h);
    dragRef.current = { u0: cu, v0: cv, u1: cu, v1: cv };
    e.currentTarget.setPointerCapture(e.pointerId);
    draw();
  };

  const onPointerMove = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const vp = viewportRef.current;
    if (!vp || size.w === 0) return;
    if (panDragRef.current) {
      const p = panDragRef.current;
      const dx = e.clientX - p.startClientX;
      const dy = e.clientY - p.startClientY;
      const np = { x: p.startPanX + dx, y: p.startPanY + dy };
      panRef.current = np;
      setPan(np);
      return;
    }
    if (!dragRef.current || disabled) return;
    const { u, v } = clientToImagePx(e.clientX, e.clientY, vp, panRef.current, zoomRef.current);
    dragRef.current.u1 = clampNum(u, 0, size.w);
    dragRef.current.v1 = clampNum(v, 0, size.h);
    draw();
  };

  const finishPointer = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const vp = viewportRef.current;
    const canvas = canvasRef.current;
    if (panDragRef.current) {
      panDragRef.current = null;
      try {
        e.currentTarget.releasePointerCapture(e.pointerId);
      } catch {
        /* ignore */
      }
      return;
    }
    const d = dragRef.current;
    if (!canvas || !d || !vp || disabled) {
      dragRef.current = null;
      draw();
      return;
    }
    try {
      canvas.releasePointerCapture(e.pointerId);
    } catch {
      /* ignore */
    }
    const { u, v } = clientToImagePx(e.clientX, e.clientY, vp, panRef.current, zoomRef.current);
    d.u1 = clampNum(u, 0, size.w);
    d.v1 = clampNum(v, 0, size.h);
    const uv = canvasDragToUvRect(d.u0, d.v0, d.u1, d.v1, size.w, size.h);
    dragRef.current = null;
    draw();
    if (uv.u1 - uv.u0 > 0.002 && uv.v1 - uv.v0 > 0.002) {
      onUvRectChange(uv);
    }
  };

  const innerTransform =
    size.w > 0 ? { transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`, transformOrigin: "0 0" as const } : {};

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 6,
          alignItems: "center",
        }}
      >
        <span style={{ color: "#9d9d9d", fontSize: 11 }}>Zoom</span>
        <button
          type="button"
          disabled={disabled || zoom <= MIN_ZOOM}
          onClick={() => zoomAroundViewportCenter(1 / BTN_ZOOM_FACTOR)}
          style={{
            background: "#3c3c3c",
            color: "#d4d4d4",
            border: "1px solid #555555",
            borderRadius: 3,
            padding: "2px 8px",
            fontSize: 12,
            cursor: disabled ? "not-allowed" : "pointer",
          }}
          aria-label="Zoom out"
        >
          −
        </button>
        <span style={{ color: "#c8c8c8", fontSize: 11, minWidth: 44, textAlign: "center" }}>
          {Math.round(zoom * 100)}%
        </span>
        <button
          type="button"
          disabled={disabled || zoom >= MAX_ZOOM}
          onClick={() => zoomAroundViewportCenter(BTN_ZOOM_FACTOR)}
          style={{
            background: "#3c3c3c",
            color: "#d4d4d4",
            border: "1px solid #555555",
            borderRadius: 3,
            padding: "2px 8px",
            fontSize: 12,
            cursor: disabled ? "not-allowed" : "pointer",
          }}
          aria-label="Zoom in"
        >
          +
        </button>
        <button
          type="button"
          disabled={disabled || (zoom <= MIN_ZOOM && pan.x === 0 && pan.y === 0)}
          onClick={resetView}
          style={{
            background: "#3c3c3c",
            color: "#d4d4d4",
            border: "1px solid #555555",
            borderRadius: 3,
            padding: "2px 8px",
            fontSize: 11,
            cursor: disabled ? "not-allowed" : "pointer",
          }}
        >
          Reset view
        </button>
      </div>

      <div
        ref={viewportRef}
        style={{
          position: "relative",
          overflow: "hidden",
          width: size.w || undefined,
          height: size.h || undefined,
          maxWidth: 280,
          borderRadius: 3,
          outline: "1px solid #444",
        }}
      >
        <div style={{ ...innerTransform, width: size.w, height: size.h, position: "relative" }}>
          <img
            src={previewUrl}
            alt=""
            width={size.w || undefined}
            height={size.h || undefined}
            crossOrigin={previewUrl.startsWith("blob:") ? undefined : "anonymous"}
            onLoad={onImgLoad}
            draggable={false}
            style={{
              display: "block",
              width: size.w || undefined,
              height: size.h || undefined,
              userSelect: "none",
              pointerEvents: "none",
            }}
          />
          <canvas
            ref={canvasRef}
            width={size.w}
            height={size.h}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={finishPointer}
            onPointerCancel={finishPointer}
            onAuxClick={(e) => e.preventDefault()}
            style={{
              position: "absolute",
              left: 0,
              top: 0,
              width: size.w || undefined,
              height: size.h || undefined,
              cursor: disabled ? "default" : "crosshair",
              touchAction: "none",
            }}
          />
        </div>
      </div>
    </div>
  );
}

/**
 * Image texture picker mode.
 * Provides both preloaded texture selection and custom file upload.
 * Users can select from available textures or upload custom image textures.
 */
export function ImageMode({
  file,
  preview,
  assetId: _assetId,
  uvRect,
  onFileChange,
  disabled = false,
}: ImageModeProps) {
  const [error, setError] = useState<string>("");
  const [textures, setTextures] = useState<TextureAsset[]>([]);
  const [loadingTextures, setLoadingTextures] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const assets = await fetchTextureAssets();
        setTextures(assets);
      } catch (err) {
        console.error("Failed to load texture assets:", err);
      } finally {
        setLoadingTextures(false);
      }
    })();
  }, []);

  useEffect(() => {
    return () => {
      if (preview && preview.startsWith("blob:")) {
        URL.revokeObjectURL(preview);
      }
    };
  }, [preview]);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.currentTarget.files?.[0];
    if (!selectedFile) return;

    if (!ALLOWED_TYPES.includes(selectedFile.type)) {
      setError("Only PNG, JPEG, and WebP images are supported");
      onFileChange(null);
      return;
    }

    if (selectedFile.size > MAX_FILE_SIZE) {
      setError("File size must be less than 5 MB");
      onFileChange(null);
      return;
    }

    const previewUrl = URL.createObjectURL(selectedFile);
    setError("");
    onFileChange(selectedFile, previewUrl, undefined, null);
  };

  const handleClear = () => {
    setError("");
    onFileChange(null, "", "", null);
  };

  const handleSelectTexture = (texture: TextureAsset & { url?: string }) => {
    setError("");
    if (texture.url) {
      onFileChange(null, texture.url, texture.id, null);
    }
  };

  const fileName = file?.name || "No file selected";

  return (
    <div style={colorPickerStyles.modeContent}>
      {!loadingTextures && textures.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 8 }}>
          <div style={colorPickerStyles.fileInputLabel}>Preloaded Textures</div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(60px, 1fr))",
              gap: 4,
            }}
          >
            {textures.map((texture) => {
              const textureWithUrl = texture as TextureAsset & { url?: string };
              return (
                <button
                  key={textureWithUrl.id}
                  type="button"
                  onClick={() => handleSelectTexture(textureWithUrl)}
                  disabled={disabled}
                  title={textureWithUrl.display_name}
                  style={{
                    background: preview === textureWithUrl.url ? "#0e639c" : "#3c3c3c",
                    border: "1px solid #555555",
                    borderRadius: 3,
                    padding: 0,
                    cursor: disabled ? "not-allowed" : "pointer",
                    opacity: disabled ? 0.5 : 1,
                    height: 60,
                    overflow: "hidden",
                    position: "relative",
                  }}
                >
                  <img
                    src={textureWithUrl.url}
                    alt={textureWithUrl.display_name}
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover",
                      pointerEvents: "none",
                    }}
                  />
                </button>
              );
            })}
          </div>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        <div style={colorPickerStyles.fileInputLabel}>Upload Custom</div>

        <div style={colorPickerStyles.fileInputWrapper}>
          <input
            type="file"
            aria-label="Upload texture image"
            accept={ALLOWED_TYPES.join(",")}
            onChange={handleFileSelect}
            disabled={disabled}
            style={{
              ...colorPickerStyles.fileInput,
              opacity: disabled ? 0.5 : 1,
              cursor: disabled ? "not-allowed" : "pointer",
            }}
          />
        </div>

        <div style={colorPickerStyles.previewText}>{fileName}</div>

        {error && (
          <div
            style={{
              ...colorPickerStyles.previewText,
              color: "#f48771",
            }}
          >
            {error}
          </div>
        )}

        {preview && (
          <div style={colorPickerStyles.previewContainer}>
            <AtlasOverlay
              previewUrl={preview}
              uvRect={uvRect}
              disabled={disabled}
              onUvRectChange={(r) => onFileChange(null, preview, _assetId, r)}
            />
            <p style={atlasHint}>
              <strong style={{ color: "#bbb" }}>Wheel</strong> zooms toward the cursor;{" "}
              <strong style={{ color: "#bbb" }}>− / +</strong> zooms about the center;{" "}
              <strong style={{ color: "#bbb" }}>Alt‑drag</strong> or <strong style={{ color: "#bbb" }}>middle‑click drag</strong>{" "}
              pans when zoomed. Drag to select a tile (optional). UV origin matches Blender (v increases upward).
            </p>
            {uvRect ? (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
                <span style={colorPickerStyles.previewText}>{stringifyImageUvRect(uvRect)}</span>
                <button
                  type="button"
                  onClick={() => onFileChange(null, preview, _assetId, null)}
                  disabled={disabled}
                  style={{
                    background: "#3c3c3c",
                    color: "#d4d4d4",
                    border: "1px solid #555555",
                    borderRadius: 3,
                    padding: "4px 8px",
                    fontSize: 11,
                    cursor: disabled ? "not-allowed" : "pointer",
                  }}
                >
                  Use full image
                </button>
              </div>
            ) : null}
            <div style={colorPickerStyles.previewText}>
              {file?.size && file.size > 0 ? `${(file.size / 1024).toFixed(1)} KB` : ""}
            </div>
            <button
              type="button"
              onClick={handleClear}
              disabled={disabled}
              style={{
                background: "#3c3c3c",
                color: "#d4d4d4",
                border: "1px solid #555555",
                borderRadius: 3,
                padding: "4px 8px",
                fontSize: 11,
                cursor: disabled ? "not-allowed" : "pointer",
                opacity: disabled ? 0.5 : 1,
              }}
            >
              Clear
            </button>
          </div>
        )}

        <div style={colorPickerStyles.previewText}>Supported: PNG, JPEG, WebP (max 5 MB)</div>
      </div>
    </div>
  );
}
