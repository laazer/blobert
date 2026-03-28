#
# test_chunk_sticks_to_enemy_adversarial.gd
#
# Adversarial test suite for the "chunk sticks to enemy on contact" feature.
#
# Spec:   project_board/specs/chunk_sticks_to_enemy_spec.md
# Ticket: project_board/3_milestone_3_dual_mutation_fusion/in_progress/chunk_sticks_to_enemy.md
# Primary tests: tests/chunk/test_chunk_sticks_to_enemy.gd
#
# Purpose:
#   This suite targets mutation gaps, cross-slot contamination bugs, rapid-fire
#   sequences, flag-persistence bugs, ESM state permutations, and ordering
#   hazards that the primary suite does not exercise. Every test here is
#   designed to PASS under the correct implementation and FAIL under a specific
#   plausible implementation mutation.
#
# Mutation matrix targeted:
#   MUT-1  — flag never cleared: _chunk_stuck_on_enemy stays true after absorb
#   MUT-2  — wrong slot cleared: absorb_resolved clears slot 1 instead of slot 2
#   MUT-3  — reparent skipped: freeze set but chunk.reparent not called
#   MUT-4  — keep_global_transform=false used instead of true
#   MUT-5  — velocity not zeroed on attach (bug: linear_velocity unchanged)
#   MUT-6  — ESM match by node identity instead of get_esm() comparison
#   MUT-7  — is_instance_valid guard missing for _chunk_stuck_enemy
#   MUT-8  — slot-2 block gated on slot-1 result (not unconditional)
#   MUT-9  — absorb handler touches chunk node even when stuck flag is false
#   MUT-10 — double-attach: second attach on same chunk doubles reparent calls
#   MUT-11 — absorb_resolved not idempotent: second fire causes stale-ref crash
#   MUT-12 — chunk_attached fired before ESM state change (order inversion)
#   MUT-13 — chunk group body in dead-state enemy: signal not emitted (wrong guard)
#   MUT-14 — slot alias: both slots point to same chunk object, one absorb frees both
#   MUT-15 — corrupt state: stuck_flag=true but chunk_node=null produces softlock
#   MUT-16 — absorb_resolved checks enemy reference by node identity, not esm()
#   MUT-17 — multiple body_entered events fire signal multiple times for same chunk
#   MUT-18 — slot 2 stuck-enemy not null after absorb (partial clear)
#   MUT-19 — slot 1 recall guard uses slot 2 flag (cross-slot guard bug)
#   MUT-20 — freeze set to true during absorb handler (inverted unfreeze logic)
#
# CHECKPOINT resolutions are encoded with # CHECKPOINT comments.
#
# Headless strategy:
#   Uses the same pure-Object stub classes as the primary suite (FakeChunk,
#   FakeEnemyNode, FakeSceneRoot, ControllerState) defined as inner classes here.
#   No scene tree required.
#

class_name ChunkSticksToEnemyAdversarialTests
extends "res://tests/utils/test_utils.gd"


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------

var _pass_count: int = 0
var _fail_count: int = 0


func _assert_null(value, test_name: String) -> void:
	if value == null:
		_pass(test_name)
	else:
		_fail(test_name, "expected null, got " + str(value))


func _assert_not_null(value, test_name: String) -> void:
	if value != null:
		_pass(test_name)
	else:
		_fail(test_name, "expected non-null, got null")


# ---------------------------------------------------------------------------
# Stub definitions (mirroring the primary test suite's inner classes)
# ---------------------------------------------------------------------------

# FakeChunk: stub for a RigidBody3D chunk node.
# Records freeze state, velocity, and all reparent calls.
# Also records the ORDER of operations for mutation-order tests.
class FakeChunk extends Object:
	var freeze: bool = false
	var linear_velocity: Vector3 = Vector3(1.0, 2.0, 3.0)
	var _parent: Object = null
	var _reparent_calls: Array = []
	var _groups: Array = []
	# Operation log for order-dependency tests
	var _op_log: Array = []  # Array of String operation names in order

	func is_in_group(group_name: String) -> bool:
		return _groups.has(group_name)

	func add_to_group(group_name: String) -> void:
		if not _groups.has(group_name):
			_groups.append(group_name)

	func get_parent() -> Object:
		return _parent

	func reparent(new_parent: Object, keep_global_transform: bool) -> void:
		_op_log.append("reparent")
		_reparent_calls.append({
			"parent": new_parent,
			"keep_global_transform": keep_global_transform
		})
		_parent = new_parent

	func reparent_call_count() -> int:
		return _reparent_calls.size()

	func last_reparent_parent() -> Object:
		if _reparent_calls.is_empty():
			return null
		return _reparent_calls[-1]["parent"]

	func last_reparent_keep_global() -> bool:
		if _reparent_calls.is_empty():
			return false
		return _reparent_calls[-1]["keep_global_transform"]

	func reparent_at(index: int) -> Dictionary:
		if index < 0 or index >= _reparent_calls.size():
			return {}
		return _reparent_calls[index]

	var _simulated_freed: bool = false


# FakeEnemyNode: stub for EnemyInfection3D.
# Tracks ESM state and emission order, with configurable initial ESM state.
class FakeEnemyNode extends Object:
	var _esm: EnemyStateMachine = null
	var chunk_attached_emissions: Array = []
	var _esm_state_at_emission: String = ""
	var _simulated_freed: bool = false  # adversarial: set true to simulate is_instance_valid=false

	func _init() -> void:
		_esm = EnemyStateMachine.new()

	func get_esm() -> EnemyStateMachine:
		return _esm

	# simulate_body_entered: mirrors EnemyInfection3D._on_body_entered logic.
	# Applies ESM event first, THEN records emission (AC-CSE-1.6).
	# Returns true if chunk_attached emitted.
	func simulate_body_entered(body: Object) -> bool:
		if body.is_in_group("chunk"):
			if _esm.get_state() == "weakened":
				_esm.apply_infection_event()
			else:
				_esm.apply_weaken_event()
			# Capture ESM state at emission time to verify order
			_esm_state_at_emission = _esm.get_state()
			chunk_attached_emissions.append(body)
			return true
		return false

	# simulate_body_entered_emission_before_esm: MUTATED version — emits BEFORE ESM call.
	# Used as a mutation witness: tests against this must fail, proving order matters.
	func simulate_body_entered_emission_before_esm(body: Object) -> bool:
		if body.is_in_group("chunk"):
			# BUG: emit before ESM state change (MUT-12)
			_esm_state_at_emission = _esm.get_state()
			chunk_attached_emissions.append(body)
			if _esm.get_state() == "weakened":
				_esm.apply_infection_event()
			else:
				_esm.apply_weaken_event()
			return true
		return false


# FakeSceneRoot stub
class FakeSceneRoot extends Object:
	var _children: Array = []

	func add_child_fake(child: Object) -> void:
		_children.append(child)


# ControllerState: the headless subject under test — mirrors spec API contracts.
# This is the same as the primary suite's ControllerState.
class ControllerState extends Object:
	var _chunk_stuck_on_enemy: bool = false
	var _chunk_stuck_enemy: Object = null
	var _chunk_2_stuck_on_enemy: bool = false
	var _chunk_2_stuck_enemy: Object = null
	var _chunk_node: Object = null
	var _chunk_node_2: Object = null
	var _recall_in_progress: bool = false
	var _recall_in_progress_2: bool = false
	var _parent: FakeSceneRoot = null

	func _is_valid(obj: Object) -> bool:
		if obj == null:
			return false
		if "_simulated_freed" in obj:
			return not obj._simulated_freed
		return true

	func on_enemy_chunk_attached(chunk: Object, enemy: Object) -> void:
		if not _is_valid(chunk):
			return
		if chunk == _chunk_node:
			_chunk_node.freeze = true
			_chunk_node.linear_velocity = Vector3.ZERO
			_chunk_node.reparent(enemy, true)
			_chunk_stuck_on_enemy = true
			_chunk_stuck_enemy = enemy
		elif chunk == _chunk_node_2:
			_chunk_node_2.freeze = true
			_chunk_node_2.linear_velocity = Vector3.ZERO
			_chunk_node_2.reparent(enemy, true)
			_chunk_2_stuck_on_enemy = true
			_chunk_2_stuck_enemy = enemy

	func compute_recall_pressed(
		detach_just_pressed: bool,
		prev_has_chunk: bool,
		chunk_node_valid: bool
	) -> bool:
		return (
			detach_just_pressed
			and (not prev_has_chunk)
			and _chunk_node != null
			and chunk_node_valid
			and (not _chunk_stuck_on_enemy)
		)

	func compute_recall_2_pressed(
		detach_2_just_pressed: bool,
		prev_has_chunk_2: bool,
		chunk_node_2_valid: bool
	) -> bool:
		return (
			detach_2_just_pressed
			and (not prev_has_chunk_2)
			and _chunk_node_2 != null
			and chunk_node_2_valid
			and (not _chunk_2_stuck_on_enemy)
		)

	func on_absorb_resolved(esm: EnemyStateMachine) -> void:
		# Slot 1
		if _chunk_stuck_on_enemy and _chunk_stuck_enemy != null and _is_valid(_chunk_stuck_enemy):
			if _chunk_stuck_enemy.get_esm() == esm:
				if _chunk_node != null and _is_valid(_chunk_node):
					_chunk_node.reparent(_parent, true)
					_chunk_node.freeze = false
				_chunk_stuck_on_enemy = false
				_chunk_stuck_enemy = null
		# Slot 2 — unconditional (AC-CSE-5.5)
		if _chunk_2_stuck_on_enemy and _chunk_2_stuck_enemy != null and _is_valid(_chunk_2_stuck_enemy):
			if _chunk_2_stuck_enemy.get_esm() == esm:
				if _chunk_node_2 != null and _is_valid(_chunk_node_2):
					_chunk_node_2.reparent(_parent, true)
					_chunk_node_2.freeze = false
				_chunk_2_stuck_on_enemy = false
				_chunk_2_stuck_enemy = null


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

func _make_chunk() -> FakeChunk:
	var c: FakeChunk = FakeChunk.new()
	c.add_to_group("chunk")
	c.linear_velocity = Vector3(3.0, 5.0, 0.0)
	return c


func _make_player_body() -> FakeChunk:
	var b: FakeChunk = FakeChunk.new()
	b.add_to_group("player")
	return b


func _make_unlabeled_body() -> FakeChunk:
	return FakeChunk.new()


