"""
animated_build_options — zone extras offset_x/y/z controls.

Spec: project_board/specs/zone_extras_offset_xyz_controls_spec.md  Requirements 1–6, 10
Ticket: 17_zone_extras_offset_xyz_controls

Covers:
  Req 1 — Constants and key schema (AC-1.1 to AC-1.7)
  Req 2 — Merge logic, flat and nested paths (AC-2.1 to AC-2.7)
  Req 3 — Sanitize logic, clamp and reset (AC-3.1 to AC-3.8)
  Req 4 — Control definitions shape and ordering (AC-4.1 to AC-4.4)
  Req 6 — Round-trip via options_for_enemy (AC-6.1 to AC-6.6)
  Req 10 — Backward compatibility (AC-10.2, AC-10.3)
"""

from src.utils import build_options as abo
from src.utils.build_options import (
    animated_build_controls_for_api,
    options_for_enemy,
)

# ---------------------------------------------------------------------------
# Requirement 1: Constants and key schema — offset_x / offset_y / offset_z
# ---------------------------------------------------------------------------


def test_offset_xyz_constants_defined_and_typed() -> None:
    """AC-1.1: _OFFSET_XYZ_MIN, _OFFSET_XYZ_MAX, _OFFSET_XYZ_STEP exist as floats."""
    assert hasattr(abo, "_OFFSET_XYZ_MIN"), "_OFFSET_XYZ_MIN must be defined"
    assert hasattr(abo, "_OFFSET_XYZ_MAX"), "_OFFSET_XYZ_MAX must be defined"
    assert hasattr(abo, "_OFFSET_XYZ_STEP"), "_OFFSET_XYZ_STEP must be defined"
    assert isinstance(abo._OFFSET_XYZ_MIN, float), "_OFFSET_XYZ_MIN must be float"
    assert isinstance(abo._OFFSET_XYZ_MAX, float), "_OFFSET_XYZ_MAX must be float"
    assert isinstance(abo._OFFSET_XYZ_STEP, float), "_OFFSET_XYZ_STEP must be float"
    assert abo._OFFSET_XYZ_MIN == -2.0
    assert abo._OFFSET_XYZ_MAX == 2.0
    assert abo._OFFSET_XYZ_STEP == 0.05


def test_extra_zone_flat_key_matches_offset_xyz_for_all_zones() -> None:
    """AC-1.2: _EXTRA_ZONE_FLAT_KEY matches offset_x/y/z for every valid zone."""
    zones = ("body", "head", "limbs", "joints", "extra")
    axes = ("offset_x", "offset_y", "offset_z")
    for zone in zones:
        for axis in axes:
            key = f"extra_zone_{zone}_{axis}"
            assert abo._EXTRA_ZONE_FLAT_KEY.match(key) is not None, f"regex should match {key!r}"


def test_extra_zone_flat_key_rejects_offset_w() -> None:
    """AC-1.3: _EXTRA_ZONE_FLAT_KEY must not match 'extra_zone_body_offset_w'."""
    assert abo._EXTRA_ZONE_FLAT_KEY.match("extra_zone_body_offset_w") is None


def test_extra_zone_flat_key_captures_zone_and_suffix() -> None:
    """AC-1.4: capture groups are (zone, suffix) for an offset_x key."""
    m = abo._EXTRA_ZONE_FLAT_KEY.match("extra_zone_body_offset_x")
    assert m is not None
    assert m.group(1) == "body"
    assert m.group(2) == "offset_x"


def test_zone_geom_extra_fields_contains_offset_xyz() -> None:
    """AC-1.5: _ZONE_GEOM_EXTRA_FIELDS includes offset_x, offset_y, offset_z."""
    assert "offset_x" in abo._ZONE_GEOM_EXTRA_FIELDS
    assert "offset_y" in abo._ZONE_GEOM_EXTRA_FIELDS
    assert "offset_z" in abo._ZONE_GEOM_EXTRA_FIELDS


def test_default_zone_geometry_extras_payload_has_offset_defaults() -> None:
    """AC-1.6: _default_zone_geometry_extras_payload returns offset_x/y/z = 0.0."""
    payload = abo._default_zone_geometry_extras_payload()
    assert payload.get("offset_x") == 0.0
    assert payload.get("offset_y") == 0.0
    assert payload.get("offset_z") == 0.0


