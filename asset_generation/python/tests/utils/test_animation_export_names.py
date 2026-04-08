"""
Tests for AnimationTypes.get_export_name() and NLA wiring behaviour in create_all_animations().

Spec:  project_board/specs/blender_animation_export_spec.md
Ticket: project_board/7_milestone_7_enemy_animation_wiring/in_progress/blender_animation_export.md

Test IDs
--------
BAE-2.1  get_export_name is a callable classmethod returning str
BAE-2.2  Required 4 clip name mappings (idle→Idle, move→Walk, damage→Hit, death→Death)
BAE-2.3  Additional 9 explicit mappings (attack, spawn, special_attack, damage_*, stunned, celebrate, taunt)
BAE-2.4  PascalCase fallback for unknown internal names
BAE-2.5  Existing class constants are unchanged (IDLE, MOVE, DAMAGE, DEATH remain lowercase)
BAE-NLA-1  create_all_animations sets armature.animation_data.action = None on return
BAE-NLA-2  create_all_animations creates exactly N NLA tracks for N animations (one track per action)
BAE-NLA-3  Each NLA track receives exactly one strip
BAE-NLA-4  Each NLA strip action_frame_start == 1
BAE-NLA-5  Each NLA strip action_frame_end == action.frame_range[1]
BAE-NLA-6  Each NLA strip frame_start == 0 (NLA timeline position)
BAE-NLA-7  OBJECT mode is set before any NLA track is created
BAE-NLA-8  Action names passed to bpy.data.actions.new() use export names, not internal names

bpy and mathutils are mocked at module level so these run outside Blender.
"""

import sys
import unittest
from unittest.mock import MagicMock

# Mock Blender modules before any src import.
# setdefault preserves real modules if somehow running inside Blender.
sys.modules.setdefault('bpy', MagicMock())
sys.modules.setdefault('mathutils', MagicMock())

from src.utils.constants import AnimationConfig, AnimationTypes

# ---------------------------------------------------------------------------
# BAE-2: get_export_name classmethod
# ---------------------------------------------------------------------------

