"""animated_build_options: defaults, nesting, and coercion."""

import re

import pytest

from src.utils import animated_build_options as abo
from src.utils.animated_build_options import (
    animated_build_controls_for_api,
    options_for_enemy,
    parse_build_options_json,
)


def test_defaults_spider() -> None:
    o = options_for_enemy("spider", {})
    assert o["eye_count"] == 2
    assert "mesh" in o
    assert o["mesh"]["BODY_BASE"] == 1.0
    assert o["mesh"]["LEG_COUNT"] == 8
    assert "features" in o
    assert o["features"]["body"]["finish"] == "default"
    assert o["features"]["body"]["hex"] == ""
    assert "feat_body_finish" not in o


def test_nested_slug_object() -> None:
    o = options_for_enemy("spider", {"spider": {"eye_count": 4}})
    assert o["eye_count"] == 4


def test_flat_keys_for_current_slug() -> None:
    o = options_for_enemy("spider", {"eye_count": 4})
    assert o["eye_count"] == 4


def test_invalid_select_falls_back() -> None:
    o = options_for_enemy("spider", {"eye_count": 200})
    assert o["eye_count"] == 2


def test_spider_eye_count_extended_options() -> None:
    o = options_for_enemy("spider", {"eye_count": 10})
    assert o["eye_count"] == 10
    ctrl = animated_build_controls_for_api()
    eye = next(c for c in ctrl["spider"] if c["key"] == "eye_count")
    assert eye["options"][-1] == 99
    rig = next(c for c in ctrl["spider"] if c["key"].startswith("RIG_"))
    assert rig["label"].startswith("Rig ")


def test_peripheral_eyes_clamped() -> None:
    o = options_for_enemy("claw_crawler", {"peripheral_eyes": 99})
    assert o["peripheral_eyes"] == 3
    o2 = options_for_enemy("claw_crawler", {"peripheral_eyes": -1})
    assert o2["peripheral_eyes"] == 0


def test_parse_build_options_json() -> None:
    assert parse_build_options_json("") == {}
    assert parse_build_options_json("not json") == {}
    assert parse_build_options_json('{"eye_count":2}') == {"eye_count": 2}


def test_api_controls_have_known_slugs() -> None:
    ctrl = animated_build_controls_for_api()
    assert "eye_count" in {c["key"] for c in ctrl["spider"]}
    assert "peripheral_eyes" in {c["key"] for c in ctrl["claw_crawler"]}
    spider_keys = {c["key"] for c in ctrl["spider"]}
    assert "BODY_BASE" in spider_keys
    assert any(c["key"] == "BODY_BASE" and c["type"] == "float" for c in ctrl["spider"])


def test_mesh_float_defs_include_editor_unit_and_hint() -> None:
    ctrl = animated_build_controls_for_api()
    body = next(c for c in ctrl["spider"] if c["key"] == "BODY_BASE")
    assert body.get("unit")
    assert body.get("hint")
    rig = next(c for c in ctrl["imp"] if c["key"].startswith("RIG_"))
    assert rig.get("unit")
    assert rig.get("hint")


def test_zone_extra_float_defs_include_unit_and_hint() -> None:
    defs = abo._zone_extra_control_defs("slug")
    spike = next(d for d in defs if d["key"].endswith("_spike_size"))
    assert spike["unit"] == "× zone"
    assert len(str(spike.get("hint", ""))) > 5
    off = next(d for d in defs if d["key"].endswith("_offset_z"))
    assert off.get("unit") == "Blender units"


def test_spider_eye_clustering_has_editor_meta() -> None:
    ctrl = animated_build_controls_for_api()
    cl = next(c for c in ctrl["spider"] if c["key"] == "eye_clustering")
    assert cl.get("unit") == "0–1"
    assert "random" in str(cl.get("hint", "")).lower()


def test_mesh_override_nested() -> None:
    o = options_for_enemy("spider", {"spider": {"mesh": {"BODY_BASE": 1.5}}})
    assert o["mesh"]["BODY_BASE"] == 1.5