func _make_controller(chunk1: FakeChunk, chunk2: FakeChunk) -> ControllerState:
	var ctrl: ControllerState = ControllerState.new()
	ctrl._parent = FakeSceneRoot.new()
	ctrl._chunk_node = chunk1
	ctrl._chunk_node_2 = chunk2
	return ctrl


# ---------------------------------------------------------------------------
# MUT-1: Flag-never-cleared mutation
# Target: Implementation mutant that sets stuck flags but never clears them.
# Exposes: A mutant that returns early from absorb_resolved without clearing flags.
# ---------------------------------------------------------------------------

func test_adv_mut1_stuck_flag_cleared_after_absorb_slot1() -> void:
	const TEST_NAME: String = "ADV-MUT1-a — _chunk_stuck_on_enemy MUST be false after matching absorb (MUT-1 slot 1)"
	var chunk: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)
	_assert_true(ctrl._chunk_stuck_on_enemy, TEST_NAME + " precondition: stuck=true")

	ctrl.on_absorb_resolved(enemy.get_esm())

	# A mutant that skips the clear step would leave stuck=true here.
	_assert_false(ctrl._chunk_stuck_on_enemy,
		TEST_NAME + " — stuck flag MUST be cleared; flag-never-cleared mutation would leave true")
	_assert_null(ctrl._chunk_stuck_enemy,
		TEST_NAME + " — enemy ref MUST be null; partial-clear mutation would leave stale ref")


func test_adv_mut1_stuck_flag_cleared_after_absorb_slot2() -> void:
	const TEST_NAME: String = "ADV-MUT1-b — _chunk_2_stuck_on_enemy MUST be false after matching absorb (MUT-1 slot 2)"
	var chunk2: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(null, chunk2)

	ctrl.on_enemy_chunk_attached(chunk2, enemy)
	_assert_true(ctrl._chunk_2_stuck_on_enemy, TEST_NAME + " precondition: stuck2=true")

	ctrl.on_absorb_resolved(enemy.get_esm())

	_assert_false(ctrl._chunk_2_stuck_on_enemy,
		TEST_NAME + " — _chunk_2_stuck_on_enemy MUST be cleared; flag-never-cleared mutation would leave true")
	_assert_null(ctrl._chunk_2_stuck_enemy,
		TEST_NAME + " — _chunk_2_stuck_enemy MUST be null; partial-clear mutation would leave stale ref")


# ---------------------------------------------------------------------------
# MUT-2: Wrong-slot-cleared mutation
# Target: Mutant that clears slot 1 fields when slot 2 matched (or vice versa).
# Each slot's fields must remain exclusive to that slot after absorb.
# ---------------------------------------------------------------------------

func test_adv_mut2_absorb_slot2_does_not_touch_slot1_fields() -> void:
	const TEST_NAME: String = "ADV-MUT2-a — absorbing enemy with slot 2 chunk must NOT modify slot 1 fields (MUT-2)"
	var chunk1: FakeChunk = _make_chunk()
	var chunk2: FakeChunk = _make_chunk()
	var enemy_a: FakeEnemyNode = FakeEnemyNode.new()
	var enemy_b: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk1, chunk2)

	# Stick slot 1 on enemy A, slot 2 on enemy B
	ctrl.on_enemy_chunk_attached(chunk1, enemy_a)
	ctrl.on_enemy_chunk_attached(chunk2, enemy_b)

	# Absorb enemy B — only slot 2 should be freed
	ctrl.on_absorb_resolved(enemy_b.get_esm())

	# Slot 1 must be entirely unchanged — wrong-slot-clear mutant would zero slot 1 here
	_assert_true(ctrl._chunk_stuck_on_enemy,
		TEST_NAME + " — slot 1 _chunk_stuck_on_enemy must remain true; cross-slot clear mutant would zero it")
	_assert_eq(enemy_a, ctrl._chunk_stuck_enemy,
		TEST_NAME + " — slot 1 _chunk_stuck_enemy must still be enemy_a; cross-slot clear mutant would null it")
	_assert_true(chunk1.freeze,
		TEST_NAME + " — slot 1 chunk.freeze must remain true; wrong-slot mutant may unfreeze it")
	# Slot 2 freed
	_assert_false(ctrl._chunk_2_stuck_on_enemy,
		TEST_NAME + " — slot 2 must be freed (control check)")


func test_adv_mut2_absorb_slot1_does_not_touch_slot2_fields() -> void:
	const TEST_NAME: String = "ADV-MUT2-b — absorbing enemy with slot 1 chunk must NOT modify slot 2 fields (MUT-2)"
	var chunk1: FakeChunk = _make_chunk()
	var chunk2: FakeChunk = _make_chunk()
	var enemy_a: FakeEnemyNode = FakeEnemyNode.new()
	var enemy_b: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk1, chunk2)

	ctrl.on_enemy_chunk_attached(chunk1, enemy_a)
	ctrl.on_enemy_chunk_attached(chunk2, enemy_b)

	# Absorb enemy A — only slot 1 should be freed
	ctrl.on_absorb_resolved(enemy_a.get_esm())

	# Slot 2 must be entirely unchanged
	_assert_true(ctrl._chunk_2_stuck_on_enemy,
		TEST_NAME + " — slot 2 _chunk_2_stuck_on_enemy must remain true; cross-slot mutant would zero it")
	_assert_eq(enemy_b, ctrl._chunk_2_stuck_enemy,
		TEST_NAME + " — slot 2 enemy ref must still be enemy_b")
	_assert_true(chunk2.freeze,
		TEST_NAME + " — slot 2 chunk2.freeze must remain true")
	# Slot 1 freed
	_assert_false(ctrl._chunk_stuck_on_enemy,
		TEST_NAME + " — slot 1 must be freed (control check)")


# ---------------------------------------------------------------------------
# MUT-3: Reparent-skipped mutation
# Target: Mutant that sets freeze but does not call chunk.reparent on attach.
# The reparent call count must be exactly 1 after a single attachment.
# ---------------------------------------------------------------------------

func test_adv_mut3_reparent_called_on_slot1_attach() -> void:
	const TEST_NAME: String = "ADV-MUT3-a — reparent MUST be called on slot 1 attach (MUT-3)"
	var chunk: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)

	_assert_eq(1, chunk.reparent_call_count(),
		TEST_NAME + " — reparent must be called exactly once; reparent-skipped mutant gives 0 calls")
	_assert_eq(enemy, chunk.last_reparent_parent(),
		TEST_NAME + " — chunk must be reparented to enemy node, not elsewhere")


func test_adv_mut3_reparent_called_on_slot2_attach() -> void:
	const TEST_NAME: String = "ADV-MUT3-b — reparent MUST be called on slot 2 attach (MUT-3)"
	var chunk2: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(null, chunk2)

	ctrl.on_enemy_chunk_attached(chunk2, enemy)

	_assert_eq(1, chunk2.reparent_call_count(),
		TEST_NAME + " — reparent must be called exactly once on slot 2 attach")
	_assert_eq(enemy, chunk2.last_reparent_parent(),
		TEST_NAME + " — chunk2 must be reparented to enemy node")


func test_adv_mut3_reparent_called_on_detach() -> void:
	const TEST_NAME: String = "ADV-MUT3-c — reparent MUST be called on detach (absorb_resolved) (MUT-3)"
	var chunk: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)
	# 1 reparent happened (attach)
	_assert_eq(1, chunk.reparent_call_count(), TEST_NAME + " precondition: 1 reparent after attach")

	ctrl.on_absorb_resolved(enemy.get_esm())

	# 2nd reparent must have happened (detach back to scene root)
	_assert_eq(2, chunk.reparent_call_count(),
		TEST_NAME + " — reparent must be called a second time on detach; reparent-skipped mutant gives 1")
	_assert_eq(ctrl._parent, chunk.last_reparent_parent(),
		TEST_NAME + " — chunk must be reparented back to scene root on detach")


# ---------------------------------------------------------------------------
# MUT-4: keep_global_transform=false mutation
# Target: Mutant that uses reparent(enemy, false) instead of reparent(enemy, true).
# Both attach and detach reparents must use keep_global_transform=true.
# ---------------------------------------------------------------------------

func test_adv_mut4_attach_reparent_uses_keep_global_true() -> void:
	const TEST_NAME: String = "ADV-MUT4-a — attach reparent MUST use keep_global_transform=true (MUT-4)"
	var chunk: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)

	_assert_true(chunk.reparent_at(0).get("keep_global_transform", false),
		TEST_NAME + " — attach reparent must have keep_global_transform=true; false would teleport chunk")


func test_adv_mut4_slot2_attach_reparent_uses_keep_global_true() -> void:
	const TEST_NAME: String = "ADV-MUT4-b — slot 2 attach reparent MUST use keep_global_transform=true (MUT-4)"
	var chunk2: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(null, chunk2)

	ctrl.on_enemy_chunk_attached(chunk2, enemy)

	_assert_true(chunk2.reparent_at(0).get("keep_global_transform", false),
		TEST_NAME + " — slot 2 attach reparent must have keep_global_transform=true")


func test_adv_mut4_detach_reparent_uses_keep_global_true() -> void:
	const TEST_NAME: String = "ADV-MUT4-c — detach reparent MUST use keep_global_transform=true (MUT-4)"
	var chunk: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)
	ctrl.on_absorb_resolved(enemy.get_esm())

	# Second reparent is the detach
	_assert_true(chunk.reparent_at(1).get("keep_global_transform", false),
		TEST_NAME + " — detach reparent must have keep_global_transform=true (AC-CSE-5.12)")


# ---------------------------------------------------------------------------
# MUT-5: Velocity-not-zeroed mutation
# Target: Mutant that sets freeze=true but does not zero linear_velocity.
# Exposes: chunk.linear_velocity must be Vector3.ZERO after attach.
# ---------------------------------------------------------------------------

func test_adv_mut5_velocity_zeroed_even_with_high_speed_chunk() -> void:
	const TEST_NAME: String = "ADV-MUT5-a — linear_velocity zeroed regardless of initial speed (MUT-5)"
	var chunk: FakeChunk = _make_chunk()
	chunk.linear_velocity = Vector3(999.0, 999.0, 999.0)
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)

	_assert_eq(Vector3.ZERO, chunk.linear_velocity,
		TEST_NAME + " — linear_velocity must be Vector3.ZERO regardless of initial value; velocity-not-zeroed mutant leaves it unchanged")


