"""
Public package for procedural enemy body archetypes and ModelTypeFactory.

Import path remains ``src.enemies.base_models`` (package replaces former monolithic module).
"""

from .base_model_type import BaseModelType
from .blob_model import BlobModel
from .humanoid_model import HumanoidModel
from .insectoid_model import InsectoidModel
from .model_type_factory import ModelTypeFactory

__all__ = [
    "BaseModelType",
    "BlobModel",
    "HumanoidModel",
    "InsectoidModel",
    "ModelTypeFactory",
]
