"""
animated_build_options — per-part rotation controls (head and body X/Y/Z).

Spec: project_board/specs/part_rotation_controls_spec.md  PRC-1 through PRC-10
Ticket: 04_part_rotation_controls (M25-04)

Covers:
  PRC-1  — Module-level constants and _rig_rotation_control_defs() (AC-1.1 to AC-1.6)
  PRC-2  — Insertion into animated_build_controls_for_api() (AC-2.1 to AC-2.2)
  PRC-3  — Wiring into _defaults_for_slug() (AC-3.1 to AC-3.3)
  PRC-4  — Wiring into options_for_enemy() allowed_non_mesh (AC-4.1 to AC-4.5)
  PRC-5  — Validation and coercion (AC-5.1 to AC-5.10)
  PRC-7  — Slug coverage matrix (AC-7.1 to AC-7.3)
  PRC-10 — Non-breaking guarantee (backward compat)

Blender rotation application (PRC-6) is out of scope for this file;
it is verified by code inspection and manual smoke test per spec.

Note: ensure_blender_stubs() is invoked by the root conftest.py; no
explicit call is required here. (Checkpoint M25-04/run-2026-04-19T01-00-00Z)
"""

import math

import pytest

from src.utils import animated_build_options as abo
from src.utils.animated_build_options import (
    animated_build_controls_for_api,
    options_for_enemy,
)

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

ANIMATED_SLUGS = [
    "spider",
    "slug",
    "imp",
    "spitter",
    "claw_crawler",
    "carapace_husk",
]

ROTATION_KEYS = [
    "RIG_HEAD_ROT_X",
    "RIG_HEAD_ROT_Y",
    "RIG_HEAD_ROT_Z",
    "RIG_BODY_ROT_X",
    "RIG_BODY_ROT_Y",
    "RIG_BODY_ROT_Z",
]

# ---------------------------------------------------------------------------
# PRC-1: Module-level constants and _rig_rotation_control_defs()
# ---------------------------------------------------------------------------


def test_rig_rot_constants_exist_and_typed() -> None:
    """AC-1.1: _RIG_ROT_MIN, _RIG_ROT_MAX, _RIG_ROT_STEP exist, are float, correct values."""
    assert hasattr(abo, "_RIG_ROT_MIN"), "_RIG_ROT_MIN must be defined on abo module"
    assert hasattr(abo, "_RIG_ROT_MAX"), "_RIG_ROT_MAX must be defined on abo module"
    assert hasattr(abo, "_RIG_ROT_STEP"), "_RIG_ROT_STEP must be defined on abo module"
    assert isinstance(abo._RIG_ROT_MIN, float), "_RIG_ROT_MIN must be float"
    assert isinstance(abo._RIG_ROT_MAX, float), "_RIG_ROT_MAX must be float"
    assert isinstance(abo._RIG_ROT_STEP, float), "_RIG_ROT_STEP must be float"
    assert abo._RIG_ROT_MIN == -180.0
    assert abo._RIG_ROT_MAX == 180.0
    assert abo._RIG_ROT_STEP == 1.0


def test_rig_rotation_control_defs_returns_six_dicts() -> None:
    """AC-1.2: _rig_rotation_control_defs() returns a list of exactly 6 dicts."""
    defs = abo._rig_rotation_control_defs()
    assert isinstance(defs, list), "return value must be a list"
    assert len(defs) == 6, f"expected 6 defs, got {len(defs)}"
    for d in defs:
        assert isinstance(d, dict), f"every element must be a dict, got {type(d)}"


def test_rig_rotation_control_defs_exact_keys() -> None:
    """AC-1.3: the 6 keys match the exact strings, in order."""
    defs = abo._rig_rotation_control_defs()
    actual_keys = [d["key"] for d in defs]
    expected_keys = ROTATION_KEYS
    assert actual_keys == expected_keys, (
        f"keys in wrong order or wrong values.\nExpected: {expected_keys}\nGot: {actual_keys}"
    )
    assert set(actual_keys) == set(expected_keys)


def test_rig_rotation_control_defs_type_and_bounds() -> None:
    """AC-1.4: every def has type=float, min=-180.0, max=180.0, step=1.0, default=0.0."""
    defs = abo._rig_rotation_control_defs()
    for d in defs:
        key = d["key"]
        assert d.get("type") == "float", f"{key}: expected type='float'"
        assert d.get("min") == -180.0, f"{key}: expected min=-180.0"
        assert d.get("max") == 180.0, f"{key}: expected max=180.0"
        assert d.get("step") == 1.0, f"{key}: expected step=1.0"
        assert d.get("default") == 0.0, f"{key}: expected default=0.0"
        # Constants must match
        assert d["min"] == abo._RIG_ROT_MIN, f"{key}: min must equal _RIG_ROT_MIN"
        assert d["max"] == abo._RIG_ROT_MAX, f"{key}: max must equal _RIG_ROT_MAX"
        assert d["step"] == abo._RIG_ROT_STEP, f"{key}: step must equal _RIG_ROT_STEP"


