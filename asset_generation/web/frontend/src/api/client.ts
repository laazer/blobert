import { Asset, FileNode } from "../types";

const BASE = "/api";

export async function fetchFileTree(): Promise<FileNode[]> {
  const res = await fetch(`${BASE}/files`);
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.tree;
}

export async function fetchFileContent(path: string): Promise<string> {
  const res = await fetch(`${BASE}/files/${path}`);
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.content;
}

export async function saveFileContent(path: string, content: string): Promise<void> {
  const res = await fetch(`${BASE}/files/${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function fetchAssets(): Promise<Asset[]> {
  const res = await fetch(`${BASE}/assets`);
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.assets;
}

export async function fetchEnemies(): Promise<string[]> {
  const res = await fetch(`${BASE}/meta/enemies`);
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.enemies;
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
