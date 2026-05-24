import type { CSSProperties } from "react";

type Props = {
  label: string;
  controlKey: string;
  checked: boolean;
  accentHue: string;
  disabled?: boolean;
  onChange: (v: boolean) => void;
};

const trackBase: CSSProperties = {
  width: 36,
  height: 20,
  borderRadius: 10,
  border: "none",
  padding: 0,
  position: "relative",
  flexShrink: 0,
  cursor: "pointer",
};

export function StudioBuildToggle({ label, controlKey, checked, accentHue, disabled, onChange }: Props) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 10,
        opacity: disabled ? 0.42 : 1,
        pointerEvents: disabled ? "none" : undefined,
      }}
      data-testid={`studio-build-toggle-${controlKey}`}
    >
      <span style={{ fontSize: 12, fontWeight: 600, color: "#ededf0" }}>{label}</span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        disabled={disabled}
        style={{
          ...trackBase,
          background: checked ? accentHue : "#2a2a36",
          cursor: disabled ? "not-allowed" : "pointer",
        }}
        onClick={() => onChange(!checked)}
      >
        <span
          aria-hidden
          style={{
            position: "absolute",
            top: 2,
            left: checked ? 18 : 2,
            width: 16,
            height: 16,
            borderRadius: "50%",
            background: "#fff",
            boxShadow: "0 1px 2px rgba(0,0,0,0.35)",
            transition: "left 0.12s ease",
          }}
        />
      </button>
    </div>
  );
}
