"""Behavior contracts for M901-09 zone geometry extras decomposition."""

from __future__ import annotations

import importlib
import inspect
import math
from typing import Any
from unittest.mock import MagicMock


def _import_module(path: str):
    return importlib.import_module(path)


def _resolve_callable(module: Any, required_tokens: tuple[str, ...]):
    for name in dir(module):
        if name.startswith("__"):
            continue
        lowered = name.lower()
        if not all(token in lowered for token in required_tokens):
            continue
        value = getattr(module, name)
        if callable(value):
            return value
    raise AssertionError(f"no callable found with tokens={required_tokens} in {module.__name__}")


def _xyz(v: Any) -> tuple[float, float, float]:
    if isinstance(v, tuple) and len(v) >= 3:
        return (float(v[0]), float(v[1]), float(v[2]))
    return (float(getattr(v, "x")), float(getattr(v, "y")), float(getattr(v, "z")))


def test_geometry_math_module_exists_without_bpy_import() -> None:
    mod = _import_module("src.enemies.zone_geometry_extras.geometry_math")
    source = inspect.getsource(mod)
    assert "import bpy" not in source


def test_geometry_math_ellipsoid_point_matches_legacy_formula() -> None:
    mod = _import_module("src.enemies.zone_geometry_extras.geometry_math")
    point_at = _resolve_callable(mod, ("ellipsoid", "point"))
    p = point_at(1.0, -2.0, 0.5, 2.0, 3.0, 4.0, math.pi / 2.0, math.pi / 2.0)
    x, y, z = _xyz(p)
    assert x == 1.0
    assert y == 1.0
    assert z == 0.5


def test_geometry_math_normal_degenerate_fallback_is_upward() -> None:
    mod = _import_module("src.enemies.zone_geometry_extras.geometry_math")
    normal = _resolve_callable(mod, ("ellipsoid", "normal"))
    n = normal(0.0, 0.0, 0.0, 1.0, 1.0, 1.0, (0.0, 0.0, 0.0))
    assert _xyz(n) == (0.0, 0.0, 1.0)


def test_geometry_math_public_callables_have_type_hints() -> None:
    mod = _import_module("src.enemies.zone_geometry_extras.geometry_math")
    for name in dir(mod):
        if name.startswith("_"):
            continue
        value = getattr(mod, name)
        if not callable(value):
            continue
        sig = inspect.signature(value)
        assert sig.return_annotation is not inspect.Signature.empty, f"{name} must type hint return"
        for param_name, param in sig.parameters.items():
            assert param.annotation is not inspect.Signature.empty, f"{name}.{param_name} must be type hinted"


def test_placement_strategy_module_resolves_distribution_and_uniform_shape() -> None:
    mod = _import_module("src.enemies.zone_geometry_extras.placement_strategy")
    zone_distribution = _resolve_callable(mod, ("distribution",))
    zone_uniform_shape = _resolve_callable(mod, ("uniform", "shape"))
    assert zone_distribution({"distribution": "BAD"}) == "uniform"
    assert zone_uniform_shape({"uniform_shape": "BAD"}) == "arc"


def test_placement_strategy_facing_gate_obeys_threshold_contract() -> None:
    mod = _import_module("src.enemies.zone_geometry_extras.placement_strategy")
    allows = _resolve_callable(mod, ("facing", "allow"))
    spec = {
        "place_top": False,
        "place_bottom": False,
        "place_front": True,
        "place_back": False,
        "place_left": False,
        "place_right": False,
    }
    assert allows(spec, (1.0, 0.0, 0.0)) is True
    assert allows(spec, (0.1, 0.0, 0.99)) is False


def test_attachment_module_exposes_enemy_and_player_entrypoints() -> None:
    mod = _import_module("src.enemies.zone_geometry_extras.attachment")
    append_enemy = _resolve_callable(mod, ("append", "animated", "enemy"))
    append_player = _resolve_callable(mod, ("append", "player", "slime"))

    class _Model:
        def __init__(self) -> None:
            self.parts: list[Any] = [MagicMock()]
            self.build_options = {"zone_geometry_extras": "not-a-dict"}

    class _Builder:
        def __init__(self) -> None:
            self._zone_extra_parts: list[Any] = [MagicMock()]
            self.build_options = {"zone_geometry_extras": "not-a-dict"}

    model = _Model()
    builder = _Builder()
    append_enemy(model)
    append_player(builder)
    assert len(model.parts) == 1
    assert len(builder._zone_extra_parts) == 1


def test_dispatcher_exports_legacy_entrypoints() -> None:
    mod = _import_module("src.enemies.zone_geometry_extras_attach")
    assert callable(getattr(mod, "append_animated_enemy_zone_extras", None))
    assert callable(getattr(mod, "append_slug_zone_extras", None))
    assert callable(getattr(mod, "append_spider_zone_extras", None))
    assert callable(getattr(mod, "append_player_slime_zone_extras", None))


def test_geometry_math_public_api_is_fully_type_annotated_explicitly() -> None:
    mod = _import_module("src.enemies.zone_geometry_extras.geometry_math")
    expected_public = {
        "vec_xyz",
        "ellipsoid_point_at",
        "ellipsoid_normal",
        "body_ref_size",
        "head_ref_size",
        "zone_extra_scale",
        "zone_extra_offset",
    }
    actual_public = {
        name for name, value in vars(mod).items() if callable(value) and not name.startswith("_")
    }
    assert actual_public == expected_public
    for name in sorted(actual_public):
        sig = inspect.signature(getattr(mod, name))
        assert sig.return_annotation is not inspect.Signature.empty, f"{name} must type hint return"
        for param_name, param in sig.parameters.items():
            assert param.annotation is not inspect.Signature.empty, f"{name}.{param_name} must be type hinted"