def test_default_zone_geometry_extras_payload_preserves_existing_keys() -> None:
    """AC-1.7: Existing keys (kind, spike_count, etc.) remain in default payload."""
    payload = abo._default_zone_geometry_extras_payload()
    pre_existing = (
        "kind", "spike_shape", "spike_count", "spike_size",
        "bulb_count", "bulb_size", "clustering", "distribution",
        "uniform_shape", "finish", "hex",
        "place_top", "place_bottom", "place_front",
        "place_back", "place_left", "place_right",
    )
    for key in pre_existing:
        assert key in payload, f"pre-existing key {key!r} missing from default payload"


# ---------------------------------------------------------------------------
# Requirement 2: Merge logic — flat and nested paths for offset_x/y/z
# ---------------------------------------------------------------------------


def test_merge_zone_extras_flat_offset_x() -> None:
    """AC-2.1: flat key extra_zone_body_offset_x sets body.offset_x."""
    got = abo._merge_zone_geometry_extras(
        "slug",
        {"extra_zone_body_offset_x": 1.5},
        abo._default_zone_geometry_extras("slug"),
    )
    assert got["body"]["offset_x"] == 1.5


def test_merge_zone_extras_nested_offset_y() -> None:
    """AC-2.2: nested zone_geometry_extras.body.offset_y sets body.offset_y."""
    got = abo._merge_zone_geometry_extras(
        "slug",
        {"zone_geometry_extras": {"body": {"offset_y": -0.75}}},
        abo._default_zone_geometry_extras("slug"),
    )
    assert got["body"]["offset_y"] == -0.75


def test_merge_zone_extras_flat_wins_over_nested_offset_z() -> None:
    """AC-2.3: flat key wins over nested when both specify the same field."""
    got = abo._merge_zone_geometry_extras(
        "slug",
        {
            "zone_geometry_extras": {"body": {"offset_z": 0.5}},
            "extra_zone_body_offset_z": 1.0,
        },
        abo._default_zone_geometry_extras("slug"),
    )
    assert got["body"]["offset_z"] == 1.0


def test_merge_zone_extras_invalid_string_offset_x_ignored() -> None:
    """AC-2.4: non-numeric string for offset_x leaves field at default (0.0)."""
    got = abo._merge_zone_geometry_extras(
        "slug",
        {"extra_zone_body_offset_x": "not_a_number"},
        abo._default_zone_geometry_extras("slug"),
    )
    assert got["body"]["offset_x"] == 0.0


def test_merge_zone_extras_absent_offsets_default_to_zero() -> None:
    """AC-2.5: when no offset keys in src, all three offsets equal base defaults (0.0)."""
    got = abo._merge_zone_geometry_extras(
        "slug",
        {},
        abo._default_zone_geometry_extras("slug"),
    )
    assert got["body"]["offset_x"] == 0.0
    assert got["body"]["offset_y"] == 0.0
    assert got["body"]["offset_z"] == 0.0


def test_merge_zone_extras_out_of_range_offset_preserved() -> None:
    """AC-2.6: out-of-range values pass through merge unclamped (clamping is sanitize's job)."""
    got = abo._merge_zone_geometry_extras(
        "slug",
        {"extra_zone_body_offset_x": 5.0},
        abo._default_zone_geometry_extras("slug"),
    )
    assert got["body"]["offset_x"] == 5.0


def test_merge_zone_extras_offset_for_absent_zone_ignored() -> None:
    """AC-2.7: offset key for a zone not in the slug's zones is silently ignored."""
    # slug has body/head/extra — no joints zone
    got = abo._merge_zone_geometry_extras(
        "slug",
        {"extra_zone_joints_offset_x": 1.0},
        abo._default_zone_geometry_extras("slug"),
    )
    assert "joints" not in got


# ---------------------------------------------------------------------------
# Requirement 3: Sanitize logic — clamp and invalid reset for offset_x/y/z
# ---------------------------------------------------------------------------


def test_sanitize_offset_x_clamped_to_max() -> None:
    """AC-3.1: offset_x = 5.0 is clamped to 2.0."""
    got = abo._sanitize_zone_geometry_extras("slug", {"body": {"offset_x": 5.0}})
    assert got["body"]["offset_x"] == 2.0


