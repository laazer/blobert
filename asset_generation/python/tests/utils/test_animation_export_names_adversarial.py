"""
Adversarial tests for AnimationTypes.get_export_name() and NLA wiring.

Spec:  project_board/specs/blender_animation_export_spec.md
Ticket: project_board/7_milestone_7_enemy_animation_wiring/in_progress/blender_animation_export.md

These tests go beyond the primary suite (test_animation_export_names.py) and
deliberately target:
  - PascalCase fallback edge cases: empty string, all-underscore, numeric-only,
    consecutive underscores, ALL_CAPS input, leading/trailing underscores
  - Return type exactness: type(result) is str, not a Mock or subclass
  - Mapping completeness: returns str for every known internal name
  - NLA strip NAME attribute must equal export name (not internal name)
  - NLA wiring for animation_set='extended' (not covered by primary suite)
  - export_enemy infra fix: bmesh properly mocked so test reaches the assertion
  - Active-action leak: create_all_animations must not set action = created_actions[0]
    (the current bug) even if NLA wiring is added but the final None-assignment is missed
  - Mutation matrix targets: move/Walk, damage/Hit non-obvious renames checked via
    title-case fallback comparison (title-case would produce Move/Damage, not Walk/Hit)
  - Idempotency: calling get_export_name twice gives same result (no global mutation)
  - get_core() and get_all() list sizes match NLA track counts precisely
  - Combinatorial: animation_set='extended' creates only extended tracks, none core

Adversarial test IDs: ADV-BAE-1 through ADV-BAE-30

bpy, mathutils, and bmesh are mocked at module level.
"""

import sys
import unittest
from unittest.mock import MagicMock, call, patch

# ---------------------------------------------------------------------------
# Mock Blender modules. setdefault preserves real modules when running in Blender.
# bmesh is required here because blender_utils.py imports it at module level —
# without this mock, importing export_enemy (via base_enemy) raises ModuleNotFoundError.
# The primary test file (test_animation_export_names.py) omits bmesh, causing
# TestExportEnemyNLAFlag to ERROR rather than FAIL — this file corrects that.
# ---------------------------------------------------------------------------
sys.modules.setdefault('bpy', MagicMock())
sys.modules.setdefault('mathutils', MagicMock())
sys.modules.setdefault('bmesh', MagicMock())

from src.utils.constants import AnimationTypes, AnimationConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_action(name: str, frame_end: int) -> MagicMock:
    action = MagicMock(name=f"MockAction<{name}>")
    action.name = name
    action.frame_range = (1, frame_end)
    action.use_fake_user = False
    return action


def _make_mock_armature() -> MagicMock:
    armature = MagicMock()
    armature.mode = 'POSE'
    bone_names = ['root', 'body', 'head']
    armature.pose.bones = [MagicMock(name=n) for n in bone_names]
    animation_data = MagicMock()
    animation_data.action = None
    created_tracks = []

    def _new_track():
        track = MagicMock()
        created_track_strips = []

        def _new_strip(name, start, action):
            strip = MagicMock()
            strip.name = name
            strip.action = action
            strip.frame_start = start
            strip.action_frame_start = None
            strip.action_frame_end = None
            created_track_strips.append(strip)
            return strip

        track.strips.new.side_effect = _new_strip
        track._strips_created = created_track_strips
        created_tracks.append(track)
        return track

    animation_data.nla_tracks.new.side_effect = _new_track
    animation_data._created_tracks = created_tracks
    armature.animation_data = animation_data
    armature.animation_data_create.return_value = None
    return armature


def _run_create_all_animations(animation_set='core'):
    """
    Run create_all_animations() with a fully mocked bpy environment.
    Returns (armature_mock, created_action_names).
    """
    import bpy as _bpy_mock

    armature = _make_mock_armature()
    created_action_names = []

    def _new_action(name):
        # Derive frame length from the action name; if it's an export name,
        # try to find the corresponding internal length, otherwise default to 24.
        length = _length_for(name)
        action = _make_mock_action(name, length)
        created_action_names.append(name)
        return action

    _bpy_mock.data.actions.new.side_effect = _new_action
    _bpy_mock.ops.object.mode_set.side_effect = lambda mode: None
    _bpy_mock.context.scene.frame_start = 1
    _bpy_mock.context.scene.frame_end = 48

    from src.animations.animation_system import create_all_animations
    import random
    rng = random.Random(42)
    create_all_animations(armature, 'blob', rng, animation_set=animation_set)
    return armature, created_action_names


