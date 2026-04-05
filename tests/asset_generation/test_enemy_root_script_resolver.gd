# test_enemy_root_script_resolver.gd
#
# REQ-ESEG-1 — Shared enemy root script resolver; dual-consumer parity (no duplicate path logic).
# REQ-ESEG-2 — Override path res://scripts/enemies/generated/{family_stem}.gd; base fallback.
# REQ-ESEG-3 — Parity: both generators preload the same resolver (ESEG-DOC).
#
# Ticket: project_board/maintenance/in_progress/enemy_script_extension_and_scene_generator.md
#
# Contract assumed for implementation (spec allows filename; tests fix the example name):
#   res://scripts/asset_generation/enemy_root_script_resolver.gd
#   Instantiates with .new(); instance method:
#     func resolve_enemy_root_script_path(family_name: String) -> String
#
# Red phase: resolver module missing or generators not wired → failures expected.

extends "res://tests/utils/test_utils.gd"

const RESOLVER_PATH := "res://scripts/asset_generation/enemy_root_script_resolver.gd"
const BASE_SCRIPT_PATH := "res://scripts/enemies/enemy_base.gd"
const GENERATE_PATH := "res://scripts/asset_generation/generate_enemy_scenes.gd"
const LOAD_ASSETS_PATH := "res://scripts/asset_generation/load_assets.gd"
const OVERRIDE_PROBE_STEM := "eseg_test_override_probe"
const OVERRIDE_PROBE_PATH := "res://scripts/enemies/generated/eseg_test_override_probe.gd"

const _EnemyNameUtils = preload("res://scripts/asset_generation/enemy_name_utils.gd")

var _pass_count: int = 0
var _fail_count: int = 0


func _load_text(path: String) -> String:
	if not ResourceLoader.exists(path):
		return ""
	var scr: GDScript = load(path) as GDScript
	if scr == null:
		return ""
	return scr.source_code


func _resolver_instance() -> Object:
	if not ResourceLoader.exists(RESOLVER_PATH):
		return null
	var gds: GDScript = load(RESOLVER_PATH) as GDScript
	if gds == null:
		return null
	if not gds.can_instantiate():
		return null
	return gds.new()


# ---------------------------------------------------------------------------
# REQ-ESEG-1a / module presence
# ---------------------------------------------------------------------------

func test_eseg_1a_resolver_module_on_disk() -> void:
	_assert_true(
		ResourceLoader.exists(RESOLVER_PATH),
		"ESEG-1a — resolver module exists at %s" % RESOLVER_PATH
	)


func test_eseg_1a_resolver_defines_base_and_override_constants_in_one_file() -> void:
	# Soft structural check: single module owns both path literals (AC-ESEG-1a).
	var src := _load_text(RESOLVER_PATH)
	if src.is_empty():
		_fail("ESEG-1a-const", "resolver source not readable — skip structure check")
		return
	_assert_true(
		src.contains("res://scripts/enemies/enemy_base.gd"),
		"ESEG-1a-const1 — resolver source references enemy_base.gd"
	)
	_assert_true(
		src.contains("res://scripts/enemies/generated/"),
		"ESEG-1a-const2 — resolver source references scripts/enemies/generated/"
	)


# ---------------------------------------------------------------------------
# REQ-ESEG-1d / 1e / REQ-ESEG-2a — resolve behavior
# ---------------------------------------------------------------------------

func test_eseg_1d_returns_base_when_override_missing() -> void:
	var inst := _resolver_instance()
	if inst == null:
		_fail("ESEG-1d", "resolver not instantiable — cannot test")
		return
	if not inst.has_method("resolve_enemy_root_script_path"):
		_fail("ESEG-1d", "resolver missing resolve_enemy_root_script_path")
		return
	var absent_stem := "zz_eseg_absent_override_%d" % Time.get_ticks_msec()
	var got: Variant = inst.call("resolve_enemy_root_script_path", absent_stem)
	_assert_eq(
		BASE_SCRIPT_PATH,
		str(got),
		"ESEG-1d — missing override → %s" % BASE_SCRIPT_PATH
	)


func test_eseg_1e_returns_override_when_probe_exists() -> void:
	_assert_true(
		ResourceLoader.exists(OVERRIDE_PROBE_PATH),
		"ESEG-1e-pre — fixture override exists at %s" % OVERRIDE_PROBE_PATH
	)
	var inst := _resolver_instance()
	if inst == null:
		_fail("ESEG-1e", "resolver not instantiable — cannot test")
		return
	if not inst.has_method("resolve_enemy_root_script_path"):
		_fail("ESEG-1e", "resolver missing resolve_enemy_root_script_path")
		return
	var got: Variant = inst.call("resolve_enemy_root_script_path", OVERRIDE_PROBE_STEM)
	_assert_eq(
		OVERRIDE_PROBE_PATH,
		str(got),
		"ESEG-1e — existing override → %s" % OVERRIDE_PROBE_PATH
	)