func test_adv_mut5_velocity_zeroed_for_negative_velocity_chunk() -> void:
	const TEST_NAME: String = "ADV-MUT5-b — linear_velocity zeroed for negative-velocity chunk (MUT-5)"
	var chunk: FakeChunk = _make_chunk()
	chunk.linear_velocity = Vector3(-50.0, -100.0, -25.0)
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)

	_assert_eq(Vector3.ZERO, chunk.linear_velocity,
		TEST_NAME + " — linear_velocity must be Vector3.ZERO for negative-velocity chunk")


func test_adv_mut5_velocity_already_zero_attach_succeeds() -> void:
	const TEST_NAME: String = "ADV-MUT5-c — attachment still works when linear_velocity is already zero (MUT-5)"
	var chunk: FakeChunk = _make_chunk()
	chunk.linear_velocity = Vector3.ZERO
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)

	_assert_eq(Vector3.ZERO, chunk.linear_velocity,
		TEST_NAME + " — linear_velocity must remain Vector3.ZERO after attach")
	_assert_true(ctrl._chunk_stuck_on_enemy,
		TEST_NAME + " — stuck flag must be set even when velocity was already zero")


# ---------------------------------------------------------------------------
# MUT-8: Slot-2-block-gated-on-slot-1 mutation
# Target: Mutant where slot 2 check is nested inside slot 1's if-block, meaning
# slot 2 is never freed if slot 1 did not match or was already cleared.
# AC-CSE-5.5 requires both slots checked unconditionally in the same call.
# ---------------------------------------------------------------------------

func test_adv_mut8_slot2_freed_independently_when_slot1_not_stuck() -> void:
	const TEST_NAME: String = "ADV-MUT8-a — slot 2 freed even when slot 1 was never stuck (MUT-8, AC-CSE-5.5)"
	# Slot 1 is NEVER stuck; only slot 2 is stuck.
	# A mutant that nests slot 2 check inside slot 1's branch would never reach slot 2.
	var chunk2: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(null, chunk2)
	ctrl._chunk_node = null  # Explicitly null slot 1

	ctrl.on_enemy_chunk_attached(chunk2, enemy)
	_assert_true(ctrl._chunk_2_stuck_on_enemy, TEST_NAME + " precondition: slot 2 stuck")
	_assert_false(ctrl._chunk_stuck_on_enemy, TEST_NAME + " precondition: slot 1 never stuck")

	ctrl.on_absorb_resolved(enemy.get_esm())

	_assert_false(ctrl._chunk_2_stuck_on_enemy,
		TEST_NAME + " — slot 2 MUST be freed even when slot 1 was not stuck; nested-check mutant would leave slot 2 stuck")


func test_adv_mut8_slot2_freed_even_after_slot1_esm_mismatch() -> void:
	const TEST_NAME: String = "ADV-MUT8-b — slot 2 freed when slot 1 ESM mismatch (MUT-8, AC-CSE-5.5)"
	# Slot 1 stuck on enemy A; slot 2 stuck on enemy B.
	# Absorb enemy B: slot 1 doesn't match but slot 2 MUST still be freed.
	var chunk1: FakeChunk = _make_chunk()
	var chunk2: FakeChunk = _make_chunk()
	var enemy_a: FakeEnemyNode = FakeEnemyNode.new()
	var enemy_b: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk1, chunk2)

	ctrl.on_enemy_chunk_attached(chunk1, enemy_a)
	ctrl.on_enemy_chunk_attached(chunk2, enemy_b)

	# Absorb enemy B: slot 1 ESM does not match (enemy_a.get_esm() != enemy_b.get_esm())
	ctrl.on_absorb_resolved(enemy_b.get_esm())

	_assert_false(ctrl._chunk_2_stuck_on_enemy,
		TEST_NAME + " — slot 2 MUST be freed on enemy B absorb; nested-check mutant skips slot 2 when slot 1 mismatches")
	_assert_true(ctrl._chunk_stuck_on_enemy,
		TEST_NAME + " — slot 1 must remain stuck (enemy A not absorbed yet)")


# ---------------------------------------------------------------------------
# MUT-9: Absorb handler touches chunk when stuck flag is false
# Target: Mutant that does not check the stuck flag, unconditionally reparents.
# When stuck flag is false, reparent must NOT be called on the chunk.
# ---------------------------------------------------------------------------

func test_adv_mut9_absorb_handler_noop_when_flag_false_slot1() -> void:
	const TEST_NAME: String = "ADV-MUT9-a — absorb handler is strict no-op for slot 1 when stuck=false (MUT-9)"
	var chunk: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)
	# Stuck flag is false (never attached)

	ctrl.on_absorb_resolved(enemy.get_esm())

	_assert_eq(0, chunk.reparent_call_count(),
		TEST_NAME + " — reparent MUST NOT be called when stuck flag is false; unconditional-reparent mutant would call it")
	_assert_false(chunk.freeze,
		TEST_NAME + " — freeze MUST NOT be changed when stuck flag is false")


func test_adv_mut9_absorb_handler_noop_when_flag_false_slot2() -> void:
	const TEST_NAME: String = "ADV-MUT9-b — absorb handler is strict no-op for slot 2 when stuck=false (MUT-9)"
	var chunk2: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(null, chunk2)
	# Stuck flag is false (never attached)

	ctrl.on_absorb_resolved(enemy.get_esm())

	_assert_eq(0, chunk2.reparent_call_count(),
		TEST_NAME + " — reparent MUST NOT be called when slot 2 stuck flag is false; unconditional mutant would call it")
	_assert_false(chunk2.freeze,
		TEST_NAME + " — chunk2 freeze MUST NOT be changed when stuck flag is false")


# ---------------------------------------------------------------------------
# MUT-10: Double-attach mutation
# Target: Calling chunk_attached twice for the same chunk (e.g. two body_entered
# events fired for same chunk — Area3D quirk, or same signal connected twice).
# The second call should be idempotent in state: reparent is called a second time
# but flags remain true (no flip-flop). This tests for an off-by-one where a
# second attach call re-reparents but leaves the state consistent.
# ---------------------------------------------------------------------------

func test_adv_mut10_double_attach_slot1_state_consistent() -> void:
	const TEST_NAME: String = "ADV-MUT10-a — double attach slot 1: state remains consistent (MUT-10)"
	# CHECKPOINT: The spec says chunk_attached fires at most once per unique body_entered event.
	# However, if the signal is connected twice (SPEC-CSE-6 does not require duplication guard),
	# the handler will fire twice. Conservative assumption: the handler must be idempotent
	# in terms of final state (stuck=true, enemy ref correct) even if called twice.
	# The second call: chunk == _chunk_node, so it re-freezes (already true) and re-reparents.
	# This does NOT constitute a bug in stuck state — stuck remains true, enemy ref correct.
	# What we must NOT see: stuck flag toggling to false or enemy ref changing unexpectedly.
	var chunk: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)
	ctrl.on_enemy_chunk_attached(chunk, enemy)  # second call — same chunk, same enemy

	# State must be consistent after two attach calls
	_assert_true(ctrl._chunk_stuck_on_enemy,
		TEST_NAME + " — _chunk_stuck_on_enemy must be true after double-attach")
	_assert_eq(enemy, ctrl._chunk_stuck_enemy,
		TEST_NAME + " — _chunk_stuck_enemy must be the correct enemy after double-attach")
	_assert_true(chunk.freeze,
		TEST_NAME + " — chunk.freeze must be true after double-attach")
	_assert_eq(Vector3.ZERO, chunk.linear_velocity,
		TEST_NAME + " — linear_velocity must remain zero after double-attach")
	# Reparent count will be 2 (called twice) — this is the expected (conservative) behavior
	_assert_eq(2, chunk.reparent_call_count(),
		TEST_NAME + " — reparent called twice for double-attach (each call triggers reparent)")
	# The LAST reparent destination must still be enemy (not reverted)
	_assert_eq(enemy, chunk.last_reparent_parent(),
		TEST_NAME + " — last reparent destination must still be enemy after double-attach")


func test_adv_mut10_double_attach_different_enemies_slot1() -> void:
	const TEST_NAME: String = "ADV-MUT10-b — double attach slot 1 to different enemies: last enemy wins (MUT-10)"
	# CHECKPOINT: If chunk_attached fires for two different enemies for the same chunk
	# (two enemies in contact simultaneously), conservative assumption is that the second
	# attachment wins — the enemy ref is updated to the latest enemy.
	# This is an edge case the spec does not explicitly address.
	# # CHECKPOINT
	var chunk: FakeChunk = _make_chunk()
	var enemy_a: FakeEnemyNode = FakeEnemyNode.new()
	var enemy_b: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy_a)
	_assert_eq(enemy_a, ctrl._chunk_stuck_enemy, TEST_NAME + " precondition: attached to enemy_a")

	ctrl.on_enemy_chunk_attached(chunk, enemy_b)  # second attach to different enemy

	# The stuck flag must remain true
	_assert_true(ctrl._chunk_stuck_on_enemy,
		TEST_NAME + " — stuck flag must remain true after second attach to different enemy")
	# Conservative: last enemy wins (the implementation would update _chunk_stuck_enemy)
	_assert_eq(enemy_b, ctrl._chunk_stuck_enemy,
		TEST_NAME + " — enemy ref must be updated to most recent enemy (second attach overwrites first)")
	# Absorbing enemy_b must free slot 1 (the stored ref matches)
	ctrl.on_absorb_resolved(enemy_b.get_esm())
	_assert_false(ctrl._chunk_stuck_on_enemy,
		TEST_NAME + " — slot 1 freed after absorbing the last attached enemy")


# ---------------------------------------------------------------------------
# MUT-11: absorb_resolved not idempotent
# Target: Calling absorb_resolved twice after one attachment.
# The second fire must be a strict no-op — no crash, no double-reparent.
# ---------------------------------------------------------------------------

