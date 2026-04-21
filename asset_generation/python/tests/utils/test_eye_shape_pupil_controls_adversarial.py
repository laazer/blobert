"""Eye shape & pupil system — adversarial tests for Python build controls.

Targets: ESPS-1, ESPS-2, ESPS-5, ESPS-6, ESPS-7

Gaps exposed vs. the Test Designer suite:
  - Mutation guard: options_for_enemy must not mutate its input dict
  - Idempotency: calling options_for_enemy twice with same dict returns identical results
  - Dynamic slug set: the three controls are present for every slug returned by
    animated_build_controls_for_api(), not just the hardcoded list (guards against
    a new slug being added to the pipeline without getting the controls)
  - None for pupil_enabled: must coerce to False (not crash)
  - Whitespace-only strings for pupil_shape and eye_shape: must fall back to defaults
  - pupil_enabled=True does NOT suppress pupil_shape from options_for_enemy output
    (server-side disabling is a UI concern only — ESPS-8)
  - _eye_shape_pupil_control_defs returns fresh list on each call (no shared mutable state)
  - options_for_enemy output is a new dict independent of the input
"""

import json

import pytest

from src.utils.build_options import (
    _defaults_for_slug,
    animated_build_controls_for_api,
    options_for_enemy,
)

# ---------------------------------------------------------------------------
# Mutation guard: input dict must not be modified
# ---------------------------------------------------------------------------


class TestInputDictNotMutated:
    """ESPS-2 mutation guard: coerce/validate must return a new dict, never modify the caller's dict."""

    def test_options_for_enemy_does_not_mutate_input_dict_spider(self) -> None:
        """Passing a dict and then checking it is unchanged after the call."""
        original = {"eye_shape": "INVALID", "pupil_enabled": 1, "pupil_shape": "NOTREAL"}
        snapshot = dict(original)
        options_for_enemy("spider", original)
        assert original == snapshot, (
            "options_for_enemy must not mutate the caller's input dict; "
            f"expected {snapshot!r} but got {original!r} after call"
        )

    def test_options_for_enemy_does_not_mutate_input_dict_slug(self) -> None:
        original = {"eye_shape": "oval", "pupil_enabled": False}
        snapshot = dict(original)
        options_for_enemy("slug", original)
        assert original == snapshot

    def test_options_for_enemy_result_is_new_dict(self) -> None:
        """The returned dict must not be the same object as the input dict."""
        inp = {"eye_shape": "circle"}
        out = options_for_enemy("spider", inp)
        assert out is not inp, "options_for_enemy must return a new dict, not the input dict"


# ---------------------------------------------------------------------------
# Idempotency: calling twice with the same input produces identical output
# ---------------------------------------------------------------------------


class TestIdempotency:
    """ESPS-2 / ESPS-5: options_for_enemy called twice with the same dict produces identical results."""

    @pytest.mark.parametrize("slug", ["spider", "slug", "claw_crawler", "imp", "carapace_husk"])
    def test_options_for_enemy_idempotent_on_defaults(self, slug: str) -> None:
        o1 = options_for_enemy(slug, {})
        o2 = options_for_enemy(slug, {})
        assert o1["eye_shape"] == o2["eye_shape"]
        assert o1["pupil_enabled"] == o2["pupil_enabled"]
        assert o1["pupil_shape"] == o2["pupil_shape"]

    @pytest.mark.parametrize("slug", ["spider", "claw_crawler"])
    def test_options_for_enemy_idempotent_on_non_default_values(self, slug: str) -> None:
        opts = {"eye_shape": "slit", "pupil_enabled": True, "pupil_shape": "diamond"}
        o1 = options_for_enemy(slug, opts)
        o2 = options_for_enemy(slug, opts)
        assert o1["eye_shape"] == o2["eye_shape"]
        assert o1["pupil_enabled"] == o2["pupil_enabled"]
        assert o1["pupil_shape"] == o2["pupil_shape"]

    def test_options_for_enemy_idempotent_after_round_trip(self) -> None:
        """Round-trip output fed back in must produce identical results."""
        o1 = options_for_enemy("spider", {"eye_shape": "square", "pupil_enabled": True, "pupil_shape": "slit"})
        o2 = options_for_enemy("spider", json.loads(json.dumps(o1)))
        assert o2["eye_shape"] == o1["eye_shape"]
        assert o2["pupil_enabled"] == o1["pupil_enabled"]
        assert o2["pupil_shape"] == o1["pupil_shape"]


