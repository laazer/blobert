Lab Escape Slime

A cozy 2.5D experimental platformer about biological mutation, physical experimentation, and elastic game feel.

Tagline:
Experiment. Adapt. Reabsorb. Escape.

Overview

Lab Escape Slime is a horizontal platformer centered around a tactile mutation system. Instead of selecting abilities from menus, the player physically detaches chunks of biomass, infects enemies, and absorbs new biological powers.

The design emphasizes:

- Soft tension over punishment
- Physical interaction over UI systems
- Horizontal flow over open exploration
- Experimentation over mastery

This is a small-scale, personal project focused on building strong game feel and systemic clarity.

Core Pillars

1. Physical Experimentation
Mutations are earned through interaction, not menus. Abilities are acquired by weakening enemies and infecting them with detached biomass chunks. Everything is tactile, animated, and visual.

2. Horizontal Flow
Primarily left-to-right progression. Light vertical segments. Minimal backtracking. Levels target 6–8 minutes. The pacing aims for comfort, not stress.

3. Cozy Combat
Low punishment. Clear enemy states. Encourages playful experimentation. Soft fail states. Combat exists to enable mutation play, not mechanical dominance.

4. Biological Identity
You are a lab-grown slime organism. Squash and stretch convey emotion. Chunks visibly detach from your body. Internal motion suggests living biomass. Damage and mutation physically alter your form. The player character is not a hero — it is an experiment.

Core Mechanics

Base Movement

- Medium-low run speed
- High acceleration
- Elastic charge jump (tap = hop, hold = bounce)
- Moderate air control
- Time-limited wall cling
- No float mechanic

Movement should feel satisfying even in an empty room.

Chunk System (Core Mechanic)

The player can detach up to 2 biomass chunks.

Throw (Lob)

- Forward-lean animation
- Gravity arc
- Small bounce on impact
- Approximately 0.5 second cooldown

While detached:

- Max HP reduced by approximately 20 percent per chunk
- Slightly reduced jump height
- Visible asymmetry in body

Recall (Tendril Absorption)

- Instant input
- Elastic tendril animation
- Stretch and snap motion
- No animation lock

The recall animation is critical to overall game feel.

Enemy States

Enemies have three states:

1. Normal
2. Weakened
3. Infected

Chunks can only infect weakened enemies.

Mutation System

Acquisition Loop

1. Weaken enemy
2. Throw chunk
3. Enemy dissolves
4. Chunk absorbs mutation
5. Recall chunk
6. Mutation fills a slot

Slots

- 2 mutation slots
- Each chunk carries one mutation

Fusion System

Mutations can fuse.

Rules:

- Two chunks must infect the same enemy sequentially
- Enemy destabilizes
- Both chunks are recalled
- Hybrid mutation is created
- Hybrid occupies both slots
- Base mutations are consumed

Fusion is a commitment. Hybrids are situationally powerful, not universally superior.

Initial Mutation Set

Base Mutations

Adhesion Membrane
Extended wall cling. Climb short vertical surfaces.

Acid Gland
Lob corrosive projectile. Melt specific surfaces.

Claw Growth
Short melee slash. Break cracked walls.

Carapace Armor
Damage reduction. Charge attack variant.

Example Hybrids

Adhesion + Acid → Sticky Acid Nodes
Adhesion + Claw → Wall Rip Dash
Adhesion + Carapace → Armored Cling
Acid + Claw → Acid Talons
Acid + Carapace → Explosive Shell
Claw + Carapace → Charging Impale

Level Design Philosophy

Each level includes:

1. Movement introduction
2. Mutation tease
3. Fusion opportunity
4. Light skill check
5. Cooldown segment

Target length: 6–8 minutes.

Initial Scope

- 1 world
- 4–5 levels
- 8–12 mutations
- 1 final boss
- Minimal narrative

This project is intentionally constrained.

Development Plan (Prototype Phase)

Week 1
Movement controller
Chunk detach and recall
Shrink and HP scaling system

Week 2
Enemy with weakened state
First mutation
Full infection loop

Week 3
Four-mutation system
Basic fusion
First prototype level

Tone and Feel

- Semi-cute, not pastel
- Translucent green slime
- Minimal facial features
- Emotion conveyed through squash and stretch
- Lab-industrial atmosphere
- Cozy pacing

Project Philosophy

This is not a large commercial production.

The goals are:

- Explore systemic game design
- Build strong mechanical feel
- Experiment with mutation combinatorics
- Ship something small but complete

Scope discipline over feature creep.