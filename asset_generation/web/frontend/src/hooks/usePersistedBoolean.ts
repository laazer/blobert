import { useEffect, useState } from "react";

function readStoredBoolean(key: string, defaultValue: boolean): boolean {
  try {
    const raw = localStorage.getItem(key);
    if (raw === null) {
      return defaultValue;
    }
    return raw === "1" || raw === "true";
  } catch {
    return defaultValue;
  }
}

function writeStoredBoolean(key: string, value: boolean): void {
  try {
    localStorage.setItem(key, value ? "1" : "0");
  } catch {
    /* quota / private mode */
  }
}

/**
 * Boolean state mirrored to localStorage (values "1" / "0") for editor UI prefs.
 */
export function usePersistedBoolean(storageKey: string, defaultValue: boolean): [boolean, (next: boolean) => void] {
  const [value, setValue] = useState(() => readStoredBoolean(storageKey, defaultValue));

  useEffect(() => {
    writeStoredBoolean(storageKey, value);
  }, [storageKey, value]);

  return [value, setValue];
}
