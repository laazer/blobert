import { parseAnimatedEnemyExportFilename, parseVariantFilename } from "./glbVariants";
import { FEATURE_ZONES_BY_SLUG } from "./animatedZoneControlsMerge";
import { normalizeAnimatedSlug, PLAYER_PROCEDURAL_BUILD_SLUG } from "./enemyDisplay";

type FeatureZoneSnapshot = {
  finish?: string;
  hex?: string;
  color_image?: {
    mode?: string;
    id?: string | null;
    preview?: string | null;
    uv_rect?: string | null;
  };
};

/**
 * Python export/registry snapshots store zone colors under ``features.{zone}``; the editor
 * uses flat ``feat_{zone}_*`` keys. Merge mesh floats to the top level before overlaying defaults.
 */
export function expandBuildOptionsSnapshotForEditor(
  slug: string,
  snapshot: Record<string, unknown>,
): Record<string, unknown> {
  const flat: Record<string, unknown> = { ...snapshot };

  const mesh = snapshot.mesh;
  if (mesh && typeof mesh === "object" && !Array.isArray(mesh)) {
    for (const [k, v] of Object.entries(mesh as Record<string, unknown>)) {
      flat[k] = v;
    }
  }
  const zones = FEATURE_ZONES_BY_SLUG[normalizeAnimatedSlug(slug)] ?? [];

  const zoneExtras = snapshot.zone_geometry_extras;
  if (zoneExtras && typeof zoneExtras === "object" && !Array.isArray(zoneExtras)) {
    const zgeMap = zoneExtras as Record<string, Record<string, unknown>>;
    for (const zone of zones) {
      const entry = zgeMap[zone];
      if (!entry || typeof entry !== "object" || Array.isArray(entry)) continue;
      for (const [field, val] of Object.entries(entry)) {
        flat[`extra_zone_${zone}_${field}`] = val;
      }
    }
  }

  delete flat.mesh;
  delete flat.features;
  delete flat.zone_geometry_extras;

  const features = snapshot.features;
  if (!features || typeof features !== "object" || Array.isArray(features)) {
    return flat;
  }
  const featMap = features as Record<string, FeatureZoneSnapshot>;

  for (const zone of zones) {
    const entry = featMap[zone];
    if (!entry || typeof entry !== "object") continue;

    if (typeof entry.finish === "string" && entry.finish.trim() !== "") {
      flat[`feat_${zone}_finish`] = entry.finish.trim();
    }
    if (typeof entry.hex === "string" && entry.hex.trim() !== "") {
      const h = entry.hex.trim().replace(/^#/, "");
      flat[`feat_${zone}_hex`] = h;
      flat[`feat_${zone}_color_hex`] = h;
    }

    const ci = entry.color_image;
    if (ci && typeof ci === "object") {
      const mode = typeof ci.mode === "string" ? ci.mode.trim().toLowerCase() : "";
      if (mode === "single" || mode === "gradient" || mode === "image") {
        flat[`feat_${zone}_color_mode`] = mode;
      }
      if (ci.id != null && String(ci.id).trim() !== "") {
        flat[`feat_${zone}_color_image_id`] = String(ci.id);
      }
      if (typeof ci.preview === "string" && ci.preview.trim() !== "") {
        flat[`feat_${zone}_color_image_preview`] = ci.preview.trim();
      }
      if (typeof ci.uv_rect === "string" && ci.uv_rect.trim() !== "") {
        flat[`feat_${zone}_color_image_uv_rect`] = ci.uv_rect;
      }
    }
  }

  return flat;
}

/**
 * Map a preview GLB path (under ``animated_exports`` or ``player_exports``) to the
 * ``animatedBuildControls`` / ``animatedBuildOptionValues`` slug, or null if unknown.
 */
export function buildOptionSlugFromPreviewGlbRelativePath(relativePath: string): string | null {
  const base = relativePath.split("/").pop() ?? "";
  const anim = parseAnimatedEnemyExportFilename(base);
  if (anim) return normalizeAnimatedSlug(anim.slug);
  const pv = parseVariantFilename(base);
  if (!pv) return null;
  if (pv.base.toLowerCase().startsWith("player_slime_")) {
    return PLAYER_PROCEDURAL_BUILD_SLUG;
  }
  return null;
}

/** ``player_exports/player_slime_blue_00.glb`` → ``blue``; unknown stem → null. */
export function playerColorFromPlayerSlimeExportRelativePath(relativePath: string): string | null {
  const base = relativePath.split("/").pop() ?? "";
  const pv = parseVariantFilename(base);
  if (!pv) return null;
  if (!pv.base.toLowerCase().startsWith("player_slime_")) return null;
  const rest = pv.base.slice("player_slime_".length);
  const c = rest.trim().toLowerCase();
  return c.length > 0 ? c : null;
}

function normalizeHexForCommandBar(raw: unknown): string | undefined {
  if (typeof raw !== "string") return undefined;
  const t = raw.trim();
  if (/^#[0-9a-fA-F]{6}$/.test(t)) return t;
  if (/^[0-9a-fA-F]{6}$/i.test(t)) return `#${t}`;
  return undefined;
}

/** Derive command-bar finish / hex from a build-options snapshot (body zone). */
export function commandExportPatchFromBuildSnapshot(
  snapshot: Record<string, unknown>,
): { finish?: string; hexColor?: string } {
  const out: { finish?: string; hexColor?: string } = {};
  let rawF = snapshot.feat_body_finish;
  let rawH = snapshot.feat_body_hex ?? snapshot.feat_body_color_hex;
  if (rawF === undefined || rawH === undefined) {
    const features = snapshot.features;
    if (features && typeof features === "object" && !Array.isArray(features)) {
      const body = (features as Record<string, FeatureZoneSnapshot>).body;
      if (body && typeof body === "object") {
        if (rawF === undefined && typeof body.finish === "string") rawF = body.finish;
        if (rawH === undefined && typeof body.hex === "string") rawH = body.hex;
      }
    }
  }
  if (typeof rawF === "string" && rawF.trim() !== "") {
    out.finish = rawF.trim();
  }
  const hx = normalizeHexForCommandBar(rawH);
  if (hx) out.hexColor = hx;
  return out;
}
