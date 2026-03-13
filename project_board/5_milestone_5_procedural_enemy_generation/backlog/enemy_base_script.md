Title:
Implement enemy_base.gd shared script

Description:
Create scripts/enemies/enemy_base.gd that all generated enemies share.
Should expose enemy_id, enemy_family, mutation_drop as @export vars and provide
stub hooks for state transitions (normal, weakened, infected).

Acceptance Criteria:
- Script attaches cleanly to CharacterBody3D generated scenes
- Exports: enemy_id, enemy_family, mutation_drop (String)
- State enum: NORMAL, WEAKENED, INFECTED
- Existing enemy state machine can drive state transitions via this script
- No regressions to existing enemy tests
