# slime_visual_state.gd
# Stub for animation/state-driven visual (kit gobot_skin pattern).
# Attach to the player's SlimeVisual (or equivalent). When 3D animations exist:
#   - Subscribe to controller state or signals: grounded, moving, wall_clinging, just_jumped, just_landed.
#   - State machine: Idle, Run, Jump, Fall, WallCling.
#   - One-shots: detach, recall, hurt (AnimationTree.set(one_shot_path, true)).
# For now this script is a no-op; juice (scale tweens) is handled in player_controller_3d.

extends Node3D

func _ready() -> void:
	pass

func _process(_delta: float) -> void:
	# When AnimationTree exists: drive state from get_parent() (PlayerController3D) state.
	# e.g. if parent.has_method("is_wall_clinging_state") and parent.is_wall_clinging_state(): play("WallCling")
	pass
