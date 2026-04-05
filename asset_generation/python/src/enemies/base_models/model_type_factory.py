"""Factory for body archetype model classes."""

from .base_model_type import BaseModelType
from .blob_model import BlobModel
from .humanoid_model import HumanoidModel
from .insectoid_model import InsectoidModel


class ModelTypeFactory:
    """Factory for creating appropriate model types"""

    MODEL_TYPES = {
        "insectoid": InsectoidModel,
        "blob": BlobModel,
        "humanoid": HumanoidModel,
    }

    @classmethod
    def create_model(cls, model_type: str, name: str, materials, rng) -> BaseModelType:
        """Create appropriate model type"""
        model_class = cls.MODEL_TYPES.get(model_type, InsectoidModel)
        model = model_class(name, materials, rng)
        model.create_geometry()
        model.apply_themed_materials()
        return model

    @classmethod
    def get_available_types(cls) -> list:
        """Get list of available model types"""
        return list(cls.MODEL_TYPES.keys())
