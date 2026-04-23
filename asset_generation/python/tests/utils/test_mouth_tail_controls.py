"""Mouth extra & tail extra — Python build control declarations, coercion, and serialization.

Spec requirements covered:
  MTE-1: Python Build Control Declarations
  MTE-2: Python Coercion and Validation
  MTE-3: Per-Slug Defaults
  MTE-9: Serialization Contract

These tests will be RED until the implementation adds mouth_control_defs() and
tail_control_defs() helpers to animated_build_options.py and extends static_defs
in animated_build_options_validate.py — that is the intended TEST_BREAK state.
"""

import json

import pytest

from src.utils.build_options import (
    animated_build_controls_for_api,
    defaults_for_slug,
    options_for_enemy,
)

# Every animated slug that must declare the six new controls (MTE-1-AC-1, MTE-3).
_ALL_SLUGS = [
    "spider",
    "slug",
    "claw_crawler",
    "imp",
    "carapace_husk",
    "spitter",
    "player_slime",
]

# Controls-only slugs: no geometry wired, but controls and options must still be present (MTE-7).
_CONTROLS_ONLY_SLUGS = ["imp", "spitter", "carapace_husk", "player_slime"]


# ---------------------------------------------------------------------------
# MTE-1: Control declarations — shape of entries
# ---------------------------------------------------------------------------