def test_dispatcher_entrypoints_remain_thin_and_delegation_focused() -> None:
    mod = _import_module("src.enemies.zone_geometry_extras_attach")
    target_functions = (
        "append_animated_enemy_zone_extras",
        "_append_body_ellipsoid_extras",
        "_append_head_ellipsoid_extras",
        "append_player_slime_zone_extras",
    )
    for function_name in target_functions:
        source = inspect.getsource(getattr(mod, function_name))
        assert "_sync_attachment_dependencies()" in source
        assert "_attachment_module." in source
        # Thin-dispatcher proof: no placement loops are re-embedded in dispatcher functions.
        assert " for " not in source
        assert " while " not in source


def test_geometry_math_scale_helper_clamps_non_finite_and_bounds() -> None:
    mod = _import_module("src.enemies.zone_geometry_extras.geometry_math")
    scale = _resolve_callable(mod, ("scale",))
    assert scale({"spike_size": "bad"}, "spike_size") == 1.0
    assert scale({"spike_size": float("nan")}, "spike_size") == 1.0
    assert scale({"spike_size": float("inf")}, "spike_size") == 3.0
    assert scale({"spike_size": float("-inf")}, "spike_size") == 0.25
    assert scale({"spike_size": 999.0}, "spike_size") == 3.0
    assert scale({"spike_size": -999.0}, "spike_size") == 0.25


def test_geometry_math_offset_helper_clamps_and_fails_closed() -> None:
    mod = _import_module("src.enemies.zone_geometry_extras.geometry_math")
    offset = _resolve_callable(mod, ("offset",))
    # CHECKPOINT: offset clamp constants are imported from shared build-option bounds.
    assert offset({"offset_x": "bad"}, "offset_x") == 0.0
    assert offset({"offset_x": float("nan")}, "offset_x") == 0.0
    assert offset({"offset_x": 1_000_000.0}, "offset_x") <= 1.0
    assert offset({"offset_x": -1_000_000.0}, "offset_x") >= -1.0


def test_placement_strategy_facing_gate_handles_toggle_extremes_and_zero_normal() -> None:
    mod = _import_module("src.enemies.zone_geometry_extras.placement_strategy")
    allows = _resolve_callable(mod, ("facing", "allow"))
    all_off = {
        "place_top": False,
        "place_bottom": False,
        "place_front": False,
        "place_back": False,
        "place_left": False,
        "place_right": False,
    }
    all_on = {
        "place_top": True,
        "place_bottom": True,
        "place_front": True,
        "place_back": True,
        "place_left": True,
        "place_right": True,
    }
    front_only = {
        "place_top": False,
        "place_bottom": False,
        "place_front": True,
        "place_back": False,
        "place_left": False,
        "place_right": False,
    }
    assert allows(all_off, (0.0, 0.0, 0.0)) is True
    assert allows(all_on, (0.0, 0.0, 0.0)) is True
    assert allows(front_only, (0.0, 0.0, 0.0)) is False


def test_placement_strategy_facing_threshold_boundary_is_stable() -> None:
    mod = _import_module("src.enemies.zone_geometry_extras.placement_strategy")
    allows = _resolve_callable(mod, ("facing", "allow"))
    spec = {
        "place_top": False,
        "place_bottom": False,
        "place_front": True,
        "place_back": False,
        "place_left": False,
        "place_right": False,
    }
    assert allows(spec, (0.45, 0.0, 0.0)) is True
    assert allows(spec, (0.4499, 0.0, 0.0)) is False


def test_placement_strategy_distribution_and_uniform_shape_normalize_case_and_whitespace() -> None:
    mod = _import_module("src.enemies.zone_geometry_extras.placement_strategy")
    zone_distribution = _resolve_callable(mod, ("distribution",))
    zone_uniform_shape = _resolve_callable(mod, ("uniform", "shape"))
    assert zone_distribution({"distribution": "  RANDOM  "}) == "random"
    assert zone_distribution({"distribution": "  UNIFORM  "}) == "uniform"
    assert zone_uniform_shape({"uniform_shape": "  RING  "}) == "ring"
    assert zone_uniform_shape({"uniform_shape": "  ARC  "}) == "arc"


def test_dispatcher_entrypoints_fail_closed_for_malformed_inputs() -> None:
    mod = _import_module("src.enemies.zone_geometry_extras_attach")
    append_enemy = getattr(mod, "append_animated_enemy_zone_extras")
    append_slug = getattr(mod, "append_slug_zone_extras")
    append_spider = getattr(mod, "append_spider_zone_extras")
    append_player = getattr(mod, "append_player_slime_zone_extras")

    class _BadModelNoTheme:
        def __init__(self) -> None:
            self.name = ""
            self.parts: list[Any] = [MagicMock()]
            self.rng = MagicMock()
            self.materials = {}
            self.build_options = {"zone_geometry_extras": {"body": {"kind": "spikes"}}}

    class _BadModelNoSpec:
        def __init__(self) -> None:
            self.name = "spider"
            self.parts: list[Any] = [MagicMock()]
            self.rng = MagicMock()
            self.materials = {}
            self.build_options = {"zone_geometry_extras": "not-a-dict"}

    class _BadBuilderNoOptions:
        def __init__(self) -> None:
            self._zone_extra_parts: list[Any] = [MagicMock()]
            self.build_options = None

    no_theme = _BadModelNoTheme()
    no_spec = _BadModelNoSpec()
    bad_builder = _BadBuilderNoOptions()
    append_enemy(no_theme)
    append_enemy(no_spec)
    append_slug(no_theme)
    append_spider(no_theme)
    append_player(bad_builder)
    assert len(no_theme.parts) == 1
    assert len(no_spec.parts) == 1
    assert len(bad_builder._zone_extra_parts) == 1
