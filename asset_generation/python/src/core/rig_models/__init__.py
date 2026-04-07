"""Rig model classes: one module per preset; ``import rig_models`` matches public API."""

from __future__ import annotations

from .base import SimpleRigModel
from .blob_simple import BlobSimpleRig
from .humanoid_simple import HumanoidSimpleRig
from .import_rigs import (
    imported_blob_rig,
    imported_humanoid_rig,
    imported_quadruped_rig,
)
from .quadruped_simple import QuadrupedSimpleRig

__all__ = [
    "SimpleRigModel",
    "BlobSimpleRig",
    "HumanoidSimpleRig",
    "QuadrupedSimpleRig",
    "imported_blob_rig",
    "imported_humanoid_rig",
    "imported_quadruped_rig",
]