def test_rig_rotation_control_defs_key_and_label_are_non_empty_strings() -> None:
    """AC-1.4/AC-1.6: 'key' and 'label' are present and non-empty strings."""
    defs = abo._rig_rotation_control_defs()
    for d in defs:
        assert isinstance(d.get("key"), str) and d["key"], f"key must be a non-empty string: {d}"
        assert isinstance(d.get("label"), str) and d["label"], (
            f"label must be a non-empty string for key {d.get('key')}"
        )


def test_rig_rotation_control_defs_label_contains_axis_and_part() -> None:
    """AC-1.6: each label contains the axis letter (X/Y/Z) and part name (head/body)."""
    defs = abo._rig_rotation_control_defs()
    for d in defs:
        label_lower = d["label"].lower()
        key = d["key"]
        # Axis
        if key.endswith("_X"):
            assert "x" in label_lower, f"{key}: label should contain axis 'x': {d['label']!r}"
        elif key.endswith("_Y"):
            assert "y" in label_lower, f"{key}: label should contain axis 'y': {d['label']!r}"
        elif key.endswith("_Z"):
            assert "z" in label_lower, f"{key}: label should contain axis 'z': {d['label']!r}"
        # Part
        if "HEAD" in key:
            assert "head" in label_lower, f"{key}: label should contain 'head': {d['label']!r}"
        elif "BODY" in key:
            assert "body" in label_lower, f"{key}: label should contain 'body': {d['label']!r}"


def test_rig_rotation_control_defs_callable_without_blender() -> None:
    """AC-1.5: function is callable; no Blender import is required (test env has no live Blender)."""
    # The test environment runs without Blender; reaching this line means the import
    # and call succeeded without bpy/mathutils.
    result = abo._rig_rotation_control_defs()
    assert result is not None


# ---------------------------------------------------------------------------
# PRC-2 / PRC-7: animated_build_controls_for_api() — inclusion and exclusion
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("slug", ANIMATED_SLUGS)
def test_animated_build_controls_for_api_includes_rotation_keys_for_all_slugs(
    slug: str,
) -> None:
    """AC-2.1 / AC-7.3: all 6 rotation keys appear in the API controls for each animated slug."""
    ctrl = animated_build_controls_for_api()
    assert slug in ctrl, f"slug {slug!r} missing from animated_build_controls_for_api() output"
    keys = {c["key"] for c in ctrl[slug]}
    for rot_key in ROTATION_KEYS:
        assert rot_key in keys, (
            f"slug {slug!r}: expected rotation key {rot_key!r} in API controls"
        )


def test_animated_build_controls_for_api_excludes_rotation_keys_for_player_slime() -> None:
    """AC-2.2 / AC-7.2: player_slime must not have any RIG_HEAD_ROT_* or RIG_BODY_ROT_* keys."""
    ctrl = animated_build_controls_for_api()
    assert "player_slime" in ctrl, "player_slime must be present in API controls output"
    ps_keys = {c["key"] for c in ctrl["player_slime"]}
    for rot_key in ROTATION_KEYS:
        assert rot_key not in ps_keys, (
            f"player_slime must not expose rotation key {rot_key!r}"
        )


# ---------------------------------------------------------------------------
# PRC-3: _defaults_for_slug()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("slug", ANIMATED_SLUGS)
def test_defaults_for_slug_has_rotation_keys_at_zero(slug: str) -> None:
    """AC-3.1 / AC-3.2: all 6 rotation keys present at top level with value 0.0 (float)."""
    defaults = abo._defaults_for_slug(slug)
    for rot_key in ROTATION_KEYS:
        assert rot_key in defaults, (
            f"slug {slug!r}: expected rotation key {rot_key!r} in _defaults_for_slug()"
        )
        val = defaults[rot_key]
        assert val == 0.0, (
            f"slug {slug!r}: expected {rot_key!r} default == 0.0, got {val!r}"
        )
        assert isinstance(val, float), (
            f"slug {slug!r}: expected {rot_key!r} to be float, got {type(val)}"
        )


