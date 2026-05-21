/**
 * M902-25 — api-client validated fetch: ApiHttpError and ApiValidationError.
 * Spec: project_board/specs/902_25_pydantic_zod_validation_spec.md (Requirement 06).
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiHttpError,
  ApiValidationError,
  getHealth,
  getMetaEnemies,
  getModelRegistry,
} from "./api-client";

const FRONTEND_ROOT = path.resolve(fileURLToPath(new URL("..", import.meta.url)));
const FIXTURES_DIR = path.join(FRONTEND_ROOT, "scripts", "fixtures", "dual_validation");

function loadFixture(name: string): string {
  const filePath = path.join(FIXTURES_DIR, name);
  return fs.readFileSync(filePath, "utf-8");
}

describe("api-client pilot (M902-25)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("getHealth resolves when fetch returns valid health fixture", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(loadFixture("health.ok.json"), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(getHealth()).resolves.toEqual({ status: "ok" });
    expect(globalThis.fetch).toHaveBeenCalledWith("/api/health", undefined);
  });

  it("getModelRegistry throws ApiValidationError when body fails Zod parse", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(loadFixture("registry.invalid.extra_top_key.json"), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(getModelRegistry()).rejects.toSatisfy((error: unknown) => {
      if (!(error instanceof ApiValidationError)) {
        return false;
      }
      return (
        error.message ===
        "The server returned unexpected data. Try refreshing the page or restarting the asset editor."
      );
    });
  });

  it("getModelRegistry throws ApiHttpError on non-ok HTTP status without Zod parse", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "registry unavailable: bridge offline" }), {
        status: 503,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(getModelRegistry()).rejects.toBeInstanceOf(ApiHttpError);
    await expect(getModelRegistry()).rejects.not.toBeInstanceOf(ApiValidationError);
    await expect(getModelRegistry()).rejects.toMatchObject({
      message: "The editor could not reach the server (HTTP 503).",
    });
  });

  it("getMetaEnemies resolves fallback fixture from mocked fetch", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(loadFixture("meta.fallback.ok.json"), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(getMetaEnemies()).resolves.toEqual({
      enemies: [{ slug: "spider", label: "Spider" }],
      animated_build_controls: {},
      meta_backend: "fallback",
      meta_error: "ImportError: simulated",
    });
  });
});
