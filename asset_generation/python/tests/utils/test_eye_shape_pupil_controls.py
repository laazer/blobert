"""Eye shape & pupil system — Python build control declarations, coercion, and serialization.

Spec requirements covered:
  ESPS-1: Python Build Control Declarations
  ESPS-2: Python Coercion and Validation
  ESPS-5: Serialization Contract
  ESPS-6: Per-Slug Defaults
  ESPS-7: Controls-Only Slugs (imp, spitter, carapace_husk, player_slime)
"""

import json

import pytest

from src.utils.build_options import (
    animated_build_controls_for_api,
    defaults_for_slug,
    options_for_enemy,
)

# Every animated slug that must declare the three new controls (ESPS-1-AC-1, ESPS-6).
_ALL_SLUGS = ["spider", "slug", "claw_crawler", "imp", "carapace_husk", "spitter", "player_slime"]

# Controls-only slugs: no geometry wired, but controls and options must still be present (ESPS-7).
_CONTROLS_ONLY_SLUGS = ["imp", "spitter", "carapace_husk", "player_slime"]

# Geometry-wired slugs (ESPS-3, ESPS-4).
_GEOMETRY_SLUGS = ["spider", "slug", "claw_crawler"]


# ---------------------------------------------------------------------------
# ESPS-1: Control declarations — shape of entries
# ---------------------------------------------------------------------------


