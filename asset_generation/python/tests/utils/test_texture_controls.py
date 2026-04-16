"""Procedural texture presets — Python build control declarations, coercion, and serialization.

Spec requirements covered:
  PTP-1: Python Build Control Declarations
  PTP-2: Python Coercion and Validation
  PTP-3: Per-Slug Defaults and Serialization Contract
  PTP-6: Python Test Coverage
"""

import json

import pytest

from src.utils.animated_build_options import (
    _defaults_for_slug,
    animated_build_controls_for_api,
    options_for_enemy,
)

# All 7 animated slugs that must expose all 10 texture controls (PTP-1-AC-3, slug coverage matrix).
_ALL_SLUGS = [
    "spider",
    "slug",
    "claw_crawler",
    "imp",
    "carapace_husk",
    "spitter",
    "player_slime",
]

# The exact 10 texture control keys, in the order they must be declared (PTP-1-AC-2).
_TEXTURE_CONTROL_KEYS = [
    "texture_mode",
    "texture_grad_color_a",
    "texture_grad_color_b",
    "texture_grad_direction",
    "texture_spot_color",
    "texture_spot_bg_color",
    "texture_spot_density",
    "texture_stripe_color",
    "texture_stripe_bg_color",
    "texture_stripe_width",
]

# Declared defaults for all 10 controls (PTP-1-AC-5, PTP-3).
_TEXTURE_DEFAULTS = {
    "texture_mode": "none",
    "texture_grad_color_a": "",
    "texture_grad_color_b": "",
    "texture_grad_direction": "horizontal",
    "texture_spot_color": "",
    "texture_spot_bg_color": "",
    "texture_spot_density": 1.0,
    "texture_stripe_color": "",
    "texture_stripe_bg_color": "",
    "texture_stripe_width": 0.2,
}


# ---------------------------------------------------------------------------
# PTP-1 / PTP-6-AC-1: _texture_control_defs() helper declaration
# ---------------------------------------------------------------------------


class TestTextureControlDefsHelper:
    """PTP-1-AC-1, PTP-1-AC-6, PTP-6-AC-1, PTP-6-AC-3: helper shape and mutation guard."""

    def test_texture_control_defs_helper_exists_and_is_callable(self) -> None:
        """PTP-1-AC-1: _texture_control_defs is callable with no arguments."""
        import src.utils.animated_build_options as abo

        assert hasattr(abo, "_texture_control_defs"), (
            "_texture_control_defs must be defined in animated_build_options"
        )
        fn = abo._texture_control_defs
        assert callable(fn)

    def test_texture_control_defs_returns_exactly_10_entries(self) -> None:
        """PTP-6-AC-1, PTP-1-AC-1: returns exactly 10 dicts."""
        import src.utils.animated_build_options as abo

        result = abo._texture_control_defs()
        assert isinstance(result, list), (
            "_texture_control_defs() must return a list"
        )
        assert len(result) == 10, (
            f"_texture_control_defs() must return exactly 10 entries, got {len(result)}"
        )

    def test_texture_control_defs_all_entries_are_dicts(self) -> None:
        """PTP-1-AC-1: every entry is a dict."""
        import src.utils.animated_build_options as abo

        result = abo._texture_control_defs()
        for i, entry in enumerate(result):
            assert isinstance(entry, dict), (
                f"Entry {i} of _texture_control_defs() must be a dict, got {type(entry)}"
            )

    def test_texture_control_defs_mutation_guard(self) -> None:
        """PTP-1-AC-6, PTP-6-AC-3: two calls return different list objects (mutation guard)."""
        import src.utils.animated_build_options as abo

        list_a = abo._texture_control_defs()
        list_b = abo._texture_control_defs()
        assert list_a is not list_b, (
            "_texture_control_defs() must return a new list on each call"
        )

    def test_texture_control_defs_mutation_does_not_affect_subsequent_call(self) -> None:
        """PTP-1-AC-6: mutating the returned list must not affect the next call."""
        import src.utils.animated_build_options as abo

        list_a = abo._texture_control_defs()
        original_length = len(list_a)
        list_a.append({"key": "injected"})
        list_b = abo._texture_control_defs()
        assert len(list_b) == original_length, (
            "Mutating the list returned by _texture_control_defs() must not affect the next call"
        )

    def test_texture_control_defs_key_order(self) -> None:
        """PTP-1-AC-2: keys appear in exactly the declared order."""
        import src.utils.animated_build_options as abo

        result = abo._texture_control_defs()
        actual_keys = [d["key"] for d in result]
        assert actual_keys == _TEXTURE_CONTROL_KEYS, (
            f"_texture_control_defs() key order mismatch. Expected {_TEXTURE_CONTROL_KEYS}, got {actual_keys}"
        )


