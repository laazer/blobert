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

function defaultValuesForDefs(defs: AnimatedBuildControlDef[]): Record<string, unknown> {
  const row: Record<string, unknown> = {};
  for (const d of defs) {
    row[d.key] = d.default;
  }
  return row;
}

/** GET /api/meta/enemies — enemies list + procedural build controls per slug. */
export async function fetchEnemyPreviewMeta(): Promise<EnemyPreviewMeta> {
  const res = await fetch(`${BASE}/meta/enemies`);
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  const raw = data.enemies as unknown;
  let enemies: AnimatedEnemyMeta[] = [];
  if (Array.isArray(raw) && raw.length > 0) {
    if (typeof raw[0] === "string") {
      enemies = (raw as string[]).map((slug) => ({
        slug: normalizeAnimatedSlug(slug),
        label: titleCaseSnake(slug),
      }));
    } else {
      enemies = (raw as AnimatedEnemyMeta[]).map((row) => ({
        ...row,
        slug: normalizeAnimatedSlug(row.slug),
      }));
    }
  }
  const animatedBuildControls = parseBuildControls(data.animated_build_controls);
  const metaBackend = data.meta_backend as "ok" | "fallback" | undefined;
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
    for (const d of defs) {
      if (next[slug][d.key] === undefined) {
        next[slug][d.key] = d.default;
      }
    }
  }
  return next;
}

export async function fetchModelRegistry(): Promise<ModelRegistryPayload> {
  const res = await fetch(`${BASE}/registry/model`);
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<ModelRegistryPayload>;
}

export async function patchRegistryEnemyVersion(
  family: string,
  versionId: string,
  body: { draft?: boolean; in_use?: boolean; name?: string | null },
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
      kind: "path";
      path: string;
    };

export type OpenExistingRegistryModelResponse = {
  kind: "enemy" | "path";
  path: string;
  family?: string;
  version_id?: string;
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