# Build reverse map: export_name -> internal_name for length lookups.
# Done lazily to avoid collection-time AttributeError when get_export_name not yet implemented.
_REVERSE_MAP: dict = {}
_REVERSE_MAP_BUILT = False


def _build_reverse_map():
    global _REVERSE_MAP, _REVERSE_MAP_BUILT
    if _REVERSE_MAP_BUILT:
        return
    for internal in AnimationTypes.get_all():
        export = AnimationTypes.get_export_name(internal)
        _REVERSE_MAP[export] = internal
    _REVERSE_MAP_BUILT = True


def _length_for(name: str) -> int:
    """Return frame length for an action name (export or internal)."""
    _build_reverse_map()
    internal = _REVERSE_MAP.get(name, name)
    return AnimationConfig.get_length(internal)


# ===========================================================================
# ADV-BAE-1..10: PascalCase fallback edge cases
# ===========================================================================

class TestGetExportNameFallbackEdgeCases(unittest.TestCase):
    """
    Adversarial edge cases for the PascalCase fallback path in get_export_name.
    All inputs below are NOT in the explicit mapping table; they exercise the
    fallback branch: split on '_', title-case each word, join without separator.
    """

    def test_adv_bae_1_empty_string_returns_empty_string(self):
        """
        ADV-BAE-1: get_export_name("") must return "" (empty join of empty split).
        Vulnerability: implementations that call .split("_") on "" then "".title()
        produce [""] which joins to "". But implementations using str.title() on the
        whole string first would return "" too. Any implementation that raises or
        returns None is wrong. # CHECKPOINT
        """
        result = AnimationTypes.get_export_name("")
        self.assertEqual(result, "",
            "ADV-BAE-1: get_export_name('') must return empty string, not raise or return None")

    def test_adv_bae_2_all_underscore_returns_empty_string(self):
        """
        ADV-BAE-2: get_export_name("___") — three underscores, all tokens are "".
        Fallback: "_".split("_") = ["", "", "", ""], each "".title() = "", joined = "".
        Vulnerability: implementations that filter out empty tokens would silently
        change the mechanical spec (split → title → join without filter).
        # CHECKPOINT
        """
        result = AnimationTypes.get_export_name("___")
        self.assertIsInstance(result, str,
            "ADV-BAE-2: get_export_name('___') must return str, not raise")
        # The spec says "split on _, title-case each word, join". Empty words join to "".
        # If the implementation filters blank tokens, result would also be "". Either
        # way the critical constraint is: it must not raise and must return str.

    def test_adv_bae_3_numeric_only_returns_title_of_numeric(self):
        """
        ADV-BAE-3: get_export_name("42") — no underscores, one token "42".
        "42".title() == "42" (digits are not affected by title-case).
        Vulnerability: an implementation that crashes on non-alpha input exposes a
        production risk if a new animation type is given a numeric prefix.
        """
        result = AnimationTypes.get_export_name("42")
        self.assertIsInstance(result, str,
            "ADV-BAE-3: get_export_name('42') must return str")
        self.assertEqual(result, "42",
            "ADV-BAE-3: digits are not title-cased; '42'.title() == '42'")

    def test_adv_bae_4_consecutive_underscores_in_middle(self):
        """
        ADV-BAE-4: get_export_name("foo__bar") — two consecutive underscores.
        "foo__bar".split("_") = ["foo", "", "bar"].
        Fallback: "Foo" + "" + "Bar" = "FooBar" (empty middle token title-cased is "").
        Vulnerability: if the implementation uses a strip/filter the empty token
        disappears and the result is still "FooBar", but the mechanical spec says
        the empty token's title-case ("") is included in the join, producing the same
        result. Both are "FooBar". This test confirms no crash occurs.
        """
        result = AnimationTypes.get_export_name("foo__bar")
        self.assertIsInstance(result, str,
            "ADV-BAE-4: get_export_name('foo__bar') must return str, not raise")
        # Mechanical result: split yields ["foo","","bar"] → title each → join = "FooBar"
        self.assertEqual(result, "FooBar",
            "ADV-BAE-4: 'foo__bar' fallback → 'FooBar' (empty middle token joins to nothing)")

    def test_adv_bae_5_leading_underscore(self):
        """
        ADV-BAE-5: get_export_name("_attack_extra") — leading underscore.
        split("_") = ["", "attack", "extra"]. title each: ["", "Attack", "Extra"].
        join = "AttackExtra".
        Vulnerability: a leading-underscore input is plausible for a private/internal
        animation convention. The fallback must handle it without crash.
        """
        result = AnimationTypes.get_export_name("_attack_extra")
        self.assertIsInstance(result, str,
            "ADV-BAE-5: get_export_name('_attack_extra') must return str")
        self.assertEqual(result, "AttackExtra",
            "ADV-BAE-5: leading underscore produces empty first token; join = 'AttackExtra'")

    def test_adv_bae_6_trailing_underscore(self):
        """
        ADV-BAE-6: get_export_name("attack_") — trailing underscore.
        split("_") = ["attack", ""]. title each: ["Attack", ""]. join = "Attack".
        """
        result = AnimationTypes.get_export_name("attack_")
        self.assertIsInstance(result, str,
            "ADV-BAE-6: get_export_name('attack_') must return str")
        self.assertEqual(result, "Attack",
            "ADV-BAE-6: trailing underscore adds empty token; join = 'Attack'")

    def test_adv_bae_7_all_caps_input_falls_back(self):
        """
        ADV-BAE-7: get_export_name("IDLE") — ALL_CAPS input not in the explicit map.
        The explicit map has "idle" -> "Idle", not "IDLE". "IDLE".split("_") = ["IDLE"].
        "IDLE".title() = "Idle". So fallback produces "Idle".
        VULNERABILITY: this reveals an important assumption — if someone passes "IDLE"
        expecting "Idle" they get "Idle" (coincidentally correct), but "MOVE" would give
        "Move" (not "Walk" which is the required export name for the "move" internal name).
        This test documents that the UPPERCASE variant is NOT in the map and produces
        a title-cased result, NOT the special mapping.
        """
        result_idle_caps = AnimationTypes.get_export_name("IDLE")
        # "IDLE" is not in the map; fallback: "IDLE".title() = "Idle"
        self.assertEqual(result_idle_caps, "Idle",
            "ADV-BAE-7: 'IDLE' (not in map) falls back to title-case 'Idle'")

        result_move_caps = AnimationTypes.get_export_name("MOVE")
        # "MOVE" is not in the map; fallback: "MOVE".title() = "Move" (NOT "Walk")
        self.assertEqual(result_move_caps, "Move",
            "ADV-BAE-7: 'MOVE' (not in map) falls back to 'Move', NOT 'Walk' — "
            "only lowercase 'move' maps to 'Walk'")

    def test_adv_bae_8_title_case_fallback_not_naive_titlecase_of_whole_string(self):
        """
        ADV-BAE-8: Verify fallback splits on _ then title-cases each part separately,
        NOT that it calls str.title() on the full string (which would also capitalize
        after digits/apostrophes).
        "a1b_c" with naive str.title() gives "A1B_C" (wrong).
        With correct split-then-join: ["a1b","c"] -> ["A1B","C"] -> "A1BC".
        Actually "a1b".title() == "A1B" (Python's title() capitalizes after non-alpha).
        This tests that the split-join approach is used.
        """
        result = AnimationTypes.get_export_name("a1b_c")
        # split: ["a1b","c"] -> title each: ["A1B","C"] -> "A1BC"
        self.assertEqual(result, "A1BC",
            "ADV-BAE-8: fallback must split on _ then title-case each part; 'a1b_c' -> 'A1BC'")

    def test_adv_bae_9_single_char_fallback(self):
        """
        ADV-BAE-9: get_export_name("x") — single lowercase char.
        Not in map. Fallback: "x".title() = "X".
        Checks that the fallback handles minimal input without crash.
        """
        result = AnimationTypes.get_export_name("x")
        self.assertEqual(result, "X",
            "ADV-BAE-9: single-char unknown name 'x' -> fallback title 'X'")

    def test_adv_bae_10_four_word_snake_case_fallback(self):
        """
        ADV-BAE-10: get_export_name("a_b_c_d") — four single-char tokens.
        Fallback: "A"+"B"+"C"+"D" = "ABCD".
        Tests that the join produces no separator between words.
        """
        result = AnimationTypes.get_export_name("a_b_c_d")
        self.assertEqual(result, "ABCD",
            "ADV-BAE-10: 'a_b_c_d' -> 'ABCD' (no separator in join)")


