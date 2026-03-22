"""
Tests for AttackData and AttackType — pure Python, no Blender required.
"""

import json
import unittest

from src.combat.attack_data import AttackData, AttackType


class TestAttackType(unittest.TestCase):

    def test_all_types_have_string_values(self):
        for attack_type in AttackType:
            self.assertIsInstance(attack_type.value, str)

    def test_expected_types_exist(self):
        expected = {'physical', 'fire', 'ice', 'acid', 'poison'}
        actual = {t.value for t in AttackType}
        self.assertEqual(expected, actual)


class TestAttackData(unittest.TestCase):

    def _make_attack(self, **overrides) -> AttackData:
        defaults = dict(
            name="test_attack",
            animation_name="attack",
            attack_type=AttackType.PHYSICAL,
            damage_min=5.0,
            damage_max=15.0,
            range=2.0,
            hit_frame=12,
            cooldown_seconds=2.0,
            knockback_force=3.0,
        )
        defaults.update(overrides)
        return AttackData(**defaults)

    def test_to_dict_contains_all_expected_keys(self):
        expected_keys = {
            'name', 'animation_name', 'attack_type',
            'damage_min', 'damage_max', 'range',
            'hit_frame', 'cooldown_seconds', 'knockback_force',
            'is_area_of_effect', 'aoe_radius',
        }
        result = self._make_attack().to_dict()
        self.assertEqual(expected_keys, set(result.keys()))

    def test_to_dict_serializes_attack_type_as_string(self):
        result = self._make_attack(attack_type=AttackType.FIRE).to_dict()
        self.assertEqual(result['attack_type'], 'fire')
        self.assertIsInstance(result['attack_type'], str)

    def test_to_dict_is_json_serializable(self):
        result = self._make_attack().to_dict()
        # Should not raise
        json.dumps(result)

    def test_aoe_defaults_to_false_with_zero_radius(self):
        attack = self._make_attack()
        self.assertFalse(attack.is_area_of_effect)
        self.assertEqual(attack.aoe_radius, 0.0)

    def test_aoe_fields_round_trip_through_to_dict(self):
        attack = self._make_attack(is_area_of_effect=True, aoe_radius=4.5)
        result = attack.to_dict()
        self.assertTrue(result['is_area_of_effect'])
        self.assertEqual(result['aoe_radius'], 4.5)

    def test_all_attack_types_serialize_correctly(self):
        for attack_type in AttackType:
            attack = self._make_attack(attack_type=attack_type)
            result = attack.to_dict()
            self.assertEqual(result['attack_type'], attack_type.value)


if __name__ == '__main__':
    unittest.main()
