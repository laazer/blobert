import type { Dispatch, SetStateAction } from "react";
import type { StudioZoneFillBindings } from "../components/studio/StudioZoneFill";

export function createDraftZoneFillBindings(
  values: Readonly<Record<string, unknown>>,
  setValues: Dispatch<SetStateAction<Record<string, unknown>>>,
): StudioZoneFillBindings {
  return {
    values,
    applyUpdates: (updates) => {
      setValues((prev) => ({ ...prev, ...updates }));
    },
    setOption: (key, value) => {
      setValues((prev) => ({ ...prev, [key]: value }));
    },
  };
}
