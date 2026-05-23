import {
  COARSE_ZONE_KEYS,
  type CoarseZoneKey,
  type ElementPalette,
} from "./elementColorPalettes";

const HEX_RE = /^#[0-9a-fA-F]{6}$/;

export function readZoneHex(values: Readonly<Record<string, unknown>>, zone: string): string {
  const colorHex = values[`feat_${zone}_color_hex`];
  const canonical = values[`feat_${zone}_hex`];
  if (typeof colorHex === "string" && colorHex.trim() !== "") return colorHex.trim();
  if (typeof canonical === "string" && canonical.trim() !== "") return canonical.trim();
  return "";
}

export function readZoneFinish(values: Readonly<Record<string, unknown>>, zone: string): string {
  const raw = values[`feat_${zone}_finish`];
  return typeof raw === "string" && raw.trim() !== "" ? raw.trim() : "default";
}

export function paletteSwatchColors(palette: ElementPalette, max = 5): string[] {
  const out: string[] = [];
  for (const zone of COARSE_ZONE_KEYS) {
    const hex = palette[zone]?.hex;
    if (hex && HEX_RE.test(hex) && !out.includes(hex)) out.push(hex);
  }
  return out.slice(0, max);
}

export function buildZoneHexUpdates(
  zone: string,
  hex: string,
  knownDefKeys: ReadonlySet<string>,
): Record<string, unknown> {
  const updates: Record<string, unknown> = {};
  const canonical = `feat_${zone}_hex`;
  const picker = `feat_${zone}_color_hex`;
  const colorA = `feat_${zone}_color_a`;
  if (knownDefKeys.has(canonical)) updates[canonical] = hex;
  if (knownDefKeys.has(picker)) updates[picker] = hex;
  if (knownDefKeys.has(colorA)) updates[colorA] = hex;
  return updates;
}

export function coarseZonesWithMaterial(
  knownDefKeys: ReadonlySet<string>,
): CoarseZoneKey[] {
  return COARSE_ZONE_KEYS.filter(
    (z) => knownDefKeys.has(`feat_${z}_finish`) || knownDefKeys.has(`feat_${z}_hex`),
  );
}

export function partRowLabel(zone: CoarseZoneKey): string {
  return zone
    .split("_")
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");
}

/** Finish pills shown on the mockup body card (subset of pipeline finishes). */
export const STUDIO_BODY_FINISH_PILLS = ["matte", "glossy", "metallic"] as const;

export function finishPillSelected(stored: string, pill: string): boolean {
  if (stored === pill) return true;
  if (pill === "matte" && (stored === "default" || stored === "")) return true;
  return false;
}

/** Display label → coarse zone key (redesign_v2 PartPicker). */
export const STUDIO_PART_ZONE_BY_LABEL: Record<string, CoarseZoneKey> = {
  Body: "body",
  Head: "head",
  Limbs: "limbs",
  Joints: "joints",
  Extra: "extra",
};

export function zoneToPartLabel(zone: CoarseZoneKey): string {
  return partRowLabel(zone);
}

export function shadeHex(hex: string, amount: number): string {
  if (!/^#[0-9a-fA-F]{6}$/.test(hex)) return hex;
  const n = hex.slice(1);
  const clamp = (v: number) => Math.max(0, Math.min(255, Math.round(v)));
  const r = clamp(Number.parseInt(n.slice(0, 2), 16) * (1 - amount));
  const g = clamp(Number.parseInt(n.slice(2, 4), 16) * (1 - amount));
  const b = clamp(Number.parseInt(n.slice(4, 6), 16) * (1 - amount));
  const h = (v: number) => v.toString(16).padStart(2, "0");
  return `#${h(r)}${h(g)}${h(b)}`;
}

export function tintHex(hex: string, amount: number): string {
  if (!/^#[0-9a-fA-F]{6}$/.test(hex)) return hex;
  const n = hex.slice(1);
  const clamp = (v: number) => Math.max(0, Math.min(255, Math.round(v)));
  const r = clamp(Number.parseInt(n.slice(0, 2), 16) + 255 * amount);
  const g = clamp(Number.parseInt(n.slice(2, 4), 16) + 255 * amount);
  const b = clamp(Number.parseInt(n.slice(4, 6), 16) + 255 * amount);
  const h = (v: number) => v.toString(16).padStart(2, "0");
  return `#${h(r)}${h(g)}${h(b)}`;
}

export const STUDIO_PATTERN_COLOR_SWATCHES = [
  "#ffd23d",
  "#ededf0",
  "#0c0c10",
  "#ff6b3d",
  "#b87dff",
] as const;
