"""
animated_build_options — shell_scale field specification tests.

Spec: project_board/specs/enemy_body_part_extras_spec.md  §shell_scale field specification
Ticket: extras-shell-visible-spikes-on-top

AC traceability:
  AC-SS1 — Constants: _SHELL_SCALE_MIN = 1.01, _SHELL_SCALE_MAX = 1.5 defined as floats
  AC-SS2 — shell_scale present in _ZONE_GEOM_EXTRA_FIELDS frozenset
  AC-SS3 — _EXTRA_ZONE_FLAT_KEY regex matches extra_zone_<zone>_shell_scale for all zones
  AC-SS4 — _default_zone_geometry_extras_payload() returns shell_scale = 1.08
  AC-SS5 — Sanitize clamp: values < 1.01 clamped to 1.01
  AC-SS6 — Sanitize clamp: values > 1.5 clamped to 1.5
  AC-SS7 — Sanitize invalid type: non-numeric shell_scale resets to 1.08
  AC-SS8 — Control def: _zone_extra_control_defs returns shell_scale float def per zone

Round-trip via options_for_enemy:
  AC-RT1 — flat key extra_zone_body_shell_scale=1.2 survives full pipeline (slug)
  AC-RT2 — shell_scale=1.08 default present in options output when not specified
  AC-RT3 — shell_scale out-of-range clamped through full pipeline
"""

import math

from src.utils import build_options as abo
from src.utils.build_options import (
    _merge_zone_geometry_extras,
    options_for_enemy,
)

# ---------------------------------------------------------------------------
# AC-SS1: Constants defined
# ---------------------------------------------------------------------------


def test_shell_scale_min_constant_defined_and_typed() -> None:
    """AC-SS1a: _SHELL_SCALE_MIN exists, is float, equals 1.01."""
    assert hasattr(abo, "_SHELL_SCALE_MIN"), "_SHELL_SCALE_MIN must be defined in animated_build_options"
    assert isinstance(abo._SHELL_SCALE_MIN, float), "_SHELL_SCALE_MIN must be a float"
    assert abo._SHELL_SCALE_MIN == 1.01, f"expected _SHELL_SCALE_MIN=1.01, got {abo._SHELL_SCALE_MIN}"


def test_shell_scale_max_constant_defined_and_typed() -> None:
    """AC-SS1b: _SHELL_SCALE_MAX exists, is float, equals 1.5."""
    assert hasattr(abo, "_SHELL_SCALE_MAX"), "_SHELL_SCALE_MAX must be defined in animated_build_options"
    assert isinstance(abo._SHELL_SCALE_MAX, float), "_SHELL_SCALE_MAX must be a float"
    assert abo._SHELL_SCALE_MAX == 1.5, f"expected _SHELL_SCALE_MAX=1.5, got {abo._SHELL_SCALE_MAX}"


# ---------------------------------------------------------------------------
# AC-SS2: Frozenset membership
# ---------------------------------------------------------------------------


def test_zone_geom_extra_fields_contains_shell_scale() -> None:
    """AC-SS2: _ZONE_GEOM_EXTRA_FIELDS includes 'shell_scale'."""
    assert "shell_scale" in abo._ZONE_GEOM_EXTRA_FIELDS, (
        "'shell_scale' must be present in _ZONE_GEOM_EXTRA_FIELDS frozenset"
    )


# ---------------------------------------------------------------------------
# AC-SS3: Regex matching
# ---------------------------------------------------------------------------


def test_extra_zone_flat_key_matches_shell_scale_for_all_zones() -> None:
    """AC-SS3: _EXTRA_ZONE_FLAT_KEY matches extra_zone_<zone>_shell_scale for every valid zone."""
    zones = ("body", "head", "limbs", "joints", "extra")
    for zone in zones:
        key = f"extra_zone_{zone}_shell_scale"
        assert abo._EXTRA_ZONE_FLAT_KEY.match(key) is not None, (
            f"_EXTRA_ZONE_FLAT_KEY regex should match {key!r}"
        )


