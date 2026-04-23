"""Runtime contract tests for M901-08 blender utilities split."""

from __future__ import annotations

import inspect
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

PRIMITIVE_SYMBOLS = ("create_sphere", "create_cylinder", "create_cone", "create_box")
CREATURE_PART_SYMBOLS = (
    "create_eye_mesh",
    "create_pupil_mesh",
    "create_mouth_mesh",
    "create_tail_mesh",
)
MESH_OP_SYMBOLS = (
    "clear_scene",
    "detect_body_scale_from_mesh",
    "apply_smooth_shading",
    "join_objects",
    "random_variance",
    "bind_mesh_to_armature",
    "bind_mesh_manually",
    "ensure_mesh_integrity",
    "fix_body_part_bindings",
    "identify_vertex_body_part",
)


def _load_split_modules():
    primitives = import_module("src.core.primitives")
    creature_parts = import_module("src.core.creature_parts")
    mesh_ops = import_module("src.core.mesh_ops")
    blender_utils = import_module("src.core.blender_utils")
    return primitives, creature_parts, mesh_ops, blender_utils


def test_split_modules_are_importable_with_expected_symbol_surfaces() -> None:
    primitives, creature_parts, mesh_ops, _blender_utils = _load_split_modules()

    for symbol in PRIMITIVE_SYMBOLS:
        assert callable(getattr(primitives, symbol))
    for symbol in CREATURE_PART_SYMBOLS:
        assert callable(getattr(creature_parts, symbol))
    for symbol in MESH_OP_SYMBOLS:
        assert callable(getattr(mesh_ops, symbol))


@pytest.mark.parametrize(
    ("symbol", "canonical_module"),
    [(name, "src.core.primitives") for name in PRIMITIVE_SYMBOLS]
    + [(name, "src.core.mesh_ops") for name in MESH_OP_SYMBOLS],
)
def test_blender_utils_re_exports_canonical_callable_identity(
    symbol: str, canonical_module: str
) -> None:
    canonical = import_module(canonical_module)
    blender_utils = import_module("src.core.blender_utils")

    assert getattr(blender_utils, symbol) is getattr(canonical, symbol)
    assert getattr(canonical, symbol).__module__ == canonical_module


@pytest.mark.parametrize(
    ("symbol", "canonical_module"),
    [(name, "src.core.primitives") for name in PRIMITIVE_SYMBOLS]
    + [(name, "src.core.creature_parts") for name in CREATURE_PART_SYMBOLS]
    + [(name, "src.core.mesh_ops") for name in MESH_OP_SYMBOLS],
)
def test_blender_utils_re_exports_preserve_callable_signatures(
    symbol: str, canonical_module: str
) -> None:
    canonical = import_module(canonical_module)
    blender_utils = import_module("src.core.blender_utils")

    assert inspect.signature(getattr(blender_utils, symbol)) == inspect.signature(
        getattr(canonical, symbol)
    )


@pytest.mark.parametrize("symbol", CREATURE_PART_SYMBOLS)
def test_blender_utils_creature_part_symbols_remain_compatibility_wrappers(
    symbol: str,
) -> None:
    """Creature-part compatibility call paths stay patchable at blender_utils."""
    creature_parts = import_module("src.core.creature_parts")
    blender_utils = import_module("src.core.blender_utils")

    assert callable(getattr(blender_utils, symbol))
    assert callable(getattr(creature_parts, symbol))
    assert getattr(blender_utils, symbol) is not getattr(creature_parts, symbol)


def test_blender_utils_exports_are_explicit_and_deterministic() -> None:
    _, _, _, blender_utils = _load_split_modules()
    exported = set(blender_utils.__all__)
    expected = set(PRIMITIVE_SYMBOLS) | set(CREATURE_PART_SYMBOLS) | set(MESH_OP_SYMBOLS)

    assert exported == expected


def test_stale_nested_blender_utils_import_path_fails_closed() -> None:
    with pytest.raises(ModuleNotFoundError):
        import_module("src.core.blender_utils.primitives")


def test_create_eye_mesh_unknown_shape_falls_back_to_circle_sphere() -> None:
    _, creature_parts, _, _ = _load_split_modules()
    sentinel = object()
    with patch.object(creature_parts, "create_sphere", return_value=sentinel) as mock_sphere:
        result = creature_parts.create_eye_mesh("unknown-shape", (1.0, 2.0, 3.0), 0.7)
    assert result is sentinel
    mock_sphere.assert_called_once_with(location=(1.0, 2.0, 3.0), scale=(0.7, 0.7, 0.7))


def test_create_pupil_mesh_unknown_shape_falls_back_to_dot_sphere() -> None:
    _, creature_parts, _, _ = _load_split_modules()
    sentinel = object()
    with patch.object(creature_parts, "create_sphere", return_value=sentinel) as mock_sphere:
        result = creature_parts.create_pupil_mesh("unknown-shape", (1.0, 2.0, 3.0), 0.4)
    assert result is sentinel
    mock_sphere.assert_called_once_with(location=(1.0, 2.0, 3.0), scale=(0.4, 0.4, 0.12))