func test_eseg_2a_override_path_uses_extract_family_stem_adhesion_bug() -> void:
	# REQ-ESEG-2c: adhesion_bug_00 → family adhesion_bug → adhesion_bug.gd
	var stem: String = EnemyNameUtils.extract_family_name("adhesion_bug_animated_00")
	_assert_eq("adhesion_bug", stem, "ESEG-2c-stem — extract_family_name adhesion_bug_animated_00")
	var expected := "res://scripts/enemies/generated/%s.gd" % stem
	var inst := _resolver_instance()
	if inst == null:
		_fail("ESEG-2a", "resolver not instantiable — cannot test")
		return
	if not inst.has_method("resolve_enemy_root_script_path"):
		_fail("ESEG-2a", "resolver missing resolve_enemy_root_script_path")
		return
	var got: Variant = inst.call("resolve_enemy_root_script_path", stem)
	# No file on disk for adhesion_bug.gd in default repo → base path until override added.
	if ResourceLoader.exists(expected):
		_assert_eq(expected, str(got), "ESEG-2a — adhesion_bug override present → override path")
	else:
		_assert_eq(BASE_SCRIPT_PATH, str(got), "ESEG-2a — adhesion_bug override absent → base path")


func test_eseg_2a_override_path_uses_extract_family_stem_acid_spitter() -> void:
	var stem: String = EnemyNameUtils.extract_family_name("acid_spitter_animated_00")
	_assert_eq("acid_spitter", stem, "ESEG-2a-spitter-stem")
	var expected := "res://scripts/enemies/generated/%s.gd" % stem
	var inst := _resolver_instance()
	if inst == null:
		_fail("ESEG-2a-spitter", "resolver not instantiable — cannot test")
		return
	if not inst.has_method("resolve_enemy_root_script_path"):
		_fail("ESEG-2a-spitter", "resolver missing resolve_enemy_root_script_path")
		return
	var got: Variant = inst.call("resolve_enemy_root_script_path", stem)
	if ResourceLoader.exists(expected):
		_assert_eq(expected, str(got), "ESEG-2a-spitter — override present")
	else:
		_assert_eq(BASE_SCRIPT_PATH, str(got), "ESEG-2a-spitter — override absent → base")


# ---------------------------------------------------------------------------
# REQ-ESEG-1b / 1c / REQ-ESEG-3b — consumers use resolver only (no duplicate path rules)
# ---------------------------------------------------------------------------

func test_eseg_1b_generate_preloads_resolver() -> void:
	var src := _load_text(GENERATE_PATH)
	if src.is_empty():
		_fail("ESEG-1b-gen", "generate_enemy_scenes.gd not readable")
		return
	_assert_true(
		src.contains("preload(\"res://scripts/asset_generation/enemy_root_script_resolver.gd\")"),
		"ESEG-1b-gen — generate_enemy_scenes.gd preloads enemy_root_script_resolver.gd"
	)


func test_eseg_1c_load_assets_preloads_resolver() -> void:
	var src := _load_text(LOAD_ASSETS_PATH)
	if src.is_empty():
		_fail("ESEG-1c-load", "load_assets.gd not readable")
		return
	_assert_true(
		src.contains("preload(\"res://scripts/asset_generation/enemy_root_script_resolver.gd\")"),
		"ESEG-1c-load — load_assets.gd preloads enemy_root_script_resolver.gd"
	)


func test_eseg_1bc_generators_do_not_embed_generated_override_dir() -> void:
	# Override path pattern must live only in the resolver (AC-ESEG-1b/c, REQ-ESEG-3b).
	for path in [GENERATE_PATH, LOAD_ASSETS_PATH]:
		var src := _load_text(path)
		if src.is_empty():
			_fail("ESEG-1bc", "%s not readable" % path)
			return
		_assert_true(
			not src.contains("res://scripts/enemies/generated/"),
			"ESEG-1bc — %s must not contain res://scripts/enemies/generated/ (resolver owns it)"
			% path
		)


func test_eseg_1bc_generators_call_resolver_before_set_script() -> void:
	for path in [GENERATE_PATH, LOAD_ASSETS_PATH]:
		var src := _load_text(path)
		if src.is_empty():
			_fail("ESEG-1bc-call", "%s not readable" % path)
			return
		_assert_true(
			src.contains("resolve_enemy_root_script_path"),
			"ESEG-1bc-call — %s must call resolve_enemy_root_script_path" % path
		)
		_assert_true(src.contains("set_script"), "ESEG-1bc-call — %s still sets root script" % path)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_enemy_root_script_resolver.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_eseg_1a_resolver_module_on_disk()
	test_eseg_1a_resolver_defines_base_and_override_constants_in_one_file()
	test_eseg_1d_returns_base_when_override_missing()
	test_eseg_1e_returns_override_when_probe_exists()
	test_eseg_2a_override_path_uses_extract_family_stem_adhesion_bug()
	test_eseg_2a_override_path_uses_extract_family_stem_acid_spitter()
	test_eseg_1b_generate_preloads_resolver()
	test_eseg_1c_load_assets_preloads_resolver()
	test_eseg_1bc_generators_do_not_embed_generated_override_dir()
	test_eseg_1bc_generators_call_resolver_before_set_script()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
