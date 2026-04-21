"""
Tests for the player slime character system.

bpy / bmesh / mathutils are mocked before any src imports.
"""

import random
import sys
from unittest.mock import MagicMock, patch

# ------------------------------------------------------------------
# Mock Blender modules before any src imports
# ------------------------------------------------------------------
sys.modules.setdefault('bpy', MagicMock())
sys.modules.setdefault('bmesh', MagicMock())
sys.modules.setdefault('mathutils', MagicMock())
sys.modules.setdefault('mathutils.Vector', MagicMock())
sys.modules.setdefault('mathutils.Euler', MagicMock())

import pytest

from src.player.player_materials import SLIME_COLORS
from src.utils.config import (
    PlayerAnimationConfig,
    PlayerAnimationTypes,
    PlayerBoneNames,
    PlayerExportConfig,
)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _make_rng(seed: int = 42) -> random.Random:
    return random.Random(seed)


# ------------------------------------------------------------------
# PlayerAnimationTypes
# ------------------------------------------------------------------

class TestPlayerAnimationTypes:
    def test_get_all_contains_eight_animations(self):
        assert len(PlayerAnimationTypes.get_all()) == 8

    def test_get_all_contains_expected_names(self):
        expected = {"idle", "move", "jump", "land", "attack", "damage", "death", "celebrate"}
        assert set(PlayerAnimationTypes.get_all()) == expected

    def test_looping_animations_are_subset_of_all(self):
        looping = set(PlayerAnimationTypes.get_looping())
        assert looping.issubset(set(PlayerAnimationTypes.get_all()))

    def test_idle_and_move_are_looping(self):
        assert PlayerAnimationTypes.IDLE in PlayerAnimationTypes.get_looping()
        assert PlayerAnimationTypes.MOVE in PlayerAnimationTypes.get_looping()

    def test_jump_land_and_death_are_non_looping(self):
        non_looping = PlayerAnimationTypes.get_non_looping()
        assert PlayerAnimationTypes.JUMP in non_looping
        assert PlayerAnimationTypes.LAND in non_looping
        assert PlayerAnimationTypes.DEATH in non_looping

    def test_all_equals_looping_plus_non_looping(self):
        combined = set(PlayerAnimationTypes.get_looping()) | set(PlayerAnimationTypes.get_non_looping())
        assert combined == set(PlayerAnimationTypes.get_all())


# ------------------------------------------------------------------
# PlayerAnimationConfig
# ------------------------------------------------------------------

class TestPlayerAnimationConfig:
    def test_all_animations_have_defined_lengths(self):
        for anim in PlayerAnimationTypes.get_all():
            length = PlayerAnimationConfig.get_length(anim)
            assert length > 0, f"{anim} has non-positive length"

    def test_fps_is_24(self):
        assert PlayerAnimationConfig.FPS == 24

    def test_duration_matches_length_over_fps(self):
        for anim in PlayerAnimationTypes.get_all():
            expected = PlayerAnimationConfig.get_length(anim) / 24.0
            assert PlayerAnimationConfig.get_duration_seconds(anim) == pytest.approx(expected)

    def test_jump_is_shorter_than_idle(self):
        assert PlayerAnimationConfig.get_length(PlayerAnimationTypes.JUMP) < \
               PlayerAnimationConfig.get_length(PlayerAnimationTypes.IDLE)

    def test_death_is_longer_than_damage(self):
        assert PlayerAnimationConfig.get_length(PlayerAnimationTypes.DEATH) > \
               PlayerAnimationConfig.get_length(PlayerAnimationTypes.DAMAGE)


# ------------------------------------------------------------------
# PlayerBoneNames
# ------------------------------------------------------------------

class TestPlayerBoneNames:
    def test_get_all_contains_six_bones(self):
        assert len(PlayerBoneNames.get_all()) == 6

    def test_root_and_body_in_get_all(self):
        bones = PlayerBoneNames.get_all()
        assert PlayerBoneNames.ROOT in bones
        assert PlayerBoneNames.BODY in bones

    def test_eyes_in_get_eyes(self):
        eyes = PlayerBoneNames.get_eyes()
        assert PlayerBoneNames.EYE_LEFT in eyes
        assert PlayerBoneNames.EYE_RIGHT in eyes

    def test_arms_in_get_arms(self):
        arms = PlayerBoneNames.get_arms()
        assert PlayerBoneNames.ARM_LEFT in arms
        assert PlayerBoneNames.ARM_RIGHT in arms

    def test_bone_names_are_lowercase_strings(self):
        for name in PlayerBoneNames.get_all():
            assert isinstance(name, str)
            assert name == name.lower()


