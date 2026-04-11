"""
animated_build_options — zone extras offset_x/y/z ADVERSARIAL tests.

Spec: project_board/specs/zone_extras_offset_xyz_controls_spec.md  Requirements 1–6
Ticket: 17_zone_extras_offset_xyz_controls
Agent: Test Breaker Agent

These tests extend the primary test suite with mutation, edge-case, and
cross-contamination scenarios that the primary tests do not cover.  Every test
that encodes a conservative assumption about unspecified behaviour is marked
with a ``# CHECKPOINT`` comment.

Adversarial dimensions covered:
  - Cross-zone contamination: body offset must not leak into head zone
  - Float edge cases: NaN, +Inf, -Inf as offset values (sanitize gate)
  - Partial field presence: zone dict has offset_x but missing offset_y/z
  - Exact boundary clamping: 2.0 stays 2.0; 2.000001 clamps to 2.0; -2.0 stays -2.0
  - Flat key with invalid zone name: extra_zone_nonexistent_offset_x ignored
  - All-axes simultaneously: offset_x=1.0, offset_y=0.5, offset_z=-1.0
  - Regression guard: extra_zone_body_offset_w still rejected (AC-1.3)
  - Merge: out-of-range value passes merge unclamped (clamp only in sanitize)
  - Mutation guard: zero offset is identity through full round-trip
  - Stress: all zones simultaneously each with distinct offset values
  - Type mutation: None, bool True, list, dict as offset values — must not crash
"""

from __future__ import annotations

import math

import pytest

from src.utils import animated_build_options as abo
from src.utils.animated_build_options import (
    options_for_enemy,
)

# ---------------------------------------------------------------------------
# Cross-zone contamination: body offset must NOT leak into head zone
# ---------------------------------------------------------------------------


def test_body_offset_x_does_not_contaminate_head_offset_via_sanitize() -> None:
    """ADVERSARIAL: sanitizing body offset_x=1.5 must leave head offset_x unchanged at 0.0."""
    # ADVERSARIAL
    got = abo._sanitize_zone_geometry_extras(
        "slug",
        {
            "body": {"offset_x": 1.5},
            "head": {},  # no offset specified — should default to 0.0
        },
    )
    assert got["body"]["offset_x"] == 1.5, "body offset must be 1.5"
    assert got["head"]["offset_x"] == 0.0, "head offset must not be contaminated by body"
    assert got["head"]["offset_y"] == 0.0
    assert got["head"]["offset_z"] == 0.0


def test_body_offset_y_does_not_contaminate_head_zone_via_merge() -> None:
    """ADVERSARIAL: flat body offset_y must not appear in head zone after merge."""
    # ADVERSARIAL
    got = abo._merge_zone_geometry_extras(
        "slug",
        {"extra_zone_body_offset_y": 0.75},
        abo._default_zone_geometry_extras("slug"),
    )
    assert got["body"]["offset_y"] == 0.75, "body offset_y must be set"
    assert got["head"]["offset_y"] == 0.0, "head offset_y must not be contaminated"


def test_all_zones_distinct_offsets_via_sanitize_no_cross_contamination() -> None:
    """ADVERSARIAL/STRESS: every slug zone with a distinct offset value — no cross-contamination."""
    # ADVERSARIAL
    # slug zones: body, head, extra
    inp = {
        "body": {"offset_x": 0.1, "offset_y": 0.2, "offset_z": 0.3},
        "head": {"offset_x": -0.1, "offset_y": -0.2, "offset_z": -0.3},
        "extra": {"offset_x": 1.0, "offset_y": 1.1, "offset_z": 1.2},
    }
    got = abo._sanitize_zone_geometry_extras("slug", inp)
    assert got["body"]["offset_x"] == pytest.approx(0.1)
    assert got["body"]["offset_y"] == pytest.approx(0.2)
    assert got["body"]["offset_z"] == pytest.approx(0.3)
    assert got["head"]["offset_x"] == pytest.approx(-0.1)
    assert got["head"]["offset_y"] == pytest.approx(-0.2)
    assert got["head"]["offset_z"] == pytest.approx(-0.3)
    assert got["extra"]["offset_x"] == pytest.approx(1.0)
    assert got["extra"]["offset_y"] == pytest.approx(1.1)
    assert got["extra"]["offset_z"] == pytest.approx(1.2)


# ---------------------------------------------------------------------------
# Float edge cases: NaN, +Inf, -Inf as sanitize inputs
# ---------------------------------------------------------------------------


