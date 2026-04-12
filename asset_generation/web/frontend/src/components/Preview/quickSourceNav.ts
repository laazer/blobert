import { type AnimatedEnemyMeta, RunCmd } from "../../types";
import {
  DEFAULT_ANIMATED_ENEMY_META,
  DEFAULT_ANIMATED_ENEMY_SLUGS,
  slugDisplayLabel,
} from "../../utils/enemyDisplay";

/** @deprecated use DEFAULT_ANIMATED_ENEMY_SLUGS from utils/enemyDisplay */
export const ANIMATED_ENEMY_SLUGS = DEFAULT_ANIMATED_ENEMY_SLUGS;

export type PartTreeNode = {
  id: string;
  label: string;
  children?: PartTreeNode[];
};

export type SourceNavTarget = {
  path: string;
  description: string;
  /** Button label in “More animation”; defaults to derived from path in the UI if omitted */
  shortLabel?: string;
};

function animatedEnemyModulePath(slug: string): string {
  return `enemies/animated_${slug}.py`;
}

export function getModelCodeTarget(
  cmd: RunCmd,
  enemy: string,
  animatedMeta: readonly AnimatedEnemyMeta[] = DEFAULT_ANIMATED_ENEMY_META,
): SourceNavTarget | null {
  const e = (enemy || "").trim();
  const animatedSlugs = animatedMeta.map((m) => m.slug);

  switch (cmd) {
    case "animated":
      if (e === "all") {
        return { path: "enemies/animated/registry.py", description: "Animated enemy registry" };
      }
      if (animatedSlugs.includes(e)) {
        return {
          path: animatedEnemyModulePath(e),
          description: `Mesh builder: ${slugDisplayLabel(e, animatedMeta)} (${e})`,
        };
      }
      return { path: "enemies/base_enemy.py", description: "Base enemy mesh API" };

    case "player":
      return { path: "player/player_slime_body.py", description: "Player slime mesh geometry" };

    case "level":
      return { path: "level/level_object_builder.py", description: "Level object mesh builder" };

    default:
      return null;
  }
}

export function getAnimationCodeTarget(cmd: RunCmd, _enemy: string): SourceNavTarget | null {
  switch (cmd) {
    case "player":
      return { path: "player/player_animations.py", description: "Player animation clips" };
    default:
      return { path: "animations/animation_system.py", description: "Enemy animation system" };
  }
}

/** Short labels for the rest of the Blender animation pipeline (same dir as animation_system). */
export function getAnimationCodeExtras(cmd: RunCmd): SourceNavTarget[] {
  switch (cmd) {
    case "player":
      return [
        {
          path: "animations/keyframe_system.py",
          description: "Shared keyframe helpers",
          shortLabel: "Keyframes",
        },
        {
          path: "player/player_armature.py",
          description: "Player armature",
          shortLabel: "Armature",
        },
      ];
    default:
      return [
        {
          path: "animations/keyframe_system.py",
          description: "Bone keyframes",
          shortLabel: "Keyframes",
        },
        {
          path: "body_families/registry.py",
          description: "Body families: registry + import rigs",
          shortLabel: "Registry",
        },
        {
          path: "body_families/motion_base.py",
          description: "Base body-type motion (core + extended clips)",
          shortLabel: "Motion base",
        },
        {
          path: "body_families/keywords.py",
          description: "Smart-generation keywords per family",
          shortLabel: "Keywords",
        },
        {
          path: "animations/body_types.py",
          description: "Thin re-export of body_families for older imports",
          shortLabel: "Re-export",
        },
        {
          path: "enemies/animated_slug.py",
          description: "Example rig (get_rig_definition) — animated_slug.py",
          shortLabel: "Example rig",
        },
      ];
  }
}

/** `PlayerSlimeBody.finalize()` join order (single joined mesh). */
function playerSlimePartTree(): PartTreeNode[] {
  return [
    {
      id: "player-root",
      label: "Player slime (join order in player_slime_body.py)",
      children: [
        {
          id: "player-body",
          label: "Body",
          children: [
            { id: "pj0", label: "[0] body — main blob" },
            { id: "pj1", label: "[1] drip — base drip sphere" },
          ],
        },
        {
          id: "player-face",
          label: "Face (per-eye: sclera → pupil → highlight)",
          children: [
            { id: "pj2", label: "[2] sclera — left" },
            { id: "pj3", label: "[3] sclera — right" },
            { id: "pj4", label: "[4] pupil — left" },
            { id: "pj5", label: "[5] pupil — right" },
            { id: "pj6", label: "[6] highlight — left" },
            { id: "pj7", label: "[7] highlight — right" },
            { id: "pj8", label: "[8] cheek — left" },
            { id: "pj9", label: "[9] cheek — right" },
          ],
        },
        {
          id: "player-arms",
          label: "Arms",
          children: [
            { id: "pj10", label: "[10] arm — left" },
            { id: "pj11", label: "[11] arm — right" },
          ],
        },
      ],
    },
  ];
}