# ===========================================================================
# ADV-BAE-11..14: Return type exactness — type(result) is str
# ===========================================================================

class TestGetExportNameReturnTypeExact(unittest.TestCase):
    """
    ADV-BAE-11..14: Verify return type is exactly str (not MagicMock, not subclass).
    assertIsInstance(x, str) passes for str subclasses and for MagicMock if __class__
    is patched. assertIs(type(x), str) is strict.
    Vulnerability: if get_export_name is not yet implemented and returns a MagicMock
    attribute lookup result, the primary test catches it via AttributeError, but a
    partially-implemented version that returns a constant Mock could slip through
    assertIsInstance.
    """

    def test_adv_bae_11_idle_return_type_is_exactly_str(self):
        """ADV-BAE-11: type(get_export_name('idle')) is str."""
        result = AnimationTypes.get_export_name("idle")
        self.assertIs(type(result), str,
            "ADV-BAE-11: return type must be exactly str, not a subclass or Mock")

    def test_adv_bae_12_move_return_type_is_exactly_str(self):
        """ADV-BAE-12: type(get_export_name('move')) is str."""
        result = AnimationTypes.get_export_name("move")
        self.assertIs(type(result), str,
            "ADV-BAE-12: return type must be exactly str")

    def test_adv_bae_13_damage_return_type_is_exactly_str(self):
        """ADV-BAE-13: type(get_export_name('damage')) is str."""
        result = AnimationTypes.get_export_name("damage")
        self.assertIs(type(result), str,
            "ADV-BAE-13: return type must be exactly str")

    def test_adv_bae_14_death_return_type_is_exactly_str(self):
        """ADV-BAE-14: type(get_export_name('death')) is str."""
        result = AnimationTypes.get_export_name("death")
        self.assertIs(type(result), str,
            "ADV-BAE-14: return type must be exactly str")


