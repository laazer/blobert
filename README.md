# Lab Escape Slime

> **Experiment. Adapt. Reabsorb. Escape.**

A cozy 2.5D experimental platformer about biological mutation, physical experimentation, and elastic game feel.

---

## Development target: 3D scenes

**We develop for 3D.** The project uses a single 3D world with 2D-like gameplay (movement constrained to a plane, side-view camera). The default run scene is **`scenes/test_movement_3d.tscn`**; the playable character is **`PlayerController3D`** (`scripts/player/player_controller_3d.gd`) with scene **`scenes/player/player_3d.tscn`**. New features, levels, and mechanics should target 3D nodes (CharacterBody3D, Camera3D, Area3D, etc.). The shared movement logic lives in **`scripts/movement/movement_simulation.gd`** (pure 2D math); the 3D controller maps its output to Vector3 and drives the 3D scene. Legacy 2D scenes (`test_movement.tscn`, `player.tscn`) remain for existing headless tests only.

---

## Built with AI Agents

Most of this project is developed **solely with AI agents** (Claude in Cursor): planning, specs, tests, and implementation are driven through a multi-agent TDD pipeline. Human input steers scope and review; agents own the bulk of the code and test authorship. If that kind of workflow interests you, the repo is a working example.

---

## Overview

**Lab Escape Slime** is a horizontal platformer centered around a tactile mutation system. Instead of selecting abilities from menus, the player physically detaches chunks of biomass, infects enemies, and absorbs new biological powers.

The design emphasizes:

- **Soft tension** over punishment
- **Physical interaction** over UI systems
- **Horizontal flow** over open exploration
- **Experimentation** over mastery

This is a small-scale, personal project focused on building strong game feel and systemic clarity.

---

## Core Pillars

### 1. Physical Experimentation

Mutations are earned through interaction, not menus. Abilities are acquired by weakening enemies and infecting them with detached biomass chunks. Everything is tactile, animated, and visual.

### 2. Horizontal Flow

Primarily left-to-right progression. Light vertical segments. Minimal backtracking. Levels target 6–8 minutes. The pacing aims for comfort, not stress.

### 3. Cozy Combat

Low punishment. Clear enemy states. Encourages playful experimentation. Soft fail states. Combat exists to enable mutation play, not mechanical dominance.

### 4. Biological Identity

You are a lab-grown slime organism. Squash and stretch convey emotion. Chunks visibly detach from your body. Internal motion suggests living biomass. Damage and mutation physically alter your form. The player character is not a hero — it is an experiment.

---

## Core Mechanics

### Base Movement

- Medium-low run speed
- High acceleration
- Elastic charge jump (tap = hop, hold = bounce)
- Moderate air control
- Time-limited wall cling
- No float mechanic

Movement should feel satisfying even in an empty room.

### Chunk System (Core Mechanic)

The player can detach up to 2 biomass chunks.

**Throw (Lob)**

- Forward-lean animation
- Gravity arc
- Small bounce on impact
- Approximately 0.5 second cooldown

**While detached**

- Max HP reduced by approximately 20 percent per chunk
- Slightly reduced jump height
- Visible asymmetry in body

**Recall (Tendril Absorption)**

- Instant input
- Elastic tendril animation
- Stretch and snap motion
- No animation lock

The recall animation is critical to overall game feel.

### Enemy States

Enemies have three states:

1. **Normal**
2. **Weakened**
3. **Infected**

Chunks can only infect weakened enemies.

### Mutation System

**Acquisition loop**

1. Weaken enemy
2. Throw chunk
3. Enemy dissolves
4. Chunk absorbs mutation
5. Recall chunk
6. Mutation fills a slot

**Slots**

- 2 mutation slots
- Each chunk carries one mutation

### Fusion System

Mutations can fuse.

**Rules**

- Two chunks must infect the same enemy sequentially
- Enemy destabilizes
- Both chunks are recalled
- Hybrid mutation is created
- Hybrid occupies both slots
- Base mutations are consumed

Fusion is a commitment. Hybrids are situationally powerful, not universally superior.

---

## Initial Mutation Set

### Base Mutations

| Mutation          | Effect                                              |
|-------------------|-----------------------------------------------------|
| **Adhesion Membrane** | Extended wall cling. Climb short vertical surfaces. |
| **Acid Gland**        | Lob corrosive projectile. Melt specific surfaces.   |
| **Claw Growth**       | Short melee slash. Break cracked walls.             |
| **Carapace Armor**    | Damage reduction. Charge attack variant.            |

### Example Hybrids

- Adhesion + Acid → Sticky Acid Nodes
- Adhesion + Claw → Wall Rip Dash
- Adhesion + Carapace → Armored Cling
- Acid + Claw → Acid Talons
- Acid + Carapace → Explosive Shell
- Claw + Carapace → Charging Impale

---

## Level Design Philosophy

Each level includes:

1. Movement introduction
2. Mutation tease
3. Fusion opportunity
4. Light skill check
5. Cooldown segment

**Target length:** 6–8 minutes.

---

## Initial Scope

- 1 world
- 4–5 levels
- 8–12 mutations
- 1 final boss
- Minimal narrative

This project is intentionally constrained.

---

## Development Plan (Prototype Phase)

- **Week 1:** Movement controller, chunk detach/recall, shrink and HP scaling system
- **Week 2:** Enemy with weakened state, first mutation, full infection loop
- **Week 3:** Four-mutation system, basic fusion, first prototype level

---

## Tone and Feel

- Semi-cute, not pastel
- Translucent green slime
- Minimal facial features
- Emotion conveyed through squash and stretch
- Lab-industrial atmosphere
- Cozy pacing

---

## Project Philosophy

This is not a large commercial production.

The goals are:

- Explore systemic game design
- Build strong mechanical feel
- Experiment with mutation combinatorics
- Ship something small but complete

**Scope discipline over feature creep.**

---

## Running the Project

Requires [Godot 4.x](https://godotengine.org/).

```bash
# Open in Godot Editor (recommended)
godot project.godot

# Or run headlessly
godot --headless
```

See `CLAUDE.md` for CLI commands (syntax check, export, etc.) used during development.

## Testing

This project uses a custom headless test runner for automated testing. Tests are written in GDScript and run without a GUI for CI compatibility.

```bash
# Run all tests (recommended - includes timeout to prevent hanging)
./ci/scripts/run_tests.sh

# Or run manually (with 5-minute timeout)
timeout 300 godot --headless -s tests/run_tests.gd
```

Tests are organized in `tests/` with suites for movement, combat, UI, and integration scenarios. The runner exits with code 0 on success or 1 on failure, making it suitable for CI pipelines.

For development, direnv is configured to make `run_tests.sh` accessible from any directory in the repo.
