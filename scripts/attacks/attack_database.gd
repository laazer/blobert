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

# --- Fused attack constants: acid_claw (101) ---
const ACID_CLAW_ATTACK_ID := 101
const ACID_CLAW_DAMAGE := 1.8
const ACID_CLAW_COOLDOWN := 2.0
const ACID_CLAW_RANGE := 1.2
const ACID_CLAW_KNOCKBACK := 80.0
const ACID_CLAW_VFX_SCALE := 1.3
const ACID_CLAW_ACID_DURATION := 2.5
const ACID_CLAW_ACID_DPS := 0.4
const ACID_CLAW_COMBO_HITS := 3
const ACID_CLAW_COMBO_FRAME_INTERVAL := 6

# --- Fused attack constants: adhesion_claw (102) ---
const ADHESION_CLAW_ATTACK_ID := 102
const ADHESION_CLAW_DAMAGE := 3.5
const ADHESION_CLAW_COOLDOWN := 2.0
const ADHESION_CLAW_RANGE := 1.5
const ADHESION_CLAW_KNOCKBACK := 1.0
const ADHESION_CLAW_VFX_SCALE := 1.2
const ADHESION_CLAW_SLOW_DURATION := 2.0

# --- Fused attack constants: carapace_claw (103) ---
const CARAPACE_CLAW_ATTACK_ID := 103
const CARAPACE_CLAW_DAMAGE := 5.0
const CARAPACE_CLAW_COOLDOWN := 3.0
const CARAPACE_CLAW_RANGE := 2.5
const CARAPACE_CLAW_KNOCKBACK := 6.0
const CARAPACE_CLAW_STARTUP_FRAMES := 8
const CARAPACE_CLAW_VFX_SCALE := 1.5

# --- Fused attack constants: acid_adhesion (104) ---
const ACID_ADHESION_ATTACK_ID := 104
const ACID_ADHESION_DAMAGE := 2.0
const ACID_ADHESION_COOLDOWN := 3.0
const ACID_ADHESION_PROJECTILE_SPEED := 10.0
const ACID_ADHESION_PROJECTILE_LIFETIME := 1.75
const ACID_ADHESION_VFX_SCALE := 1.2
const ACID_ADHESION_SLOW_DURATION := 2.5
const ACID_ADHESION_ACID_DURATION := 3.0
const ACID_ADHESION_ACID_DPS := 1.2

# --- Fused attack constants: acid_carapace (105) ---
const ACID_CARAPACE_ATTACK_ID := 105
const ACID_CARAPACE_DAMAGE := 4.5
const ACID_CARAPACE_COOLDOWN := 4.0
const ACID_CARAPACE_RANGE := 3.5
const ACID_CARAPACE_KNOCKBACK := 4.0
const ACID_CARAPACE_STARTUP_FRAMES := 12
const ACID_CARAPACE_VFX_SCALE := 1.8
const ACID_CARAPACE_ACID_DURATION := 2.5
const ACID_CARAPACE_ACID_DPS := 0.6

# --- Fused attack constants: adhesion_carapace (106) ---
const ADHESION_CARAPACE_ATTACK_ID := 106
const ADHESION_CARAPACE_DAMAGE := 3.5
const ADHESION_CARAPACE_COOLDOWN := 3.5
const ADHESION_CARAPACE_RANGE := 3.0
const ADHESION_CARAPACE_KNOCKBACK := 2.0
const ADHESION_CARAPACE_STARTUP_FRAMES := 12
const ADHESION_CARAPACE_VFX_SCALE := 1.6
const ADHESION_CARAPACE_SLOW_DURATION := 2.0

const ACID_CLAW_COLOR := Color(0.6, 0.85, 0.0)
const ADHESION_CLAW_COLOR := Color(0.85, 0.65, 0.0)
const CARAPACE_CLAW_COLOR := Color(0.65, 0.35, 0.05)
const ACID_ADHESION_COLOR := Color(0.3, 0.75, 0.1)
const ACID_CARAPACE_COLOR := Color(0.4, 0.65, 0.05)
const ADHESION_CARAPACE_COLOR := Color(0.55, 0.45, 0.1)

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
	_register_fused_defaults()


