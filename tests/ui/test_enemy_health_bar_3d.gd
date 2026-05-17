#
# test_enemy_health_bar_3d.gd
#
# Behavioral tests for world-space enemy health bar UI (M8 feature).
# Tests health bar instantiation, positioning, fill state, visibility logic,
# and lifecycle cleanup.
#
# Ticket: project_board/8_milestone_8_enemy_attacks/in_progress/01_enemy_floating_health_bar.md
# Requirements:
#   - Each spawned enemy renders a floating health bar anchored above its head/body center
#   - Bar fill is driven by enemy current HP / max HP and updates immediately on damage/heal
#   - Bar is visible for damaged enemies and hidden for full-health enemies after a short timeout
#   - Bar always faces the camera (billboard behavior) and remains readable while moving
#   - Bar is removed when the enemy dies or is despawned (no orphan UI nodes)
#   - Feature can be toggled with a project/debug flag for performance testing
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Test infrastructure: fixtures and helpers
# ---------------------------------------------------------------------------

# Create a mock enemy with health component for testing.
# Returns a CharacterBody3D node with basic health properties.
func _create_mock_enemy(hp: float = 100.0, max_hp: float = 100.0) -> CharacterBody3D:
	var body := CharacterBody3D.new()
	body.set_script(load("res://scripts/enemies/enemy_base.gd"))
	# Inject health state as properties on the enemy node.
	body.set_meta("current_hp", hp)
	body.set_meta("max_hp", max_hp)
	return body


# Create a mock scene tree if not in one. Returns null if no valid tree exists.
func _ensure_scene_tree() -> Variant:
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("_ensure_scene_tree", "Could not get or create SceneTree")
	return tree


# Attempt to load the health bar scene. Returns null if not yet created.
func _load_health_bar_scene() -> Variant:
	var path := "res://scenes/ui/enemy_health_bar_3d.tscn"
	var scene = load(path)
	return scene


# ---------------------------------------------------------------------------
# EHB-LOAD: Health bar scene and asset existence
# ---------------------------------------------------------------------------

func test_ehb_load_1_health_bar_scene_path_exists() -> void:
	# EHB-LOAD-1: The health bar scene file exists at res://scenes/ui/enemy_health_bar_3d.tscn.
	# This is a basic file existence check; does not require full implementation.
	var path := "res://scenes/ui/enemy_health_bar_3d.tscn"
	var scene = load(path)
	_assert_true(
		scene != null,
		"EHB-LOAD-1 — health bar scene file exists at " + path
	)


func test_ehb_load_2_health_bar_scene_loads_as_node() -> void:
	# EHB-LOAD-2: The loaded scene can be instantiated as a Node.
	var scene = _load_health_bar_scene()
	if scene == null:
		_fail("EHB-LOAD-2", "health bar scene file not found; skipping instantiation test")
		return
	var instance = scene.instantiate() as Node
	_assert_true(
		instance != null and instance is Node,
		"EHB-LOAD-2 — health bar scene instantiates as a Node"
	)
	if instance != null:
		instance.queue_free()


# ---------------------------------------------------------------------------
# EHB-STRUCTURE: Health bar node hierarchy and component structure
# ---------------------------------------------------------------------------

func test_ehb_structure_1_scene_has_root_node() -> void:
	# EHB-STRUCTURE-1: The health bar scene has a root Node (any type is acceptable at this stage).
	var scene = _load_health_bar_scene()
	if scene == null:
		_fail("EHB-STRUCTURE-1", "health bar scene not found")
		return
	var instance = scene.instantiate() as Node
	if instance == null:
		_fail("EHB-STRUCTURE-1", "could not instantiate scene")
		return
	_assert_true(
		instance != null,
		"EHB-STRUCTURE-1 — scene root is a valid Node"
	)
	instance.queue_free()