# ---------------------------------------------------------------------------
# PTP-1-AC-2: Exact dict shape for each of the 10 entries
# ---------------------------------------------------------------------------


class TestTextureControlDefsExactShape:
    """PTP-1-AC-2: exact dict shape for each of the 10 declared entries."""

    def test_texture_mode_exact_shape(self) -> None:
        import src.utils.animated_build_options as abo

        result = abo._texture_control_defs()
        entry = next(d for d in result if d["key"] == "texture_mode")
        assert entry["label"] == "Texture mode"
        assert entry["type"] == "select_str"
        assert entry["options"] == ["none", "gradient", "spots", "stripes"]
        assert entry["default"] == "none"

    def test_texture_grad_color_a_exact_shape(self) -> None:
        import src.utils.animated_build_options as abo

        result = abo._texture_control_defs()
        entry = next(d for d in result if d["key"] == "texture_grad_color_a")
        assert entry["label"] == "Gradient color A"
        assert entry["type"] == "str"
        assert entry["default"] == ""

    def test_texture_grad_color_b_exact_shape(self) -> None:
        import src.utils.animated_build_options as abo

        result = abo._texture_control_defs()
        entry = next(d for d in result if d["key"] == "texture_grad_color_b")
        assert entry["label"] == "Gradient color B"
        assert entry["type"] == "str"
        assert entry["default"] == ""

    def test_texture_grad_direction_exact_shape(self) -> None:
        import src.utils.animated_build_options as abo

        result = abo._texture_control_defs()
        entry = next(d for d in result if d["key"] == "texture_grad_direction")
        assert entry["label"] == "Gradient direction"
        assert entry["type"] == "select_str"
        assert entry["options"] == ["horizontal", "vertical", "radial"]
        assert entry["default"] == "horizontal"

    def test_texture_spot_color_exact_shape(self) -> None:
        import src.utils.animated_build_options as abo

        result = abo._texture_control_defs()
        entry = next(d for d in result if d["key"] == "texture_spot_color")
        assert entry["label"] == "Spot color"
        assert entry["type"] == "str"
        assert entry["default"] == ""

    def test_texture_spot_bg_color_exact_shape(self) -> None:
        import src.utils.animated_build_options as abo

        result = abo._texture_control_defs()
        entry = next(d for d in result if d["key"] == "texture_spot_bg_color")
        assert entry["label"] == "Spot background color"
        assert entry["type"] == "str"
        assert entry["default"] == ""

    def test_texture_spot_density_exact_shape(self) -> None:
        import src.utils.animated_build_options as abo

        result = abo._texture_control_defs()
        entry = next(d for d in result if d["key"] == "texture_spot_density")
        assert entry["label"] == "Spot density"
        assert entry["type"] == "float"
        assert entry["min"] == 0.1
        assert entry["max"] == 5.0
        assert entry["step"] == 0.05
        assert entry["default"] == 1.0

    def test_texture_stripe_color_exact_shape(self) -> None:
        import src.utils.animated_build_options as abo

        result = abo._texture_control_defs()
        entry = next(d for d in result if d["key"] == "texture_stripe_color")
        assert entry["label"] == "Stripe color"
        assert entry["type"] == "str"
        assert entry["default"] == ""

    def test_texture_stripe_bg_color_exact_shape(self) -> None:
        import src.utils.animated_build_options as abo

        result = abo._texture_control_defs()
        entry = next(d for d in result if d["key"] == "texture_stripe_bg_color")
        assert entry["label"] == "Stripe background color"
        assert entry["type"] == "str"
        assert entry["default"] == ""

    def test_texture_stripe_width_exact_shape(self) -> None:
        import src.utils.animated_build_options as abo

        result = abo._texture_control_defs()
        entry = next(d for d in result if d["key"] == "texture_stripe_width")
        assert entry["label"] == "Stripe width"
        assert entry["type"] == "float"
        assert entry["min"] == 0.05
        assert entry["max"] == 1.0
        assert entry["step"] == 0.01
        assert entry["default"] == 0.2


# ---------------------------------------------------------------------------
# PTP-1-AC-3, PTP-6-AC-2: All 7 slugs expose all 10 texture controls
# ---------------------------------------------------------------------------


