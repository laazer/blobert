"""
Tests for AnimatedAdhesionBug, AnimatedAcidSpitter, AnimatedClawCrawler, AnimatedCarapaceHusk.
Pure Python — no bpy import. Runs via: uv run pytest tests/

Spec traceability:
  BPG-REG-*   : TestEnemyRegistration
  BPG-CLASS-* : TestAdhesionBugClass, TestAcidSpitterClass, TestClawCrawlerClass, TestCarapaceHuskClass
  BPG-CONST-* : TestEnemyTypesConstants
  BPG-MAT-*   : TestCarapaceHuskMaterialTheme
"""

import inspect
import unittest

from src.enemies.animated_enemies import (
    AnimatedEnemyBuilder,
    AnimatedAdhesionBug,
    AnimatedAcidSpitter,
    AnimatedClawCrawler,
    AnimatedCarapaceHusk,
)
from src.enemies.base_enemy import BaseEnemy
from src.utils.constants import EnemyTypes
from src.utils.materials import MaterialThemes, MaterialColors


# ---------------------------------------------------------------------------
# BPG-REG-* : Registration
# ---------------------------------------------------------------------------

class TestEnemyRegistration(unittest.TestCase):
    """Verify all 6 enemy types are registered in AnimatedEnemyBuilder.ENEMY_CLASSES."""

    def test_BPG_REG_01_enemy_classes_has_six_entries(self):
        """BPG-REG-01: ENEMY_CLASSES contains exactly 6 keys."""
        self.assertEqual(len(AnimatedEnemyBuilder.ENEMY_CLASSES), 6)

    def test_BPG_REG_02_acid_spitter_key_present(self):
        """BPG-REG-02: 'acid_spitter' is a key in ENEMY_CLASSES."""
        self.assertIn('acid_spitter', AnimatedEnemyBuilder.ENEMY_CLASSES)

    def test_BPG_REG_03_claw_crawler_key_present(self):
        """BPG-REG-03: 'claw_crawler' is a key in ENEMY_CLASSES."""
        self.assertIn('claw_crawler', AnimatedEnemyBuilder.ENEMY_CLASSES)

    def test_BPG_REG_04_carapace_husk_key_present(self):
        """BPG-REG-04: 'carapace_husk' is a key in ENEMY_CLASSES."""
        self.assertIn('carapace_husk', AnimatedEnemyBuilder.ENEMY_CLASSES)

    def test_BPG_REG_05_acid_spitter_value_is_class(self):
        """BPG-REG-05: ENEMY_CLASSES['acid_spitter'] is a class."""
        self.assertTrue(inspect.isclass(AnimatedEnemyBuilder.ENEMY_CLASSES['acid_spitter']))

    def test_BPG_REG_06_claw_crawler_value_is_class(self):
        """BPG-REG-06: ENEMY_CLASSES['claw_crawler'] is a class."""
        self.assertTrue(inspect.isclass(AnimatedEnemyBuilder.ENEMY_CLASSES['claw_crawler']))

    def test_BPG_REG_07_carapace_husk_value_is_class(self):
        """BPG-REG-07: ENEMY_CLASSES['carapace_husk'] is a class."""
        self.assertTrue(inspect.isclass(AnimatedEnemyBuilder.ENEMY_CLASSES['carapace_husk']))

    def test_BPG_REG_08_acid_spitter_subclass_of_base_enemy(self):
        """BPG-REG-08: ENEMY_CLASSES['acid_spitter'] is a subclass of BaseEnemy."""
        self.assertTrue(issubclass(AnimatedEnemyBuilder.ENEMY_CLASSES['acid_spitter'], BaseEnemy))

    def test_BPG_REG_09_claw_crawler_subclass_of_base_enemy(self):
        """BPG-REG-09: ENEMY_CLASSES['claw_crawler'] is a subclass of BaseEnemy."""
        self.assertTrue(issubclass(AnimatedEnemyBuilder.ENEMY_CLASSES['claw_crawler'], BaseEnemy))

    def test_BPG_REG_10_carapace_husk_subclass_of_base_enemy(self):
        """BPG-REG-10: ENEMY_CLASSES['carapace_husk'] is a subclass of BaseEnemy."""
        self.assertTrue(issubclass(AnimatedEnemyBuilder.ENEMY_CLASSES['carapace_husk'], BaseEnemy))

    def test_BPG_REG_11_get_available_types_returns_six(self):
        """BPG-REG-11: get_available_types() returns a list of exactly 6 strings."""
        available = AnimatedEnemyBuilder.get_available_types()
        self.assertEqual(len(available), 6)

    def test_BPG_REG_12_get_available_types_contains_all_six_keys(self):
        """BPG-REG-12: get_available_types() contains all 6 expected type strings."""
        expected = {
            'adhesion_bug', 'tar_slug', 'ember_imp',
            'acid_spitter', 'claw_crawler', 'carapace_husk',
        }
        available = set(AnimatedEnemyBuilder.get_available_types())
        self.assertEqual(available, expected)

    def test_BPG_REG_13_adhesion_bug_key_present(self):
        """BPG-REG-13: 'adhesion_bug' is a key in ENEMY_CLASSES."""
        self.assertIn('adhesion_bug', AnimatedEnemyBuilder.ENEMY_CLASSES)

    def test_BPG_REG_14_adhesion_bug_value_is_class(self):
        """BPG-REG-14: ENEMY_CLASSES['adhesion_bug'] is a class."""
        self.assertTrue(inspect.isclass(AnimatedEnemyBuilder.ENEMY_CLASSES['adhesion_bug']))

    def test_BPG_REG_15_adhesion_bug_subclass_of_base_enemy(self):
        """BPG-REG-15: ENEMY_CLASSES['adhesion_bug'] is a subclass of BaseEnemy."""
        self.assertTrue(issubclass(AnimatedEnemyBuilder.ENEMY_CLASSES['adhesion_bug'], BaseEnemy))


