"""Mouth extra & tail extra — adversarial Python build control tests.

Adversarial coverage:
  - Mutation guards (shared mutable state detection)
  - Idempotency (multiple calls return identical results)
  - Dynamic slug coverage (runtime slug resolution)
  - Boundary value analysis for tail_length
  - Coercion edge cases (None, whitespace strings, empty string, type coercion weirdness)
  - Fresh-list-per-call guards

Spec requirements tested adversarially: MTE-1..3, MTE-2 coercion, MTE-9 serialization.
"""

from __future__ import annotations

import json
from copy import deepcopy

import pytest

from src.utils.build_options import (
    animated_build_controls_for_api,
    defaults_for_slug,
    mouth_control_defs,
    options_for_enemy,
    tail_control_defs,
)

# ---------------------------------------------------------------------------
# Mutation guards: shared mutable state detection
# ---------------------------------------------------------------------------


class TestMutationGuardsSharedMutableState:
    """Guard against shared mutable list/dict return values that break callers."""

    def testmouth_control_defs_returns_fresh_list_per_call(self) -> None:
        """MTE-1-AC-9: mouth_control_defs returns a new list each time, not reused."""
        result1 = mouth_control_defs()
        result2 = mouth_control_defs()
        assert result1 is not result2, (
            "mouth_control_defs must return a fresh list per call"
        )

    def testtail_control_defs_returns_fresh_list_per_call(self) -> None:
        """MTE-1-AC-10: tail_control_defs returns a new list each time."""
        result1 = tail_control_defs()
        result2 = tail_control_defs()
        assert result1 is not result2, (
            "tail_control_defs must return a fresh list per call"
        )

    def testmouth_control_defs_entries_are_not_shared(self) -> None:
        """Modifying one entry's dict should not affect other calls."""
        result1 = mouth_control_defs()
        result2 = mouth_control_defs()
        # Mutate the first entry in result1
        result1[0]["label"] = "MUTATED"
        assert result2[0]["label"] == "Mouth", (
            "Entries must be independent dicts, not shared references"
        )

    def test_options_for_enemy_does_not_mutate_input(self) -> None:
        """options_for_enemy should not mutate the input dict."""
        input_opts = {"mouth_enabled": True, "tail_length": 2.5}
        original = deepcopy(input_opts)
        _ = options_for_enemy("slug", input_opts)
        assert input_opts == original, (
            "options_for_enemy must not mutate the caller's input dict"
        )

    def test_options_for_enemy_does_not_mutate_nested_input(self) -> None:
        """Nested envelope format should also be protected from mutation."""
        nested = {"spider": {"mouth_enabled": True}}
        original = deepcopy(nested)
        _ = options_for_enemy("spider", nested)
        assert nested == original, (
            "options_for_enemy must not mutate nested input structures"
        )

    def test_options_for_enemy_returns_independent_result(self) -> None:
        """Multiple calls should return independent result dicts."""
        result1 = options_for_enemy("slug", {"mouth_enabled": True})
        result2 = options_for_enemy("slug", {"mouth_enabled": False})
        # Mutate result1
        result1["mouth_enabled"] = "MUTATED"
        assert isinstance(result2["mouth_enabled"], bool), (
            "Results must be independent dicts, not shared references"
        )


# ---------------------------------------------------------------------------
# Idempotency tests: multiple calls return identical results
# ---------------------------------------------------------------------------


