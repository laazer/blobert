import { useMemo, useState, type KeyboardEvent } from "react";
import { ELEMENTS, type ElementId } from "../../constants/elements";
import type { RegistryEnemyVersion } from "../../types";
import { displayVersionTags, normalizeTagInput } from "../../utils/registryTags";
import { elementTagChipStyle } from "../../utils/studioVersionUi";
import { studioAddTagButtonStyle } from "./studioVersionStyles";

type Props = {
  family: string;
  version: RegistryEnemyVersion;
  knownTags: readonly string[];
  hideDisplayTags: ReadonlySet<string>;
  disabled?: boolean;
  tagIndentPx?: number;
  /** Inline row (preview meta bar); default stacked under version row. */
  layout?: "stacked" | "inline";
  onCommit: (tags: string[]) => void | Promise<void>;
};

function isElementTag(tag: string): tag is ElementId {
  return tag in ELEMENTS;
}

export function StudioVersionTags({
  family,
  version,
  knownTags,
  hideDisplayTags,
  disabled,
  tagIndentPx = 0,
  layout = "stacked",
  onCommit,
}: Props) {
  const [adderOpen, setAdderOpen] = useState(false);
  const [draft, setDraft] = useState("");

  const allTags = useMemo(() => {
    const raw = version.tags && version.tags.length > 0 ? version.tags : [family];
    return raw;
  }, [version.tags, family]);

  const visible = displayVersionTags(version, family, hideDisplayTags);

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
    if (!tok || tok === family || allTags.includes(tok)) {
      setDraft("");
      setAdderOpen(false);
      return;
    }
    commitTags([...allTags, tok]);
    setDraft("");
    setAdderOpen(false);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addDraft();
    }
    if (e.key === "Escape") {
      setAdderOpen(false);
      setDraft("");
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: 4,
        alignItems: "center",
        ...(layout === "stacked" ? { marginTop: 6, marginLeft: tagIndentPx } : { flex: "1 1 auto", minWidth: 0 }),
      }}
      data-testid={`studio-version-tags-${version.id}`}
    >
      {visible.map((tag) => {
        const isFamily = tag === family;
        const elStyle = isElementTag(tag) ? elementTagChipStyle(tag) : null;
        return (
          <span
            key={tag}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
              padding: "1px 7px",
              borderRadius: 4,
              fontSize: 10,
              fontWeight: 600,
              maxWidth: "100%",
              ...(elStyle ?? {
                background: "rgba(255,255,255,0.04)",
                color: "#bababf",
                border: "1px solid rgba(255,255,255,0.08)",
              }),
            }}
          >
            {tag}
            {!isFamily && !disabled ? (
              <button
                type="button"
                aria-label={`Remove tag ${tag}`}
                style={{
                  border: "none",
                  background: "transparent",
                  color: "inherit",
                  cursor: "pointer",
                  padding: 0,
                  fontSize: 11,
                  lineHeight: 1,
                  opacity: 0.7,
                }}
                onClick={(ev) => {
                  ev.stopPropagation();
                  commitTags(allTags.filter((t) => t !== tag));
                }}
              >
                ×
              </button>
            ) : null}
          </span>
        );
      })}
      {!disabled ? (
        adderOpen ? (
          <input
            type="text"
            list={`studio-tag-suggestions-${family}-${version.id}`}
            autoFocus
            value={draft}
            placeholder="tag"
            aria-label={`Add tag for ${version.id}`}
            data-testid={`studio-version-tag-input-${version.id}`}
            style={{
              padding: "2px 6px",
              borderRadius: 4,
              border: "1px solid rgba(255,255,255,0.12)",
              background: "#121218",
              color: "#ededf0",
              fontSize: 10,
              width: 72,
            }}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={onKeyDown}
            onBlur={() => {
              if (draft.trim()) addDraft();
              else setAdderOpen(false);
            }}
          />
        ) : (
          <button
            type="button"
            style={studioAddTagButtonStyle}
            data-testid={`studio-version-tag-add-${version.id}`}
            onClick={(ev) => {
              ev.stopPropagation();
              setAdderOpen(true);
            }}
          >
            ＋ tag
          </button>
        )
      ) : null}
      <datalist id={`studio-tag-suggestions-${family}-${version.id}`}>
        {suggestions.map((t) => (
          <option key={t} value={t} />
        ))}
      </datalist>
    </div>
  );
}
