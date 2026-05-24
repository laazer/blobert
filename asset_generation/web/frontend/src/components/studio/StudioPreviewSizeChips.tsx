import { studioPreviewSizeChipStyle } from "../../styles/studioPreviewStyles";
import { studioPreviewScaleLabel, type StudioPreviewScaleLevel } from "../../utils/studioPreviewScale";

type Props = {
  scale: StudioPreviewScaleLevel;
  canShrink: boolean;
  canEnlarge: boolean;
  onShrink: () => void;
  onEnlarge: () => void;
};

export function StudioPreviewSizeChips({ scale, canShrink, canEnlarge, onShrink, onEnlarge }: Props) {
  return (
    <div
      style={{ display: "inline-flex", alignItems: "center", gap: 4, flexShrink: 0 }}
      data-testid="studio-preview-size-chips"
      role="group"
      aria-label="Preview size"
    >
      <button
        type="button"
        style={studioPreviewSizeChipStyle(!canShrink)}
        disabled={!canShrink}
        aria-label="Shrink preview"
        data-testid="studio-preview-shrink"
        onClick={onShrink}
      >
        −
      </button>
      <span
        style={studioPreviewSizeChipStyle(true)}
        data-testid="studio-preview-scale-label"
        aria-live="polite"
      >
        {studioPreviewScaleLabel(scale)}
      </span>
      <button
        type="button"
        style={studioPreviewSizeChipStyle(!canEnlarge)}
        disabled={!canEnlarge}
        aria-label="Enlarge preview"
        data-testid="studio-preview-enlarge"
        onClick={onEnlarge}
      >
        +
      </button>
    </div>
  );
}