def test_mesh_override_flat() -> None:
    o = options_for_enemy("spider", {"spider": {"BODY_BASE": 1.4, "eye_count": 4}})
    assert o["eye_count"] == 4
    assert o["mesh"]["BODY_BASE"] == 1.4


def test_features_nested_and_flat() -> None:
    o = options_for_enemy(
        "imp",
        {
            "imp": {
                "features": {
                    "body": {"finish": "glossy", "hex": "ff00aa"},
                    "head": {"finish": "matte", "hex": ""},
                },
                "feat_limbs_finish": "metallic",
                "feat_limbs_hex": "112233",
            }
        },
    )
    assert o["features"]["body"]["finish"] == "glossy"
    assert o["features"]["body"]["hex"] == "ff00aa"
    assert o["features"]["head"]["finish"] == "matte"
    assert o["features"]["limbs"]["finish"] == "metallic"
    assert o["features"]["limbs"]["hex"] == "112233"


def test_features_invalid_finish_hex() -> None:
    o = options_for_enemy("slug", {"feat_body_finish": "not_a_finish", "feat_extra_hex": "gggggg"})
    assert o["features"]["body"]["finish"] == "default"
    assert o["features"]["extra"]["hex"] == ""


def test_api_includes_feature_controls() -> None:
    ctrl = animated_build_controls_for_api()
    keys = {c["key"] for c in ctrl["spider"]}
    assert "feat_body_finish" in keys
    assert "feat_body_hex" in keys
    body_finish = next(c for c in ctrl["spider"] if c["key"] == "feat_body_finish")
    assert body_finish["type"] == "select_str"
    assert "glossy" in body_finish["options"]


def test_imp_api_includes_all_feature_zones() -> None:
    ctrl = animated_build_controls_for_api()
    keys = {c["key"] for c in ctrl["imp"]}
    assert "feat_head_finish" in keys
    assert "feat_limbs_hex" in keys


def test_gel_finish_accepted() -> None:
    o = options_for_enemy("spider", {"feat_body_finish": "gel"})
    assert o["features"]["body"]["finish"] == "gel"


def test_hex_sanitizes_non_hex_and_truncates() -> None:
    o = options_for_enemy("spider", {"feat_body_hex": "ff#00ggaa99"})
    assert o["features"]["body"]["hex"] == "ff00aa"


def test_nested_feature_skips_non_dict_zone_payload() -> None:
    o = options_for_enemy(
        "imp",
        {"imp": {"features": {"body": "not_a_dict", "head": {"finish": "matte"}}}},
    )
    assert o["features"]["body"]["finish"] == "default"
    assert o["features"]["head"]["finish"] == "matte"


def test_flat_feat_unknown_zone_ignored() -> None:
    o = options_for_enemy("spider", {"feat_tail_finish": "glossy"})
    assert o["features"]["body"]["finish"] == "default"


def test_merge_features_non_dict_base_zone_uses_defaults() -> None:
    got = abo._merge_features_for_slug(
        "spider",
        {},
        {"body": "bad"},
    )
    assert got["body"]["finish"] == "default"
    assert got["body"]["hex"] == ""


def test_parse_then_options_round_trip_features() -> None:
    raw = parse_build_options_json('{"feat_body_finish": "metallic", "feat_body_hex": "aabbcc"}')
    o = options_for_enemy("claw_crawler", raw)
    assert o["features"]["body"]["finish"] == "metallic"
    assert o["features"]["body"]["hex"] == "aabbcc"


def test_unknown_slug_mesh_empty_features_body_only() -> None:
    o = options_for_enemy("not_a_real_enemy_type", {})
    assert o["mesh"] == {}
    assert list(o["features"].keys()) == ["body"]


def test_options_rebuilds_features_when_base_missing(monkeypatch) -> None:
    real = abo._defaults_for_slug

    def without_features(slug: str):
        b = real(slug)
        del b["features"]
        return b

    monkeypatch.setattr(abo, "_defaults_for_slug", without_features)
    o = options_for_enemy("spider", {"eye_count": 2})
    assert o["features"]["body"]["finish"] == "default"


def test_spider_features_include_joints_and_extra_zones() -> None:
    o = options_for_enemy("spider", {})
    assert set(o["features"].keys()) == {"body", "head", "limbs", "joints", "extra"}