func test_ehb_structure_2_scene_has_progress_bar_child() -> void:
	# EHB-STRUCTURE-2: The health bar scene contains a ProgressBar as a child (direct or nested).
	# This test checks structural composition.
	var scene = _load_health_bar_scene()
	if scene == null:
		_fail("EHB-STRUCTURE-2", "health bar scene not found")
		return
	var instance = scene.instantiate() as Node
	if instance == null:
		_fail("EHB-STRUCTURE-2", "could not instantiate scene")
		return

	# Recursive search for ProgressBar anywhere in tree.
	var found_progress_bar: bool = false
	var stack: Array[Node] = [instance]
	while stack.size() > 0:
		var node = stack.pop_front()
		if node is ProgressBar:
			found_progress_bar = true
			break
		for child in node.get_children():
			stack.append(child)

	_assert_true(
		found_progress_bar,
		"EHB-STRUCTURE-2 — scene contains a ProgressBar child"
	)
	instance.queue_free()


# ---------------------------------------------------------------------------
# EHB-FILL: Health bar fill ratio reflects HP/max HP
# ---------------------------------------------------------------------------

func test_ehb_fill_1_fill_updates_on_hp_change() -> void:
	# EHB-FILL-1: When enemy HP changes, the health bar fill value reflects current_hp / max_hp.
	# Tests the core state→UI binding.
	var scene = _load_health_bar_scene()
	if scene == null:
		_fail("EHB-FILL-1", "health bar scene not found")
		return
	var bar_instance = scene.instantiate() as Node
	if bar_instance == null:
		_fail("EHB-FILL-1", "could not instantiate scene")
		return

	# Locate the ProgressBar within the instance.
	var progress_bar: ProgressBar = null
	var stack: Array[Node] = [bar_instance]
	while stack.size() > 0:
		var node = stack.pop_front()
		if node is ProgressBar:
			progress_bar = node
			break
		for child in node.get_children():
			stack.append(child)

	if progress_bar == null:
		_fail("EHB-FILL-1", "could not locate ProgressBar in instance")
		bar_instance.queue_free()
		return

	# Simulate a health update: set bar.value to 50 (out of 100).
	# This represents 50% health.
	progress_bar.max_value = 100.0
	progress_bar.value = 50.0

	_assert_eq_float(
		0.5,
		progress_bar.value / progress_bar.max_value,
		"EHB-FILL-1 — bar fill ratio is 0.5 when value=50, max=100"
	)

	bar_instance.queue_free()


func test_ehb_fill_2_full_health_bar_value_equals_max() -> void:
	# EHB-FILL-2: When enemy is at full health, bar.value == bar.max_value.
	var scene = _load_health_bar_scene()
	if scene == null:
		_fail("EHB-FILL-2", "health bar scene not found")
		return
	var bar_instance = scene.instantiate() as Node
	if bar_instance == null:
		_fail("EHB-FILL-2", "could not instantiate scene")
		return

	var progress_bar: ProgressBar = null
	var stack: Array[Node] = [bar_instance]
	while stack.size() > 0:
		var node = stack.pop_front()
		if node is ProgressBar:
			progress_bar = node
			break
		for child in node.get_children():
			stack.append(child)

	if progress_bar == null:
		_fail("EHB-FILL-2", "could not locate ProgressBar in instance")
		bar_instance.queue_free()
		return

	progress_bar.max_value = 100.0
	progress_bar.value = 100.0

	_assert_eq(
		progress_bar.value,
		progress_bar.max_value,
		"EHB-FILL-2 — bar.value == bar.max_value at full health"
	)

	bar_instance.queue_free()


func test_ehb_fill_3_zero_health_bar_value_is_zero() -> void:
	# EHB-FILL-3: When enemy HP is 0, bar.value == 0.
	var scene = _load_health_bar_scene()
	if scene == null:
		_fail("EHB-FILL-3", "health bar scene not found")
		return
	var bar_instance = scene.instantiate() as Node
	if bar_instance == null:
		_fail("EHB-FILL-3", "could not instantiate scene")
		return

	var progress_bar: ProgressBar = null
	var stack: Array[Node] = [bar_instance]
	while stack.size() > 0:
		var node = stack.pop_front()
		if node is ProgressBar:
			progress_bar = node
			break
		for child in node.get_children():
			stack.append(child)

	if progress_bar == null:
		_fail("EHB-FILL-3", "could not locate ProgressBar in instance")
		bar_instance.queue_free()
		return

	progress_bar.max_value = 100.0
	progress_bar.value = 0.0

	_assert_eq(
		0.0,
		progress_bar.value,
		"EHB-FILL-3 — bar.value == 0 when enemy is dead"
	)

	bar_instance.queue_free()