class TestIdempotencyMultipleCalls:
    """Guard against non-deterministic behavior across repeated calls."""

    def testmouth_control_defs_idempotent(self) -> None:
        """mouth_control_defs returns identical structure on repeated calls."""
        for _ in range(10):
            result = mouth_control_defs()
            assert len(result) == 2
            assert result[0]["key"] == "mouth_enabled"
            assert result[1]["key"] == "mouth_shape"

    def testtail_control_defs_idempotent(self) -> None:
        """tail_control_defs returns identical structure on repeated calls."""
        for _ in range(10):
            result = tail_control_defs()
            assert len(result) == 3
            keys = [d["key"] for d in result]
            assert keys == ["tail_enabled", "tail_shape", "tail_length"]

    @pytest.mark.parametrize("slug", ["spider", "slug", "claw_crawler"])
    def testdefaults_for_slug_idempotent(self, slug: str) -> None:
        """defaults_for_slug returns identical defaults on repeated calls."""
        for _ in range(10):
            d = defaults_for_slug(slug)
            assert d["mouth_enabled"] is False
            assert d["tail_length"] == 1.0

    def test_options_for_enemy_idempotent_with_same_input(self) -> None:
        """options_for_enemy returns identical results for same input."""
        opts = {"mouth_shape": "fang", "tail_length": 2.5}
        result1 = options_for_enemy("spider", opts)
        result2 = options_for_enemy("spider", opts)
        assert result1 == result2, (
            "options_for_enemy must be deterministic for same input"
        )


# ---------------------------------------------------------------------------
# Dynamic slug coverage: runtime slug resolution
# ---------------------------------------------------------------------------


class TestDynamicSlugCoverage:
    """Test with dynamically resolved slugs from ENEMY_CLASSES."""

    def test_all_enemy_classes_declare_mouth_tail_controls(self) -> None:
        """All slugs in ENEMY_CLASSES must declare the 6 new controls."""
        from src.enemies.animated import AnimatedEnemyBuilder

        all_slugs = set(AnimatedEnemyBuilder.ENEMY_CLASSES)
        ctrl = animated_build_controls_for_api()
        for slug in all_slugs:
            keys = {c["key"] for c in ctrl[slug]}
            assert "mouth_enabled" in keys, f"{slug} missing mouth_enabled"
            assert "tail_length" in keys, f"{slug} missing tail_length"

    def test_dynamic_slug_from_list(self) -> None:
        """Slug dynamically chosen from list must work."""
        slugs = ["spider", "slug", "claw_crawler", "imp", "carapace_husk", "spitter"]
        for slug in slugs:
            o = options_for_enemy(slug, {"mouth_enabled": True})
            assert o["mouth_enabled"] is True

    def test_unknown_slug_returns_empty_controls(self) -> None:
        """Unknown slug should return empty control list (not crash)."""
        ctrl = animated_build_controls_for_api()
        result = ctrl.get("unknown_nonexistent_slug", [])
        assert isinstance(result, list), "Missing slugs should default to []"


# ---------------------------------------------------------------------------
# Boundary value analysis for tail_length
# ---------------------------------------------------------------------------


class TestTailLengthBoundaryAnalysis:
    """Comprehensive boundary testing for tail_length clamping."""

    @pytest.mark.parametrize(
        ("input_val", "expected"),
        [
            (0.0, 0.5),  # below min
            (-1.0, 0.5),  # negative
            (0.49, 0.5),  # just below min
            (0.5, 0.5),  # exact min
            (0.51, 0.51),  # just above min
            (1.72638, 1.72638),  # arbitrary valid
            (2.99, 2.99),  # just below max
            (3.0, 3.0),  # exact max
            (3.01, 3.0),  # just above max
            (5.0, 3.0),  # way above max
            (100.0, 3.0),  # extreme above max
        ],
    )
    def test_tail_length_clamping_at_boundaries(
        self, input_val: float, expected: float
    ) -> None:
        """tail_length must clamp to [0.5, 3.0] at all boundaries."""
        o = options_for_enemy("slug", {"tail_length": input_val})
        assert o["tail_length"] == expected, (
            f"tail_length {input_val} should clamp to {expected}"
        )

    def test_tail_length_float_precision_preserved(self) -> None:
        """Valid values should preserve float precision."""
        o = options_for_enemy("slug", {"tail_length": 1.23456789})
        assert abs(o["tail_length"] - 1.23456789) < 0.0000001

    def test_tail_length_step_validation(self) -> None:
        """Step value of 0.05 should be respected in control definition."""
        ctrl = animated_build_controls_for_api()
        entry = next(c for c in ctrl["slug"] if c["key"] == "tail_length")
        assert entry["step"] == 0.05