# ------------------------------------------------------------------
# PlayerExportConfig
# ------------------------------------------------------------------

class TestPlayerExportConfig:
    def test_player_dir_is_defined(self):
        assert PlayerExportConfig.PLAYER_DIR

    def test_filename_pattern_formats_correctly(self):
        result = PlayerExportConfig.FILENAME_PATTERN.format(color="blue", variant=0)
        assert result == "player_slime_blue_00"

    def test_filename_pattern_pads_variant_to_two_digits(self):
        result = PlayerExportConfig.FILENAME_PATTERN.format(color="pink", variant=3)
        assert result == "player_slime_pink_03"


# ------------------------------------------------------------------
# SLIME_COLORS palette
# ------------------------------------------------------------------

class TestSlimeColors:
    def test_at_least_four_colors_defined(self):
        assert len(SLIME_COLORS) >= 4

    def test_blue_and_green_are_present(self):
        assert "blue" in SLIME_COLORS
        assert "green" in SLIME_COLORS

    def test_all_colors_are_rgba_tuples(self):
        for name, color in SLIME_COLORS.items():
            assert len(color) == 4, f"{name}: expected RGBA tuple"
            for channel in color:
                assert 0.0 <= channel <= 1.0, f"{name}: channel out of [0, 1]"

    def test_all_color_keys_are_lowercase_strings(self):
        for name in SLIME_COLORS:
            assert isinstance(name, str)
            assert name == name.lower()


# ------------------------------------------------------------------
# PlayerSlimeBody — geometry structure (mocked Blender calls)
# ------------------------------------------------------------------

class TestPlayerSlimeBody:
    def _build_body(self, color: str = "blue"):
        mock_part = MagicMock(name="mesh_part")

        with patch('src.player.player_slime_body.create_sphere', return_value=mock_part), \
             patch('src.player.player_slime_body.join_objects', return_value=mock_part), \
             patch('src.player.player_slime_body.apply_smooth_shading'), \
             patch('src.player.player_slime_body.apply_material_to_object'), \
             patch('src.player.player_slime_body.create_slime_body_material', return_value=MagicMock()), \
             patch('src.player.player_slime_body.create_sclera_material', return_value=MagicMock()), \
             patch('src.player.player_slime_body.create_pupil_material', return_value=MagicMock()), \
             patch('src.player.player_slime_body.create_highlight_material', return_value=MagicMock()), \
             patch('src.player.player_slime_body.create_cheek_material', return_value=MagicMock()):

            from src.player.player_slime_body import PlayerSlimeBody
            body = PlayerSlimeBody(color=color, rng=_make_rng())
            mesh = body.build()
            return body, mesh

    def test_build_returns_a_mesh(self):
        _, mesh = self._build_body()
        assert mesh is not None

    def test_body_parts_created(self):
        body, _ = self._build_body()
        assert len(body._body_parts) >= 1

    def test_two_eye_scleras_created(self):
        body, _ = self._build_body()
        assert len(body._sclera_parts) == 2

    def test_two_pupils_created(self):
        body, _ = self._build_body()
        assert len(body._pupil_parts) == 2

    def test_two_eye_highlights_created(self):
        body, _ = self._build_body()
        assert len(body._highlight_parts) == 2

    def test_two_cheeks_created(self):
        body, _ = self._build_body()
        assert len(body._cheek_parts) == 2

    def test_two_arm_nubs_created(self):
        body, _ = self._build_body()
        assert len(body._arm_parts) == 2

    def test_invalid_color_falls_back_to_blue(self):
        body, _ = self._build_body(color="neon_rainbow_unicorn")
        assert body.color == "blue"


# ------------------------------------------------------------------
# PlayerSlimeAnimations — animation method coverage
# ------------------------------------------------------------------

