/**
 * Validated fetch layer for pilot API endpoints (M902-25).
 */
import type { ZodError, ZodType, ZodTypeDef } from "zod";

import {
  HealthResponseSchema,
  MetaEnemiesResponseSchema,
  ModelRegistryResponseSchema,
  type HealthResponse,
  type MetaEnemiesResponse,
  type ModelRegistryResponse,
} from "./schemas";

const API_BASE = "/api";

const USER_VALIDATION_MESSAGE =
  "The server returned unexpected data. Try refreshing the page or restarting the asset editor.";

export class ApiHttpError extends Error {
  readonly status: number;
  readonly url: string;

  constructor(status: number, url: string, bodySnippet: string) {
    super(`The editor could not reach the server (HTTP ${status}).`);
    this.name = "ApiHttpError";
    this.status = status;
    this.url = url;
    if (bodySnippet) {
      console.error("[api-client]", url, bodySnippet.slice(0, 200));
    }
  }
}

export class ApiValidationError extends Error {
  readonly url: string;
  readonly cause: ZodError;

  constructor(url: string, cause: ZodError) {
    super(USER_VALIDATION_MESSAGE);
    this.name = "ApiValidationError";
    this.url = url;
    this.cause = cause;
    console.error("[api-client]", url, cause);
  }
}

export async function validatedFetch<T>(
  url: string,
  schema: ZodType<T, ZodTypeDef, unknown>,
  init?: RequestInit,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`network error fetching ${url}: ${message}`);
  }

  if (!response.ok) {
    const bodyText = await response.text().catch(() => "");
    throw new ApiHttpError(response.status, url, bodyText);
  }

  let data: unknown;
  try {
    data = await response.json();
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`The server returned a response that could not be read. (${url}: ${message})`);
  }

  const parsed = schema.safeParse(data);
  if (!parsed.success) {
    throw new ApiValidationError(url, parsed.error);
  }
  return parsed.data;
}

export async function getHealth(): Promise<HealthResponse> {
  return validatedFetch(`${API_BASE}/health`, HealthResponseSchema);
}

export async function getModelRegistry(): Promise<ModelRegistryResponse> {
  return validatedFetch(`${API_BASE}/registry/model`, ModelRegistryResponseSchema);
}

export async function getMetaEnemies(): Promise<MetaEnemiesResponse> {
  return validatedFetch(`${API_BASE}/meta/enemies`, MetaEnemiesResponseSchema);
}