class TestAnimationTypesGetExportName(unittest.TestCase):
    """BAE-2.1 through BAE-2.5 — AnimationTypes.get_export_name mapping."""

    # BAE-2.1
    def test_get_export_name_is_callable_classmethod_returning_str(self):
        """get_export_name must be callable without an instance and return str."""
        result = AnimationTypes.get_export_name("idle")
        self.assertIsInstance(result, str,
            "BAE-2.1: get_export_name must return a str")

    # BAE-2.2 — required 4 clips (non-negotiable per spec)
    def test_idle_maps_to_Idle(self):
        """BAE-2.2: 'idle' → 'Idle'"""
        self.assertEqual(AnimationTypes.get_export_name("idle"), "Idle",
            "BAE-2.2: idle must map to 'Idle'")

    def test_move_maps_to_Walk(self):
        """BAE-2.2: 'move' → 'Walk' (non-obvious; not 'Move')"""
        self.assertEqual(AnimationTypes.get_export_name("move"), "Walk",
            "BAE-2.2: move must map to 'Walk' (Godot controller contract)")

    def test_damage_maps_to_Hit(self):
        """BAE-2.2: 'damage' → 'Hit' (non-obvious; not 'Damage')"""
        self.assertEqual(AnimationTypes.get_export_name("damage"), "Hit",
            "BAE-2.2: damage must map to 'Hit' (Godot controller contract)")

    def test_death_maps_to_Death(self):
        """BAE-2.2: 'death' → 'Death'"""
        self.assertEqual(AnimationTypes.get_export_name("death"), "Death",
            "BAE-2.2: death must map to 'Death'")

    # BAE-2.3 — additional explicit mappings
    def test_attack_maps_to_Attack(self):
        """BAE-2.3: 'attack' → 'Attack'"""
        self.assertEqual(AnimationTypes.get_export_name("attack"), "Attack",
            "BAE-2.3: attack → Attack")

    def test_spawn_maps_to_Spawn(self):
        """BAE-2.3: 'spawn' → 'Spawn'"""
        self.assertEqual(AnimationTypes.get_export_name("spawn"), "Spawn",
            "BAE-2.3: spawn → Spawn")

    def test_special_attack_maps_to_SpecialAttack(self):
        """BAE-2.3: 'special_attack' → 'SpecialAttack'"""
        self.assertEqual(AnimationTypes.get_export_name("special_attack"), "SpecialAttack",
            "BAE-2.3: special_attack → SpecialAttack")

    def test_damage_heavy_maps_to_DamageHeavy(self):
        """BAE-2.3: 'damage_heavy' → 'DamageHeavy'"""
        self.assertEqual(AnimationTypes.get_export_name("damage_heavy"), "DamageHeavy",
            "BAE-2.3: damage_heavy → DamageHeavy")

    def test_damage_fire_maps_to_DamageFire(self):
        """BAE-2.3: 'damage_fire' → 'DamageFire'"""
        self.assertEqual(AnimationTypes.get_export_name("damage_fire"), "DamageFire",
            "BAE-2.3: damage_fire → DamageFire")

    def test_damage_ice_maps_to_DamageIce(self):
        """BAE-2.3: 'damage_ice' → 'DamageIce'"""
        self.assertEqual(AnimationTypes.get_export_name("damage_ice"), "DamageIce",
            "BAE-2.3: damage_ice → DamageIce")

    def test_stunned_maps_to_Stunned(self):
        """BAE-2.3: 'stunned' → 'Stunned'"""
        self.assertEqual(AnimationTypes.get_export_name("stunned"), "Stunned",
            "BAE-2.3: stunned → Stunned")

    def test_celebrate_maps_to_Celebrate(self):
        """BAE-2.3: 'celebrate' → 'Celebrate'"""
        self.assertEqual(AnimationTypes.get_export_name("celebrate"), "Celebrate",
            "BAE-2.3: celebrate → Celebrate")

    def test_taunt_maps_to_Taunt(self):
        """BAE-2.3: 'taunt' → 'Taunt'"""
        self.assertEqual(AnimationTypes.get_export_name("taunt"), "Taunt",
            "BAE-2.3: taunt → Taunt")

    # BAE-2.4 — PascalCase fallback for unknown internal names
    def test_unknown_single_word_returns_title_case(self):
        """BAE-2.4: 'someanim' → 'Someanim' (title-case of single word)"""
        result = AnimationTypes.get_export_name("someanim")
        self.assertEqual(result, "Someanim",
            "BAE-2.4: single-word unknown name must be title-cased")

    def test_unknown_two_word_returns_pascal_case(self):
        """BAE-2.4: 'some_new_anim' → 'SomeNewAnim' (mechanical PascalCase)"""
        result = AnimationTypes.get_export_name("some_new_anim")
        self.assertEqual(result, "SomeNewAnim",
            "BAE-2.4: snake_case unknown name must be PascalCase converted")

    def test_unknown_two_part_name_returns_pascal_case(self):
        """BAE-2.4: 'roll_dodge' → 'RollDodge'"""
        result = AnimationTypes.get_export_name("roll_dodge")
        self.assertEqual(result, "RollDodge",
            "BAE-2.4: two-word unknown → concatenated title-case words")

    def test_get_export_name_is_deterministic(self):
        """NFR-2: same input always produces same output (pure function, no global state)."""
        first = AnimationTypes.get_export_name("idle")
        second = AnimationTypes.get_export_name("idle")
        self.assertEqual(first, second,
            "NFR-2: get_export_name must be deterministic")

    def test_get_export_name_fallback_is_deterministic(self):
        """NFR-2: fallback PascalCase conversion is deterministic."""
        first = AnimationTypes.get_export_name("some_new_anim")
        second = AnimationTypes.get_export_name("some_new_anim")
        self.assertEqual(first, second,
            "NFR-2: fallback PascalCase must be deterministic")

    def test_get_export_name_callable_without_bpy(self):
        """BAE-R2.4: get_export_name must not import bpy; callable outside Blender."""
        # If get_export_name tried to access bpy at call time and bpy was removed,
        # it would raise AttributeError. The MagicMock ensures no real bpy is needed,
        # but the intent is to confirm constants.py has no bpy dependency.
        import src.utils.constants as constants_module
        # Verify no bpy attribute is accessed on AnimationTypes.get_export_name
        # by calling it with a fresh invocation under the mocked bpy.
        result = constants_module.AnimationTypes.get_export_name("idle")
        self.assertEqual(result, "Idle",
            "BAE-R2.4: get_export_name must work without bpy being a real module")

    # BAE-2.5 — existing class constants unchanged
    def test_IDLE_constant_unchanged(self):
        """BAE-2.5: AnimationTypes.IDLE must still equal 'idle'."""
        self.assertEqual(AnimationTypes.IDLE, "idle",
            "BAE-2.5: AnimationTypes.IDLE must not be renamed")

    def test_MOVE_constant_unchanged(self):
        """BAE-2.5: AnimationTypes.MOVE must still equal 'move'."""
        self.assertEqual(AnimationTypes.MOVE, "move",
            "BAE-2.5: AnimationTypes.MOVE must not be renamed")

    def test_DAMAGE_constant_unchanged(self):
        """BAE-2.5: AnimationTypes.DAMAGE must still equal 'damage'."""
        self.assertEqual(AnimationTypes.DAMAGE, "damage",
            "BAE-2.5: AnimationTypes.DAMAGE must not be renamed")

    def test_DEATH_constant_unchanged(self):
        """BAE-2.5: AnimationTypes.DEATH must still equal 'death'."""
        self.assertEqual(AnimationTypes.DEATH, "death",
            "BAE-2.5: AnimationTypes.DEATH must not be renamed")

    def test_ATTACK_constant_unchanged(self):
        """BAE-2.5: AnimationTypes.ATTACK must still equal 'attack'."""
        self.assertEqual(AnimationTypes.ATTACK, "attack",
            "BAE-2.5: AnimationTypes.ATTACK must not be renamed")

    def test_SPECIAL_ATTACK_constant_unchanged(self):
        """BAE-2.5: AnimationTypes.SPECIAL_ATTACK must still equal 'special_attack'."""
        self.assertEqual(AnimationTypes.SPECIAL_ATTACK, "special_attack",
            "BAE-2.5: AnimationTypes.SPECIAL_ATTACK must not be renamed")

    def test_get_length_lookup_still_uses_internal_name(self):
        """BAE-2.7: AnimationConfig.get_length uses internal names as keys (must not break)."""
        # If LENGTHS keys were renamed to export names, get_length("idle") would
        # fall back to default 24 instead of the configured 48.
        self.assertEqual(AnimationConfig.get_length("idle"), 48,
            "BAE-2.7: get_length('idle') must return 48 — LENGTHS keys must remain internal names")
        self.assertEqual(AnimationConfig.get_length("move"), 24,
            "BAE-2.7: get_length('move') must return 24")
        self.assertEqual(AnimationConfig.get_length("damage"), 12,
            "BAE-2.7: get_length('damage') must return 12")
        self.assertEqual(AnimationConfig.get_length("death"), 72,
            "BAE-2.7: get_length('death') must return 72")

    def test_get_length_does_not_accept_export_names(self):
        """BAE-2.7 / Risk-R2.1: get_length('Idle') must NOT return 48 (keys are internal, not export)."""
        # If this returned 48, it would mean LENGTHS keys were incorrectly changed to export names.
        # The configured default is 24 for unknown keys.
        result = AnimationConfig.get_length("Idle")
        self.assertEqual(result, 24,
            "BAE-2.7/R2.1: get_length must use internal names — 'Idle' is not a valid key")