def test_defaults_for_slug_existing_keys_not_affected() -> None:
    """AC-3.3: adding rotation keys must not remove or change pre-existing default keys."""
    defaults = abo._defaults_for_slug("imp")
    # Spot-check 3 pre-existing keys
    assert "tail_enabled" in defaults, "tail_enabled must remain in _defaults_for_slug('imp')"
    assert defaults["tail_enabled"] is False, "tail_enabled default must remain False"
    assert "eye_shape" in defaults, "eye_shape must remain in _defaults_for_slug('imp')"
    assert defaults["eye_shape"] == "circle", "eye_shape default must remain 'circle'"
    assert "mouth_enabled" in defaults, "mouth_enabled must remain in _defaults_for_slug('imp')"


# ---------------------------------------------------------------------------
# PRC-4: options_for_enemy() — allowed_non_mesh pass-through
# ---------------------------------------------------------------------------


def test_options_for_enemy_rotation_key_passes_through() -> None:
    """AC-4.1: supplied RIG_HEAD_ROT_X=45.0 is preserved in output."""
    result = options_for_enemy("imp", {"RIG_HEAD_ROT_X": 45.0})
    assert result["RIG_HEAD_ROT_X"] == 45.0


def test_options_for_enemy_rotation_default_when_absent() -> None:
    """AC-4.2: when no rotation key supplied, default 0.0 is returned."""
    result = options_for_enemy("imp", {})
    assert result["RIG_HEAD_ROT_X"] == 0.0


def test_options_for_enemy_all_six_rotation_keys_present() -> None:
    """AC-4.3: options_for_enemy returns all 6 rotation keys at 0.0 when none supplied."""
    result = options_for_enemy("slug", {})
    for rot_key in ROTATION_KEYS:
        assert rot_key in result, f"expected {rot_key!r} in options_for_enemy output"
        assert result[rot_key] == 0.0, f"expected {rot_key!r} == 0.0, got {result[rot_key]!r}"


def test_options_for_enemy_rotation_does_not_affect_other_keys() -> None:
    """AC-4.4: supplying a rotation key does not alter non-rotation keys."""
    result = options_for_enemy("imp", {"RIG_HEAD_ROT_X": 45.0})
    assert result["tail_enabled"] is False, "tail_enabled must remain False"


def test_options_for_enemy_rotation_key_not_resolved_from_nested_mesh() -> None:
    """AC-4.5: rotation keys are flat-only; a nested 'mesh' dict does not supply them."""
    result = options_for_enemy("imp", {"mesh": {"RIG_HEAD_ROT_X": 45.0}})
    # The nested mesh value must not propagate to the top-level rotation key.
    assert result["RIG_HEAD_ROT_X"] == 0.0, (
        "rotation key in 'mesh' sub-dict must not set top-level RIG_HEAD_ROT_X"
    )


# ---------------------------------------------------------------------------
# PRC-5: Validation and coercion — clamp, NaN, inf, string
# ---------------------------------------------------------------------------


def test_options_for_enemy_rotation_upper_clamp() -> None:
    """AC-5.1 / AC-8.6: value 200.0 is clamped to 180.0."""
    result = options_for_enemy("imp", {"RIG_HEAD_ROT_X": 200.0})
    assert result["RIG_HEAD_ROT_X"] == 180.0


def test_options_for_enemy_rotation_lower_clamp() -> None:
    """AC-5.2 / AC-8.6: value -200.0 is clamped to -180.0."""
    result = options_for_enemy("slug", {"RIG_BODY_ROT_Z": -200.0})
    assert result["RIG_BODY_ROT_Z"] == -180.0


def test_options_for_enemy_rotation_boundary_max_passes_through() -> None:
    """AC-5.3 / AC-8.6: exact max value 180.0 passes through unchanged."""
    result = options_for_enemy("imp", {"RIG_HEAD_ROT_Y": 180.0})
    assert result["RIG_HEAD_ROT_Y"] == 180.0


def test_options_for_enemy_rotation_boundary_min_passes_through() -> None:
    """AC-5.4 / AC-8.6: exact min value -180.0 passes through unchanged."""
    result = options_for_enemy("imp", {"RIG_BODY_ROT_X": -180.0})
    assert result["RIG_BODY_ROT_X"] == -180.0


def test_options_for_enemy_rotation_nan_reverts_to_default() -> None:
    """AC-5.5 / AC-8.6: NaN input coerces to 0.0 default."""
    result = options_for_enemy("imp", {"RIG_HEAD_ROT_Z": float("nan")})
    assert result["RIG_HEAD_ROT_Z"] == 0.0
    assert not math.isnan(result["RIG_HEAD_ROT_Z"])


