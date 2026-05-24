import { useEffect, useState, type KeyboardEvent } from "react";
import { useStudioPreviewVersion } from "../../hooks/useStudioPreviewVersion";
import { studioPreviewMetaFileChip, studioPreviewMetaNameChip } from "../../styles/studioPreviewStyles";
import { StudioVersionTags } from "./StudioVersionTags";

type Props = {
  /** When false, only the inner chips/tags render (parent supplies the bar shell). */
  embedded?: boolean;
};

export function StudioPreviewMetaBar({ embedded = false }: Props) {
  const {
    previewContext,
    glbLabel,
    tagCatalog,
    hideDisplayTags,
    patchName,
    patchTags,
    saving,
  } = useStudioPreviewVersion();

  const version = previewContext?.version;
  const family = previewContext?.family;
  const versionId = previewContext?.versionId;

  const savedName = version?.name?.trim() ?? "";
  const [draftName, setDraftName] = useState(savedName);

  useEffect(() => {
    setDraftName(savedName);
  }, [savedName, versionId]);

  if (!version || !family || !versionId || !glbLabel) {
    return embedded ? null : <div data-testid="studio-preview-meta-bar" />;
  }

  const commitName = () => {
    void patchName(draftName.trim());
  };

  const onNameKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.currentTarget.blur();
    }
    if (e.key === "Escape") {
      setDraftName(savedName);
      e.currentTarget.blur();
    }
  };

  const inner = (
    <>
      <span
        style={studioPreviewMetaFileChip}
        title="Registry version file"
        data-testid="studio-preview-meta-filename"
      >
        {glbLabel}
      </span>
      <input
        type="text"
        style={studioPreviewMetaNameChip}
        value={draftName}
        placeholder="Untitled"
        disabled={saving}
        aria-label="Model display name"
        data-testid="studio-preview-meta-name"
        onChange={(e) => setDraftName(e.target.value)}
        onBlur={commitName}
        onKeyDown={onNameKeyDown}
      />
      <StudioVersionTags
        family={family}
        version={version}
        knownTags={tagCatalog}
        hideDisplayTags={hideDisplayTags}
        disabled={saving}
        layout="inline"
        onCommit={patchTags}
      />
    </>
  );

  if (embedded) {
    return inner;
  }

  return <div data-testid="studio-preview-meta-bar">{inner}</div>;
}