class TestAllSlugsExposeTextureControls:
    """PTP-1-AC-3, PTP-6-AC-2: every slug exposes all 10 texture control keys."""

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_all_10_texture_keys_present_for_slug(self, slug: str) -> None:
        """PTP-1-AC-3, PTP-6-AC-2."""
        ctrl = animated_build_controls_for_api()
        assert slug in ctrl, f"slug '{slug}' missing from animated_build_controls_for_api()"
        keys = {c["key"] for c in ctrl[slug]}
        for key in _TEXTURE_CONTROL_KEYS:
            assert key in keys, (
                f"texture key '{key}' missing from controls for slug '{slug}'"
            )

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_texture_mode_key_present_for_slug(self, slug: str) -> None:
        """PTP-1-AC-3: texture_mode specifically present for each slug."""
        ctrl = animated_build_controls_for_api()
        keys = {c["key"] for c in ctrl[slug]}
        assert "texture_mode" in keys, (
            f"texture_mode missing from controls for slug '{slug}'"
        )

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_texture_float_controls_present_for_slug(self, slug: str) -> None:
        """PTP-1-AC-3: float texture controls present for each slug."""
        ctrl = animated_build_controls_for_api()
        keys = {c["key"] for c in ctrl[slug]}
        assert "texture_spot_density" in keys, (
            f"texture_spot_density missing from controls for slug '{slug}'"
        )
        assert "texture_stripe_width" in keys, (
            f"texture_stripe_width missing from controls for slug '{slug}'"
        )

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_no_texture_key_appears_twice_for_slug(self, slug: str) -> None:
        """Uniqueness: each texture key appears exactly once per slug."""
        ctrl = animated_build_controls_for_api()
        keys = [c["key"] for c in ctrl[slug]]
        for key in _TEXTURE_CONTROL_KEYS:
            count = keys.count(key)
            assert count == 1, (
                f"texture key '{key}' appears {count} times for slug '{slug}', expected exactly 1"
            )


# ---------------------------------------------------------------------------
# PTP-1-AC-4, PTP-6-AC-14, PTP-8-AC-4: Ordering — texture before placement_seed
# ---------------------------------------------------------------------------


class TestTextureControlOrdering:
    """PTP-1-AC-4, PTP-6-AC-14, PTP-8-AC-4: texture controls appear before placement_seed."""

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_placement_seed_appears_after_all_texture_controls(self, slug: str) -> None:
        """PTP-1-AC-4, PTP-6-AC-14: placement_seed is after all 10 texture controls."""
        ctrl = animated_build_controls_for_api()
        keys = [c["key"] for c in ctrl[slug]]
        assert "placement_seed" in keys, (
            f"placement_seed missing from controls for slug '{slug}'"
        )
        idx_placement_seed = keys.index("placement_seed")
        for tex_key in _TEXTURE_CONTROL_KEYS:
            assert tex_key in keys, (
                f"texture key '{tex_key}' missing for slug '{slug}'"
            )
            idx_tex = keys.index(tex_key)
            assert idx_tex < idx_placement_seed, (
                f"slug '{slug}': '{tex_key}' (index {idx_tex}) must appear before "
                f"placement_seed (index {idx_placement_seed})"
            )

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_placement_seed_is_last_entry(self, slug: str) -> None:
        """PTP-8-AC-4: placement_seed remains the last entry in the control list."""
        ctrl = animated_build_controls_for_api()
        last_key = ctrl[slug][-1]["key"]
        assert last_key == "placement_seed", (
            f"slug '{slug}': last entry must be 'placement_seed', got '{last_key}'"
        )

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_texture_mode_appears_before_texture_grad_color_a(self, slug: str) -> None:
        """PTP-1-AC-2 ordering: texture_mode before texture_grad_color_a."""
        ctrl = animated_build_controls_for_api()
        keys = [c["key"] for c in ctrl[slug]]
        idx_mode = keys.index("texture_mode")
        idx_color_a = keys.index("texture_grad_color_a")
        assert idx_mode < idx_color_a, (
            f"slug '{slug}': texture_mode must appear before texture_grad_color_a"
        )

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_texture_stripe_width_appears_before_placement_seed(self, slug: str) -> None:
        """PTP-1-AC-4: last texture control (texture_stripe_width) before placement_seed."""
        ctrl = animated_build_controls_for_api()
        keys = [c["key"] for c in ctrl[slug]]
        idx_stripe_width = keys.index("texture_stripe_width")
        idx_placement_seed = keys.index("placement_seed")
        assert idx_stripe_width < idx_placement_seed, (
            f"slug '{slug}': texture_stripe_width must appear before placement_seed"
        )


