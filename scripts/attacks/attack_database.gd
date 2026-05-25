class_name AttackDatabaseNode
extends Node

var _base_attacks: Dictionary = {}
var _fused_attacks: Dictionary = {}


func register_base_attack(mutation_id: String, resource: AttackResource) -> void:
	if mutation_id == "":
		push_warning("AttackDatabase: cannot register base attack with empty mutation_id")
		return
	if resource == null:
		push_warning(
			"AttackDatabase: cannot register null resource for mutation_id '%s'" % mutation_id
		)
		return
	_base_attacks[mutation_id] = resource


func get_base_attack(mutation_id: String) -> AttackResource:
	if mutation_id in _base_attacks:
		return _base_attacks[mutation_id]
	push_warning("AttackDatabase: no base attack found for mutation_id '%s'" % mutation_id)
	return null


func register_fused_attack(
	slot_a_id: String, slot_b_id: String, resource: AttackResource
) -> void:
	if slot_a_id == "" or slot_b_id == "":
		push_warning("AttackDatabase: cannot register fused attack with empty slot id")
		return
	if slot_a_id == slot_b_id:
		push_warning(
			"AttackDatabase: fused attack requires two different mutations, got '%s'" % slot_a_id
		)
		return
	if resource == null:
		push_warning("AttackDatabase: cannot register null fused resource")
		return
	var key: String = _make_fused_key(slot_a_id, slot_b_id)
	_fused_attacks[key] = resource


func get_fused_attack(slot_a_id: String, slot_b_id: String) -> AttackResource:
	var key: String = _make_fused_key(slot_a_id, slot_b_id)
	if key in _fused_attacks:
		return _fused_attacks[key]
	push_warning(
		"AttackDatabase: no fused attack found for combo '%s' + '%s'" % [slot_a_id, slot_b_id]
	)
	return null


func has_base_attack(mutation_id: String) -> bool:
	return mutation_id in _base_attacks


func get_base_attack_count() -> int:
	return _base_attacks.size()


func get_fused_attack_count() -> int:
	return _fused_attacks.size()


func clear() -> void:
	_base_attacks.clear()
	_fused_attacks.clear()


func _make_fused_key(id_a: String, id_b: String) -> String:
	var pair: Array = [id_a, id_b]
	pair.sort()
	return "%s_%s" % [pair[0], pair[1]]
