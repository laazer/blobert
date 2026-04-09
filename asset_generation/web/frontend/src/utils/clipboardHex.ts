const SIX_HEX = /^[0-9a-fA-F]{6}$/;

/**
 * Parse clipboard / pasted text into 6 lowercase hex digits (no ``#``), matching
 * how the color picker path stores ``feat_*_hex`` values in the editor.
 */
export function normalizeHexForBuildOption(raw: string): string | null {
  const t = raw.trim();
  const body = t.startsWith("#") ? t.slice(1) : t;
  const digits = body.replace(/[^0-9a-fA-F]/g, "");
  if (digits.length !== 6 || !SIX_HEX.test(digits)) return null;
  return digits.toLowerCase();
}

/** Write ``#RRGGBB`` to the clipboard (common interchange format). */
export async function copyHexToClipboard(hexWithOrWithoutHash: string): Promise<boolean> {
  const t = hexWithOrWithoutHash.trim();
  const body = t.startsWith("#") ? t.slice(1) : t;
  if (!SIX_HEX.test(body)) return false;
  const canonical = `#${body.toLowerCase()}`;
  try {
    if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(canonical);
      return true;
    }
  } catch {
    return false;
  }
  return false;
}

/** Read clipboard text and return 6-char hex (no ``#``) or null. */
export async function readHexFromClipboard(): Promise<string | null> {
  try {
    if (typeof navigator === "undefined" || !navigator.clipboard?.readText) return null;
    const text = await navigator.clipboard.readText();
    return normalizeHexForBuildOption(text);
  } catch {
    return null;
  }
}