def test_sanitize_offset_x_positive_infinity_clamps_to_max() -> None:
    """ADVERSARIAL: offset_x = +Inf should clamp to 2.0 (max), not remain infinite.

    float('inf') is a valid float, passes float() without raising, but
    max(-2.0, min(2.0, inf)) == 2.0.  Verifies the clamp handles float extremes.
    """
    # ADVERSARIAL
    got = abo._sanitize_zone_geometry_extras(
        "slug", {"body": {"offset_x": math.inf}}
    )
    assert got["body"]["offset_x"] == pytest.approx(2.0), (
        f"expected clamped max 2.0, got {got['body']['offset_x']}"
    )


def test_sanitize_offset_x_negative_infinity_clamps_to_min() -> None:
    """ADVERSARIAL: offset_x = -Inf should clamp to -2.0 (min)."""
    # ADVERSARIAL
    got = abo._sanitize_zone_geometry_extras(
        "slug", {"body": {"offset_x": -math.inf}}
    )
    assert got["body"]["offset_x"] == pytest.approx(-2.0), (
        f"expected clamped min -2.0, got {got['body']['offset_x']}"
    )


def test_sanitize_offset_x_nan_produces_finite_result() -> None:  # CHECKPOINT
    """ADVERSARIAL/CHECKPOINT: offset_x = NaN — result must be finite (not NaN).

    Spec says invalid non-numeric values reset to 0.0 (TypeError/ValueError).
    NaN is technically a valid float() value, so it may not trigger the except
    branch.  The clamp max(-2.0, min(2.0, nan)) is implementation-defined in Python.
    Conservative assumption: the implementation must produce a finite, in-range result.
    If the implementation's clamp lets NaN through, this test exposes the gap.
    """
    # CHECKPOINT: conservative — NaN should not survive sanitize as NaN
    got = abo._sanitize_zone_geometry_extras(
        "slug", {"body": {"offset_x": math.nan}}
    )
    result = got["body"]["offset_x"]
    assert math.isfinite(result), (
        f"offset_x after sanitize must be finite, got {result!r} (NaN leaked through)"
    )
    assert -2.0 <= result <= 2.0, (
        f"offset_x must be in [-2.0, 2.0], got {result!r}"
    )


def test_sanitize_offset_string_inf_treated_as_invalid() -> None:
    """ADVERSARIAL: string 'inf' as offset_x — must be coerced or reset.

    float('inf') succeeds, so string 'inf' may produce float infinity
    which then clamps to 2.0.  Verify no exception and result is in [-2.0, 2.0].
    """
    # ADVERSARIAL
    got = abo._sanitize_zone_geometry_extras(
        "slug", {"body": {"offset_x": "inf"}}
    )
    result = got["body"]["offset_x"]
    assert math.isfinite(result) or result == 2.0, (
        f"string 'inf' must not produce invalid float in sanitize, got {result!r}"
    )
    assert -2.0 <= result <= 2.0


# ---------------------------------------------------------------------------
# Partial field presence: zone dict has some offset fields but not all
# ---------------------------------------------------------------------------


def test_sanitize_partial_offset_fields_missing_y_and_z_default_to_zero() -> None:
    """ADVERSARIAL: zone has offset_x but no offset_y or offset_z — missing axes default to 0.0."""
    # ADVERSARIAL
    got = abo._sanitize_zone_geometry_extras(
        "slug",
        {"body": {"offset_x": 1.0}},  # offset_y and offset_z absent
    )
    assert got["body"]["offset_x"] == pytest.approx(1.0)
    assert got["body"]["offset_y"] == pytest.approx(0.0), "missing offset_y must default to 0.0"
    assert got["body"]["offset_z"] == pytest.approx(0.0), "missing offset_z must default to 0.0"


def test_merge_partial_offset_only_x_head_zone_y_z_default() -> None:
    """ADVERSARIAL: merge with only offset_z for head — x and y must stay 0.0."""
    # ADVERSARIAL
    got = abo._merge_zone_geometry_extras(
        "slug",
        {"extra_zone_head_offset_z": -0.5},
        abo._default_zone_geometry_extras("slug"),
    )
    assert got["head"]["offset_z"] == pytest.approx(-0.5)
    assert got["head"]["offset_x"] == pytest.approx(0.0), "missing offset_x must stay 0.0"
    assert got["head"]["offset_y"] == pytest.approx(0.0), "missing offset_y must stay 0.0"


