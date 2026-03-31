# Epic: Milestone 8 – Enemy Attacks

**Goal:** Enemies deal damage and telegraph intent — you can die to an enemy.

## Scope

- Attack patterns per family (adhesion: slow lunge, acid: ranged spit, claw: fast swipe, carapace: charge)
- Hitbox activation tied to attack animation (depends on M7 animation wiring)
- Player takes damage on hit
- Basic telegraphing: wind-up animation or visual indicator before attack lands
- Attack cooldowns and aggro range (enemy only attacks when player is close)
- Damage does not break the infection loop (weakened/infected enemies still absorbable)

## Dependencies

- M7 (Enemy Animation Wiring) — attack animations must exist before hitboxes can be timed to them

## Asset Generation Dependency

Attack animations (wind-up, strike, recovery) per family will need to be added to the Blender export pipeline if not already present.

## Exit Criteria

Each of the 4 families has a distinct attack. The player can die. Attacks are readable — you can see them coming.

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Playable, tested, merged