def test_extra_zone_flat_key_captures_shell_scale_suffix() -> None:
    """AC-SS3 capture groups: match on extra_zone_body_shell_scale gives (zone='body', suffix='shell_scale')."""
    m = abo._EXTRA_ZONE_FLAT_KEY.match("extra_zone_body_shell_scale")
    assert m is not None, "_EXTRA_ZONE_FLAT_KEY must match 'extra_zone_body_shell_scale'"
    assert m.group(1) == "body", f"expected zone group 'body', got {m.group(1)!r}"
    assert m.group(2) == "shell_scale", f"expected suffix group 'shell_scale', got {m.group(2)!r}"


def test_extra_zone_flat_key_rejects_shell_size_typo() -> None:
    """AC-SS3 negative: _EXTRA_ZONE_FLAT_KEY must not match 'extra_zone_body_shell_size' (invalid suffix)."""
    assert abo._EXTRA_ZONE_FLAT_KEY.match("extra_zone_body_shell_size") is None, (
        "_EXTRA_ZONE_FLAT_KEY must not match 'extra_zone_body_shell_size'"
    )


# ---------------------------------------------------------------------------
# AC-SS4: Default payload
# ---------------------------------------------------------------------------


def test_default_zone_geometry_extras_payload_has_shell_scale() -> None:
    """AC-SS4: _default_zone_geometry_extras_payload() returns 'shell_scale' == 1.08."""
    payload = abo._default_zone_geometry_extras_payload()
    assert "shell_scale" in payload, (
        "'shell_scale' key must be present in _default_zone_geometry_extras_payload() output"
    )
    assert payload["shell_scale"] == 1.08, (
        f"expected shell_scale default=1.08, got {payload['shell_scale']}"
    )


def test_default_zone_geometry_extras_payload_preserves_existing_keys_with_shell_scale() -> None:
    """AC-SS4 compat: Adding shell_scale does not remove pre-existing payload keys."""
    payload = abo._default_zone_geometry_extras_payload()
    pre_existing = (
        "kind", "spike_shape", "spike_count", "spike_size",
        "bulb_count", "bulb_size", "clustering", "distribution",
        "uniform_shape", "finish", "hex",
        "place_top", "place_bottom", "place_front",
        "place_back", "place_left", "place_right",
        "offset_x", "offset_y", "offset_z",
    )
    for key in pre_existing:
        assert key in payload, f"pre-existing key {key!r} missing from default payload after adding shell_scale"


# ---------------------------------------------------------------------------
# AC-SS5/SS6: Sanitize clamping
# ---------------------------------------------------------------------------


def test_sanitize_shell_scale_below_min_clamped() -> None:
    """AC-SS5: shell_scale = 0.5 (below min 1.01) is clamped to 1.01."""
    got = abo._sanitize_zone_geometry_extras("slug", {"body": {"shell_scale": 0.5}})
    assert got["body"]["shell_scale"] == 1.01, (
        f"shell_scale 0.5 should be clamped to 1.01, got {got['body']['shell_scale']}"
    )


def test_sanitize_shell_scale_above_max_clamped() -> None:
    """AC-SS6: shell_scale = 2.0 (above max 1.5) is clamped to 1.5."""
    got = abo._sanitize_zone_geometry_extras("slug", {"body": {"shell_scale": 2.0}})
    assert got["body"]["shell_scale"] == 1.5, (
        f"shell_scale 2.0 should be clamped to 1.5, got {got['body']['shell_scale']}"
    )


def test_sanitize_shell_scale_at_min_boundary_not_over_clamped() -> None:
    """AC-SS5 boundary: shell_scale = 1.01 (exact min) passes through unchanged."""
    got = abo._sanitize_zone_geometry_extras("slug", {"body": {"shell_scale": 1.01}})
    assert abs(got["body"]["shell_scale"] - 1.01) < 1e-9, (
        f"shell_scale 1.01 at exact min should pass through, got {got['body']['shell_scale']}"
    )


