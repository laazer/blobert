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

export type SourceNavTarget = { path: string; description: string };

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

    case "test":
      return {
        path: "enemies/animated_spider.py",
        description: "Test command uses spider mesh (animated_spider.py)",
      };

    case "stats":
      if (e && animatedSlugs.includes(e)) {
        return {
          path: animatedEnemyModulePath(e),
          description: `Mesh builder: ${slugDisplayLabel(e, animatedMeta)} (${e})`,
        };
      }
      return { path: "enemies/base_enemy.py", description: "Base enemy mesh API" };

    case "smart":
    default:
      return null;
  }
}

export function getAnimationCodeTarget(cmd: RunCmd, _enemy: string): SourceNavTarget | null {
  switch (cmd) {
    case "player":
      return { path: "player/player_animations.py", description: "Player animation clips" };
    case "smart":
      return null;
    default:
      return { path: "animations/animation_system.py", description: "Enemy animation system" };
  }
}

/** Short labels for the rest of the Blender animation pipeline (same dir as animation_system). */
export function getAnimationCodeExtras(cmd: RunCmd): SourceNavTarget[] {
  switch (cmd) {
    case "player":
      return [
        { path: "animations/keyframe_system.py", description: "Shared keyframe helpers" },
        { path: "player/player_armature.py", description: "Player armature" },
      ];
    case "smart":
      return [];
    default:
      return [
        { path: "animations/keyframe_system.py", description: "Bone keyframes" },
        { path: "animations/body_types.py", description: "Per-body-type poses & clips" },
        {
          path: "enemies/animated_slug.py",
          description: "Example rig (get_rig_definition) — animated_slug.py",
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

function _coerceSpiderEyeCount(raw: unknown): 2 | 4 {
  return Number(raw) === 4 ? 4 : 2;
}

function _coerceClawPeripheralEyes(raw: unknown): number {
  const n = Math.floor(Number(raw));
  if (Number.isNaN(n)) return 0;
  return Math.max(0, Math.min(3, n));
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
function spiderPartTreeForBuild(eyeCount: 2 | 4): PartTreeNode {
  const children: PartTreeNode[] = [
    { id: "sp-0", label: "parts[0] — body" },
    { id: "sp-1", label: "parts[1] — head" },
  ];
  for (let i = 0; i < eyeCount; i += 1) {
    children.push({ id: `sp-e-${i}`, label: `parts[${2 + i}] — eye` });
  }
  for (let i = 0; i < 6; i += 1) {
    const idx = 2 + eyeCount + i;
    children.push({
      id: `sp-leg-${i}`,
      label: `parts[${idx}] — leg — ${_SPIDER_LEG_NAMES[i]}`,
    });
  }
  const total = 2 + eyeCount + 6;
  return {
    id: "spider-root",
    label: `Spider — parts[] (${total} parts, animated_spider.py)`,
    children,
  };
}

/** `self.parts` for claw crawler — matches `animated_claw_crawler.py` for `peripheral_eyes`. */
function clawCrawlerPartTreeForBuild(peripheralEyes: number): PartTreeNode {
  const pe = _coerceClawPeripheralEyes(peripheralEyes);
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

/** Full `self.parts` order per `animated_{slug}.py` (variant-specific when `buildOptions` is set). */
function animatedEnemyPartTree(slug: string, buildOptions: Record<string, unknown> = {}): PartTreeNode {
  switch (slug) {
    case "spider":
      return spiderPartTreeForBuild(_coerceSpiderEyeCount(buildOptions.eye_count));

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
          { id: "as0", label: "parts[0] — body" },
          { id: "as1", label: "parts[1] — head" },
          { id: "as2", label: "parts[2] — tendril — left" },
          { id: "as3", label: "parts[3] — tendril — right" },
        ],
      };

    case "claw_crawler":
      return clawCrawlerPartTreeForBuild(buildOptions.peripheral_eyes);

    case "carapace_husk":
      return {
        id: "cara-root",
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
        id: `generic-${slug}`,
        label: `${slugDisplayLabel(slug)} — parts[] (animated_${slug}.py)`,
        children: baseEnemyFallbackTree()[0].children,
      };
  }
}

function levelObjectPartTree(): PartTreeNode[] {
  return [
    {
      id: "level-root",
      label: "Level object — type picks class in level_object_builder.py",
      children: [
        {
          id: "lo-platforms",
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
          children: [animatedEnemyPartTree(m.slug, {})],
        })),
      },
    ];
  }

  const knownAnimated = animatedSlugs.includes(e) ? e : "";

  if (cmd === "test" || ((cmd === "animated" || cmd === "stats") && e === "spider")) {
    return [animatedEnemyPartTree("spider", buildOptions)];
  }

  if ((cmd === "animated" || cmd === "stats") && knownAnimated) {
    return [animatedEnemyPartTree(knownAnimated, buildOptions)];
  }

  if (cmd === "animated" && e && !knownAnimated) {
    return baseEnemyFallbackTree();
  }

  return baseEnemyFallbackTree();
}
