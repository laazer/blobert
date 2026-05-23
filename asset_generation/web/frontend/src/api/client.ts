import { getMetaEnemies, getModelRegistry } from "../api-client";
import {
  AnimatedBuildControlDef,
  AnimatedEnemyMeta,
  Asset,
  EnemyFamilySlotsPayload,
  EnemyPreviewMeta,
  FileNode,
  ModelRegistryPayload,
} from "../types";
import { normalizeAnimatedSlug, titleCaseSnake } from "../utils/enemyDisplay";
import { FEATURE_ZONES_BY_SLUG } from "../utils/animatedZoneControlsMerge";
import { expandBuildOptionsSnapshotForEditor } from "../utils/glbBuildOptionsHydration";

const BASE = "/api";

/** Encode each segment for ``GET/PUT /api/files/{path}`` (spaces, ``#``, Unicode, etc.). */
export function encodeFileApiPath(relPath: string): string {
  return relPath
    .split("/")
    .filter((seg) => seg.length > 0)
    .map((seg) => encodeURIComponent(seg))
    .join("/");
}

export async function fetchFileTree(): Promise<FileNode[]> {
  const res = await fetch(`${BASE}/files`);
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.tree;
}

export async function fetchFileContent(path: string): Promise<string> {
  const enc = encodeFileApiPath(path);
  const res = await fetch(`${BASE}/files/${enc}`);
  if (!res.ok) {
    const body = (await res.text()).trim();
    throw new Error(body || `HTTP ${res.status} ${res.statusText}`);
  }
  const data = await res.json();
  return data.content;
}

