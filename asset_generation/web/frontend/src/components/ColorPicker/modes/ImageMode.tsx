import { useState, useEffect } from "react";
import { colorPickerStyles } from "../colorPickerStyles";
import { fetchTextureAssets, type TextureAsset } from "../../../api/client";

export interface ImageModeProps {
  file: File | null;
  preview?: string;
  assetId?: string;
  onFileChange: (file: File | null, preview?: string, assetId?: string) => void;
  disabled?: boolean;
}

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB
const ALLOWED_TYPES = ["image/png", "image/jpeg", "image/jpg", "image/webp"];

/**
 * Image texture picker mode.
 * Provides both preloaded texture selection and custom file upload.
 * Users can select from available textures or upload custom image textures.
 */
export function ImageMode({
  file,
  preview,
  onFileChange,
  disabled = false,
}: ImageModeProps) {
  const [error, setError] = useState<string>("");
  const [textures, setTextures] = useState<TextureAsset[]>([]);
  const [loadingTextures, setLoadingTextures] = useState(true);

  // Fetch available textures on mount
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

  // Clean up preview URL on unmount
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

    // Validate file type
    if (!ALLOWED_TYPES.includes(selectedFile.type)) {
      setError("Only PNG, JPEG, and WebP images are supported");
      onFileChange(null);
      return;
    }

    // Validate file size
    if (selectedFile.size > MAX_FILE_SIZE) {
      setError("File size must be less than 5 MB");
      onFileChange(null);
      return;
    }

    // Generate preview URL
    const previewUrl = URL.createObjectURL(selectedFile);
    setError("");
    onFileChange(selectedFile, previewUrl);
  };

  const handleClear = () => {
    setError("");
    onFileChange(null);
  };

  const handleSelectTexture = (texture: TextureAsset & { url?: string }) => {
    setError("");
    if (texture.url) {
      // Use the URL from the API response and pass the asset ID
      onFileChange(null, texture.url, texture.id);
    }
  };

  const fileName = file?.name || "No file selected";

  return (
    <div style={colorPickerStyles.modeContent}>
      {/* Preloaded Textures Section */}
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

      {/* Custom Upload Section */}
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

      {/* File name and info */}
      <div style={colorPickerStyles.previewText}>{fileName}</div>

      {/* Error message */}
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

      {/* Image preview */}
      {preview && (
        <div style={colorPickerStyles.previewContainer}>
          <img src={preview} alt="Preview" style={colorPickerStyles.previewImage} />
          <div style={colorPickerStyles.previewText}>
            {file?.size && file.size > 0
              ? `${(file.size / 1024).toFixed(1)} KB`
              : ""}
          </div>
          <button
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

      {/* Info text */}
      <div style={colorPickerStyles.previewText}>
        Supported: PNG, JPEG, WebP (max 5 MB)
      </div>
      </div>
    </div>
  );
}
