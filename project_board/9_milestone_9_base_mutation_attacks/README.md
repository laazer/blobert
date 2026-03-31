# Epic: Milestone 9 – Base Mutation Attacks

**Goal:** Each of the 4 base mutations gives Blobert a usable offensive move.

## Scope

- One distinct attack per base mutation:
  - Adhesion — sticky projectile or lunge that briefly immobilises
  - Acid — ranged acid spit that applies a damage-over-time debuff
  - Claw — fast melee swipe with short cooldown
  - Carapace — slow heavy slam or charge with knockback
- Input binding for attack action (separate from absorb/infect)
- Per-mutation cooldown system
- Attacks interact with enemy state machine (e.g. claw can weaken, acid can infect)
- Visual + audio feedback on attack (minimal — functional first)

## Dependencies

- M2 (Infection Loop) — mutation slot system already in place
- M3 (Dual Mutation + Fusion) — mutation identity per slot established

## Exit Criteria

Player has 4 distinct offensive tools. Each mutation attack feels different from the others and has at least one meaningful interaction with the enemy infection loop.

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Playable, tested, merged