_SPIDER_ZONE_FEAT_RE = re.compile(r"^feat_(body|head|limbs|joints|extra)_(finish|hex)$")


def test_api_spider_includes_zone_and_part_material_keys() -> None:
    ctrl = animated_build_controls_for_api()
    keys = {c["key"] for c in ctrl["spider"]}
    assert "feat_joints_finish" in keys
    assert "feat_joints_hex" in keys
    assert "feat_limb_leg_0_hex" in keys
    assert "feat_joint_leg_0_root_hex" in keys


def test_api_spider_has_exactly_ten_coarse_zone_material_controls() -> None:
    """Colors pane 'Zones' section lists five slots × finish + hex (no feat_limb_/feat_joint_)."""
    ctrl = animated_build_controls_for_api()["spider"]
    zone_rows = [c for c in ctrl if _SPIDER_ZONE_FEAT_RE.match(c["key"])]
    assert len(zone_rows) == 10
    kinds = {c["key"].split("_")[1] for c in zone_rows}
    assert kinds == {"body", "extra", "head", "joints", "limbs"}


def test_feat_limb_and_joint_part_flat_merge() -> None:
    o = options_for_enemy(
        "imp",
        {"feat_limb_arm_0_hex": "aabbcc", "feat_joint_arm_0_j0_hex": "112233"},
    )
    assert o["features"]["limbs"]["parts"]["arm_0"]["hex"] == "aabbcc"
    assert o["features"]["joints"]["parts"]["arm_0_j0"]["hex"] == "112233"


def test_validate_features_map_coerces_non_dict_zone_payload() -> None:
    out = abo._validate_features_map({"body": "not_a_dict"})
    assert out["body"]["finish"] == "default"
    assert out["body"]["hex"] == ""


def test_merge_skips_non_dict_part_entry_under_nested_features() -> None:
    o = options_for_enemy(
        "imp",
        {"imp": {"features": {"limbs": {"parts": {"arm_0": "not_a_dict", "arm_1": {"hex": "aabbcc"}}}}}},
    )
    parts = o["features"]["limbs"].get("parts", {})
    assert "arm_0" not in parts
    assert parts.get("arm_1", {}).get("hex") == "aabbcc"


def test_claw_crawler_and_spitter_have_multi_zone_features() -> None:
    ctrl = animated_build_controls_for_api()
    claw = {c["key"] for c in ctrl["claw_crawler"]}
    assert "feat_body_hex" in claw
    assert "feat_head_finish" in claw
    assert "feat_limbs_hex" in claw
    assert "feat_extra_finish" in claw
    spit = {c["key"] for c in ctrl["spitter"]}
    assert "feat_head_hex" in spit
    assert "feat_limbs_finish" in spit
    assert "feat_extra_hex" not in spit


def test_options_defaults_claw_crawler_features_four_zones() -> None:
    o = options_for_enemy("claw_crawler", {})
    assert set(o["features"].keys()) == {"body", "head", "limbs", "extra"}


def test_options_defaults_spitter_features_three_zones() -> None:
    o = options_for_enemy("spitter", {})
    assert set(o["features"].keys()) == {"body", "head", "limbs"}


def test_feat_joint_flat_ignored_when_slug_has_no_joints_zone() -> None:
    o = options_for_enemy("slug", {"feat_joint_any_hex": "ff00ff"})
    assert "joints" not in o["features"]


def test_nested_parts_round_trip() -> None:
    nested = {
        "imp": {
            "features": {
                "limbs": {"parts": {"arm_1": {"hex": "ffeedd"}}},
                "joints": {"parts": {"leg_0_j0": {"finish": "metallic", "hex": ""}}},
            }
        }
    }
    o = options_for_enemy("imp", nested)
    assert o["features"]["limbs"]["parts"]["arm_1"]["hex"] == "ffeedd"
    assert o["features"]["joints"]["parts"]["leg_0_j0"]["finish"] == "metallic"


