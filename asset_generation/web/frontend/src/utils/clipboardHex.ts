const SIX_HEX = /^[0-9a-fA-F]{6}$/;

/**
 * Format stored 6-char hex (no ``#``) for ``<input type="color">``, which requires ``#RRGGBB``.
 * Falls back to a neutral gray when the value is incomplete or invalid.
 */
export function hexForColorInput(raw: string): string {
  if (typeof raw !== "string") {
    return "#6b6b6b";
  }
  const h = (raw || "").replace(/^#/, "").trim();
  if (SIX_HEX.test(h)) return `#${h.toLowerCase()}`;
  return "#6b6b6b";
}

/**
 * Strip ``#`` and non-hex characters; keep at most 6 hex digits, lowercase.
 * On blur, only a full 6-digit value is kept; partial or corrupted input clears
 * so the parent does not persist invalid hex.
 */
export function sanitizeHex(raw: string): string {
  const t = raw.replace(/^#/, "").replace(/[^0-9a-fA-F]/g, "").slice(0, 6).toLowerCase();
  if (t.length === 6) return t;
  return "";
}

/**
 * Parse clipboard / pasted text into 6 lowercase hex digits (no ``#``), matching
 * how the color picker path stores ``feat_*_hex`` values in the editor.
 * Rejects strings with malformed hex (non-hex characters interspersed, wrong prefixes, etc).
 */
export function normalizeHexForBuildOption(raw: string): string | null {
  if (typeof raw !== "string") return null;
  const t = raw.trim();

  // Try exact match first: #RRGGBB or RRGGBB
  if (t.startsWith("#")) {
    const body = t.slice(1);
    if (body.length === 6 && SIX_HEX.test(body)) {
      return body.toLowerCase();
    }
  } else if (t.length === 6 && SIX_HEX.test(t)) {
    return t.toLowerCase();
  }

  return null;
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
    
    // Try strict parsing first
    const result = normalizeHexForBuildOption(text);
    if (result !== null) return result;
    
    // If that fails, try to find a hex pattern in the clipboard content
    const hexMatch = text.match(/#([0-9a-fA-F]{6})/i);
    if (hexMatch && hexMatch[1]) {
      return hexMatch[1].toLowerCase();
    }
    
    // If still nothing, try extracting any 6 hex digits from the text
    const body = text.startsWith("#") ? text.slice(1) : text;
    const digits = body.replace(/[^0-9a-fA-F]/g, "");
    if (digits.length === 6 && SIX_HEX.test(digits)) {
      return digits.toLowerCase();
    }
    
    return null;
  } catch {
    return null;
  }
}