# ---------------------------------------------------------------------------
# PTP-1-AC-5, PTP-6-AC-12: _defaults_for_slug contains all 10 texture keys
# ---------------------------------------------------------------------------


class TestPerSlugDefaults:
    """PTP-1-AC-5, PTP-3-AC-6, PTP-6-AC-12: _defaults_for_slug returns correct texture defaults."""

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_defaults_for_slug_includes_all_10_texture_keys(self, slug: str) -> None:
        """PTP-6-AC-12: all 10 texture keys present in _defaults_for_slug."""
        d = _defaults_for_slug(slug)
        for key in _TEXTURE_CONTROL_KEYS:
            assert key in d, (
                f"_defaults_for_slug('{slug}') missing key '{key}'"
            )

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_defaults_texture_mode_is_none(self, slug: str) -> None:
        """PTP-1-AC-5: texture_mode default is 'none'."""
        d = _defaults_for_slug(slug)
        assert d["texture_mode"] == "none", (
            f"_defaults_for_slug('{slug}')['texture_mode'] must be 'none', got {d['texture_mode']!r}"
        )

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_defaults_texture_grad_direction_is_horizontal(self, slug: str) -> None:
        """PTP-1-AC-5: texture_grad_direction default is 'horizontal'."""
        d = _defaults_for_slug(slug)
        assert d["texture_grad_direction"] == "horizontal"

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_defaults_texture_spot_density_is_1_0(self, slug: str) -> None:
        """PTP-1-AC-5: texture_spot_density default is 1.0."""
        d = _defaults_for_slug(slug)
        assert d["texture_spot_density"] == 1.0
        assert type(d["texture_spot_density"]) is float

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_defaults_texture_stripe_width_is_0_2(self, slug: str) -> None:
        """PTP-1-AC-5: texture_stripe_width default is 0.2."""
        d = _defaults_for_slug(slug)
        assert d["texture_stripe_width"] == 0.2
        assert type(d["texture_stripe_width"]) is float

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_defaults_color_fields_are_empty_string(self, slug: str) -> None:
        """PTP-1-AC-5: all 6 color fields default to ''."""
        d = _defaults_for_slug(slug)
        color_keys = [
            "texture_grad_color_a",
            "texture_grad_color_b",
            "texture_spot_color",
            "texture_spot_bg_color",
            "texture_stripe_color",
            "texture_stripe_bg_color",
        ]
        for key in color_keys:
            assert d[key] == "", (
                f"_defaults_for_slug('{slug}')['{key}'] must be '', got {d[key]!r}"
            )

    def test_player_slime_defaults_include_all_10_texture_keys(self) -> None:
        """PTP-3-AC-6: player_slime receives all 10 texture defaults with no special casing."""
        d = _defaults_for_slug("player_slime")
        for key, expected in _TEXTURE_DEFAULTS.items():
            assert key in d, f"player_slime defaults missing key '{key}'"
            assert d[key] == expected, (
                f"player_slime default for '{key}' expected {expected!r}, got {d[key]!r}"
            )

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_options_for_enemy_defaults_match_defaults_for_slug(self, slug: str) -> None:
        """PTP-1-AC-5: options_for_enemy({}) texture values match _defaults_for_slug."""
        d = _defaults_for_slug(slug)
        o = options_for_enemy(slug, {})
        for key in _TEXTURE_CONTROL_KEYS:
            assert o[key] == d[key], (
                f"slug '{slug}': options_for_enemy({{}})[\'{key}\'] = {o[key]!r} "
                f"does not match _defaults_for_slug result {d[key]!r}"
            )


# ---------------------------------------------------------------------------
# PTP-2, PTP-6-AC-4..9,15..17: Coercion and validation
# ---------------------------------------------------------------------------


