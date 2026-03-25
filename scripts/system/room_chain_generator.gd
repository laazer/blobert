# room_chain_generator.gd
#
# Pure deterministic room chain generator.
# No SceneTree, no Node, no autoload dependencies.
#
# Ownership: Core Simulation Agent
# Ticket: project_board/6_milestone_6_roguelike_run_structure/in_progress/procedural_room_chaining.md
# Spec: agent_context/agents/2_spec/procedural_room_chaining_spec.md (Rev 2)
#
# Invariants:
#   - Does not mutate the caller's pool Dictionary or any Array within it.
#   - All randomness is driven by a fresh RandomNumberGenerator seeded at the
#     start of each generate() call; no state is retained between calls.
#   - Fisher-Yates shuffle uses rng.randi_range() for unbiased results (no Array.shuffle()).
#   - Returns a partial Array[String] on pool exhaustion; push_error is called
#     and no further items are appended for the exhausted category.

class_name RoomChainGenerator
extends RefCounted


func generate(sequence: Array[String], pool: Dictionary, seed: int) -> Array[String]:
	print("[RoomChainGenerator] seed: %d" % seed)

	# Empty sequence — valid degenerate input, no error.
	if sequence.is_empty():
		return []

	var rng := RandomNumberGenerator.new()
	rng.seed = seed

	# Validation pass: collect unique categories in first-appearance order and
	# verify each one exists in the pool as a non-empty Array.
	var unique_categories: Array[String] = []
	for category in sequence:
		if not unique_categories.has(category):
			unique_categories.append(category)

	for category in unique_categories:
		if not pool.has(category):
			push_error("[RoomChainGenerator] pool is missing required category: \"%s\"" % category)
			return []
		var pool_value = pool[category]
		if not pool_value is Array:
			push_error("[RoomChainGenerator] pool[\"%s\"] is not an Array" % category)
			return []
		if (pool_value as Array).is_empty():
			push_error("[RoomChainGenerator] pool[\"%s\"] is empty" % category)
			return []

	# Build a shuffled working copy per category (Fisher-Yates, immutable source).
	# working_copies: category -> Array (shuffled duplicate)
	# draw_indices:   category -> int (next draw position)
	var working_copies: Dictionary = {}
	var draw_indices: Dictionary = {}

	for category in unique_categories:
		var arr: Array = (pool[category] as Array).duplicate()
		# Fisher-Yates shuffle using rng.randi_range() for determinism without modulo bias.
		for i in range(arr.size() - 1, 0, -1):
			var j: int = rng.randi_range(0, i)
			var temp = arr[i]
			arr[i] = arr[j]
			arr[j] = temp
		working_copies[category] = arr
		draw_indices[category] = 0

	# Draw one item per sequence slot in order.
	var result: Array[String] = []

	for category in sequence:
		var idx: int = draw_indices[category]
		var wc: Array = working_copies[category]
		if idx >= wc.size():
			push_error("[RoomChainGenerator] pool[\"%s\"] exhausted after %d draws" % [category, wc.size()])
			return result
		result.append(wc[idx] as String)
		draw_indices[category] = idx + 1

	return result
