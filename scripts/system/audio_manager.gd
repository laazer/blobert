# audio_manager.gd
# Autoload: SFX for jump, detach, recall (and optional footsteps).
# Same pattern as 3D-Platformer-Kit; blobert uses slime/jump/detach/recall.
# Note: Do not use class_name here — it conflicts with the autoload singleton name.

extends Node

@onready var jump_sfx: AudioStreamPlayer = $JumpSfx
@onready var detach_sfx: AudioStreamPlayer = $DetachSfx
@onready var recall_sfx: AudioStreamPlayer = $RecallSfx

func _ready() -> void:
	# Optional: ensure nodes exist for headless tests
	pass