def test_sanitize_shell_scale_at_max_boundary_not_over_clamped() -> None:
    """AC-SS6 boundary: shell_scale = 1.5 (exact max) passes through unchanged."""
    got = abo._sanitize_zone_geometry_extras("slug", {"body": {"shell_scale": 1.5}})
    assert abs(got["body"]["shell_scale"] - 1.5) < 1e-9, (
        f"shell_scale 1.5 at exact max should pass through, got {got['body']['shell_scale']}"
    )


def test_sanitize_shell_scale_in_range_preserved() -> None:
    """AC-SS5/SS6: shell_scale = 1.2 (in range) passes through unchanged."""
    got = abo._sanitize_zone_geometry_extras("slug", {"body": {"shell_scale": 1.2}})
    assert abs(got["body"]["shell_scale"] - 1.2) < 1e-9, (
        f"shell_scale 1.2 in range should be preserved, got {got['body']['shell_scale']}"
    )


# ---------------------------------------------------------------------------
# AC-SS7: Invalid type resets to default
# ---------------------------------------------------------------------------


def test_sanitize_shell_scale_string_resets_to_default() -> None:
    """AC-SS7: non-numeric shell_scale string → resets to 1.08 (default)."""
    got = abo._sanitize_zone_geometry_extras("slug", {"body": {"shell_scale": "invalid"}})
    assert got["body"]["shell_scale"] == 1.08, (
        f"shell_scale 'invalid' (non-numeric) should reset to 1.08, got {got['body']['shell_scale']}"
    )


def test_sanitize_shell_scale_none_resets_to_default() -> None:
    """AC-SS7: None shell_scale → resets to 1.08 (default)."""
    got = abo._sanitize_zone_geometry_extras("slug", {"body": {"shell_scale": None}})
    assert got["body"]["shell_scale"] == 1.08, (
        f"shell_scale None should reset to 1.08, got {got['body']['shell_scale']}"
    )


def test_sanitize_shell_scale_missing_uses_default() -> None:
    """AC-SS4/SS7: when shell_scale absent from zone dict, default 1.08 is used."""
    got = abo._sanitize_zone_geometry_extras("slug", {"body": {"kind": "shell"}})
    assert got["body"]["shell_scale"] == 1.08, (
        f"missing shell_scale should default to 1.08, got {got['body']['shell_scale']}"
    )


# ---------------------------------------------------------------------------
# AC-SS8: Control def shape
# ---------------------------------------------------------------------------


def test_zone_extra_control_defs_includes_shell_scale_for_all_zones() -> None:
    """AC-SS8: _zone_extra_control_defs returns a shell_scale def for every zone of slug."""
    defs = abo._zone_extra_control_defs("slug")
    keys = {d["key"] for d in defs}
    for zone in abo._feature_zones("slug"):
        expected_key = f"extra_zone_{zone}_shell_scale"
        assert expected_key in keys, (
            f"missing shell_scale control def for zone {zone!r}: key {expected_key!r} not found"
        )


def test_zone_extra_control_defs_shell_scale_shape_and_values() -> None:
    """AC-SS8: each shell_scale def has type=float, min=1.01, max=1.5, step=0.01, default=1.08."""
    defs = abo._zone_extra_control_defs("slug")
    shell_scale_defs = [d for d in defs if d["key"].endswith("_shell_scale")]
    assert len(shell_scale_defs) > 0, "no shell_scale control defs found in _zone_extra_control_defs"
    for d in shell_scale_defs:
        assert d["type"] == "float", f"{d['key']}: expected type=float, got {d['type']!r}"
        assert d["min"] == 1.01, f"{d['key']}: expected min=1.01, got {d['min']}"
        assert d["max"] == 1.5, f"{d['key']}: expected max=1.5, got {d['max']}"
        assert d["step"] == 0.01, f"{d['key']}: expected step=0.01, got {d['step']}"
        assert d["default"] == 1.08, f"{d['key']}: expected default=1.08, got {d['default']}"


