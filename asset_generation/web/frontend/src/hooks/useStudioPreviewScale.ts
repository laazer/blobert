import { useCallback, useEffect, useState } from "react";
import {
  STUDIO_PREVIEW_SCALE_DEFAULT_INDEX,
  STUDIO_PREVIEW_SCALE_LEVELS,
  clampPreviewScaleIndex,
  readStoredPreviewScaleIndex,
  writeStoredPreviewScaleIndex,
} from "../utils/studioPreviewScale";

export function useStudioPreviewScale() {
  const [scaleIndex, setScaleIndex] = useState(() => readStoredPreviewScaleIndex());

  const scale = STUDIO_PREVIEW_SCALE_LEVELS[scaleIndex];

  useEffect(() => {
    writeStoredPreviewScaleIndex(scaleIndex);
  }, [scaleIndex]);

  useEffect(() => {
    requestAnimationFrame(() => window.dispatchEvent(new Event("resize")));
  }, [scaleIndex]);

  const canShrink = scaleIndex > 0;
  const canEnlarge = scaleIndex < STUDIO_PREVIEW_SCALE_LEVELS.length - 1;

  const shrink = useCallback(() => {
    setScaleIndex((i) => clampPreviewScaleIndex(i - 1));
  }, []);

  const enlarge = useCallback(() => {
    setScaleIndex((i) => clampPreviewScaleIndex(i + 1));
  }, []);

  const reset = useCallback(() => {
    setScaleIndex(STUDIO_PREVIEW_SCALE_DEFAULT_INDEX);
  }, []);

  return { scale, scaleIndex, canShrink, canEnlarge, shrink, enlarge, reset };
}