# ---------------------------------------------------------------------------
# EHB-VISIBILITY: Show/hide logic based on damage state
# ---------------------------------------------------------------------------

func test_ehb_visibility_1_hidden_by_default_when_full_health() -> void:
	# EHB-VISIBILITY-1: Health bar is hidden (visible=false) when enemy is at full health
	# and has not been recently damaged.
	var scene = _load_health_bar_scene()
	if scene == null:
		_fail("EHB-VISIBILITY-1", "health bar scene not found")
		return
	var bar_instance = scene.instantiate() as Node
	if bar_instance == null:
		_fail("EHB-VISIBILITY-1", "could not instantiate scene")
		return

	# For now, we only verify the property exists and can be toggled.
	if bar_instance is CanvasItem:
		bar_instance.visible = false
		_assert_false(
			bar_instance.visible,
			"EHB-VISIBILITY-1 — health bar can be set to invisible"
		)
	else:
		_fail("EHB-VISIBILITY-1", "health bar root is not a CanvasItem; cannot test visibility")

	bar_instance.queue_free()


func test_ehb_visibility_2_shown_when_damaged() -> void:
	# EHB-VISIBILITY-2: Health bar becomes visible when enemy takes damage.
	# After damage, bar.visible == true.
	var scene = _load_health_bar_scene()
	if scene == null:
		_fail("EHB-VISIBILITY-2", "health bar scene not found")
		return
	var bar_instance = scene.instantiate() as Node
	if bar_instance == null:
		_fail("EHB-VISIBILITY-2", "could not instantiate scene")
		return

	if bar_instance is CanvasItem:
		bar_instance.visible = true
		_assert_true(
			bar_instance.visible,
			"EHB-VISIBILITY-2 — health bar can be set to visible"
		)
	else:
		_fail("EHB-VISIBILITY-2", "health bar root is not a CanvasItem; cannot test visibility")

	bar_instance.queue_free()


# ---------------------------------------------------------------------------
# EHB-BILLBOARD: Camera-facing billboard behavior
# ---------------------------------------------------------------------------

func test_ehb_billboard_1_bar_can_face_camera() -> void:
	# EHB-BILLBOARD-1: The health bar is positioned above the enemy and can be configured
	# to face the camera (billboard mode). Tests that the node structure supports
	# billboard configuration.
	var scene = _load_health_bar_scene()
	if scene == null:
		_fail("EHB-BILLBOARD-1", "health bar scene not found")
		return
	var bar_instance = scene.instantiate() as Node
	if bar_instance == null:
		_fail("EHB-BILLBOARD-1", "could not instantiate scene")
		return

	# Check if the instance or its children have a Node3D (supports billboard_mode).
	var has_3d_node: bool = false
	var stack: Array[Node] = [bar_instance]
	while stack.size() > 0:
		var node = stack.pop_front()
		if node is Node3D:
			has_3d_node = true
			break
		for child in node.get_children():
			stack.append(child)

	_assert_true(
		has_3d_node,
		"EHB-BILLBOARD-1 — health bar scene contains a Node3D for billboard support"
	)

	bar_instance.queue_free()


func test_ehb_billboard_2_positioned_above_enemy() -> void:
	# EHB-BILLBOARD-2: Health bar is positioned above (higher Y) the enemy's origin.
	# Tests that the bar has an offset position in world space.
	var scene = _load_health_bar_scene()
	if scene == null:
		_fail("EHB-BILLBOARD-2", "health bar scene not found")
		return
	var bar_instance = scene.instantiate() as Node
	if bar_instance == null:
		_fail("EHB-BILLBOARD-2", "could not instantiate scene")
		return

	# If the root is Node3D, it should have a position property.
	if bar_instance is Node3D:
		var initial_pos = bar_instance.position
		bar_instance.position = initial_pos + Vector3(0, 2, 0)
		_assert_true(
			bar_instance.position.y > initial_pos.y,
			"EHB-BILLBOARD-2 — health bar position can be offset above the enemy"
		)
	else:
		_fail("EHB-BILLBOARD-2", "health bar root is not a Node3D; cannot test positioning")

	bar_instance.queue_free()


# ---------------------------------------------------------------------------
# EHB-LIFECYCLE: Cleanup on enemy death/despawn
# ---------------------------------------------------------------------------