class TestEyeShapeControlDeclaration:
    """ESPS-1-AC-1, ESPS-1-AC-2: eye_shape control is declared for every slug with correct shape."""

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_eye_shape_key_present_for_slug(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        keys = {c["key"] for c in ctrl[slug]}
        assert "eye_shape" in keys, f"eye_shape missing from controls for slug '{slug}'"

    def test_eye_shape_control_exact_shape_spider(self) -> None:
        """ESPS-1-AC-2: exact dict shape for eye_shape."""
        ctrl = animated_build_controls_for_api()
        entry = next(c for c in ctrl["spider"] if c["key"] == "eye_shape")
        assert entry["label"] == "Eye shape"
        assert entry["type"] == "select_str"
        assert entry["options"] == ["circle", "oval", "slit", "square"]
        assert entry["default"] == "circle"

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_eye_shape_options_consistent_across_slugs(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        entry = next(c for c in ctrl[slug] if c["key"] == "eye_shape")
        assert entry["options"] == ["circle", "oval", "slit", "square"]
        assert entry["default"] == "circle"
        assert entry["type"] == "select_str"


class TestPupilEnabledControlDeclaration:
    """ESPS-1-AC-1, ESPS-1-AC-3: pupil_enabled control is declared for every slug with correct shape."""

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_pupil_enabled_key_present_for_slug(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        keys = {c["key"] for c in ctrl[slug]}
        assert "pupil_enabled" in keys, f"pupil_enabled missing from controls for slug '{slug}'"

    def test_pupil_enabled_control_exact_shape_spider(self) -> None:
        """ESPS-1-AC-3: exact dict shape for pupil_enabled."""
        ctrl = animated_build_controls_for_api()
        entry = next(c for c in ctrl["spider"] if c["key"] == "pupil_enabled")
        assert entry["label"] == "Pupil"
        assert entry["type"] == "bool"
        assert entry["default"] is False

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_pupil_enabled_default_is_python_false_not_int(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        entry = next(c for c in ctrl[slug] if c["key"] == "pupil_enabled")
        assert entry["default"] is False
        assert type(entry["default"]) is bool  # not int


class TestPupilShapeControlDeclaration:
    """ESPS-1-AC-1, ESPS-1-AC-4: pupil_shape control is declared for every slug with correct shape."""

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_pupil_shape_key_present_for_slug(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        keys = {c["key"] for c in ctrl[slug]}
        assert "pupil_shape" in keys, f"pupil_shape missing from controls for slug '{slug}'"

    def test_pupil_shape_control_exact_shape_spider(self) -> None:
        """ESPS-1-AC-4: exact dict shape for pupil_shape."""
        ctrl = animated_build_controls_for_api()
        entry = next(c for c in ctrl["spider"] if c["key"] == "pupil_shape")
        assert entry["label"] == "Pupil shape"
        assert entry["type"] == "select_str"
        assert entry["options"] == ["dot", "slit", "diamond"]
        assert entry["default"] == "dot"

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_pupil_shape_options_consistent_across_slugs(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        entry = next(c for c in ctrl[slug] if c["key"] == "pupil_shape")
        assert entry["options"] == ["dot", "slit", "diamond"]
        assert entry["default"] == "dot"
        assert entry["type"] == "select_str"


class TestControlOrdering:
    """ESPS-1-AC-6: eye_shape → pupil_enabled → pupil_shape appear together in this order,
    before mesh float controls."""

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_eye_shape_pupil_controls_appear_in_order(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        keys = [c["key"] for c in ctrl[slug]]
        idx_eye_shape = keys.index("eye_shape")
        idx_pupil_enabled = keys.index("pupil_enabled")
        idx_pupil_shape = keys.index("pupil_shape")
        assert idx_eye_shape < idx_pupil_enabled, (
            f"slug '{slug}': eye_shape must appear before pupil_enabled"
        )
        assert idx_pupil_enabled < idx_pupil_shape, (
            f"slug '{slug}': pupil_enabled must appear before pupil_shape"
        )

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_eye_shape_pupil_controls_appear_before_mesh_floats(self, slug: str) -> None:
        ctrl = animated_build_controls_for_api()
        all_defs = ctrl[slug]
        # Find last float control index
        float_indices = [i for i, c in enumerate(all_defs) if c.get("type") == "float"]
        if not float_indices:
            pytest.skip(f"slug '{slug}' has no float controls; ordering constraint does not apply")
        first_float_idx = min(float_indices)
        eye_shape_idx = next(i for i, c in enumerate(all_defs) if c["key"] == "eye_shape")
        assert eye_shape_idx < first_float_idx, (
            f"slug '{slug}': eye_shape must appear before mesh float controls"
        )


class TestHelperFunctionDeclaration:
    """ESPS-1-AC-7: eye_shape_pupil_control_defs helper exists and has correct signature."""

    def test_helper_exists_and_is_callable(self) -> None:
        import src.utils.build_options as abo
        assert hasattr(abo, "eye_shape_pupil_control_defs"), (
            "eye_shape_pupil_control_defs must be defined in animated_build_options"
        )
        fn = abo.eye_shape_pupil_control_defs
        assert callable(fn)

    def test_helper_returns_three_entries(self) -> None:
        import src.utils.build_options as abo
        result = abo.eye_shape_pupil_control_defs()
        assert isinstance(result, list)
        assert len(result) == 3
        keys = [d["key"] for d in result]
        assert keys == ["eye_shape", "pupil_enabled", "pupil_shape"]


# ---------------------------------------------------------------------------
# ESPS-2: Coercion and validation
# ---------------------------------------------------------------------------


class TestEyeShapeCoercion:
    """ESPS-2-AC-1, ESPS-2-AC-2: eye_shape coercion via options_for_enemy."""

    def test_invalid_eye_shape_falls_back_to_circle_spider(self) -> None:
        """ESPS-2-AC-1."""
        o = options_for_enemy("spider", {"eye_shape": "INVALID"})
        assert o["eye_shape"] == "circle"

    def test_invalid_eye_shape_triangle_falls_back(self) -> None:
        o = options_for_enemy("slug", {"eye_shape": "triangle"})
        assert o["eye_shape"] == "circle"

    def test_valid_eye_shape_square_accepted_slug(self) -> None:
        """ESPS-2-AC-2."""
        o = options_for_enemy("slug", {"eye_shape": "square"})
        assert o["eye_shape"] == "square"

    @pytest.mark.parametrize("valid_shape", ["circle", "oval", "slit", "square"])
    def test_all_valid_eye_shapes_accepted(self, valid_shape: str) -> None:
        o = options_for_enemy("spider", {"eye_shape": valid_shape})
        assert o["eye_shape"] == valid_shape

    def test_empty_string_eye_shape_falls_back(self) -> None:
        o = options_for_enemy("spider", {"eye_shape": ""})
        assert o["eye_shape"] == "circle"


class TestPupilEnabledCoercion:
    """ESPS-2-AC-3..6: pupil_enabled bool coercion."""

    def test_true_bool_input_returns_true(self) -> None:
        """ESPS-2-AC-3."""
        o = options_for_enemy("spider", {"pupil_enabled": True})
        assert o["pupil_enabled"] is True
        assert type(o["pupil_enabled"]) is bool

    def test_truthy_string_yes_coerces_to_true(self) -> None:
        """ESPS-2-AC-4."""
        o = options_for_enemy("spider", {"pupil_enabled": "yes"})
        assert o["pupil_enabled"] is True

    def test_int_zero_coerces_to_false(self) -> None:
        """ESPS-2-AC-5."""
        o = options_for_enemy("spider", {"pupil_enabled": 0})
        assert o["pupil_enabled"] is False
        assert type(o["pupil_enabled"]) is bool

    def test_int_one_coerces_to_true(self) -> None:
        o = options_for_enemy("spider", {"pupil_enabled": 1})
        assert o["pupil_enabled"] is True
        assert type(o["pupil_enabled"]) is bool

    def test_default_claw_crawler_pupil_enabled_false(self) -> None:
        """ESPS-2-AC-6."""
        o = options_for_enemy("claw_crawler", {})
        assert o["pupil_enabled"] is False

    def test_false_string_coerces_to_false(self) -> None:
        o = options_for_enemy("spider", {"pupil_enabled": "false"})
        assert o["pupil_enabled"] is False

    def test_truthy_string_true_coerces_to_true(self) -> None:
        o = options_for_enemy("slug", {"pupil_enabled": "true"})
        assert o["pupil_enabled"] is True

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_pupil_enabled_type_is_bool_for_all_slugs(self, slug: str) -> None:
        o = options_for_enemy(slug, {})
        assert type(o["pupil_enabled"]) is bool, (
            f"pupil_enabled for slug '{slug}' must be Python bool, not {type(o['pupil_enabled'])}"
        )


class TestPupilShapeCoercion:
    """ESPS-2-AC-7: pupil_shape invalid value falls back to 'dot'."""

    def test_invalid_pupil_shape_falls_back_to_dot(self) -> None:
        """ESPS-2-AC-7."""
        o = options_for_enemy("claw_crawler", {"pupil_shape": "NOTREAL"})
        assert o["pupil_shape"] == "dot"

    @pytest.mark.parametrize("valid_shape", ["dot", "slit", "diamond"])
    def test_all_valid_pupil_shapes_accepted(self, valid_shape: str) -> None:
        o = options_for_enemy("spider", {"pupil_shape": valid_shape})
        assert o["pupil_shape"] == valid_shape

    def test_empty_string_pupil_shape_falls_back(self) -> None:
        o = options_for_enemy("slug", {"pupil_shape": ""})
        assert o["pupil_shape"] == "dot"


# ---------------------------------------------------------------------------
# ESPS-5: Serialization contract
# ---------------------------------------------------------------------------


class TestSerializationContract:
    """ESPS-5: JSON serialize/deserialize with correct types."""

    def test_json_dumps_contains_eye_shape_circle(self) -> None:
        """ESPS-5-AC-1."""
        blob = json.dumps(options_for_enemy("spider", {}))
        assert '"eye_shape": "circle"' in blob or '"eye_shape":"circle"' in blob
        # More robustly, parse back and check
        parsed = json.loads(blob)
        assert parsed["eye_shape"] == "circle"

    def test_json_dumps_pupil_enabled_is_boolean_false_not_zero(self) -> None:
        """ESPS-5-AC-2: pupil_enabled serializes as JSON false, not integer 0."""
        blob = json.dumps(options_for_enemy("spider", {}))
        # JSON boolean false, not integer 0
        assert "false" in blob
        assert '"pupil_enabled": 0' not in blob
        assert '"pupil_enabled":0' not in blob
        parsed = json.loads(blob)
        assert parsed["pupil_enabled"] is False

    def test_json_dumps_contains_pupil_shape_dot(self) -> None:
        """ESPS-5-AC-3."""
        parsed = json.loads(json.dumps(options_for_enemy("spider", {})))
        assert parsed["pupil_shape"] == "dot"

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_pupil_enabled_type_bool_not_int_after_dumps(self, slug: str) -> None:
        """ESPS-5-AC-4: after JSON round-trip, pupil_enabled is still Python bool."""
        o = options_for_enemy(slug, {})
        blob = json.dumps(o)
        parsed = json.loads(blob)
        assert type(parsed["pupil_enabled"]) is bool, (
            f"slug '{slug}': pupil_enabled must round-trip as bool"
        )

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_round_trip_default_options_unchanged(self, slug: str) -> None:
        """ESPS-5-AC-5: full round-trip invariant for default options."""
        o1 = options_for_enemy(slug, {})
        o2 = options_for_enemy(slug, json.loads(json.dumps(o1)))
        # eye_shape / pupil_enabled / pupil_shape must survive the round-trip
        assert o2["eye_shape"] == o1["eye_shape"]
        assert o2["pupil_enabled"] == o1["pupil_enabled"]
        assert type(o2["pupil_enabled"]) is bool
        assert o2["pupil_shape"] == o1["pupil_shape"]

    def test_nested_slug_envelope_eye_shape_oval(self) -> None:
        """ESPS-5-AC-6: nested slug envelope input format accepted."""
        o = options_for_enemy(
            "spider",
            {"spider": {"eye_shape": "oval", "pupil_enabled": True, "pupil_shape": "slit"}},
        )
        assert o["eye_shape"] == "oval"
        assert o["pupil_enabled"] is True
        assert o["pupil_shape"] == "slit"

    def test_round_trip_non_default_valid_options(self) -> None:
        """ESPS-5-AC-5 with non-default values."""
        o1 = options_for_enemy("slug", {"eye_shape": "square", "pupil_enabled": True, "pupil_shape": "diamond"})
        blob = json.dumps(o1)
        o2 = options_for_enemy("slug", json.loads(blob))
        assert o2["eye_shape"] == "square"
        assert o2["pupil_enabled"] is True
        assert o2["pupil_shape"] == "diamond"


# ---------------------------------------------------------------------------
# ESPS-6: Per-slug defaults
# ---------------------------------------------------------------------------


class TestPerSlugDefaults:
    """ESPS-6-AC-1..3: defaults_for_slug returns correct defaults for all slugs."""

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_defaults_eye_shape_is_circle(self, slug: str) -> None:
        """ESPS-6-AC-1."""
        d = defaults_for_slug(slug)
        assert d["eye_shape"] == "circle", f"slug '{slug}': eye_shape default must be 'circle'"

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_defaults_pupil_enabled_is_python_false(self, slug: str) -> None:
        """ESPS-6-AC-2."""
        d = defaults_for_slug(slug)
        assert d["pupil_enabled"] is False, f"slug '{slug}': pupil_enabled default must be False"
        assert type(d["pupil_enabled"]) is bool

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_defaults_pupil_shape_is_dot(self, slug: str) -> None:
        """ESPS-6-AC-3."""
        d = defaults_for_slug(slug)
        assert d["pupil_shape"] == "dot", f"slug '{slug}': pupil_shape default must be 'dot'"

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_options_for_enemy_defaults_matchdefaults_for_slug(self, slug: str) -> None:
        """options_for_enemy with empty input returns same eye/pupil defaults as defaults_for_slug."""
        d = defaults_for_slug(slug)
        o = options_for_enemy(slug, {})
        assert o["eye_shape"] == d["eye_shape"]
        assert o["pupil_enabled"] == d["pupil_enabled"]
        assert o["pupil_shape"] == d["pupil_shape"]


# ---------------------------------------------------------------------------
# ESPS-7: Controls-only slugs
# ---------------------------------------------------------------------------


class TestControlsOnlySlugs:
    """ESPS-7-AC-2, ESPS-7-AC-3: imp, spitter, carapace_husk, player_slime declare controls
    and store options correctly even though geometry is not wired."""

    @pytest.mark.parametrize("slug", _CONTROLS_ONLY_SLUGS)
    def test_all_three_keys_present_in_api_controls(self, slug: str) -> None:
        """ESPS-7-AC-2."""
        ctrl = animated_build_controls_for_api()
        keys = {c["key"] for c in ctrl[slug]}
        assert "eye_shape" in keys, f"slug '{slug}': eye_shape missing"
        assert "pupil_enabled" in keys, f"slug '{slug}': pupil_enabled missing"
        assert "pupil_shape" in keys, f"slug '{slug}': pupil_shape missing"

    @pytest.mark.parametrize("slug", _CONTROLS_ONLY_SLUGS)
    def test_options_for_enemy_stores_eye_shape_and_pupil_enabled(self, slug: str) -> None:
        """ESPS-7-AC-3: options are stored and returned even for controls-only slugs."""
        o = options_for_enemy(slug, {"eye_shape": "square", "pupil_enabled": True})
        assert o["eye_shape"] == "square"
        assert o["pupil_enabled"] is True

    @pytest.mark.parametrize("slug", _CONTROLS_ONLY_SLUGS)
    def test_controls_only_slugs_do_not_crash_on_options_call(self, slug: str) -> None:
        """Calling options_for_enemy with all three new keys does not raise for controls-only slugs."""
        o = options_for_enemy(
            slug,
            {"eye_shape": "oval", "pupil_enabled": True, "pupil_shape": "slit"},
        )
        assert o["eye_shape"] == "oval"
        assert o["pupil_shape"] == "slit"

    @pytest.mark.parametrize("slug", _CONTROLS_ONLY_SLUGS)
    def test_controls_only_slugs_round_trip(self, slug: str) -> None:
        """Round-trip JSON for controls-only slugs preserves eye/pupil values."""
        o1 = options_for_enemy(slug, {"eye_shape": "slit", "pupil_enabled": False, "pupil_shape": "diamond"})
        o2 = options_for_enemy(slug, json.loads(json.dumps(o1)))
        assert o2["eye_shape"] == "slit"
        assert o2["pupil_enabled"] is False
        assert o2["pupil_shape"] == "diamond"


# ---------------------------------------------------------------------------
# Regression: existing tests not broken
# ---------------------------------------------------------------------------


class TestRegressionExistingControls:
    """ESPS-2-AC-9: spot-check that existing control keys still work after the change."""

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