# ---------------------------------------------------------------------------
# Exact boundary clamping: epsilon above/below max/min
# ---------------------------------------------------------------------------


def test_sanitize_offset_x_just_above_max_clamps_to_2() -> None:
    """ADVERSARIAL: 2.000001 must clamp to exactly 2.0 (one epsilon over max)."""
    # ADVERSARIAL
    got = abo._sanitize_zone_geometry_extras(
        "slug", {"body": {"offset_x": 2.000001}}
    )
    assert got["body"]["offset_x"] == pytest.approx(2.0), (
        f"2.000001 should clamp to 2.0, got {got['body']['offset_x']}"
    )


def test_sanitize_offset_x_at_max_boundary_exact() -> None:
    """ADVERSARIAL: exactly 2.0 must not be over-clamped — must remain 2.0."""
    # ADVERSARIAL
    got = abo._sanitize_zone_geometry_extras(
        "slug", {"body": {"offset_x": 2.0}}
    )
    assert got["body"]["offset_x"] == pytest.approx(2.0)


def test_sanitize_offset_x_just_below_min_clamps_to_neg2() -> None:
    """ADVERSARIAL: -2.000001 must clamp to -2.0 (one epsilon under min)."""
    # ADVERSARIAL
    got = abo._sanitize_zone_geometry_extras(
        "slug", {"body": {"offset_x": -2.000001}}
    )
    assert got["body"]["offset_x"] == pytest.approx(-2.0), (
        f"-2.000001 should clamp to -2.0, got {got['body']['offset_x']}"
    )


def test_sanitize_offset_x_at_min_boundary_exact() -> None:
    """ADVERSARIAL: exactly -2.0 must not be over-clamped — must remain -2.0."""
    # ADVERSARIAL
    got = abo._sanitize_zone_geometry_extras(
        "slug", {"body": {"offset_x": -2.0}}
    )
    assert got["body"]["offset_x"] == pytest.approx(-2.0)


# ---------------------------------------------------------------------------
# Flat key with invalid zone name: must not create new zone entry
# ---------------------------------------------------------------------------


def test_flat_key_nonexistent_zone_not_matched_by_regex() -> None:
    """ADVERSARIAL: 'extra_zone_nonexistent_offset_x' — regex must not match."""
    # ADVERSARIAL
    m = abo._EXTRA_ZONE_FLAT_KEY.match("extra_zone_nonexistent_offset_x")
    assert m is None, (
        "regex must not match keys for zones outside the known alternation group"
    )


def test_merge_flat_key_nonexistent_zone_does_not_create_entry() -> None:
    """ADVERSARIAL/CHECKPOINT: flat key with unknown zone must not add that zone to the output.

    Conservative assumption: only zones from _feature_zones(slug) appear in the result.
    """
    # ADVERSARIAL + CHECKPOINT
    got = abo._merge_zone_geometry_extras(
        "slug",
        {"extra_zone_nonexistent_offset_x": 1.0},
        abo._default_zone_geometry_extras("slug"),
    )
    assert "nonexistent" not in got, (
        "merge must not create a new zone entry for an unknown zone name in a flat key"
    )
    # Also verify slug's known zones are intact
    for zone in abo._feature_zones("slug"):
        assert zone in got


def test_merge_flat_key_offset_w_axis_does_not_match() -> None:
    """ADVERSARIAL: 'extra_zone_body_offset_w' — regression guard, must stay rejected (AC-1.3)."""
    # ADVERSARIAL — regression guard to ensure AC-1.3 is not accidentally broken
    m = abo._EXTRA_ZONE_FLAT_KEY.match("extra_zone_body_offset_w")
    assert m is None, (
        "AC-1.3 regression: 'extra_zone_body_offset_w' must still be rejected by regex "
        "even after adding offset_x/y/z support"
    )


# ---------------------------------------------------------------------------
# All-axes simultaneously: offset_x=1.0, offset_y=0.5, offset_z=-1.0
# ---------------------------------------------------------------------------


def test_merge_all_three_axes_simultaneously_flat_keys() -> None:
    """ADVERSARIAL: all three axes set via flat keys in one src dict — all must land correctly."""
    # ADVERSARIAL
    got = abo._merge_zone_geometry_extras(
        "slug",
        {
            "extra_zone_body_offset_x": 1.0,
            "extra_zone_body_offset_y": 0.5,
            "extra_zone_body_offset_z": -1.0,
        },
        abo._default_zone_geometry_extras("slug"),
    )
    assert got["body"]["offset_x"] == pytest.approx(1.0)
    assert got["body"]["offset_y"] == pytest.approx(0.5)
    assert got["body"]["offset_z"] == pytest.approx(-1.0)