class TestTextureModeCoercion:
    """PTP-2-AC-1..7, PTP-6-AC-4,5,15: texture_mode coercion via options_for_enemy."""

    def test_invalid_texture_mode_falls_back_to_none(self) -> None:
        """PTP-2-AC-1, PTP-6-AC-4."""
        o = options_for_enemy("slug", {"texture_mode": "invalid"})
        assert o["texture_mode"] == "none", (
            f"invalid texture_mode must coerce to 'none', got {o['texture_mode']!r}"
        )

    def test_valid_gradient_mode_accepted(self) -> None:
        """PTP-2-AC-2, PTP-6-AC-5."""
        o = options_for_enemy("slug", {"texture_mode": "gradient"})
        assert o["texture_mode"] == "gradient"

    def test_valid_spots_mode_accepted(self) -> None:
        """PTP-2-AC-3."""
        o = options_for_enemy("slug", {"texture_mode": "spots"})
        assert o["texture_mode"] == "spots"

    def test_valid_stripes_mode_accepted(self) -> None:
        """PTP-2-AC-4."""
        o = options_for_enemy("slug", {"texture_mode": "stripes"})
        assert o["texture_mode"] == "stripes"

    def test_valid_none_mode_accepted(self) -> None:
        """PTP-2-AC-7: 'none' is a valid mode."""
        o = options_for_enemy("slug", {"texture_mode": "none"})
        assert o["texture_mode"] == "none"

    def test_uppercase_gradient_mode_coerces_to_lowercase(self) -> None:
        """PTP-2-AC-5: case-insensitive coercion via .strip().lower()."""
        o = options_for_enemy("slug", {"texture_mode": "GRADIENT"})
        assert o["texture_mode"] == "gradient"

    def test_capitalized_spots_mode_coerces_to_lowercase(self) -> None:
        """PTP-6-AC-15: 'SPOTS' -> 'spots'."""
        o = options_for_enemy("slug", {"texture_mode": "SPOTS"})
        assert o["texture_mode"] == "spots"

    def test_capitalized_none_mode_coerces_to_lowercase(self) -> None:
        """PTP-2-AC-6: 'None' (capitalized) -> 'none'."""
        o = options_for_enemy("slug", {"texture_mode": "None"})
        assert o["texture_mode"] == "none"

    def test_absent_texture_mode_returns_default_none(self) -> None:
        """PTP-2-AC-7: texture_mode absent -> default 'none'."""
        o = options_for_enemy("slug", {})
        assert o["texture_mode"] == "none"

    def test_empty_string_texture_mode_falls_back_to_none(self) -> None:
        """Empty string is not a valid option -> coerces to default 'none'."""
        o = options_for_enemy("slug", {"texture_mode": ""})
        assert o["texture_mode"] == "none"


class TestGradDirectionCoercion:
    """PTP-2-AC-8,9, PTP-6-AC-16,17: texture_grad_direction coercion."""

    def test_invalid_grad_direction_falls_back_to_horizontal(self) -> None:
        """PTP-2-AC-8, PTP-6-AC-17."""
        o = options_for_enemy("spider", {"texture_grad_direction": "diagonal"})
        assert o["texture_grad_direction"] == "horizontal"

    def test_valid_radial_direction_accepted(self) -> None:
        """PTP-2-AC-9, PTP-6-AC-16."""
        o = options_for_enemy("spider", {"texture_grad_direction": "radial"})
        assert o["texture_grad_direction"] == "radial"

    def test_valid_vertical_direction_accepted(self) -> None:
        o = options_for_enemy("spider", {"texture_grad_direction": "vertical"})
        assert o["texture_grad_direction"] == "vertical"

    def test_valid_horizontal_direction_accepted(self) -> None:
        o = options_for_enemy("spider", {"texture_grad_direction": "horizontal"})
        assert o["texture_grad_direction"] == "horizontal"

    def test_absent_grad_direction_returns_horizontal(self) -> None:
        o = options_for_enemy("slug", {})
        assert o["texture_grad_direction"] == "horizontal"


class TestSpotDensityCoercion:
    """PTP-2-AC-10..14, PTP-6-AC-6,7: texture_spot_density float clamping."""

    def test_spot_density_below_min_clamped_to_01(self) -> None:
        """PTP-2-AC-10, PTP-6-AC-6: 0.0 -> 0.1."""
        o = options_for_enemy("slug", {"texture_spot_density": 0.0})
        assert o["texture_spot_density"] == 0.1, (
            f"texture_spot_density 0.0 must clamp to 0.1, got {o['texture_spot_density']}"
        )

    def test_spot_density_above_max_clamped_to_50(self) -> None:
        """PTP-2-AC-11, PTP-6-AC-7: 99.0 -> 5.0."""
        o = options_for_enemy("slug", {"texture_spot_density": 99.0})
        assert o["texture_spot_density"] == 5.0, (
            f"texture_spot_density 99.0 must clamp to 5.0, got {o['texture_spot_density']}"
        )

    def test_spot_density_valid_mid_value_unchanged(self) -> None:
        """PTP-2-AC-12: 2.5 is within [0.1, 5.0] -> unchanged."""
        o = options_for_enemy("slug", {"texture_spot_density": 2.5})
        assert o["texture_spot_density"] == 2.5

    def test_spot_density_at_boundary_min_unchanged(self) -> None:
        """PTP-2-AC-13: 0.1 is the boundary min -> stays 0.1."""
        o = options_for_enemy("slug", {"texture_spot_density": 0.1})
        assert o["texture_spot_density"] == 0.1

    def test_spot_density_at_boundary_max_unchanged(self) -> None:
        """PTP-2-AC-14: 5.0 is the boundary max -> stays 5.0."""
        o = options_for_enemy("slug", {"texture_spot_density": 5.0})
        assert o["texture_spot_density"] == 5.0

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_spot_density_default_is_float(self, slug: str) -> None:
        """PTP-3-AC-2: default texture_spot_density is Python float 1.0."""
        o = options_for_enemy(slug, {})
        assert type(o["texture_spot_density"]) is float
        assert o["texture_spot_density"] == 1.0

    def test_spot_density_very_negative_clamped_to_min(self) -> None:
        """Below-zero values clamp to 0.1."""
        o = options_for_enemy("slug", {"texture_spot_density": -10.0})
        assert o["texture_spot_density"] == 0.1


