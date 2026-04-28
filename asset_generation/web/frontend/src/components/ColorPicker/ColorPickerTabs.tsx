// Three-tab color picker: Color, Gradient, Image
import { useState } from "react";
import type { ColorPickerValue } from "./ColorPickerUniversal";
export type { ColorPickerValue };
import { SingleColorMode } from "./modes/SingleColorMode";
import { GradientMode } from "./modes/GradientMode";
import { ImageMode } from "./modes/ImageMode";

const tabStyles = {
  container: {
    display: "flex",
    flexDirection: "column" as const,
    gap: 12,
    padding: "8px 0",
  },
  tabBar: {
    display: "flex",
    gap: 2,
    borderBottom: "1px solid #3c3c3c",
  },
  tab: (active: boolean) => ({
    flex: "1 1 auto",
    padding: "8px 12px",
    fontSize: 11,
    fontWeight: 500 as const,
    textAlign: "center" as const,
    cursor: "pointer",
    background: active ? "#0e639c" : "transparent",
    color: active ? "#ffffff" : "#a8a8a8",
    border: "none",
    borderBottom: active ? "2px solid #0e639c" : "2px solid transparent",
    marginBottom: -1,
    transition: "all 0.15s ease-out",
  }),
  content: {
    display: "flex",
    flexDirection: "column" as const,
    gap: 8,
  },
} as const;

export interface ColorPickerTabsProps {
  mode: "single" | "gradient" | "image";
  onModeChange: (mode: "single" | "gradient" | "image") => void;
  value: ColorPickerValue;
  onChange: (value: ColorPickerValue) => void;
  disabled?: boolean;
  label?: string;
}

/**
 * Clean tab-based color picker with three modes:
 * - Color: Single hex color selection
 * - Gradient: Two colors with direction control
 * - Image: File upload for custom textures
 */
export function ColorPickerTabs({
  mode,
  onModeChange,
  value,
  onChange,
  disabled = false,
  label,
}: ColorPickerTabsProps) {
  return (
    <div style={tabStyles.container}>
      {label && (
        <div style={{ color: "#9d9d9d", fontSize: 11, fontWeight: 600 }}>
          {label}
        </div>
      )}

      {/* Tab bar */}
      <div style={tabStyles.tabBar}>
        {["single", "gradient", "image"].map((tab) => (
          <button
            key={tab}
            disabled={disabled}
            onClick={() => onModeChange(tab as "single" | "gradient" | "image")}
            style={tabStyles.tab(mode === tab)}
          >
            {tab === "single" ? "Color" : tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div style={tabStyles.content}>
        {mode === "single" && value.type === "single" && (
          <SingleColorMode
            color={value.color}
            onChange={(color) => onChange({ type: "single", color })}
            disabled={disabled}
          />
        )}

        {mode === "gradient" && value.type === "gradient" && (
          <GradientMode
            colorA={value.colorA}
            colorB={value.colorB}
            direction={value.direction}
            onChange={(colorA, colorB, direction) =>
              onChange({ type: "gradient", colorA, colorB, direction })
            }
            disabled={disabled}
          />
        )}

        {mode === "image" && value.type === "image" && (
          <ImageMode
            file={null}
            preview={value.preview}
            onFileChange={(file, preview, assetId) => onChange({ type: "image", file, preview, assetId })}
            disabled={disabled}
          />
        )}
      </div>
    </div>
  );
}