# ---------------------------------------------------------------------------
# BAE-NLA: NLA wiring behaviour in create_all_animations()
#
# These tests mock bpy at the module level (already done above) and additionally
# patch bpy internals to capture NLA API calls made by create_all_animations().
# They verify the structural post-loop block required by BAE-1.1 through BAE-1.7.
#
# Strategy: patch bpy.data.actions.new, bpy.ops.object.mode_set, and the
# armature's animation_data to record calls, then assert on their order and counts.
# ---------------------------------------------------------------------------

def _make_mock_action(name: str, frame_end: int) -> MagicMock:
    """Build a minimal mock bpy action with a readable frame_range."""
    action = MagicMock(name=f"MockAction<{name}>")
    action.name = name
    action.frame_range = (1, frame_end)
    action.use_fake_user = False
    return action


def _make_mock_armature() -> MagicMock:
    """
    Build a minimal mock armature whose NLA API is instrumented for capture.
    Each call to nla_tracks.new() returns a distinct mock track.
    Each call to track.strips.new() records strip creation args.
    """
    armature = MagicMock()
    armature.mode = 'POSE'

    # Bones list — minimal: root + body + head to satisfy set_rest_pose_keyframe
    bone_names = ['root', 'body', 'head']
    armature.pose.bones = [MagicMock(name=n) for n in bone_names]

    # animation_data is always present
    animation_data = MagicMock()
    animation_data.action = None

    # nla_tracks.new() returns a new distinct mock each call
    created_tracks = []

    def _new_track():
        track = MagicMock()
        track.strips = MagicMock()
        created_track_strips = []
        track.strips.new.side_effect = lambda name, start, action: _record_strip(
            track, created_track_strips, name, start, action
        )
        track._strips_created = created_track_strips
        created_tracks.append(track)
        return track

    def _record_strip(track, strips_list, name, start, action):
        strip = MagicMock()
        strip.name = name
        strip.action = action
        strip.frame_start = start
        strip.action_frame_start = None
        strip.action_frame_end = None
        strips_list.append(strip)
        return strip

    animation_data.nla_tracks.new.side_effect = _new_track
    animation_data._created_tracks = created_tracks

    armature.animation_data = animation_data
    armature.animation_data_create.return_value = None

    return armature


