# player_state_derivation_context.gd
#
# Input snapshot for PlayerStateMachine.compute_derived_state / sync_from_context.
# Spec: project_board/specs/player_state_machine_spec.md (PSM-7)

class_name PlayerStateDerivationContext
extends RefCounted

## Matches PlayerExportAnimationController3D default (PSM-7).
const DEFAULT_MOVE_SPEED_THRESHOLD: float = 0.12
const DEFAULT_CURRENT_HP: float = 100.0

var is_on_floor: bool = false
var horizontal_speed: float = 0.0
var vertical_velocity: float = 0.0
var move_speed_threshold: float = DEFAULT_MOVE_SPEED_THRESHOLD
var is_wall_clinging: bool = false
var is_any_chunk_stuck: bool = false
var is_mutation_active: bool = false
var current_hp: float = DEFAULT_CURRENT_HP
var min_hp: float = 0.0
var hurt_pending: bool = false
