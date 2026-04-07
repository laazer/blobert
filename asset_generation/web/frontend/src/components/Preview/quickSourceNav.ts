import { RunCmd } from "../../types";

/** Default slugs when /api/meta/enemies has not loaded yet. */
export const DEFAULT_ANIMATED_ENEMY_SLUGS = [
  "adhesion_bug",
  "tar_slug",
  "ember_imp",
  "acid_spitter",
  "claw_crawler",
  "carapace_husk",
] as const;

/** @deprecated use DEFAULT_ANIMATED_ENEMY_SLUGS or store `animatedEnemySlugs` */
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
  animatedSlugs: readonly string[] = DEFAULT_ANIMATED_ENEMY_SLUGS,
): SourceNavTarget | null {
  const e = (enemy || "").trim();

  switch (cmd) {
    case "animated":
      if (e === "all") {
        return { path: "enemies/animated/registry.py", description: "Animated enemy registry" };
      }
      if (animatedSlugs.includes(e)) {
        return { path: animatedEnemyModulePath(e), description: `Mesh builder: ${e}` };
      }
      return { path: "enemies/base_enemy.py", description: "Base enemy mesh API" };

    case "player":
      return { path: "player/player_slime_body.py", description: "Player slime mesh geometry" };

    case "level":
      return { path: "level/level_object_builder.py", description: "Level object mesh builder" };

    case "test":
      return { path: "enemies/animated_adhesion_bug.py", description: "Test command uses adhesion bug" };

    case "stats":
      if (e && animatedSlugs.includes(e)) {
        return { path: animatedEnemyModulePath(e), description: `Mesh builder: ${e}` };
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
        { path: "enemies/animated_tar_slug.py", description: "Enemy-specific rig (get_rig_definition)" },
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

/** Full `self.parts` order per `animated_{slug}.py`. */
function animatedEnemyPartTree(slug: string): PartTreeNode {
  switch (slug) {
    case "adhesion_bug":
      return {
        id: "adhesion-root",
        label: "Adhesion bug — parts[] (animated_adhesion_bug.py)",
        children: [
          {
            id: "adhesion-2eye",
            label: "Variant: 2 eyes (10 parts)",
            children: [
              { id: "ab2-0", label: "parts[0] — body" },
              { id: "ab2-1", label: "parts[1] — head" },
              { id: "ab2-2", label: "parts[2] — eye" },
              { id: "ab2-3", label: "parts[3] — eye" },
              { id: "ab2-4", label: "parts[4] — leg — front left" },
              { id: "ab2-5", label: "parts[5] — leg — front right" },
              { id: "ab2-6", label: "parts[6] — leg — middle left" },
              { id: "ab2-7", label: "parts[7] — leg — middle right" },
              { id: "ab2-8", label: "parts[8] — leg — back left" },
              { id: "ab2-9", label: "parts[9] — leg — back right" },
            ],
          },
          {
            id: "adhesion-4eye",
            label: "Variant: 4 eyes (12 parts)",
            children: [
              { id: "ab4-0", label: "parts[0] — body" },
              { id: "ab4-1", label: "parts[1] — head" },
              { id: "ab4-2", label: "parts[2] — eye" },
              { id: "ab4-3", label: "parts[3] — eye" },
              { id: "ab4-4", label: "parts[4] — eye" },
              { id: "ab4-5", label: "parts[5] — eye" },
              { id: "ab4-6", label: "parts[6] — leg — front left" },
              { id: "ab4-7", label: "parts[7] — leg — front right" },
              { id: "ab4-8", label: "parts[8] — leg — middle left" },
              { id: "ab4-9", label: "parts[9] — leg — middle right" },
              { id: "ab4-10", label: "parts[10] — leg — back left" },
              { id: "ab4-11", label: "parts[11] — leg — back right" },
            ],
          },
        ],
      };

    case "tar_slug":
      return {
        id: "tar-slug-root",
        label: "Tar slug — parts[] (animated_tar_slug.py)",
        children: [
          { id: "ts0", label: "parts[0] — body" },
          { id: "ts1", label: "parts[1] — head bump" },
          { id: "ts2", label: "parts[2] — eye stalk — left" },
          { id: "ts3", label: "parts[3] — eye — left" },
          { id: "ts4", label: "parts[4] — eye stalk — right" },
          { id: "ts5", label: "parts[5] — eye — right" },
        ],
      };

    case "ember_imp":
      return {
        id: "ember-imp-root",
        label: "Ember imp — parts[] (animated_ember_imp.py)",
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

    case "acid_spitter":
      return {
        id: "acid-root",
        label: "Acid spitter — parts[] (animated_acid_spitter.py)",
        children: [
          { id: "as0", label: "parts[0] — body" },
          { id: "as1", label: "parts[1] — head" },
          { id: "as2", label: "parts[2] — tendril — left" },
          { id: "as3", label: "parts[3] — tendril — right" },
        ],
      };

    case "claw_crawler":
      return {
        id: "claw-root",
        label: "Claw crawler — parts[] (animated_claw_crawler.py)",
        children: [
          { id: "cc0", label: "parts[0] — body" },
          { id: "cc1", label: "parts[1] — head" },
          { id: "cc2", label: "parts[2] — front claw — left" },
          { id: "cc3", label: "parts[3] — front claw — right" },
          { id: "cc4", label: "parts[4] — leg — middle left" },
          { id: "cc5", label: "parts[5] — leg — middle right" },
          { id: "cc6", label: "parts[6] — leg — back left" },
          { id: "cc7", label: "parts[7] — leg — back right" },
        ],
      };

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
        label: `Enemy ${slug} — parts[] (animated_${slug}.py)`,
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
  animatedSlugs: readonly string[] = DEFAULT_ANIMATED_ENEMY_SLUGS,
): PartTreeNode[] {
  const e = (enemy || "").trim();

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
        children: animatedSlugs.map((slug) => ({
          id: `reg-${slug}`,
          label: slug,
          children: [animatedEnemyPartTree(slug)],
        })),
      },
    ];
  }

  const knownAnimated = animatedSlugs.includes(e) ? e : "";

  if (cmd === "test" || ((cmd === "animated" || cmd === "stats") && e === "adhesion_bug")) {
    return [animatedEnemyPartTree("adhesion_bug")];
  }

  if ((cmd === "animated" || cmd === "stats") && knownAnimated) {
    return [animatedEnemyPartTree(knownAnimated)];
  }

  if (cmd === "animated" && e && !knownAnimated) {
    return baseEnemyFallbackTree();
  }

  return baseEnemyFallbackTree();
}
