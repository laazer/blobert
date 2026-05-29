# slime_visual_state.gd
# Fusion active color feedback for the player's SlimeVisual node.
# Tints the mesh bright orange with emission while a fused mutation is active
# (PlayerController3D.is_fusion_active() == true), reverts to the mesh baseline otherwise.
#
# Attach to: SlimeVisual (Node3D), direct child of PlayerController3D.
# Resolves MeshInstance3D as direct child "MeshInstance3D" (procedural slime) or the first
# MeshInstance3D under this node (e.g. imported player GLB).

class_name SlimeVisualState
extends Node3D

const COLOR_BASELINE = Color(0.4, 0.9, 0.6, 1.0)
const COLOR_MUTATION_TINT = Color(1.0, 0.15, 0.0, 1.0)
const COLOR_MUTATION_EMISSION = Color(0.8, 0.1, 0.0, 1.0)

var _mesh: MeshInstance3D = null
var _mesh_ready: bool = false
var _material: StandardMaterial3D = null
var _player: Object = null  # PlayerController3D, resolved lazily in _process
var _current_tinted: bool = false
var _baseline_albedo: Color = COLOR_BASELINE
var _baseline_emission_enabled: bool = false
var _baseline_emission: Color = Color.BLACK
var _baseline_emission_energy: float = 1.0


func _ready() -> void:
	_mesh = _resolve_tint_mesh()
	if _mesh == null:
		push_error("SlimeVisualState: no MeshInstance3D found — color feedback disabled")
		return
	if not _bind_first_standard_material(_mesh):
		push_error(
			"SlimeVisualState: no StandardMaterial3D on MeshInstance3D — color feedback disabled"
		)
		return
	_baseline_albedo = _material.albedo_color
	_baseline_emission_enabled = _material.emission_enabled
	_baseline_emission = _material.emission
	_baseline_emission_energy = _material.emission_energy_multiplier
	_mesh_ready = true
	_player = get_parent()


func _resolve_tint_mesh() -> MeshInstance3D:
	var direct: MeshInstance3D = get_node_or_null("MeshInstance3D") as MeshInstance3D
	if direct != null and direct.visible:
		return direct
	var fallback: MeshInstance3D = direct
	for n: Node in find_children("*", "MeshInstance3D", true, false):
		var mi: MeshInstance3D = n as MeshInstance3D
		if mi != null and mi.visible:
			return mi
	return fallback


func _bind_first_standard_material(mi: MeshInstance3D) -> bool:
	if mi.material_override is StandardMaterial3D:
		_material = (mi.material_override as StandardMaterial3D).duplicate() as StandardMaterial3D
		mi.material_override = _material
		return _material != null
	if mi.mesh != null:
		for si in mi.mesh.get_surface_count():
			var am: Material = mi.get_active_material(si)
			if am is StandardMaterial3D:
				_material = (am as StandardMaterial3D).duplicate() as StandardMaterial3D
				mi.set_surface_override_material(si, _material)
				return _material != null
	return false


func _process(_delta: float) -> void:
	if not _mesh_ready or not is_instance_valid(_mesh):
		return
	if _player == null or not is_instance_valid(_player):
		_player = get_parent()
	if _player == null or not _player.has_method("is_fusion_active"):
		return
	var should_tint: bool = _player.is_fusion_active()
	if should_tint == _current_tinted:
		return
	_current_tinted = should_tint
	if _current_tinted:
		_material.albedo_color = COLOR_MUTATION_TINT
		_material.emission_enabled = true
		_material.emission = COLOR_MUTATION_EMISSION
		_material.emission_energy_multiplier = 1.5
	else:
		_material.albedo_color = _baseline_albedo
		_material.emission_enabled = _baseline_emission_enabled
		_material.emission = _baseline_emission
		_material.emission_energy_multiplier = _baseline_emission_energy