def test_zone_extra_control_defs_shell_scale_has_label() -> None:
    """AC-SS8: shell_scale control def has a non-empty label containing 'shell scale'."""
    defs = abo._zone_extra_control_defs("slug")
    shell_scale_defs = [d for d in defs if d["key"].endswith("_shell_scale")]
    assert len(shell_scale_defs) > 0
    for d in shell_scale_defs:
        label = d.get("label", "")
        assert "shell scale" in label.lower(), (
            f"{d['key']}: label {label!r} should mention 'shell scale'"
        )


def test_animated_build_controls_for_api_includes_shell_scale_for_slug() -> None:
    """AC-SS8: animated_build_controls_for_api()['slug'] includes extra_zone_body_shell_scale."""
    from src.utils.build_options import animated_build_controls_for_api
    ctrl = animated_build_controls_for_api()
    assert "slug" in ctrl, "slug must appear in animated_build_controls_for_api() output"
    keys = {c["key"] for c in ctrl["slug"]}
    assert "extra_zone_body_shell_scale" in keys, (
        "extra_zone_body_shell_scale must be present in animated_build_controls_for_api()['slug']"
    )


# ---------------------------------------------------------------------------
# AC-RT1/RT2/RT3: Round-trip via options_for_enemy
# ---------------------------------------------------------------------------


def test_options_for_enemy_flat_shell_scale_round_trip() -> None:
    """AC-RT1: flat key extra_zone_body_shell_scale=1.2 survives full pipeline for slug."""
    o = options_for_enemy("slug", {"extra_zone_body_shell_scale": 1.2})
    result = o["zone_geometry_extras"]["body"]["shell_scale"]
    assert abs(result - 1.2) < 1e-9, (
        f"expected shell_scale=1.2 after round-trip, got {result}"
    )


def test_options_for_enemy_default_shell_scale_when_absent() -> None:
    """AC-RT2: shell_scale defaults to 1.08 when not specified in options_for_enemy."""
    o = options_for_enemy("slug", {})
    result = o["zone_geometry_extras"]["body"]["shell_scale"]
    assert result == 1.08, (
        f"expected default shell_scale=1.08 when absent, got {result}"
    )


def test_options_for_enemy_shell_scale_out_of_range_clamped() -> None:
    """AC-RT3: flat shell_scale=0.5 is clamped to 1.01 through full pipeline."""
    o = options_for_enemy("slug", {"extra_zone_body_shell_scale": 0.5})
    result = o["zone_geometry_extras"]["body"]["shell_scale"]
    assert result == 1.01, (
        f"expected shell_scale 0.5 clamped to 1.01, got {result}"
    )


def test_options_for_enemy_shell_scale_max_clamp_round_trip() -> None:
    """AC-RT3: flat shell_scale=3.0 (above max 1.5) is clamped to 1.5."""
    o = options_for_enemy("slug", {"extra_zone_body_shell_scale": 3.0})
    result = o["zone_geometry_extras"]["body"]["shell_scale"]
    assert result == 1.5, (
        f"expected shell_scale 3.0 clamped to 1.5, got {result}"
    )


def test_options_for_enemy_shell_scale_does_not_affect_head_zone() -> None:
    """AC-RT1 isolation: setting body shell_scale does not change head zone shell_scale."""
    o = options_for_enemy("slug", {"extra_zone_body_shell_scale": 1.3})
    head_result = o["zone_geometry_extras"]["head"]["shell_scale"]
    assert head_result == 1.08, (
        f"head shell_scale should remain 1.08 (default) when only body shell_scale is set; got {head_result}"
    )


def test_options_for_enemy_nested_shell_scale_round_trip() -> None:
    """AC-RT1 nested: zone_geometry_extras.body.shell_scale=1.25 survives full pipeline."""
    o = options_for_enemy("slug", {"zone_geometry_extras": {"body": {"shell_scale": 1.25}}})
    result = o["zone_geometry_extras"]["body"]["shell_scale"]
    assert abs(result - 1.25) < 1e-9, (
        f"nested shell_scale=1.25 should round-trip, got {result}"
    )