# ---------------------------------------------------------------------------
# BPG-CLASS-24 through BPG-CLASS-30 : AnimatedAdhesionBug class structure
# ---------------------------------------------------------------------------

class TestAdhesionBugClass(unittest.TestCase):
    """Verify AnimatedAdhesionBug class contract via introspection."""

    def test_BPG_CLASS_24_adhesion_bug_importable(self):
        """BPG-CLASS-24: AnimatedAdhesionBug is importable from src.enemies.animated_enemies."""
        self.assertTrue(True)

    def test_BPG_CLASS_25_adhesion_bug_defined_in_dedicated_module(self):
        """BPG-CLASS-25: AnimatedAdhesionBug class object lives in animated_adhesion_bug module."""
        self.assertEqual(AnimatedAdhesionBug.__module__, 'src.enemies.animated_adhesion_bug')

    def test_BPG_CLASS_26_adhesion_bug_subclass_of_base_enemy(self):
        """BPG-CLASS-26: AnimatedAdhesionBug is a subclass of BaseEnemy."""
        self.assertTrue(issubclass(AnimatedAdhesionBug, BaseEnemy))

    def test_BPG_CLASS_27_has_all_required_methods(self):
        """BPG-CLASS-27: AnimatedAdhesionBug defines all 6 required methods."""
        required = ['create_body', 'create_head', 'create_limbs',
                    'apply_materials', 'create_armature', 'get_body_type']
        for method_name in required:
            with self.subTest(method=method_name):
                self.assertTrue(hasattr(AnimatedAdhesionBug, method_name))
                self.assertTrue(callable(getattr(AnimatedAdhesionBug, method_name)))

    def test_BPG_CLASS_28_get_body_type_source_references_quadruped(self):
        """BPG-CLASS-28: get_body_type source contains EnemyBodyTypes.QUADRUPED."""
        source = inspect.getsource(AnimatedAdhesionBug.get_body_type)
        self.assertIn('EnemyBodyTypes.QUADRUPED', source)

    def test_BPG_CLASS_29_create_armature_source_references_create_quadruped_armature(self):
        """BPG-CLASS-29: create_armature source contains create_quadruped_armature."""
        source = inspect.getsource(AnimatedAdhesionBug.create_armature)
        self.assertIn('create_quadruped_armature', source)

    def test_BPG_CLASS_30_apply_materials_source_references_adhesion_bug_key(self):
        """BPG-CLASS-30: apply_materials source contains 'adhesion_bug' string literal."""
        source = inspect.getsource(AnimatedAdhesionBug.apply_materials)
        self.assertIn("'adhesion_bug'", source)


# ---------------------------------------------------------------------------
# BPG-CLASS-01 through BPG-CLASS-11 : AnimatedAcidSpitter class structure
# ---------------------------------------------------------------------------