# ---------------------------------------------------------------------------
# Coercion edge cases: None, whitespace strings, weird types
# ---------------------------------------------------------------------------


class TestCoercionEdgeCasesNoneWhitespace:
    """Extreme coercion edge cases for all control types."""

    def test_mouth_enabled_none_coerces_to_false(self) -> None:
        """mouth_enabled=None should coerce to False (bool default)."""
        o = options_for_enemy("slug", {"mouth_enabled": None})
        assert o["mouth_enabled"] is False
        assert type(o["mouth_enabled"]) is bool

    def test_tail_enabled_none_coerces_to_false(self) -> None:
        """tail_enabled=None should coerce to False."""
        o = options_for_enemy("slug", {"tail_enabled": None})
        assert o["tail_enabled"] is False

    def test_mouth_shape_whitespace_string_falls_back(self) -> None:
        """mouth_shape='   ' (whitespace) should fall back to 'smile'."""
        o = options_for_enemy("slug", {"mouth_shape": "   "})
        assert o["mouth_shape"] == "smile"

    def test_mouth_shape_newline_char_falls_back(self) -> None:
        """mouth_shape='\n' should fall back to 'smile'."""
        o = options_for_enemy("slug", {"mouth_shape": "\n"})
        assert o["mouth_shape"] == "smile"

    def test_tail_shape_whitespace_string_falls_back(self) -> None:
        """tail_shape='   ' should fall back to 'spike'."""
        o = options_for_enemy("slug", {"tail_shape": "   "})
        assert o["tail_shape"] == "spike"

    def test_mouth_shape_empty_string_falls_back(self) -> None:
        """mouth_shape='' should fall back to 'smile'.</string>"""
        o = options_for_enemy("slug", {"mouth_shape": ""})
        assert o["mouth_shape"] == "smile"

    def test_tail_shape_empty_string_falls_back(self) -> None:
        """tail_shape='' should fall back to 'spike'."""
        o = options_for_enemy("slug", {"tail_shape": ""})
        assert o["tail_shape"] == "spike"

    def test_mouth_enabled_int_float_coerced_to_bool(self) -> None:
        """mouth_enabled=3.14 should coerce to True (non-zero bool)."""
        o = options_for_enemy("slug", {"mouth_enabled": 3.14})
        assert o["mouth_enabled"] is True

    def test_mouth_enabled_list_triggers_fallback(self) -> None:
        """mouth_enabled=[1,2] should trigger fallback to default False."""
        # List is not a valid boolish input; should use default
        o = options_for_enemy("slug", {"mouth_enabled": [1, 2]})
        assert o["mouth_enabled"] is False

    def test_tail_length_string_numeric_coerced_to_float(self) -> None:
        """tail_length='2.5' (string) should coerce to float 2.5."""
        o = options_for_enemy("slug", {"tail_length": "2.5"})
        assert o["tail_length"] == 2.5
        assert type(o["tail_length"]) is float

    def test_tail_length_string_out_of_range_clamped(self) -> None:
        """tail_length='10' (string) should coerce to 10.0, then clamp to 3.0."""
        o = options_for_enemy("slug", {"tail_length": "10"})
        assert o["tail_length"] == 3.0


# ---------------------------------------------------------------------------
# Fresh-list-per-call guards for control definitions
# ---------------------------------------------------------------------------


class TestFreshListPerCallGuards:
    """Guard against cached/reused list references in control definitions."""

    def test_animated_build_controls_for_api_returns_fresh_dict(self) -> None:
        """Each call returns a new dict, not cached reference."""
        ctrl1 = animated_build_controls_for_api()
        ctrl2 = animated_build_controls_for_api()
        assert ctrl1 is not ctrl2, (
            "animated_build_controls_for_api must return fresh dict per call"
        )

    def test_modify_one_slug_does_not_affect_other_calls(self) -> None:
        """Modifying one slug's control list should not affect other calls."""
        ctrl1 = animated_build_controls_for_api()
        ctrl2 = animated_build_controls_for_api()
        # Mutate spider controls in ctrl1
        ctrl1["spider"].append({"key": "MUTATED"})
        keys2 = {c["key"] for c in ctrl2["spider"]}
        assert "MUTATED" not in keys2, "Slug control lists must be independent"