def test_coerce_skips_static_control_when_key_absent() -> None:
    base = abo._defaults_for_slug("claw_crawler")
    del base["peripheral_eyes"]
    out = abo._coerce_and_validate("claw_crawler", base)
    assert "peripheral_eyes" not in out


def test_slug_defaults_zone_geometry_extras() -> None:
    o = options_for_enemy("slug", {})
    z = o["zone_geometry_extras"]
    assert set(z.keys()) == {"body", "head", "extra"}
    assert z["body"]["kind"] == "none"
    assert z["body"]["spike_count"] == 8
    assert z["body"]["spike_size"] == 1.0
    assert z["body"]["bulb_size"] == 1.0
    assert z["body"]["place_top"] is True
    assert z["body"]["place_front"] is True


def test_zone_geometry_extras_place_flat_keys_merge() -> None:
    o = options_for_enemy(
        "slug",
        {
            "extra_zone_body_place_top": False,
            "extra_zone_body_place_bottom": True,
            "extra_zone_head_place_front": 0,
        },
    )
    assert o["zone_geometry_extras"]["body"]["place_top"] is False
    assert o["zone_geometry_extras"]["body"]["place_bottom"] is True
    assert o["zone_geometry_extras"]["head"]["place_front"] is False


def test_extra_zone_spike_size_nested_top_level_applies() -> None:
    o = options_for_enemy("slug", {"slug": {"extra_zone_body_spike_size": 2.2}})
    assert o["zone_geometry_extras"]["body"]["spike_size"] == 2.2


def test_extra_zone_spike_size_under_mesh_dict_is_ignored() -> None:
    """``mesh`` only accepts ClassVar keys; misplaced ``extra_zone_*`` floats must not merge into extras."""
    o = options_for_enemy(
        "slug",
        {"slug": {"mesh": {"extra_zone_body_spike_size": 2.2, "LENGTH_BASE": 1.55}}},
    )
    assert o["zone_geometry_extras"]["body"]["spike_size"] == 1.0
    assert o["mesh"]["LENGTH_BASE"] == pytest.approx(1.55)


def test_sanitize_zone_geometry_extras_place_bools() -> None:
    got = abo._sanitize_zone_geometry_extras(
        "slug",
        {
            "body": {
                "place_top": "false",
                "place_front": 1,
                "place_bottom": 0,
            }
        },
    )
    assert got["body"]["place_top"] is False
    assert got["body"]["place_front"] is True
    assert got["body"]["place_bottom"] is False


def test_golden_slug_nested_zone_geometry_extras_spikes() -> None:
    raw = {
        "slug": {
            "zone_geometry_extras": {
                "body": {"kind": "spikes", "spike_shape": "pyramid", "spike_count": 12},
            }
        }
    }
    o = options_for_enemy("slug", raw)
    b = o["zone_geometry_extras"]["body"]
    assert b["kind"] == "spikes"
    assert b["spike_shape"] == "pyramid"
    assert b["spike_count"] == 12
    assert b["spike_size"] == 1.0
    assert b["clustering"] == 0.5
    assert b["distribution"] == "uniform"
    assert b["uniform_shape"] == "arc"


def test_zone_geometry_extras_clustering_merge_and_clamp() -> None:
    o = options_for_enemy(
        "slug",
        {"extra_zone_body_clustering": 0.2, "extra_zone_head_clustering": 9},
    )
    assert o["zone_geometry_extras"]["body"]["clustering"] == 0.2
    assert o["zone_geometry_extras"]["head"]["clustering"] == 1.0


def test_spider_eye_clustering_defaults_and_clamp() -> None:
    o = options_for_enemy("spider", {})
    assert o["eye_clustering"] == 0.5
    assert options_for_enemy("spider", {"eye_clustering": -1})["eye_clustering"] == 0.0
    assert options_for_enemy("spider", {"eye_clustering": 2})["eye_clustering"] == 1.0


def test_zone_geometry_extras_flat_keys_merge() -> None:
    o = options_for_enemy(
        "slug",
        {
            "extra_zone_body_kind": "bulbs",
            "extra_zone_body_bulb_count": 9,
            "extra_zone_body_bulb_size": 2.0,
            "extra_zone_body_finish": "metallic",
        },
    )
    b = o["zone_geometry_extras"]["body"]
    assert b["kind"] == "bulbs"
    assert b["bulb_count"] == 9
    assert b["bulb_size"] == 2.0
    assert b["finish"] == "metallic"


