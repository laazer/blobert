"""
Tests for enemy attack profiles — pure Python, no Blender required.
"""

import json
import unittest

from src.combat.attack_data import AttackData, AttackType
from src.combat.enemy_attack_profiles import get_attack_profile, _hit_frame
from src.utils.constants import AnimationConfig, AnimationTypes


ANIMATED_ENEMY_TYPES = ['adhesion_bug', 'tar_slug', 'ember_imp']


class TestHitFrameHelper(unittest.TestCase):

    def test_hit_frame_is_positive(self):
        for anim in [AnimationTypes.ATTACK, AnimationTypes.SPECIAL_ATTACK]:
            self.assertGreater(_hit_frame(anim, 0.5), 0)

    def test_hit_frame_is_within_animation_length(self):
        for anim in [AnimationTypes.ATTACK, AnimationTypes.SPECIAL_ATTACK]:
            length = AnimationConfig.get_length(anim)
            self.assertLessEqual(_hit_frame(anim, 0.5), length)
            self.assertLessEqual(_hit_frame(anim, 1.0), length)

    def test_hit_frame_scales_with_fraction(self):
        early = _hit_frame(AnimationTypes.ATTACK, 0.25)
        late = _hit_frame(AnimationTypes.ATTACK, 0.75)
        self.assertLess(early, late)


class TestAttackProfileCompleteness(unittest.TestCase):

    def test_all_enemy_types_have_at_least_one_attack(self):
        for enemy_type in ANIMATED_ENEMY_TYPES:
            with self.subTest(enemy_type=enemy_type):
                self.assertGreater(len(get_attack_profile(enemy_type)), 0)

    def test_all_enemies_have_basic_and_special_attack(self):
        for enemy_type in ANIMATED_ENEMY_TYPES:
            with self.subTest(enemy_type=enemy_type):
                anim_names = {a.animation_name for a in get_attack_profile(enemy_type)}
                self.assertIn(AnimationTypes.ATTACK, anim_names,
                              f"{enemy_type} is missing a basic attack")
                self.assertIn(AnimationTypes.SPECIAL_ATTACK, anim_names,
                              f"{enemy_type} is missing a special attack")

    def test_unknown_enemy_returns_empty_list(self):
        self.assertEqual(get_attack_profile('does_not_exist'), [])

    def test_returned_objects_are_attack_data_instances(self):
        for enemy_type in ANIMATED_ENEMY_TYPES:
            for attack in get_attack_profile(enemy_type):
                with self.subTest(enemy_type=enemy_type, attack=attack.name):
                    self.assertIsInstance(attack, AttackData)


class TestAttackProfileValidity(unittest.TestCase):

    def test_all_attacks_have_valid_attack_type(self):
        for enemy_type in ANIMATED_ENEMY_TYPES:
            for attack in get_attack_profile(enemy_type):
                with self.subTest(enemy_type=enemy_type, attack=attack.name):
                    self.assertIsInstance(attack.attack_type, AttackType)

    def test_all_hit_frames_are_positive(self):
        for enemy_type in ANIMATED_ENEMY_TYPES:
            for attack in get_attack_profile(enemy_type):
                with self.subTest(enemy_type=enemy_type, attack=attack.name):
                    self.assertGreater(attack.hit_frame, 0)

    def test_all_hit_frames_are_within_animation_length(self):
        for enemy_type in ANIMATED_ENEMY_TYPES:
            for attack in get_attack_profile(enemy_type):
                with self.subTest(enemy_type=enemy_type, attack=attack.name):
                    length = AnimationConfig.get_length(attack.animation_name)
                    self.assertLessEqual(attack.hit_frame, length)

    def test_aoe_attacks_have_positive_radius(self):
        for enemy_type in ANIMATED_ENEMY_TYPES:
            for attack in get_attack_profile(enemy_type):
                if attack.is_area_of_effect:
                    with self.subTest(enemy_type=enemy_type, attack=attack.name):
                        self.assertGreater(attack.aoe_radius, 0)

    def test_all_ranges_are_positive(self):
        for enemy_type in ANIMATED_ENEMY_TYPES:
            for attack in get_attack_profile(enemy_type):
                with self.subTest(enemy_type=enemy_type, attack=attack.name):
                    self.assertGreater(attack.range, 0)

    def test_all_cooldowns_are_positive(self):
        for enemy_type in ANIMATED_ENEMY_TYPES:
            for attack in get_attack_profile(enemy_type):
                with self.subTest(enemy_type=enemy_type, attack=attack.name):
                    self.assertGreater(attack.cooldown_seconds, 0)

    def test_all_profiles_are_json_serializable(self):
        for enemy_type in ANIMATED_ENEMY_TYPES:
            with self.subTest(enemy_type=enemy_type):
                data = [a.to_dict() for a in get_attack_profile(enemy_type)]
                # Should not raise
                json.dumps(data)

    def test_attack_names_are_unique_per_enemy(self):
        for enemy_type in ANIMATED_ENEMY_TYPES:
            with self.subTest(enemy_type=enemy_type):
                names = [a.name for a in get_attack_profile(enemy_type)]
                self.assertEqual(len(names), len(set(names)),
                                 f"{enemy_type} has duplicate attack names")


if __name__ == '__main__':
    unittest.main()