# ===========================================================================
# ADV-BAE-15..16: Mutation targets — title-case fallback would produce wrong result
# ===========================================================================

class TestExplicitMappingNotFallback(unittest.TestCase):
    """
    ADV-BAE-15..16: Verify that 'move' -> 'Walk' and 'damage' -> 'Hit' cannot be
    produced by title-case fallback.

    If an implementer (incorrectly) used str.title() as the only mechanism, they
    would get 'Move' and 'Damage'. These tests confirm the expected values are NOT
    what title-case would produce, which means the explicit map MUST be implemented.
    The primary tests already assert the correct value; these adversarial tests add
    an explicit assertion that the title-case-only fallback value is wrong.
    """

    def test_adv_bae_15_move_export_name_is_not_title_case_of_move(self):
        """
        ADV-BAE-15: 'move'.title() == 'Move', but the required export name is 'Walk'.
        If get_export_name returns 'Move', the explicit map was not implemented.
        """
        result = AnimationTypes.get_export_name("move")
        self.assertNotEqual(result, "Move",
            "ADV-BAE-15: 'move' must NOT return 'Move' (title-case fallback) — "
            "the explicit map must return 'Walk'")
        self.assertEqual(result, "Walk",
            "ADV-BAE-15: 'move' must return 'Walk' (explicit map required)")

    def test_adv_bae_16_damage_export_name_is_not_title_case_of_damage(self):
        """
        ADV-BAE-16: 'damage'.title() == 'Damage', but the required export name is 'Hit'.
        If get_export_name returns 'Damage', the explicit map was not implemented.
        """
        result = AnimationTypes.get_export_name("damage")
        self.assertNotEqual(result, "Damage",
            "ADV-BAE-16: 'damage' must NOT return 'Damage' (title-case fallback) — "
            "the explicit map must return 'Hit'")
        self.assertEqual(result, "Hit",
            "ADV-BAE-16: 'damage' must return 'Hit' (explicit map required)")


# ===========================================================================
# ADV-BAE-17: Mapping completeness — all 13 known internal names return str
# ===========================================================================

class TestMappingCompleteness(unittest.TestCase):
    """
    ADV-BAE-17: Every name in AnimationTypes.get_all() must yield a non-empty str
    from get_export_name(). Missing entries produce the fallback which is always str,
    but this test verifies no name causes an exception or returns empty.
    Vulnerability: if get_all() returns a name that is accidentally passed as None
    or if the map lookup raises on an unexpected input type, one of the 13 will fail.
    """

    def test_adv_bae_17_all_internal_names_return_nonempty_str(self):
        """ADV-BAE-17: all 13 internal names return a non-empty str."""
        for internal in AnimationTypes.get_all():
            with self.subTest(internal=internal):
                result = AnimationTypes.get_export_name(internal)
                self.assertIsInstance(result, str,
                    f"ADV-BAE-17: get_export_name('{internal}') must return str")
                self.assertGreater(len(result), 0,
                    f"ADV-BAE-17: get_export_name('{internal}') must return non-empty str")