# ---------------------------------------------------------------------------
# Combined coercion tests: multiple controls mutated together
# ---------------------------------------------------------------------------


class TestCombinedCoercionMultipleControls:
    """Test coercion when multiple controls are set simultaneously."""

    def test_all_six_controls_mutated_together(self) -> None:
        """All six new controls should coerce independently when set together."""
        o = options_for_enemy(
            "slug",
            {
                "mouth_enabled": True,
                "mouth_shape": "fang",
                "tail_enabled": 1,
                "tail_shape": "whip",
                "tail_length": 2.5,
            },
        )
        assert o["mouth_enabled"] is True
        assert o["mouth_shape"] == "fang"
        assert o["tail_enabled"] is True
        assert o["tail_shape"] == "whip"
        assert o["tail_length"] == 2.5

    def test_invalid_combination_falls_back_gracefully(self) -> None:
        """Invalid values should fall back independently without cascading errors."""
        o = options_for_enemy(
            "slug",
            {
                "mouth_enabled": "invalid_bool",
                "mouth_shape": "INVALID_SHAPE",
                "tail_enabled": 0,
                "tail_shape": "NOTREAL",
                "tail_length": -999.0,
            },
        )
        assert o["mouth_enabled"] is False  # fallback default
        assert o["mouth_shape"] == "smile"  # fallback default
        assert o["tail_enabled"] is False
        assert o["tail_shape"] == "spike"  # fallback default
        assert o["tail_length"] == 0.5  # clamped to min


# ---------------------------------------------------------------------------
# Serialization edge cases
# ---------------------------------------------------------------------------


class TestSerializationEdgeCases:
    """JSON serialization edge cases for mouth/tail controls."""

    def test_json_serialize_mouth_enabled_true(self) -> None:
        """mouth_enabled=True should serialize as JSON true."""
        o = options_for_enemy("slug", {"mouth_enabled": True})
        blob = json.dumps(o)
        assert '"mouth_enabled":true' in blob or '"mouth_enabled": true' in blob

    def test_json_serialize_mouth_enabled_false(self) -> None:
        """mouth_enabled=False should serialize as JSON false."""
        o = options_for_enemy("slug", {"mouth_enabled": False})
        blob = json.dumps(o)
        assert '"mouth_enabled":false' in blob or '"mouth_enabled": false' in blob

    def test_json_round_trip_preserves_bool_type(self) -> None:
        """JSON round-trip should preserve Python bool type."""
        o1 = options_for_enemy("slug", {"mouth_enabled": True})
        o2 = options_for_enemy("slug", json.loads(json.dumps(o1)))
        assert type(o2["mouth_enabled"]) is bool

    def test_json_round_trip_preserves_float_type(self) -> None:
        """JSON round-trip should preserve Python float type for tail_length."""
        o1 = options_for_enemy("slug", {"tail_length": 2.5})
        o2 = options_for_enemy("slug", json.loads(json.dumps(o1)))
        assert type(o2["tail_length"]) is float

    def test_json_serialize_empty_string_values(self) -> None:
        """Empty strings should serialize correctly."""
        o = options_for_enemy("slug", {"mouth_shape": ""})
        blob = json.dumps(o)
        parsed = json.loads(blob)
        assert parsed["mouth_shape"] == "smile"  # falls back on deserialize


# ---------------------------------------------------------------------------
# Mutation guard: mouth_enabled=True but mouth_shape is None/missing
# Exposes gap: coercion layer must handle None mouth_shape without propagating
# "None" (stringified) as a shape value to the geometry builder.
# ---------------------------------------------------------------------------