class TestStripeWidthCoercion:
    """PTP-2-AC-15..19, PTP-6-AC-8,9: texture_stripe_width float clamping."""

    def test_stripe_width_below_min_clamped_to_005(self) -> None:
        """PTP-2-AC-15, PTP-6-AC-8: 0.0 -> 0.05."""
        o = options_for_enemy("slug", {"texture_stripe_width": 0.0})
        assert o["texture_stripe_width"] == 0.05, (
            f"texture_stripe_width 0.0 must clamp to 0.05, got {o['texture_stripe_width']}"
        )

    def test_stripe_width_above_max_clamped_to_10(self) -> None:
        """PTP-2-AC-16, PTP-6-AC-9: 99.0 -> 1.0."""
        o = options_for_enemy("slug", {"texture_stripe_width": 99.0})
        assert o["texture_stripe_width"] == 1.0, (
            f"texture_stripe_width 99.0 must clamp to 1.0, got {o['texture_stripe_width']}"
        )

    def test_stripe_width_valid_mid_value_unchanged(self) -> None:
        """PTP-2-AC-17: 0.5 is within [0.05, 1.0] -> unchanged."""
        o = options_for_enemy("slug", {"texture_stripe_width": 0.5})
        assert o["texture_stripe_width"] == 0.5

    def test_stripe_width_at_boundary_min_unchanged(self) -> None:
        """PTP-2-AC-18: 0.05 is the boundary min -> stays 0.05."""
        o = options_for_enemy("slug", {"texture_stripe_width": 0.05})
        assert o["texture_stripe_width"] == 0.05

    def test_stripe_width_at_boundary_max_unchanged(self) -> None:
        """PTP-2-AC-19: 1.0 is the boundary max -> stays 1.0."""
        o = options_for_enemy("slug", {"texture_stripe_width": 1.0})
        assert o["texture_stripe_width"] == 1.0

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_stripe_width_default_is_float(self, slug: str) -> None:
        """PTP-3-AC-3: default texture_stripe_width is Python float 0.2."""
        o = options_for_enemy(slug, {})
        assert type(o["texture_stripe_width"]) is float
        assert o["texture_stripe_width"] == 0.2

    def test_stripe_width_very_negative_clamped_to_min(self) -> None:
        """Below-zero values clamp to 0.05."""
        o = options_for_enemy("slug", {"texture_stripe_width": -1.0})
        assert o["texture_stripe_width"] == 0.05