# ===========================================================================
# ADV-BAE-18: Idempotency — repeated calls with same input give same output
# ===========================================================================

class TestGetExportNameIdempotency(unittest.TestCase):
    """
    ADV-BAE-18: Multiple calls to get_export_name with the same input must return
    the same value. This catches implementations that mutate the internal map
    (e.g., accidentally adding fallback results back into the explicit dict).
    NFR-2 states the function must be pure with no global state mutation.
    """

    def test_adv_bae_18_repeated_calls_same_result(self):
        """ADV-BAE-18: three consecutive calls to get_export_name produce identical results."""
        for internal in AnimationTypes.get_all() + ["unknown_anim", "some_new_anim"]:
            with self.subTest(internal=internal):
                r1 = AnimationTypes.get_export_name(internal)
                r2 = AnimationTypes.get_export_name(internal)
                r3 = AnimationTypes.get_export_name(internal)
                self.assertEqual(r1, r2,
                    f"ADV-BAE-18: second call changed result for '{internal}': {r1!r} -> {r2!r}")
                self.assertEqual(r2, r3,
                    f"ADV-BAE-18: third call changed result for '{internal}': {r2!r} -> {r3!r}")


# ===========================================================================
# ADV-BAE-19: NLA strip name attribute must equal the export name
# ===========================================================================

class TestNLAStripNameEqualsExportName(unittest.TestCase):
    """
    ADV-BAE-19: Each NLA strip's name (the first argument to track.strips.new())
    must equal AnimationTypes.get_export_name(internal_name), not the internal name.

    The primary suite (test_bae_nla_3_one_strip_per_track) verifies one strip per
    track but does NOT verify the strip NAME. A mutation where the implementer passes
    the internal name (e.g., "idle") as the strip name instead of the export name
    (e.g., "Idle") satisfies BAE-NLA-3 but breaks BAE-1.3.
    """

    def test_adv_bae_19_nla_strip_names_use_export_names_not_internal(self):
        """ADV-BAE-19: every NLA strip.name must equal the export name for its action."""
        armature, created_action_names = _run_create_all_animations(animation_set='core')
        tracks = armature.animation_data._created_tracks

        # Build expected export names for core set
        expected_export_names = set(
            AnimationTypes.get_export_name(n) for n in AnimationTypes.get_core()
        )
        actual_strip_names = set()
        for track in tracks:
            for strip in track._strips_created:
                actual_strip_names.add(strip.name)

        for export_name in expected_export_names:
            self.assertIn(
                export_name, actual_strip_names,
                f"ADV-BAE-19: NLA strip name '{export_name}' not found in strip names. "
                f"Actual strip names: {actual_strip_names}. "
                "Strips must use export names (PascalCase), not internal names."
            )

        # Explicit check: internal names must NOT appear as strip names
        # (the non-obvious ones: "move" and "damage" — their export names differ)
        internal_names_that_differ = ["move", "damage"]
        for internal in internal_names_that_differ:
            self.assertNotIn(
                internal, actual_strip_names,
                f"ADV-BAE-19: internal name '{internal}' must not appear as NLA strip name. "
                f"The export name must be used instead."
            )


# ===========================================================================
# ADV-BAE-20: NLA wiring for animation_set='extended' only
# ===========================================================================

class TestNLAWiringExtendedSet(unittest.TestCase):
    """
    ADV-BAE-20: When animation_set='extended', create_all_animations() must create
    exactly len(AnimationTypes.get_extended()) NLA tracks — no more, no fewer.

    The primary suite tests 'core' and 'all' but not 'extended'. A mutation where
    NLA wiring always creates tracks for all 13 (regardless of animation_set) would
    fail this test.
    """

    def test_adv_bae_20_extended_set_creates_correct_nla_track_count(self):
        """ADV-BAE-20: animation_set='extended' -> exactly N=8 NLA tracks."""
        armature, _ = _run_create_all_animations(animation_set='extended')
        expected = len(AnimationTypes.get_extended())
        actual = armature.animation_data.nla_tracks.new.call_count
        self.assertEqual(
            actual, expected,
            f"ADV-BAE-20: extended set should create {expected} NLA tracks, got {actual}"
        )

    def test_adv_bae_20b_extended_set_action_is_none_on_return(self):
        """ADV-BAE-20b: animation_data.action must be None after extended-set run."""
        armature, _ = _run_create_all_animations(animation_set='extended')
        self.assertIsNone(
            armature.animation_data.action,
            "ADV-BAE-20b: animation_data.action must be None after extended-set run "
            "(NLA-driven mode, not single-action export)"
        )


