"""animated_build_options: defaults, nesting, and coercion."""

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
    o = options_for_enemy("spider", {"eye_count": 99})
    assert o["eye_count"] == 2


def test_spider_eye_count_extended_options() -> None:
    o = options_for_enemy("spider", {"eye_count": 10})
    assert o["eye_count"] == 10
    ctrl = animated_build_controls_for_api()
    eye = next(c for c in ctrl["spider"] if c["key"] == "eye_count")
    assert eye["options"][-1] == 12
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


def test_api_spider_includes_zone_and_part_material_keys() -> None:
    ctrl = animated_build_controls_for_api()
    keys = {c["key"] for c in ctrl["spider"]}
    assert "feat_joints_finish" in keys
    assert "feat_joints_hex" in keys
    assert "feat_limb_leg_0_hex" in keys
    assert "feat_joint_leg_0_root_hex" in keys


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
