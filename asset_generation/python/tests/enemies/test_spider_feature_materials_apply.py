"""Spider leg materials: zone split calls ``material_for_zone_part`` (mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.enemies.animated_spider import AnimatedSpider


@patch("src.enemies.animated_spider.apply_material_to_object")
@patch(
    "src.enemies.animated_spider.material_for_zone_part",
    side_effect=lambda *a, **kw: MagicMock(name="mat"),
)
def test_spider_apply_themed_materials_uses_zone_part_per_leg_mesh(
    mock_zone_part: MagicMock,
    _mock_apply: MagicMock,
) -> None:
    inst = AnimatedSpider.__new__(AnimatedSpider)
    inst._eye_count = 2
    inst.build_options = {"features": {"limbs": {"parts": {"leg_0": {"hex": "aabbcc"}}}}}
    per_leg = 8
    leg_start = 2 + 2
    n_parts = leg_start + 8 * per_leg
    inst.parts = [MagicMock() for _ in range(n_parts)]

    def _mesh(name: str):
        if name == "DEFAULT_EYE_COUNT":
            return 2
        return int(getattr(AnimatedSpider, name, 0))

    inst._mesh = MagicMock(side_effect=_mesh)
    mats = {z: MagicMock(name=z) for z in ("body", "head", "limbs", "joints", "extra")}
    inst._themed_slot_materials_for = MagicMock(return_value=mats)

    AnimatedSpider.apply_themed_materials(inst)

    assert mock_zone_part.call_count == 8 * per_leg
    first = mock_zone_part.call_args_list[0]
    assert first[0][0] == "limbs"
    assert first[0][1] == "leg_0"