# ---------------------------------------------------------------------------
# Dynamic slug set: controls must be present for all slugs in the API, not just
# the hardcoded list in the Test Designer suite
# ---------------------------------------------------------------------------


class TestDynamicSlugCoverage:
    """ESPS-1-AC-1 dynamic check: every slug returned by animated_build_controls_for_api()
    must declare all three new controls regardless of whether the slug was anticipated
    when the test was originally written.

    This guard catches the regression where a new slug is added to the pipeline but
    _eye_shape_pupil_control_defs() is not wired for it.
    """

    def test_every_api_slug_has_eye_shape_key(self) -> None:
        ctrl = animated_build_controls_for_api()
        for slug, defs in ctrl.items():
            keys = {d["key"] for d in defs}
            assert "eye_shape" in keys, (
                f"Slug '{slug}' (returned by animated_build_controls_for_api) "
                f"is missing 'eye_shape'. Was a new slug added without wiring _eye_shape_pupil_control_defs?"
            )

    def test_every_api_slug_has_pupil_enabled_key(self) -> None:
        ctrl = animated_build_controls_for_api()
        for slug, defs in ctrl.items():
            keys = {d["key"] for d in defs}
            assert "pupil_enabled" in keys, (
                f"Slug '{slug}' is missing 'pupil_enabled'."
            )

    def test_every_api_slug_has_pupil_shape_key(self) -> None:
        ctrl = animated_build_controls_for_api()
        for slug, defs in ctrl.items():
            keys = {d["key"] for d in defs}
            assert "pupil_shape" in keys, (
                f"Slug '{slug}' is missing 'pupil_shape'."
            )

    def test_every_api_slug_defaults_contain_eye_controls(self) -> None:
        """_defaults_for_slug must contain defaults for every slug the API knows about."""
        ctrl = animated_build_controls_for_api()
        for slug in ctrl:
            d = _defaults_for_slug(slug)
            assert "eye_shape" in d, f"_defaults_for_slug('{slug}') missing 'eye_shape'"
            assert "pupil_enabled" in d, f"_defaults_for_slug('{slug}') missing 'pupil_enabled'"
            assert "pupil_shape" in d, f"_defaults_for_slug('{slug}') missing 'pupil_shape'"


# ---------------------------------------------------------------------------
# None input for pupil_enabled
# ---------------------------------------------------------------------------


class TestNoneInputCoercion:
    """ESPS-2-AC-3..5: None is a falsy value and must coerce to False, not crash.

    # CHECKPOINT: spec does not explicitly address None input for pupil_enabled.
    # Conservative assumption: None is falsy → coerces to False (consistent with
    # _coerce_boolish treating it like any falsy value). Test encodes this assumption.
    """

    def test_none_pupil_enabled_coerces_to_false_spider(self) -> None:
        # CHECKPOINT: None for a bool control is a common API boundary value.
        # Assume: coerces to False (falsy → False).
        o = options_for_enemy("spider", {"pupil_enabled": None})
        assert o["pupil_enabled"] is False, (
            "None for pupil_enabled must coerce to False; received: "
            f"{o['pupil_enabled']!r} (type={type(o['pupil_enabled']).__name__})"
        )
        assert type(o["pupil_enabled"]) is bool

    def test_none_pupil_enabled_coerces_to_false_claw_crawler(self) -> None:
        # CHECKPOINT: same None-coercion assumption for a different slug.
        o = options_for_enemy("claw_crawler", {"pupil_enabled": None})
        assert o["pupil_enabled"] is False
        assert type(o["pupil_enabled"]) is bool


