"""
Tests for LevelObjectBuilder and per-object trap data / metadata.

bpy is mocked before any imports so these tests run outside Blender.
"""

import sys
import json
import random
from unittest.mock import MagicMock, patch, call

# ------------------------------------------------------------------
# Mock Blender modules before any src imports
# ------------------------------------------------------------------
sys.modules.setdefault('bpy', MagicMock())
sys.modules.setdefault('bmesh', MagicMock())
sys.modules.setdefault('mathutils', MagicMock())
sys.modules.setdefault('mathutils.Vector', MagicMock())
sys.modules.setdefault('mathutils.Euler', MagicMock())

import pytest

from src.level.level_object_data import TrapType
from src.level.level_object_builder import LevelObjectBuilder
from src.utils.constants import LevelObjectTypes


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _make_rng(seed: int = 42) -> random.Random:
    return random.Random(seed)


def _patched_build(object_type: str, rng):
    """Call create_object with all Blender ops mocked out."""
    mock_mesh = MagicMock(name="mesh")
    mock_mesh.name = "mock_mesh"

    with patch('src.level.platforms.create_box', return_value=mock_mesh), \
         patch('src.level.walls.create_box', return_value=mock_mesh), \
         patch('src.level.traps.create_box', return_value=mock_mesh), \
         patch('src.level.traps.create_cylinder', return_value=mock_mesh), \
         patch('src.level.checkpoints.create_box', return_value=mock_mesh), \
         patch('src.level.checkpoints.create_cylinder', return_value=mock_mesh), \
         patch('src.level.base_level_object.join_objects', return_value=mock_mesh), \
         patch('src.level.base_level_object.apply_smooth_shading'), \
         patch('src.level.platforms.create_solid_material', return_value=MagicMock()), \
         patch('src.level.walls.create_solid_material', return_value=MagicMock()), \
         patch('src.level.traps.create_solid_material', return_value=MagicMock()), \
         patch('src.level.traps.create_emissive_material', return_value=MagicMock()), \
         patch('src.level.checkpoints.create_solid_material', return_value=MagicMock()), \
         patch('src.level.checkpoints.create_emissive_material', return_value=MagicMock()), \
         patch('src.level.platforms._apply_single_material'), \
         patch('src.level.walls._apply_single_material'), \
         patch('src.materials.material_system.apply_material_to_object'):
        return LevelObjectBuilder.create_object(object_type, rng)


# ------------------------------------------------------------------
# Builder type registration
# ------------------------------------------------------------------

class TestLevelObjectBuilderRegistration:
    def test_all_level_object_types_registered(self):
        registered = set(LevelObjectBuilder.get_available_types())
        expected = set(LevelObjectTypes.get_all())
        assert expected == registered

    def test_get_available_types_returns_list(self):
        assert isinstance(LevelObjectBuilder.get_available_types(), list)

    def test_unknown_type_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown level object type"):
            LevelObjectBuilder.create_object("flying_spaghetti_monster", _make_rng())


# ------------------------------------------------------------------
# Platform builders
# ------------------------------------------------------------------

class TestPlatformBuilders:
    @pytest.mark.parametrize("object_type", LevelObjectTypes.get_platforms())
    def test_platform_build_returns_mesh_and_object(self, object_type):
        mesh, level_object = _patched_build(object_type, _make_rng())
        assert mesh is not None
        assert level_object is not None

    @pytest.mark.parametrize("object_type", LevelObjectTypes.get_platforms())
    def test_platform_has_no_trap_data(self, object_type):
        _, level_object = _patched_build(object_type, _make_rng())
        assert level_object.get_trap_data() == []

    def test_flat_platform_metadata_has_width_and_depth(self):
        _, obj = _patched_build(LevelObjectTypes.FLAT_PLATFORM, _make_rng())
        metadata = obj.get_object_metadata()
        assert "width" in metadata
        assert "depth" in metadata

    def test_moving_platform_metadata_has_movement_params(self):
        _, obj = _patched_build(LevelObjectTypes.MOVING_PLATFORM, _make_rng())
        metadata = obj.get_object_metadata()
        assert "movement_speed" in metadata
        assert "movement_range" in metadata
        assert "movement_axis" in metadata

    def test_crumbling_platform_metadata_has_crumble_delay(self):
        _, obj = _patched_build(LevelObjectTypes.CRUMBLING_PLATFORM, _make_rng())
        metadata = obj.get_object_metadata()
        assert "crumble_delay_seconds" in metadata
        assert metadata["crumble_delay_seconds"] > 0