def test_horns_on_slug_body_coerced_to_none() -> None:
    o = options_for_enemy("slug", {"extra_zone_body_kind": "horns"})
    assert o["zone_geometry_extras"]["body"]["kind"] == "none"


def test_horns_on_slug_head_preserved() -> None:
    o = options_for_enemy("slug", {"extra_zone_head_kind": "horns", "extra_zone_head_spike_shape": "pyramid"})
    h = o["zone_geometry_extras"]["head"]
    assert h["kind"] == "horns"
    assert h["spike_shape"] == "pyramid"


def test_spike_and_bulb_counts_clamped() -> None:
    o = options_for_enemy(
        "slug",
        {"extra_zone_body_spike_count": 999, "extra_zone_extra_bulb_count": 0},
    )
    assert o["zone_geometry_extras"]["body"]["spike_count"] == 24
    assert o["zone_geometry_extras"]["extra"]["bulb_count"] == 1


def test_spike_and_bulb_sizes_clamped() -> None:
    o = options_for_enemy(
        "slug",
        {
            "extra_zone_body_spike_size": 0.01,
            "extra_zone_head_bulb_size": 99,
        },
    )
    assert o["zone_geometry_extras"]["body"]["spike_size"] == 0.25
    assert o["zone_geometry_extras"]["head"]["bulb_size"] == 3.0


def test_api_slug_includes_zone_extra_control_keys() -> None:
    ctrl = animated_build_controls_for_api()
    keys = {c["key"] for c in ctrl["slug"]}
    assert "extra_zone_body_kind" in keys
    assert "extra_zone_extra_bulb_count" in keys
    assert "extra_zone_body_spike_size" in keys
    assert "extra_zone_body_bulb_size" in keys
    assert "extra_zone_body_clustering" in keys
    assert "extra_zone_body_place_top" in keys
    assert any(c["key"] == "extra_zone_body_place_top" and c["type"] == "bool" for c in ctrl["slug"])


def test_api_spider_includes_eye_clustering_control() -> None:
    ctrl = animated_build_controls_for_api()
    keys = {c["key"] for c in ctrl["spider"]}
    assert "eye_clustering" in keys
    assert "eye_distribution" in keys
    assert "placement_seed" in keys
    ec = next(c for c in ctrl["spider"] if c["key"] == "eye_clustering")
    assert ec["type"] == "float"


def test_options_spider_eye_distribution_coerce() -> None:
    o = options_for_enemy("spider", {"eye_distribution": "random"})
    assert o["eye_distribution"] == "random"
    o2 = options_for_enemy("spider", {"eye_distribution": "bogus"})
    assert o2["eye_distribution"] == "uniform"


def test_unknown_kind_coerced_to_none() -> None:
    o = options_for_enemy("slug", {"extra_zone_body_kind": "quantum_spikes"})
    assert o["zone_geometry_extras"]["body"]["kind"] == "none"


def test_features_unchanged_when_zone_extras_set() -> None:
    o = options_for_enemy(
        "slug",
        {"feat_body_finish": "glossy", "extra_zone_body_kind": "spikes"},
    )
    assert o["features"]["body"]["finish"] == "glossy"
    assert o["zone_geometry_extras"]["body"]["kind"] == "spikes"


def test_merge_zone_extras_nested_then_flat_overwrites() -> None:
    o = options_for_enemy(
        "slug",
        {
            "slug": {
                "zone_geometry_extras": {"body": {"kind": "spikes", "spike_count": 4}},
            },
            "extra_zone_body_kind": "bulbs",
        },
    )
    assert o["zone_geometry_extras"]["body"]["kind"] == "bulbs"
    assert o["zone_geometry_extras"]["body"]["spike_count"] == 4