def test_create_mouth_mesh_unknown_shape_falls_back_to_smile_cylinder() -> None:
    _, creature_parts, _, _ = _load_split_modules()
    sentinel = object()
    with patch.object(
        creature_parts, "create_cylinder", return_value=sentinel
    ) as mock_cylinder:
        result = creature_parts.create_mouth_mesh("unknown-shape", (0.0, 0.0, 0.0), 1.0)
    assert result is sentinel
    mock_cylinder.assert_called_once()
    assert mock_cylinder.call_args.kwargs["scale"] == pytest.approx((1.2, 1.0, 0.15))


def test_create_tail_mesh_unknown_shape_falls_back_to_curled_sphere() -> None:
    _, creature_parts, _, _ = _load_split_modules()
    sentinel = object()
    with patch.object(creature_parts, "create_sphere", return_value=sentinel) as mock_sphere:
        result = creature_parts.create_tail_mesh("unknown-shape", 2.0, (0.0, 0.0, 0.0))
    assert result is sentinel
    mock_sphere.assert_called_once_with(location=(0.0, 0.0, 0.0), scale=(1.2, 1.2, 0.6))


def test_detect_body_scale_from_mesh_returns_fallback_for_missing_or_empty_data() -> None:
    _, _, mesh_ops, _ = _load_split_modules()

    assert mesh_ops.detect_body_scale_from_mesh(None) == 1.0
    assert mesh_ops.detect_body_scale_from_mesh(SimpleNamespace(data=None)) == 1.0
    assert mesh_ops.detect_body_scale_from_mesh(SimpleNamespace(data=SimpleNamespace())) == 1.0
    assert (
        mesh_ops.detect_body_scale_from_mesh(SimpleNamespace(data=SimpleNamespace(vertices=[])))
        == 1.0
    )


def test_detect_body_scale_from_mesh_enforces_lower_bound() -> None:
    _, _, mesh_ops, _ = _load_split_modules()
    vertices = [SimpleNamespace(co=SimpleNamespace(z=1.0)), SimpleNamespace(co=SimpleNamespace(z=1.1))]
    mesh = SimpleNamespace(data=SimpleNamespace(vertices=vertices))

    assert mesh_ops.detect_body_scale_from_mesh(mesh) == pytest.approx(0.1)


def test_random_variance_formula_with_deterministic_rng() -> None:
    _, _, mesh_ops, _ = _load_split_modules()
    rng = SimpleNamespace(random=lambda: 0.75)

    assert mesh_ops.random_variance(base_value=10.0, factor=0.2, rng=rng) == pytest.approx(11.0)


def test_random_variance_factor_zero_is_stable_for_extreme_rng_values() -> None:
    _, _, mesh_ops, _ = _load_split_modules()

    assert (
        mesh_ops.random_variance(
            base_value=13.5, factor=0.0, rng=SimpleNamespace(random=lambda: 0.0)
        )
        == 13.5
    )
    assert (
        mesh_ops.random_variance(
            base_value=13.5, factor=0.0, rng=SimpleNamespace(random=lambda: 1.0)
        )
        == 13.5
    )


def test_bind_mesh_to_armature_uses_manual_fallback_when_auto_bind_raises() -> None:
    _, _, mesh_ops, _ = _load_split_modules()
    mesh_obj = MagicMock()
    mesh_obj.vertex_groups = []
    armature = MagicMock()

    with (
        patch.object(mesh_ops.bpy.ops.object, "select_all"),
        patch.object(mesh_ops.bpy.ops.object, "parent_set", side_effect=RuntimeError("boom")),
        patch.object(mesh_ops, "bind_mesh_manually", return_value="manual-result") as manual_bind,
    ):
        assert mesh_ops.bind_mesh_to_armature(mesh_obj, armature) == "manual-result"
    manual_bind.assert_called_once_with(mesh_obj, armature)


def test_bind_mesh_to_armature_uses_manual_fallback_when_no_groups_created() -> None:
    _, _, mesh_ops, _ = _load_split_modules()
    mesh_obj = MagicMock()
    mesh_obj.vertex_groups = []
    armature = MagicMock()

    with (
        patch.object(mesh_ops.bpy.ops.object, "select_all"),
        patch.object(mesh_ops.bpy.ops.object, "parent_set"),
        patch.object(mesh_ops, "bind_mesh_manually", return_value="manual-result") as manual_bind,
    ):
        assert mesh_ops.bind_mesh_to_armature(mesh_obj, armature) == "manual-result"
    manual_bind.assert_called_once_with(mesh_obj, armature)


def test_bind_mesh_to_armature_returns_mesh_when_auto_bind_creates_groups() -> None:
    _, _, mesh_ops, _ = _load_split_modules()
    mesh_obj = MagicMock()
    mesh_obj.vertex_groups = [object()]
    armature = MagicMock()

    with (
        patch.object(mesh_ops.bpy.ops.object, "select_all"),
        patch.object(mesh_ops.bpy.ops.object, "parent_set"),
        patch.object(mesh_ops, "bind_mesh_manually") as manual_bind,
    ):
        result = mesh_ops.bind_mesh_to_armature(mesh_obj, armature)

    assert result is mesh_obj
    manual_bind.assert_not_called()