def test_options_for_enemy_rotation_inf_clamped_to_max() -> None:
    """AC-5.6 / AC-8.6: positive inf is clamped to 180.0."""
    result = options_for_enemy("imp", {"RIG_HEAD_ROT_X": float("inf")})
    assert result["RIG_HEAD_ROT_X"] == 180.0


def test_options_for_enemy_rotation_neg_inf_clamped_to_min() -> None:
    """AC-5.7 / AC-8.6: negative inf is clamped to -180.0."""
    result = options_for_enemy("imp", {"RIG_BODY_ROT_Y": float("-inf")})
    assert result["RIG_BODY_ROT_Y"] == -180.0


def test_options_for_enemy_rotation_string_numeric_coerced() -> None:
    """AC-5.8: string '45.0' is coerced to float 45.0."""
    result = options_for_enemy("imp", {"RIG_HEAD_ROT_X": "45.0"})
    assert result["RIG_HEAD_ROT_X"] == 45.0


def test_options_for_enemy_rotation_string_integer_coerced() -> None:
    """PRC-5 (task instruction): string '45' (integer form) is coerced to 45.0."""
    result = options_for_enemy("imp", {"RIG_HEAD_ROT_X": "45"})
    assert result["RIG_HEAD_ROT_X"] == 45.0


def test_options_for_enemy_rotation_non_parseable_string_reverts_to_default() -> None:
    """AC-5.9: non-parseable string input reverts to default 0.0."""
    result = options_for_enemy("imp", {"RIG_HEAD_ROT_X": "not_a_number"})
    assert result["RIG_HEAD_ROT_X"] == 0.0


# ---------------------------------------------------------------------------
# PRC-5 AC-5.10 / AC-8.7: cross-slug clamp coverage (parametrized)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("slug", ANIMATED_SLUGS)
def test_options_for_enemy_rotation_upper_clamp_all_slugs(slug: str) -> None:
    """AC-5.10 / AC-8.7: value 200.0 is clamped to 180.0 for every animated slug."""
    result = options_for_enemy(slug, {"RIG_BODY_ROT_Z": 200.0})
    assert result["RIG_BODY_ROT_Z"] == 180.0, (
        f"slug {slug!r}: RIG_BODY_ROT_Z=200.0 should clamp to 180.0"
    )


@pytest.mark.parametrize("slug", ANIMATED_SLUGS)
def test_options_for_enemy_rotation_lower_clamp_all_slugs(slug: str) -> None:
    """AC-5.10 / AC-8.7: value -200.0 is clamped to -180.0 for every animated slug."""
    result = options_for_enemy(slug, {"RIG_BODY_ROT_Z": -200.0})
    assert result["RIG_BODY_ROT_Z"] == -180.0, (
        f"slug {slug!r}: RIG_BODY_ROT_Z=-200.0 should clamp to -180.0"
    )


# ---------------------------------------------------------------------------
# PRC-10: Non-breaking guarantee — backward compatibility
# ---------------------------------------------------------------------------


def test_options_for_enemy_rotation_does_not_break_existing_keys_on_imp() -> None:
    """AC-8.8 / PRC-10: adding rotation keys does not alter pre-existing key values."""
    result = options_for_enemy("imp", {"RIG_HEAD_ROT_X": 45.0})
    assert result["tail_enabled"] is False, (
        "tail_enabled must remain False when rotation key is supplied"
    )
    assert result["eye_shape"] == "circle", (
        "eye_shape must remain 'circle' when rotation key is supplied"
    )


def test_options_for_enemy_imp_rig_head_scale_still_present() -> None:
    """PRC-10 / task instruction: RIG_HEAD_SCALE remains in imp output after rotation keys added."""
    result = options_for_enemy("imp", {})
    # RIG_HEAD_SCALE (or equivalent pre-existing rig key) must not be displaced.
    # If the key name changed in a prior milestone this test documents the expectation.
    assert "RIG_HEAD_SCALE" in result, (
        "RIG_HEAD_SCALE must remain present in options_for_enemy('imp', {}) after rotation keys added"
    )


def test_options_for_enemy_no_crash_on_empty_raw_all_animated_slugs() -> None:
    """PRC-10: options_for_enemy(slug, {}) must not raise for any animated slug."""
    for slug in ANIMATED_SLUGS:
        result = options_for_enemy(slug, {})
        assert isinstance(result, dict), f"slug {slug!r}: expected dict result"
