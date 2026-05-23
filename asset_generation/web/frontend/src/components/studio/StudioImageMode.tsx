import { useEffect, useRef, useState } from "react";
import { fetchTextureAssets, type TextureAsset } from "../../api/client";
import { AtlasOverlay } from "../ColorPicker/modes/ImageMode";
import type { ImageModeProps } from "../ColorPicker/modes/ImageMode";
import { stringifyImageUvRect } from "../ColorPicker/imageUvRect";
import { STUDIO_INK_PRIMARY } from "../../styles/studioTokens";
import {
  studioChipButtonStyle,
  studioFillContentStyle,
  studioLabelCaps,
} from "./studioFillStyles";

const MAX_FILE_SIZE = 5 * 1024 * 1024;
const ALLOWED_TYPES = ["image/png", "image/jpeg", "image/jpg", "image/webp"];
/** Hero crop viewport — same interaction as legacy ImageMode atlas (zoom + drag select). */
const HERO_HEIGHT_PX = 140;

export type StudioImageModeProps = ImageModeProps & {
  accentHue: string;
};

/** Studio Look image fill: hero crop viewport + library grid (replace via library / replace only). */
export function StudioImageMode({
  file,
  preview,
  assetId: assetIdProp,
  uvRect,
  onFileChange,
  disabled = false,
  accentHue,
}: StudioImageModeProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState("");
  const [textures, setTextures] = useState<TextureAsset[]>([]);
  const [loadingTextures, setLoadingTextures] = useState(true);

  const resolvedAssetId =
    assetIdProp ??
    textures.find((texture) => preview && texture.url === preview)?.id ??
    "";

  const selectedTexture = textures.find(
    (t) => t.id === resolvedAssetId || (preview && t.url === preview),
  );
  const displayName =
    selectedTexture?.display_name ?? file?.name ?? (preview ? "Custom image" : "No image");
  const hasSelection = Boolean(preview);

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

  const applyFile = (selectedFile: File) => {
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

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.currentTarget.files?.[0];
    e.currentTarget.value = "";
    if (selectedFile) applyFile(selectedFile);
  };

  const handleSelectTexture = (texture: TextureAsset) => {
    setError("");
    onFileChange(null, texture.url, texture.id, null);
  };

  const isSelected = (texture: TextureAsset) =>
    resolvedAssetId === texture.id || preview === texture.url;

  const openFilePicker = () => {
    if (!disabled) fileInputRef.current?.click();
  };

  return (
    <div style={studioFillContentStyle} data-testid="studio-image-mode">
      {hasSelection ? (
        <div
          data-testid="studio-image-preview"
          style={{
            width: "100%",
            borderRadius: 7,
            overflow: "hidden",
            border: `2px solid ${accentHue}`,
            background: "#0a0a10",
          }}
        >
          <AtlasOverlay
            variant="hero"
            heroHeight={HERO_HEIGHT_PX}
            previewUrl={preview!}
            uvRect={uvRect}
            disabled={disabled}
            onUvRectChange={(r) => onFileChange(null, preview, resolvedAssetId, r)}
          />
        </div>
      ) : (
        <button
          type="button"
          disabled={disabled}
          data-testid="studio-image-upload-empty"
          title="Upload or pick a texture from the library"
          onClick={openFilePicker}
          style={{
            height: HERO_HEIGHT_PX,
            width: "100%",
            borderRadius: 7,
            padding: 0,
            background: "#16161d",
            border: "1px dashed rgba(255,255,255,0.18)",
            boxShadow: "inset 0 0 0 1px rgba(255,255,255,0.04)",
            cursor: disabled ? "not-allowed" : "pointer",
            color: "#8a8a96",
            fontSize: 28,
          }}
        >
          ＋
        </button>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span
            style={{
              fontSize: 11,
              fontFamily: "var(--font-mono, monospace)",
              color: STUDIO_INK_PRIMARY,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
              flex: 1,
              minWidth: 0,
            }}
          >
            {displayName}
          </span>
          {hasSelection ? (
            <button
              type="button"
              disabled={disabled}
              style={studioChipButtonStyle}
              onClick={openFilePicker}
            >
              replace
            </button>
          ) : null}
        </div>
        {hasSelection && uvRect ? (
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              alignItems: "flex-start",
              gap: 6,
              width: "100%",
            }}
            data-testid="studio-image-uv-preview"
          >
            <span
              style={{
                flex: "1 1 120px",
                minWidth: 0,
                fontSize: 10,
                fontFamily: "var(--font-mono, monospace)",
                color: "#7a7a86",
                whiteSpace: "normal",
                overflowWrap: "anywhere",
                wordBreak: "break-all",
                lineHeight: 1.4,
              }}
            >
              {stringifyImageUvRect(uvRect)}
            </span>
            <button
              type="button"
              disabled={disabled}
              style={{ ...studioChipButtonStyle, flexShrink: 0 }}
              onClick={() => onFileChange(null, preview, resolvedAssetId, null)}
            >
              full image
            </button>
          </div>
        ) : null}
        <input
          ref={fileInputRef}
          type="file"
          accept={ALLOWED_TYPES.join(",")}
          disabled={disabled}
          aria-label="Upload texture image"
          style={{ display: "none" }}
          onChange={handleFileSelect}
        />
      </div>

      {!loadingTextures && textures.length > 0 ? (
        <div>
          <div style={{ ...studioLabelCaps, letterSpacing: 0.6, marginBottom: 5 }}>Library</div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, 1fr)",
              gap: 5,
            }}
          >
            {textures.map((texture) => {
              const selected = isSelected(texture);
              if (selected) {
                return (
                  <div
                    key={texture.id}
                    data-testid={`studio-texture-${texture.id}`}
                    aria-label={`${texture.display_name} (shown above)`}
                    style={{
                      height: 44,
                      borderRadius: 6,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 9,
                      fontWeight: 700,
                      letterSpacing: 0.4,
                      textTransform: "uppercase",
                      color: accentHue,
                      background: "rgba(255,255,255,0.03)",
                      border: `2px solid ${accentHue}`,
                    }}
                  >
                    Active
                  </div>
                );
              }
              return (
                <button
                  key={texture.id}
                  type="button"
                  title={texture.display_name}
                  disabled={disabled}
                  data-testid={`studio-texture-${texture.id}`}
                  onClick={() => handleSelectTexture(texture)}
                  style={{
                    height: 44,
                    borderRadius: 6,
                    padding: 0,
                    overflow: "hidden",
                    border: "1px solid rgba(255,255,255,0.08)",
                    cursor: disabled ? "not-allowed" : "pointer",
                  }}
                >
                  <img
                    src={texture.url}
                    alt=""
                    aria-hidden
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
            <button
              type="button"
              title="Upload image"
              disabled={disabled}
              data-testid="studio-texture-upload"
              onClick={openFilePicker}
              style={{
                height: 44,
                borderRadius: 6,
                padding: 0,
                background: "transparent",
                border: "1px dashed rgba(255,255,255,0.18)",
                color: "#8a8a96",
                fontSize: 18,
                cursor: disabled ? "not-allowed" : "pointer",
              }}
            >
              ＋
            </button>
          </div>
        </div>
      ) : null}

      {error ? (
        <div style={{ fontSize: 10, color: "#f48771", fontFamily: "var(--font-mono, monospace)" }}>
          {error}
        </div>
      ) : null}
    </div>
  );
}
