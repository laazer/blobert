export interface FileNode {
  type: "file" | "dir";
  path: string;
  name: string;
  children?: FileNode[];
}

export interface Asset {
  path: string;
  name: string;
  dir: string;
  size: number;
}

export interface TerminalLine {
  id: number;
  text: string;
}

export type RunCmd = "animated" | "player" | "level" | "smart" | "stats" | "test";

/** Animated enemy slug + display label from GET /api/meta/enemies (source of truth: Python registry). */
export type AnimatedEnemyMeta = {
  slug: string;
  label: string;
};

/** One procedural control for an animated enemy slug (from Python `animated_build_options`). */
export type AnimatedBuildControlDef =
  | {
      key: string;
      label: string;
      type: "int";
      min: number;
      max: number;
      default: number;
    }
  | {
      key: string;
      label: string;
      type: "select";
      options: number[];
      default: number;
    }
  | {
      key: string;
      label: string;
      type: "float";
      min: number;
      max: number;
      step: number;
      default: number;
    }
  | {
      key: string;
      label: string;
      type: "str";
      default: string;
    }
  | {
      key: string;
      label: string;
      type: "select_str";
      options: string[];
      default: string;
    };

/** One row under ``enemies[slug].versions`` (MRVC-2). */
export type RegistryEnemyVersion = {
  id: string;
  path: string;
  draft: boolean;
  in_use: boolean;
};

/** GET /api/registry/model payload. */
export type ModelRegistryPayload = {
  schema_version: number;
  enemies: Record<string, { versions: RegistryEnemyVersion[] }>;
  player_active_visual: null | { path: string; draft: boolean };
};

/** GET /api/meta/enemies payload (enemies + procedural build controls per slug). */
export type EnemyPreviewMeta = {
  enemies: AnimatedEnemyMeta[];
  animatedBuildControls: Record<string, AnimatedBuildControlDef[]>;
  /** Present when API could not load Python introspection (ImportError); controls are empty. */
  metaBackend?: "ok" | "fallback";
  metaError?: string | null;
};
