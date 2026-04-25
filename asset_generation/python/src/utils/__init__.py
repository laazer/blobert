"""
Utility classes and constants for the enemy generation system
"""

from . import run_contract
from .config import (
    AnimationConfig,
    AnimationTypes,
    BoneNames,
    EnemyBodyTypes,
    EnemyTypes,
    ExportConfig,
)
from .materials import (
    BodyPartMaterials,
    MaterialCategories,
    MaterialColors,
    MaterialNames,
    MaterialThemes,
)

__all__ = [
    # Core constants
    'EnemyTypes', 'AnimationTypes', 'EnemyBodyTypes', 'BoneNames',
    'AnimationConfig', 'ExportConfig',

    # Material constants
    'MaterialColors', 'MaterialNames', 'MaterialThemes',
    'MaterialCategories', 'BodyPartMaterials'
]