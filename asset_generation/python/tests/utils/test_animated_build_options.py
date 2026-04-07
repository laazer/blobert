"""animated_build_options: defaults, nesting, and coercion."""

from src.utils.animated_build_options import (
    animated_build_controls_for_api,
    options_for_enemy,
    parse_build_options_json,
)


def test_defaults_spider() -> None:
    o = options_for_enemy("spider", {})
    assert o["eye_count"] == 2


def test_nested_slug_object() -> None:
    o = options_for_enemy("spider", {"spider": {"eye_count": 4}})
    assert o["eye_count"] == 4


def test_flat_keys_for_current_slug() -> None:
    o = options_for_enemy("spider", {"eye_count": 4})
    assert o["eye_count"] == 4


def test_invalid_select_falls_back() -> None:
    o = options_for_enemy("spider", {"eye_count": 99})
    assert o["eye_count"] == 2


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