# ------------------------------------------------------------------
# Wall builders
# ------------------------------------------------------------------

class TestWallBuilders:
    @pytest.mark.parametrize("object_type", LevelObjectTypes.get_walls())
    def test_wall_build_returns_mesh_and_object(self, object_type):
        mesh, level_object = _patched_build(object_type, _make_rng())
        assert mesh is not None
        assert level_object is not None

    @pytest.mark.parametrize("object_type", LevelObjectTypes.get_walls())
    def test_walls_have_no_trap_data(self, object_type):
        _, level_object = _patched_build(object_type, _make_rng())
        assert level_object.get_trap_data() == []

    def test_crenellated_wall_metadata_has_merlon_count(self):
        _, obj = _patched_build(LevelObjectTypes.CRENELLATED_WALL, _make_rng())
        metadata = obj.get_object_metadata()
        assert "merlon_count" in metadata
        assert metadata["merlon_count"] > 0


# ------------------------------------------------------------------
# Trap builders
# ------------------------------------------------------------------

class TestTrapBuilders:
    @pytest.mark.parametrize("object_type", LevelObjectTypes.get_traps())
    def test_trap_build_returns_mesh_and_object(self, object_type):
        mesh, level_object = _patched_build(object_type, _make_rng())
        assert mesh is not None
        assert level_object is not None

    @pytest.mark.parametrize("object_type", LevelObjectTypes.get_traps())
    def test_traps_have_at_least_one_trap_datum(self, object_type):
        _, level_object = _patched_build(object_type, _make_rng())
        trap_data = level_object.get_trap_data()
        assert len(trap_data) >= 1

    def test_spike_trap_type_is_spike(self):
        _, obj = _patched_build(LevelObjectTypes.SPIKE_TRAP, _make_rng())
        assert obj.get_trap_data()[0].trap_type == TrapType.SPIKE

    def test_fire_trap_type_is_fire(self):
        _, obj = _patched_build(LevelObjectTypes.FIRE_TRAP, _make_rng())
        assert obj.get_trap_data()[0].trap_type == TrapType.FIRE

    @pytest.mark.parametrize("object_type", LevelObjectTypes.get_traps())
    def test_trap_damage_is_positive(self, object_type):
        _, obj = _patched_build(object_type, _make_rng())
        for trap in obj.get_trap_data():
            assert trap.damage_per_hit > 0

    @pytest.mark.parametrize("object_type", LevelObjectTypes.get_traps())
    def test_trap_trigger_radius_is_positive(self, object_type):
        _, obj = _patched_build(object_type, _make_rng())
        for trap in obj.get_trap_data():
            assert trap.trigger_radius > 0

    @pytest.mark.parametrize("object_type", LevelObjectTypes.get_traps())
    def test_trap_cooldown_is_positive(self, object_type):
        _, obj = _patched_build(object_type, _make_rng())
        for trap in obj.get_trap_data():
            assert trap.cooldown_seconds > 0

    @pytest.mark.parametrize("object_type", LevelObjectTypes.get_traps())
    def test_trap_data_is_json_serializable(self, object_type):
        _, obj = _patched_build(object_type, _make_rng())
        for trap in obj.get_trap_data():
            json.dumps(trap.to_dict())  # must not raise


# ------------------------------------------------------------------
# Checkpoint builder
# ------------------------------------------------------------------

class TestCheckpointBuilder:
    def test_checkpoint_build_returns_mesh_and_object(self):
        mesh, level_object = _patched_build(LevelObjectTypes.CHECKPOINT, _make_rng())
        assert mesh is not None
        assert level_object is not None

    def test_checkpoint_has_no_trap_data(self):
        _, obj = _patched_build(LevelObjectTypes.CHECKPOINT, _make_rng())
        assert obj.get_trap_data() == []

    def test_checkpoint_metadata_has_gate_width_and_pillar_height(self):
        _, obj = _patched_build(LevelObjectTypes.CHECKPOINT, _make_rng())
        metadata = obj.get_object_metadata()
        assert "gate_width" in metadata
        assert "pillar_height" in metadata
        assert metadata["gate_width"] > 0
        assert metadata["pillar_height"] > 0
