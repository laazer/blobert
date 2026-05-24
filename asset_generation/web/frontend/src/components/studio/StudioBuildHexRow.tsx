import { useState } from "react";
import { readHexFromClipboard } from "../../utils/clipboardHex";
import { studioBuildRowLabel, studioBuildSegmentTrack } from "./studioBuildStyles";

type Props = {
  label: string;
  controlKey: string;
  value: string;
  disabled?: boolean;
  onChange: (v: string) => void;
};

function normalizeHex(raw: string): string {
  const t = raw.trim();
  if (!t) return "";
  return t.startsWith("#") ? t : `#${t}`;
}

export function StudioBuildHexRow({ label, controlKey, value, disabled, onChange }: Props) {
  const strVal = typeof value === "string" ? value : "";
  const [pasteHint, setPasteHint] = useState<string | null>(null);

  async function pasteColor() {
    const parsed = await readHexFromClipboard();
    if (parsed) {
      onChange(parsed);
      setPasteHint(null);
    } else {
      setPasteHint("No #RRGGBB in clipboard");
      window.setTimeout(() => setPasteHint(null), 2000);
    }
  }

  const swatch = normalizeHex(strVal) || "#444";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 4,
        opacity: disabled ? 0.42 : 1,
        pointerEvents: disabled ? "none" : undefined,
      }}
      data-testid={`studio-build-hex-${controlKey}`}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={studioBuildRowLabel}>{label}</div>
        <div style={{ ...studioBuildSegmentTrack, flexShrink: 0 }}>
          <span
            aria-hidden
            style={{
              width: 22,
              height: 22,
              borderRadius: 5,
              background: swatch,
              border: "1px solid rgba(255,255,255,0.12)",
              flexShrink: 0,
            }}
          />
          <input
            type="text"
            aria-label={label}
            value={strVal}
            spellCheck={false}
            placeholder="#RRGGBB"
            style={{
              width: 72,
              border: 0,
              background: "transparent",
              color: "#ededf0",
              fontSize: 11,
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
              fontWeight: 600,
              padding: "2px 4px",
            }}
            onChange={(e) => onChange(e.target.value)}
          />
          <button
            type="button"
            title="Paste #RRGGBB from clipboard"
            style={{
              padding: "4px 8px",
              border: 0,
              borderRadius: 4,
              background: "transparent",
              color: "#8a8a96",
              fontSize: 10,
              fontWeight: 600,
              cursor: "pointer",
            }}
            onClick={() => void pasteColor()}
          >
            Paste
          </button>
        </div>
      </div>
      {pasteHint ? <span style={{ fontSize: 10, color: "#f48771", marginLeft: 4 }}>{pasteHint}</span> : null}
    </div>
  );
}