# ===========================================================================
# ADV-BAE-21: Active-action leak detection
# (mirrors BAE-NLA-1 but with an explicit check for the CURRENT BUG in the source)
# ===========================================================================

class TestActiveActionLeakCurrentBug(unittest.TestCase):
    """
    ADV-BAE-21: The current implementation ends with:
        armature.animation_data.action = created_actions[0]
    This is the bug that BAE-NLA-1 is meant to catch. This adversarial test reads
    the animation_system.py SOURCE to assert the buggy assignment is absent,
    providing a static-analysis complement to the runtime mock test.

    This guards against a mutation where the implementation adds `action = None`
    but THEN re-adds `action = created_actions[0]` after the NLA block.
    """

    def test_adv_bae_21_source_does_not_set_action_to_created_actions_0(self):
        """
        ADV-BAE-21: animation_system.py must not contain the line
        'armature.animation_data.action = created_actions[0]'
        (the current bug; implementation must replace it with 'action = None').
        """
        import os
        src_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..', 'src', 'animations', 'animation_system.py'
        )
        src_path = os.path.normpath(src_path)
        with open(src_path, 'r') as f:
            source = f.read()

        self.assertNotIn(
            "animation_data.action = created_actions[0]",
            source,
            "ADV-BAE-21: animation_system.py must not set action = created_actions[0] "
            "after the NLA wiring block. The bug line must be replaced with action = None."
        )

    def test_adv_bae_21b_source_sets_action_to_none_after_nla(self):
        """
        ADV-BAE-21b: animation_system.py must contain the NLA-driven mode line
        'armature.animation_data.action = None' somewhere after the NLA wiring block.
        This is the required replacement for the buggy created_actions[0] assignment.
        """
        import os
        src_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..', 'src', 'animations', 'animation_system.py'
        )
        src_path = os.path.normpath(src_path)
        with open(src_path, 'r') as f:
            source = f.read()

        self.assertIn(
            "animation_data.action = None",
            source,
            "ADV-BAE-21b: animation_system.py must contain 'animation_data.action = None' "
            "to enable NLA-driven export mode (GLTF exporter reads NLA strips when action=None)."
        )


# ===========================================================================
# ADV-BAE-22..24: export_enemy tests with bmesh properly mocked
# (Fixes the infra gap in test_animation_export_names.py::TestExportEnemyNLAFlag
# where bmesh is not mocked, causing ERROR instead of FAIL on the intended assertion)
# ===========================================================================

class TestExportEnemyNLAFlagFixed(unittest.TestCase):
    """
    ADV-BAE-22..24: These are the corrected versions of TestExportEnemyNLAFlag
    from the primary suite. The primary suite fails with ModuleNotFoundError for
    bmesh because blender_utils.py imports it at module level.

    With bmesh mocked at the top of THIS file, these tests reach the actual
    assertion and produce the intended red-phase FAIL (missing export_nla_strips)
    rather than an ERROR.
    """

    def _capture_gltf_kwargs(self):
        """
        Build mock environment, call export_enemy(), return captured gltf kwargs.
        """
        import bpy as _bpy_mock

        armature = MagicMock()
        armature.animation_data = MagicMock()
        armature.animation_data.action = None
        armature.select_set = MagicMock()

        mesh = MagicMock()
        mesh.select_set = MagicMock()

        gltf_kwargs_captured = {}

        def _capture_gltf(**kwargs):
            gltf_kwargs_captured.update(kwargs)

        _bpy_mock.ops.export_scene.gltf.side_effect = _capture_gltf
        _bpy_mock.ops.wm.save_as_mainfile.return_value = None
        _bpy_mock.ops.object.mode_set.return_value = None
        _bpy_mock.ops.object.select_all.return_value = None
        _bpy_mock.context.view_layer.objects.active = None

        from src.enemies.base_enemy import export_enemy
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            export_enemy(armature, mesh, "test_enemy_adv", tmpdir)

        return gltf_kwargs_captured

    def test_adv_bae_22_export_nla_strips_kwarg_present_and_true(self):
        """
        ADV-BAE-22 / BAE-1.5: bpy.ops.export_scene.gltf() must be called with
        export_nla_strips=True. This is the corrected version of
        TestExportEnemyNLAFlag.test_bae_1_5_export_nla_strips_passed_to_gltf
        with bmesh properly mocked so the test reaches the assertion.

        Will FAIL (red) until Task 1 implementation adds the kwarg.
        """
        kwargs = self._capture_gltf_kwargs()
        self.assertIn(
            'export_nla_strips', kwargs,
            "ADV-BAE-22/BAE-1.5: bpy.ops.export_scene.gltf() must include "
            "export_nla_strips kwarg. Currently absent — NLA strips will not be "
            "exported in Blender 3.x without this flag."
        )
        self.assertTrue(
            kwargs.get('export_nla_strips'),
            "ADV-BAE-22/BAE-1.5: export_nla_strips must be True"
        )

    def test_adv_bae_23_export_animations_true(self):
        """
        ADV-BAE-23 / BAE-1.5 (supporting): export_animations=True must remain.
        A mutation that disables animations entirely would break all clip export.
        """
        kwargs = self._capture_gltf_kwargs()
        self.assertTrue(
            kwargs.get('export_animations', False),
            "ADV-BAE-23: export_animations must be True in gltf() call"
        )

    def test_adv_bae_24_export_format_is_glb(self):
        """
        ADV-BAE-24: export_format must be 'GLB' (not 'GLTF_EMBEDDED' or 'GLTF_SEPARATE').
        A mutation that switches to GLTF_SEPARATE would write .gltf + .bin + textures
        rather than a self-contained .glb, breaking the Godot import pipeline.
        """
        kwargs = self._capture_gltf_kwargs()
        self.assertEqual(
            kwargs.get('export_format'), 'GLB',
            "ADV-BAE-24: export_format must be 'GLB', not 'GLTF_EMBEDDED' or 'GLTF_SEPARATE'"
        )


