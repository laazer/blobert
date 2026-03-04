extends SceneTree

func _initialize() -> void:
	var total_failures: int = 0
	var s1: GDScript = load("res://tests/test_detach_recall_fx.gd") as GDScript
	var s2: GDScript = load("res://tests/test_detach_recall_fx_adversarial.gd") as GDScript
	if s1 != null:
		total_failures += s1.new().run_all()
	if s2 != null:
		total_failures += s2.new().run_all()
	print("")
	print("DetachRecallFx total failures: " + str(total_failures))
	quit(1 if total_failures > 0 else 0)