function _coerceSpiderEyeCount(
  raw: unknown,
  allowed: readonly number[],
  defaultVal: number,
): number {
  const n = Math.floor(Number(raw));
  if (Number.isNaN(n)) return defaultVal;
  if (allowed.length > 0) {
    if (allowed.includes(n)) return n;
    return defaultVal;
  }
  // Server options not loaded (e.g. tests): use build value for part-tree labels only
  if (n >= 0 && n <= 32) return n;
  return defaultVal;
}

function _coerceClawPeripheralEyes(raw: unknown, min: number, max: number): number {
  const n = Math.floor(Number(raw));
  if (Number.isNaN(n)) return min;
  return Math.max(min, Math.min(max, n));
}

const _SPIDER_LEG_NAMES = [
  "front left",
  "front right",
  "middle left",
  "middle right",
  "back left",
  "back right",
] as const;

/** `self.parts` for spider — order matches `animated_spider.py` for the given `eye_count`. */
function spiderPartTreeForBuild(eyeCount: number): PartTreeNode {
  const ec = Math.max(0, eyeCount);
  const children: PartTreeNode[] = [
    { id: "sp-0", label: "parts[0] — body" },
    { id: "sp-1", label: "parts[1] — head" },
  ];
  for (let i = 0; i < ec; i += 1) {
    children.push({ id: `sp-e-${i}`, label: `parts[${2 + i}] — eye` });
  }
  for (let i = 0; i < 6; i += 1) {
    const idx = 2 + ec + i;
    children.push({
      id: `sp-leg-${i}`,
      label: `parts[${idx}] — leg — ${_SPIDER_LEG_NAMES[i]}`,
    });
  }
  const total = 2 + ec + 6;
  return {
    id: "spider-root",
    label: `Spider — parts[] (${total} parts, animated_spider.py)`,
    children,
  };
}

/** `self.parts` for claw crawler — matches `animated_claw_crawler.py` for `peripheral_eyes`. */
function clawCrawlerPartTreeForBuild(
  raw: unknown,
  min = 0,
  max = 3,
): PartTreeNode {
  const pe = _coerceClawPeripheralEyes(raw, min, max);
  const children: PartTreeNode[] = [
    { id: "cc-0", label: "parts[0] — body" },
    { id: "cc-1", label: "parts[1] — head" },
  ];
  let idx = 2;
  for (let i = 0; i < pe; i += 1) {
    children.push({ id: `cc-pe-${i}`, label: `parts[${idx}] — peripheral eye` });
    idx += 1;
  }
  children.push(
    { id: "cc-cl-l", label: `parts[${idx}] — front claw — left` },
    { id: "cc-cl-r", label: `parts[${idx + 1}] — front claw — right` },
  );
  idx += 2;
  const legNames = ["middle left", "middle right", "back left", "back right"] as const;
  for (let i = 0; i < 4; i += 1) {
    children.push({ id: `cc-leg-${i}`, label: `parts[${idx + i}] — leg — ${legNames[i]}` });
  }
  const total = 2 + pe + 2 + 4;
  return {
    id: "claw-root",
    label: `Claw crawler — parts[] (${total} parts, animated_claw_crawler.py)`,
    children,
  };
}

/** Optional hints from GET /api/meta ``animated_build_controls`` (same source as Build panel). */
export type MeshPartTreeControlHints = {
  spiderEyeOptions?: readonly number[];
  spiderEyeDefault?: number;
  clawPeripheralMin?: number;
  clawPeripheralMax?: number;
};