class TestHexColorPassthrough:
    """PTP-2-AC-20,21, PTP-6-AC-10,11: str/hex color fields pass through unchanged."""

    def test_empty_hex_string_passes_through_unchanged(self) -> None:
        """PTP-2-AC-21, PTP-6-AC-10."""
        o = options_for_enemy("slug", {"texture_grad_color_a": ""})
        assert o["texture_grad_color_a"] == ""

    def test_nonempty_hex_string_passes_through_unchanged(self) -> None:
        """PTP-2-AC-20, PTP-6-AC-11."""
        o = options_for_enemy("slug", {"texture_grad_color_a": "ff0000"})
        assert o["texture_grad_color_a"] == "ff0000"

    def test_hex_string_grad_color_b_passes_through(self) -> None:
        o = options_for_enemy("slug", {"texture_grad_color_b": "00ff00"})
        assert o["texture_grad_color_b"] == "00ff00"

    def test_hex_string_spot_color_passes_through(self) -> None:
        o = options_for_enemy("slug", {"texture_spot_color": "0000ff"})
        assert o["texture_spot_color"] == "0000ff"

    def test_hex_string_spot_bg_color_passes_through(self) -> None:
        o = options_for_enemy("slug", {"texture_spot_bg_color": "ffffff"})
        assert o["texture_spot_bg_color"] == "ffffff"

    def test_hex_string_stripe_color_passes_through(self) -> None:
        o = options_for_enemy("slug", {"texture_stripe_color": "aabbcc"})
        assert o["texture_stripe_color"] == "aabbcc"

    def test_hex_string_stripe_bg_color_passes_through(self) -> None:
        o = options_for_enemy("slug", {"texture_stripe_bg_color": "112233"})
        assert o["texture_stripe_bg_color"] == "112233"

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_default_color_fields_round_trip_as_empty_string(self, slug: str) -> None:
        """PTP-3: default empty color fields survive JSON round-trip."""
        o = options_for_enemy(slug, {})
        blob = json.dumps(o)
        parsed = json.loads(blob)
        color_keys = [
            "texture_grad_color_a",
            "texture_grad_color_b",
            "texture_spot_color",
            "texture_spot_bg_color",
            "texture_stripe_color",
            "texture_stripe_bg_color",
        ]
        for key in color_keys:
            assert parsed[key] == "", (
                f"slug '{slug}': JSON round-trip of '{key}' must yield '', got {parsed[key]!r}"
            )


# ---------------------------------------------------------------------------
# PTP-3: Serialization contract
# ---------------------------------------------------------------------------


class TestSerializationContract:
    """PTP-3: all 10 texture keys are JSON-serializable flat top-level keys."""

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_options_for_enemy_includes_all_10_texture_keys(self, slug: str) -> None:
        """PTP-2-AC-22: all 10 keys in output of options_for_enemy(slug, {})."""
        o = options_for_enemy(slug, {})
        for key in _TEXTURE_CONTROL_KEYS:
            assert key in o, (
                f"options_for_enemy('{slug}', {{}}) missing key '{key}'"
            )

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_options_for_enemy_texture_keys_are_top_level(self, slug: str) -> None:
        """PTP-3-AC-7: texture keys are flat top-level keys, not nested."""
        o = options_for_enemy(slug, {})
        for key in _TEXTURE_CONTROL_KEYS:
            assert key in o, f"key '{key}' must be a flat top-level key"
            # Confirm it is not nested under known sub-objects.
            for sub_key in ("features", "zone_geometry_extras", "mesh"):
                if sub_key in o and isinstance(o[sub_key], dict):
                    assert key not in o[sub_key], (
                        f"key '{key}' must not appear under '{sub_key}' sub-object for slug '{slug}'"
                    )

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_json_dumps_succeeds_for_all_slugs(self, slug: str) -> None:
        """PTP-3-AC-4: json.dumps(options_for_enemy(slug, {})) must not raise TypeError."""
        o = options_for_enemy(slug, {})
        blob = json.dumps(o)  # must not raise
        assert isinstance(blob, str)

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_json_round_trip_preserves_all_texture_defaults(self, slug: str) -> None:
        """PTP-3-AC-5: JSON round-trip preserves all 10 texture keys at defaults."""
        o = options_for_enemy(slug, {})
        parsed = json.loads(json.dumps(o))
        for key, expected_default in _TEXTURE_DEFAULTS.items():
            assert key in parsed, (
                f"slug '{slug}': JSON round-trip result missing key '{key}'"
            )
            assert parsed[key] == expected_default, (
                f"slug '{slug}': JSON round-trip '{key}' expected {expected_default!r}, "
                f"got {parsed[key]!r}"
            )

    def test_json_dumps_texture_mode_is_string_none(self) -> None:
        """PTP-3-AC-1: texture_mode default serializes to JSON string 'none'."""
        blob = json.dumps(options_for_enemy("slug", {}))
        parsed = json.loads(blob)
        assert parsed["texture_mode"] == "none"
        assert isinstance(parsed["texture_mode"], str)

    def test_json_dumps_texture_spot_density_is_float(self) -> None:
        """PTP-3-AC-2: texture_spot_density serializes as JSON number."""
        blob = json.dumps(options_for_enemy("slug", {}))
        parsed = json.loads(blob)
        assert parsed["texture_spot_density"] == 1.0
        assert isinstance(parsed["texture_spot_density"], float)

    def test_json_dumps_texture_stripe_width_is_float(self) -> None:
        """PTP-3-AC-3: texture_stripe_width serializes as JSON number."""
        blob = json.dumps(options_for_enemy("slug", {}))
        parsed = json.loads(blob)
        assert parsed["texture_stripe_width"] == 0.2
        assert isinstance(parsed["texture_stripe_width"], float)

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_round_trip_double_options_for_enemy_call(self, slug: str) -> None:
        """PTP-2-AC-23 analogue: two-hop round-trip produces consistent results."""
        o1 = options_for_enemy(slug, {})
        o2 = options_for_enemy(slug, json.loads(json.dumps(o1)))
        for key in _TEXTURE_CONTROL_KEYS:
            assert o2[key] == o1[key], (
                f"slug '{slug}': two-hop round-trip mismatch on '{key}': "
                f"{o1[key]!r} vs {o2[key]!r}"
            )