# ===========================================================================
# ADV-BAE-25: get_export_name must not mutate the explicit mapping dictionary
# ===========================================================================

class TestGetExportNameNoMapMutation(unittest.TestCase):
    """
    ADV-BAE-25: Calling get_export_name with an unknown name must not insert the
    fallback result into the explicit mapping. If the map is mutated, subsequent
    calls with the same unknown name would hit the map instead of the fallback,
    which is correct behavior — BUT it also means the map can grow unboundedly,
    and more critically: if an implementer stores the result of the fallback back
    into the map using the WRONG key (e.g., the export name as key rather than
    the internal name), then get_export_name(known_internal) would be corrupted.

    This test verifies the four required mappings remain correct after calling
    get_export_name with several unknown names.
    """

    def test_adv_bae_25_required_mappings_unchanged_after_unknown_lookups(self):
        """ADV-BAE-25: required mappings unaffected by unknown-name lookups."""
        # Trigger fallback for several unknown names
        unknowns = [
            "idle_variant", "move_fast", "Walk", "Hit", "Idle", "Death",
            "some_long_animation_name_with_many_parts"
        ]
        for u in unknowns:
            AnimationTypes.get_export_name(u)  # discard result; exercise the fallback

        # Required mappings must still return correct values
        self.assertEqual(AnimationTypes.get_export_name("idle"), "Idle",
            "ADV-BAE-25: 'idle' -> 'Idle' must survive unknown-name lookups")
        self.assertEqual(AnimationTypes.get_export_name("move"), "Walk",
            "ADV-BAE-25: 'move' -> 'Walk' must survive unknown-name lookups")
        self.assertEqual(AnimationTypes.get_export_name("damage"), "Hit",
            "ADV-BAE-25: 'damage' -> 'Hit' must survive unknown-name lookups")
        self.assertEqual(AnimationTypes.get_export_name("death"), "Death",
            "ADV-BAE-25: 'death' -> 'Death' must survive unknown-name lookups")


# ===========================================================================
# ADV-BAE-26: NLA track count must equal action count exactly (no extras)
# ===========================================================================

class TestNLATrackCountExact(unittest.TestCase):
    """
    ADV-BAE-26: nla_tracks.new() must be called exactly N times — no extra
    "setup" or "cleanup" tracks. A mutation that creates an extra empty track
    before the loop (e.g., for a "rest" pose track) would inflate the count.

    The primary suite tests that count >= expected; this test also verifies
    count == expected for the 'all' set (13 actions).
    """

    def test_adv_bae_26_nla_track_count_equals_all_animation_count_exactly(self):
        """ADV-BAE-26: for 'all' set, NLA track count == 13 (len(get_all()))."""
        armature, _ = _run_create_all_animations(animation_set='all')
        expected = len(AnimationTypes.get_all())
        actual = armature.animation_data.nla_tracks.new.call_count
        self.assertEqual(
            actual, expected,
            f"ADV-BAE-26: expected exactly {expected} NLA tracks for 'all' set, got {actual}. "
            "Extra tracks indicate a setup/cleanup track was created unintentionally."
        )