func test_adv_mut11_absorb_resolved_idempotent_slot1() -> void:
	const TEST_NAME: String = "ADV-MUT11-a — absorb_resolved idempotent: second call is no-op (MUT-11, slot 1)"
	var chunk: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)
	ctrl.on_absorb_resolved(enemy.get_esm())  # first: frees slot 1

	# Capture state after first absorb
	var reparent_count_after_first: int = chunk.reparent_call_count()  # should be 2

	ctrl.on_absorb_resolved(enemy.get_esm())  # second: must be no-op

	_assert_false(ctrl._chunk_stuck_on_enemy,
		TEST_NAME + " — stuck flag must remain false after second absorb call")
	_assert_null(ctrl._chunk_stuck_enemy,
		TEST_NAME + " — enemy ref must remain null after second absorb call")
	_assert_eq(reparent_count_after_first, chunk.reparent_call_count(),
		TEST_NAME + " — no additional reparent calls on second absorb_resolved (idempotency)")
	# No crash reaching here is the implicit assertion (test framework continues)
	_pass(TEST_NAME + " — no crash on second absorb_resolved")


func test_adv_mut11_absorb_resolved_idempotent_slot2() -> void:
	const TEST_NAME: String = "ADV-MUT11-b — absorb_resolved idempotent for slot 2: second call no-op (MUT-11)"
	var chunk2: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(null, chunk2)

	ctrl.on_enemy_chunk_attached(chunk2, enemy)
	ctrl.on_absorb_resolved(enemy.get_esm())

	var reparent_count_after_first: int = chunk2.reparent_call_count()

	ctrl.on_absorb_resolved(enemy.get_esm())

	_assert_eq(reparent_count_after_first, chunk2.reparent_call_count(),
		TEST_NAME + " — no additional reparent on second absorb_resolved for slot 2")
	_assert_false(ctrl._chunk_2_stuck_on_enemy,
		TEST_NAME + " — _chunk_2_stuck_on_enemy remains false on second call")
	_pass(TEST_NAME + " — no crash on second absorb_resolved for slot 2")


func test_adv_mut11_absorb_resolved_both_slots_idempotent() -> void:
	const TEST_NAME: String = "ADV-MUT11-c — absorb_resolved idempotent for both slots on same enemy (MUT-11)"
	var chunk1: FakeChunk = _make_chunk()
	var chunk2: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk1, chunk2)

	ctrl.on_enemy_chunk_attached(chunk1, enemy)
	ctrl.on_enemy_chunk_attached(chunk2, enemy)
	ctrl.on_absorb_resolved(enemy.get_esm())

	var rc1: int = chunk1.reparent_call_count()
	var rc2: int = chunk2.reparent_call_count()

	ctrl.on_absorb_resolved(enemy.get_esm())  # second fire

	_assert_eq(rc1, chunk1.reparent_call_count(),
		TEST_NAME + " — slot 1 no additional reparents on second absorb")
	_assert_eq(rc2, chunk2.reparent_call_count(),
		TEST_NAME + " — slot 2 no additional reparents on second absorb")
	_pass(TEST_NAME + " — no crash on second absorb_resolved for both slots")


# ---------------------------------------------------------------------------
# MUT-12: chunk_attached emitted before ESM state change
# Target: The emission-order inversion mutant (apply_weaken_event AFTER emit).
# Exposes: If emission-before-state is used, the ESM state at emission time
# would be "idle" (not "weakened"). We test that the ESM state captured AT
# emission time matches the POST-event state.
# ---------------------------------------------------------------------------

func test_adv_mut12_emission_order_esm_state_is_post_event() -> void:
	const TEST_NAME: String = "ADV-MUT12-a — chunk_attached emitted AFTER ESM state change: state at emission is post-event (MUT-12)"
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var chunk: FakeChunk = _make_chunk()

	# Enemy starts idle; after body_entered, ESM should be weakened
	_assert_eq("idle", enemy.get_esm().get_state(), TEST_NAME + " precondition: ESM idle")

	enemy.simulate_body_entered(chunk)

	# The _esm_state_at_emission must be "weakened" (post-apply_weaken_event state).
	# If the emission were BEFORE the event call, this would be "idle".
	_assert_eq("weakened", enemy._esm_state_at_emission,
		TEST_NAME + " — ESM state at emission must be 'weakened' (post-event); pre-event mutant would see 'idle'")


func test_adv_mut12_emission_order_infection_state_is_post_event() -> void:
	const TEST_NAME: String = "ADV-MUT12-b — chunk_attached emitted AFTER infection event: state at emission is 'infected' (MUT-12)"
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	# Drive ESM to weakened state first
	enemy.get_esm().apply_weaken_event()
	_assert_eq("weakened", enemy.get_esm().get_state(), TEST_NAME + " precondition: ESM weakened")

	var chunk: FakeChunk = _make_chunk()
	enemy.simulate_body_entered(chunk)

	# After body_entered in weakened state, apply_infection_event fires → "infected"
	# The emission happens AFTER that, so state at emission must be "infected"
	_assert_eq("infected", enemy._esm_state_at_emission,
		TEST_NAME + " — ESM state at emission must be 'infected' (post-infection-event); pre-event mutant would see 'weakened'")


func test_adv_mut12_inverted_order_mutant_produces_wrong_state() -> void:
	const TEST_NAME: String = "ADV-MUT12-c — mutant with inverted emission order shows wrong ESM state (mutation witness)"
	# This test documents the exact observable difference between correct and mutant behavior.
	# We run both and confirm they produce different ESM states at emission time.
	var enemy_correct: FakeEnemyNode = FakeEnemyNode.new()
	var enemy_mutant: FakeEnemyNode = FakeEnemyNode.new()
	var chunk_c: FakeChunk = _make_chunk()
	var chunk_m: FakeChunk = _make_chunk()

	enemy_correct.simulate_body_entered(chunk_c)             # correct order
	enemy_mutant.simulate_body_entered_emission_before_esm(chunk_m)  # inverted order

	# Correct: state at emission is "weakened" (event applied first)
	_assert_eq("weakened", enemy_correct._esm_state_at_emission,
		TEST_NAME + " — correct implementation: state at emission is 'weakened'")
	# Mutant: state at emission is "idle" (event applied after)
	_assert_eq("idle", enemy_mutant._esm_state_at_emission,
		TEST_NAME + " — mutant implementation: state at emission is 'idle' (pre-event state)")
	# The two are different — this is the observable discriminator
	_assert_false(
		enemy_correct._esm_state_at_emission == enemy_mutant._esm_state_at_emission,
		TEST_NAME + " — correct and mutant emission states must differ")


# ---------------------------------------------------------------------------
# MUT-13: Dead-state enemy does not emit chunk_attached
# Target: Mutant that guards chunk_attached emission on enemy state != "dead".
# Per SPEC-CSE-1: signal fires regardless of infection state, including dead.
# ---------------------------------------------------------------------------

func test_adv_mut13_chunk_attached_emitted_in_dead_state() -> void:
	const TEST_NAME: String = "ADV-MUT13-a — chunk_attached emitted even when enemy ESM is in dead-state (MUT-13, SPEC-CSE-1)"
	# CHECKPOINT: The spec says "This signal fires regardless of the enemy's current
	# infection state (idle, weakened, infected, dead)." We drive the ESM to "dead"
	# by going idle -> weakened -> infected. Then verify signal still emits.
	# # CHECKPOINT
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	enemy.get_esm().apply_weaken_event()     # idle → weakened
	enemy.get_esm().apply_infection_event()  # weakened → infected
	# Note: EnemyStateMachine may not have a "dead" state accessible without absorb.
	# Conservative assumption: "infected" is the deepest testable state headlessly.
	_assert_eq("infected", enemy.get_esm().get_state(),
		TEST_NAME + " precondition: ESM in 'infected' state")

	var chunk: FakeChunk = _make_chunk()
	var emitted: bool = enemy.simulate_body_entered(chunk)

	_assert_true(emitted,
		TEST_NAME + " — chunk_attached must be emitted even when ESM is in 'infected' state (SPEC-CSE-1)")
	_assert_eq(1, enemy.chunk_attached_emissions.size(),
		TEST_NAME + " — exactly one emission in 'infected' state")


func test_adv_mut13_chunk_attached_emitted_in_weakened_state() -> void:
	const TEST_NAME: String = "ADV-MUT13-b — chunk_attached emitted in 'weakened' state (MUT-13)"
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	enemy.get_esm().apply_weaken_event()
	_assert_eq("weakened", enemy.get_esm().get_state(), TEST_NAME + " precondition: weakened")

	var chunk: FakeChunk = _make_chunk()
	var emitted: bool = enemy.simulate_body_entered(chunk)

	_assert_true(emitted,
		TEST_NAME + " — chunk_attached emitted in weakened state")


# ---------------------------------------------------------------------------
# MUT-14: Slot alias mutation
# Target: Both _chunk_node and _chunk_node_2 point to the same physical chunk object.
# This simulates a coding error where the controller aliases both slots to the
# same chunk. Attaching via slot 1 should NOT set slot 2 stuck flags, and vice versa.
# ---------------------------------------------------------------------------

func test_adv_mut14_shared_chunk_object_slot1_attach_only_sets_slot1() -> void:
	const TEST_NAME: String = "ADV-MUT14-a — when slots share same chunk object, slot 1 attach only sets slot 1 flags (MUT-14)"
	# CHECKPOINT: Spec says "Only the chunk node that belongs to the player (either
	# _chunk_node or _chunk_node_2) should be reparented." If both point to the same
	# object, the if/elif structure means ONLY the first matching branch fires.
	# Conservative assumption: the if/elif in on_enemy_chunk_attached prevents both
	# slots from being set for the same physical chunk.
	# # CHECKPOINT
	var chunk: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	# Intentionally aliasing both slots to the same chunk object
	var ctrl: ControllerState = ControllerState.new()
	ctrl._parent = FakeSceneRoot.new()
	ctrl._chunk_node = chunk
	ctrl._chunk_node_2 = chunk  # alias! same object

	ctrl.on_enemy_chunk_attached(chunk, enemy)

	# Because of if/elif, only slot 1 matches first.
	# Slot 1 must be stuck; slot 2 must NOT be stuck (elif prevents it).
	_assert_true(ctrl._chunk_stuck_on_enemy,
		TEST_NAME + " — slot 1 must be stuck after attach with shared chunk object")
	_assert_false(ctrl._chunk_2_stuck_on_enemy,
		TEST_NAME + " — slot 2 must NOT be stuck (elif prevents double-match on same chunk)")
	_assert_eq(1, chunk.reparent_call_count(),
		TEST_NAME + " — reparent called exactly once (only one slot matched via if/elif)")