class TestPlayerSlimeAnimations:
    def _make_animator(self):
        mock_armature = MagicMock(name="armature")
        mock_armature.pose.bones = {}
        mock_armature.animation_data = None
        mock_armature.mode = 'OBJECT'
        return mock_armature

    def _run_animation(self, method_name: str, length: int):
        """Call a single animation method with set_bone_keyframe mocked."""
        from src.player.player_animations import PlayerSlimeAnimations

        armature = self._make_animator()
        animator = PlayerSlimeAnimations(armature, _make_rng())

        with patch('src.player.player_animations.set_bone_keyframe') as mock_kf:
            getattr(animator, method_name)(length)
        return mock_kf

    def test_idle_sets_body_keyframes(self):
        mock_kf = self._run_animation('create_idle_animation', 48)
        body_calls = [c for c in mock_kf.call_args_list if c.args[1] == PlayerBoneNames.BODY]
        assert len(body_calls) >= 3

    def test_idle_sets_eye_blink_keyframes(self):
        mock_kf = self._run_animation('create_idle_animation', 48)
        eye_calls = [c for c in mock_kf.call_args_list
                     if c.args[1] in PlayerBoneNames.get_eyes()]
        assert len(eye_calls) >= 4  # open + closed + reopen × 2 eyes

    def test_move_sets_squash_and_stretch(self):
        from src.player.player_animations import _BIG_SQUASH, _SQUASH, _STRETCH
        mock_kf = self._run_animation('create_move_animation', 24)
        # Check that both squash and stretch presets appear
        keyword_scales = [c.kwargs.get('scale') for c in mock_kf.call_args_list if 'scale' in c.kwargs]
        assert _SQUASH in keyword_scales or _BIG_SQUASH in keyword_scales
        assert _STRETCH in keyword_scales

    def test_jump_includes_root_location_lift(self):
        mock_kf = self._run_animation('create_jump_animation', 20)
        root_calls = [c for c in mock_kf.call_args_list if c.args[1] == PlayerBoneNames.ROOT]
        # At least one root keyframe should have a positive Z location
        z_values = [c.kwargs.get('location', (0, 0, 0))[2] for c in root_calls if 'location' in c.kwargs]
        assert any(z > 0 for z in z_values)

    def test_land_creates_impact_squash(self):
        from src.player.player_animations import _IMPACT
        mock_kf = self._run_animation('create_land_animation', 16)
        keyword_scales = [c.kwargs.get('scale') for c in mock_kf.call_args_list if 'scale' in c.kwargs]
        assert _IMPACT in keyword_scales

    def test_attack_windup_and_spit_frames_are_distinct(self):
        mock_kf = self._run_animation('create_attack_animation', 30)
        body_calls = [c for c in mock_kf.call_args_list if c.args[1] == PlayerBoneNames.BODY]
        frames = [c.args[2] for c in body_calls]
        assert len(frames) == len(set(frames)), "Duplicate attack frames on body bone"

    def test_damage_sets_root_offset_both_sides(self):
        mock_kf = self._run_animation('create_damage_animation', 12)
        root_calls = [c for c in mock_kf.call_args_list if c.args[1] == PlayerBoneNames.ROOT]
        x_locs = [c.kwargs.get('location', (0,0,0))[0] for c in root_calls if 'location' in c.kwargs]
        positives = [x for x in x_locs if x > 0]
        negatives = [x for x in x_locs if x < 0]
        assert positives, "Damage animation should shake right"
        assert negatives, "Damage animation should shake left"

    def test_death_closes_eyes_at_end(self):
        from src.player.player_animations import _BLINK_CLOSED
        mock_kf = self._run_animation('create_death_animation', 60)
        eye_calls = [c for c in mock_kf.call_args_list
                     if c.args[1] in PlayerBoneNames.get_eyes()]
        end_scales = [
            c.kwargs.get('scale')
            for c in eye_calls
            if 'scale' in c.kwargs and c.args[2] == 60
        ]
        assert any(s == _BLINK_CLOSED for s in end_scales), "Eyes should be closed at end of death"

    def test_death_sinks_root_at_end(self):
        mock_kf = self._run_animation('create_death_animation', 60)
        root_calls = [c for c in mock_kf.call_args_list if c.args[1] == PlayerBoneNames.ROOT]
        final_z = [
            c.kwargs.get('location', (0,0,0))[2]
            for c in root_calls
            if 'location' in c.kwargs and c.args[2] == 60
        ]
        assert final_z and final_z[0] < 0, "Root should sink below ground at end of death"

    def test_celebrate_has_more_squash_stretch_frames_than_idle(self):
        from src.player.player_animations import _REST
        mock_idle = self._run_animation('create_idle_animation', 48)
        mock_celebrate = self._run_animation('create_celebrate_animation', 36)

        def count_non_rest(mock_obj):
            return sum(
                1 for c in mock_obj.call_args_list
                if c.args[1] == PlayerBoneNames.BODY
                and c.kwargs.get('scale', _REST) != _REST
            )

        assert count_non_rest(mock_celebrate) >= count_non_rest(mock_idle)
