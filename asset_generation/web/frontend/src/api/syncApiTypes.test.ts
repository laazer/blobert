/**
 * M902-24 — sync-api-types.sh integration (Vitest, node env).
 * Spec: project_board/specs/902_24_openapi_typescript_gen_spec.md (Requirement 07).
 */
import { execSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it } from "vitest";

const FRONTEND_ROOT = path.resolve(fileURLToPath(new URL("../..", import.meta.url)));
const SYNC_SCRIPT = path.join(FRONTEND_ROOT, "scripts", "sync-api-types.sh");

type OpenApiFixture = {
  openapi: string;
  info: { title: string; version: string };
  paths: Record<string, unknown>;
};

function minimalOpenApi(): OpenApiFixture {
  return {
    openapi: "3.0.3",
    info: { title: "Blobert Asset Editor API", version: "0.1.0" },
    paths: {
      "/api/health": {
        get: {
          responses: {
            200: {
              content: {
                "application/json": {
                  schema: {
                    type: "object",
                    properties: { status: { type: "string" } },
                    required: ["status"],
                  },
                },
              },
            },
          },
        },
      },
      "/api/registry/model": {
        get: {
          responses: {
            200: {
              content: {
                "application/json": {
                  schema: { type: "object" },
                },
              },
            },
          },
        },
      },
    },
  };
}

function runSync(env: Record<string, string>): { status: number; stderr: string; stdout: string } {
  const merged = { ...process.env, ...env };
  try {
    const stdout = execSync(`bash "${SYNC_SCRIPT}"`, {
      cwd: FRONTEND_ROOT,
      env: merged,
      encoding: "utf-8",
      stdio: ["ignore", "pipe", "pipe"],
      timeout: 120_000,
    });
    return { status: 0, stderr: "", stdout };
  } catch (err: unknown) {
    const e = err as { status?: number; stderr?: string; stdout?: string };
    return {
      status: typeof e.status === "number" ? e.status : 1,
      stderr: e.stderr ?? "",
      stdout: e.stdout ?? "",
    };
  }
}

describe("sync-api-types.sh (M902-24)", () => {
  const tmpDirs: string[] = [];

  afterEach(() => {
    for (const dir of tmpDirs.splice(0)) {
      fs.rmSync(dir, { recursive: true, force: true });
    }
  });

  function isolatedPaths(): { cache: string; output: string; dir: string } {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "blobert-sync-api-types-"));
    tmpDirs.push(dir);
    return {
      dir,
      cache: path.join(dir, "openapi.cached.json"),
      output: path.join(dir, "api.types.ts"),
    };
  }

  it("script exists and is executable", () => {
    expect(fs.existsSync(SYNC_SCRIPT)).toBe(true);
    fs.accessSync(SYNC_SCRIPT, fs.constants.X_OK);
  });

  it("T1: valid cache with BLOBERT_SYNC_SKIP_FETCH=1 exits 0 and writes paths", () => {
    const { cache, output } = isolatedPaths();
    fs.writeFileSync(cache, JSON.stringify(minimalOpenApi()));

    const result = runSync({
      BLOBERT_OPENAPI_CACHE: cache,
      BLOBERT_OPENAPI_OUTPUT: output,
      BLOBERT_SYNC_SKIP_FETCH: "1",
    });

    expect(result.status).toBe(0);
    const generated = fs.readFileSync(output, "utf-8");
    expect(generated).toContain("paths");
    expect(generated).toContain('"/api/health"');
    expect(generated).toContain('"/api/registry/model"');
  });

  it("T1 offline: fetch failure uses valid cache (stderr warning, exit 0)", () => {
    const { cache, output } = isolatedPaths();
    fs.writeFileSync(cache, JSON.stringify(minimalOpenApi()));

    const result = runSync({
      BLOBERT_OPENAPI_CACHE: cache,
      BLOBERT_OPENAPI_OUTPUT: output,
      BLOBERT_OPENAPI_URL: "http://127.0.0.1:1/openapi.json",
    });

    expect(result.status).toBe(0);
    expect(result.stderr).toMatch(/using cached OpenAPI/i);
    expect(fs.existsSync(output)).toBe(true);
  });

  it("T2: no cache and unreachable fetch exits 3", () => {
    const { cache, output } = isolatedPaths();

    const result = runSync({
      BLOBERT_OPENAPI_CACHE: cache,
      BLOBERT_OPENAPI_OUTPUT: output,
      BLOBERT_OPENAPI_URL: "http://127.0.0.1:1/openapi.json",
    });

    expect(result.status).toBe(3);
    expect(result.stderr).toMatch(/fetch failed/i);
    expect(result.stderr).toMatch(/no cache/i);
    expect(fs.existsSync(output)).toBe(false);
  });

  it("T4: corrupt cache JSON exits 4", () => {
    const { cache, output } = isolatedPaths();
    fs.writeFileSync(cache, "{not-json");

    const result = runSync({
      BLOBERT_OPENAPI_CACHE: cache,
      BLOBERT_OPENAPI_OUTPUT: output,
      BLOBERT_SYNC_SKIP_FETCH: "1",
    });

    expect(result.status).toBe(4);
    expect(result.stderr).toMatch(/invalid cache/i);
    expect(fs.existsSync(output)).toBe(false);
  });

  it("T6: generated module is importable shape for /api/health (grep contract)", () => {
    const { cache, output } = isolatedPaths();
    fs.writeFileSync(cache, JSON.stringify(minimalOpenApi()));

    const result = runSync({
      BLOBERT_OPENAPI_CACHE: cache,
      BLOBERT_OPENAPI_OUTPUT: output,
      BLOBERT_SYNC_SKIP_FETCH: "1",
    });
    expect(result.status).toBe(0);

    const text = fs.readFileSync(output, "utf-8");
    expect(text).toMatch(/AUTO-GENERATED by scripts\/sync-api-types\.sh/i);
    expect(text).toContain('"/api/health"');
  });
});
