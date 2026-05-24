import {
  buildFeatUpdatesFromPalette,
  COARSE_ZONE_KEYS,
  DEFAULT_ELEMENT_PALETTES,
  extractZonePaletteFromValues,
  sanitizeFinish,
  sanitizeHex,
  type CoarseZoneKey,
  type ElementId,
  type ElementPalette,
  type ZoneMaterial,
} from "./elementColorPalettes";
import { pickElementMaterialOptions } from "./studioElementDefaultKeys";

export const ELEMENT_PALETTE_OVERRIDES_LS = "blobert.studio.elementPaletteOverrides";

type ElementDefaultsRecord = {
  palette?: ElementPalette;
  options?: Record<string, unknown>;
};

export type ElementPaletteOverrides = Partial<Record<ElementId, ElementDefaultsRecord>>;

function readRaw(): ElementPaletteOverrides {
  if (typeof localStorage === "undefined") return {};
  try {
    const raw = localStorage.getItem(ELEMENT_PALETTE_OVERRIDES_LS);
    if (!raw) return {};
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return {};
    return normalizeOverrides(parsed as Record<string, unknown>);
  } catch {
    return {};
  }
}

function normalizeZoneMaterial(value: unknown): ZoneMaterial | undefined {
  if (!value || typeof value !== "object") return undefined;
  const row = value as { finish?: unknown; hex?: unknown };
  const hex = typeof row.hex === "string" ? sanitizeHex(row.hex) : "";
  if (!hex) return undefined;
  const finish = typeof row.finish === "string" ? sanitizeFinish(row.finish) : "matte";
  return { finish, hex };
}

function normalizePaletteOnly(elementId: string, zones: Record<string, unknown>): ElementPalette {
  const palette: ElementPalette = {};
  for (const zone of COARSE_ZONE_KEYS) {
    const mat = normalizeZoneMaterial(zones[zone]);
    if (mat) palette[zone as CoarseZoneKey] = mat;
  }
  return palette;
}

function normalizeOverrides(raw: Record<string, unknown>): ElementPaletteOverrides {
  const out: ElementPaletteOverrides = {};
  for (const [elementId, entryRaw] of Object.entries(raw)) {
    if (!entryRaw || typeof entryRaw !== "object") continue;
    const entry = entryRaw as Record<string, unknown>;
    const isWrapped = "options" in entry || "palette" in entry;
    const paletteSource =
      isWrapped && entry.palette && typeof entry.palette === "object"
        ? (entry.palette as Record<string, unknown>)
        : isWrapped
          ? null
          : entry;
    const palette =
      paletteSource && Object.keys(paletteSource).length > 0
        ? normalizePaletteOnly(elementId, paletteSource)
        : undefined;
    const options =
      entry.options && typeof entry.options === "object"
        ? (entry.options as Record<string, unknown>)
        : undefined;

    if (options && Object.keys(options).length > 0) {
      out[elementId as ElementId] = { palette, options };
    } else if (palette && Object.keys(palette).length > 0) {
      out[elementId as ElementId] = { palette };
    }
  }
  return out;
}

export function loadElementPaletteOverrides(): ElementPaletteOverrides {
  return readRaw();
}

function loadRecord(elementId: ElementId): ElementDefaultsRecord | undefined {
  return readRaw()[elementId];
}

export function saveElementPaletteOverrides(overrides: ElementPaletteOverrides): void {
  if (typeof localStorage === "undefined") return;
  localStorage.setItem(ELEMENT_PALETTE_OVERRIDES_LS, JSON.stringify(overrides));
}

export function resolveElementPalette(elementId: ElementId): ElementPalette {
  const base = DEFAULT_ELEMENT_PALETTES[elementId];
  const record = loadRecord(elementId);
  if (record?.options && Object.keys(record.options).length > 0) {
    const fromOptions = extractZonePaletteFromValues(record.options);
    const merged: ElementPalette = {};
    for (const zone of COARSE_ZONE_KEYS) {
      merged[zone] = fromOptions[zone] ?? record.palette?.[zone] ?? base[zone];
    }
    return merged;
  }
  if (record?.palette) {
    const merged: ElementPalette = {};
    for (const zone of COARSE_ZONE_KEYS) {
      merged[zone] = record.palette[zone] ?? base[zone];
    }
    return merged;
  }
  return { ...base };
}