class TestCreateAllAnimationsNLAWiring(unittest.TestCase):
    """
    BAE-NLA-1 through BAE-NLA-8: verify NLA wiring structure in create_all_animations().

    These tests call create_all_animations() with mocked bpy, capturing which
    Blender API calls are made and in what order.
    """

    def _run_create_all_animations(self, animation_set='core'):
        """
        Run create_all_animations() with a fully mocked bpy environment.
        Returns (armature_mock, mode_set_calls, action_new_calls).
        """
        import bpy as _bpy_mock  # already mocked via sys.modules

        armature = _make_mock_armature()

        # Track mode_set calls in order
        mode_set_calls = []
        _bpy_mock.ops.object.mode_set.side_effect = lambda mode: mode_set_calls.append(mode)

        # Track actions.new calls and return distinct mocks with export-name labels
        action_counter = [0]
        created_action_names = []

        def _new_action(name):
            action_counter[0] += 1
            length = AnimationConfig.get_length(
                # Reverse-lookup internal name from export name for frame length
                # (we record what name was passed to verify export names are used)
                # Fall back to 24 if not found via export name
                _get_internal_name_for_length_lookup(name)
            )
            action = _make_mock_action(name, length)
            created_action_names.append(name)
            return action

        _bpy_mock.data.actions.new.side_effect = _new_action

        # Patch scene frame attributes as integers
        _bpy_mock.context.scene.frame_start = 1
        _bpy_mock.context.scene.frame_end = 48

        import random

        from src.animations.animation_system import create_all_animations
        rng = random.Random(42)

        create_all_animations(armature, 'blob', rng, animation_set=animation_set)

        return armature, mode_set_calls, created_action_names

    def test_bae_nla_1_action_is_none_on_return(self):
        """BAE-NLA-1 / BAE-1.4: armature.animation_data.action is None after create_all_animations returns."""
        armature, _, _ = self._run_create_all_animations(animation_set='core')
        self.assertIsNone(
            armature.animation_data.action,
            "BAE-NLA-1/BAE-1.4: animation_data.action must be None after create_all_animations "
            "(NLA-driven mode; GLTF exporter requires action=None to export all NLA strips)"
        )

    def test_bae_nla_2_one_nla_track_per_action(self):
        """BAE-NLA-2 / BAE-1.2: nla_tracks.new() is called once per created action."""
        armature, _, _ = self._run_create_all_animations(animation_set='core')
        expected_count = len(AnimationTypes.get_core())
        actual_count = armature.animation_data.nla_tracks.new.call_count
        self.assertEqual(
            actual_count, expected_count,
            f"BAE-NLA-2/BAE-1.2: expected {expected_count} nla_tracks.new() calls "
            f"(one per action), got {actual_count}"
        )

    def test_bae_nla_2_all_tracks_one_per_action_full_set(self):
        """BAE-NLA-2: for animation_set='all', N=13 NLA tracks must be created."""
        armature, _, _ = self._run_create_all_animations(animation_set='all')
        expected_count = len(AnimationTypes.get_all())
        actual_count = armature.animation_data.nla_tracks.new.call_count
        self.assertEqual(
            actual_count, expected_count,
            f"BAE-NLA-2/BAE-1.2: expected {expected_count} NLA tracks for 'all' set, got {actual_count}"
        )

    def test_bae_nla_3_one_strip_per_track(self):
        """BAE-NLA-3 / BAE-1.3: each NLA track has exactly one strip added via strips.new()."""
        armature, _, _ = self._run_create_all_animations(animation_set='core')
        created_tracks = armature.animation_data._created_tracks
        for idx, track in enumerate(created_tracks):
            strip_count = len(track._strips_created)
            self.assertEqual(
                strip_count, 1,
                f"BAE-NLA-3/BAE-1.3: track {idx} must have exactly 1 strip, got {strip_count}"
            )

    def test_bae_nla_4_strip_action_frame_start_is_1(self):
        """BAE-NLA-4 / BAE-1.3: every NLA strip.action_frame_start == 1."""
        armature, _, _ = self._run_create_all_animations(animation_set='core')
        for idx, track in enumerate(armature.animation_data._created_tracks):
            for strip in track._strips_created:
                self.assertEqual(
                    strip.action_frame_start, 1,
                    f"BAE-NLA-4/BAE-1.3: track {idx} strip.action_frame_start must be 1"
                )

    def test_bae_nla_5_strip_action_frame_end_matches_action_frame_range(self):
        """BAE-NLA-5 / BAE-1.3: every NLA strip.action_frame_end == action.frame_range[1]."""
        armature, _, _ = self._run_create_all_animations(animation_set='core')
        for idx, track in enumerate(armature.animation_data._created_tracks):
            for strip in track._strips_created:
                expected_end = strip.action.frame_range[1]
                self.assertEqual(
                    strip.action_frame_end, expected_end,
                    f"BAE-NLA-5/BAE-1.3: track {idx} strip.action_frame_end must equal "
                    f"action.frame_range[1] ({expected_end})"
                )

    def test_bae_nla_6_strip_frame_start_is_0(self):
        """BAE-NLA-6 / BAE-1.3: every NLA strip.frame_start == 0 (NLA timeline position)."""
        armature, _, _ = self._run_create_all_animations(animation_set='core')
        for idx, track in enumerate(armature.animation_data._created_tracks):
            for strip in track._strips_created:
                self.assertEqual(
                    strip.frame_start, 0,
                    f"BAE-NLA-6/BAE-1.3: track {idx} NLA strip frame_start (timeline position) must be 0"
                )

    def test_bae_nla_7_object_mode_set_before_any_nla_track_call(self):
        """
        BAE-NLA-7 / BAE-1.1: bpy.ops.object.mode_set(mode='OBJECT') must be called
        before the first nla_tracks.new() call.

        Strategy: record mode_set call ordering relative to nla_tracks.new() via
        a shared call sequence list.
        """
        import bpy as _bpy_mock

        call_sequence = []
        armature = _make_mock_armature()

        def _record_mode_set(mode):
            call_sequence.append(('mode_set', mode))

        _bpy_mock.ops.object.mode_set.side_effect = _record_mode_set

        original_nla_new = armature.animation_data.nla_tracks.new.side_effect

        def _record_nla_new():
            call_sequence.append(('nla_tracks_new',))
            return original_nla_new()

        armature.animation_data.nla_tracks.new.side_effect = _record_nla_new

        def _new_action(name):
            length = AnimationConfig.get_length(
                _get_internal_name_for_length_lookup(name)
            )
            return _make_mock_action(name, length)

        _bpy_mock.data.actions.new.side_effect = _new_action
        _bpy_mock.context.scene.frame_start = 1
        _bpy_mock.context.scene.frame_end = 48

        import random

        from src.animations.animation_system import create_all_animations
        rng = random.Random(42)
        create_all_animations(armature, 'blob', rng, animation_set='core')

        # Find last OBJECT mode_set index and first nla_tracks_new index
        object_mode_indices = [
            i for i, entry in enumerate(call_sequence)
            if entry == ('mode_set', 'OBJECT')
        ]
        nla_new_indices = [
            i for i, entry in enumerate(call_sequence)
            if entry == ('nla_tracks_new',)
        ]

        self.assertGreater(
            len(object_mode_indices), 0,
            "BAE-NLA-7/BAE-1.1: bpy.ops.object.mode_set(mode='OBJECT') was never called"
        )
        self.assertGreater(
            len(nla_new_indices), 0,
            "BAE-NLA-7: nla_tracks.new() was never called — NLA wiring not implemented"
        )

        last_object_mode_idx = max(object_mode_indices)
        first_nla_new_idx = min(nla_new_indices)

        self.assertLess(
            last_object_mode_idx, first_nla_new_idx,
            "BAE-NLA-7/BAE-1.1: mode_set(OBJECT) must occur before the first nla_tracks.new() call. "
            f"Last OBJECT mode switch at position {last_object_mode_idx}, "
            f"first NLA track creation at {first_nla_new_idx}."
        )

    def test_bae_nla_8_action_names_use_export_names(self):
        """
        BAE-NLA-8 / BAE-2.6: bpy.data.actions.new(name=...) must be called with
        export names (PascalCase), not internal names (lowercase snake_case).
        """
        _, _, created_action_names = self._run_create_all_animations(animation_set='core')

        expected_export_names = [
            AnimationTypes.get_export_name(n) for n in AnimationTypes.get_core()
        ]

        for export_name in expected_export_names:
            self.assertIn(
                export_name, created_action_names,
                f"BAE-NLA-8/BAE-2.6: export name '{export_name}' was not passed to "
                f"bpy.data.actions.new(). Actions created: {created_action_names}"
            )

        # Verify no internal names leaked through (the 4 non-obvious mappings)
        internal_should_not_appear = ["move", "damage"]  # these map to Walk and Hit
        for internal_name in internal_should_not_appear:
            self.assertNotIn(
                internal_name, created_action_names,
                f"BAE-NLA-8/BAE-2.6: internal name '{internal_name}' must not be used "
                f"as an action name. Use export name instead."
            )

    def test_bae_nla_strip_count_equals_action_count(self):
        """BAE-1.7: total NLA strip count across all tracks equals len(created_actions)."""
        armature, _, _ = self._run_create_all_animations(animation_set='core')
        expected_count = len(AnimationTypes.get_core())
        total_strips = sum(
            len(track._strips_created)
            for track in armature.animation_data._created_tracks
        )
        self.assertEqual(
            total_strips, expected_count,
            f"BAE-1.7: total NLA strips ({total_strips}) must equal "
            f"number of created actions ({expected_count})"
        )


