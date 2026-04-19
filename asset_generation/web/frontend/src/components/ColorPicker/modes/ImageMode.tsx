import { useState, useEffect } from "react";
import { colorPickerStyles } from "../colorPickerStyles";

export interface ImageModeProps {
  file: File | null;
  preview?: string;
  onFileChange: (file: File | null, preview?: string) => void;
  disabled?: boolean;
}

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB
const ALLOWED_TYPES = ["image/png", "image/jpeg", "image/jpg", "image/webp"];

/**
 * Image texture picker mode.
 * Provides file input for uploading custom image textures.
 * Generates preview URL and emits file + preview on selection.
 */
export function ImageMode({
  file,
  preview,
  onFileChange,
  disabled = false,
}: ImageModeProps) {
  const [error, setError] = useState<string>("");

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

  const fileName = file?.name || "No file selected";

  return (
    <div style={colorPickerStyles.modeContent}>
      <div style={colorPickerStyles.fileInputLabel}>Texture Image</div>

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
  );
}
