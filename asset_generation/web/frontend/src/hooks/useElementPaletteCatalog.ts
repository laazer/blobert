import { useCallback, useState } from "react";
import type { ElementId, ElementPalette } from "../utils/elementColorPalettes";
import {
  clearElementPaletteOverride,
  hasElementPaletteOverride,
  resolveElementPalette,
  setElementMaterialOverride,
} from "../utils/elementPaletteOverrides";

/** Reactive catalog of element default palettes (built-in + local overrides). */
export function useElementPaletteCatalog() {
  const [revision, setRevision] = useState(0);

  const bump = useCallback(() => setRevision((r) => r + 1), []);

  const getPalette = useCallback(
    (elementId: ElementId): ElementPalette => {
      void revision;
      return resolveElementPalette(elementId);
    },
    [revision],
  );

  const isOverridden = useCallback(
    (elementId: ElementId): boolean => {
      void revision;
      return hasElementPaletteOverride(elementId);
    },
    [revision],
  );

  const saveMaterialDefaults = useCallback(
    (
      elementId: ElementId,
      draftValues: Readonly<Record<string, unknown>>,
      knownDefKeys: ReadonlySet<string>,
    ) => {
      setElementMaterialOverride(elementId, draftValues, knownDefKeys);
      bump();
    },
    [bump],
  );

  const resetPalette = useCallback(
    (elementId: ElementId) => {
      clearElementPaletteOverride(elementId);
      bump();
    },
    [bump],
  );

  return { getPalette, isOverridden, saveMaterialDefaults, resetPalette };
}