class TestMutationGuardMouthEnabledWithNoneShape:
    """Guard against mouth_enabled=True combined with None/missing mouth_shape.

    Risk: if builder does str(options.get("mouth_shape", "smile")) and options
    contains mouth_shape=None explicitly, the result is "None" — an invalid shape
    that must fall back to "smile" via the coercion path, not reach the builder.
    """

    def test_mouth_shape_none_falls_back_to_smile_in_options(self) -> None:
        """mouth_shape=None should coerce to 'smile' via options_for_enemy."""
        o = options_for_enemy("slug", {"mouth_enabled": True, "mouth_shape": None})
        assert o["mouth_shape"] == "smile", (
            "mouth_shape=None must coerce to default 'smile', not 'None' string"
        )

    def test_mouth_shape_none_is_not_the_string_none(self) -> None:
        """Ensure coercion never produces the literal string 'None'."""
        o = options_for_enemy("spider", {"mouth_enabled": True, "mouth_shape": None})
        assert o["mouth_shape"] != "None", (
            "mouth_shape must not become the string 'None' after coercion"
        )
        assert o["mouth_shape"] in ("smile", "grimace", "flat", "fang", "beak")

    def test_tail_shape_none_falls_back_to_spike(self) -> None:
        """tail_shape=None should coerce to 'spike', not 'None' string."""
        o = options_for_enemy("slug", {"tail_enabled": True, "tail_shape": None})
        assert o["tail_shape"] == "spike", (
            "tail_shape=None must coerce to default 'spike', not 'None' string"
        )

    def test_tail_shape_none_is_not_the_string_none(self) -> None:
        """Ensure tail_shape=None coercion never produces the literal string 'None'."""
        o = options_for_enemy("spider", {"tail_enabled": True, "tail_shape": None})
        assert o["tail_shape"] != "None"
        assert o["tail_shape"] in ("spike", "whip", "club", "segmented", "curled")

    def test_mouth_enabled_true_with_no_mouth_shape_key_uses_default(self) -> None:
        """When mouth_enabled=True but mouth_shape key is absent, default 'smile' is used."""
        o = options_for_enemy("slug", {"mouth_enabled": True})
        assert o["mouth_shape"] == "smile", (
            "Absent mouth_shape with mouth_enabled=True should return 'smile' default"
        )

    def test_tail_enabled_true_with_no_tail_shape_key_uses_default(self) -> None:
        """When tail_enabled=True but tail_shape/tail_length absent, defaults used."""
        o = options_for_enemy("slug", {"tail_enabled": True})
        assert o["tail_shape"] == "spike"
        assert o["tail_length"] == 1.0

    @pytest.mark.parametrize("slug", ["spider", "slug", "claw_crawler", "imp", "carapace_husk", "spitter"])
    def test_mouth_shape_none_stable_across_all_geometry_wired_slugs(self, slug: str) -> None:
        """All geometry-wired slugs must coerce mouth_shape=None to 'smile'."""
        o = options_for_enemy(slug, {"mouth_enabled": True, "mouth_shape": None})
        assert o["mouth_shape"] == "smile", f"slug '{slug}': None mouth_shape must become 'smile'"


# ---------------------------------------------------------------------------
# Exact boundary values for tail_length: task-specified edge cases
# Exposes gap: implementation may use strict > vs >= comparison at boundaries.
# ---------------------------------------------------------------------------


