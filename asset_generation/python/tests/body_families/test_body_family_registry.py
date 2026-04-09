"""Runtime shape checks for ``BODY_FAMILY_REGISTRY`` (TypedDict-backed rows)."""

from __future__ import annotations

from src.body_families.ids import EnemyBodyTypes
from src.body_families.registry import BODY_FAMILY_REGISTRY


def test_body_family_registry_has_three_core_families() -> None:
    assert EnemyBodyTypes.BLOB in BODY_FAMILY_REGISTRY
    assert EnemyBodyTypes.QUADRUPED in BODY_FAMILY_REGISTRY
    assert EnemyBodyTypes.HUMANOID in BODY_FAMILY_REGISTRY


def test_body_family_registry_entry_shape() -> None:
    for _fid, row in BODY_FAMILY_REGISTRY.items():
        assert set(row.keys()) == {"motion_class", "rig_factory", "keywords"}
        assert callable(row["rig_factory"])
        assert isinstance(row["keywords"], list)
        assert isinstance(row["motion_class"], type)
