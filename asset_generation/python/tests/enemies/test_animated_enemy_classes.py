"""
Tests for animated enemy classes (registration, structure, constants, materials).
Pure Python — no bpy import.
"""

import inspect
import unittest

from src.enemies.animated import (
    AnimatedCarapaceHusk,
    AnimatedClawCrawler,
    AnimatedEnemyBuilder,
    AnimatedImp,
    AnimatedSlug,
    AnimatedSpider,
    AnimatedSpitter,
)
from src.enemies.animated_enemy import AnimatedEnemy
from src.enemies.base_enemy import BaseEnemy
from src.utils.constants import EnemyTypes
from src.utils.materials import MaterialThemes

_ALL_ANIMATED = (
    AnimatedSpider,
    AnimatedSpitter,
    AnimatedClawCrawler,
    AnimatedImp,
    AnimatedSlug,
    AnimatedCarapaceHusk,
)


class TestEnemyRegistration(unittest.TestCase):
    def test_BPG_REG_01_enemy_classes_has_six_entries(self):
        self.assertEqual(len(AnimatedEnemyBuilder.ENEMY_CLASSES), 6)

    def test_BPG_REG_08_acid_subclass_of_base_and_animated(self):
        self.assertTrue(issubclass(AnimatedEnemyBuilder.ENEMY_CLASSES["spitter"], BaseEnemy))
        self.assertTrue(issubclass(AnimatedEnemyBuilder.ENEMY_CLASSES["spitter"], AnimatedEnemy))

    def test_BPG_REG_11_get_available_types_returns_six(self):
        self.assertEqual(len(AnimatedEnemyBuilder.get_available_types()), 6)


class TestAnimatedEnemyClassContract(unittest.TestCase):
    """Each concrete enemy implements mesh + rig + body type."""

    def test_each_defines_build_mesh_parts_and_get_rig(self):
        required_own = ("build_mesh_parts", "get_rig_definition", "apply_themed_materials", "get_body_type")
        for cls in _ALL_ANIMATED:
            with self.subTest(cls=cls.__name__):
                for name in required_own:
                    self.assertIn(name, cls.__dict__, f"{cls.__name__} must define {name}")
                self.assertTrue(issubclass(cls, AnimatedEnemy))

    def test_armature_slug_via_self_name(self):
        src = inspect.getsource(AnimatedEnemy.create_armature)
        self.assertIn("self.name", src)
        self.assertIn("get_rig_definition", src)

    def test_get_rig_uses_typed_helper(self):
        rig_helpers = (
            "rig_from_bone_map",
            "humanoid_simple_rig_definition",
            "quadruped_simple_rig_definition",
        )
        for cls in _ALL_ANIMATED:
            with self.subTest(cls=cls.__name__):
                gsrc = inspect.getsource(cls.get_rig_definition)
                self.assertTrue(
                    any(h in gsrc for h in rig_helpers),
                    f"{cls.__name__}.get_rig_definition must delegate via {rig_helpers}",
                )


class TestEnemyTypesConstants(unittest.TestCase):
    def test_BPG_CONST_02_get_animated_returns_six(self):
        self.assertEqual(len(EnemyTypes.get_animated()), 6)

    def test_BPG_CONST_10_animated_and_static_disjoint(self):
        animated = set(EnemyTypes.get_animated())
        static = set(EnemyTypes.get_static())
        self.assertTrue(animated.isdisjoint(static))


class TestCarapaceHuskMaterialTheme(unittest.TestCase):
    def test_BPG_MAT_01_carapace_husk_key_exists(self):
        self.assertIn("carapace_husk", MaterialThemes.ENEMY_THEMES)

    def test_BPG_MAT_07_get_theme_matches(self):
        self.assertEqual(
            MaterialThemes.get_theme("carapace_husk"),
            ["stone_gray", "bone_white", "chrome_silver"],
        )


if __name__ == "__main__":
    unittest.main()