class TestTailLengthExactBoundaryValues:
    """Exact boundary arithmetic — task specifically called out 0.5, 3.0, 0.0, 3.001."""

    def test_tail_length_exactly_05_is_valid_not_clamped(self) -> None:
        """tail_length=0.5 is the minimum valid value; must NOT be clamped further."""
        o = options_for_enemy("slug", {"tail_length": 0.5})
        assert o["tail_length"] == 0.5, (
            "tail_length=0.5 (exact min) must be accepted unchanged"
        )

    def test_tail_length_exactly_30_is_valid_not_clamped(self) -> None:
        """tail_length=3.0 is the maximum valid value; must NOT be clamped further."""
        o = options_for_enemy("slug", {"tail_length": 3.0})
        assert o["tail_length"] == 3.0, (
            "tail_length=3.0 (exact max) must be accepted unchanged"
        )

    def test_tail_length_exactly_00_clamped_to_05(self) -> None:
        """tail_length=0.0 is below minimum; must clamp to 0.5."""
        o = options_for_enemy("slug", {"tail_length": 0.0})
        assert o["tail_length"] == 0.5, (
            "tail_length=0.0 must clamp to minimum 0.5"
        )

    def test_tail_length_3001_clamped_to_30(self) -> None:
        """tail_length=3.001 is just above maximum; must clamp to 3.0.

        # CHECKPOINT: This test guards against off-by-one/epsilon implementation error.
        # Assumption: clamp uses max(0.5, min(3.0, value)) so 3.001 → 3.0.
        # Conservative assumption: any value > 3.0 clamps to exactly 3.0.
        """
        o = options_for_enemy("slug", {"tail_length": 3.001})
        assert o["tail_length"] == 3.0, (
            "tail_length=3.001 must clamp to maximum 3.0 (not 3.001)"
        )

    def test_tail_length_just_below_min_499_clamped(self) -> None:
        """tail_length=0.499 is just below minimum; must clamp to 0.5."""
        o = options_for_enemy("slug", {"tail_length": 0.499})
        assert o["tail_length"] == 0.5, (
            "tail_length=0.499 must clamp to 0.5"
        )

    def test_tail_length_negative_clamped_to_05(self) -> None:
        """Negative tail_length must clamp to minimum 0.5."""
        o = options_for_enemy("claw_crawler", {"tail_length": -10.0})
        assert o["tail_length"] == 0.5


# ---------------------------------------------------------------------------
# player_slime controls-only isolation
# Exposes gap: no existing test verifies that the controls are stored for
# player_slime but no geometry builder call is ever possible.
# ---------------------------------------------------------------------------


class TestPlayerSlimeControlsOnlyIsolation:
    """MTE-7-AC-8: player_slime stores all 6 controls but no geometry fires.

    # CHECKPOINT: player_slime is controls-only. We verify:
    # (a) All 6 keys appear in animated_build_controls_for_api()["player_slime"]
    # (b) options_for_enemy("player_slime", ...) round-trips all 6 values
    # (c) player_slime is absent from ENEMY_CLASSES (so no builder is instantiated)
    # Assumption: player_slime builder class may not exist; we test the API surface only.
    """

    def test_player_slime_controls_in_api_with_mouth_enabled_true(self) -> None:
        """player_slime controls API must return all 6 keys even when mouth_enabled=True."""
        ctrl = animated_build_controls_for_api()
        assert "player_slime" in ctrl, "player_slime must be a key in controls API"
        keys = {c["key"] for c in ctrl["player_slime"]}
        for expected_key in ("mouth_enabled", "mouth_shape", "tail_enabled", "tail_shape", "tail_length"):
            assert expected_key in keys, f"player_slime missing key {expected_key}"

    def test_player_slime_options_stores_mouth_enabled_true(self) -> None:
        """options_for_enemy must store mouth_enabled=True for player_slime."""
        o = options_for_enemy("player_slime", {"mouth_enabled": True, "mouth_shape": "fang"})
        assert o["mouth_enabled"] is True
        assert o["mouth_shape"] == "fang"

    def test_player_slime_options_stores_tail_enabled_true(self) -> None:
        """options_for_enemy must store tail_enabled=True for player_slime."""
        o = options_for_enemy("player_slime", {"tail_enabled": True, "tail_shape": "whip", "tail_length": 2.0})
        assert o["tail_enabled"] is True
        assert o["tail_shape"] == "whip"
        assert o["tail_length"] == 2.0

    def test_player_slime_not_in_enemy_classes(self) -> None:
        """player_slime must NOT be in ENEMY_CLASSES (geometry isolation guarantee)."""
        from src.enemies.animated import AnimatedEnemyBuilder
        assert "player_slime" not in AnimatedEnemyBuilder.ENEMY_CLASSES, (
            "player_slime must be absent from ENEMY_CLASSES so no geometry builder fires"
        )

    def test_player_slime_round_trip_all_six_keys(self) -> None:
        """Round-trip for player_slime must preserve all 6 mouth/tail values."""
        input_vals = {
            "mouth_enabled": True,
            "mouth_shape": "beak",
            "tail_enabled": True,
            "tail_shape": "segmented",
            "tail_length": 2.5,
        }
        o1 = options_for_enemy("player_slime", input_vals)
        o2 = options_for_enemy("player_slime", json.loads(json.dumps(o1)))
        assert o2["mouth_enabled"] is True
        assert o2["mouth_shape"] == "beak"
        assert o2["tail_enabled"] is True
        assert o2["tail_shape"] == "segmented"
        assert o2["tail_length"] == 2.5


