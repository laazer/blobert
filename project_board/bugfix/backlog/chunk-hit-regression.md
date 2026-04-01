# BUG: Enemies cannot be hit by chunk

## Bug Report

Manual QA checklist `mutation_slot_manual_checklist` (M2/testing) reported checks 3–4 failed with the note: "enemy can not be hit by chunk." Checks 1–2 and 5–7 passed. The chunk throw and recall mechanics appear intact but the chunk no longer triggers the weakening flow on enemy contact.

## Acceptance Criteria

- Throwing the chunk at a NORMAL enemy transitions it to WEAKENED state
- Visual feedback for WEAKENED state activates on contact (enemy color/shader change)
- Chunk collision with enemy registers in the infection state machine (EnemyStateMachine driven transition)
- Chunk can be recalled after hitting an enemy
- All pre-existing passing tests continue to pass (`run_tests.sh` exits 0)

## Reproduction Steps

1. Run `test_movement_3d.tscn` (F6 or `run_tests.sh`)
2. Press chunk detach to throw chunk at any placed enemy
3. Observe: enemy does not enter WEAKENED state; no visual change

## Investigation Starting Points

- `scripts/player/player_controller_3d.gd` — chunk Area3D collision detection
- `scripts/enemy/enemy_infection_3d.gd` — `_on_body_entered` / `_on_area_entered` handlers
- `scripts/enemy/enemy_state_machine.gd` — NORMAL → WEAKENED transition trigger
- Check if recent model swap (`call_deferred("_swap_model_scene")`) changed the Area3D hierarchy, causing chunk detection to miss the target collision layer

## Dependencies

- M2 (Infection Loop) must remain intact after fix