def test_adversarial_duplicate_zone_extra_sources_last_flat_wins_kind() -> None:
    # CHECKPOINT: flat kind after nested slug envelope wins (documented merge order).
    o = options_for_enemy(
        "slug",
        {"slug": {"zone_geometry_extras": {"body": {"kind": "shell"}}}, "extra_zone_body_kind": "none"},
    )
    assert o["zone_geometry_extras"]["body"]["kind"] == "none"


def test_merge_zone_geometry_extras_non_dict_base_zone() -> None:
    base = {"body": "bad", "head": {"kind": "spikes", "spike_count": 3}}
    got = abo._merge_zone_geometry_extras("slug", {}, base)
    assert got["body"]["kind"] == "none"
    assert got["head"]["kind"] == "spikes"
    assert got["head"]["spike_count"] == 3


def test_merge_zone_geometry_extras_nested_skips_unknown_zone() -> None:
    got = abo._merge_zone_geometry_extras(
        "slug",
        {"zone_geometry_extras": {"torso": {"kind": "spikes"}, "body": {"kind": "bulbs"}}},
        abo._default_zone_geometry_extras("slug"),
    )
    assert "torso" not in got
    assert got["body"]["kind"] == "bulbs"


def test_merge_zone_geometry_extras_flat_invalid_int_ignored() -> None:
    got = abo._merge_zone_geometry_extras(
        "slug",
        {"extra_zone_body_spike_count": "nope"},
        abo._default_zone_geometry_extras("slug"),
    )
    assert got["body"]["spike_count"] == 8


def test_merge_zone_geometry_extras_flat_invalid_float_ignored() -> None:
    got = abo._merge_zone_geometry_extras(
        "slug",
        {"extra_zone_body_spike_size": "nope"},
        abo._default_zone_geometry_extras("slug"),
    )
    assert got["body"]["spike_size"] == 1.0


def test_merge_zone_geometry_extras_flat_invalid_clustering_ignored() -> None:
    got = abo._merge_zone_geometry_extras(
        "slug",
        {"extra_zone_body_clustering": "nope"},
        abo._default_zone_geometry_extras("slug"),
    )
    assert got["body"]["clustering"] == 0.5


def test_sanitize_zone_geometry_extras_invalid_shape_and_int_fields() -> None:
    got = abo._sanitize_zone_geometry_extras(
        "slug",
        {
            "body": {
                "kind": "spikes",
                "spike_shape": "torus",
                "spike_count": "x",
                "bulb_count": [],
                "finish": "not_real",
            }
        },
    )
    assert got["body"]["spike_shape"] == "cone"
    assert got["body"]["spike_count"] == 8
    assert got["body"]["bulb_count"] == 4
    assert got["body"]["finish"] == "default"


def test_sanitize_zone_geometry_extras_float_sizes() -> None:
    got = abo._sanitize_zone_geometry_extras(
        "slug",
        {
            "body": {
                "kind": "spikes",
                "spike_size": "x",
                "bulb_size": {},
            }
        },
    )
    assert got["body"]["spike_size"] == 1.0
    assert got["body"]["bulb_size"] == 1.0


def test_merge_flat_skips_zone_absent_from_slug() -> None:
    got = abo._merge_zone_geometry_extras(
        "slug",
        {"extra_zone_joints_kind": "spikes"},
        abo._default_zone_geometry_extras("slug"),
    )
    assert "joints" not in got


def test_options_recovers_zone_geometry_extras_when_defaults_omit_key(monkeypatch) -> None:
    real = abo._defaults_for_slug

    def strip_zg(slug: str):
        d = real(slug)
        del d["zone_geometry_extras"]
        return d

    monkeypatch.setattr(abo, "_defaults_for_slug", strip_zg)
    o = options_for_enemy("slug", {})
    assert isinstance(o["zone_geometry_extras"], dict)
    assert o["zone_geometry_extras"]["body"]["kind"] == "none"


def test_coerce_zone_geometry_extras_non_dict_reset() -> None:
    base = abo._defaults_for_slug("slug")
    base["zone_geometry_extras"] = None
    out = abo._coerce_and_validate("slug", base)
    assert isinstance(out["zone_geometry_extras"], dict)
    assert out["zone_geometry_extras"]["body"]["kind"] == "none"

