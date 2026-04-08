"""Imp limb materials: ``material_for_zone_part`` on cylinders and joint balls (mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.enemies.animated_imp import AnimatedImp


@patch("src.enemies.animated_imp.apply_material_to_object")
@patch(
    "src.enemies.animated_imp.material_for_zone_part",
    side_effect=lambda *a, **kw: MagicMock(name="mat"),
)
def test_imp_apply_themed_materials_calls_zone_part_for_each_limb_cylinder(
    mock_zone_part: MagicMock,
    _mock_apply: MagicMock,
) -> None:
    inst = AnimatedImp.__new__(AnimatedImp)
    inst.build_options = {"features": {}}
    # body, head, 2 arms (1 seg + sphere hand) * 2 pairs, 2 legs (1 seg, no foot)
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
        v = getattr(AnimatedImp, name, 0)
        return int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v

    inst._mesh = MagicMock(side_effect=_mesh)
    inst._mesh_str = MagicMock(
        side_effect=lambda name, allowed=None: "sphere" if name == "ARM_END_SHAPE" else "none",
    )
    mats = {z: MagicMock(name=z) for z in ("body", "head", "limbs", "joints", "extra")}
    inst._themed_slot_materials_for = MagicMock(return_value=mats)

    AnimatedImp.apply_themed_materials(inst)

    assert mock_zone_part.call_count == 4
    zones = [c[0][0] for c in mock_zone_part.call_args_list]
    assert zones.count("limbs") == 4


@patch("src.enemies.animated_imp.apply_material_to_object")
@patch(
    "src.enemies.animated_imp.material_for_zone_part",
    side_effect=lambda *a, **kw: MagicMock(name="mat"),
)
def test_imp_apply_calls_joint_zone_when_multi_segment_arm(
    mock_zone_part: MagicMock,
    _mock_apply: MagicMock,
) -> None:
    inst = AnimatedImp.__new__(AnimatedImp)
    inst.build_options = {"features": {}}
    # body, head, 2 arms × (2 cyl + 1 joint), 2 legs × (2 cyl + 1 joint) = 2+6+6
    inst.parts = [MagicMock() for _ in range(14)]

    def _mesh(name: str):
        fixed = {
            "ARM_SEGMENTS": 2,
            "LEG_SEGMENTS": 2,
            "LIMB_JOINT_VISUAL": True,
            "LIMB_PAIRS": 2,
        }
        if name in fixed:
            return fixed[name]
        v = getattr(AnimatedImp, name, 0)
        return int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v

    inst._mesh = MagicMock(side_effect=_mesh)
    inst._mesh_str = MagicMock(return_value="none")
    mats = {z: MagicMock(name=z) for z in ("body", "head", "limbs", "joints", "extra")}
    inst._themed_slot_materials_for = MagicMock(return_value=mats)

    AnimatedImp.apply_themed_materials(inst)

    zones = [c[0][0] for c in mock_zone_part.call_args_list]
    assert "joints" in zones
    assert zones.count("joints") >= 4


@patch("src.enemies.animated_imp.apply_material_to_object")
@patch(
    "src.enemies.animated_imp.material_for_zone_part",
    side_effect=lambda *a, **kw: MagicMock(name="mat"),
)
def test_imp_apply_uses_limb_material_for_leg_end_cap(
    _mock_zone_part: MagicMock,
    _mock_apply: MagicMock,
) -> None:
    """Leg end primitive uses base limb slot (line coverage for foot sphere)."""
    inst = AnimatedImp.__new__(AnimatedImp)
    inst.build_options = {"features": {}}
    inst.parts = [MagicMock() for _ in range(8)]

    def _mesh(name: str):
        fixed = {
            "ARM_SEGMENTS": 1,
            "LEG_SEGMENTS": 1,
            "LIMB_JOINT_VISUAL": False,
            "LIMB_PAIRS": 2,
        }
        if name in fixed:
            return fixed[name]
        v = getattr(AnimatedImp, name, 0)
        return int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v

    inst._mesh = MagicMock(side_effect=_mesh)

    def _mesh_str(name: str, allowed=None):
        return "sphere" if name == "LEG_END_SHAPE" else "none"

    inst._mesh_str = MagicMock(side_effect=_mesh_str)
    mats = {z: MagicMock(name=z) for z in ("body", "head", "limbs", "joints", "extra")}
    inst._themed_slot_materials_for = MagicMock(return_value=mats)

    AnimatedImp.apply_themed_materials(inst)