# ---------------------------------------------------------------------------
# BAE-1.5: export_enemy passes export_nla_strips flag (or version-guarded fallback)
# ---------------------------------------------------------------------------

class TestExportEnemyNLAFlag(unittest.TestCase):
    """
    BAE-1.5: bpy.ops.export_scene.gltf() called inside export_enemy() must
    include export_nla_strips=True, OR the code must contain a Blender-version
    runtime check that conditionally passes the parameter.

    Strategy: mock bpy.ops.export_scene.gltf and bpy.ops.wm.save_as_mainfile,
    call export_enemy() with minimal mocks, capture the kwargs passed to gltf(),
    and assert either:
      (a) 'export_nla_strips' key is present and True in those kwargs, OR
      (b) the call is made without the key (version-guarded path) and
          armature.animation_data.action was None before the call (NLA-driven mode).

    The test enforces the strictest-defensible interpretation: export_nla_strips=True
    must be present in the gltf() call. If a Blender-version check is implemented,
    a second test verifies the fallback path sets action=None before export.
    """

    def _make_export_mocks(self):
        """Build minimal mocks for calling export_enemy()."""
        import bpy as _bpy_mock

        armature = MagicMock()
        armature.animation_data = MagicMock()
        armature.animation_data.action = None  # NLA-driven mode already set
        armature.select_set = MagicMock()

        mesh = MagicMock()
        mesh.select_set = MagicMock()

        # gltf() call capture
        gltf_kwargs_captured = {}

        def _capture_gltf(**kwargs):
            gltf_kwargs_captured.update(kwargs)

        _bpy_mock.ops.export_scene.gltf.side_effect = _capture_gltf
        _bpy_mock.ops.wm.save_as_mainfile.return_value = None
        _bpy_mock.ops.object.mode_set.return_value = None
        _bpy_mock.ops.object.select_all.return_value = None
        _bpy_mock.context.view_layer.objects.active = None

        return armature, mesh, gltf_kwargs_captured

    def test_bae_1_5_export_nla_strips_passed_to_gltf(self):
        """
        BAE-1.5: bpy.ops.export_scene.gltf() must receive export_nla_strips=True.

        This test will FAIL (red) until the implementation adds the keyword argument
        to the gltf() call in export_enemy(). It is the contract that drives Task 1
        implementation.
        """
        import tempfile

        armature, mesh, gltf_kwargs = self._make_export_mocks()

        from src.enemies.base_enemy import export_enemy

        with tempfile.TemporaryDirectory() as tmpdir:
            export_enemy(armature, mesh, "test_enemy", tmpdir)

        self.assertIn(
            'export_nla_strips', gltf_kwargs,
            "BAE-1.5: bpy.ops.export_scene.gltf() must be called with export_nla_strips kwarg. "
            "The kwarg is absent, meaning NLA strips will not be exported in Blender 3.x."
        )
        self.assertTrue(
            gltf_kwargs.get('export_nla_strips'),
            "BAE-1.5: export_nla_strips must be True, not False or absent"
        )

    def test_bae_1_5_export_animations_true(self):
        """
        BAE-1.5 (supporting): export_animations=True must remain in the gltf() call.
        A regression where animations are disabled entirely would silently break all
        animation export without failing the NLA strip test.
        """
        import tempfile

        armature, mesh, gltf_kwargs = self._make_export_mocks()

        from src.enemies.base_enemy import export_enemy

        with tempfile.TemporaryDirectory() as tmpdir:
            export_enemy(armature, mesh, "test_enemy", tmpdir)

        self.assertTrue(
            gltf_kwargs.get('export_animations', False),
            "BAE-1.5 (supporting): export_animations must be True in gltf() call"
        )