class TestAcidSpitterClass(unittest.TestCase):
    """Verify AnimatedAcidSpitter class contract via introspection."""

    def test_BPG_CLASS_01_acid_spitter_importable(self):
        """BPG-CLASS-01: AnimatedAcidSpitter is importable from src.enemies.animated_enemies."""
        # Import at module level above; reaching this line proves the import succeeded.
        self.assertTrue(True)

    def test_BPG_CLASS_01b_acid_spitter_defined_in_dedicated_module(self):
        """BPG-CLASS-01b: AnimatedAcidSpitter class object lives in animated_acid_spitter module."""
        self.assertEqual(AnimatedAcidSpitter.__module__, 'src.enemies.animated_acid_spitter')

    def test_BPG_CLASS_02_acid_spitter_subclass_of_base_enemy(self):
        """BPG-CLASS-02: AnimatedAcidSpitter is a subclass of BaseEnemy."""
        self.assertTrue(issubclass(AnimatedAcidSpitter, BaseEnemy))

    def test_BPG_CLASS_03_has_create_body(self):
        """BPG-CLASS-03: AnimatedAcidSpitter defines create_body."""
        self.assertTrue(hasattr(AnimatedAcidSpitter, 'create_body'))
        self.assertTrue(callable(getattr(AnimatedAcidSpitter, 'create_body')))

    def test_BPG_CLASS_04_has_create_head(self):
        """BPG-CLASS-04: AnimatedAcidSpitter defines create_head."""
        self.assertTrue(hasattr(AnimatedAcidSpitter, 'create_head'))
        self.assertTrue(callable(getattr(AnimatedAcidSpitter, 'create_head')))

    def test_BPG_CLASS_05_has_create_limbs(self):
        """BPG-CLASS-05: AnimatedAcidSpitter defines create_limbs."""
        self.assertTrue(hasattr(AnimatedAcidSpitter, 'create_limbs'))
        self.assertTrue(callable(getattr(AnimatedAcidSpitter, 'create_limbs')))

    def test_BPG_CLASS_06_has_apply_materials(self):
        """BPG-CLASS-06: AnimatedAcidSpitter defines apply_materials."""
        self.assertTrue(hasattr(AnimatedAcidSpitter, 'apply_materials'))
        self.assertTrue(callable(getattr(AnimatedAcidSpitter, 'apply_materials')))

    def test_BPG_CLASS_07_has_create_armature(self):
        """BPG-CLASS-07: AnimatedAcidSpitter defines create_armature."""
        self.assertTrue(hasattr(AnimatedAcidSpitter, 'create_armature'))
        self.assertTrue(callable(getattr(AnimatedAcidSpitter, 'create_armature')))

    def test_BPG_CLASS_08_has_get_body_type(self):
        """BPG-CLASS-08: AnimatedAcidSpitter defines get_body_type."""
        self.assertTrue(hasattr(AnimatedAcidSpitter, 'get_body_type'))
        self.assertTrue(callable(getattr(AnimatedAcidSpitter, 'get_body_type')))

    def test_BPG_CLASS_09_get_body_type_source_references_blob(self):
        """BPG-CLASS-09: get_body_type source contains EnemyBodyTypes.BLOB."""
        source = inspect.getsource(AnimatedAcidSpitter.get_body_type)
        self.assertIn('EnemyBodyTypes.BLOB', source)

    def test_BPG_CLASS_10_create_armature_source_references_create_blob_armature(self):
        """BPG-CLASS-10: create_armature source contains create_blob_armature."""
        source = inspect.getsource(AnimatedAcidSpitter.create_armature)
        self.assertIn('create_blob_armature', source)

    def test_BPG_CLASS_11_apply_materials_source_references_acid_spitter_key(self):
        """BPG-CLASS-11: apply_materials source contains 'acid_spitter' string literal."""
        source = inspect.getsource(AnimatedAcidSpitter.apply_materials)
        self.assertIn("'acid_spitter'", source)


# ---------------------------------------------------------------------------
# BPG-CLASS-12 through BPG-CLASS-17 : AnimatedClawCrawler class structure
# ---------------------------------------------------------------------------