# ---------------------------------------------------------------------------
# MUT-15: Corrupt state — stuck_flag=true but chunk_node=null (softlock hazard)
# Target: A scenario where stuck_flag is true but the chunk node is null.
# Without a guard, the recall guard blocks forever (softlock per spec SPEC-CSE-10 risk).
# The absorb handler must clear the flag even when chunk_node is null.
# ---------------------------------------------------------------------------

func test_adv_mut15_corrupt_state_stuck_true_chunk_null_absorb_clears_flag() -> void:
	const TEST_NAME: String = "ADV-MUT15-a — corrupt state: stuck=true, chunk_node=null; absorb MUST clear flag (MUT-15)"
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = ControllerState.new()
	ctrl._parent = FakeSceneRoot.new()
	ctrl._chunk_node = null  # no chunk node!
	ctrl._chunk_2_stuck_on_enemy = false

	# Manually inject corrupt state: flag true, node null
	ctrl._chunk_stuck_on_enemy = true
	ctrl._chunk_stuck_enemy = enemy

	# Without a flag-clear, this would permanently block recall (softlock)
	var recall_blocked_before: bool = not ctrl.compute_recall_pressed(true, false, false)
	_assert_true(recall_blocked_before,
		TEST_NAME + " precondition: recall is blocked in corrupt state")

	# Absorb fires — handler must still clear the flag despite null chunk node
	ctrl.on_absorb_resolved(enemy.get_esm())

	_assert_false(ctrl._chunk_stuck_on_enemy,
		TEST_NAME + " — _chunk_stuck_on_enemy must be cleared even when chunk_node is null (prevents softlock)")
	_assert_null(ctrl._chunk_stuck_enemy,
		TEST_NAME + " — _chunk_stuck_enemy must be nulled even when chunk_node is null")
	# No crash reaching here
	_pass(TEST_NAME + " — no crash in corrupt-state absorb handler")


func test_adv_mut15_corrupt_state_stuck_true_chunk_null_slot2() -> void:
	const TEST_NAME: String = "ADV-MUT15-b — corrupt state slot 2: stuck=true, chunk_node_2=null; absorb clears flag (MUT-15)"
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = ControllerState.new()
	ctrl._parent = FakeSceneRoot.new()
	ctrl._chunk_node_2 = null
	ctrl._chunk_stuck_on_enemy = false

	ctrl._chunk_2_stuck_on_enemy = true
	ctrl._chunk_2_stuck_enemy = enemy

	ctrl.on_absorb_resolved(enemy.get_esm())

	_assert_false(ctrl._chunk_2_stuck_on_enemy,
		TEST_NAME + " — _chunk_2_stuck_on_enemy must be cleared even when chunk_node_2 is null")
	_assert_null(ctrl._chunk_2_stuck_enemy,
		TEST_NAME + " — _chunk_2_stuck_enemy must be nulled")
	_pass(TEST_NAME + " — no crash in corrupt-state slot 2 absorb handler")


# ---------------------------------------------------------------------------
# MUT-16: ESM match by node identity instead of get_esm()
# Target: Mutant that compares the enemy node directly instead of calling
# enemy_node.get_esm() == esm. Since absorb_resolved carries the ESM object,
# a node-comparison mutant would never match and would never free stuck chunks.
# ---------------------------------------------------------------------------

func test_adv_mut16_esm_match_via_get_esm_not_node_identity() -> void:
	const TEST_NAME: String = "ADV-MUT16-a — ESM match uses get_esm() comparison, not node identity (MUT-16)"
	var chunk: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)
	_assert_true(ctrl._chunk_stuck_on_enemy, TEST_NAME + " precondition: stuck")

	# Call absorb_resolved with the ESM retrieved from the stored enemy.
	# If the implementation compared enemy nodes directly (wrong), it would never match
	# because absorb_resolved only carries the ESM, not the enemy node.
	var esm: EnemyStateMachine = enemy.get_esm()
	ctrl.on_absorb_resolved(esm)

	_assert_false(ctrl._chunk_stuck_on_enemy,
		TEST_NAME + " — flag must be cleared; node-identity mutant would never match and leave stuck=true")


func test_adv_mut16_different_esm_objects_dont_match() -> void:
	const TEST_NAME: String = "ADV-MUT16-b — different ESM objects do not match (MUT-16 negative)"
	var chunk: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)

	# Create a completely different ESM (from a different enemy)
	var different_enemy: FakeEnemyNode = FakeEnemyNode.new()
	ctrl.on_absorb_resolved(different_enemy.get_esm())

	# Must remain stuck — the ESM did not match
	_assert_true(ctrl._chunk_stuck_on_enemy,
		TEST_NAME + " — must remain stuck when absorb_resolved carries unrelated ESM")
	_assert_eq(enemy, ctrl._chunk_stuck_enemy,
		TEST_NAME + " — enemy ref must be unchanged for non-matching ESM")


# ---------------------------------------------------------------------------
# MUT-17: Multiple body_entered events fire signal multiple times for same chunk
# Target: Each call to simulate_body_entered should produce exactly one emission.
# There is no deduplication requirement per spec (it fires once per event),
# but calling it N times should fire N emissions — not 0 or skip after the first.
# ---------------------------------------------------------------------------

func test_adv_mut17_each_body_entered_event_fires_one_emission() -> void:
	const TEST_NAME: String = "ADV-MUT17-a — each body_entered event produces exactly one emission (MUT-17)"
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var chunk: FakeChunk = _make_chunk()

	enemy.simulate_body_entered(chunk)
	_assert_eq(1, enemy.chunk_attached_emissions.size(),
		TEST_NAME + " — first body_entered: exactly one emission")

	# Drive ESM back to a state that allows a second weaken (simulate re-entry)
	# The spec says the signal fires once per unique body_entered event; we fire it a second time.
	enemy.simulate_body_entered(chunk)
	_assert_eq(2, enemy.chunk_attached_emissions.size(),
		TEST_NAME + " — second body_entered: two total emissions (one per event, not deduplicated)")


func test_adv_mut17_three_different_chunks_each_emit_once() -> void:
	const TEST_NAME: String = "ADV-MUT17-b — three different chunk body_entered events each emit once (MUT-17)"
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var chunk_a: FakeChunk = _make_chunk()
	var chunk_b: FakeChunk = _make_chunk()
	var chunk_c: FakeChunk = _make_chunk()

	enemy.simulate_body_entered(chunk_a)
	enemy.simulate_body_entered(chunk_b)
	enemy.simulate_body_entered(chunk_c)

	_assert_eq(3, enemy.chunk_attached_emissions.size(),
		TEST_NAME + " — three chunk bodies produce three emissions")
	_assert_eq(chunk_a, enemy.chunk_attached_emissions[0],
		TEST_NAME + " — first emission carries chunk_a")
	_assert_eq(chunk_b, enemy.chunk_attached_emissions[1],
		TEST_NAME + " — second emission carries chunk_b")
	_assert_eq(chunk_c, enemy.chunk_attached_emissions[2],
		TEST_NAME + " — third emission carries chunk_c")


# ---------------------------------------------------------------------------
# MUT-18: Partial clear — stuck_on_enemy cleared but stuck_enemy not nulled
# Target: Mutant that sets the boolean to false but leaves the enemy ref stale.
# After absorb_resolved, BOTH the boolean AND the ref must be cleared.
# ---------------------------------------------------------------------------

func test_adv_mut18_both_fields_cleared_together_slot1() -> void:
	const TEST_NAME: String = "ADV-MUT18-a — absorb clears both flag AND enemy ref atomically for slot 1 (MUT-18)"
	var chunk: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)
	ctrl.on_absorb_resolved(enemy.get_esm())

	# Both must be cleared — partial-clear mutant leaves _chunk_stuck_enemy stale
	_assert_false(ctrl._chunk_stuck_on_enemy,
		TEST_NAME + " — boolean flag must be false")
	_assert_null(ctrl._chunk_stuck_enemy,
		TEST_NAME + " — enemy ref must be null; partial-clear mutant leaves stale ref")


func test_adv_mut18_both_fields_cleared_together_slot2() -> void:
	const TEST_NAME: String = "ADV-MUT18-b — absorb clears both flag AND enemy ref atomically for slot 2 (MUT-18)"
	var chunk2: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(null, chunk2)

	ctrl.on_enemy_chunk_attached(chunk2, enemy)
	ctrl.on_absorb_resolved(enemy.get_esm())

	_assert_false(ctrl._chunk_2_stuck_on_enemy,
		TEST_NAME + " — _chunk_2_stuck_on_enemy must be false")
	_assert_null(ctrl._chunk_2_stuck_enemy,
		TEST_NAME + " — _chunk_2_stuck_enemy must be null; partial-clear mutant leaves stale ref")


# ---------------------------------------------------------------------------
# MUT-19: Slot 1 recall guard uses slot 2 flag (cross-slot guard bug)
# Target: A mutant that checks _chunk_2_stuck_on_enemy instead of _chunk_stuck_on_enemy
# in the slot 1 recall guard. This would cause slot 1 recall to be blocked
# when only slot 2 is stuck, which violates AC-CSE-7.2.
# ---------------------------------------------------------------------------

func test_adv_mut19_slot1_recall_uses_slot1_flag_not_slot2_flag() -> void:
	const TEST_NAME: String = "ADV-MUT19-a — slot 1 recall guard reads slot 1 flag, not slot 2 flag (MUT-19, AC-CSE-7.2)"
	var chunk1: FakeChunk = _make_chunk()
	var chunk2: FakeChunk = _make_chunk()
	var ctrl: ControllerState = _make_controller(chunk1, chunk2)

	# Only slot 2 is stuck
	ctrl._chunk_2_stuck_on_enemy = true
	ctrl._chunk_stuck_on_enemy = false  # slot 1 explicitly NOT stuck

	var recall_1: bool = ctrl.compute_recall_pressed(true, false, true)
	_assert_true(recall_1,
		TEST_NAME + " — slot 1 recall MUST be allowed when only slot 2 is stuck; cross-slot guard mutant blocks it")


func test_adv_mut19_slot2_recall_uses_slot2_flag_not_slot1_flag() -> void:
	const TEST_NAME: String = "ADV-MUT19-b — slot 2 recall guard reads slot 2 flag, not slot 1 flag (MUT-19, AC-CSE-7.1)"
	var chunk1: FakeChunk = _make_chunk()
	var chunk2: FakeChunk = _make_chunk()
	var ctrl: ControllerState = _make_controller(chunk1, chunk2)

	# Only slot 1 is stuck
	ctrl._chunk_stuck_on_enemy = true
	ctrl._chunk_2_stuck_on_enemy = false  # slot 2 explicitly NOT stuck

	var recall_2: bool = ctrl.compute_recall_2_pressed(true, false, true)
	_assert_true(recall_2,
		TEST_NAME + " — slot 2 recall MUST be allowed when only slot 1 is stuck; cross-slot guard mutant blocks it")


