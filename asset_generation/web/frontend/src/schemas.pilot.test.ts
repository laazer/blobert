/**
 * M902-25 — Zod drift tests for pilot response schemas.
 * Spec: project_board/specs/902_25_pydantic_zod_validation_spec.md (Requirement 09).
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { z, ZodError } from "zod";

import {
  HealthResponseSchema,
  MetaEnemiesResponseSchema,
  ModelRegistryResponseSchema,
} from "./schemas";

const FRONTEND_ROOT = path.resolve(fileURLToPath(new URL("..", import.meta.url)));
const FIXTURES_DIR = path.join(FRONTEND_ROOT, "scripts", "fixtures", "dual_validation");

function loadFixture(name: string): unknown {
  const filePath = path.join(FIXTURES_DIR, name);
  expect(fs.existsSync(filePath), `missing fixture ${filePath}`).toBe(true);
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

const VALID_CASES: Array<{ file: string; schema: z.ZodTypeAny }> = [
  { file: "health.ok.json", schema: HealthResponseSchema },
  { file: "registry.minimal.ok.json", schema: ModelRegistryResponseSchema },
  { file: "meta.ok.minimal.json", schema: MetaEnemiesResponseSchema },
  { file: "meta.fallback.ok.json", schema: MetaEnemiesResponseSchema },
];

const INVALID_CASES: Array<{ file: string; schema: z.ZodTypeAny }> = [
  { file: "health.invalid.wrong_status.json", schema: HealthResponseSchema },
  { file: "health.invalid.empty.json", schema: HealthResponseSchema },
  { file: "health.invalid.extra_key.json", schema: HealthResponseSchema },
  { file: "registry.invalid.extra_top_key.json", schema: ModelRegistryResponseSchema },
  { file: "registry.invalid.schema_version.json", schema: ModelRegistryResponseSchema },
  { file: "registry.invalid.version_missing_draft.json", schema: ModelRegistryResponseSchema },
  { file: "registry.invalid.bad_path.json", schema: ModelRegistryResponseSchema },
  { file: "registry.invalid.pav_extra_key.json", schema: ModelRegistryResponseSchema },
  { file: "meta.invalid.backend.json", schema: MetaEnemiesResponseSchema },
  { file: "meta.invalid.missing_slug.json", schema: MetaEnemiesResponseSchema },
  { file: "meta.invalid.controls_not_object.json", schema: MetaEnemiesResponseSchema },
  { file: "meta.invalid.control_missing_type.json", schema: MetaEnemiesResponseSchema },
  { file: "meta.invalid.row_extra_key.json", schema: MetaEnemiesResponseSchema },
  { file: "meta.invalid.fallback_missing_error.json", schema: MetaEnemiesResponseSchema },
];

describe("pilot Zod schemas (M902-25 drift fixtures)", () => {
  it("coerces null enemy slots to an empty array (registry families without slot assignments)", () => {
    const parsed = ModelRegistryResponseSchema.parse({
      schema_version: 1,
      enemies: {
        acid_spitter: {
          versions: [
            {
              id: "acid_spitter_animated_00",
              path: "animated_exports/acid_spitter_animated_00.glb",
              draft: false,
              in_use: true,
            },
          ],
          slots: null,
        },
      },
      player_active_visual: null,
    });
    expect(parsed.enemies.acid_spitter.slots).toEqual([]);
  });

  it.each(VALID_CASES)("parses valid fixture $file", ({ file, schema }) => {
    const payload = loadFixture(file);
    const parsed = schema.parse(payload);
    expect(parsed).toStrictEqual(payload);
  });

  it.each(INVALID_CASES)("rejects invalid fixture $file", ({ file, schema }) => {
    const payload = loadFixture(file);
    expect(() => schema.parse(payload)).toThrow(ZodError);
    try {
      schema.parse(payload);
    } catch (error) {
      expect(error).toBeInstanceOf(ZodError);
      expect((error as ZodError).issues.length).toBeGreaterThanOrEqual(1);
    }
  });
});