class TestClawCrawlerClass(unittest.TestCase):
    """Verify AnimatedClawCrawler class contract via introspection."""

    def test_BPG_CLASS_12_claw_crawler_importable(self):
        """BPG-CLASS-12: AnimatedClawCrawler is importable from src.enemies.animated_enemies."""
        self.assertTrue(True)

    def test_BPG_CLASS_13_claw_crawler_subclass_of_base_enemy(self):
        """BPG-CLASS-13: AnimatedClawCrawler is a subclass of BaseEnemy."""
        self.assertTrue(issubclass(AnimatedClawCrawler, BaseEnemy))

    def test_BPG_CLASS_14_has_all_required_methods(self):
        """BPG-CLASS-14: AnimatedClawCrawler defines all 6 required methods."""
        required = ['create_body', 'create_head', 'create_limbs',
                    'apply_materials', 'create_armature', 'get_body_type']
        for method_name in required:
            with self.subTest(method=method_name):
                self.assertTrue(hasattr(AnimatedClawCrawler, method_name))
                self.assertTrue(callable(getattr(AnimatedClawCrawler, method_name)))

    def test_BPG_CLASS_15_get_body_type_source_references_quadruped(self):
        """BPG-CLASS-15: get_body_type source contains EnemyBodyTypes.QUADRUPED."""
        source = inspect.getsource(AnimatedClawCrawler.get_body_type)
        self.assertIn('EnemyBodyTypes.QUADRUPED', source)

    def test_BPG_CLASS_16_create_armature_source_references_create_quadruped_armature(self):
        """BPG-CLASS-16: create_armature source contains create_quadruped_armature."""
        source = inspect.getsource(AnimatedClawCrawler.create_armature)
        self.assertIn('create_quadruped_armature', source)

    def test_BPG_CLASS_17_apply_materials_source_references_claw_crawler_key(self):
        """BPG-CLASS-17: apply_materials source contains 'claw_crawler' string literal."""
        source = inspect.getsource(AnimatedClawCrawler.apply_materials)
        self.assertIn("'claw_crawler'", source)


# ---------------------------------------------------------------------------
# BPG-CLASS-18 through BPG-CLASS-23 : AnimatedCarapaceHusk class structure
# ---------------------------------------------------------------------------

class TestCarapaceHuskClass(unittest.TestCase):
    """Verify AnimatedCarapaceHusk class contract via introspection."""

    def test_BPG_CLASS_18_carapace_husk_importable(self):
        """BPG-CLASS-18: AnimatedCarapaceHusk is importable from src.enemies.animated_enemies."""
        self.assertTrue(True)

    def test_BPG_CLASS_19_carapace_husk_subclass_of_base_enemy(self):
        """BPG-CLASS-19: AnimatedCarapaceHusk is a subclass of BaseEnemy."""
        self.assertTrue(issubclass(AnimatedCarapaceHusk, BaseEnemy))

    def test_BPG_CLASS_20_has_all_required_methods(self):
        """BPG-CLASS-20: AnimatedCarapaceHusk defines all 6 required methods."""
        required = ['create_body', 'create_head', 'create_limbs',
                    'apply_materials', 'create_armature', 'get_body_type']
        for method_name in required:
            with self.subTest(method=method_name):
                self.assertTrue(hasattr(AnimatedCarapaceHusk, method_name))
                self.assertTrue(callable(getattr(AnimatedCarapaceHusk, method_name)))

    def test_BPG_CLASS_21_get_body_type_source_references_humanoid(self):
        """BPG-CLASS-21: get_body_type source contains EnemyBodyTypes.HUMANOID."""
        source = inspect.getsource(AnimatedCarapaceHusk.get_body_type)
        self.assertIn('EnemyBodyTypes.HUMANOID', source)

    def test_BPG_CLASS_22_create_armature_source_references_create_humanoid_armature(self):
        """BPG-CLASS-22: create_armature source contains create_humanoid_armature."""
        source = inspect.getsource(AnimatedCarapaceHusk.create_armature)
        self.assertIn('create_humanoid_armature', source)

    def test_BPG_CLASS_23_apply_materials_source_references_carapace_husk_key(self):
        """BPG-CLASS-23: apply_materials source contains 'carapace_husk' string literal."""
        source = inspect.getsource(AnimatedCarapaceHusk.apply_materials)
        self.assertIn("'carapace_husk'", source)


# ---------------------------------------------------------------------------
# BPG-CONST-* : EnemyTypes constants
# ---------------------------------------------------------------------------