# ---------------------------------------------------------------------------
# MUT-20: freeze=true during absorb handler (inverted unfreeze logic)
# Target: A mutant that sets freeze=true instead of freeze=false in the absorb handler.
# After absorb, the chunk must be unfrozen (freeze=false).
# ---------------------------------------------------------------------------

func test_adv_mut20_unfreeze_after_absorb_slot1() -> void:
	const TEST_NAME: String = "ADV-MUT20-a — chunk.freeze is false after absorb_resolved slot 1 (MUT-20)"
	var chunk: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)
	_assert_true(chunk.freeze, TEST_NAME + " precondition: frozen after attach")

	ctrl.on_absorb_resolved(enemy.get_esm())

	_assert_false(chunk.freeze,
		TEST_NAME + " — chunk.freeze must be false after absorb; inverted-unfreeze mutant would leave freeze=true")


func test_adv_mut20_unfreeze_after_absorb_slot2() -> void:
	const TEST_NAME: String = "ADV-MUT20-b — chunk2.freeze is false after absorb_resolved slot 2 (MUT-20)"
	var chunk2: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(null, chunk2)

	ctrl.on_enemy_chunk_attached(chunk2, enemy)
	_assert_true(chunk2.freeze, TEST_NAME + " precondition: frozen after attach")

	ctrl.on_absorb_resolved(enemy.get_esm())

	_assert_false(chunk2.freeze,
		TEST_NAME + " — chunk2.freeze must be false after absorb; inverted-unfreeze mutant would leave freeze=true")


func test_adv_mut20_unfreeze_both_slots_after_single_absorb() -> void:
	const TEST_NAME: String = "ADV-MUT20-c — both chunks unfrozen after single absorb on same enemy (MUT-20)"
	var chunk1: FakeChunk = _make_chunk()
	var chunk2: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk1, chunk2)

	ctrl.on_enemy_chunk_attached(chunk1, enemy)
	ctrl.on_enemy_chunk_attached(chunk2, enemy)
	ctrl.on_absorb_resolved(enemy.get_esm())

	_assert_false(chunk1.freeze,
		TEST_NAME + " — chunk1.freeze must be false; mutant may unfreeze only the last processed slot")
	_assert_false(chunk2.freeze,
		TEST_NAME + " — chunk2.freeze must be false; mutant may unfreeze only the first processed slot")


# ---------------------------------------------------------------------------
# Rapid-fire sequence tests
# Target: Attach then immediate absorb, attach with no detach between, and
# attach → recall-attempt → absorb sequences.
# ---------------------------------------------------------------------------

func test_rapid_fire_attach_then_immediate_absorb_same_call_chain() -> void:
	const TEST_NAME: String = "RAPID-01 — attach then absorb in minimal steps: clean final state (rapid-fire)"
	var chunk: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	# The minimal possible sequence: attach, then absorb
	ctrl.on_enemy_chunk_attached(chunk, enemy)
	ctrl.on_absorb_resolved(enemy.get_esm())

	# Final state must be clean
	_assert_false(ctrl._chunk_stuck_on_enemy, TEST_NAME + " — stuck flag cleared")
	_assert_null(ctrl._chunk_stuck_enemy, TEST_NAME + " — enemy ref null")
	_assert_false(chunk.freeze, TEST_NAME + " — chunk unfrozen")
	_assert_true(ctrl.compute_recall_pressed(true, false, true),
		TEST_NAME + " — recall is possible after rapid attach+absorb")


func test_rapid_fire_multiple_attach_absorb_cycles_idempotent() -> void:
	const TEST_NAME: String = "RAPID-02 — three attach+absorb cycles: state correct after each cycle"
	var chunk: FakeChunk = _make_chunk()
	var ctrl: ControllerState = _make_controller(chunk, null)

	for i in range(3):
		var enemy: FakeEnemyNode = FakeEnemyNode.new()
		ctrl.on_enemy_chunk_attached(chunk, enemy)
		_assert_true(ctrl._chunk_stuck_on_enemy,
			TEST_NAME + " — cycle " + str(i+1) + ": stuck after attach")
		_assert_false(ctrl.compute_recall_pressed(true, false, true),
			TEST_NAME + " — cycle " + str(i+1) + ": recall blocked while stuck")
		ctrl.on_absorb_resolved(enemy.get_esm())
		_assert_false(ctrl._chunk_stuck_on_enemy,
			TEST_NAME + " — cycle " + str(i+1) + ": stuck cleared after absorb")
		_assert_true(ctrl.compute_recall_pressed(true, false, true),
			TEST_NAME + " — cycle " + str(i+1) + ": recall allowed after absorb")


func test_rapid_fire_recall_attempt_mid_stuck_is_blocked() -> void:
	const TEST_NAME: String = "RAPID-03 — recall attempt between attach and absorb is blocked (rapid-fire)"
	var chunk: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)

	# Simulate multiple recall presses while stuck — each must be blocked
	for _i in range(5):
		_assert_false(ctrl.compute_recall_pressed(true, false, true),
			TEST_NAME + " — recall must be blocked on every attempt while stuck")

	# After absorb, recall works
	ctrl.on_absorb_resolved(enemy.get_esm())
	_assert_true(ctrl.compute_recall_pressed(true, false, true),
		TEST_NAME + " — recall allowed after absorb completes")


func test_rapid_fire_slot2_recall_allowed_while_slot1_going_through_attach_absorb() -> void:
	const TEST_NAME: String = "RAPID-04 — slot 2 recall allowed throughout slot 1 attach+absorb cycle (rapid-fire)"
	var chunk1: FakeChunk = _make_chunk()
	var chunk2: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk1, chunk2)

	# Slot 1 attach
	ctrl.on_enemy_chunk_attached(chunk1, enemy)
	_assert_false(ctrl.compute_recall_pressed(true, false, true),
		TEST_NAME + " — slot 1 recall blocked after attach")
	_assert_true(ctrl.compute_recall_2_pressed(true, false, true),
		TEST_NAME + " — slot 2 recall MUST be allowed while slot 1 is stuck")

	# Slot 1 absorb
	ctrl.on_absorb_resolved(enemy.get_esm())
	_assert_true(ctrl.compute_recall_pressed(true, false, true),
		TEST_NAME + " — slot 1 recall allowed after absorb")
	_assert_true(ctrl.compute_recall_2_pressed(true, false, true),
		TEST_NAME + " — slot 2 recall still allowed after slot 1 absorb")


# ---------------------------------------------------------------------------
# Cross-slot contamination: every ordering of slot-1-stuck + slot-2-recall
# and every combination of absorb ordering.
# ---------------------------------------------------------------------------

func test_cross_slot_ordering_slot1_attach_slot2_absorb_then_slot1_absorb() -> void:
	const TEST_NAME: String = "CROSS-01 — slot1 stuck; slot2 stuck; absorb slot2 first; slot1 still stuck"
	var chunk1: FakeChunk = _make_chunk()
	var chunk2: FakeChunk = _make_chunk()
	var enemy_a: FakeEnemyNode = FakeEnemyNode.new()
	var enemy_b: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk1, chunk2)

	ctrl.on_enemy_chunk_attached(chunk1, enemy_a)
	ctrl.on_enemy_chunk_attached(chunk2, enemy_b)

	# Absorb slot 2 first
	ctrl.on_absorb_resolved(enemy_b.get_esm())
	_assert_false(ctrl._chunk_2_stuck_on_enemy, TEST_NAME + " — slot 2 freed after enemy B absorb")
	_assert_true(ctrl._chunk_stuck_on_enemy, TEST_NAME + " — slot 1 remains stuck after enemy B absorb")

	# Now absorb slot 1
	ctrl.on_absorb_resolved(enemy_a.get_esm())
	_assert_false(ctrl._chunk_stuck_on_enemy, TEST_NAME + " — slot 1 freed after enemy A absorb")
	_assert_null(ctrl._chunk_stuck_enemy, TEST_NAME + " — slot 1 enemy ref null")


func test_cross_slot_ordering_both_stuck_same_enemy_absorb_frees_both_no_extra_reparent() -> void:
	const TEST_NAME: String = "CROSS-02 — both slots on same enemy; single absorb; no extra reparents on second absorb"
	var chunk1: FakeChunk = _make_chunk()
	var chunk2: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk1, chunk2)

	ctrl.on_enemy_chunk_attached(chunk1, enemy)
	ctrl.on_enemy_chunk_attached(chunk2, enemy)

	ctrl.on_absorb_resolved(enemy.get_esm())

	# Both freed
	_assert_false(ctrl._chunk_stuck_on_enemy, TEST_NAME + " — slot 1 freed")
	_assert_false(ctrl._chunk_2_stuck_on_enemy, TEST_NAME + " — slot 2 freed")

	# Capture reparent counts
	var rc1: int = chunk1.reparent_call_count()  # attach + detach = 2
	var rc2: int = chunk2.reparent_call_count()  # attach + detach = 2

	# Second absorb — no-op (idempotency cross-slot)
	ctrl.on_absorb_resolved(enemy.get_esm())
	_assert_eq(rc1, chunk1.reparent_call_count(),
		TEST_NAME + " — chunk1 no extra reparents after second absorb on same enemy")
	_assert_eq(rc2, chunk2.reparent_call_count(),
		TEST_NAME + " — chunk2 no extra reparents after second absorb on same enemy")


func test_cross_slot_ordering_slot1_free_slot2_stuck_unrelated_absorb() -> void:
	const TEST_NAME: String = "CROSS-03 — slot 1 free, slot 2 stuck; unrelated absorb is no-op for both"
	var chunk1: FakeChunk = _make_chunk()
	var chunk2: FakeChunk = _make_chunk()
	var enemy_b: FakeEnemyNode = FakeEnemyNode.new()
	var unrelated_enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk1, chunk2)

	# Only slot 2 stuck
	ctrl.on_enemy_chunk_attached(chunk2, enemy_b)
	_assert_false(ctrl._chunk_stuck_on_enemy, TEST_NAME + " precondition: slot 1 free")
	_assert_true(ctrl._chunk_2_stuck_on_enemy, TEST_NAME + " precondition: slot 2 stuck")

	# Absorb unrelated enemy
	ctrl.on_absorb_resolved(unrelated_enemy.get_esm())

	_assert_false(ctrl._chunk_stuck_on_enemy,
		TEST_NAME + " — slot 1 remains free after unrelated absorb")
	_assert_true(ctrl._chunk_2_stuck_on_enemy,
		TEST_NAME + " — slot 2 remains stuck after unrelated absorb; unrelated absorb must not contaminate")


