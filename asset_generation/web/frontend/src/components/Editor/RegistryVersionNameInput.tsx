import type { CSSProperties } from "react";

/** Matches ``_MAX_VERSION_NAME_LEN`` in ``model_registry/schema.py``. */
export const REGISTRY_VERSION_NAME_MAX = 128;

const inputStyle: CSSProperties = {
  width: "100%",
  maxWidth: 200,
  boxSizing: "border-box",
  fontSize: 11,
  color: "#d4d4d4",
  background: "#252526",
  border: "1px solid #555",
  borderRadius: 3,
  padding: "3px 6px",
};

export type RegistryVersionNameInputProps = {
  versionId: string;
  /** Stored manifest name (may be undefined). */
  storedName: string | undefined;
  disabled: boolean;
  onCommit: (trimmed: string) => void | Promise<void>;
};

/**
 * Blur or Enter commits when the trimmed value differs from the stored name.
 * Empty string clears the display name (``name: null`` on the API).
 */
export function RegistryVersionNameInput({ versionId, storedName, disabled, onCommit }: RegistryVersionNameInputProps) {
  const stored = (storedName ?? "").trim();
  return (
    <input
      type="text"
      aria-label={`Display name for ${versionId}`}
      defaultValue={stored}
      key={`${versionId}:${stored}`}
      disabled={disabled}
      maxLength={REGISTRY_VERSION_NAME_MAX}
      placeholder="Display name"
      style={inputStyle}
      autoComplete="off"
      onKeyDown={(e) => {
        if (e.key === "Enter") (e.target as HTMLInputElement).blur();
      }}
      onBlur={(e) => {
        const t = e.target.value.trim();
        if (t === stored) return;
        void onCommit(t);
      }}
    />
  );
}