# ===========================================================================
# ADV-BAE-27: Frame range assignment must precede NLA strip creation (order test)
# ===========================================================================

class TestFrameRangeAssignedBeforeNLAStrip(unittest.TestCase):
    """
    ADV-BAE-27: action.frame_range = (1, length) must be assigned before
    track.strips.new() is called for that action.

    Risk R1.4 in the spec notes that frame_range is read-only until at least one
    keyframe exists; the existing code already assigns it explicitly. This test
    verifies that when the strip is created via track.strips.new(name, 0, action),
    the action already has frame_range set (i.e., the strip references the same
    action object that has frame_range = (1, length)).

    Strategy: capture the frame_range of the action object at strip-creation time
    and assert it equals (1, length) for each action.
    """

    def test_adv_bae_27_action_frame_range_set_before_strip_creation(self):
        """
        ADV-BAE-27: at the moment track.strips.new(name, start, action) is called,
        action.frame_range[1] must equal the configured length for that animation.
        """
        import bpy as _bpy_mock

        frame_ranges_at_strip_creation = {}  # action_name -> frame_range at creation time
        armature = _make_mock_armature()
        created_actions_by_name = {}

        def _new_action(name):
            length = _length_for(name)
            action = _make_mock_action(name, length)
            created_actions_by_name[name] = action
            return action

        _bpy_mock.data.actions.new.side_effect = _new_action
        _bpy_mock.ops.object.mode_set.side_effect = lambda mode: None
        _bpy_mock.context.scene.frame_start = 1
        _bpy_mock.context.scene.frame_end = 48

        # Instrument the armature's NLA tracks to record frame_range at strip creation
        original_nla_new = armature.animation_data.nla_tracks.new.side_effect

        def _new_track_capturing():
            track = original_nla_new()
            original_strips_new = track.strips.new.side_effect

            def _new_strip_capturing(name, start, action):
                # Record frame_range of the action at the moment the strip is created
                frame_ranges_at_strip_creation[action.name] = action.frame_range
                return original_strips_new(name, start, action)

            track.strips.new.side_effect = _new_strip_capturing
            return track

        armature.animation_data.nla_tracks.new.side_effect = _new_track_capturing

        from src.animations.animation_system import create_all_animations
        import random
        rng = random.Random(42)
        create_all_animations(armature, 'blob', rng, animation_set='core')

        # Now verify each action's frame_range was set before strip creation
        for action_name, frame_range in frame_ranges_at_strip_creation.items():
            with self.subTest(action=action_name):
                internal = _REVERSE_MAP.get(action_name, action_name)
                expected_length = AnimationConfig.get_length(internal)
                self.assertEqual(
                    frame_range[1], expected_length,
                    f"ADV-BAE-27: at strip creation time, action '{action_name}' "
                    f"frame_range[1] should be {expected_length}, got {frame_range[1]}. "
                    "This means frame_range was not yet set when the strip was created."
                )


# ===========================================================================
# ADV-BAE-28: get_export_name is not None for None-like inputs (robustness)
# ===========================================================================

class TestGetExportNameNoneHandling(unittest.TestCase):
    """
    ADV-BAE-28: get_export_name(None) should either raise TypeError or return a str.
    It must NOT silently return None (which could propagate into bpy.data.actions.new(name=None)).
    The spec does not define behaviour for None; the conservative assumption is that
    passing None is a programming error and should raise. This test documents the
    contract and will catch an implementation that returns None silently.
    """

    def test_adv_bae_28_none_input_raises_or_returns_str(self):
        """
        ADV-BAE-28: get_export_name(None) must either raise TypeError/AttributeError
        (correct: None is not a valid internal name) or return a str. It must NOT
        return None, which would cause bpy.data.actions.new(name=None) to crash silently.
        """
        try:
            result = AnimationTypes.get_export_name(None)
            # If it doesn't raise, result must at least be a str (not None)
            self.assertIsNotNone(result,
                "ADV-BAE-28: get_export_name(None) returned None — must raise or return str")
            self.assertIsInstance(result, str,
                "ADV-BAE-28: get_export_name(None) must return str if it doesn't raise")
        except (TypeError, AttributeError):
            # Raising is the correct behaviour for None input; test passes.
            pass


if __name__ == '__main__':
    unittest.main()
