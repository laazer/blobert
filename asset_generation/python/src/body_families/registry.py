"""Registry for body-family motion classes and import rig factories (keywords: ``keywords.py``)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, TypedDict

from .ids import EnemyBodyTypes
from .keywords import keywords_for_family
from .motion_blob import BlobBodyType
from .motion_humanoid import HumanoidBodyType
from .motion_quadruped import QuadrupedBodyType

if TYPE_CHECKING:
    try:
        from core.rig_types import RigDefinition
    except ImportError:
        from src.core.rig_types import RigDefinition


class BodyFamilyRegistryEntry(TypedDict):
    """Static registry row: motion class, rig factory, and text keywords."""

    motion_class: type
    rig_factory: Callable[[], RigDefinition]
    keywords: list[str]


def _rig_blob() -> RigDefinition:
    try:
        from core.rig_models.import_rigs import imported_blob_rig
    except ImportError:
        from src.core.rig_models.import_rigs import imported_blob_rig
    return imported_blob_rig()


def _rig_quadruped() -> RigDefinition:
    try:
        from core.rig_models.import_rigs import imported_quadruped_rig
    except ImportError:
        from src.core.rig_models.import_rigs import imported_quadruped_rig
    return imported_quadruped_rig()


def _rig_humanoid() -> RigDefinition:
    try:
        from core.rig_models.import_rigs import imported_humanoid_rig
    except ImportError:
        from src.core.rig_models.import_rigs import imported_humanoid_rig
    return imported_humanoid_rig()


BODY_FAMILY_REGISTRY: dict[str, BodyFamilyRegistryEntry] = {
    EnemyBodyTypes.BLOB: {
        "motion_class": BlobBodyType,
        "rig_factory": _rig_blob,
        "keywords": keywords_for_family(EnemyBodyTypes.BLOB),
    },
    EnemyBodyTypes.QUADRUPED: {
        "motion_class": QuadrupedBodyType,
        "rig_factory": _rig_quadruped,
        "keywords": keywords_for_family(EnemyBodyTypes.QUADRUPED),
    },
    EnemyBodyTypes.HUMANOID: {
        "motion_class": HumanoidBodyType,
        "rig_factory": _rig_humanoid,
        "keywords": keywords_for_family(EnemyBodyTypes.HUMANOID),
    },
}


def rig_definition_for_import(body_type: str) -> RigDefinition:
    """RigDefinition for external import pipeline when mesh has no armature."""
    bt = (body_type or "").strip().lower()
    if bt == EnemyBodyTypes.BLOB:
        return _rig_blob()
    if bt == EnemyBodyTypes.HUMANOID:
        return _rig_humanoid()
    return _rig_quadruped()


def get_rig_factory(body_type_id: str) -> Callable[[], RigDefinition]:
    """Callable that returns RigDefinition for a canonical family id."""
    bt = (body_type_id or "").strip().lower()
    if bt == EnemyBodyTypes.BLOB:
        return _rig_blob
    if bt == EnemyBodyTypes.HUMANOID:
        return _rig_humanoid
    return _rig_quadruped