/** Full `self.parts` order per `animated_{slug}.py` (variant-specific when `buildOptions` is set). */
function animatedEnemyPartTree(
  slug: string,
  buildOptions: Record<string, unknown> = {},
  hints?: MeshPartTreeControlHints,
): PartTreeNode {
  switch (slug) {
    case "spider": {
      const opts = hints?.spiderEyeOptions;
      const allowed = opts && opts.length > 0 ? [...opts] : [];
      const eyeDefault = hints?.spiderEyeDefault;
      const def =
        allowed.length > 0
          ? eyeDefault != null && allowed.includes(eyeDefault)
            ? eyeDefault
            : (allowed[0] ?? 2)
          : (eyeDefault ?? 2);
      const eyeCount = _coerceSpiderEyeCount(buildOptions.eye_count, allowed, def);
      return spiderPartTreeForBuild(eyeCount);
    }

    case "slug":
      return {
        id: "slug-root",
        label: "Slug — parts[] (animated_slug.py)",
        children: [
          { id: "ts0", label: "parts[0] — body" },
          { id: "ts1", label: "parts[1] — head bump" },
          { id: "ts2", label: "parts[2] — eye stalk — left" },
          { id: "ts3", label: "parts[3] — eye — left" },
          { id: "ts4", label: "parts[4] — eye stalk — right" },
          { id: "ts5", label: "parts[5] — eye — right" },
        ],
      };

    case "imp":
      return {
        id: "imp-root",
        label: "Imp — parts[] (animated_imp.py)",
        children: [
          { id: "ei0", label: "parts[0] — body" },
          { id: "ei1", label: "parts[1] — head" },
          { id: "ei2", label: "parts[2] — arm — left" },
          { id: "ei3", label: "parts[3] — hand — left" },
          { id: "ei4", label: "parts[4] — arm — right" },
          { id: "ei5", label: "parts[5] — hand — right" },
          { id: "ei6", label: "parts[6] — leg — left" },
          { id: "ei7", label: "parts[7] — leg — right" },
        ],
      };

    case "spitter":
      return {
        id: "spitter-root",
        label: "Spitter — parts[] (animated_spitter.py)",
        children: [
          { id: "st0", label: "parts[0] — body" },
          { id: "st1", label: "parts[1] — head" },
          { id: "st2", label: "parts[2] — tendril — left" },
          { id: "st3", label: "parts[3] — tendril — right" },
        ],
      };

    case "claw_crawler": {
      const min = hints?.clawPeripheralMin ?? 0;
      const max = hints?.clawPeripheralMax ?? 3;
      return clawCrawlerPartTreeForBuild(buildOptions.peripheral_eyes, min, max);
    }

    case "carapace_husk":
      return {
        id: "ch-root",
        label: "Carapace husk — parts[] (animated_carapace_husk.py)",
        children: [
          { id: "ch0", label: "parts[0] — body" },
          { id: "ch1", label: "parts[1] — head" },
          { id: "ch2", label: "parts[2] — arm — left" },
          { id: "ch3", label: "parts[3] — arm — right" },
          { id: "ch4", label: "parts[4] — leg — left" },
          { id: "ch5", label: "parts[5] — leg — right" },
        ],
      };

    default:
      return {
        id: "unknown-root",
        label: `${slug} — parts[] (animated_${slug}.py)`,
        children: [{ id: "unk0", label: "parts[0…] — see module" }],
      };
  }
}

function levelObjectPartTree(): PartTreeNode[] {
  return [
    {
      id: "level-root",
      label: "Level objects (LevelObjectBuilder)",
      children: [
        {
          id: "lo-plat",
          label: "platforms.py",
          children: [
            { id: "flat", label: "flat_platform — FlatPlatform" },
            { id: "moving", label: "moving_platform — MovingPlatform" },
            { id: "crumbling", label: "crumbling_platform — CrumblingPlatform" },
          ],
        },
        {
          id: "lo-walls",
          label: "walls.py",
          children: [
            { id: "solid", label: "solid_wall — SolidWall" },
            { id: "cren", label: "crenellated_wall — CrenellatedWall" },
          ],
        },
        {
          id: "lo-traps",
          label: "traps.py",
          children: [
            { id: "spike", label: "spike_trap — SpikeTrap" },
            { id: "fire", label: "fire_trap — FireTrap" },
          ],
        },
        {
          id: "lo-chk",
          label: "checkpoints.py",
          children: [{ id: "cp", label: "checkpoint — Checkpoint" }],
        },
      ],
    },
  ];
}

function baseEnemyFallbackTree(): PartTreeNode[] {
  return [
    {
      id: "fallback",
      label: "Enemy mesh (BaseAnimatedModel pipeline)",
      children: [
        { id: "fb0", label: "parts[0…] — build_mesh_parts() (see concrete animated_*.py)" },
      ],
    },
  ];
}

export function getMeshPartTree(
  cmd: RunCmd,
  enemy: string,
  animatedMeta: readonly AnimatedEnemyMeta[] = DEFAULT_ANIMATED_ENEMY_META,
  /** Current procedural build values for the selected animated enemy (spider eye_count, claw peripheral_eyes, …). */
  buildOptions: Record<string, unknown> = {},
  /** Control defs from GET /api/meta ``animated_build_controls`` (same as Build panel). */
  hints?: MeshPartTreeControlHints,
): PartTreeNode[] {
  const e = (enemy || "").trim();
  const animatedSlugs = animatedMeta.map((m) => m.slug);

  if (cmd === "player") {
    return playerSlimePartTree();
  }

  if (cmd === "level") {
    return levelObjectPartTree();
  }

  if (cmd === "animated" && e === "all") {
    return [
      {
        id: "all-root",
        label: "All animated enemies",
        children: animatedMeta.map((m) => ({
          id: `reg-${m.slug}`,
          label: m.label,
          children: [
            animatedEnemyPartTree(m.slug, {}, hints),
          ],
        })),
      },
    ];
  }

  const knownAnimated = animatedSlugs.includes(e) ? e : "";

  if (cmd === "animated" && e === "spider") {
    return [animatedEnemyPartTree("spider", buildOptions, hints)];
  }

  if (cmd === "animated" && knownAnimated) {
    return [animatedEnemyPartTree(knownAnimated, buildOptions, hints)];
  }

  if (cmd === "animated" && e && !knownAnimated) {
    return baseEnemyFallbackTree();
  }

  return baseEnemyFallbackTree();
}
