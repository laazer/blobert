class_name AttackDatabaseNode
extends Node

const CLAW_DAMAGE := 3.0
const CLAW_COOLDOWN := 0.8
const CLAW_RANGE := 1.5
const CLAW_KNOCKBACK := 2.0
const CLAW_VFX_SCALE := 1.2

const ACID_DAMAGE := 1.0
const ACID_COOLDOWN := 2.0
const ACID_PROJECTILE_SPEED := 8.0
const ACID_PROJECTILE_LIFETIME := 2.0
const ACID_DPS := 1.0
const ACID_DURATION := 3.0

const CARAPACE_ATTACK_ID := 3
const CARAPACE_DAMAGE := 4.0
const CARAPACE_COOLDOWN := 3.5
const CARAPACE_RANGE := 3.0
const CARAPACE_KNOCKBACK := 5.0
const CARAPACE_STARTUP_FRAMES := 12
const CARAPACE_VFX_SCALE := 1.5

const ADHESION_ATTACK_ID := 4
const ADHESION_DAMAGE := 1.0
const ADHESION_COOLDOWN := 2.5
const ADHESION_PROJECTILE_SPEED := 8.0
const ADHESION_PROJECTILE_LIFETIME := 1.25
const ADHESION_ROOT_DURATION := 3.0

var _base_attacks: Dictionary = {}
var _fused_attacks: Dictionary = {}


func _ready() -> void:
	_register_defaults()


func _register_defaults() -> void:
	var claw := AttackResource.new()
	claw.attack_id = 1
	claw.attack_name = "Claw Swipe"
	claw.description = "Fast melee swipe with short cooldown. Infects weakened enemies."
	claw.effect_type = "MELEE_SWIPE"
	claw.damage = CLAW_DAMAGE
	claw.cooldown = CLAW_COOLDOWN
	claw.attack_range = CLAW_RANGE
	claw.startup_frames = 0
	claw.knockback_magnitude = CLAW_KNOCKBACK
	claw.knockback_direction = "away"
	claw.color = Color.ORANGE_RED
	claw.vfx_scale = CLAW_VFX_SCALE
	claw.modifiers = {"infect_weakened": true}
	register_base_attack("claw", claw)

	var acid := AttackResource.new()
	acid.attack_id = 2
	acid.attack_name = "Acid Spit"
	acid.description = "Ranged acid projectile. Applies damage over time. WEAKENED enemies suffer double duration."
	acid.effect_type = "PROJECTILE_SPIT"
	acid.damage = ACID_DAMAGE
	acid.cooldown = ACID_COOLDOWN
	acid.attack_range = 0.0
	acid.startup_frames = 0
	acid.knockback_magnitude = 0.0
	acid.knockback_direction = "none"
	acid.projectile_speed = ACID_PROJECTILE_SPEED
	acid.projectile_lifetime = ACID_PROJECTILE_LIFETIME
	acid.color = Color.CHARTREUSE
	acid.vfx_scale = 1.0
	acid.modifiers = {"acid_on_hit": true, "acid_duration": ACID_DURATION, "acid_dps": ACID_DPS}
	register_base_attack("acid", acid)

	var carapace := AttackResource.new()
	carapace.attack_id = CARAPACE_ATTACK_ID
	carapace.attack_name = "Ground Slam"
	carapace.description = "Heavy ground slam. Damages and knocks back all enemies in radius. Slams on landing if airborne."
	carapace.effect_type = "SLAM_AOE"
	carapace.damage = CARAPACE_DAMAGE
	carapace.cooldown = CARAPACE_COOLDOWN
	carapace.attack_range = CARAPACE_RANGE
	carapace.startup_frames = CARAPACE_STARTUP_FRAMES
	carapace.knockback_magnitude = CARAPACE_KNOCKBACK
	carapace.knockback_direction = "away"
	carapace.color = Color.SADDLE_BROWN
	carapace.vfx_scale = CARAPACE_VFX_SCALE
	carapace.modifiers = {}
	register_base_attack("carapace", carapace)

	var adhesion := AttackResource.new()
	adhesion.attack_id = ADHESION_ATTACK_ID
	adhesion.attack_name = "Sticky Spit"
	adhesion.description = "Sticky projectile that roots the first enemy hit, stopping all movement for 3.0s."
	adhesion.effect_type = "PROJECTILE_SPIT"
	adhesion.damage = ADHESION_DAMAGE
	adhesion.cooldown = ADHESION_COOLDOWN
	adhesion.attack_range = 0.0
	adhesion.startup_frames = 0
	adhesion.knockback_magnitude = 0.0
	adhesion.knockback_direction = "none"
	adhesion.projectile_speed = ADHESION_PROJECTILE_SPEED
	adhesion.projectile_lifetime = ADHESION_PROJECTILE_LIFETIME
	adhesion.color = Color.DARK_GOLDENROD
	adhesion.vfx_scale = 1.0
	adhesion.modifiers = {"slow": 0.0, "slow_duration": ADHESION_ROOT_DURATION}
	register_base_attack("adhesion", adhesion)


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
