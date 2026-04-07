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
    };

/** GET /api/meta/enemies payload (enemies + procedural build controls per slug). */
export type EnemyPreviewMeta = {
  enemies: AnimatedEnemyMeta[];
  animatedBuildControls: Record<string, AnimatedBuildControlDef[]>;
};
