"""
Behavioral tests for ModelTypeFactory and src.enemies.base_models public surface.

Spec: project_board/specs/base_models_split_by_archetype_spec.md (BMSBA-2, BMSBA-3, BMSBA-5).

Uses tests/enemies/conftest.py bpy/bmesh/mathutils stubs. Geometry and material
helpers are patched so create_model runs headless without Blender.
"""

from __future__ import annotations

import random
import unittest
from unittest.mock import MagicMock, patch

import src.enemies.base_models as bm


def _mesh_object_mock() -> MagicMock:
    obj = MagicMock()
    obj.type = "MESH"
    obj.data = MagicMock()
    obj.data.materials = []
    return obj


_MATERIAL_MAP = {"body": object(), "head": object(), "limbs": object(), "extra": object()}

_FIXED_SEED = 42
# Snapshot from current base_models geometry + rng.Random(42) (BMSBA-3.2).
_EXPECTED_PART_COUNTS = {
    "insectoid": 12,
    "blob": 6,
    "humanoid": 8,
}
# apply_themed_materials call counts on apply_material_to_object (current behavior).
_EXPECTED_APPLY_MATERIAL_CALLS = {
    "insectoid": 12,
    "blob": 6,
    "humanoid": 8,
}


class TestBaseModelsPublicExports(unittest.TestCase):
    """BMSBA-1.1 / BMSBA-2: stable names on src.enemies.base_models."""

    def test_BMSBA_EXP_01_module_exposes_required_symbols(self):
        for name in (
            "BaseModelType",
            "InsectoidModel",
            "BlobModel",
            "HumanoidModel",
            "ModelTypeFactory",
        ):
            with self.subTest(name=name):
                self.assertTrue(hasattr(bm, name), f"missing {name!r}")
                self.assertIsNotNone(getattr(bm, name))


class TestModelTypeFactoryRegistry(unittest.TestCase):
    """BMSBA-2.1, BMSBA-2.2."""

    def test_BMSBA_REG_01_model_types_keys_and_classes(self):
        mt = bm.ModelTypeFactory.MODEL_TYPES
        self.assertEqual(set(mt.keys()), {"insectoid", "blob", "humanoid"})
        self.assertIs(mt["insectoid"], bm.InsectoidModel)
        self.assertIs(mt["blob"], bm.BlobModel)
        self.assertIs(mt["humanoid"], bm.HumanoidModel)

    def test_BMSBA_REG_02_get_available_types_order(self):
        self.assertEqual(
            bm.ModelTypeFactory.get_available_types(),
            ["insectoid", "blob", "humanoid"],
        )


class TestModelTypeFactoryCreateModel(unittest.TestCase):
    """BMSBA-2.3, BMSBA-3."""

    def _patches(self):
        return patch.multiple(
            bm,
            create_sphere=MagicMock(side_effect=lambda **kwargs: _mesh_object_mock()),
            create_cylinder=MagicMock(side_effect=lambda **kwargs: _mesh_object_mock()),
            get_enemy_materials=MagicMock(return_value=_MATERIAL_MAP),
            apply_material_to_object=MagicMock(),
        )

    def test_BMSBA_CM_01_known_types_instance_and_part_counts(self):
        materials = {"a": object(), "b": object()}
        with self._patches():
            apply_mock = bm.apply_material_to_object
            for model_type, expected_n in _EXPECTED_PART_COUNTS.items():
                rng = random.Random(_FIXED_SEED)
                model = bm.ModelTypeFactory.create_model(
                    model_type, "probe_enemy", materials, rng
                )
                with self.subTest(model_type=model_type):
                    self.assertIs(
                        type(model),
                        bm.ModelTypeFactory.MODEL_TYPES[model_type],
                    )
                    self.assertGreater(len(model.parts), 0)
                    self.assertEqual(len(model.parts), expected_n)
                    self.assertEqual(model.name, "probe_enemy")
                    self.assertIs(model.materials, materials)
                    self.assertIs(model.rng, rng)
                    self.assertEqual(
                        apply_mock.call_count,
                        _EXPECTED_APPLY_MATERIAL_CALLS[model_type],
                    )
                apply_mock.reset_mock()

    def test_BMSBA_CM_02_unknown_model_type_defaults_to_insectoid(self):
        materials = {"a": object()}
        unknown_keys = ("", "unknown", "BLOB")
        with self._patches():
            for key in unknown_keys:
                rng = random.Random(_FIXED_SEED)
                model = bm.ModelTypeFactory.create_model(
                    key, "fallback_enemy", materials, rng
                )
                with self.subTest(key=key):
                    self.assertIs(type(model), bm.InsectoidModel)
                    self.assertEqual(len(model.parts), _EXPECTED_PART_COUNTS["insectoid"])

    def test_BMSBA_CM_03_unknown_matches_explicit_insectoid_same_rng(self):
        materials = {"x": object()}
        with self._patches():
            rng_a = random.Random(_FIXED_SEED)
            m_insect = bm.ModelTypeFactory.create_model(
                "insectoid", "same", materials, rng_a
            )
            rng_b = random.Random(_FIXED_SEED)
            m_unknown = bm.ModelTypeFactory.create_model(
                "not_a_real_type", "same", materials, rng_b
            )
        self.assertEqual(len(m_unknown.parts), len(m_insect.parts))


if __name__ == "__main__":
    unittest.main()
