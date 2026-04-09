/**
 * Split ``extra_zone_<zone>_*`` control defs from meta (aligned with Python ``_zone_extra_control_defs``).
 */

import { FEATURE_ZONES_BY_SLUG } from "../../utils/animatedZoneControlsMerge";
import { normalizeAnimatedSlug } from "../../utils/enemyDisplay";

const SUFFIX_ORDER = ["kind", "spike_shape", "spike_count", "bulb_count", "finish", "hex"] as const;

/** ``extra_zone_<zone>_<suffix>`` */
export const EXTRA_ZONE_PREFIX_RE = /^extra_zone_(body|head|limbs|joints|extra)_/;

export function extraZoneFromDefKey(key: string): string | null {
  const m = /^extra_zone_(body|head|limbs|joints|extra)_/.exec(key);
  return m ? m[1] : null;
}

function suffixRank(key: string): number {
  const m = /^extra_zone_\w+_(\w+)$/.exec(key);
  const s = m?.[1] ?? "";
  const i = SUFFIX_ORDER.indexOf(s as (typeof SUFFIX_ORDER)[number]);
  return i >= 0 ? i : 99;
}

export function partitionZoneExtraDefs<T extends { key: string }>(
  slug: string,
  allDefs: readonly T[],
): { zones: string[]; byZone: Record<string, T[]>; hasAny: boolean } {
  const slugKey = normalizeAnimatedSlug(slug);
  const zoneOrder = FEATURE_ZONES_BY_SLUG[slugKey] ?? [];
  const byZone: Record<string, T[]> = {};
  for (const z of zoneOrder) {
    byZone[z] = [];
  }
  for (const d of allDefs) {
    const z = extraZoneFromDefKey(d.key);
    if (!z || !byZone[z]) continue;
    byZone[z].push(d);
  }
  for (const z of zoneOrder) {
    byZone[z].sort((a, b) => suffixRank(a.key) - suffixRank(b.key));
  }
  const hasAny = zoneOrder.some((z) => byZone[z].length > 0);
  return { zones: [...zoneOrder], byZone, hasAny };
}

export const EXTRA_KINDS_ALL = ["none", "shell", "spikes", "horns", "bulbs"] as const;

export function kindOptionsForZone(zone: string): readonly string[] {
  if (zone === "head") return EXTRA_KINDS_ALL;
  return EXTRA_KINDS_ALL.filter((k) => k !== "horns");
}