class TestMouthEnabledControlDeclaration:
    """MTE-1-AC-2, MTE-1-AC-8: mouth_enabled control is declared for every slug with correct shape."""

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_mouth_enabled_key_present_for_slug(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        keys = {c["key"] for c in ctrl[slug]}
        assert "mouth_enabled" in keys, (
            f"mouth_enabled missing from controls for slug '{slug}'"
        )

    def test_mouth_enabled_control_exact_shape_spider(self) -> None:
        """MTE-1-AC-2: exact dict shape for mouth_enabled."""
        ctrl = animated_build_controls_for_api()
        entry = next(c for c in ctrl["spider"] if c["key"] == "mouth_enabled")
        assert entry["label"] == "Mouth"
        assert entry["type"] == "bool"
        assert entry["default"] is False
        assert type(entry["default"]) is bool

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_mouth_enabled_default_is_python_false_not_int(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        entry = next(c for c in ctrl[slug] if c["key"] == "mouth_enabled")
        assert entry["default"] is False
        assert type(entry["default"]) is bool


class TestMouthShapeControlDeclaration:
    """MTE-1-AC-1, MTE-1-AC-3: mouth_shape control is declared for every slug with correct shape."""

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_mouth_shape_key_present_for_slug(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        keys = {c["key"] for c in ctrl[slug]}
        assert "mouth_shape" in keys, (
            f"mouth_shape missing from controls for slug '{slug}'"
        )

    def test_mouth_shape_control_exact_shape_spider(self) -> None:
        """MTE-1-AC-3: exact dict shape for mouth_shape."""
        ctrl = animated_build_controls_for_api()
        entry = next(c for c in ctrl["spider"] if c["key"] == "mouth_shape")
        assert entry["label"] == "Mouth shape"
        assert entry["type"] == "select_str"
        assert entry["options"] == ["smile", "grimace", "flat", "fang", "beak"]
        assert entry["default"] == "smile"

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_mouth_shape_options_consistent_across_slugs(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        entry = next(c for c in ctrl[slug] if c["key"] == "mouth_shape")
        assert entry["options"] == ["smile", "grimace", "flat", "fang", "beak"]
        assert entry["default"] == "smile"
        assert entry["type"] == "select_str"


class TestTailEnabledControlDeclaration:
    """MTE-1-AC-1, MTE-1-AC-4: tail_enabled control is declared for every slug with correct shape."""

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_tail_enabled_key_present_for_slug(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        keys = {c["key"] for c in ctrl[slug]}
        assert "tail_enabled" in keys, (
            f"tail_enabled missing from controls for slug '{slug}'"
        )

    def test_tail_enabled_control_exact_shape_spider(self) -> None:
        """MTE-1-AC-4: exact dict shape for tail_enabled."""
        ctrl = animated_build_controls_for_api()
        entry = next(c for c in ctrl["spider"] if c["key"] == "tail_enabled")
        assert entry["label"] == "Tail"
        assert entry["type"] == "bool"
        assert entry["default"] is False

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_tail_enabled_default_is_python_false_not_int(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        entry = next(c for c in ctrl[slug] if c["key"] == "tail_enabled")
        assert entry["default"] is False
        assert type(entry["default"]) is bool


class TestTailShapeControlDeclaration:
    """MTE-1-AC-1, MTE-1-AC-5: tail_shape control is declared for every slug with correct shape."""

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_tail_shape_key_present_for_slug(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        keys = {c["key"] for c in ctrl[slug]}
        assert "tail_shape" in keys, (
            f"tail_shape missing from controls for slug '{slug}'"
        )

    def test_tail_shape_control_exact_shape_spider(self) -> None:
        """MTE-1-AC-5: exact dict shape for tail_shape."""
        ctrl = animated_build_controls_for_api()
        entry = next(c for c in ctrl["spider"] if c["key"] == "tail_shape")
        assert entry["label"] == "Tail shape"
        assert entry["type"] == "select_str"
        assert entry["options"] == ["spike", "whip", "club", "segmented", "curled"]
        assert entry["default"] == "spike"

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_tail_shape_options_consistent_across_slugs(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        entry = next(c for c in ctrl[slug] if c["key"] == "tail_shape")
        assert entry["options"] == ["spike", "whip", "club", "segmented", "curled"]
        assert entry["default"] == "spike"
        assert entry["type"] == "select_str"


class TestTailLengthControlDeclaration:
    """MTE-1-AC-1, MTE-1-AC-6: tail_length control is declared for every slug with correct shape."""

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_tail_length_key_present_for_slug(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        keys = {c["key"] for c in ctrl[slug]}
        assert "tail_length" in keys, (
            f"tail_length missing from controls for slug '{slug}'"
        )

    def test_tail_length_control_exact_shape_spider(self) -> None:
        """MTE-1-AC-6: exact dict shape for tail_length."""
        ctrl = animated_build_controls_for_api()
        entry = next(c for c in ctrl["spider"] if c["key"] == "tail_length")
        assert entry["label"] == "Tail length"
        assert entry["type"] == "float"
        assert entry["min"] == 0.5
        assert entry["max"] == 3.0
        assert entry["step"] == 0.05
        assert entry["default"] == 1.0

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_tail_length_values_consistent_across_slugs(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        entry = next(c for c in ctrl[slug] if c["key"] == "tail_length")
        assert entry["min"] == 0.5
        assert entry["max"] == 3.0
        assert entry["step"] == 0.05
        assert entry["default"] == 1.0


class TestControlOrdering:
    """MTE-1-AC-8: mouth_enabled, mouth_shape, tail_enabled, tail_shape appear before any float control,
    after eye/pupil controls; tail_length appears in float block."""

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_mouth_tail_controls_appear_in_order(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        keys = [c["key"] for c in ctrl[slug]]
        idx_mouth_enabled = keys.index("mouth_enabled")
        idx_mouth_shape = keys.index("mouth_shape")
        idx_tail_enabled = keys.index("tail_enabled")
        idx_tail_shape = keys.index("tail_shape")
        assert idx_mouth_enabled < idx_mouth_shape, (
            f"slug '{slug}': mouth_enabled must appear before mouth_shape"
        )
        assert idx_mouth_shape < idx_tail_enabled, (
            f"slug '{slug}': mouth_shape must appear before tail_enabled"
        )
        assert idx_tail_enabled < idx_tail_shape, (
            f"slug '{slug}': tail_enabled must appear before tail_shape"
        )

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_mouth_tail_non_float_controls_appear_before_mesh_floats(
        self, slug: str
    ) -> None:
        ctrl = animated_build_controls_for_api()
        all_defs = ctrl[slug]
        # Find first float control index
        float_indices = [i for i, c in enumerate(all_defs) if c.get("type") == "float"]
        if not float_indices:
            pytest.skip(
                f"slug '{slug}' has no float controls; ordering constraint does not apply"
            )
        first_float_idx = min(float_indices)
        mouth_enabled_idx = next(
            i for i, c in enumerate(all_defs) if c["key"] == "mouth_enabled"
        )
        assert mouth_enabled_idx < first_float_idx, (
            f"slug '{slug}': mouth_enabled must appear before mesh float controls"
        )

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_mouth_tail_controls_appear_after_eye_pupil(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        keys = [c["key"] for c in ctrl[slug]]
        idx_pupil_shape = keys.index("pupil_shape")
        idx_mouth_enabled = keys.index("mouth_enabled")
        assert idx_pupil_shape < idx_mouth_enabled, (
            f"slug '{slug}': pupil_shape must appear before mouth_enabled"
        )


class TestHelperFunctionDeclaration:
    """MTE-1-AC-7, MTE-1-AC-9, MTE-1-AC-10: mouth_control_defs and tail_control_defs helpers exist."""

    def testmouth_control_defs_helper_exists_and_is_callable(self) -> None:
        import src.utils.build_options as abo

        assert hasattr(abo, "mouth_control_defs"), (
            "mouth_control_defs must be defined in animated_build_options"
        )
        fn = abo.mouth_control_defs
        assert callable(fn)

    def testmouth_control_defs_returns_two_entries(self) -> None:
        import src.utils.build_options as abo

        result = abo.mouth_control_defs()
        assert isinstance(result, list)
        assert len(result) == 2
        keys = [d["key"] for d in result]
        assert keys == ["mouth_enabled", "mouth_shape"]

    def testtail_control_defs_helper_exists_and_is_callable(self) -> None:
        import src.utils.build_options as abo

        assert hasattr(abo, "tail_control_defs"), (
            "tail_control_defs must be defined in animated_build_options"
        )
        fn = abo.tail_control_defs
        assert callable(fn)

    def testtail_control_defs_returns_three_entries_in_order(self) -> None:
        """MTE-1-AC-10: tail_enabled, tail_shape, tail_length order."""
        import src.utils.build_options as abo

        result = abo.tail_control_defs()
        assert isinstance(result, list)
        assert len(result) == 3
        keys = [d["key"] for d in result]
        assert keys == ["tail_enabled", "tail_shape", "tail_length"]


# ---------------------------------------------------------------------------
# MTE-2: Coercion and validation
# ---------------------------------------------------------------------------


class TestMouthShapeCoercion:
    """MTE-2-AC-1, MTE-2-AC-2: mouth_shape coercion via options_for_enemy."""

    def test_invalid_mouth_shape_falls_back_to_smile_spider(self) -> None:
        """MTE-2-AC-1."""
        o = options_for_enemy("spider", {"mouth_shape": "INVALID"})
        assert o["mouth_shape"] == "smile"

    def test_invalid_mouth_shape_triangle_falls_back(self) -> None:
        o = options_for_enemy("slug", {"mouth_shape": "triangle"})
        assert o["mouth_shape"] == "smile"

    def test_valid_mouth_shape_fang_accepted_slug(self) -> None:
        """MTE-2-AC-2."""
        o = options_for_enemy("slug", {"mouth_shape": "fang"})
        assert o["mouth_shape"] == "fang"

    @pytest.mark.parametrize(
        "valid_shape", ["smile", "grimace", "flat", "fang", "beak"]
    )
    def test_all_valid_mouth_shapes_accepted(self, valid_shape: str) -> None:
        o = options_for_enemy("spider", {"mouth_shape": valid_shape})
        assert o["mouth_shape"] == valid_shape

    def test_empty_string_mouth_shape_falls_back(self) -> None:
        o = options_for_enemy("spider", {"mouth_shape": ""})
        assert o["mouth_shape"] == "smile"


class TestTailShapeCoercion:
    """MTE-2-AC-3, MTE-2-AC-4: tail_shape invalid value falls back to 'spike'."""

    def test_invalid_tail_shape_falls_back_to_spike(self) -> None:
        """MTE-2-AC-3."""
        o = options_for_enemy("spider", {"tail_shape": "NOTREAL"})
        assert o["tail_shape"] == "spike"

    def test_valid_tail_shape_curled_accepted_spider(self) -> None:
        """MTE-2-AC-4."""
        o = options_for_enemy("spider", {"tail_shape": "curled"})
        assert o["tail_shape"] == "curled"

    @pytest.mark.parametrize(
        "valid_shape", ["spike", "whip", "club", "segmented", "curled"]
    )
    def test_all_valid_tail_shapes_accepted(self, valid_shape: str) -> None:
        o = options_for_enemy("slug", {"tail_shape": valid_shape})
        assert o["tail_shape"] == valid_shape

    def test_empty_string_tail_shape_falls_back(self) -> None:
        o = options_for_enemy("claw_crawler", {"tail_shape": ""})
        assert o["tail_shape"] == "spike"


class TestMouthEnabledCoercion:
    """MTE-2-AC-5..7: mouth_enabled bool coercion."""

    def test_true_bool_input_returns_true(self) -> None:
        """MTE-2-AC-5."""
        o = options_for_enemy("spider", {"mouth_enabled": True})
        assert o["mouth_enabled"] is True
        assert type(o["mouth_enabled"]) is bool

    def test_truthy_string_yes_coerces_to_true(self) -> None:
        """MTE-2-AC-6."""
        o = options_for_enemy("spider", {"mouth_enabled": "yes"})
        assert o["mouth_enabled"] is True

    def test_int_zero_coerces_to_false(self) -> None:
        """MTE-2-AC-7."""
        o = options_for_enemy("spider", {"mouth_enabled": 0})
        assert o["mouth_enabled"] is False
        assert type(o["mouth_enabled"]) is bool

    def test_int_one_coerces_to_true(self) -> None:
        o = options_for_enemy("spider", {"mouth_enabled": 1})
        assert o["mouth_enabled"] is True
        assert type(o["mouth_enabled"]) is bool

    def test_default_claw_crawler_mouth_enabled_false(self) -> None:
        """MTE-2-AC-8."""
        o = options_for_enemy("claw_crawler", {})
        assert o["mouth_enabled"] is False


class TestTailEnabledCoercion:
    """tail_enabled bool coercion similar to mouth_enabled."""

    def test_true_bool_input_returns_true(self) -> None:
        o = options_for_enemy("spider", {"tail_enabled": True})
        assert o["tail_enabled"] is True
        assert type(o["tail_enabled"]) is bool

    def test_truthy_string_yes_coerces_to_true(self) -> None:
        o = options_for_enemy("slug", {"tail_enabled": "true"})
        assert o["tail_enabled"] is True

    def test_int_zero_coerces_to_false(self) -> None:
        o = options_for_enemy("spider", {"tail_enabled": 0})
        assert o["tail_enabled"] is False
        assert type(o["tail_enabled"]) is bool

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_tail_enabled_type_is_bool_for_all_slugs(self, slug: str) -> None:
        o = options_for_enemy(slug, {})
        assert type(o["tail_enabled"]) is bool


class TestTailLengthCoercion:
    """MTE-2-AC-10..14: tail_length clamping to [0.5, 3.0]."""

    def test_tail_length_below_min_clamped_to_05(self) -> None:
        """MTE-2-AC-10."""
        o = options_for_enemy("slug", {"tail_length": 0.0})
        assert o["tail_length"] == 0.5

    def test_tail_length_at_boundary_min_stays_05(self) -> None:
        """MTE-2-AC-13."""
        o = options_for_enemy("slug", {"tail_length": 0.5})
        assert o["tail_length"] == 0.5

    def test_tail_length_valid_unchanged(self) -> None:
        """MTE-2-AC-12."""
        o = options_for_enemy("slug", {"tail_length": 1.5})
        assert o["tail_length"] == 1.5

    def test_tail_length_at_boundary_max_stays_30(self) -> None:
        """MTE-2-AC-14."""
        o = options_for_enemy("slug", {"tail_length": 3.0})
        assert o["tail_length"] == 3.0

    def test_tail_length_above_max_clamped_to_30(self) -> None:
        """MTE-2-AC-11."""
        o = options_for_enemy("slug", {"tail_length": 5.0})
        assert o["tail_length"] == 3.0

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_tail_length_type_is_float(self, slug: str) -> None:
        o = options_for_enemy(slug, {})
        assert type(o["tail_length"]) is float


# ---------------------------------------------------------------------------
# MTE-9: Serialization contract
# ---------------------------------------------------------------------------


class TestSerializationContract:
    """MTE-9: JSON serialize/deserialize with correct types."""

    def test_json_dumps_mouth_enabled_is_boolean_false_not_zero(self) -> None:
        """MTE-9-AC-1, MTE-9-AC-6."""
        blob = json.dumps(options_for_enemy("spider", {}))
        assert '"mouth_enabled": false' in blob or '"mouth_enabled":false' in blob
        assert '"mouth_enabled": 0' not in blob
        assert '"mouth_enabled":0' not in blob
        parsed = json.loads(blob)
        assert parsed["mouth_enabled"] is False

    def test_json_dumps_tail_enabled_is_boolean_false_not_zero(self) -> None:
        """MTE-9-AC-2, MTE-9-AC-7."""
        blob = json.dumps(options_for_enemy("spider", {}))
        assert '"tail_enabled": false' in blob or '"tail_enabled":false' in blob
        parsed = json.loads(blob)
        assert parsed["tail_enabled"] is False

    def test_json_dumps_mouth_shape_smile(self) -> None:
        """MTE-9-AC-3."""
        parsed = json.loads(json.dumps(options_for_enemy("spider", {})))
        assert parsed["mouth_shape"] == "smile"

    def test_json_dumps_tail_shape_spike(self) -> None:
        """MTE-9-AC-4."""
        parsed = json.loads(json.dumps(options_for_enemy("spider", {})))
        assert parsed["tail_shape"] == "spike"

    def test_json_dumps_tail_length_is_float(self) -> None:
        """MTE-9-AC-5, MTE-9-AC-8."""
        o = options_for_enemy("slug", {})
        blob = json.dumps(o)
        assert '"tail_length": 1.0' in blob or '"tail_length":1.0' in blob
        parsed = json.loads(blob)
        assert type(parsed["tail_length"]) is float

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_mouth_enabled_type_bool_not_int_after_dumps(self, slug: str) -> None:
        """MTE-9-AC-6."""
        o = options_for_enemy(slug, {})
        blob = json.dumps(o)
        parsed = json.loads(blob)
        assert type(parsed["mouth_enabled"]) is bool

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_tail_enabled_type_bool_not_int_after_dumps(self, slug: str) -> None:
        """MTE-9-AC-7."""
        o = options_for_enemy(slug, {})
        blob = json.dumps(o)
        parsed = json.loads(blob)
        assert type(parsed["tail_enabled"]) is bool

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_tail_length_type_float_after_dumps(self, slug: str) -> None:
        """MTE-9-AC-8."""
        o = options_for_enemy(slug, {})
        blob = json.dumps(o)
        parsed = json.loads(blob)
        assert type(parsed["tail_length"]) is float

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_round_trip_default_options_unchanged(self, slug: str) -> None:
        """MTE-9-AC-10."""
        o1 = options_for_enemy(slug, {})
        o2 = options_for_enemy(slug, json.loads(json.dumps(o1)))
        assert o2["mouth_enabled"] == o1["mouth_enabled"]
        assert type(o2["mouth_enabled"]) is bool
        assert o2["mouth_shape"] == o1["mouth_shape"]
        assert o2["tail_enabled"] == o1["tail_enabled"]
        assert type(o2["tail_enabled"]) is bool
        assert o2["tail_shape"] == o1["tail_shape"]
        assert o2["tail_length"] == o1["tail_length"]

    def test_nested_slug_envelope_mouth_tail(self) -> None:
        """MTE-9-AC-9."""
        o = options_for_enemy(
            "spider",
            {
                "spider": {
                    "mouth_enabled": True,
                    "mouth_shape": "grimace",
                    "tail_enabled": True,
                    "tail_shape": "curled",
                    "tail_length": 2.0,
                }
            },
        )
        assert o["mouth_enabled"] is True
        assert o["mouth_shape"] == "grimace"
        assert o["tail_enabled"] is True
        assert o["tail_shape"] == "curled"
        assert o["tail_length"] == 2.0


# ---------------------------------------------------------------------------
# MTE-3: Per-slug defaults
# ---------------------------------------------------------------------------


class TestPerSlugDefaults:
    """MTE-3-AC-1..5: defaults_for_slug returns correct defaults for all slugs."""

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_defaults_mouth_enabled_is_python_false(self, slug: str) -> None:
        """MTE-3-AC-1."""
        d = defaults_for_slug(slug)
        assert d["mouth_enabled"] is False
        assert type(d["mouth_enabled"]) is bool

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_defaults_mouth_shape_is_smile(self, slug: str) -> None:
        """MTE-3-AC-2."""
        d = defaults_for_slug(slug)
        assert d["mouth_shape"] == "smile"

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_defaults_tail_enabled_is_python_false(self, slug: str) -> None:
        """MTE-3-AC-3."""
        d = defaults_for_slug(slug)
        assert d["tail_enabled"] is False
        assert type(d["tail_enabled"]) is bool

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_defaults_tail_shape_is_spike(self, slug: str) -> None:
        """MTE-3-AC-4."""
        d = defaults_for_slug(slug)
        assert d["tail_shape"] == "spike"

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_defaults_tail_length_is_10(self, slug: str) -> None:
        """MTE-3-AC-5."""
        d = defaults_for_slug(slug)
        assert d["tail_length"] == 1.0

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_options_for_enemy_defaults_matchdefaults_for_slug(
        self, slug: str
    ) -> None:
        """MTE-3."""
        d = defaults_for_slug(slug)
        o = options_for_enemy(slug, {})
        assert o["mouth_enabled"] == d["mouth_enabled"]
        assert o["mouth_shape"] == d["mouth_shape"]
        assert o["tail_enabled"] == d["tail_enabled"]
        assert o["tail_shape"] == d["tail_shape"]
        assert o["tail_length"] == d["tail_length"]


# ---------------------------------------------------------------------------
# MTE-7: Controls-only slugs
# ---------------------------------------------------------------------------


class TestControlsOnlySlugs:
    """MTE-7: imp, spitter, carapace_husk, player_slime declare controls and store options correctly."""

    @pytest.mark.parametrize("slug", _CONTROLS_ONLY_SLUGS)
    def test_all_six_keys_present_in_api_controls(self, slug: str) -> None:
        """MTE-7-AC-1."""
        ctrl = animated_build_controls_for_api()
        keys = {c["key"] for c in ctrl[slug]}
        assert "mouth_enabled" in keys
        assert "mouth_shape" in keys
        assert "tail_enabled" in keys
        assert "tail_shape" in keys
        assert "tail_length" in keys

    @pytest.mark.parametrize("slug", _CONTROLS_ONLY_SLUGS)
    def test_options_for_enemy_stores_mouth_tail_values(self, slug: str) -> None:
        """MTE-7: options are stored and returned even for controls-only slugs."""
        o = options_for_enemy(
            slug,
            {
                "mouth_enabled": True,
                "mouth_shape": "fang",
                "tail_enabled": True,
                "tail_shape": "whip",
            },
        )
        assert o["mouth_enabled"] is True
        assert o["mouth_shape"] == "fang"
        assert o["tail_enabled"] is True
        assert o["tail_shape"] == "whip"

    @pytest.mark.parametrize("slug", _CONTROLS_ONLY_SLUGS)
    def test_controls_only_slugs_do_not_crash_on_options_call(self, slug: str) -> None:
        o = options_for_enemy(
            slug,
            {
                "mouth_enabled": True,
                "mouth_shape": "beak",
                "tail_enabled": True,
                "tail_shape": "segmented",
                "tail_length": 2.5,
            },
        )
        assert o["mouth_shape"] == "beak"
        assert o["tail_length"] == 2.5

    @pytest.mark.parametrize("slug", _CONTROLS_ONLY_SLUGS)
    def test_controls_only_slugs_round_trip(self, slug: str) -> None:
        """MTE-9-AC-10."""
        o1 = options_for_enemy(
            slug, {"mouth_enabled": True, "mouth_shape": "grimace", "tail_length": 2.0}
        )
        o2 = options_for_enemy(slug, json.loads(json.dumps(o1)))
        assert o2["mouth_enabled"] is True
        assert o2["mouth_shape"] == "grimace"
        assert o2["tail_length"] == 2.0


# ---------------------------------------------------------------------------
# Regression: existing tests not broken
# ---------------------------------------------------------------------------


class TestRegressionExistingControls:
    """MTE-2-AC-15: spot-check that existing control keys still work after the change."""

    def test_spider_eye_count_default_still_works(self) -> None:
        o = options_for_enemy("spider", {})
        assert o["eye_count"] == 2

    def test_claw_crawler_peripheral_eyes_still_coerced(self) -> None:
        o = options_for_enemy("claw_crawler", {"peripheral_eyes": 99})
        assert o["peripheral_eyes"] == 3

    def test_spider_api_controls_still_include_eye_count(self) -> None:
        ctrl = animated_build_controls_for_api()
        keys = {c["key"] for c in ctrl["spider"]}
        assert "eye_count" in keys
        assert "BODY_BASE" in keys