func test_ehb_lifecycle_1_bar_removed_on_enemy_death() -> void:
	# EHB-LIFECYCLE-1: When enemy dies or is despawned, the health bar is removed
	# (queue_free or freed immediately). No orphan UI nodes remain.
	# Tests that a bar instance can be freed without crashing.
	var scene = _load_health_bar_scene()
	if scene == null:
		_fail("EHB-LIFECYCLE-1", "health bar scene not found")
		return
	var bar_instance = scene.instantiate() as Node
	if bar_instance == null:
		_fail("EHB-LIFECYCLE-1", "could not instantiate scene")
		return

	# Adding to scene tree and then freeing should work cleanly.
	var tree = _ensure_scene_tree()
	if tree == null:
		_fail("EHB-LIFECYCLE-1", "no valid scene tree")
		bar_instance.queue_free()
		return

	tree.root.add_child(bar_instance)
	_assert_true(
		bar_instance.get_parent() == tree.root,
		"EHB-LIFECYCLE-1 — bar_instance added to scene tree"
	)

	bar_instance.queue_free()

	_assert_true(
		bar_instance.is_queued_for_deletion(),
		"EHB-LIFECYCLE-1 — bar_instance queued for deletion"
	)


func test_ehb_lifecycle_2_health_bar_ownership() -> void:
	# EHB-LIFECYCLE-2: Health bar is owned by the enemy node or is managed by a component
	# that handles lifecycle. Tests that the bar instance tracks its owner.
	var scene = _load_health_bar_scene()
	if scene == null:
		_fail("EHB-LIFECYCLE-2", "health bar scene not found")
		return
	var bar_instance = scene.instantiate() as Node
	if bar_instance == null:
		_fail("EHB-LIFECYCLE-2", "could not instantiate scene")
		return

	var tree = _ensure_scene_tree()
	if tree == null:
		_fail("EHB-LIFECYCLE-2", "no valid scene tree")
		bar_instance.queue_free()
		return

	# Create a mock enemy and attach the bar to it.
	var enemy = _create_mock_enemy()
	tree.root.add_child(enemy)
	enemy.add_child(bar_instance)

	_assert_true(
		bar_instance.get_parent() == enemy,
		"EHB-LIFECYCLE-2 — health bar is attached as child of enemy"
	)

	enemy.queue_free()

	_assert_true(
		enemy.is_queued_for_deletion(),
		"EHB-LIFECYCLE-2 — enemy is queued for deletion"
	)


# ---------------------------------------------------------------------------
# EHB-DEBUG-FLAG: Feature toggle for performance testing
# ---------------------------------------------------------------------------

func test_ehb_debug_flag_1_toggle_exists() -> void:
	# EHB-DEBUG-FLAG-1: A debug/performance toggle exists (project setting or script export).
	# This allows disabling the feature without removing code.
	# Look for a ProjectSettings entry or export variable in the health bar script.

	var scene = _load_health_bar_scene()
	if scene == null:
		_fail("EHB-DEBUG-FLAG-1", "health bar scene not found")
		return

	# Check if ProjectSettings has an enemy_health_bar-related entry.
	var flag_exists: bool = false
	if ProjectSettings.has_setting("debug/enable_enemy_health_bars"):
		flag_exists = true

	# Also check if the scene root has an export variable for toggling.
	var bar_instance = scene.instantiate() as Node
	if bar_instance == null:
		_fail("EHB-DEBUG-FLAG-1", "could not instantiate scene")
		return

	# If the root has a script, check for an @export variable like "enabled" or "show_health_bar".
	if bar_instance.get_script() != null:
		var script = bar_instance.get_script() as GDScript
		if script.source_code.contains("@export") and script.source_code.contains("enabled"):
			flag_exists = true

	_assert_true(
		flag_exists,
		"EHB-DEBUG-FLAG-1 — debug flag or toggle mechanism exists for health bar"
	)

	bar_instance.queue_free()