def test_options_for_enemy_all_three_axes_flat_keys_round_trip() -> None:
    """ADVERSARIAL: all three offset axes round-trip through options_for_enemy in one call."""
    # ADVERSARIAL
    o = options_for_enemy(
        "imp",
        {
            "extra_zone_body_offset_x": 1.0,
            "extra_zone_body_offset_y": 0.5,
            "extra_zone_body_offset_z": -1.0,
        },
    )
    b = o["zone_geometry_extras"]["body"]
    assert b["offset_x"] == pytest.approx(1.0)
    assert b["offset_y"] == pytest.approx(0.5)
    assert b["offset_z"] == pytest.approx(-1.0)


def test_options_for_enemy_all_three_axes_nested_round_trip() -> None:
    """ADVERSARIAL: all three offset axes via nested JSON round-trip through options_for_enemy."""
    # ADVERSARIAL
    o = options_for_enemy(
        "imp",
        {"zone_geometry_extras": {"body": {"offset_x": 1.0, "offset_y": 0.5, "offset_z": -1.0}}},
    )
    b = o["zone_geometry_extras"]["body"]
    assert b["offset_x"] == pytest.approx(1.0)
    assert b["offset_y"] == pytest.approx(0.5)
    assert b["offset_z"] == pytest.approx(-1.0)


# ---------------------------------------------------------------------------
# Mutation guard: zero offset is identical to no-offset through full round-trip
# ---------------------------------------------------------------------------


def test_options_for_enemy_explicit_zero_offset_matches_absent_offset() -> None:
    """ADVERSARIAL: offset_x=0.0 via flat key must produce same result as not specifying it."""
    # ADVERSARIAL
    with_zero = options_for_enemy("imp", {"extra_zone_body_offset_x": 0.0})
    without = options_for_enemy("imp", {})
    assert with_zero["zone_geometry_extras"]["body"]["offset_x"] == pytest.approx(
        without["zone_geometry_extras"]["body"]["offset_x"]
    )


# ---------------------------------------------------------------------------
# Type mutation: None, bool, list, dict as offset values — no crash
# ---------------------------------------------------------------------------


def test_merge_offset_x_none_value_ignored() -> None:
    """ADVERSARIAL: None as offset_x value must be handled gracefully (no crash, stays at 0.0)."""
    # ADVERSARIAL
    got = abo._merge_zone_geometry_extras(
        "slug",
        {"extra_zone_body_offset_x": None},
        abo._default_zone_geometry_extras("slug"),
    )
    # None triggers TypeError in float(None) — field must stay at default
    assert got["body"]["offset_x"] == pytest.approx(0.0)


def test_sanitize_offset_x_none_resets_to_zero() -> None:
    """ADVERSARIAL: None as offset_x in raw zone dict must reset to 0.0 (not crash)."""
    # ADVERSARIAL
    got = abo._sanitize_zone_geometry_extras(
        "slug", {"body": {"offset_x": None}}
    )
    assert got["body"]["offset_x"] == pytest.approx(0.0)


def test_sanitize_offset_x_bool_true_treated_as_float() -> None:
    """ADVERSARIAL: bool True as offset_x — float(True) == 1.0, result must be 1.0 (in range)."""
    # ADVERSARIAL — bool is a subclass of int in Python; float(True) == 1.0
    got = abo._sanitize_zone_geometry_extras(
        "slug", {"body": {"offset_x": True}}
    )
    # Conservative: bool coerces to float cleanly, result is 1.0 (in range)
    assert got["body"]["offset_x"] == pytest.approx(1.0)


def test_sanitize_offset_x_list_value_resets_to_zero() -> None:
    """ADVERSARIAL: list as offset_x must be handled gracefully, reset to 0.0."""
    # ADVERSARIAL
    got = abo._sanitize_zone_geometry_extras(
        "slug", {"body": {"offset_x": [1.0, 2.0]}}
    )
    assert got["body"]["offset_x"] == pytest.approx(0.0)


