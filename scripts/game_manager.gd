# game_manager.gd
# Optional autoload: global score/state for UI (kit pattern).
# UI can bind to GameManager.score; collectibles call add_score().

extends Node

var score: int = 0

func add_score() -> void:
	score += 1