# ---------------------------------------------------------------------------
# Whitespace-only strings
# ---------------------------------------------------------------------------


class TestWhitespaceInputFallback:
    """ESPS-2-AC-1, ESPS-2-AC-7: whitespace-only strings are not valid option values
    and must fall back to defaults.

    # CHECKPOINT: spec only says 'invalid string falls back'. A whitespace-only
    # string (e.g. "  ") is invalid per the options list.
    # Conservative assumption: treated as an invalid option → default fallback.
    """

    def test_whitespace_only_eye_shape_falls_back_to_circle(self) -> None:
        # CHECKPOINT: "  " is not in ["circle", "oval", "slit", "square"] → fallback "circle".
        o = options_for_enemy("spider", {"eye_shape": "  "})
        assert o["eye_shape"] == "circle", (
            f"Whitespace-only eye_shape must fall back to 'circle'; got {o['eye_shape']!r}"
        )

    def test_whitespace_only_pupil_shape_falls_back_to_dot(self) -> None:
        # CHECKPOINT: "  " is not in ["dot", "slit", "diamond"] → fallback "dot".
        o = options_for_enemy("slug", {"pupil_shape": "  "})
        assert o["pupil_shape"] == "dot", (
            f"Whitespace-only pupil_shape must fall back to 'dot'; got {o['pupil_shape']!r}"
        )

    def test_tab_character_eye_shape_falls_back(self) -> None:
        o = options_for_enemy("claw_crawler", {"eye_shape": "\t"})
        assert o["eye_shape"] == "circle"

    def test_newline_character_pupil_shape_falls_back(self) -> None:
        o = options_for_enemy("spider", {"pupil_shape": "\n"})
        assert o["pupil_shape"] == "dot"


# ---------------------------------------------------------------------------
# pupil_enabled=True does NOT suppress pupil_shape from options_for_enemy output
# (disabling is UI-only per ESPS-8, not server-side)
# ---------------------------------------------------------------------------


class TestPupilShapeNotSuppressedServerSide:
    """ESPS-2 / ESPS-8: the server-side coercion must NOT strip pupil_shape from
    the returned dict when pupil_enabled is True. The UI conditional disabling
    (ESPS-8) is a presentation concern only. options_for_enemy must return
    pupil_shape regardless of pupil_enabled value.
    """

    def test_pupil_shape_present_in_output_when_pupil_enabled_true(self) -> None:
        o = options_for_enemy("spider", {"pupil_enabled": True, "pupil_shape": "diamond"})
        assert "pupil_shape" in o, "pupil_shape must be present in options output when pupil_enabled=True"
        assert o["pupil_shape"] == "diamond"

    def test_pupil_shape_present_in_output_when_pupil_enabled_false(self) -> None:
        """pupil_shape must also be present (with its default) when pupil_enabled=False;
        the UI disables the control but the value is still stored."""
        o = options_for_enemy("spider", {"pupil_enabled": False})
        assert "pupil_shape" in o, "pupil_shape must be present even when pupil_enabled=False"

    @pytest.mark.parametrize("slug", ["spider", "slug", "claw_crawler", "imp"])
    def test_pupil_shape_always_in_options_output(self, slug: str) -> None:
        """pupil_shape must appear in options_for_enemy output for every slug."""
        o = options_for_enemy(slug, {"pupil_enabled": True, "pupil_shape": "slit"})
        assert "pupil_shape" in o, f"slug '{slug}': pupil_shape missing from options when pupil_enabled=True"
        assert o["pupil_shape"] == "slit"


# ---------------------------------------------------------------------------
# _eye_shape_pupil_control_defs returns fresh list each call (no shared mutable state)
# ---------------------------------------------------------------------------