def test_sanitize_offset_y_clamped_to_min() -> None:
    """AC-3.2: offset_y = -3.0 is clamped to -2.0."""
    got = abo._sanitize_zone_geometry_extras("slug", {"body": {"offset_y": -3.0}})
    assert got["body"]["offset_y"] == -2.0


def test_sanitize_offset_z_invalid_string_resets_to_zero() -> None:
    """AC-3.3: string value for offset_z resets to 0.0."""
    got = abo._sanitize_zone_geometry_extras("slug", {"body": {"offset_z": "bad"}})
    assert got["body"]["offset_z"] == 0.0


def test_sanitize_offset_x_zero_passes_through() -> None:
    """AC-3.4: offset_x = 0.0 is the identity — stays 0.0."""
    got = abo._sanitize_zone_geometry_extras("slug", {"body": {"offset_x": 0.0}})
    assert got["body"]["offset_x"] == 0.0


def test_sanitize_offset_x_at_max_boundary_not_over_clamped() -> None:
    """AC-3.5: offset_x = 2.0 (exact max) passes through unchanged."""
    got = abo._sanitize_zone_geometry_extras("slug", {"body": {"offset_x": 2.0}})
    assert got["body"]["offset_x"] == 2.0


def test_sanitize_offset_x_at_min_boundary_not_over_clamped() -> None:
    """AC-3.6: offset_x = -2.0 (exact min) passes through unchanged."""
    got = abo._sanitize_zone_geometry_extras("slug", {"body": {"offset_x": -2.0}})
    assert got["body"]["offset_x"] == -2.0


def test_sanitize_missing_offset_keys_default_to_zero() -> None:
    """AC-3.7: zones without offset keys in input produce offset_x/y/z = 0.0."""
    got = abo._sanitize_zone_geometry_extras("slug", {"body": {"kind": "spikes"}})
    assert got["body"]["offset_x"] == 0.0
    assert got["body"]["offset_y"] == 0.0
    assert got["body"]["offset_z"] == 0.0


def test_sanitize_offset_isolation_between_zones() -> None:
    """AC-3.8: sanitizing one zone's offset does not affect another zone's offset fields."""
    got = abo._sanitize_zone_geometry_extras(
        "slug",
        {
            "body": {"offset_x": 1.5},
            "head": {"offset_x": -0.5},
        },
    )
    assert got["body"]["offset_x"] == 1.5
    assert got["head"]["offset_x"] == -0.5


# ---------------------------------------------------------------------------
# Requirement 4: Control definitions — _zone_extra_control_defs
# ---------------------------------------------------------------------------


def test_zone_extra_control_defs_includes_offset_xyz_for_all_zones() -> None:
    """AC-4.1: _zone_extra_control_defs returns offset_x/y/z defs for every zone."""
    defs = abo._zone_extra_control_defs("slug")
    keys = {d["key"] for d in defs}
    for zone in abo._feature_zones("slug"):
        assert f"extra_zone_{zone}_offset_x" in keys, f"missing offset_x for zone {zone}"
        assert f"extra_zone_{zone}_offset_y" in keys, f"missing offset_y for zone {zone}"
        assert f"extra_zone_{zone}_offset_z" in keys, f"missing offset_z for zone {zone}"


def test_zone_extra_control_defs_offset_shape_and_values() -> None:
    """AC-4.2: each offset def has type=float, min=-2.0, max=2.0, step=0.05, default=0.0."""
    defs = abo._zone_extra_control_defs("slug")
    offset_defs = [d for d in defs if d["key"].endswith(("_offset_x", "_offset_y", "_offset_z"))]
    assert len(offset_defs) > 0, "no offset defs found"
    for d in offset_defs:
        assert d["type"] == "float", f"{d['key']}: expected type=float"
        assert d["min"] == -2.0, f"{d['key']}: expected min=-2.0"
        assert d["max"] == 2.0, f"{d['key']}: expected max=2.0"
        assert d["step"] == 0.05, f"{d['key']}: expected step=0.05"
        assert d["default"] == 0.0, f"{d['key']}: expected default=0.0"