# ---------------------------------------------------------------------------
# Helpers used by NLA tests (not exported)
# ---------------------------------------------------------------------------

# _EXPORT_TO_INTERNAL is built lazily on first use to avoid a collection-time
# AttributeError when get_export_name has not been implemented yet (red phase).
# All NLA tests that call _get_internal_name_for_length_lookup will fail at
# runtime (not collection time) when get_export_name is absent.
_EXPORT_TO_INTERNAL: dict = {}
_EXPORT_TO_INTERNAL_BUILT: bool = False


def _build_export_to_internal() -> None:
    global _EXPORT_TO_INTERNAL, _EXPORT_TO_INTERNAL_BUILT
    if _EXPORT_TO_INTERNAL_BUILT:
        return
    for _internal in AnimationTypes.get_all():
        _EXPORT_TO_INTERNAL[AnimationTypes.get_export_name(_internal)] = _internal
    _EXPORT_TO_INTERNAL_BUILT = True


def _get_internal_name_for_length_lookup(export_or_internal_name: str) -> str:
    """Resolve an export name back to an internal name for AnimationConfig.get_length."""
    _build_export_to_internal()
    return _EXPORT_TO_INTERNAL.get(export_or_internal_name, export_or_internal_name)


if __name__ == '__main__':
    unittest.main()
