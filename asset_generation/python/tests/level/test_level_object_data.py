"""
Tests for TrapData serialization and the TrapType enum.

These tests are pure Python and run outside Blender.
"""

import json

from src.level.level_object_data import TrapData, TrapType


class TestTrapType:
    def test_all_expected_values_exist(self):
        expected = {"spike", "fire", "ice", "crusher"}
        actual = {member.value for member in TrapType}
        assert actual == expected

    def test_values_are_lowercase_strings(self):
        for member in TrapType:
            assert member.value == member.value.lower()
            assert isinstance(member.value, str)


class TestTrapData:
    def _make_spike_trap_data(self) -> TrapData:
        return TrapData(
            name="spike_strike",
            trap_type=TrapType.SPIKE,
            damage_per_hit=25.0,
            trigger_radius=1.2,
            cooldown_seconds=2.0,
        )

    def _make_fire_trap_data(self) -> TrapData:
        return TrapData(
            name="fire_burst",
            trap_type=TrapType.FIRE,
            damage_per_hit=15.0,
            trigger_radius=1.8,
            cooldown_seconds=3.0,
            activation_delay_seconds=0.5,
        )

    # ------------------------------------------------------------------
    # to_dict() key coverage
    # ------------------------------------------------------------------

    def test_to_dict_contains_all_required_keys(self):
        required_keys = {
            "name",
            "trap_type",
            "damage_per_hit",
            "trigger_radius",
            "cooldown_seconds",
            "activation_delay_seconds",
            "is_visible_when_inactive",
        }
        result = self._make_spike_trap_data().to_dict()
        assert required_keys.issubset(result.keys())

    # ------------------------------------------------------------------
    # Value serialization
    # ------------------------------------------------------------------

    def test_trap_type_serialized_as_string_value(self):
        result = self._make_spike_trap_data().to_dict()
        assert result["trap_type"] == "spike"
        assert isinstance(result["trap_type"], str)

    def test_fire_trap_type_serialized_correctly(self):
        result = self._make_fire_trap_data().to_dict()
        assert result["trap_type"] == "fire"

    def test_numeric_fields_preserved(self):
        data = self._make_spike_trap_data()
        result = data.to_dict()
        assert result["damage_per_hit"] == 25.0
        assert result["trigger_radius"] == 1.2
        assert result["cooldown_seconds"] == 2.0

    def test_activation_delay_default_is_zero(self):
        result = self._make_spike_trap_data().to_dict()
        assert result["activation_delay_seconds"] == 0.0

    def test_activation_delay_preserved_when_set(self):
        result = self._make_fire_trap_data().to_dict()
        assert result["activation_delay_seconds"] == 0.5

    def test_is_visible_when_inactive_defaults_to_true(self):
        result = self._make_spike_trap_data().to_dict()
        assert result["is_visible_when_inactive"] is True

    def test_is_visible_when_inactive_can_be_set_false(self):
        trap = TrapData(
            name="hidden_spike",
            trap_type=TrapType.SPIKE,
            damage_per_hit=20.0,
            trigger_radius=1.0,
            cooldown_seconds=1.5,
            is_visible_when_inactive=False,
        )
        result = trap.to_dict()
        assert result["is_visible_when_inactive"] is False

    # ------------------------------------------------------------------
    # JSON round-trip safety
    # ------------------------------------------------------------------

    def test_to_dict_is_json_serializable(self):
        result = self._make_spike_trap_data().to_dict()
        # Must not raise
        serialized = json.dumps(result)
        restored = json.loads(serialized)
        assert restored["name"] == "spike_strike"
        assert restored["trap_type"] == "spike"

    def test_fire_trap_to_dict_is_json_serializable(self):
        result = self._make_fire_trap_data().to_dict()
        json.dumps(result)  # must not raise
