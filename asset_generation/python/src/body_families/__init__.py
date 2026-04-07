"""Body families: ids, bones, motion (*), factory, registry.

Import submodules explicitly (e.g. ``body_families.factory``) to avoid loading
the full animation stack when only ``bones`` / ``ids`` are needed.
"""

from .bones import BoneNames
from .ids import EnemyBodyTypes

__all__ = ["BoneNames", "EnemyBodyTypes"]
