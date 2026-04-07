"""Rig helpers for the external import pipeline (no concrete enemy mesh class)."""

from __future__ import annotations

from ...utils.procedural_constants import IMPORT_DEFAULT_BODY_HEIGHT
from ..rig_types import RigDefinition
from .blob_simple import BlobSimpleRig
from .humanoid_simple import HumanoidSimpleRig
from .quadruped_simple import QuadrupedSimpleRig


class _ImportBlobRig(BlobSimpleRig):
    body_height = IMPORT_DEFAULT_BODY_HEIGHT


class _ImportHumanoidRig(HumanoidSimpleRig):
    body_height = IMPORT_DEFAULT_BODY_HEIGHT


class _ImportQuadrupedRig(QuadrupedSimpleRig):
    body_height = IMPORT_DEFAULT_BODY_HEIGHT


def imported_blob_rig() -> RigDefinition:
    return _ImportBlobRig().rig_definition()


def imported_humanoid_rig() -> RigDefinition:
    return _ImportHumanoidRig().rig_definition()


def imported_quadruped_rig() -> RigDefinition:
    return _ImportQuadrupedRig().rig_definition()