func _register_fused_defaults() -> void:
	var acid_claw_attack := AttackResource.new()
	acid_claw_attack.attack_id = ACID_CLAW_ATTACK_ID
	acid_claw_attack.attack_name = "Venomous Shred"
	acid_claw_attack.description = "Rapid 3-hit melee combo. Each hit applies an independent acid DoT stack."
	acid_claw_attack.effect_type = "MELEE_SWIPE_COMBO"
	acid_claw_attack.damage = ACID_CLAW_DAMAGE
	acid_claw_attack.cooldown = ACID_CLAW_COOLDOWN
	acid_claw_attack.attack_range = ACID_CLAW_RANGE
	acid_claw_attack.startup_frames = 0
	acid_claw_attack.combo_hits = ACID_CLAW_COMBO_HITS
	acid_claw_attack.knockback_magnitude = ACID_CLAW_KNOCKBACK
	acid_claw_attack.knockback_direction = "away"
	acid_claw_attack.projectile_speed = 0.0
	acid_claw_attack.projectile_lifetime = 0.0
	acid_claw_attack.color = ACID_CLAW_COLOR
	acid_claw_attack.vfx_scale = ACID_CLAW_VFX_SCALE
	acid_claw_attack.modifiers = {
		"acid_on_hit": true,
		"acid_duration": ACID_CLAW_ACID_DURATION,
		"acid_dps": ACID_CLAW_ACID_DPS,
		"combo_frame_interval": ACID_CLAW_COMBO_FRAME_INTERVAL,
	}
	register_fused_attack("acid", "claw", acid_claw_attack)

	var adhesion_claw_attack := AttackResource.new()
	adhesion_claw_attack.attack_id = ADHESION_CLAW_ATTACK_ID
	adhesion_claw_attack.attack_name = "Sticky Slash"
	adhesion_claw_attack.description = "Melee swipe that roots the target on contact."
	adhesion_claw_attack.effect_type = "MELEE_SWIPE"
	adhesion_claw_attack.damage = ADHESION_CLAW_DAMAGE
	adhesion_claw_attack.cooldown = ADHESION_CLAW_COOLDOWN
	adhesion_claw_attack.attack_range = ADHESION_CLAW_RANGE
	adhesion_claw_attack.startup_frames = 0
	adhesion_claw_attack.knockback_magnitude = ADHESION_CLAW_KNOCKBACK
	adhesion_claw_attack.knockback_direction = "away"
	adhesion_claw_attack.projectile_speed = 0.0
	adhesion_claw_attack.projectile_lifetime = 0.0
	adhesion_claw_attack.color = ADHESION_CLAW_COLOR
	adhesion_claw_attack.vfx_scale = ADHESION_CLAW_VFX_SCALE
	adhesion_claw_attack.modifiers = {"slow": 0.0, "slow_duration": ADHESION_CLAW_SLOW_DURATION}
	register_fused_attack("adhesion", "claw", adhesion_claw_attack)

	var carapace_claw_attack := AttackResource.new()
	carapace_claw_attack.attack_id = CARAPACE_CLAW_ATTACK_ID
	carapace_claw_attack.attack_name = "Armored Slam"
	carapace_claw_attack.description = "Powerful melee slam in a wider arc. Infects weakened enemies."
	carapace_claw_attack.effect_type = "SLAM_AOE"
	carapace_claw_attack.damage = CARAPACE_CLAW_DAMAGE
	carapace_claw_attack.cooldown = CARAPACE_CLAW_COOLDOWN
	carapace_claw_attack.attack_range = CARAPACE_CLAW_RANGE
	carapace_claw_attack.startup_frames = CARAPACE_CLAW_STARTUP_FRAMES
	carapace_claw_attack.knockback_magnitude = CARAPACE_CLAW_KNOCKBACK
	carapace_claw_attack.knockback_direction = "away"
	carapace_claw_attack.projectile_speed = 0.0
	carapace_claw_attack.projectile_lifetime = 0.0
	carapace_claw_attack.color = CARAPACE_CLAW_COLOR
	carapace_claw_attack.vfx_scale = CARAPACE_CLAW_VFX_SCALE
	carapace_claw_attack.modifiers = {"infect_weakened": true}
	register_fused_attack("carapace", "claw", carapace_claw_attack)

	var acid_adhesion_attack := AttackResource.new()
	acid_adhesion_attack.attack_id = ACID_ADHESION_ATTACK_ID
	acid_adhesion_attack.attack_name = "Venom Web"
	acid_adhesion_attack.description = "Sticky acid projectile. Roots first target and applies acid."
	acid_adhesion_attack.effect_type = "PROJECTILE_SPIT"
	acid_adhesion_attack.damage = ACID_ADHESION_DAMAGE
	acid_adhesion_attack.cooldown = ACID_ADHESION_COOLDOWN
	acid_adhesion_attack.attack_range = 0.0
	acid_adhesion_attack.startup_frames = 0
	acid_adhesion_attack.knockback_magnitude = 0.0
	acid_adhesion_attack.knockback_direction = "none"
	acid_adhesion_attack.projectile_speed = ACID_ADHESION_PROJECTILE_SPEED
	acid_adhesion_attack.projectile_lifetime = ACID_ADHESION_PROJECTILE_LIFETIME
	acid_adhesion_attack.color = ACID_ADHESION_COLOR
	acid_adhesion_attack.vfx_scale = ACID_ADHESION_VFX_SCALE
	acid_adhesion_attack.modifiers = {
		"acid_on_hit": true,
		"acid_duration": ACID_ADHESION_ACID_DURATION,
		"acid_dps": ACID_ADHESION_ACID_DPS,
		"slow": 0.0,
		"slow_duration": ACID_ADHESION_SLOW_DURATION,
	}
	register_fused_attack("acid", "adhesion", acid_adhesion_attack)

	var acid_carapace_attack := AttackResource.new()
	acid_carapace_attack.attack_id = ACID_CARAPACE_ATTACK_ID
	acid_carapace_attack.attack_name = "Corrosive Slam"
	acid_carapace_attack.description = "Ground slam that coats the impact zone with acid."
	acid_carapace_attack.effect_type = "SLAM_AOE"
	acid_carapace_attack.damage = ACID_CARAPACE_DAMAGE
	acid_carapace_attack.cooldown = ACID_CARAPACE_COOLDOWN
	acid_carapace_attack.attack_range = ACID_CARAPACE_RANGE
	acid_carapace_attack.startup_frames = ACID_CARAPACE_STARTUP_FRAMES
	acid_carapace_attack.knockback_magnitude = ACID_CARAPACE_KNOCKBACK
	acid_carapace_attack.knockback_direction = "away"
	acid_carapace_attack.projectile_speed = 0.0
	acid_carapace_attack.projectile_lifetime = 0.0
	acid_carapace_attack.color = ACID_CARAPACE_COLOR
	acid_carapace_attack.vfx_scale = ACID_CARAPACE_VFX_SCALE
	acid_carapace_attack.modifiers = {
		"acid_on_hit": true,
		"acid_duration": ACID_CARAPACE_ACID_DURATION,
		"acid_dps": ACID_CARAPACE_ACID_DPS,
	}
	register_fused_attack("acid", "carapace", acid_carapace_attack)

	var adhesion_carapace_attack := AttackResource.new()
	adhesion_carapace_attack.attack_id = ADHESION_CARAPACE_ATTACK_ID
	adhesion_carapace_attack.attack_name = "Web Slam"
	adhesion_carapace_attack.description = "Ground slam that roots all enemies in the impact zone."
	adhesion_carapace_attack.effect_type = "SLAM_AOE"
	adhesion_carapace_attack.damage = ADHESION_CARAPACE_DAMAGE
	adhesion_carapace_attack.cooldown = ADHESION_CARAPACE_COOLDOWN
	adhesion_carapace_attack.attack_range = ADHESION_CARAPACE_RANGE
	adhesion_carapace_attack.startup_frames = ADHESION_CARAPACE_STARTUP_FRAMES
	adhesion_carapace_attack.knockback_magnitude = ADHESION_CARAPACE_KNOCKBACK
	adhesion_carapace_attack.knockback_direction = "away"
	adhesion_carapace_attack.projectile_speed = 0.0
	adhesion_carapace_attack.projectile_lifetime = 0.0
	adhesion_carapace_attack.color = ADHESION_CARAPACE_COLOR
	adhesion_carapace_attack.vfx_scale = ADHESION_CARAPACE_VFX_SCALE
	adhesion_carapace_attack.modifiers = {"slow": 0.0, "slow_duration": ADHESION_CARAPACE_SLOW_DURATION}
	register_fused_attack("adhesion", "carapace", adhesion_carapace_attack)


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
