import { FINISH_OPTIONS_ORDER } from "./animatedZoneControlsMerge";

/**
 * Built-in visual sets: combat-aligned (physical, fire, ice, acid, poison) plus
 * environment themes (earth, forest, water, lightning). Not user-overridable.
 */
export const ELEMENT_IDS = [
  "physical",
  "fire",
  "ice",
  "acid",
  "poison",
  "earth",
  "forest",
  "water",
  "lightning",
] as const;
export type ElementId = (typeof ELEMENT_IDS)[number];

export const ELEMENT_LABELS: Record<ElementId, string> = {
  physical: "Physical",
  fire: "Fire",
  ice: "Ice",
  acid: "Acid",
  poison: "Poison",
  earth: "Earth",
  forest: "Forest",
  water: "Water",
  lightning: "Lightning",
};

/** Coarse material zones (``feat_{zone}_*``); limb/joint overrides stay per-enemy. */
export const COARSE_ZONE_KEYS = ["body", "head", "limbs", "joints", "extra"] as const;
export type CoarseZoneKey = (typeof COARSE_ZONE_KEYS)[number];

export type ZoneMaterial = { finish: string; hex: string };

/** Finish + hex per zone; missing zones are skipped on apply. */
export type ElementPalette = Partial<Record<CoarseZoneKey, ZoneMaterial>>;

/** Editor hint: suggested palette row for an animated slug (not runtime combat). */
export const ANIMATED_SLUG_DEFAULT_ELEMENT: Readonly<Record<string, ElementId>> = {
  spider: "poison",
  slug: "water",
  imp: "fire",
  spitter: "acid",
  claw_crawler: "forest",
  carapace_husk: "earth",
};

export const DEFAULT_ELEMENT_PALETTES: Record<ElementId, ElementPalette> = {
  physical: {
    body: { finish: "matte", hex: "#6b6e72" },
    head: { finish: "matte", hex: "#5c5f63" },
    limbs: { finish: "matte", hex: "#7a7d82" },
    joints: { finish: "matte", hex: "#4a4d51" },
    extra: { finish: "matte", hex: "#8f9196" },
  },
  fire: {
    body: { finish: "glossy", hex: "#b83228" },
    head: { finish: "glossy", hex: "#e85d2a" },
    limbs: { finish: "matte", hex: "#7a1e0f" },
    joints: { finish: "metallic", hex: "#f0a030" },
    extra: { finish: "glossy", hex: "#ff5a1f" },
  },
  ice: {
    body: { finish: "glossy", hex: "#7eb8d6" },
    head: { finish: "glossy", hex: "#a8d8f0" },
    limbs: { finish: "matte", hex: "#4a7a9a" },
    joints: { finish: "matte", hex: "#c5e8ff" },
    extra: { finish: "gel", hex: "#b0e0ff" },
  },
  acid: {
    body: { finish: "gel", hex: "#6bc94a" },
    head: { finish: "glossy", hex: "#9fe04a" },
    limbs: { finish: "matte", hex: "#3d7a2a" },
    joints: { finish: "glossy", hex: "#d4ff6a" },
    extra: { finish: "glossy", hex: "#bfff00" },
  },
  poison: {
    body: { finish: "matte", hex: "#6b3d8f" },
    head: { finish: "glossy", hex: "#8b4cb8" },
    limbs: { finish: "matte", hex: "#4a2560" },
    joints: { finish: "metallic", hex: "#c080d0" },
    extra: { finish: "gel", hex: "#50c878" },
  },
  earth: {
    body: { finish: "matte", hex: "#6b5a4a" },
    head: { finish: "matte", hex: "#8b7355" },
    limbs: { finish: "matte", hex: "#4a3d32" },
    joints: { finish: "matte", hex: "#a89880" },
    extra: { finish: "matte", hex: "#5c4d3d" },
  },
  forest: {
    body: { finish: "matte", hex: "#2d4a2d" },
    head: { finish: "glossy", hex: "#3d6b3d" },
    limbs: { finish: "matte", hex: "#1e331e" },
    joints: { finish: "matte", hex: "#5a8f4a" },
    extra: { finish: "gel", hex: "#6b8c3a" },
  },
  water: {
    body: { finish: "glossy", hex: "#2a6b8f" },
    head: { finish: "glossy", hex: "#4a9ec8" },
    limbs: { finish: "matte", hex: "#1a4a66" },
    joints: { finish: "gel", hex: "#7ec8e8" },
    extra: { finish: "glossy", hex: "#3d8cb0" },
  },
  lightning: {
    body: { finish: "metallic", hex: "#e8e0a0" },
    head: { finish: "glossy", hex: "#fffacd" },
    limbs: { finish: "metallic", hex: "#b8a040" },
    joints: { finish: "glossy", hex: "#fff8dc" },
    extra: { finish: "metallic", hex: "#f4d03f" },
  },
};

function isValidFinish(f: string): boolean {
  return (FINISH_OPTIONS_ORDER as readonly string[]).includes(f);
}

export function sanitizeFinish(f: string): string {
  return isValidFinish(f) ? f : "matte";
}

const HEX_RE = /^#[0-9a-fA-F]{6}$/;

export function sanitizeHex(h: string): string {
  const t = h.trim();
  return HEX_RE.test(t) ? t : "";
}

/** Build store updates for coarse zone keys that exist on this enemy. */
export function buildFeatUpdatesFromPalette(
  palette: ElementPalette,
  existingDefKeys: ReadonlySet<string>,
): Record<string, unknown> {
  const updates: Record<string, unknown> = {};
  for (const zone of COARSE_ZONE_KEYS) {
    const mat = palette[zone];
    if (!mat) continue;
    const fk = `feat_${zone}_finish`;
    const hk = `feat_${zone}_hex`;
    if (existingDefKeys.has(fk)) updates[fk] = sanitizeFinish(mat.finish);
    if (existingDefKeys.has(hk)) updates[hk] = sanitizeHex(mat.hex);
  }
  return updates;
}

export function extractZonePaletteFromValues(values: Readonly<Record<string, unknown>>): ElementPalette {
  const out: ElementPalette = {};
  for (const zone of COARSE_ZONE_KEYS) {
    const ff = values[`feat_${zone}_finish`];
    const hx = values[`feat_${zone}_hex`];
    if (typeof ff === "string" && typeof hx === "string") {
      out[zone] = { finish: ff, hex: hx };
    }
  }
  return out;
}

export function defaultElementForSlug(slug: string): ElementId | null {
  const s = slug.trim().toLowerCase();
  return ANIMATED_SLUG_DEFAULT_ELEMENT[s] ?? null;
}