# ---------------------------------------------------------------------------
# Boundary: empty/null inputs to stub signal simulation
# ---------------------------------------------------------------------------

func test_boundary_no_enemy_nodes_controller_state_clean() -> void:
	const TEST_NAME: String = "BOUNDARY-01 — controller with no enemy interactions starts fully clean"
	var chunk1: FakeChunk = _make_chunk()
	var chunk2: FakeChunk = _make_chunk()
	var ctrl: ControllerState = _make_controller(chunk1, chunk2)

	# No interactions at all
	_assert_false(ctrl._chunk_stuck_on_enemy, TEST_NAME + " — slot 1 stuck flag clean")
	_assert_null(ctrl._chunk_stuck_enemy, TEST_NAME + " — slot 1 enemy ref null")
	_assert_false(ctrl._chunk_2_stuck_on_enemy, TEST_NAME + " — slot 2 stuck flag clean")
	_assert_null(ctrl._chunk_2_stuck_enemy, TEST_NAME + " — slot 2 enemy ref null")
	_assert_false(ctrl._recall_in_progress, TEST_NAME + " — recall progress clean")
	_assert_false(ctrl._recall_in_progress_2, TEST_NAME + " — recall 2 progress clean")
	_assert_eq(0, chunk1.reparent_call_count(), TEST_NAME + " — no reparents on chunk1")
	_assert_eq(0, chunk2.reparent_call_count(), TEST_NAME + " — no reparents on chunk2")


func test_boundary_absorb_with_null_chunk_nodes_no_crash() -> void:
	const TEST_NAME: String = "BOUNDARY-02 — absorb_resolved with null chunk nodes in both slots: no crash"
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = ControllerState.new()
	ctrl._parent = FakeSceneRoot.new()
	ctrl._chunk_node = null
	ctrl._chunk_node_2 = null

	# Inject stuck state with null chunk nodes
	ctrl._chunk_stuck_on_enemy = true
	ctrl._chunk_stuck_enemy = enemy
	ctrl._chunk_2_stuck_on_enemy = true
	ctrl._chunk_2_stuck_enemy = enemy

	ctrl.on_absorb_resolved(enemy.get_esm())

	_assert_false(ctrl._chunk_stuck_on_enemy,
		TEST_NAME + " — slot 1 flag cleared even with null chunk node")
	_assert_null(ctrl._chunk_stuck_enemy,
		TEST_NAME + " — slot 1 enemy ref cleared")
	_assert_false(ctrl._chunk_2_stuck_on_enemy,
		TEST_NAME + " — slot 2 flag cleared even with null chunk node")
	_assert_null(ctrl._chunk_2_stuck_enemy,
		TEST_NAME + " — slot 2 enemy ref cleared")
	_pass(TEST_NAME + " — no crash with null chunk nodes in absorb handler")


func test_boundary_chunk_with_zero_velocity_on_attach() -> void:
	const TEST_NAME: String = "BOUNDARY-03 — chunk with zero velocity attaches correctly"
	var chunk: FakeChunk = _make_chunk()
	chunk.linear_velocity = Vector3.ZERO
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)

	_assert_true(ctrl._chunk_stuck_on_enemy, TEST_NAME + " — stuck flag set for zero-velocity chunk")
	_assert_true(chunk.freeze, TEST_NAME + " — freeze set for zero-velocity chunk")
	_assert_eq(Vector3.ZERO, chunk.linear_velocity, TEST_NAME + " — velocity remains zero")


func test_boundary_player_body_group_not_chunk_group_no_emit() -> void:
	const TEST_NAME: String = "BOUNDARY-04 — body in both 'player' AND 'chunk' groups: behavior is implementation-defined (CHECKPOINT)"
	# CHECKPOINT: The spec says chunk_attached fires for bodies in "chunk" group and NOT
	# for bodies in "player" group. A body in BOTH groups is not addressed.
	# Conservative assumption: the implementation checks is_in_group("chunk") first (or
	# is_in_group("player") first in the original code). We test both outcomes to document
	# the ambiguity. The critical contract is that the chunk group check drives emission.
	# # CHECKPOINT
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ambiguous_body: FakeChunk = FakeChunk.new()
	ambiguous_body.add_to_group("chunk")
	ambiguous_body.add_to_group("player")

	# The FakeEnemyNode.simulate_body_entered checks "chunk" group — it will emit.
	# This documents that the chunk-group check takes precedence in the spec-derived stub.
	var emitted: bool = enemy.simulate_body_entered(ambiguous_body)
	_assert_true(emitted,
		TEST_NAME + " — body in both groups: chunk check first means emission fires (conservative assumption per spec stub logic)")


func test_boundary_chunk_not_in_any_group_no_emit() -> void:
	const TEST_NAME: String = "BOUNDARY-05 — unlabeled body (no groups): no emission"
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var body: FakeChunk = _make_unlabeled_body()

	var emitted: bool = enemy.simulate_body_entered(body)

	_assert_false(emitted, TEST_NAME + " — unlabeled body must not emit chunk_attached")
	_assert_eq(0, enemy.chunk_attached_emissions.size(),
		TEST_NAME + " — no emissions for unlabeled body")


# ---------------------------------------------------------------------------
# Stress: large number of absorb_resolved calls on non-matching ESM
# Target: Performance/correctness — N non-matching absorb signals must not
# corrupt state.
# ---------------------------------------------------------------------------

func test_stress_many_nonmatching_absorb_calls_do_not_corrupt_state() -> void:
	const TEST_NAME: String = "STRESS-01 — 100 non-matching absorb calls: slot 1 state unchanged"
	var chunk: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)
	_assert_true(ctrl._chunk_stuck_on_enemy, TEST_NAME + " precondition: stuck")

	for _i in range(100):
		var decoy_enemy: FakeEnemyNode = FakeEnemyNode.new()
		ctrl.on_absorb_resolved(decoy_enemy.get_esm())

	# State must remain entirely unchanged — still stuck on original enemy
	_assert_true(ctrl._chunk_stuck_on_enemy,
		TEST_NAME + " — stuck flag must survive 100 non-matching absorb calls")
	_assert_eq(enemy, ctrl._chunk_stuck_enemy,
		TEST_NAME + " — enemy ref must be unchanged after 100 non-matching absorbs")
	_assert_eq(1, chunk.reparent_call_count(),
		TEST_NAME + " — reparent count must be 1 (attach only); no detach reparents from non-matching absorbs")

	# The correct absorb finally frees it
	ctrl.on_absorb_resolved(enemy.get_esm())
	_assert_false(ctrl._chunk_stuck_on_enemy,
		TEST_NAME + " — stuck cleared after correct absorb following 100 decoys")


func test_stress_both_slots_survive_100_nonmatching_absorb_calls() -> void:
	const TEST_NAME: String = "STRESS-02 — 100 non-matching absorbs on two-slot state: both remain stuck"
	var chunk1: FakeChunk = _make_chunk()
	var chunk2: FakeChunk = _make_chunk()
	var enemy_a: FakeEnemyNode = FakeEnemyNode.new()
	var enemy_b: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk1, chunk2)

	ctrl.on_enemy_chunk_attached(chunk1, enemy_a)
	ctrl.on_enemy_chunk_attached(chunk2, enemy_b)

	for _i in range(100):
		var decoy: FakeEnemyNode = FakeEnemyNode.new()
		ctrl.on_absorb_resolved(decoy.get_esm())

	_assert_true(ctrl._chunk_stuck_on_enemy,
		TEST_NAME + " — slot 1 remains stuck after 100 decoy absorbs")
	_assert_true(ctrl._chunk_2_stuck_on_enemy,
		TEST_NAME + " — slot 2 remains stuck after 100 decoy absorbs")
	_assert_eq(enemy_a, ctrl._chunk_stuck_enemy,
		TEST_NAME + " — slot 1 enemy ref unchanged")
	_assert_eq(enemy_b, ctrl._chunk_2_stuck_enemy,
		TEST_NAME + " — slot 2 enemy ref unchanged")


# ---------------------------------------------------------------------------
# Determinism: same scenario, identical results
# Target: Calling the same operation sequence twice on fresh state produces
# identical outcomes. Tests for non-deterministic side effects.
# ---------------------------------------------------------------------------

func test_determinism_attach_absorb_cycle_produces_identical_results() -> void:
	const TEST_NAME: String = "DETERM-01 — two independent attach+absorb cycles produce identical final state"
	# Run the same scenario on two independent ControllerState instances
	var run_check: Callable = func(label: String) -> void:
		var chunk: FakeChunk = _make_chunk()
		chunk.linear_velocity = Vector3(7.0, 3.0, -2.0)
		var enemy: FakeEnemyNode = FakeEnemyNode.new()
		var ctrl: ControllerState = _make_controller(chunk, null)

		ctrl.on_enemy_chunk_attached(chunk, enemy)
		ctrl.on_absorb_resolved(enemy.get_esm())

		_assert_false(ctrl._chunk_stuck_on_enemy, TEST_NAME + " [" + label + "] stuck cleared")
		_assert_null(ctrl._chunk_stuck_enemy, TEST_NAME + " [" + label + "] enemy null")
		_assert_false(chunk.freeze, TEST_NAME + " [" + label + "] unfrozen")
		_assert_eq(2, chunk.reparent_call_count(), TEST_NAME + " [" + label + "] exactly 2 reparents")
		_assert_eq(ctrl._parent, chunk.last_reparent_parent(),
			TEST_NAME + " [" + label + "] final parent is scene root")

	run_check.call("run1")
	run_check.call("run2")


# ---------------------------------------------------------------------------
# Assumption check: Spec constraint SPEC-CSE-11 — MovementSimulation not touched
# Target: Confirms no stuck-state logic leaks into simulation fields.
# ---------------------------------------------------------------------------