class TestHelperReturnsFreshList:
    """ESPS-1-AC-7: the helper must not return a shared mutable list.
    Mutating the returned list must not affect subsequent calls.
    """

    def test_helper_returns_distinct_list_objects(self) -> None:
        import src.utils.build_options as abo
        first = abo._eye_shape_pupil_control_defs()
        second = abo._eye_shape_pupil_control_defs()
        assert first is not second, (
            "_eye_shape_pupil_control_defs must return a new list each call, "
            "not a module-level singleton"
        )

    def test_mutating_returned_list_does_not_affect_next_call(self) -> None:
        import src.utils.build_options as abo
        first = abo._eye_shape_pupil_control_defs()
        first.clear()  # destroy the list contents
        second = abo._eye_shape_pupil_control_defs()
        assert len(second) == 3, (
            "Mutating the list returned by _eye_shape_pupil_control_defs must not "
            f"affect subsequent calls; expected 3 entries, got {len(second)}"
        )

    def test_mutating_returned_dict_entry_does_not_affect_next_call(self) -> None:
        import src.utils.build_options as abo
        first = abo._eye_shape_pupil_control_defs()
        # Poison the eye_shape options list
        entry = next(d for d in first if d["key"] == "eye_shape")
        original_options = list(entry["options"])
        entry["options"].clear()
        entry["options"].append("poisoned")
        second = abo._eye_shape_pupil_control_defs()
        eye_entry = next(d for d in second if d["key"] == "eye_shape")
        assert eye_entry["options"] == original_options, (
            "Mutating a dict entry in the returned list must not affect the next call. "
            f"Expected {original_options!r}, got {eye_entry['options']!r}. "
            "Control defs must not share mutable list references across calls."
        )


# ---------------------------------------------------------------------------
# Combinatorial: boundary + invalid combinations
# ---------------------------------------------------------------------------


class TestCombinatorialBoundary:
    """Multi-factor edge combinations not covered by the Test Designer suite."""

    def test_all_three_keys_invalid_at_once_falls_back_to_all_defaults(self) -> None:
        """Simultaneous invalid values for all three new keys → all defaults returned."""
        o = options_for_enemy("spider", {
            "eye_shape": "INVALID",
            "pupil_enabled": "notabool",
            "pupil_shape": "INVALID",
        })
        assert o["eye_shape"] == "circle"
        assert o["pupil_shape"] == "dot"
        # "notabool" is a truthy non-empty string → coerces to True per _coerce_boolish.
        # CHECKPOINT: "notabool" is non-empty string, truthy → True.
        # This is the most conservative reading of the bool coercion spec.
        assert type(o["pupil_enabled"]) is bool

    def test_empty_dict_input_returns_all_three_defaults_for_every_slug(self) -> None:
        ctrl = animated_build_controls_for_api()
        for slug in ctrl:
            o = options_for_enemy(slug, {})
            assert o["eye_shape"] == "circle", f"slug='{slug}'"
            assert o["pupil_enabled"] is False, f"slug='{slug}'"
            assert o["pupil_shape"] == "dot", f"slug='{slug}'"

    def test_extra_unknown_keys_do_not_suppress_eye_shape(self) -> None:
        """Spurious unknown keys in input must not cause eye_shape to disappear."""
        o = options_for_enemy("spider", {"UNKNOWN_KEY": "blah", "eye_shape": "oval"})
        assert o["eye_shape"] == "oval"

    def test_integer_string_eye_shape_falls_back(self) -> None:
        """Numeric strings are not valid shape names."""
        o = options_for_enemy("slug", {"eye_shape": "42"})
        assert o["eye_shape"] == "circle"

    def test_unicode_eye_shape_falls_back(self) -> None:
        """Unicode strings are not valid option values."""
        o = options_for_enemy("spider", {"eye_shape": "circ\u00e9"})
        assert o["eye_shape"] == "circle"

    def test_list_value_for_eye_shape_falls_back(self) -> None:
        """A list passed as eye_shape value must not crash and must fall back."""
        # CHECKPOINT: a list is not a string option, must treat as invalid → default.
        o = options_for_enemy("spider", {"eye_shape": ["circle"]})
        assert o["eye_shape"] == "circle"
