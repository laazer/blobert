"""Carapace limb materials: ``material_for_zone_part`` on cylinders and joints (mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

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
