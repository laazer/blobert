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

from src.utils import build_options as abo
from src.utils.build_options import (
    animated_build_controls_for_api,
    options_for_enemy,
)
from src.utils.build_options.schema import (
    _RIG_ROT_MAX,
    _RIG_ROT_MIN,
    _RIG_ROT_STEP,
    _rig_rotation_control_defs,
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
    assert isinstance(_RIG_ROT_MIN, float), "_RIG_ROT_MIN must be float"
    assert isinstance(_RIG_ROT_MAX, float), "_RIG_ROT_MAX must be float"
    assert isinstance(_RIG_ROT_STEP, float), "_RIG_ROT_STEP must be float"
    assert _RIG_ROT_MIN == -180.0
    assert _RIG_ROT_MAX == 180.0
    assert _RIG_ROT_STEP == 1.0


def test_rig_rotation_control_defs_returns_six_dicts() -> None:
    """AC-1.2: _rig_rotation_control_defs() returns a list of exactly 6 dicts."""
    defs = _rig_rotation_control_defs()
    assert isinstance(defs, list), "return value must be a list"
    assert len(defs) == 6, f"expected 6 defs, got {len(defs)}"
    for d in defs:
        assert isinstance(d, dict), f"every element must be a dict, got {type(d)}"


def test_rig_rotation_control_defs_exact_keys() -> None:
    """AC-1.3: the 6 keys match the exact strings, in order."""
    defs = _rig_rotation_control_defs()
    actual_keys = [d["key"] for d in defs]
    expected_keys = ROTATION_KEYS
    assert actual_keys == expected_keys, (
        f"keys in wrong order or wrong values.\nExpected: {expected_keys}\nGot: {actual_keys}"
    )
    assert set(actual_keys) == set(expected_keys)


def test_rig_rotation_control_defs_type_and_bounds() -> None:
    """AC-1.4: every def has type=float, min=-180.0, max=180.0, step=1.0, default=0.0."""
    defs = _rig_rotation_control_defs()
    for d in defs:
        key = d["key"]
        assert d.get("type") == "float", f"{key}: expected type='float'"
        assert d.get("min") == -180.0, f"{key}: expected min=-180.0"
        assert d.get("max") == 180.0, f"{key}: expected max=180.0"
        assert d.get("step") == 1.0, f"{key}: expected step=1.0"
        assert d.get("default") == 0.0, f"{key}: expected default=0.0"
        # Constants must match
        assert d["min"] == _RIG_ROT_MIN, f"{key}: min must equal _RIG_ROT_MIN"
        assert d["max"] == _RIG_ROT_MAX, f"{key}: max must equal _RIG_ROT_MAX"
        assert d["step"] == _RIG_ROT_STEP, f"{key}: step must equal _RIG_ROT_STEP"


def test_rig_rotation_control_defs_key_and_label_are_non_empty_strings() -> None:
    """AC-1.4/AC-1.6: 'key' and 'label' are present and non-empty strings."""
    defs = _rig_rotation_control_defs()
    for d in defs:
        assert isinstance(d.get("key"), str) and d["key"], f"key must be a non-empty string: {d}"
        assert isinstance(d.get("label"), str) and d["label"], (
            f"label must be a non-empty string for key {d.get('key')}"
        )


def test_rig_rotation_control_defs_label_contains_axis_and_part() -> None:
    """AC-1.6: each label contains the axis letter (X/Y/Z) and part name (head/body)."""
    defs = _rig_rotation_control_defs()
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
    result = _rig_rotation_control_defs()
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


# ===========================================================================
# ADVERSARIAL HARDENING — Test Breaker Agent additions
# ===========================================================================

# ---------------------------------------------------------------------------
# [TB-1] Ordering guarantee: rotation defs appear after static_float and
#         before _mesh_float_control_defs in animated_build_controls_for_api()
#         (PRC-2 AC-2.3 / AC-2.4) — asserted by index position, not just presence
# ---------------------------------------------------------------------------

# Keys that always come from _mesh_float_control_defs (examples observed in imp).
# We do not hard-code the full list; instead we detect mesh-float keys as any
# key that does NOT appear in the non-mesh known-set.  The safer approach:
# We assert that the FIRST rotation key appears BEFORE the first mesh-float key
# and AFTER the last static_float key.  We identify static_float vs mesh-float
# by position relative to the rotation block.
#
# CHECKPOINT: The spec states the ordering must be:
#   static_float → rotation_defs → _mesh_float_control_defs
# We use the known RIG_HEAD_ROT_X (first rotation def) and the heuristic that
# mesh float keys are those that appear AFTER all 6 rotation keys have been seen.
# This is Medium confidence; if the implementer inserts rotation defs elsewhere
# this test will catch it.  # CHECKPOINT


def _extract_key_list(slug: str) -> list[str]:
    """Return the ordered list of 'key' values from animated_build_controls_for_api() for slug."""
    ctrl = animated_build_controls_for_api()
    return [c["key"] for c in ctrl[slug]]


def test_rotation_defs_appear_after_tail_length_and_before_mesh_float_for_imp() -> None:
    """PRC-2 AC-2.3/AC-2.4: rotation defs are inserted after static_float and before mesh floats.

    Strategy: tail_length is the last non-mesh float before static_float in the current
    build (it is explicitly placed before static_float per the merged list comment).
    _mesh_float_control_defs returns keys whose names include BODY_ prefixed mesh keys
    (e.g. BODY_RADIUS, HEAD_RADIUS).  We assert index(RIG_HEAD_ROT_X) > index(tail_length)
    and index(RIG_HEAD_ROT_X) < index of any key starting with BODY_ that is NOT a ROT key.
    """  # CHECKPOINT — assumes tail_length is before static_float per the existing merged list
    keys = _extract_key_list("imp")

    assert "RIG_HEAD_ROT_X" in keys, "RIG_HEAD_ROT_X must be present in imp API controls"
    rot_x_idx = keys.index("RIG_HEAD_ROT_X")

    # tail_length is the last pre-rotation float (placed explicitly before static_float).
    assert "tail_length" in keys, "tail_length must be present (pre-existing control)"
    tail_length_idx = keys.index("tail_length")
    assert rot_x_idx > tail_length_idx, (
        f"RIG_HEAD_ROT_X (idx={rot_x_idx}) must appear AFTER tail_length (idx={tail_length_idx})"
    )

    # The first mesh float key is one that starts with BODY_ or HEAD_ but is NOT a ROT key.
    mesh_float_candidates = [
        k for k in keys
        if (k.startswith("BODY_") or k.startswith("HEAD_")) and "ROT" not in k
    ]
    assert mesh_float_candidates, (
        "Expected at least one BODY_*/HEAD_* (non-ROT) mesh float key for imp"
    )
    first_mesh_float_idx = keys.index(mesh_float_candidates[0])
    assert rot_x_idx < first_mesh_float_idx, (
        f"RIG_HEAD_ROT_X (idx={rot_x_idx}) must appear BEFORE first mesh float key "
        f"{mesh_float_candidates[0]!r} (idx={first_mesh_float_idx})"
    )


def test_all_six_rotation_defs_appear_consecutively_in_api_output() -> None:
    """PRC-2: all 6 rotation keys are contiguous (no interleaving with mesh or other keys)."""
    keys = _extract_key_list("imp")
    rot_indices = [keys.index(k) for k in ROTATION_KEYS if k in keys]
    assert len(rot_indices) == 6, "All 6 rotation keys must be present"
    # Indices must be strictly consecutive (no gaps)
    for i in range(1, len(rot_indices)):
        assert rot_indices[i] == rot_indices[i - 1] + 1, (
            f"Rotation keys must be consecutive; gap between index {rot_indices[i-1]} "
            f"and {rot_indices[i]} (keys: {keys[rot_indices[i-1]]!r}, {keys[rot_indices[i]]!r})"
        )


@pytest.mark.parametrize("slug", ANIMATED_SLUGS)
def test_rotation_defs_ordering_for_all_animated_slugs(slug: str) -> None:
    """PRC-2 AC-2.3: for every animated slug, RIG_HEAD_ROT_X appears before any mesh-float key."""
    keys = _extract_key_list(slug)
    assert "RIG_HEAD_ROT_X" in keys, f"{slug!r}: RIG_HEAD_ROT_X must be present"
    rot_x_idx = keys.index("RIG_HEAD_ROT_X")
    mesh_float_candidates = [
        k for k in keys
        if (k.startswith("BODY_") or k.startswith("HEAD_")) and "ROT" not in k
    ]
    if mesh_float_candidates:
        first_mesh_float_idx = keys.index(mesh_float_candidates[0])
        assert rot_x_idx < first_mesh_float_idx, (
            f"slug {slug!r}: RIG_HEAD_ROT_X (idx={rot_x_idx}) must appear BEFORE "
            f"first mesh float {mesh_float_candidates[0]!r} (idx={first_mesh_float_idx})"
        )


# ---------------------------------------------------------------------------
# [TB-2] player_slime defaults: spec PRC-3 says defaults may be unconditional.
#         The API exclusion is the authoritative gate, but if _defaults_for_slug
#         also adds rotation keys to player_slime it is a latent hazard.
#         We document the conservative expectation: player_slime defaults must
#         NOT contain RIG_*_ROT_* keys (matching the API exclusion intent).
#         Mark CHECKPOINT because PRC-3 Risk explicitly says this is an open question.
# ---------------------------------------------------------------------------


def test_defaults_for_slug_player_slime_does_not_contain_rotation_keys() -> None:
    """PRC-3 (conservative): _defaults_for_slug('player_slime') must not expose rotation keys.

    The spec PRC-3 Risk section acknowledges that _defaults_for_slug() may be
    unconditional and that player_slime would then receive rotation keys in its
    defaults dict.  The spec calls this 'harmless for the defaults function'.
    However, from an API boundary perspective, if player_slime defaults contain
    rotation keys, those keys may leak into API responses or coerce_validate paths.
    Conservative assumption: the 6 animated slugs are the only ones that should
    expose rotation keys anywhere in the pipeline.
    """  # CHECKPOINT — PRC-3 Risk says this is ambiguous; we enforce the stricter variant
    defaults = abo._defaults_for_slug("player_slime")
    for rot_key in ROTATION_KEYS:
        assert rot_key not in defaults, (
            f"player_slime _defaults_for_slug() must not contain {rot_key!r}; "
            "rotation keys are exclusive to the 6 animated enemy slugs"
        )


# ---------------------------------------------------------------------------
# [TB-3] Mutation guard: _rig_rotation_control_defs() must return a fresh list
#         each call — mutating the first result must not affect the second call.
# ---------------------------------------------------------------------------


def test_rig_rotation_control_defs_returns_fresh_list_each_call() -> None:
    """PRC-1 mutation guard: mutating the returned list must not affect subsequent calls."""
    first = _rig_rotation_control_defs()
    first.clear()  # Destructive mutation
    second = _rig_rotation_control_defs()
    assert len(second) == 6, (
        "_rig_rotation_control_defs() must return a fresh list each call; "
        "mutating the first result affected the second (shared mutable reference)"
    )


def test_rig_rotation_control_defs_dict_mutation_does_not_affect_next_call() -> None:
    """PRC-1 mutation guard: mutating a dict inside the returned list must not affect the next call."""
    first = _rig_rotation_control_defs()
    original_key = first[0]["key"]
    first[0]["key"] = "MUTATED_KEY"  # Mutate the first dict's key field
    second = _rig_rotation_control_defs()
    assert second[0]["key"] == original_key, (
        "_rig_rotation_control_defs() returned the same dict object across calls; "
        "dicts must be independent copies, not shared references"
    )


# ---------------------------------------------------------------------------
# [TB-4] None input coercion — PRC-5 says NaN → 0.0; None is a separate case.
#         The existing validate loop uses float(out[key]) which raises TypeError
#         for None.  Conservative assumption: None should revert to default 0.0,
#         same as non-parseable string and NaN.
# ---------------------------------------------------------------------------


def test_options_for_enemy_rotation_none_reverts_to_default() -> None:
    """PRC-5 (extended): None input for a rotation key should coerce to default 0.0.

    PRC-5 explicitly covers NaN, inf, and non-parseable string.  None is not
    mentioned.  The validate loop calls float(out[key]); float(None) raises
    TypeError, which would be an unhandled exception if None is admitted through
    allowed_non_mesh.  Conservative expectation: either None is treated like a
    non-parseable value (default 0.0) or it raises cleanly.  We assert the safe
    outcome (0.0) to surface any unhandled TypeError in the coerce path.
    """  # CHECKPOINT — None coercion is not in the spec; this tests implicit behavior
    result = options_for_enemy("imp", {"RIG_HEAD_ROT_X": None})
    assert result["RIG_HEAD_ROT_X"] == 0.0, (
        "None input for RIG_HEAD_ROT_X must coerce to default 0.0, not raise or produce None"
    )
    assert result["RIG_HEAD_ROT_X"] is not None


# ---------------------------------------------------------------------------
# [TB-5] Zero boundary identity: 0.0 is returned as exactly 0.0 (not -0.0, nan)
# ---------------------------------------------------------------------------


def test_options_for_enemy_rotation_zero_is_positive_zero() -> None:
    """PRC-5 boundary: 0.0 input returns exactly positive 0.0, not -0.0 or NaN."""
    result = options_for_enemy("imp", {"RIG_BODY_ROT_Y": 0.0})
    val = result["RIG_BODY_ROT_Y"]
    assert val == 0.0, f"Expected 0.0, got {val!r}"
    assert not math.isnan(val), "0.0 must not become NaN"
    # Distinguish +0.0 from -0.0 using the sign bit
    import struct
    packed = struct.pack("d", val)
    sign_bit = (packed[-1] & 0x80) >> 7
    assert sign_bit == 0, (
        "0.0 must be positive zero (+0.0), not negative zero (-0.0); "
        f"got value with sign_bit={sign_bit}"
    )


def test_options_for_enemy_rotation_zero_absent_key_is_positive_zero() -> None:
    """PRC-5 boundary: default 0.0 (key absent from input) is positive zero, not -0.0 or NaN."""
    result = options_for_enemy("imp", {})
    val = result["RIG_BODY_ROT_Y"]
    assert val == 0.0
    assert not math.isnan(val)
    import struct
    packed = struct.pack("d", val)
    sign_bit = (packed[-1] & 0x80) >> 7
    assert sign_bit == 0, f"Default 0.0 must be +0.0, not -0.0; sign_bit={sign_bit}"


# ---------------------------------------------------------------------------
# [TB-6] All 6 slugs × all 6 keys clamping — full combinatorial coverage.
#         The existing tests only exercise RIG_BODY_ROT_Z for upper/lower clamp.
#         A broken clamp on RIG_HEAD_ROT_X for a specific slug would go undetected.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("slug", ANIMATED_SLUGS)
@pytest.mark.parametrize("rot_key", ROTATION_KEYS)
def test_options_for_enemy_upper_clamp_all_slugs_all_keys(slug: str, rot_key: str) -> None:
    """PRC-5 AC-5.10: every slug × every rotation key clamps 200.0 → 180.0."""
    result = options_for_enemy(slug, {rot_key: 200.0})
    assert result[rot_key] == 180.0, (
        f"slug={slug!r}, key={rot_key!r}: 200.0 must clamp to 180.0, got {result[rot_key]!r}"
    )


@pytest.mark.parametrize("slug", ANIMATED_SLUGS)
@pytest.mark.parametrize("rot_key", ROTATION_KEYS)
def test_options_for_enemy_lower_clamp_all_slugs_all_keys(slug: str, rot_key: str) -> None:
    """PRC-5 AC-5.10: every slug × every rotation key clamps -200.0 → -180.0."""
    result = options_for_enemy(slug, {rot_key: -200.0})
    assert result[rot_key] == -180.0, (
        f"slug={slug!r}, key={rot_key!r}: -200.0 must clamp to -180.0, got {result[rot_key]!r}"
    )


# ---------------------------------------------------------------------------
# [TB-7] options_for_enemy idempotency: same input → same output, no input mutation
# ---------------------------------------------------------------------------


def test_options_for_enemy_idempotent_output() -> None:
    """PRC-4: calling options_for_enemy twice with identical input returns identical output."""
    raw = {"RIG_HEAD_ROT_X": 45.0, "RIG_BODY_ROT_Z": -90.0}
    result1 = options_for_enemy("imp", raw)
    result2 = options_for_enemy("imp", raw)
    for rot_key in ROTATION_KEYS:
        assert result1[rot_key] == result2[rot_key], (
            f"options_for_enemy is not idempotent for {rot_key!r}: "
            f"first={result1[rot_key]!r}, second={result2[rot_key]!r}"
        )


def test_options_for_enemy_does_not_mutate_input_dict() -> None:
    """PRC-4: options_for_enemy must not mutate the caller's input dict."""
    raw: dict = {"RIG_HEAD_ROT_X": 45.0}
    raw_copy = dict(raw)
    options_for_enemy("imp", raw)
    assert raw == raw_copy, (
        f"options_for_enemy mutated the input dict; before={raw_copy!r}, after={raw!r}"
    )


def test_options_for_enemy_does_not_mutate_input_dict_on_clamp() -> None:
    """PRC-4/PRC-5: clamping must not mutate the caller's input dict (200.0 stays 200.0 in raw)."""
    raw: dict = {"RIG_HEAD_ROT_X": 200.0}
    options_for_enemy("imp", raw)
    assert raw["RIG_HEAD_ROT_X"] == 200.0, (
        "options_for_enemy clamped the value in the input dict (mutated caller's dict); "
        "the input dict must be unchanged, with clamp applied only in the returned copy"
    )


# ---------------------------------------------------------------------------
# [TB-8] Type check: all 6 defs have type exactly "float" (not "int" or other)
# ---------------------------------------------------------------------------


def test_rig_rotation_control_defs_type_is_exactly_float_string_not_int() -> None:
    """PRC-1 AC-1.4: type field is the string 'float', not the string 'int' or Python type float."""
    defs = _rig_rotation_control_defs()
    for d in defs:
        key = d["key"]
        t = d.get("type")
        assert t == "float", f"{key}: type must be exactly string 'float', got {t!r}"
        assert t != "int", f"{key}: type must not be 'int'"
        assert not isinstance(t, type), (
            f"{key}: type field must be the string 'float', not the Python type object {t!r}"
        )


# ---------------------------------------------------------------------------
# [TB-9] Step value type: _RIG_ROT_STEP is float 1.0, not int 1
#         (already tested in test_rig_rot_constants_exist_and_typed, but we add
#          a dedicated assertion to guard against `1` being used instead of `1.0`)
# ---------------------------------------------------------------------------


def test_rig_rot_step_is_float_not_int() -> None:
    """PRC-1 AC-1.1: _RIG_ROT_STEP must be float 1.0, not integer 1."""
    step = _RIG_ROT_STEP
    assert isinstance(step, float), (
        f"_RIG_ROT_STEP must be float, got {type(step).__name__!r} with value {step!r}"
    )
    assert step == 1.0
    # Explicit int check: `isinstance(True, int)` is True in Python, so also guard booleans
    assert not isinstance(step, bool), "_RIG_ROT_STEP must not be a boolean"
    assert not isinstance(step, int), "_RIG_ROT_STEP must not be int (even if value equals 1)"


def test_rig_rotation_control_defs_step_field_is_float_not_int() -> None:
    """PRC-1 AC-1.4: the step field in every def is a float, not int."""
    defs = _rig_rotation_control_defs()
    for d in defs:
        key = d["key"]
        step = d.get("step")
        assert isinstance(step, float), (
            f"{key}: step must be float 1.0, got {type(step).__name__!r} with value {step!r}"
        )
        assert not isinstance(step, bool), f"{key}: step must not be a boolean"


# ---------------------------------------------------------------------------
# [TB-10] Dict type isolation: options_for_enemy for one slug does not affect another
# ---------------------------------------------------------------------------


def test_options_for_enemy_slug_isolation_no_shared_mutable_state() -> None:
    """PRC-4: results for two different slugs are independent (no shared mutable defaults)."""
    result_imp = options_for_enemy("imp", {"RIG_HEAD_ROT_X": 90.0})
    result_slug = options_for_enemy("slug", {})

    # imp result has the supplied value
    assert result_imp["RIG_HEAD_ROT_X"] == 90.0, "imp: RIG_HEAD_ROT_X should be 90.0"
    # slug result has the default (not contaminated by imp call)
    assert result_slug["RIG_HEAD_ROT_X"] == 0.0, (
        "slug: RIG_HEAD_ROT_X should be 0.0 (default); "
        "was contaminated by previous options_for_enemy('imp', ...) call"
    )


def test_options_for_enemy_repeated_calls_same_slug_no_accumulation() -> None:
    """PRC-4: calling options_for_enemy multiple times for the same slug with different values
    does not accumulate state; each call starts from the canonical defaults."""
    first = options_for_enemy("imp", {"RIG_HEAD_ROT_X": 90.0})
    second = options_for_enemy("imp", {})
    assert first["RIG_HEAD_ROT_X"] == 90.0
    assert second["RIG_HEAD_ROT_X"] == 0.0, (
        "Second call with empty raw should return default 0.0; "
        "previous call with 90.0 must not have mutated shared state"
    )