def test_zone_extra_control_defs_offset_xyz_after_hex() -> None:
    """AC-4.3: offset_x/y/z defs appear after the hex def in the per-zone def list."""
    defs = abo._zone_extra_control_defs("slug")
    body_defs = [d for d in defs if d["key"].startswith("extra_zone_body_")]
    keys = [d["key"] for d in body_defs]
    assert "extra_zone_body_hex" in keys, "hex def must be present"
    assert "extra_zone_body_offset_x" in keys, "offset_x def must be present"
    hex_idx = keys.index("extra_zone_body_hex")
    ox_idx = keys.index("extra_zone_body_offset_x")
    oy_idx = keys.index("extra_zone_body_offset_y")
    oz_idx = keys.index("extra_zone_body_offset_z")
    assert ox_idx > hex_idx, "offset_x must come after hex"
    assert oy_idx > hex_idx, "offset_y must come after hex"
    assert oz_idx > hex_idx, "offset_z must come after hex"


def test_animated_build_controls_for_api_imp_includes_offset_x() -> None:
    """AC-4.4: animated_build_controls_for_api()['imp'] includes extra_zone_body_offset_x."""
    ctrl = animated_build_controls_for_api()
    keys = {c["key"] for c in ctrl["imp"]}
    assert "extra_zone_body_offset_x" in keys


# ---------------------------------------------------------------------------
# Requirement 6: Round-trip via options_for_enemy
# ---------------------------------------------------------------------------


def test_options_for_enemy_flat_offset_x_round_trip() -> None:
    """AC-6.1: flat key extra_zone_body_offset_x=1.0 survives full pipeline."""
    o = options_for_enemy("imp", {"extra_zone_body_offset_x": 1.0})
    assert o["zone_geometry_extras"]["body"]["offset_x"] == 1.0


def test_options_for_enemy_nested_offset_y_round_trip() -> None:
    """AC-6.2: nested zone_geometry_extras.body.offset_y=-1.0 survives full pipeline."""
    o = options_for_enemy("imp", {"zone_geometry_extras": {"body": {"offset_y": -1.0}}})
    assert o["zone_geometry_extras"]["body"]["offset_y"] == -1.0


def test_options_for_enemy_flat_offset_z_out_of_range_clamped() -> None:
    """AC-6.3: flat offset_z=5.0 is clamped to 2.0 by sanitize step."""
    o = options_for_enemy("imp", {"extra_zone_body_offset_z": 5.0})
    assert o["zone_geometry_extras"]["body"]["offset_z"] == 2.0


def test_options_for_enemy_default_offset_when_absent() -> None:
    """AC-6.4: offset_x defaults to 0.0 when not specified."""
    o = options_for_enemy("imp", {})
    assert o["zone_geometry_extras"]["body"]["offset_x"] == 0.0


def test_options_for_enemy_slug_flat_offset_x() -> None:
    """AC-6.5: slug enemy also handles flat offset_x correctly."""
    o = options_for_enemy("slug", {"extra_zone_body_offset_x": 0.5})
    assert o["zone_geometry_extras"]["body"]["offset_x"] == 0.5


def test_options_for_enemy_body_offset_does_not_affect_head_offset() -> None:
    """AC-6.6: setting body offset_x does not change head zone offset_x."""
    o = options_for_enemy("slug", {"extra_zone_body_offset_x": 0.5})
    assert o["zone_geometry_extras"]["head"]["offset_x"] == 0.0


# ---------------------------------------------------------------------------
# Requirement 10: Backward compatibility
# ---------------------------------------------------------------------------


def test_options_for_enemy_backward_compat_no_offset_keys() -> None:
    """AC-10.2/10.3: legacy JSON without offset keys produces 0.0 defaults and no crash."""
    o = options_for_enemy("imp", {})
    assert o["zone_geometry_extras"]["body"]["offset_x"] == 0.0
    assert o["zone_geometry_extras"]["body"]["offset_y"] == 0.0
    assert o["zone_geometry_extras"]["body"]["offset_z"] == 0.0


def test_options_for_enemy_existing_keys_intact_with_offsets() -> None:
    """AC-10.3: existing spike settings preserved alongside new offset defaults."""
    o = options_for_enemy(
        "imp",
        {"zone_geometry_extras": {"body": {"kind": "spikes", "spike_count": 8}}},
    )
    b = o["zone_geometry_extras"]["body"]
    assert b["kind"] == "spikes"
    assert b["spike_count"] == 8
    assert b["offset_x"] == 0.0
    assert b["offset_y"] == 0.0
    assert b["offset_z"] == 0.0
