import { useCallback } from "react";
import { copyHexToClipboard, hexForColorInput, sanitizeHex } from "../../utils/clipboardHex";
import { STUDIO_INK_MUTED, STUDIO_INK_PRIMARY } from "../../styles/studioTokens";

type Props = {
  color: string;
  onChange: (hexWithoutHash: string) => void;
  disabled?: boolean;
};

export function StudioHexRow({ color, onChange, disabled = false }: Props) {
  const display = color.trim() ? `#${color.replace(/^#/, "")}` : "#000000";

  const onCopy = useCallback(async () => {
    await copyHexToClipboard(display);
  }, [display]);

  const onPaste = useCallback(async () => {
    try {
      const text = await navigator.clipboard.readText();
      onChange(sanitizeHex(text));
    } catch {
      // clipboard unavailable in test / permission denied
    }
  }, [onChange]);

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <label
        style={{
          width: 18,
          height: 18,
          borderRadius: 4,
          background: display,
          boxShadow: "0 0 0 1px rgba(255,255,255,0.1)",
          overflow: "hidden",
          cursor: disabled ? "default" : "pointer",
          flexShrink: 0,
        }}
      >
        <input
          type="color"
          value={hexForColorInput(color)}
          disabled={disabled}
          aria-label="Pick color"
          style={{ opacity: 0, width: "100%", height: "100%", border: 0, cursor: "pointer" }}
          onChange={(e) => onChange(e.target.value.replace(/^#/, "").toLowerCase())}
        />
      </label>
      <span style={{ fontFamily: "var(--font-mono, monospace)", fontSize: 11, color: STUDIO_INK_PRIMARY }}>
        {display}
      </span>
      <div style={{ flex: 1 }} />
      <button
        type="button"
        disabled={disabled}
        onClick={() => void onCopy()}
        style={studioChipButtonStyle}
      >
        copy
      </button>
      <button type="button" disabled={disabled} onClick={() => void onPaste()} style={studioChipButtonStyle}>
        paste
      </button>
    </div>
  );
}

const studioChipButtonStyle = {
  fontSize: 10,
  color: STUDIO_INK_MUTED,
  background: "transparent",
  border: "1px solid rgba(255,255,255,0.06)",
  borderRadius: 4,
  padding: "2px 7px",
  cursor: "pointer",
  fontFamily: "var(--font-mono, monospace)",
  fontWeight: 600,
} as const;