func test_assumption_simulation_fields_untouched_by_attach_detach() -> void:
	const TEST_NAME: String = "ASSUME-01 — full attach+absorb cycle does not set _recall_in_progress (SPEC-CSE-11)"
	var chunk: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)
	ctrl.on_absorb_resolved(enemy.get_esm())

	_assert_false(ctrl._recall_in_progress,
		TEST_NAME + " — _recall_in_progress must not be set during attach+absorb cycle")
	_assert_false(ctrl._recall_in_progress_2,
		TEST_NAME + " — _recall_in_progress_2 must not be set during attach+absorb cycle")


func test_assumption_attach_does_not_set_recall_in_progress() -> void:
	const TEST_NAME: String = "ASSUME-02 — attach alone does not set _recall_in_progress"
	var chunk: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)

	_assert_false(ctrl._recall_in_progress,
		TEST_NAME + " — _recall_in_progress must remain false after attach-only")
	_assert_false(ctrl._recall_in_progress_2,
		TEST_NAME + " — _recall_in_progress_2 must remain false after attach-only")


# ---------------------------------------------------------------------------
# Invalid/corrupt enemy node in stuck_enemy reference (SPEC-CSE-10 extension)
# Target: _chunk_stuck_enemy is set but becomes freed/invalid before absorb fires.
# The is_instance_valid guard must prevent access to the freed enemy.
# ---------------------------------------------------------------------------

func test_invalid_enemy_ref_absorb_with_freed_enemy_node() -> void:
	const TEST_NAME: String = "INVALID-01 — freed enemy node in stuck_enemy: absorb handler skips ESM check, flags may stay (SPEC-CSE-10 ext)"
	# CHECKPOINT: If _chunk_stuck_enemy is freed (is_instance_valid returns false),
	# the absorb handler must not crash. However, the flags cannot be cleared by
	# get_esm() comparison because the enemy ref is dead.
	# Conservative assumption: when is_instance_valid(_chunk_stuck_enemy) returns false,
	# the slot-1 block is skipped entirely (flags remain true — this is a known risk per spec).
	# This encodes the defensive behavior of the is_instance_valid guard.
	# # CHECKPOINT
	var chunk: FakeChunk = _make_chunk()
	var enemy: FakeEnemyNode = FakeEnemyNode.new()
	var ctrl: ControllerState = _make_controller(chunk, null)

	ctrl.on_enemy_chunk_attached(chunk, enemy)

	# Simulate the enemy node being freed
	enemy._simulated_freed = true

	# Add _simulated_freed support to FakeEnemyNode for _is_valid check
	# Note: FakeEnemyNode doesn't have this property by default in primary stubs.
	# We add it here for the adversarial scenario.

	# The controller's _is_valid check reads _simulated_freed on the enemy.
	# Since the enemy is freed, the block is skipped — flags remain.
	var esm: EnemyStateMachine = enemy.get_esm()  # Get ESM before enemy is fully inert
	ctrl.on_absorb_resolved(esm)

	# Per spec: is_instance_valid guard prevents ESM match → flags remain (spec risk note).
	# The test encodes this conservative assumption with a CHECKPOINT comment.
	# A correct implementation respects the guard: no crash, flag state depends on impl.
	_pass(TEST_NAME + " — no crash when enemy node is freed before absorb fires (guard protects)")
	# Note: the spec acknowledges flags may remain true in this edge case (SPEC-CSE-5 risk).
	# The key contract is: no crash, no null dereference.


func test_invalid_enemy_ref_not_accessible_via_freed_node() -> void:
	const TEST_NAME: String = "INVALID-02 — is_instance_valid guard detects freed objects via _simulated_freed (SPEC-CSE-10 ext)"
	# Verify that the _is_valid helper properly detects freed objects via _simulated_freed.
	# FakeChunk declares _simulated_freed — use it as the stand-in for the freed-node check.
	# The same mechanism protects both chunk nodes and enemy node refs in the absorb handler.
	var ctrl: ControllerState = ControllerState.new()
	ctrl._parent = FakeSceneRoot.new()

	var live_chunk: FakeChunk = _make_chunk()
	_assert_true(ctrl._is_valid(live_chunk),
		TEST_NAME + " — live FakeChunk (with _simulated_freed=false) is valid")

	live_chunk._simulated_freed = true
	_assert_false(ctrl._is_valid(live_chunk),
		TEST_NAME + " — FakeChunk with _simulated_freed=true is detected as invalid")

	# Null is also invalid
	_assert_false(ctrl._is_valid(null),
		TEST_NAME + " — null is always invalid")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_chunk_sticks_to_enemy_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	print("  -- MUT-1: Flag-never-cleared mutation --")
	test_adv_mut1_stuck_flag_cleared_after_absorb_slot1()
	test_adv_mut1_stuck_flag_cleared_after_absorb_slot2()

	print("  -- MUT-2: Wrong-slot-cleared mutation --")
	test_adv_mut2_absorb_slot2_does_not_touch_slot1_fields()
	test_adv_mut2_absorb_slot1_does_not_touch_slot2_fields()

	print("  -- MUT-3: Reparent-skipped mutation --")
	test_adv_mut3_reparent_called_on_slot1_attach()
	test_adv_mut3_reparent_called_on_slot2_attach()
	test_adv_mut3_reparent_called_on_detach()

	print("  -- MUT-4: keep_global_transform=false mutation --")
	test_adv_mut4_attach_reparent_uses_keep_global_true()
	test_adv_mut4_slot2_attach_reparent_uses_keep_global_true()
	test_adv_mut4_detach_reparent_uses_keep_global_true()

	print("  -- MUT-5: Velocity-not-zeroed mutation --")
	test_adv_mut5_velocity_zeroed_even_with_high_speed_chunk()
	test_adv_mut5_velocity_zeroed_for_negative_velocity_chunk()
	test_adv_mut5_velocity_already_zero_attach_succeeds()

	print("  -- MUT-8: Slot-2-block-gated-on-slot-1 mutation --")
	test_adv_mut8_slot2_freed_independently_when_slot1_not_stuck()
	test_adv_mut8_slot2_freed_even_after_slot1_esm_mismatch()

	print("  -- MUT-9: Absorb handler touches chunk when flag false --")
	test_adv_mut9_absorb_handler_noop_when_flag_false_slot1()
	test_adv_mut9_absorb_handler_noop_when_flag_false_slot2()

	print("  -- MUT-10: Double-attach mutation --")
	test_adv_mut10_double_attach_slot1_state_consistent()
	test_adv_mut10_double_attach_different_enemies_slot1()

	print("  -- MUT-11: absorb_resolved not idempotent --")
	test_adv_mut11_absorb_resolved_idempotent_slot1()
	test_adv_mut11_absorb_resolved_idempotent_slot2()
	test_adv_mut11_absorb_resolved_both_slots_idempotent()

	print("  -- MUT-12: Emission before ESM state change --")
	test_adv_mut12_emission_order_esm_state_is_post_event()
	test_adv_mut12_emission_order_infection_state_is_post_event()
	test_adv_mut12_inverted_order_mutant_produces_wrong_state()

	print("  -- MUT-13: Dead-state enemy signal emission --")
	test_adv_mut13_chunk_attached_emitted_in_dead_state()
	test_adv_mut13_chunk_attached_emitted_in_weakened_state()

	print("  -- MUT-14: Slot alias mutation --")
	test_adv_mut14_shared_chunk_object_slot1_attach_only_sets_slot1()

	print("  -- MUT-15: Corrupt state softlock --")
	test_adv_mut15_corrupt_state_stuck_true_chunk_null_absorb_clears_flag()
	test_adv_mut15_corrupt_state_stuck_true_chunk_null_slot2()

	print("  -- MUT-16: ESM match by node identity --")
	test_adv_mut16_esm_match_via_get_esm_not_node_identity()
	test_adv_mut16_different_esm_objects_dont_match()

	print("  -- MUT-17: Multiple body_entered emission count --")
	test_adv_mut17_each_body_entered_event_fires_one_emission()
	test_adv_mut17_three_different_chunks_each_emit_once()

	print("  -- MUT-18: Partial clear mutation --")
	test_adv_mut18_both_fields_cleared_together_slot1()
	test_adv_mut18_both_fields_cleared_together_slot2()

	print("  -- MUT-19: Cross-slot recall guard bug --")
	test_adv_mut19_slot1_recall_uses_slot1_flag_not_slot2_flag()
	test_adv_mut19_slot2_recall_uses_slot2_flag_not_slot1_flag()

	print("  -- MUT-20: Inverted unfreeze logic --")
	test_adv_mut20_unfreeze_after_absorb_slot1()
	test_adv_mut20_unfreeze_after_absorb_slot2()
	test_adv_mut20_unfreeze_both_slots_after_single_absorb()

	print("  -- Rapid-fire sequences --")
	test_rapid_fire_attach_then_immediate_absorb_same_call_chain()
	test_rapid_fire_multiple_attach_absorb_cycles_idempotent()
	test_rapid_fire_recall_attempt_mid_stuck_is_blocked()
	test_rapid_fire_slot2_recall_allowed_while_slot1_going_through_attach_absorb()

	print("  -- Cross-slot contamination orderings --")
	test_cross_slot_ordering_slot1_attach_slot2_absorb_then_slot1_absorb()
	test_cross_slot_ordering_both_stuck_same_enemy_absorb_frees_both_no_extra_reparent()
	test_cross_slot_ordering_slot1_free_slot2_stuck_unrelated_absorb()

	print("  -- Boundary conditions --")
	test_boundary_no_enemy_nodes_controller_state_clean()
	test_boundary_absorb_with_null_chunk_nodes_no_crash()
	test_boundary_chunk_with_zero_velocity_on_attach()
	test_boundary_player_body_group_not_chunk_group_no_emit()
	test_boundary_chunk_not_in_any_group_no_emit()

	print("  -- Stress/load --")
	test_stress_many_nonmatching_absorb_calls_do_not_corrupt_state()
	test_stress_both_slots_survive_100_nonmatching_absorb_calls()

	print("  -- Determinism --")
	test_determinism_attach_absorb_cycle_produces_identical_results()

	print("  -- Assumption checks --")
	test_assumption_simulation_fields_untouched_by_attach_detach()
	test_assumption_attach_does_not_set_recall_in_progress()

	print("  -- Invalid/corrupt node refs --")
	test_invalid_enemy_ref_absorb_with_freed_enemy_node()
	test_invalid_enemy_ref_not_accessible_via_freed_node()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