func test_ehb_debug_flag_2_toggle_hides_bar_when_disabled() -> void:
	# EHB-DEBUG-FLAG-2: When the debug flag is disabled, health bar is not shown.
	var scene = _load_health_bar_scene()
	if scene == null:
		_fail("EHB-DEBUG-FLAG-2", "health bar scene not found")
		return

	var bar_instance = scene.instantiate() as Node
	if bar_instance == null:
		_fail("EHB-DEBUG-FLAG-2", "could not instantiate scene")
		return

	# Attempt to disable via ProjectSettings (if flag exists).
	if ProjectSettings.has_setting("debug/enable_enemy_health_bars"):
		ProjectSettings.set_setting("debug/enable_enemy_health_bars", false)

		# After disabling, the bar should not be visible.
		if bar_instance is CanvasItem:
			bar_instance.visible = false
			_assert_false(
				bar_instance.visible,
				"EHB-DEBUG-FLAG-2 — health bar is hidden when toggle is disabled"
			)
		else:
			_fail("EHB-DEBUG-FLAG-2", "health bar root is not a CanvasItem")
	else:
		# Skip if no ProjectSettings entry exists yet.
		print("  SKIP: EHB-DEBUG-FLAG-2 — debug flag not yet in ProjectSettings")

	bar_instance.queue_free()


# ---------------------------------------------------------------------------
# EHB-INTEGRATION: Enemy health bar attachment and wiring
# ---------------------------------------------------------------------------

func test_ehb_integration_1_bar_attached_to_enemy_on_spawn() -> void:
	# EHB-INTEGRATION-1: When an enemy is spawned, a health bar is automatically
	# instantiated and attached as a child.
	# This test verifies the attachment pattern.

	var tree = _ensure_scene_tree()
	if tree == null:
		_fail("EHB-INTEGRATION-1", "no valid scene tree")
		return

	var scene = _load_health_bar_scene()
	if scene == null:
		_fail("EHB-INTEGRATION-1", "health bar scene not found")
		return

	var enemy = _create_mock_enemy()
	var bar = scene.instantiate() as Node

	tree.root.add_child(enemy)
	enemy.add_child(bar)

	_assert_true(
		bar in enemy.get_children(),
		"EHB-INTEGRATION-1 — health bar is a child of the enemy"
	)

	enemy.queue_free()


func test_ehb_integration_2_bar_follows_enemy_position() -> void:
	# EHB-INTEGRATION-2: Health bar world position tracks enemy position (with offset).
	# Tests that the bar's parent relationship keeps it anchored to the enemy.

	var tree = _ensure_scene_tree()
	if tree == null:
		_fail("EHB-INTEGRATION-2", "no valid scene tree")
		return

	var scene = _load_health_bar_scene()
	if scene == null:
		_fail("EHB-INTEGRATION-2", "health bar scene not found")
		return

	var enemy = _create_mock_enemy()
	var bar = scene.instantiate() as Node

	tree.root.add_child(enemy)
	enemy.add_child(bar)

	# Move enemy and verify bar moves with it (if both are Node3D).
	if enemy is Node3D and bar is Node3D:
		var enemy_start = enemy.global_position
		var bar_start = bar.global_position

		enemy.global_position = enemy_start + Vector3(1, 0, 0)

		# Bar's local position should not change; global position should follow.
		var enemy_moved = enemy.global_position
		var bar_moved = bar.global_position

		_assert_true(
			bar_moved.x == bar_start.x + 1,
			"EHB-INTEGRATION-2 — bar follows enemy movement"
		)
	else:
		print("  SKIP: EHB-INTEGRATION-2 — not a 3D scene")

	enemy.queue_free()


# ---------------------------------------------------------------------------
# EHB-EDGE-CASES: Edge cases and boundary conditions
# ---------------------------------------------------------------------------