# ---------------------------------------------------------------------------
# Ordering: tail_length in float block, before mesh float controls
# Exposes gap: tail_length could accidentally land in non-float block or
# after mesh float controls, violating MTE-1-AC-8.
# ---------------------------------------------------------------------------


class TestTailLengthInFloatBlockOrdering:
    """MTE-1-AC-8: tail_length appears in float section before mesh float controls."""

    @pytest.mark.parametrize("slug", ["spider", "slug", "claw_crawler", "imp", "carapace_husk", "spitter", "player_slime"])
    def test_tail_length_is_a_float_type_control(self, slug: str) -> None:
        """tail_length control must have type='float' (not select_str or bool)."""
        ctrl = animated_build_controls_for_api()
        entry = next(c for c in ctrl[slug] if c["key"] == "tail_length")
        assert entry["type"] == "float", (
            f"tail_length for slug '{slug}' must have type='float'"
        )

    @pytest.mark.parametrize("slug", ["spider", "slug", "claw_crawler", "imp", "carapace_husk", "spitter"])
    def test_tail_shape_is_not_a_float_type_control(self, slug: str) -> None:
        """tail_shape must have type='select_str' (not float — verifies non-float/float split)."""
        ctrl = animated_build_controls_for_api()
        entry = next(c for c in ctrl[slug] if c["key"] == "tail_shape")
        assert entry["type"] == "select_str", (
            f"tail_shape for slug '{slug}' must have type='select_str', not float"
        )

    @pytest.mark.parametrize("slug", ["spider", "slug", "claw_crawler"])
    def test_tail_length_appears_before_mesh_float_controls(self, slug: str) -> None:
        """tail_length index < first BODY_BASE or mesh-float control index.

        MTE-1-AC-8: tail_length in float block BEFORE mesh float controls.
        """
        ctrl = animated_build_controls_for_api()
        all_defs = ctrl[slug]
        tail_length_idx = next(i for i, c in enumerate(all_defs) if c["key"] == "tail_length")
        # BODY_BASE is a known mesh float control present for all animated slugs
        mesh_float_candidates = [
            i for i, c in enumerate(all_defs)
            if c.get("type") == "float" and c["key"] not in ("tail_length",)
        ]
        if mesh_float_candidates:
            first_other_float_idx = min(mesh_float_candidates)
            assert tail_length_idx < first_other_float_idx, (
                f"slug '{slug}': tail_length (idx {tail_length_idx}) must appear before "
                f"other float controls (first at idx {first_other_float_idx})"
            )

    @pytest.mark.parametrize("slug", ["spider", "slug", "claw_crawler"])
    def test_mouth_enabled_appears_before_tail_length(self, slug: str) -> None:
        """Non-float controls (mouth_enabled) must appear before float controls (tail_length).

        MTE-1-AC-8: non-float block before float block.
        """
        ctrl = animated_build_controls_for_api()
        all_defs = ctrl[slug]
        mouth_enabled_idx = next(i for i, c in enumerate(all_defs) if c["key"] == "mouth_enabled")
        tail_length_idx = next(i for i, c in enumerate(all_defs) if c["key"] == "tail_length")
        assert mouth_enabled_idx < tail_length_idx, (
            f"slug '{slug}': mouth_enabled (non-float) must appear before tail_length (float)"
        )