class TestEnemyTypesConstants(unittest.TestCase):
    """Verify EnemyTypes constant additions and reclassification."""

    def test_BPG_CONST_01_carapace_husk_constant_value(self):
        """BPG-CONST-01: EnemyTypes.CARAPACE_HUSK == 'carapace_husk'."""
        self.assertEqual(EnemyTypes.CARAPACE_HUSK, "carapace_husk")

    def test_BPG_CONST_02_get_animated_returns_six(self):
        """BPG-CONST-02: EnemyTypes.get_animated() returns exactly 6 items."""
        self.assertEqual(len(EnemyTypes.get_animated()), 6)

    def test_BPG_CONST_03_acid_spitter_in_animated(self):
        """BPG-CONST-03: 'acid_spitter' is in EnemyTypes.get_animated()."""
        self.assertIn("acid_spitter", EnemyTypes.get_animated())

    def test_BPG_CONST_04_claw_crawler_in_animated(self):
        """BPG-CONST-04: 'claw_crawler' is in EnemyTypes.get_animated()."""
        self.assertIn("claw_crawler", EnemyTypes.get_animated())

    def test_BPG_CONST_05_carapace_husk_in_animated(self):
        """BPG-CONST-05: 'carapace_husk' is in EnemyTypes.get_animated()."""
        self.assertIn("carapace_husk", EnemyTypes.get_animated())

    def test_BPG_CONST_06_get_static_returns_five(self):
        """BPG-CONST-06: EnemyTypes.get_static() returns exactly 5 items."""
        self.assertEqual(len(EnemyTypes.get_static()), 5)

    def test_BPG_CONST_07_acid_spitter_not_in_static(self):
        """BPG-CONST-07: 'acid_spitter' is NOT in EnemyTypes.get_static()."""
        self.assertNotIn("acid_spitter", EnemyTypes.get_static())

    def test_BPG_CONST_08_claw_crawler_not_in_static(self):
        """BPG-CONST-08: 'claw_crawler' is NOT in EnemyTypes.get_static()."""
        self.assertNotIn("claw_crawler", EnemyTypes.get_static())

    def test_BPG_CONST_09_get_all_returns_eleven(self):
        """BPG-CONST-09: EnemyTypes.get_all() returns exactly 11 items."""
        self.assertEqual(len(EnemyTypes.get_all()), 11)

    def test_BPG_CONST_10_animated_and_static_are_disjoint(self):
        """BPG-CONST-10: get_animated() and get_static() share no values."""
        animated = set(EnemyTypes.get_animated())
        static = set(EnemyTypes.get_static())
        self.assertTrue(animated.isdisjoint(static))


# ---------------------------------------------------------------------------
# BPG-MAT-* : carapace_husk material theme
# ---------------------------------------------------------------------------

class TestCarapaceHuskMaterialTheme(unittest.TestCase):
    """Verify carapace_husk entry in MaterialThemes.ENEMY_THEMES."""

    def test_BPG_MAT_01_carapace_husk_key_exists(self):
        """BPG-MAT-01: 'carapace_husk' is a key in MaterialThemes.ENEMY_THEMES."""
        self.assertIn('carapace_husk', MaterialThemes.ENEMY_THEMES)

    def test_BPG_MAT_02_theme_is_list_of_three(self):
        """BPG-MAT-02: carapace_husk theme is a list of exactly 3 strings."""
        theme = MaterialThemes.ENEMY_THEMES['carapace_husk']
        self.assertIsInstance(theme, list)
        self.assertEqual(len(theme), 3)

    def test_BPG_MAT_03_first_entry_is_stone_gray(self):
        """BPG-MAT-03: carapace_husk theme[0] == 'stone_gray'."""
        self.assertEqual(MaterialThemes.ENEMY_THEMES['carapace_husk'][0], "stone_gray")

    def test_BPG_MAT_04_second_entry_is_bone_white(self):
        """BPG-MAT-04: carapace_husk theme[1] == 'bone_white'."""
        self.assertEqual(MaterialThemes.ENEMY_THEMES['carapace_husk'][1], "bone_white")

    def test_BPG_MAT_05_third_entry_is_chrome_silver(self):
        """BPG-MAT-05: carapace_husk theme[2] == 'chrome_silver'."""
        self.assertEqual(MaterialThemes.ENEMY_THEMES['carapace_husk'][2], "chrome_silver")

    def test_BPG_MAT_06_has_theme_returns_true(self):
        """BPG-MAT-06: MaterialThemes.has_theme('carapace_husk') is True."""
        self.assertTrue(MaterialThemes.has_theme('carapace_husk'))

    def test_BPG_MAT_07_get_theme_matches_enemy_themes_entry(self):
        """BPG-MAT-07: get_theme('carapace_husk') returns same list as ENEMY_THEMES entry."""
        self.assertEqual(
            MaterialThemes.get_theme('carapace_husk'),
            ["stone_gray", "bone_white", "chrome_silver"],
        )

    def test_BPG_MAT_08_all_three_colors_are_recognised_material_names(self):
        """BPG-MAT-08: All three theme strings are valid keys in MaterialColors.get_all()."""
        known_colors = MaterialColors.get_all()
        theme = MaterialThemes.ENEMY_THEMES['carapace_husk']
        for color_name in theme:
            with self.subTest(color=color_name):
                self.assertIn(color_name, known_colors,
                              f"'{color_name}' is not a recognised MaterialColors key")


if __name__ == '__main__':
    unittest.main()
