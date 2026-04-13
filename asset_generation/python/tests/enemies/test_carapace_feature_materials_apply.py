"""Carapace limb materials: ``material_for_zone_part`` on cylinders and joints (mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.core.rig_models.humanoid_simple import (
    MESH_BODY_CENTER_Z_FACTOR,
    HumanoidSimpleRig,
)
from src.enemies import animated_imp as imp_mod
from src.enemies.animated_carapace_husk import AnimatedCarapaceHusk


@patch("src.enemies.animated_carapace_husk.apply_material_to_object")
@patch(
    "src.enemies.animated_carapace_husk.material_for_zone_part",
    side_effect=lambda *a, **kw: MagicMock(name="mat"),
)
def test_carapace_apply_themed_materials_calls_zone_part_for_limb_cylinders(
    mock_zone_part: MagicMock,
    _mock_apply: MagicMock,
) -> None:
    inst = AnimatedCarapaceHusk.__new__(AnimatedCarapaceHusk)
    inst.build_options = {"features": {}}
    inst.parts = [MagicMock() for _ in range(8)]

    def _mesh(name: str):
        fixed = {
            "ARM_SEGMENTS": 1,
            "LEG_SEGMENTS": 1,
            "LIMB_JOINT_VISUAL": True,
            "LIMB_PAIRS": 2,
        }
        if name in fixed:
            return fixed[name]
        v = getattr(AnimatedCarapaceHusk, name, 0)
        return int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v

    inst._mesh = MagicMock(side_effect=_mesh)
    inst._mesh_str = MagicMock(return_value="none")
    mats = {z: MagicMock(name=z) for z in ("body", "head", "limbs", "joints", "extra")}
    inst._themed_slot_materials_for = MagicMock(return_value=mats)

    AnimatedCarapaceHusk.apply_themed_materials(inst)

    assert mock_zone_part.call_count == 4


@patch("src.enemies.animated_carapace_husk.apply_material_to_object")
@patch(
    "src.enemies.animated_carapace_husk.material_for_zone_part",
    side_effect=lambda *a, **kw: MagicMock(name="mat"),
)
def test_carapace_apply_hits_joint_paths_when_multi_segment(
    mock_zone_part: MagicMock,
    _mock_apply: MagicMock,
) -> None:
    inst = AnimatedCarapaceHusk.__new__(AnimatedCarapaceHusk)
    inst.build_options = {"features": {}}
    # body + carapace + head + limbs (2 arms × 3 + 2 legs × 3 for n_seg=2, joints on)
    inst.parts = [MagicMock() for _ in range(18)]

    def _mesh(name: str):
        fixed = {
            "ARM_SEGMENTS": 2,
            "LEG_SEGMENTS": 2,
            "LIMB_JOINT_VISUAL": True,
            "LIMB_PAIRS": 2,
        }
        if name in fixed:
            return fixed[name]
        v = getattr(AnimatedCarapaceHusk, name, 0)
        return int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v

    inst._mesh = MagicMock(side_effect=_mesh)
    inst._mesh_str = MagicMock(return_value="none")
    mats = {z: MagicMock(name=z) for z in ("body", "head", "limbs", "joints", "extra")}
    inst._themed_slot_materials_for = MagicMock(return_value=mats)

    AnimatedCarapaceHusk.apply_themed_materials(inst)

    zones = [c[0][0] for c in mock_zone_part.call_args_list]
    assert "joints" in zones


def test_carapace_humanoid_limb_kinds_matches_imp_segmentation() -> None:
    from src.enemies import animated_carapace_husk as ch

    assert ch._humanoid_limb_part_kinds(2, True, "none") == imp_mod._humanoid_limb_part_kinds(
        2,
        True,
        "none",
    )


@patch("src.enemies.animated_carapace_husk.append_segmented_limb_mesh")
@patch("src.enemies.animated_carapace_husk.create_sphere", return_value=MagicMock(name="head"))
@patch("src.enemies.animated_carapace_husk.create_cylinder", return_value=MagicMock(name="cyl"))
@patch(
    "src.enemies.animated_carapace_husk.random_variance",
    side_effect=lambda base, _variance, _rng: float(base),
)
def test_build_mesh_parts_second_cylinder_is_carapace_plate(
    _mock_rv: MagicMock,
    mock_cylinder: MagicMock,
    _mock_sphere: MagicMock,
    _mock_limb: MagicMock,
) -> None:
    """Covers dorsal carapace scale and placement (diff-cover on build_mesh_parts)."""
    inst = AnimatedCarapaceHusk.__new__(AnimatedCarapaceHusk)
    inst.rng = MagicMock()
    inst.parts = []

    def _mesh_val(name: str):
        for cls in (AnimatedCarapaceHusk, HumanoidSimpleRig):
            if hasattr(cls, name):
                return getattr(cls, name)
        raise AssertionError(f"unknown mesh key {name!r}")

    inst._mesh = MagicMock(side_effect=_mesh_val)
    inst._mesh_str = MagicMock(
        side_effect=lambda k: str(_mesh_val(k)),
    )

    AnimatedCarapaceHusk.build_mesh_parts(inst)

    assert mock_cylinder.call_count >= 2
    body_width = float(AnimatedCarapaceHusk.BODY_WIDTH_BASE)
    carapace_call = mock_cylinder.call_args_list[1]
    sx, sy, sz = carapace_call.kwargs["scale"]
    assert sx == pytest.approx(body_width * float(AnimatedCarapaceHusk.CARAPACE_XY_SCALE))
    assert sy == pytest.approx(body_width * float(AnimatedCarapaceHusk.CARAPACE_XY_SCALE))
    bz = float(AnimatedCarapaceHusk.BODY_HEIGHT_BASE * MESH_BODY_CENTER_Z_FACTOR)
    expected_z = bz + float(AnimatedCarapaceHusk.BODY_HEIGHT_BASE * AnimatedCarapaceHusk.CARAPACE_Z_ABOVE_CENTER)
    assert carapace_call.kwargs["location"] == pytest.approx((0.0, 0.0, expected_z))
    assert sz == pytest.approx(float(AnimatedCarapaceHusk.BODY_HEIGHT_BASE * AnimatedCarapaceHusk.CARAPACE_Z_SCALE))