def test_options_for_enemy_shell_scale_present_for_imp() -> None:
    """AC-RT2: shell_scale defaults to 1.08 for imp (non-slug enemy) — field always present."""
    o = options_for_enemy("imp", {})
    result = o["zone_geometry_extras"]["body"]["shell_scale"]
    assert result == 1.08, (
        f"expected shell_scale default 1.08 for imp, got {result}"
    )


# ---------------------------------------------------------------------------
# ADVERSARIAL — NaN / inf, merge order, string coercion
# ---------------------------------------------------------------------------


def test_sanitize_shell_scale_nan_resets_to_default() -> None:
    """
    ADV: float('nan') must not poison clamp (min/max with NaN stays NaN in Python).

    Parity with offset_xyz handling in the same sanitize function.
    """
    got = abo._sanitize_zone_geometry_extras("slug", {"body": {"shell_scale": float("nan")}})
    assert got["body"]["shell_scale"] == 1.08, (
        f"NaN shell_scale should reset to default 1.08, got {got['body']['shell_scale']}"
    )
    assert not math.isnan(float(got["body"]["shell_scale"]))


def test_sanitize_shell_scale_negative_infinity_clamped_to_min() -> None:
    """ADV: -inf coerces through float() then must clamp to 1.01, not crash."""
    got = abo._sanitize_zone_geometry_extras("slug", {"body": {"shell_scale": float("-inf")}})
    assert got["body"]["shell_scale"] == 1.01, (
        f"-inf shell_scale should clamp to min 1.01, got {got['body']['shell_scale']}"
    )


def test_options_for_enemy_root_flat_shell_scale_overrides_slug_envelope_nested() -> None:
    """
    ADV merge order: options_for_enemy applies root-level flat keys after the slug dict merge.

    Catches: second _merge_zone_geometry_extras pass omitted for shell_scale flat keys.
    """
    raw = {
        "slug": {"zone_geometry_extras": {"body": {"shell_scale": 1.1}}},
        "extra_zone_body_shell_scale": 1.35,
    }
    o = options_for_enemy("slug", raw)
    assert abs(o["zone_geometry_extras"]["body"]["shell_scale"] - 1.35) < 1e-9


def test_merge_zone_geometry_extras_coerces_shell_scale_numeric_string() -> None:
    """
    ADV: Flat API may send JSON numbers as strings; merge + sanitize must yield float.

    Requires shell_scale in the merge float-coercion branch (alongside spike_size).
    """
    base = abo._default_zone_geometry_extras("slug")
    merged = _merge_zone_geometry_extras(
        "slug",
        {"extra_zone_body_shell_scale": "1.22"},
        base,
    )
    sanitized = abo._sanitize_zone_geometry_extras("slug", merged)
    assert abs(sanitized["body"]["shell_scale"] - 1.22) < 1e-9


def test_options_for_enemy_body_and_head_shell_scale_independent() -> None:
    """ADV combinatorial: both zones set; neither bleeds into the other."""
    o = options_for_enemy(
        "slug",
        {
            "extra_zone_body_shell_scale": 1.11,
            "extra_zone_head_shell_scale": 1.44,
        },
    )
    assert abs(o["zone_geometry_extras"]["body"]["shell_scale"] - 1.11) < 1e-9
    assert abs(o["zone_geometry_extras"]["head"]["shell_scale"] - 1.44) < 1e-9


def test_sanitize_shell_scale_just_below_min_epsilon_clamped() -> None:
    """ADV boundary: 1.009 (just below 1.01) clamps up to 1.01."""
    got = abo._sanitize_zone_geometry_extras("slug", {"body": {"shell_scale": 1.009}})
    assert got["body"]["shell_scale"] == 1.01


def test_sanitize_shell_scale_just_above_max_epsilon_clamped() -> None:
    """ADV boundary: 1.5001 clamps down to 1.5."""
    got = abo._sanitize_zone_geometry_extras("slug", {"body": {"shell_scale": 1.5001}})
    assert abs(got["body"]["shell_scale"] - 1.5) < 1e-9
