import { useMemo, useState, type CSSProperties, type KeyboardEvent } from "react";
import { normalizeTagInput, versionTags } from "../../utils/registryTags";
import type { RegistryEnemyVersion } from "../../types";
import { RegistryTagChips } from "./RegistryTagChips";

const wrap: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 4,
  minWidth: 0,
  maxWidth: 220,
};
const inputRow: CSSProperties = {
  display: "flex",
  gap: 4,
  flexWrap: "wrap",
  alignItems: "center",
};
const inputStyle: CSSProperties = {
  flex: "1 1 72px",
  minWidth: 72,
  maxWidth: "100%",
  fontSize: 10,
  padding: "3px 6px",
  border: "1px solid #555",
  borderRadius: 3,
  background: "#252526",
  color: "#d4d4d4",
};
const addBtn: CSSProperties = {
  padding: "3px 8px",
  fontSize: 10,
  border: "1px solid #555",
  borderRadius: 3,
  cursor: "pointer",
  background: "#3c3c3c",
  color: "#d4d4d4",
  flexShrink: 0,
};

export type RegistryTagEditorProps = {
  family: string;
  version: RegistryEnemyVersion;
  knownTags: readonly string[];
  hideDisplayTags: ReadonlySet<string>;
  disabled?: boolean;
  onCommit: (nextTags: string[]) => void | Promise<void>;
};

export function RegistryTagEditor({
  family,
  version,
  knownTags,
  hideDisplayTags,
  disabled,
  onCommit,
}: RegistryTagEditorProps) {
  const [draft, setDraft] = useState("");
  const allTags = versionTags(version, family);
  const visible = allTags.filter((t) => !hideDisplayTags?.has(t));

  const suggestions = useMemo(() => {
    const have = new Set(allTags);
    return knownTags.filter((t) => !have.has(t) && t !== family);
  }, [allTags, knownTags, family]);

  const commitTags = (nextUserTags: string[]) => {
    const normalized = nextUserTags
      .map((t) => normalizeTagInput(t))
      .filter((t): t is string => t != null && t !== family);
    const merged = [family, ...normalized.filter((t, i, arr) => arr.indexOf(t) === i)];
    void onCommit(merged);
  };

  const addDraft = () => {
    const tok = normalizeTagInput(draft);
    if (!tok || tok === family) {
      setDraft("");
      return;
    }
    if (allTags.includes(tok)) {
      setDraft("");
      return;
    }
    commitTags([...allTags, tok]);
    setDraft("");
  };

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addDraft();
    }
  };

  return (
    <div style={wrap} data-testid={`registry-tag-editor-${family}-${version.id}`}>
      <RegistryTagChips
        tags={visible}
        family={family}
        disabled={disabled}
        onRemove={(tag) => commitTags(allTags.filter((t) => t !== tag))}
      />
      <div style={inputRow}>
        <input
          type="text"
          list={`registry-tag-suggestions-${family}-${version.id}`}
          style={inputStyle}
          disabled={disabled}
          placeholder="Add tag…"
          value={draft}
          aria-label={`Add tag for ${version.id}`}
          data-testid={`registry-tag-input-${family}-${version.id}`}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKeyDown}
          onBlur={() => {
            if (draft.trim()) addDraft();
          }}
        />
        <button
          type="button"
          style={addBtn}
          disabled={disabled || !normalizeTagInput(draft)}
          onClick={addDraft}
        >
          Add
        </button>
      </div>
      <datalist id={`registry-tag-suggestions-${family}-${version.id}`}>
        {suggestions.map((t) => (
          <option key={t} value={t} />
        ))}
      </datalist>
    </div>
  );
}
