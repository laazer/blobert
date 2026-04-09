"""Slug zone geometry extras attach (mocked Blender)."""

from unittest.mock import MagicMock, patch

from src.enemies.animated_slug import AnimatedSlug
from src.enemies.zone_geometry_extras_attach import append_slug_zone_extras


def _minimal_slug() -> AnimatedSlug:
    mats = {"Organic_Brown": MagicMock(), "Flesh_Pink": MagicMock(), "Bone_White": MagicMock()}
    rng = MagicMock()
    rng.random = MagicMock(return_value=0.25)
    slug = AnimatedSlug("slug", mats, rng, build_options={})
    slug.length = 2.0
    slug.width = 0.8
    slug.height = 0.6
    slug.parts = [MagicMock(), MagicMock()]
    return slug


def test_slug_apply_themed_materials_calls_zone_extras_hook() -> None:
    s = _minimal_slug()
    mats = {
        "body": MagicMock(),
        "head": MagicMock(),
        "limbs": MagicMock(),
        "extra": MagicMock(),
    }
    with patch("src.enemies.animated_slug.get_enemy_materials", return_value=mats):
        with patch("src.enemies.animated_slug.apply_material_to_object"):
            with patch("src.enemies.animated_slug.append_slug_zone_extras") as ap:
                s.apply_themed_materials()
    ap.assert_called_once_with(s)


def test_append_slug_zone_extras_skips_when_no_options() -> None:
    s = _minimal_slug()
    append_slug_zone_extras(s)
    assert len(s.parts) == 2


def test_append_slug_body_spikes_appends_cones() -> None:
    s = _minimal_slug()
    s.build_options = {
        "features": {"body": {"finish": "default", "hex": ""}},
        "zone_geometry_extras": {"body": {"kind": "spikes", "spike_count": 3, "spike_shape": "cone"}},
    }
    fake_cone = MagicMock()
    with patch("src.enemies.zone_geometry_extras_attach.create_cone", return_value=fake_cone):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object") as am:
            with patch("src.enemies.zone_geometry_extras_attach.get_enemy_materials", return_value={"body": MagicMock()}):
                with patch(
                    "src.enemies.zone_geometry_extras_attach.apply_feature_slot_overrides",
                    side_effect=lambda slots, _f: slots,
                ):
                    with patch(
                        "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                        return_value=MagicMock(),
                    ):
                        append_slug_zone_extras(s)
    assert len(s.parts) == 5
    assert am.call_count == 3