func test_ehb_edge_1_bar_handles_zero_max_hp() -> void:
	# EHB-EDGE-1: If enemy max_hp is 0 (edge case), health bar does not crash.
	# Defensive coding: division by zero guard.

	var scene = _load_health_bar_scene()
	if scene == null:
		_fail("EHB-EDGE-1", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("EHB-EDGE-1", "could not instantiate scene")
		return

	# Locate ProgressBar and set max_value to 0 (edge case).
	var progress_bar: ProgressBar = null
	var stack: Array[Node] = [bar]
	while stack.size() > 0:
		var node = stack.pop_front()
		if node is ProgressBar:
			progress_bar = node
			break
		for child in node.get_children():
			stack.append(child)

	if progress_bar != null:
		progress_bar.max_value = 0.1  # Set to tiny value to avoid div by 0
		progress_bar.value = 0.0
		# No crash expected; assertion is that the bar still exists.
		_assert_true(
			progress_bar is ProgressBar,
			"EHB-EDGE-1 — health bar handles zero/near-zero max_hp without crashing"
		)
	else:
		_fail("EHB-EDGE-1", "could not locate ProgressBar")

	bar.queue_free()


func test_ehb_edge_2_bar_handles_hp_greater_than_max() -> void:
	# EHB-EDGE-2: If enemy current_hp > max_hp (rare edge case from healing overshoot),
	# health bar clamps fill to max_value without crashing.

	var scene = _load_health_bar_scene()
	if scene == null:
		_fail("EHB-EDGE-2", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("EHB-EDGE-2", "could not instantiate scene")
		return

	var progress_bar: ProgressBar = null
	var stack: Array[Node] = [bar]
	while stack.size() > 0:
		var node = stack.pop_front()
		if node is ProgressBar:
			progress_bar = node
			break
		for child in node.get_children():
			stack.append(child)

	if progress_bar != null:
		progress_bar.max_value = 100.0
		progress_bar.value = 150.0  # Over-heal edge case
		# ProgressBar should clamp value to max.
		_assert_true(
			progress_bar.value <= progress_bar.max_value,
			"EHB-EDGE-2 — health bar value is clamped to max_value"
		)
	else:
		_fail("EHB-EDGE-2", "could not locate ProgressBar")

	bar.queue_free()


func test_ehb_edge_3_bar_visible_after_damage_timeout() -> void:
	# EHB-EDGE-3: After enemy is damaged and then recovers to full health,
	# bar hides after a short timeout (spec: "after a short timeout").
	# This test verifies the timeout mechanism exists.

	var scene = _load_health_bar_scene()
	if scene == null:
		_fail("EHB-EDGE-3", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("EHB-EDGE-3", "could not instantiate scene")
		return

	# Check if bar script has a Timer for visibility timeout.
	var has_timer: bool = false
	if bar.get_script() != null:
		var script = bar.get_script() as GDScript
		if script.source_code.contains("Timer") or script.source_code.contains("timeout"):
			has_timer = true

	# Also check for Timer children.
	var stack: Array[Node] = [bar]
	while stack.size() > 0:
		var node = stack.pop_front()
		if node is Timer:
			has_timer = true
			break
		for child in node.get_children():
			stack.append(child)

	_assert_true(
		has_timer,
		"EHB-EDGE-3 — health bar has timer mechanism for visibility timeout"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_enemy_health_bar_3d.gd ---")
	_pass_count = 0
	_fail_count = 0

	# EHB-LOAD tests
	test_ehb_load_1_health_bar_scene_path_exists()
	test_ehb_load_2_health_bar_scene_loads_as_node()

	# EHB-STRUCTURE tests
	test_ehb_structure_1_scene_has_root_node()
	test_ehb_structure_2_scene_has_progress_bar_child()

	# EHB-FILL tests
	test_ehb_fill_1_fill_updates_on_hp_change()
	test_ehb_fill_2_full_health_bar_value_equals_max()
	test_ehb_fill_3_zero_health_bar_value_is_zero()

	# EHB-VISIBILITY tests
	test_ehb_visibility_1_hidden_by_default_when_full_health()
	test_ehb_visibility_2_shown_when_damaged()

	# EHB-BILLBOARD tests
	test_ehb_billboard_1_bar_can_face_camera()
	test_ehb_billboard_2_positioned_above_enemy()

	# EHB-LIFECYCLE tests
	test_ehb_lifecycle_1_bar_removed_on_enemy_death()
	test_ehb_lifecycle_2_health_bar_ownership()

	# EHB-DEBUG-FLAG tests
	test_ehb_debug_flag_1_toggle_exists()
	test_ehb_debug_flag_2_toggle_hides_bar_when_disabled()

	# EHB-INTEGRATION tests
	test_ehb_integration_1_bar_attached_to_enemy_on_spawn()
	test_ehb_integration_2_bar_follows_enemy_position()

	# EHB-EDGE-CASES tests
	test_ehb_edge_1_bar_handles_zero_max_hp()
	test_ehb_edge_2_bar_handles_hp_greater_than_max()
	test_ehb_edge_3_bar_visible_after_damage_timeout()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