def test_sanitize_offset_x_dict_value_resets_to_zero() -> None:
    """ADVERSARIAL: dict as offset_x must be handled gracefully, reset to 0.0."""
    # ADVERSARIAL
    got = abo._sanitize_zone_geometry_extras(
        "slug", {"body": {"offset_x": {"nested": 1.0}}}
    )
    assert got["body"]["offset_x"] == pytest.approx(0.0)


def test_sanitize_offset_x_string_abc_resets_to_zero() -> None:
    """ADVERSARIAL: literal 'abc' as offset_x resets to 0.0 (invalid float)."""
    # ADVERSARIAL
    got = abo._sanitize_zone_geometry_extras(
        "slug", {"body": {"offset_x": "abc"}}
    )
    assert got["body"]["offset_x"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Regression guard: verify rowDisabled behaviour for ALL 5 known kind values
# (this is tested in the frontend suite but also covered here as Python-side
#  regression guard on the constant that drives kind options)
# ---------------------------------------------------------------------------


def test_extra_kinds_order_includes_all_five_known_kinds() -> None:
    """ADVERSARIAL: _EXTRA_KINDS_ORDER must still contain all five known kinds (regression guard).

    If a kind is removed from the constant, rowDisabled tests in the frontend
    might pass vacuously or with wrong assumptions.
    """
    # ADVERSARIAL
    expected = {"none", "shell", "spikes", "horns", "bulbs"}
    actual = set(abo._EXTRA_KINDS_ORDER)
    assert expected == actual, (
        f"_EXTRA_KINDS_ORDER missing or has extra kinds: expected {expected}, got {actual}"
    )


# ---------------------------------------------------------------------------
# Stress: large number of zones with distinct values — no bleed
# ---------------------------------------------------------------------------


def test_imp_all_zones_distinct_offsets_no_cross_contamination() -> None:
    """ADVERSARIAL/STRESS: imp has 5 zones — each with unique offset, no cross-contamination."""
    # ADVERSARIAL
    zones = abo._feature_zones("imp")  # body, head, limbs, joints, extra
    raw = {
        z: {
            "offset_x": float(i) * 0.1,
            "offset_y": float(i) * 0.2,
            "offset_z": float(i) * -0.1,
        }
        for i, z in enumerate(zones)
    }
    got = abo._sanitize_zone_geometry_extras("imp", raw)
    for i, z in enumerate(zones):
        assert got[z]["offset_x"] == pytest.approx(float(i) * 0.1), (
            f"zone {z!r} offset_x contaminated"
        )
        assert got[z]["offset_y"] == pytest.approx(float(i) * 0.2), (
            f"zone {z!r} offset_y contaminated"
        )
        assert got[z]["offset_z"] == pytest.approx(float(i) * -0.1), (
            f"zone {z!r} offset_z contaminated"
        )


# ---------------------------------------------------------------------------
# Merge priority: nested then flat wins — adversarial order mutation
# ---------------------------------------------------------------------------


def test_merge_flat_overrides_nested_for_all_three_axes() -> None:
    """ADVERSARIAL: flat keys must override nested for all three axes simultaneously."""
    # ADVERSARIAL — mutation of priority order from primary test AC-2.3
    got = abo._merge_zone_geometry_extras(
        "slug",
        {
            "zone_geometry_extras": {
                "body": {"offset_x": 0.1, "offset_y": 0.2, "offset_z": 0.3}
            },
            "extra_zone_body_offset_x": 1.0,
            "extra_zone_body_offset_y": 1.5,
            "extra_zone_body_offset_z": -0.5,
        },
        abo._default_zone_geometry_extras("slug"),
    )
    assert got["body"]["offset_x"] == pytest.approx(1.0), "flat must override nested for offset_x"
    assert got["body"]["offset_y"] == pytest.approx(1.5), "flat must override nested for offset_y"
    assert got["body"]["offset_z"] == pytest.approx(-0.5), "flat must override nested for offset_z"


# ---------------------------------------------------------------------------
# Control defs: verify offset defs are ordered x then y then z within zone
# ---------------------------------------------------------------------------


def test_zone_extra_control_defs_offset_xyz_order_within_zone() -> None:
    """ADVERSARIAL: within a zone block, offset_x must precede offset_y, which precedes offset_z."""
    # ADVERSARIAL
    defs = abo._zone_extra_control_defs("slug")
    body_keys = [d["key"] for d in defs if d["key"].startswith("extra_zone_body_")]
    ox_idx = body_keys.index("extra_zone_body_offset_x")
    oy_idx = body_keys.index("extra_zone_body_offset_y")
    oz_idx = body_keys.index("extra_zone_body_offset_z")
    assert ox_idx < oy_idx < oz_idx, (
        f"offset defs must be in x/y/z order; got indices x={ox_idx}, y={oy_idx}, z={oz_idx}"
    )


def test_zone_extra_control_defs_offset_are_last_three_per_zone_body() -> None:
    """ADVERSARIAL: offset_x/y/z must be the LAST THREE entries in the body zone block."""
    # ADVERSARIAL — mutation: implementer might add more defs after offset_z
    defs = abo._zone_extra_control_defs("slug")
    body_keys = [d["key"] for d in defs if d["key"].startswith("extra_zone_body_")]
    assert body_keys[-3] == "extra_zone_body_offset_x", (
        f"expected offset_x at -3, got {body_keys[-3]!r}"
    )
    assert body_keys[-2] == "extra_zone_body_offset_y", (
        f"expected offset_y at -2, got {body_keys[-2]!r}"
    )
    assert body_keys[-1] == "extra_zone_body_offset_z", (
        f"expected offset_z at -1, got {body_keys[-1]!r}"
    )


# ---------------------------------------------------------------------------
# AC-1.3 regression: ensure primary test is not accidentally vacuous
# ---------------------------------------------------------------------------


def test_extra_zone_flat_key_still_matches_existing_suffixes_after_regex_change() -> None:
    """ADVERSARIAL: regression — existing valid suffixes still match after offset regex extension."""
    # ADVERSARIAL — regex change must be purely additive
    existing_suffixes = [
        "kind", "spike_shape", "spike_count", "spike_size",
        "bulb_count", "bulb_size", "clustering", "distribution",
        "uniform_shape", "finish", "hex",
        "place_top", "place_bottom", "place_front", "place_back",
        "place_left", "place_right",
    ]
    for suffix in existing_suffixes:
        key = f"extra_zone_body_{suffix}"
        m = abo._EXTRA_ZONE_FLAT_KEY.match(key)
        assert m is not None, (
            f"REGRESSION: existing key {key!r} no longer matches after regex extension"
        )


# ---------------------------------------------------------------------------
# round-trip: out-of-range offset through full options_for_enemy gets clamped
# ---------------------------------------------------------------------------


def test_options_for_enemy_flat_offset_x_large_negative_clamped() -> None:
    """ADVERSARIAL: large negative offset_x=-10.0 must clamp to -2.0 through full pipeline."""
    # ADVERSARIAL
    o = options_for_enemy("imp", {"extra_zone_body_offset_x": -10.0})
    assert o["zone_geometry_extras"]["body"]["offset_x"] == pytest.approx(-2.0)


def test_options_for_enemy_nested_offset_y_large_positive_clamped() -> None:
    """ADVERSARIAL: large positive nested offset_y=999.0 must clamp to 2.0."""
    # ADVERSARIAL
    o = options_for_enemy(
        "imp",
        {"zone_geometry_extras": {"body": {"offset_y": 999.0}}},
    )
    assert o["zone_geometry_extras"]["body"]["offset_y"] == pytest.approx(2.0)


def test_options_for_enemy_offset_does_not_affect_spike_settings() -> None:
    """ADVERSARIAL: adding offset fields must not alter pre-existing spike_count or kind values."""
    # ADVERSARIAL
    o = options_for_enemy(
        "imp",
        {
            "zone_geometry_extras": {
                "body": {"kind": "spikes", "spike_count": 12}
            },
            "extra_zone_body_offset_x": 0.5,
        },
    )
    b = o["zone_geometry_extras"]["body"]
    assert b["kind"] == "spikes", "kind must not be altered by offset fields"
    assert b["spike_count"] == 12, "spike_count must not be altered by offset fields"
    assert b["offset_x"] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Default payload: offset keys absent from default produce 0.0 (not key error)
# ---------------------------------------------------------------------------


def test_default_zone_geometry_extras_payload_offset_types_are_float() -> None:
    """ADVERSARIAL: default payload offset values must be float 0.0, not int 0 or None."""
    # ADVERSARIAL — type mutation: int 0 vs float 0.0 distinction matters for strict type checks
    payload = abo._default_zone_geometry_extras_payload()
    for axis in ("offset_x", "offset_y", "offset_z"):
        val = payload[axis]
        assert isinstance(val, float), (
            f"default {axis} must be float, got {type(val).__name__}"
        )
        assert val == 0.0
