import { defaultValuesForDefs } from "../api/client";
import type { AnimatedBuildControlDef } from "../types";
import { FEATURE_ZONES_BY_SLUG } from "./animatedZoneControlsMerge";
import { normalizeAnimatedSlug } from "./enemyDisplay";

function sanitizeHexForFeat(raw: string): string {
  return raw
    .replace(/^#/, "")
    .trim()
    .toLowerCase()
    .replace(/[^0-9a-f]/g, "")
    .slice(0, 6);
}

/**
 * Build `feat_{zone}_finish` / `feat_{zone}_hex` updates so the Colors tab matches the command bar
 * for zones that still equal merged defaults (first visit or fresh slug).
 */
export function buildZoneColorHydrationFromCommandBar(
  slug: string,
  defs: readonly AnimatedBuildControlDef[],
  current: Readonly<Record<string, unknown>>,
  commandFinish: string,
  commandHexWithHash: string,
): Record<string, unknown> {
  const defaults = defaultValuesForDefs(defs);
  const zones = FEATURE_ZONES_BY_SLUG[normalizeAnimatedSlug(slug)] ?? [];
  const updates: Record<string, unknown> = {};

  const hexStripped =
    commandHexWithHash.trim() !== "" && /^#[0-9a-fA-F]{6}$/.test(commandHexWithHash.trim())
      ? sanitizeHexForFeat(commandHexWithHash)
      : "";

  /** Aligned with Python ``_default_features_dict`` / zone finish defaults when meta is empty. */
  const fallbackFinish = "default";
  const fallbackHex = "";

  for (const z of zones) {
    const fk = `feat_${z}_finish`;
    const hk = `feat_${z}_hex`;
    const defF = defaults[fk] !== undefined ? defaults[fk] : fallbackFinish;
    const defH = defaults[hk] !== undefined ? defaults[hk] : fallbackHex;
    const rawCurF = current[fk];
    const rawCurH = current[hk];
    const curF = rawCurF === undefined || rawCurF === null ? defF : rawCurF;
    const curHNorm = rawCurH === undefined || rawCurH === null ? defH : rawCurH;
    const curHStr = typeof curHNorm === "string" ? curHNorm : "";
    const atHexDefault = curHStr === defH || curHStr === "";

    if (commandFinish.trim() !== "" && curF === defF && curF !== commandFinish) {
      updates[fk] = commandFinish;
    }
    if (atHexDefault && hexStripped && curHStr !== hexStripped) {
      updates[hk] = hexStripped;
    }
  }
  return updates;
}
