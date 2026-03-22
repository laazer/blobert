"""
Factory for building and exporting level objects
"""

from typing import Type

from ..utils.constants import LevelObjectTypes, LevelExportConfig
from .base_level_object import BaseLevelObject, export_level_object
from .platforms import FlatPlatform, MovingPlatform, CrumblingPlatform
from .walls import SolidWall, CrenellatedWall
from .traps import SpikeTrap, FireTrap
from .checkpoints import Checkpoint


class LevelObjectBuilder:
    """Factory that creates and exports level objects by type name."""

    OBJECT_CLASSES: dict[str, Type[BaseLevelObject]] = {
        LevelObjectTypes.FLAT_PLATFORM: FlatPlatform,
        LevelObjectTypes.MOVING_PLATFORM: MovingPlatform,
        LevelObjectTypes.CRUMBLING_PLATFORM: CrumblingPlatform,
        LevelObjectTypes.SOLID_WALL: SolidWall,
        LevelObjectTypes.CRENELLATED_WALL: CrenellatedWall,
        LevelObjectTypes.SPIKE_TRAP: SpikeTrap,
        LevelObjectTypes.FIRE_TRAP: FireTrap,
        LevelObjectTypes.CHECKPOINT: Checkpoint,
    }

    @classmethod
    def create_object(cls, object_type: str, rng) -> tuple:
        """Build a level object and return (mesh, level_object_instance).

        Returns (None, None) if the type is unknown or the build fails.
        """
        if object_type not in cls.OBJECT_CLASSES:
            raise ValueError(
                f"Unknown level object type: {object_type!r}. "
                f"Available: {list(cls.OBJECT_CLASSES)}"
            )

        object_class = cls.OBJECT_CLASSES[object_type]
        level_object = object_class(name=object_type, rng=rng)
        mesh = level_object.build()

        return mesh, level_object

    @classmethod
    def get_available_types(cls):
        return list(cls.OBJECT_CLASSES)

    @classmethod
    def export(
        cls,
        object_type: str,
        rng,
        variant_index: int = 0,
        export_dir: str = LevelExportConfig.LEVEL_DIR,
    ) -> str:
        """Build a level object and export it to GLB (+ JSON if applicable).

        Returns the path of the exported GLB file.
        """
        mesh, level_object = cls.create_object(object_type, rng)
        if mesh is None:
            raise RuntimeError(f"Build failed for level object type {object_type!r}")

        filename = LevelExportConfig.OBJECT_FILENAME_PATTERN.format(
            object_type=object_type, variant=variant_index
        )
        return export_level_object(mesh, filename, export_dir, level_object)
