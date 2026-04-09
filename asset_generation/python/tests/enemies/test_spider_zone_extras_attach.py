"""Spider zone geometry extras attach (mocked Blender)."""

from unittest.mock import MagicMock, patch

from src.enemies.animated_spider import AnimatedSpider
from src.enemies.zone_geometry_extras_attach import append_animated_enemy_zone_extras, append_spider_zone_extras


def _minimal_spider() -> AnimatedSpider:
    mats = {"Organic_Brown": MagicMock(), "Flesh_Pink": MagicMock(), "Bone_White": MagicMock()}
    rng = MagicMock()
    rng.random = MagicMock(return_value=0.25)
    spider = AnimatedSpider("spider", mats, rng, build_options={})
    spider.parts = [MagicMock(), MagicMock()]
    from mathutils import Vector

    spider._zone_geom_body_center = Vector((0.0, 0.0, 1.0))
    spider._zone_geom_body_radii = Vector((1.0, 0.8, 0.9))
    spider._zone_geom_head_center = Vector((1.5, 0.0, 1.0))
    spider._zone_geom_head_radii = Vector((0.5, 0.5, 0.5))
    return spider


def test_spider_apply_themed_materials_calls_zone_extras_hook() -> None:
    inst = AnimatedSpider.__new__(AnimatedSpider)
    inst._eye_count = 2
    inst.build_options = {"features": {}}
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
    with patch("src.enemies.animated_spider.apply_material_to_object"):
        with patch("src.enemies.animated_spider.material_for_zone_part", return_value=MagicMock()):
            with patch("src.enemies.animated_spider.append_animated_enemy_zone_extras") as ap:
                AnimatedSpider.apply_themed_materials(inst)
    ap.assert_called_once_with(inst)


def test_append_spider_zone_extras_skips_when_no_options() -> None:
    s = _minimal_spider()
    append_spider_zone_extras(s)
    assert len(s.parts) == 2


def test_append_spider_body_spikes_appends_cones() -> None:
    s = _minimal_spider()
    s.build_options = {
        "features": {"body": {"finish": "default", "hex": ""}},
        "zone_geometry_extras": {"body": {"kind": "spikes", "spike_count": 3, "spike_shape": "cone"}},
    }
    fake_cone = MagicMock()
    with patch("src.enemies.zone_geometry_extras_attach.create_cone", return_value=fake_cone):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object") as am:
            with patch(
                "src.enemies.zone_geometry_extras_attach.get_enemy_materials", return_value={"body": MagicMock()}
            ):
                with patch(
                    "src.enemies.zone_geometry_extras_attach.apply_feature_slot_overrides",
                    side_effect=lambda slots, _f: slots,
                ):
                    with patch(
                        "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                        return_value=MagicMock(),
                    ):
                        append_spider_zone_extras(s)
    assert len(s.parts) == 5
    assert am.call_count == 3


def test_append_animated_skips_without_stored_geometry() -> None:
    mats = {"Organic_Brown": MagicMock()}
    rng = MagicMock()
    spider = AnimatedSpider("spider", mats, rng, build_options={"zone_geometry_extras": {"body": {"kind": "spikes"}}})
    spider.parts = [MagicMock()]
    append_animated_enemy_zone_extras(spider)
    assert len(spider.parts) == 1


def test_append_skips_non_spider() -> None:
    class NotSpider:
        build_options = {"zone_geometry_extras": {"body": {"kind": "spikes"}}}

    append_spider_zone_extras(NotSpider())