export async function saveFileContent(path: string, content: string): Promise<void> {
  const enc = encodeFileApiPath(path);
  const res = await fetch(`${BASE}/files/${enc}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) {
    const body = (await res.text()).trim();
    throw new Error(body || `HTTP ${res.status} ${res.statusText}`);
  }
}

export async function fetchAssets(): Promise<Asset[]> {
  const res = await fetch(`${BASE}/assets`);
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.assets;
}

function parseBuildControls(raw: unknown): Record<string, AnimatedBuildControlDef[]> {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return {};
  return raw as Record<string, AnimatedBuildControlDef[]>;
}

/** Defaults for one slug's control defs (used by merge + run JSON pruning). */
export function defaultValuesForDefs(defs: readonly AnimatedBuildControlDef[]): Record<string, unknown> {
  const row: Record<string, unknown> = {};
  for (const d of defs) {
    row[d.key] = "default" in d ? d.default : undefined;
  }
  return row;
}

const LEGACY_GLOBAL_TEXTURE_KEYS = [
  "texture_mode",
  "texture_spot_color",
  "texture_spot_bg_color",
  "texture_spot_density",
  "texture_spot_pattern",
  "texture_stripe_color",
  "texture_stripe_bg_color",
  "texture_stripe_width",
  "texture_stripe_direction",
  "texture_stripe_rot_yaw",
  "texture_stripe_rot_pitch",
] as const;

const LEGACY_TEXTURE_TO_SUFFIX: Record<(typeof LEGACY_GLOBAL_TEXTURE_KEYS)[number], string> = {
  texture_mode: "mode",
  texture_spot_color: "pattern",
  texture_spot_bg_color: "background",
  texture_spot_density: "spot_density",
  texture_spot_pattern: "spot_pattern",
  texture_stripe_color: "pattern",
  texture_stripe_bg_color: "background",
  texture_stripe_width: "stripe_width",
  texture_stripe_direction: "stripe_direction",
  texture_stripe_rot_yaw: "stripe_rot_yaw",
  texture_stripe_rot_pitch: "stripe_rot_pitch",
};

/** Map old global ``texture_stripe_rot_{x,y,z}`` to yaw/pitch before zone copy. */
function migrateLegacyGlobalStripeRotation(merged: Record<string, unknown>): void {
  const x = merged.texture_stripe_rot_x;
  const y = merged.texture_stripe_rot_y;
  const z = merged.texture_stripe_rot_z;
  if (x === undefined && y === undefined && z === undefined) return;
  if (merged.texture_stripe_rot_pitch === undefined && x !== undefined) {
    merged.texture_stripe_rot_pitch = x;
  }
  if (merged.texture_stripe_rot_yaw === undefined && y !== undefined) {
    merged.texture_stripe_rot_yaw = y;
  }
  delete merged.texture_stripe_rot_x;
  delete merged.texture_stripe_rot_y;
  delete merged.texture_stripe_rot_z;
}

/** Copy legacy global ``texture_*`` keys into ``feat_{zone}_texture_*`` once, then drop globals. */
function migrateLegacyGlobalTextureToZones(slug: string, merged: Record<string, unknown>): void {
  migrateLegacyGlobalStripeRotation(merged);
  const hasLegacy = LEGACY_GLOBAL_TEXTURE_KEYS.some((k) => merged[k] !== undefined);
  if (!hasLegacy) return;
  if (merged.feat_body_texture_mode !== undefined) return;

  const zones = FEATURE_ZONES_BY_SLUG[normalizeAnimatedSlug(slug)];
  if (!zones?.length) return;

  for (const z of zones) {
    for (const legacy of LEGACY_GLOBAL_TEXTURE_KEYS) {
      const v = merged[legacy];
      if (v === undefined) continue;
      const suf = LEGACY_TEXTURE_TO_SUFFIX[legacy];
      merged[`feat_${z}_texture_${suf}`] = v;
    }
  }
  for (const k of LEGACY_GLOBAL_TEXTURE_KEYS) {
    delete merged[k];
  }
}

/** GET /api/meta/enemies — enemies list + procedural build controls per slug. */
export async function fetchEnemyPreviewMeta(): Promise<EnemyPreviewMeta> {
  const data = await getMetaEnemies();
  const enemies: AnimatedEnemyMeta[] = data.enemies.map((row) => ({
    slug: normalizeAnimatedSlug(row.slug),
    label: row.label,
  }));
  const animatedBuildControls = parseBuildControls(data.animated_build_controls);
  const metaBackend = data.meta_backend;
  const metaError =
    typeof data.meta_error === "string" && data.meta_error.trim()
      ? data.meta_error
      : null;
  return { enemies, animatedBuildControls, metaBackend, metaError };
}

/** Merge server defaults with existing per-slug option maps (preserves user edits). */
export function mergeBuildOptionValues(
  controls: Record<string, AnimatedBuildControlDef[]>,
  previous: Record<string, Record<string, unknown>>,
): Record<string, Record<string, unknown>> {
  const next: Record<string, Record<string, unknown>> = { ...previous };
  for (const slug of Object.keys(controls)) {
    const defs = controls[slug];
    const defaults = defaultValuesForDefs(defs);
    const existing = next[slug] ?? {};
    next[slug] = { ...defaults, ...existing };
    migrateLegacyGlobalTextureToZones(slug, next[slug]);
    for (const d of defs) {
      if (next[slug][d.key] === undefined) {
        next[slug][d.key] = "default" in d ? d.default : undefined;
      }
    }
  }
  return next;
}

/** ``GET /api/assets/{path}`` for ``*.build_options.json`` next to an animated/player GLB (404 → null). */
export async function fetchBuildOptionsSidecarForGlbPath(relativeGlbPath: string): Promise<Record<string, unknown> | null> {
  if (!relativeGlbPath.toLowerCase().endsWith(".glb")) return null;
  const jsonPath = relativeGlbPath.replace(/\.glb$/i, ".build_options.json");
  const enc = jsonPath
    .split("/")
    .filter((seg) => seg.length > 0)
    .map((seg) => encodeURIComponent(seg))
    .join("/");
  const res = await fetch(`${BASE}/assets/${enc}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error((await res.text()).trim() || `HTTP ${res.status}`);
  const data: unknown = await res.json();
  if (!data || typeof data !== "object" || Array.isArray(data)) return null;
  return data as Record<string, unknown>;
}

/**
 * Replace one slug's build row with ``defaults ∪ snapshot`` (used when the preview GLB has a sidecar).
 * Runs legacy texture migration for that row.
 */
export function replaceAnimatedSlugBuildOptionsRow(
  controls: Record<string, AnimatedBuildControlDef[]>,
  full: Record<string, Record<string, unknown>>,
  slug: string,
  snapshot: Record<string, unknown>,
): Record<string, Record<string, unknown>> {
  const defs = controls[slug] ?? [];
  const defaults = defaultValuesForDefs(defs);
  const flatSnapshot = expandBuildOptionsSnapshotForEditor(slug, snapshot);
  const row: Record<string, unknown> = { ...defaults, ...flatSnapshot };
  migrateLegacyGlobalTextureToZones(slug, row);
  return { ...full, [slug]: row };
}

export async function fetchModelRegistry(): Promise<ModelRegistryPayload> {
  const data = await getModelRegistry();
  return data as ModelRegistryPayload;
}

export async function patchRegistryEnemyVersion(
  family: string,
  versionId: string,
  body: { draft?: boolean; in_use?: boolean; name?: string | null; tags?: string[] },
): Promise<ModelRegistryPayload> {
  const encFamily = encodeURIComponent(family);
  const encVid = encodeURIComponent(versionId);
  const res = await fetch(`${BASE}/registry/model/enemies/${encFamily}/versions/${encVid}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<ModelRegistryPayload>;
}

export async function patchRegistryPlayerActiveVisual(body: {
  draft?: boolean;
  path?: string;
}): Promise<ModelRegistryPayload> {
  const res = await fetch(`${BASE}/registry/model/player_active_visual`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<ModelRegistryPayload>;
}

export async function fetchEnemyFamilySlots(family: string): Promise<EnemyFamilySlotsPayload> {
  const encFamily = encodeURIComponent(family);
  const res = await fetch(`${BASE}/registry/model/enemies/${encFamily}/slots`);
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<EnemyFamilySlotsPayload>;
}

/** Register ``animated_exports/{family}_animated_*.glb`` on disk that are missing from the manifest. */
export async function postSyncDiscoveredAnimatedGlbVersions(family: string): Promise<ModelRegistryPayload> {
  const encFamily = encodeURIComponent(family);
  const res = await fetch(`${BASE}/registry/model/enemies/${encFamily}/sync_animated_exports`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<ModelRegistryPayload>;
}

export async function putEnemyFamilySlots(
  family: string,
  versionIds: string[],
): Promise<EnemyFamilySlotsPayload> {
  const encFamily = encodeURIComponent(family);
  const res = await fetch(`${BASE}/registry/model/enemies/${encFamily}/slots`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ version_ids: versionIds }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<EnemyFamilySlotsPayload>;
}

/** POST /api/registry/model/player/sync_player_exports — scan player_exports/*.glb and register missing rows. */
export async function postSyncDiscoveredPlayerGlbVersions(): Promise<ModelRegistryPayload> {
  const res = await fetch(`${BASE}/registry/model/player/sync_player_exports`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<ModelRegistryPayload>;
}

/** Player slot list; same payload shape as enemy slots with ``family: "player"``. */
export type PlayerFamilySlotsPayload = EnemyFamilySlotsPayload;

export async function fetchPlayerFamilySlots(): Promise<PlayerFamilySlotsPayload> {
  const res = await fetch(`${BASE}/registry/model/player/slots`);
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<PlayerFamilySlotsPayload>;
}

export async function putPlayerFamilySlots(versionIds: string[]): Promise<PlayerFamilySlotsPayload> {
  const res = await fetch(`${BASE}/registry/model/player/slots`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ version_ids: versionIds }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<PlayerFamilySlotsPayload>;
}

export type DeleteEnemyVersionRequest = {
  delete_files?: boolean;
  confirm: boolean;
  confirm_text?: string;
  target_path?: string;
};

export async function deleteRegistryEnemyVersion(
  family: string,
  versionId: string,
  body: DeleteEnemyVersionRequest,
): Promise<ModelRegistryPayload> {
  const encFamily = encodeURIComponent(family);
  const encVid = encodeURIComponent(versionId);
  const res = await fetch(`${BASE}/registry/model/enemies/${encFamily}/versions/${encVid}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<ModelRegistryPayload>;
}

export type DeletePlayerActiveVisualRequest = {
  confirm: boolean;
};

export async function deleteRegistryPlayerActiveVisual(
  body: DeletePlayerActiveVisualRequest,
): Promise<ModelRegistryPayload> {
  const res = await fetch(`${BASE}/registry/model/player_active_visual`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<ModelRegistryPayload>;
}

export type LoadExistingCandidate =
  | {
      kind: "enemy";
      family: string;
      version_id: string;
      path: string;
    }
  | {
      kind: "player";
      version_id: string;
      path: string;
    };

export type LoadExistingCandidatesPayload = {
  candidates: LoadExistingCandidate[];
};

export type OpenExistingRegistryModelRequest =
  | {
      kind: "enemy";
      family: string;
      version_id: string;
    }
  | {
      kind: "player";
      version_id: string;
    }
  | {
      kind: "path";
      path: string;
    };

export type OpenExistingRegistryModelResponse = {
  kind: "enemy" | "player" | "path";
  path: string;
  family?: string;
  version_id?: string;
  /** Validated procedural build snapshot when the registry row has one. */
  build_options?: Record<string, unknown>;
};

export async function fetchLoadExistingCandidates(): Promise<LoadExistingCandidatesPayload> {
  const res = await fetch(`${BASE}/registry/model/load_existing/candidates`);
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<LoadExistingCandidatesPayload>;
}

export async function openExistingRegistryModel(
  body: OpenExistingRegistryModelRequest,
): Promise<OpenExistingRegistryModelResponse> {
  const res = await fetch(`${BASE}/registry/model/load_existing/open`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<OpenExistingRegistryModelResponse>;
}

export async function fetchAnimations(): Promise<string[]> {
  const res = await fetch(`${BASE}/meta/animations`);
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.animations;
}

export async function killProcess(): Promise<void> {
  await fetch(`${BASE}/run/kill`, { method: "POST" });
}

export function assetUrl(path: string, bust?: boolean): string {
  const url = `${BASE}/assets/${path}`;
  return bust ? `${url}?t=${Date.now()}` : url;
}

export interface TextureAsset {
  id: string;
  filename: string;
  display_name: string;
  description: string;
  layout: string;
  url: string;
  width: number;
  height: number;
  tiling_supported: boolean;
}

export async function fetchTextureAssets(): Promise<TextureAsset[]> {
  const res = await fetch(`${BASE}/assets/textures`);
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  const textures = Array.isArray(data.textures) ? data.textures : [];
  return textures.filter((texture: unknown): texture is TextureAsset => {
    if (!texture || typeof texture !== "object") return false;
    const row = texture as Record<string, unknown>;
    return (
      typeof row.id === "string" &&
      typeof row.filename === "string" &&
      typeof row.display_name === "string" &&
      typeof row.description === "string" &&
      typeof row.layout === "string" &&
      typeof row.url === "string" &&
      typeof row.width === "number" &&
      typeof row.height === "number" &&
      typeof row.tiling_supported === "boolean"
    );
  });
}