# ---------------------------------------------------------------------------
# PTP-2-AC-23, PTP-6-AC-13: Idempotency
# ---------------------------------------------------------------------------


class TestIdempotency:
    """PTP-2-AC-23, PTP-6-AC-13: options_for_enemy called twice returns equal dicts."""

    def test_idempotent_spots_mode_with_density(self) -> None:
        """PTP-2-AC-23, PTP-6-AC-13."""
        params = {"texture_mode": "spots", "texture_spot_density": 3.0}
        o1 = options_for_enemy("claw_crawler", params)
        o2 = options_for_enemy("claw_crawler", params)
        assert o1 == o2, (
            "options_for_enemy must return equal dicts on identical inputs"
        )

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_idempotent_default_inputs(self, slug: str) -> None:
        """Idempotency for empty input across all slugs."""
        o1 = options_for_enemy(slug, {})
        o2 = options_for_enemy(slug, {})
        for key in _TEXTURE_CONTROL_KEYS:
            assert o1[key] == o2[key], (
                f"slug '{slug}': idempotency failed on key '{key}'"
            )

    def test_idempotent_stripes_mode(self) -> None:
        """Idempotency for stripes mode with all params."""
        params = {
            "texture_mode": "stripes",
            "texture_stripe_color": "ff0000",
            "texture_stripe_bg_color": "0000ff",
            "texture_stripe_width": 0.5,
        }
        o1 = options_for_enemy("spider", params)
        o2 = options_for_enemy("spider", params)
        assert o1["texture_mode"] == o2["texture_mode"] == "stripes"
        assert o1["texture_stripe_width"] == o2["texture_stripe_width"] == 0.5
        assert o1["texture_stripe_color"] == o2["texture_stripe_color"] == "ff0000"

    def test_idempotent_gradient_mode(self) -> None:
        """Idempotency for gradient mode."""
        params = {
            "texture_mode": "gradient",
            "texture_grad_color_a": "aabbcc",
            "texture_grad_direction": "radial",
        }
        o1 = options_for_enemy("imp", params)
        o2 = options_for_enemy("imp", params)
        assert o1["texture_mode"] == "gradient"
        assert o1["texture_grad_direction"] == "radial"
        assert o1 == o2


# ---------------------------------------------------------------------------
# Regression: existing controls not broken (PTP-8)
# ---------------------------------------------------------------------------


class TestRegressionExistingControls:
    """PTP-8-AC-1,3: existing controls still work after texture additions."""

    def test_spider_eye_count_default_still_works(self) -> None:
        """PTP-8-AC-3: eye_count unaffected."""
        o = options_for_enemy("spider", {})
        assert o["eye_count"] == 2

    def test_spider_api_controls_still_include_eye_count(self) -> None:
        """PTP-8-AC-3: eye_count still in api controls."""
        ctrl = animated_build_controls_for_api()
        keys = {c["key"] for c in ctrl["spider"]}
        assert "eye_count" in keys

    def test_mouth_enabled_default_still_false(self) -> None:
        """PTP-8: mouth_enabled unaffected."""
        o = options_for_enemy("spider", {})
        assert o["mouth_enabled"] is False
        assert type(o["mouth_enabled"]) is bool

    def test_tail_enabled_default_still_false(self) -> None:
        """PTP-8: tail_enabled unaffected."""
        o = options_for_enemy("spider", {})
        assert o["tail_enabled"] is False

    def test_invalid_mouth_shape_still_falls_back_to_smile(self) -> None:
        """PTP-8: mouth_shape coercion unaffected."""
        o = options_for_enemy("spider", {"mouth_shape": "INVALID"})
        assert o["mouth_shape"] == "smile"

    def test_tail_length_clamping_still_works(self) -> None:
        """PTP-8: tail_length clamping unaffected."""
        o = options_for_enemy("slug", {"tail_length": 99.0})
        assert o["tail_length"] == 3.0
