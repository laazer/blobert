"""
Behavioral tests for ModelTypeFactory and src.enemies.base_models public surface.

Spec: project_board/specs/base_models_split_by_archetype_spec.md (BMSBA-2, BMSBA-3, BMSBA-5).

Uses tests/enemies/conftest.py bpy/bmesh/mathutils stubs. Geometry and material
helpers are patched so create_model runs headless without Blender.
"""

from __future__ import annotations

import importlib
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

    def test_BMSBA_CM_04_whitespace_and_unicode_misses_resolve_to_insectoid(self):
        """Boundary: keys that look like known types but are not exact dict hits (BMSBA-2.3)."""
        materials = {"a": object()}
        misleading = (
            " insectoid",
            "insectoid ",
            "blob\n",
            "humanoid\t",
            "insectoid\u200b",  # zero-width space suffix
        )
        with self._patches():
            for key in misleading:
                rng = random.Random(_FIXED_SEED)
                model = bm.ModelTypeFactory.create_model(
                    key, "edge", materials, rng
                )
                with self.subTest(key=repr(key)):
                    self.assertIs(type(model), bm.InsectoidModel)
                    self.assertEqual(
                        len(model.parts), _EXPECTED_PART_COUNTS["insectoid"]
                    )

    def test_BMSBA_CM_05_very_long_unknown_key_still_fallback(self):
        materials = {"a": object()}
        long_key = "x" * 8000
        with self._patches():
            rng = random.Random(_FIXED_SEED)
            model = bm.ModelTypeFactory.create_model(
                long_key, "long_key", materials, rng
            )
        self.assertIs(type(model), bm.InsectoidModel)
        self.assertEqual(len(model.parts), _EXPECTED_PART_COUNTS["insectoid"])


class TestModelTypeFactoryCaseSensitivity(unittest.TestCase):
    """BMSBA-2.3: registry keys are case-sensitive; aliases must not silently match."""

    def _patches(self):
        return patch.multiple(
            bm,
            create_sphere=MagicMock(side_effect=lambda **kwargs: _mesh_object_mock()),
            create_cylinder=MagicMock(side_effect=lambda **kwargs: _mesh_object_mock()),
            get_enemy_materials=MagicMock(return_value=_MATERIAL_MAP),
            apply_material_to_object=MagicMock(),
        )

    def test_BMSBA_CASE_01_capitalized_names_are_unknown_not_blob_or_humanoid(self):
        materials = {"a": object()}
        with self._patches():
            for wrong_key, canonical_key in (
                ("Blob", "blob"),
                ("HUMANOID", "humanoid"),
                ("Insectoid", "insectoid"),
            ):
                rng_wrong = random.Random(_FIXED_SEED)
                model_wrong = bm.ModelTypeFactory.create_model(
                    wrong_key, "case_test", materials, rng_wrong
                )
                rng_ok = random.Random(_FIXED_SEED)
                model_ok = bm.ModelTypeFactory.create_model(
                    canonical_key, "case_test", materials, rng_ok
                )
                with self.subTest(wrong_key=wrong_key):
                    self.assertIs(type(model_wrong), bm.InsectoidModel)
                    if canonical_key != "insectoid":
                        self.assertIs(
                            type(model_ok),
                            bm.ModelTypeFactory.MODEL_TYPES[canonical_key],
                        )
                        self.assertEqual(
                            len(model_ok.parts),
                            _EXPECTED_PART_COUNTS[canonical_key],
                        )
                        self.assertNotEqual(
                            len(model_wrong.parts),
                            len(model_ok.parts),
                        )
                    else:
                        self.assertIs(type(model_ok), bm.InsectoidModel)
                        self.assertEqual(
                            len(model_wrong.parts),
                            len(model_ok.parts),
                        )


class TestGetAvailableTypesContract(unittest.TestCase):
    """BMSBA-2.2 + defensive contract: callers must not mutate factory registry via return value."""

    def test_BMSBA_GAT_01_mutation_of_returned_list_does_not_alter_next_call(self):
        # CHECKPOINT: adversarial review — returned list must not alias registry keys.
        expected = ["insectoid", "blob", "humanoid"]
        first = bm.ModelTypeFactory.get_available_types()
        self.assertEqual(first, expected)
        first.append("injected")
        first.reverse()
        second = bm.ModelTypeFactory.get_available_types()
        self.assertEqual(second, expected)
        self.assertEqual(
            set(bm.ModelTypeFactory.MODEL_TYPES.keys()),
            {"insectoid", "blob", "humanoid"},
        )

    def test_BMSBA_GAT_02_repeated_calls_are_equal_and_deterministic(self):
        samples = [bm.ModelTypeFactory.get_available_types() for _ in range(32)]
        for i, s in enumerate(samples):
            with self.subTest(i=i):
                self.assertEqual(s, ["insectoid", "blob", "humanoid"])


class TestBaseModelsImportGraph(unittest.TestCase):
    """BMSBA-1.1 / BMSBA-1.3: package (or module) import succeeds without cycles."""

    def test_BMSBA_IMP_01_importlib_loads_same_module_object(self):
        # CHECKPOINT: spec import graph / no duplicate broken loaders after package split.
        mod = importlib.import_module("src.enemies.base_models")
        again = importlib.import_module("src.enemies.base_models")
        self.assertIs(mod, again)
        self.assertIs(mod.ModelTypeFactory, bm.ModelTypeFactory)

    def test_BMSBA_IMP_02_import_animated_enemies_then_base_models_succeeds(self):
        # CHECKPOINT: consumer chain must not introduce circular import (BMSBA-1.3).
        importlib.import_module("src.enemies.animated_enemies")
        mod = importlib.import_module("src.enemies.base_models")
        self.assertTrue(hasattr(mod, "ModelTypeFactory"))
        self.assertTrue(callable(mod.ModelTypeFactory.create_model))

    def test_BMSBA_IMP_03_explicit_public_imports_match_module_attributes(self):
        from src.enemies.base_models import (
            BaseModelType,
            BlobModel,
            HumanoidModel,
            InsectoidModel,
            ModelTypeFactory,
        )

        self.assertIs(BaseModelType, bm.BaseModelType)
        self.assertIs(InsectoidModel, bm.InsectoidModel)
        self.assertIs(BlobModel, bm.BlobModel)
        self.assertIs(HumanoidModel, bm.HumanoidModel)
        self.assertIs(ModelTypeFactory, bm.ModelTypeFactory)


if __name__ == "__main__":
    unittest.main()
