/**
 * Zod runtime schemas for pilot API responses (M902-25).
 * Wire keys use snake_case to match FastAPI JSON.
 */
import { z } from "zod";

export const HealthResponseSchema = z
  .object({
    status: z.literal("ok"),
  })
  .strict();

export type HealthResponse = z.infer<typeof HealthResponseSchema>;

const ALLOWLIST_PREFIXES = [
  "animated_exports/",
  "exports/",
  "player_exports/",
  "level_exports/",
] as const;

function pathIsAllowlisted(path: string): boolean {
  if (!path || path.startsWith("/") || path.split("/").includes("..")) {
    return false;
  }
  return ALLOWLIST_PREFIXES.some((prefix) => path.startsWith(prefix));
}

const VersionRowSchema = z
  .object({
    id: z.string().min(1),
    path: z
      .string()
      .min(1)
      .refine(pathIsAllowlisted, { message: "path not allowlisted" }),
    draft: z.boolean(),
    in_use: z.boolean(),
    name: z.string().max(128).nullable().optional(),
    /** Normalized tags; first entry is the model family slug (Godot-ready manifest field). */
    tags: z.array(z.string().min(1)).optional(),
    /** Validated procedural build snapshot when persisted on the version row (`null` when absent in manifest). */
    build_options: z.preprocess(
      (val) => (val === null ? undefined : val),
      z.record(z.string(), z.unknown()).optional(),
    ),
  })
  .strict();

const SlotsArraySchema = z
  .array(z.string())
  .nullish()
  .transform((value) => value ?? []);

const FamilyBlockSchema = z
  .object({
    versions: z.array(VersionRowSchema),
    slots: SlotsArraySchema.optional(),
  })
  .strict();

const PlayerActiveVisualSchema = z
  .object({
    path: z.string().min(1),
    draft: z.boolean(),
  })
  .strict();

export const ModelRegistryResponseSchema = z
  .object({
    schema_version: z.number().int().min(1),
    enemies: z.record(z.string().min(1), FamilyBlockSchema),
    player: FamilyBlockSchema.nullable().optional(),
    player_active_visual: z.union([z.null(), PlayerActiveVisualSchema]),
  })
  .strict();

export type ModelRegistryResponse = z.infer<typeof ModelRegistryResponseSchema>;

const EnemyMetaRowSchema = z
  .object({
    slug: z.string().min(1),
    label: z.string().min(1),
  })
  .strict();

export const AnimatedBuildControlDefSchema = z.discriminatedUnion("type", [
  z
    .object({
      type: z.literal("int"),
      key: z.string().min(1),
      label: z.string().min(1),
      min: z.number(),
      max: z.number(),
      default: z.number(),
    })
    .strict(),
  z
    .object({
      type: z.literal("select"),
      key: z.string().min(1),
      label: z.string().min(1),
      options: z.array(z.number()),
      default: z.number(),
    })
    .strict(),
  z
    .object({
      type: z.literal("float"),
      key: z.string().min(1),
      label: z.string().min(1),
      min: z.number(),
      max: z.number(),
      step: z.number(),
      default: z.number(),
      unit: z.string().optional(),
      hint: z.string().optional(),
    })
    .strict(),
  z
    .object({
      type: z.literal("str"),
      key: z.string().min(1),
      label: z.string().min(1),
      default: z.string(),
    })
    .strict(),
  z
    .object({
      type: z.literal("select_str"),
      key: z.string().min(1),
      label: z.string().min(1),
      options: z.array(z.string()),
      default: z.string(),
      segmented: z.boolean().optional(),
      hint: z.string().optional(),
    })
    .strict(),
  z
    .object({
      type: z.literal("fill_picker"),
      key: z.string().min(1),
      label: z.string().min(1),
    })
    .strict(),
  z
    .object({
      type: z.literal("bool"),
      key: z.string().min(1),
      label: z.string().min(1),
      default: z.boolean(),
    })
    .strict(),
]);

export const MetaEnemiesResponseSchema = z
  .object({
    enemies: z.array(EnemyMetaRowSchema),
    animated_build_controls: z.record(z.string(), z.array(AnimatedBuildControlDefSchema)),
    meta_backend: z.enum(["ok", "fallback"]),
    meta_error: z.string().min(1).optional(),
  })
  .strict()
  .superRefine((value, ctx) => {
    if (value.meta_backend === "fallback") {
      if (!value.meta_error?.trim()) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "meta_error required when meta_backend is fallback",
          path: ["meta_error"],
        });
      }
    } else if (value.meta_error !== undefined) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "meta_error must be omitted when meta_backend is ok",
        path: ["meta_error"],
      });
    }
  });

export type MetaEnemiesResponse = z.infer<typeof MetaEnemiesResponseSchema>;