export function hasElementPaletteOverride(elementId: ElementId): boolean {
  const record = loadRecord(elementId);
  if (!record) return false;
  if (record.options && Object.keys(record.options).length > 0) return true;
  if (record.palette && Object.keys(record.palette).length > 0) return true;
  return false;
}

export function seedElementDefaultDraftValues(
  elementId: ElementId,
  knownDefKeys: ReadonlySet<string>,
): Record<string, unknown> {
  const record = loadRecord(elementId);
  const fromBuiltin = buildFeatUpdatesFromPalette(
    DEFAULT_ELEMENT_PALETTES[elementId],
    knownDefKeys,
    {},
  );
  if (record?.options && Object.keys(record.options).length > 0) {
    return { ...fromBuiltin, ...record.options };
  }
  if (record?.palette) {
    return {
      ...fromBuiltin,
      ...buildFeatUpdatesFromPalette(record.palette, knownDefKeys, {}),
    };
  }
  return fromBuiltin;
}

export function builtinElementDefaultOptions(
  elementId: ElementId,
  knownDefKeys: ReadonlySet<string>,
): Record<string, unknown> {
  return buildFeatUpdatesFromPalette(DEFAULT_ELEMENT_PALETTES[elementId], knownDefKeys, {});
}

function optionsEqual(
  a: Record<string, unknown>,
  b: Record<string, unknown>,
): boolean {
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  for (const key of keys) {
    if (a[key] !== b[key]) return false;
  }
  return true;
}

export function setElementMaterialOverride(
  elementId: ElementId,
  draftValues: Readonly<Record<string, unknown>>,
  knownDefKeys: ReadonlySet<string>,
): void {
  const all = readRaw();
  const options = pickElementMaterialOptions(draftValues, knownDefKeys);
  const builtin = builtinElementDefaultOptions(elementId, knownDefKeys);
  if (optionsEqual(options, builtin)) {
    delete all[elementId];
  } else {
    all[elementId] = { options };
  }
  saveElementPaletteOverrides(all);
}

/** @deprecated Use {@link setElementMaterialOverride}. */
export function setElementPaletteOverride(elementId: ElementId, palette: ElementPalette): void {
  const all = readRaw();
  const normalized = sanitizeElementPaletteDraft(palette);
  if (Object.keys(normalized).length === 0 || isPaletteSameAsBuiltin(elementId, normalized)) {
    delete all[elementId];
  } else {
    all[elementId] = { palette: normalized };
  }
  saveElementPaletteOverrides(all);
}

export function clearElementPaletteOverride(elementId: ElementId): void {
  const all = readRaw();
  delete all[elementId];
  saveElementPaletteOverrides(all);
}

export function buildElementApplyUpdates(
  elementId: ElementId,
  knownDefKeys: ReadonlySet<string>,
  currentValues: Readonly<Record<string, unknown>>,
): Record<string, unknown> {
  const palette = resolveElementPalette(elementId);
  const base = buildFeatUpdatesFromPalette(palette, knownDefKeys, currentValues);
  const record = loadRecord(elementId);
  if (!record?.options) return base;
  const merged = { ...base };
  for (const [key, value] of Object.entries(record.options)) {
    if (knownDefKeys.has(key)) merged[key] = value;
  }
  return merged;
}

export function sanitizeElementPaletteDraft(palette: ElementPalette): ElementPalette {
  const out: ElementPalette = {};
  for (const zone of COARSE_ZONE_KEYS) {
    const mat = palette[zone];
    if (!mat) continue;
    const hex = sanitizeHex(mat.hex);
    if (!hex) continue;
    out[zone] = { finish: sanitizeFinish(mat.finish), hex };
  }
  return out;
}

export function palettesEqual(a: ElementPalette, b: ElementPalette): boolean {
  for (const zone of COARSE_ZONE_KEYS) {
    const am = a[zone];
    const bm = b[zone];
    if (!am && !bm) continue;
    if (!am || !bm) return false;
    if (am.hex.toLowerCase() !== bm.hex.toLowerCase()) return false;
    if (am.finish !== bm.finish) return false;
  }
  return true;
}

export function isPaletteSameAsBuiltin(elementId: ElementId, palette: ElementPalette): boolean {
  return palettesEqual(palette, DEFAULT_ELEMENT_PALETTES[elementId]);
}
