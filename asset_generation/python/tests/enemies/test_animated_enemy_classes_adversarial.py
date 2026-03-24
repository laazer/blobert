"""
Adversarial tests for AnimatedAcidSpitter, AnimatedClawCrawler, AnimatedCarapaceHusk.
Pure Python — no bpy import. Runs via: uv run pytest tests/

These tests target structural invariants and mutation surfaces NOT covered by
the primary suite (test_animated_enemy_classes.py). Each test documents which
gap or mutation it defends against.

Spec traceability prefix:
  BPG-ADV-REG-*   : Registration adversarial
  BPG-ADV-CONST-* : Constants adversarial
  BPG-ADV-MAT-*   : Material theme adversarial
  BPG-ADV-CLASS-* : Class structure adversarial
"""

import inspect
import unittest

from src.enemies.animated_enemies import (
    AnimatedEnemyBuilder,
    AnimatedAcidSpitter,
    AnimatedClawCrawler,
    AnimatedCarapaceHusk,
    AnimatedAdhesionBug,
    AnimatedTarSlug,
    AnimatedEmberImp,
)
from src.enemies.base_enemy import BaseEnemy
from src.utils.constants import EnemyTypes
from src.utils.materials import MaterialThemes


# ---------------------------------------------------------------------------
# BPG-ADV-REG-* : Registration adversarial
# ---------------------------------------------------------------------------

class TestRegistrationAdversarial(unittest.TestCase):
    """
    Adversarial registration tests. The primary suite checks presence and
    subclass relationships but misses:
      - dict value aliasing (two keys → same class object)
      - key type invariants (non-string keys would silently pass lookup)
      - the 3 new keys being distinct from each other (not aliased strings)
      - get_available_types() returning a list, not a set or generator
    """

    def test_BPG_ADV_REG_01_no_two_enemy_classes_values_share_same_class_object(self):
        """
        BPG-ADV-REG-01: No two keys in ENEMY_CLASSES map to the same class object.

        Mutation surface: A developer could accidentally write
            'acid_spitter': AnimatedAcidSpitter,
            'claw_crawler': AnimatedAcidSpitter,   # copy-paste error
        The primary suite only checks each key individually — it never checks
        that the VALUES are all distinct objects.
        """
        classes = list(AnimatedEnemyBuilder.ENEMY_CLASSES.values())
        # id() uniqueness covers the 'same class object' case; since classes
        # are defined at module level, two entries pointing to the same class
        # will have the same id().
        unique_ids = {id(cls) for cls in classes}
        self.assertEqual(
            len(unique_ids),
            len(classes),
            "Two or more ENEMY_CLASSES keys map to the same class object — "
            "likely a copy-paste registration error.",
        )

    def test_BPG_ADV_REG_02_all_enemy_classes_keys_are_str(self):
        """
        BPG-ADV-REG-02: Every key in ENEMY_CLASSES is a str instance.

        Mutation surface: A None key or integer key would not raise on dict
        construction but would silently break lookup by string type. The
        primary suite checks value types, not key types.
        """
        for key in AnimatedEnemyBuilder.ENEMY_CLASSES.keys():
            with self.subTest(key=key):
                self.assertIsInstance(
                    key,
                    str,
                    f"ENEMY_CLASSES contains a non-string key: {key!r}",
                )

    def test_BPG_ADV_REG_03_no_none_key_in_enemy_classes(self):
        """
        BPG-ADV-REG-03: None is not a key in ENEMY_CLASSES.

        Mutation surface: Explicit check because None is a commonly introduced
        sentinel during draft implementations, and assertIsInstance(None, str)
        would fail with a confusing message — this gives a direct failure.
        """
        self.assertNotIn(None, AnimatedEnemyBuilder.ENEMY_CLASSES)

    def test_BPG_ADV_REG_04_three_new_key_strings_are_mutually_distinct(self):
        """
        BPG-ADV-REG-04: The 3 new key strings are all different from each other.

        Mutation surface: If an implementor re-used the same string literal for
        two registrations (e.g. both 'acid_spitter' entries), Python dicts deduplicate
        silently — the count test in the primary suite catches the final count but
        would only fail if count != 6. This test directly asserts distinctness.
        """
        new_keys = ['acid_spitter', 'claw_crawler', 'carapace_husk']
        self.assertEqual(
            len(set(new_keys)),
            3,
            "The 3 new key literals are not all distinct — internal spec error.",
        )
        # Now verify the actual dict keys match the distinct set
        registered = set(AnimatedEnemyBuilder.ENEMY_CLASSES.keys())
        for k in new_keys:
            self.assertIn(k, registered)

    def test_BPG_ADV_REG_05_get_available_types_returns_list_not_set_or_generator(self):
        """
        BPG-ADV-REG-05: get_available_types() returns a list, not a set or generator.

        Mutation surface: Returning set(ENEMY_CLASSES.keys()) or a generator
        expression would satisfy the primary suite's len() and set-equality checks
        while breaking downstream consumers that depend on list semantics (indexing,
        JSON serialization, iteration order).
        """
        result = AnimatedEnemyBuilder.get_available_types()
        self.assertIsInstance(
            result,
            list,
            f"get_available_types() returned {type(result).__name__}, expected list.",
        )

    def test_BPG_ADV_REG_06_get_available_types_is_stable_across_two_calls(self):
        """
        BPG-ADV-REG-06: get_available_types() returns identical lists on consecutive calls.

        Mutation surface: A non-deterministic implementation (e.g. using
        dict.keys() on a Python version < 3.7, or randomising output) would
        produce different ordering. The primary suite only calls it once.
        """
        first = AnimatedEnemyBuilder.get_available_types()
        second = AnimatedEnemyBuilder.get_available_types()
        self.assertEqual(
            first,
            second,
            "get_available_types() returns a different order on two consecutive calls.",
        )

    def test_BPG_ADV_REG_07_enemy_classes_values_are_all_classes_not_instances(self):
        """
        BPG-ADV-REG-07: No value in ENEMY_CLASSES is an instance; all are class objects.

        Mutation surface: An implementor might accidentally write
            'acid_spitter': AnimatedAcidSpitter(...),   # instantiated, not the class
        inspect.isclass() handles this, but the primary suite only checks the
        three new keys — it does not guard the existing three keys.
        This test covers all 6.
        """
        for key, value in AnimatedEnemyBuilder.ENEMY_CLASSES.items():
            with self.subTest(key=key):
                self.assertTrue(
                    inspect.isclass(value),
                    f"ENEMY_CLASSES[{key!r}] is {value!r}, not a class.",
                )


# ---------------------------------------------------------------------------
# BPG-ADV-CONST-* : Constants adversarial
# ---------------------------------------------------------------------------

class TestConstantsAdversarial(unittest.TestCase):
    """
    Adversarial tests for EnemyTypes constants. The primary suite checks counts
    and membership but misses:
      - get_animated() returning a list (not a set/generator)
      - carapace_husk is absent from get_static() at the same time it is in get_animated()
      - get_animated() + get_static() union exactly equals get_all() (no extras/omissions)
      - order stability of get_animated()
      - no duplicate entries in get_animated() or get_all()
    """

    def test_BPG_ADV_CONST_01_get_animated_returns_list_not_set_or_generator(self):
        """
        BPG-ADV-CONST-01: EnemyTypes.get_animated() returns a list.

        Mutation surface: Returning a set or frozenset would pass the primary
        suite's len() and 'in' membership tests but break any consumer that
        expects ordered, indexable output.
        """
        result = EnemyTypes.get_animated()
        self.assertIsInstance(
            result,
            list,
            f"get_animated() returned {type(result).__name__}, expected list.",
        )

    def test_BPG_ADV_CONST_02_get_static_returns_list_not_set_or_generator(self):
        """
        BPG-ADV-CONST-02: EnemyTypes.get_static() returns a list.

        Same mutation surface as CONST-01. Primary suite never checks the
        return type of get_static().
        """
        result = EnemyTypes.get_static()
        self.assertIsInstance(
            result,
            list,
            f"get_static() returned {type(result).__name__}, expected list.",
        )

    def test_BPG_ADV_CONST_03_get_all_returns_list_not_set_or_generator(self):
        """
        BPG-ADV-CONST-03: EnemyTypes.get_all() returns a list.

        Same mutation surface.
        """
        result = EnemyTypes.get_all()
        self.assertIsInstance(
            result,
            list,
            f"get_all() returned {type(result).__name__}, expected list.",
        )

    def test_BPG_ADV_CONST_04_carapace_husk_in_animated_and_not_in_static_simultaneously(self):
        """
        BPG-ADV-CONST-04: carapace_husk appears in get_animated() AND is absent
        from get_static() in the same assertion chain.

        Mutation surface: An implementor could add 'carapace_husk' to get_animated()
        while forgetting to remove it from get_static(), making both contain it.
        The primary suite tests each condition independently — this test enforces
        both in one atomic assertion so neither side can be independently patched.
        """
        animated = EnemyTypes.get_animated()
        static = EnemyTypes.get_static()
        in_animated = "carapace_husk" in animated
        not_in_static = "carapace_husk" not in static
        self.assertTrue(
            in_animated and not_in_static,
            f"carapace_husk presence: animated={in_animated}, absent-from-static={not_in_static}. "
            "Both must be True simultaneously.",
        )

    def test_BPG_ADV_CONST_05_get_animated_union_get_static_equals_get_all_exactly(self):
        """
        BPG-ADV-CONST-05: set(get_animated()) | set(get_static()) == set(get_all()).

        Mutation surface: get_all() could include extra types not in either
        sub-list, or miss types present in the sub-lists. The primary suite
        checks individual counts (6 animated, 5 static, 11 all) but does not
        check that the union equals get_all() with no extras or gaps.
        """
        animated = set(EnemyTypes.get_animated())
        static = set(EnemyTypes.get_static())
        all_types = set(EnemyTypes.get_all())
        union = animated | static

        extras_in_all = all_types - union
        missing_from_all = union - all_types

        self.assertEqual(
            extras_in_all,
            set(),
            f"get_all() contains items not in get_animated()|get_static(): {extras_in_all}",
        )
        self.assertEqual(
            missing_from_all,
            set(),
            f"get_all() is missing items present in get_animated()|get_static(): {missing_from_all}",
        )

    def test_BPG_ADV_CONST_06_get_animated_has_no_duplicate_entries(self):
        """
        BPG-ADV-CONST-06: get_animated() contains no duplicate string values.

        Mutation surface: A careless implementation could append the same
        constant twice (e.g. 'adhesion_bug' listed twice). The primary suite
        checks len() == 6 — if there are two 'acid_spitter' entries replacing
        one expected entry, the count is still 6 but the type is missing.
        """
        animated = EnemyTypes.get_animated()
        self.assertEqual(
            len(animated),
            len(set(animated)),
            f"get_animated() contains duplicate entries: {animated}",
        )

    def test_BPG_ADV_CONST_07_get_all_has_no_duplicate_entries(self):
        """
        BPG-ADV-CONST-07: get_all() contains no duplicate string values.

        Mutation surface: If get_all() is implemented as get_animated() +
        get_static() and both lists mistakenly share an entry, duplicates
        appear. This was previously guarded only by disjoint check in the
        primary suite — but disjoint does not prevent duplicates within
        a single sub-list.
        """
        all_types = EnemyTypes.get_all()
        self.assertEqual(
            len(all_types),
            len(set(all_types)),
            f"get_all() contains duplicate entries: {all_types}",
        )

    def test_BPG_ADV_CONST_08_get_animated_order_is_stable_across_two_calls(self):
        """
        BPG-ADV-CONST-08: get_animated() returns the same list in the same order
        on consecutive calls.

        Mutation surface: A set-based or randomised implementation would pass
        membership and count checks while breaking determinism required for
        reproducible GLB generation.
        """
        first = EnemyTypes.get_animated()
        second = EnemyTypes.get_animated()
        self.assertEqual(
            first,
            second,
            "get_animated() returns a different order on two consecutive calls.",
        )

    def test_BPG_ADV_CONST_09_carapace_husk_constant_attribute_exists_on_class(self):
        """
        BPG-ADV-CONST-09: EnemyTypes.CARAPACE_HUSK attribute exists as a class-level
        attribute (not only inlined inside get_animated()).

        Mutation surface: An implementor could inline 'carapace_husk' as a literal
        inside get_animated() without defining the class constant. The primary suite
        checks the value via EnemyTypes.CARAPACE_HUSK — but only after the import
        succeeds, which is true regardless of whether the attribute is used in the
        method or if the method hardcodes the string.
        This test verifies the attribute is accessible as EnemyTypes.CARAPACE_HUSK
        and that get_animated() actually contains that attribute's value (not just
        the literal string 'carapace_husk').
        """
        carapace_husk_value = EnemyTypes.CARAPACE_HUSK
        self.assertIn(
            carapace_husk_value,
            EnemyTypes.get_animated(),
            "EnemyTypes.get_animated() does not contain the value of "
            "EnemyTypes.CARAPACE_HUSK — the constant and the method may be out of sync.",
        )

    def test_BPG_ADV_CONST_10_acid_spitter_constant_attribute_value_in_animated(self):
        """
        BPG-ADV-CONST-10: EnemyTypes.ACID_SPITTER attribute value appears in get_animated().

        Mutation surface: The constant value could be updated without updating
        get_animated(), so the attribute and method would be out of sync.
        """
        self.assertIn(
            EnemyTypes.ACID_SPITTER,
            EnemyTypes.get_animated(),
            "EnemyTypes.get_animated() does not contain EnemyTypes.ACID_SPITTER value.",
        )

    def test_BPG_ADV_CONST_11_claw_crawler_constant_attribute_value_in_animated(self):
        """
        BPG-ADV-CONST-11: EnemyTypes.CLAW_CRAWLER attribute value appears in get_animated().

        Same mutation surface as CONST-10.
        """
        self.assertIn(
            EnemyTypes.CLAW_CRAWLER,
            EnemyTypes.get_animated(),
            "EnemyTypes.get_animated() does not contain EnemyTypes.CLAW_CRAWLER value.",
        )


# ---------------------------------------------------------------------------
# BPG-ADV-MAT-* : Material theme adversarial
# ---------------------------------------------------------------------------

class TestCarapaceHuskMaterialThemeAdversarial(unittest.TestCase):
    """
    Adversarial tests for carapace_husk material theme. The primary suite
    checks exact string values and recognisability but misses:
      - duplicate entries within the theme list
      - theme list mutability (shared reference risk)
      - the theme list being exactly 3 elements (not more via accidental append)
    """

    def test_BPG_ADV_MAT_01_carapace_husk_theme_has_no_duplicate_entries(self):
        """
        BPG-ADV-MAT-01: MaterialThemes.ENEMY_THEMES['carapace_husk'] contains
        no duplicate strings.

        Mutation surface: An implementor writing
            'carapace_husk': ['stone_gray', 'stone_gray', 'chrome_silver']
        would pass BPG-MAT-03 (checks index 0) and BPG-MAT-05 (checks index 2)
        but the duplicate 'stone_gray' at index 1 would go undetected because
        BPG-MAT-04 only checks that theme[1] == 'bone_white'. If the value is
        wrong AND a duplicate, BPG-MAT-04 catches the wrong value but not the
        structural duplicate invariant.
        This test guards the structural invariant independently.
        """
        theme = MaterialThemes.ENEMY_THEMES['carapace_husk']
        self.assertEqual(
            len(theme),
            len(set(theme)),
            f"carapace_husk theme contains duplicate entries: {theme}",
        )

    def test_BPG_ADV_MAT_02_carapace_husk_theme_is_exactly_three_elements(self):
        """
        BPG-ADV-MAT-02: The carapace_husk theme list has exactly 3 elements.

        The primary suite checks len == 3 in BPG-MAT-02; this test adds an
        explicit upper-bound guard so that a 4-element theme (accidental extra
        append) is caught even if an unrelated refactor changes the check.
        """
        theme = MaterialThemes.ENEMY_THEMES['carapace_husk']
        self.assertLessEqual(len(theme), 3, "carapace_husk theme has more than 3 entries.")
        self.assertGreaterEqual(len(theme), 3, "carapace_husk theme has fewer than 3 entries.")

    def test_BPG_ADV_MAT_03_get_theme_returns_same_content_as_direct_dict_access(self):
        """
        BPG-ADV-MAT-03: MaterialThemes.get_theme('carapace_husk') content equals
        MaterialThemes.ENEMY_THEMES['carapace_husk'] content.

        Mutation surface: get_theme() could have special-case logic that returns
        a different list than the dict entry, or could apply a transformation.
        The primary suite's BPG-MAT-07 checks the final expected value but does
        not verify equivalence to the direct dict access path.
        """
        via_method = MaterialThemes.get_theme('carapace_husk')
        via_dict = MaterialThemes.ENEMY_THEMES['carapace_husk']
        self.assertEqual(
            via_method,
            via_dict,
            "get_theme('carapace_husk') returns different content than "
            "ENEMY_THEMES['carapace_husk'] direct access.",
        )

    def test_BPG_ADV_MAT_04_existing_themes_not_overwritten_by_carapace_husk_addition(self):
        """
        BPG-ADV-MAT-04: The pre-existing themes for acid_spitter and claw_crawler
        are still present and unmodified after carapace_husk is added.

        Mutation surface: A materials.py edit that adds carapace_husk could
        accidentally overwrite an existing entry if using a dict update rather
        than a literal entry. No primary suite test verifies the pre-existing
        entries are intact.
        """
        # acid_spitter pre-existing theme
        acid_theme = MaterialThemes.ENEMY_THEMES.get('acid_spitter')
        self.assertIsNotNone(acid_theme, "acid_spitter theme has been removed from ENEMY_THEMES.")
        self.assertEqual(len(acid_theme), 3, "acid_spitter theme should have 3 entries.")

        # claw_crawler pre-existing theme
        claw_theme = MaterialThemes.ENEMY_THEMES.get('claw_crawler')
        self.assertIsNotNone(claw_theme, "claw_crawler theme has been removed from ENEMY_THEMES.")
        self.assertEqual(len(claw_theme), 3, "claw_crawler theme should have 3 entries.")

    def test_BPG_ADV_MAT_05_get_theme_for_unknown_key_returns_fallback_not_raises(self):
        """
        BPG-ADV-MAT-05: MaterialThemes.get_theme() with an unrecognised key returns
        a fallback value rather than raising KeyError.

        Mutation surface: If get_theme() is refactored to use direct dict access
        instead of .get(), any unrecognised lookup in production code would raise
        rather than returning the fallback. No primary suite test exercises the
        error path.
        """
        try:
            result = MaterialThemes.get_theme('nonexistent_enemy_xyz')
            # Must not raise; result must be a list (the fallback)
            self.assertIsInstance(
                result,
                list,
                "get_theme() fallback for unknown key must return a list.",
            )
        except KeyError as e:
            self.fail(
                f"get_theme() raised KeyError for unknown key instead of returning fallback: {e}"
            )


# ---------------------------------------------------------------------------
# BPG-ADV-CLASS-* : Class structure adversarial
# ---------------------------------------------------------------------------

class TestNewClassesAdversarial(unittest.TestCase):
    """
    Adversarial class structure tests. The primary suite checks method presence
    and source-text fragments. Gaps:
      - The 3 new classes are distinct from each other (not aliased names)
      - The 3 new classes are distinct from the 3 existing classes
      - Methods defined on the new classes are NOT simply inherited from BaseEnemy
        (i.e., the new classes provide their own concrete implementations)
      - apply_materials source on new classes does NOT reference the wrong key
        (e.g. acid_spitter's apply_materials must not contain 'tar_slug')
    """

    def test_BPG_ADV_CLASS_01_three_new_classes_are_distinct_objects(self):
        """
        BPG-ADV-CLASS-01: AnimatedAcidSpitter, AnimatedClawCrawler, and
        AnimatedCarapaceHusk are three distinct class objects.

        Mutation surface: An alias assignment like
            AnimatedClawCrawler = AnimatedAcidSpitter
        would pass all individual class structure tests while silently
        producing only one real implementation.
        """
        new_classes = [AnimatedAcidSpitter, AnimatedClawCrawler, AnimatedCarapaceHusk]
        unique_ids = {id(cls) for cls in new_classes}
        self.assertEqual(
            len(unique_ids),
            3,
            "At least two of AnimatedAcidSpitter, AnimatedClawCrawler, "
            "AnimatedCarapaceHusk are aliases of the same class object.",
        )

    def test_BPG_ADV_CLASS_02_new_classes_distinct_from_existing_classes(self):
        """
        BPG-ADV-CLASS-02: None of the 3 new classes are the same object as
        AnimatedAdhesionBug, AnimatedTarSlug, or AnimatedEmberImp.

        Mutation surface: Re-using an existing class under a new name.
        """
        existing = {AnimatedAdhesionBug, AnimatedTarSlug, AnimatedEmberImp}
        new_classes = {AnimatedAcidSpitter, AnimatedClawCrawler, AnimatedCarapaceHusk}
        overlap = existing & new_classes
        self.assertEqual(
            overlap,
            set(),
            f"New class(es) are the same object as an existing class: {overlap}",
        )

    def test_BPG_ADV_CLASS_03_acid_spitter_create_body_is_overridden_not_inherited(self):
        """
        BPG-ADV-CLASS-03: AnimatedAcidSpitter.create_body is defined on the class
        itself, not inherited from BaseEnemy.

        Mutation surface: Forgetting to implement create_body in the subclass
        would leave the abstract method in place and fail at runtime, but
        introspection (hasattr) would still return True because BaseEnemy
        defines the abstract method. This test checks ownership.
        """
        self.assertIn(
            'create_body',
            AnimatedAcidSpitter.__dict__,
            "AnimatedAcidSpitter.create_body is not defined on the class itself — "
            "it may be inherited from BaseEnemy rather than overridden.",
        )

    def test_BPG_ADV_CLASS_04_claw_crawler_create_body_is_overridden_not_inherited(self):
        """
        BPG-ADV-CLASS-04: Same as CLASS-03 for AnimatedClawCrawler.
        """
        self.assertIn(
            'create_body',
            AnimatedClawCrawler.__dict__,
            "AnimatedClawCrawler.create_body is not defined on the class itself.",
        )

    def test_BPG_ADV_CLASS_05_carapace_husk_create_body_is_overridden_not_inherited(self):
        """
        BPG-ADV-CLASS-05: Same as CLASS-03 for AnimatedCarapaceHusk.
        """
        self.assertIn(
            'create_body',
            AnimatedCarapaceHusk.__dict__,
            "AnimatedCarapaceHusk.create_body is not defined on the class itself.",
        )

    def test_BPG_ADV_CLASS_06_acid_spitter_apply_materials_does_not_reference_wrong_key(self):
        """
        BPG-ADV-CLASS-06: AnimatedAcidSpitter.apply_materials source does NOT
        contain 'tar_slug', 'ember_imp', 'adhesion_bug', 'claw_crawler', or
        'carapace_husk' as the get_enemy_materials key.

        Mutation surface: Copy-paste from an existing class would carry the
        wrong string literal. The primary suite only verifies the presence of
        the correct key — not the absence of wrong keys.
        """
        source = inspect.getsource(AnimatedAcidSpitter.apply_materials)
        wrong_keys = ["'tar_slug'", "'ember_imp'", "'adhesion_bug'",
                      "'claw_crawler'", "'carapace_husk'"]
        for wrong in wrong_keys:
            with self.subTest(wrong_key=wrong):
                self.assertNotIn(
                    wrong,
                    source,
                    f"AnimatedAcidSpitter.apply_materials source contains wrong key {wrong}.",
                )

    def test_BPG_ADV_CLASS_07_claw_crawler_apply_materials_does_not_reference_wrong_key(self):
        """
        BPG-ADV-CLASS-07: AnimatedClawCrawler.apply_materials source does NOT
        contain wrong enemy keys.
        """
        source = inspect.getsource(AnimatedClawCrawler.apply_materials)
        wrong_keys = ["'tar_slug'", "'ember_imp'", "'adhesion_bug'",
                      "'acid_spitter'", "'carapace_husk'"]
        for wrong in wrong_keys:
            with self.subTest(wrong_key=wrong):
                self.assertNotIn(
                    wrong,
                    source,
                    f"AnimatedClawCrawler.apply_materials source contains wrong key {wrong}.",
                )

    def test_BPG_ADV_CLASS_08_carapace_husk_apply_materials_does_not_reference_wrong_key(self):
        """
        BPG-ADV-CLASS-08: AnimatedCarapaceHusk.apply_materials source does NOT
        contain wrong enemy keys.
        """
        source = inspect.getsource(AnimatedCarapaceHusk.apply_materials)
        wrong_keys = ["'tar_slug'", "'ember_imp'", "'adhesion_bug'",
                      "'acid_spitter'", "'claw_crawler'"]
        for wrong in wrong_keys:
            with self.subTest(wrong_key=wrong):
                self.assertNotIn(
                    wrong,
                    source,
                    f"AnimatedCarapaceHusk.apply_materials source contains wrong key {wrong}.",
                )

    def test_BPG_ADV_CLASS_09_acid_spitter_get_body_type_does_not_reference_wrong_type(self):
        """
        BPG-ADV-CLASS-09: AnimatedAcidSpitter.get_body_type source does NOT
        contain QUADRUPED or HUMANOID.

        Mutation surface: Copy-paste from EmberImp or AdhesionBug would carry
        the wrong body type constant. The primary suite only checks presence of
        BLOB, not absence of the other two.
        """
        source = inspect.getsource(AnimatedAcidSpitter.get_body_type)
        self.assertNotIn(
            'EnemyBodyTypes.QUADRUPED',
            source,
            "AnimatedAcidSpitter.get_body_type references QUADRUPED — should be BLOB.",
        )
        self.assertNotIn(
            'EnemyBodyTypes.HUMANOID',
            source,
            "AnimatedAcidSpitter.get_body_type references HUMANOID — should be BLOB.",
        )

    def test_BPG_ADV_CLASS_10_claw_crawler_get_body_type_does_not_reference_wrong_type(self):
        """
        BPG-ADV-CLASS-10: AnimatedClawCrawler.get_body_type source does NOT
        contain BLOB or HUMANOID.
        """
        source = inspect.getsource(AnimatedClawCrawler.get_body_type)
        self.assertNotIn(
            'EnemyBodyTypes.BLOB',
            source,
            "AnimatedClawCrawler.get_body_type references BLOB — should be QUADRUPED.",
        )
        self.assertNotIn(
            'EnemyBodyTypes.HUMANOID',
            source,
            "AnimatedClawCrawler.get_body_type references HUMANOID — should be QUADRUPED.",
        )

    def test_BPG_ADV_CLASS_11_carapace_husk_get_body_type_does_not_reference_wrong_type(self):
        """
        BPG-ADV-CLASS-11: AnimatedCarapaceHusk.get_body_type source does NOT
        contain BLOB or QUADRUPED.
        """
        source = inspect.getsource(AnimatedCarapaceHusk.get_body_type)
        self.assertNotIn(
            'EnemyBodyTypes.BLOB',
            source,
            "AnimatedCarapaceHusk.get_body_type references BLOB — should be HUMANOID.",
        )
        self.assertNotIn(
            'EnemyBodyTypes.QUADRUPED',
            source,
            "AnimatedCarapaceHusk.get_body_type references QUADRUPED — should be HUMANOID.",
        )

    def test_BPG_ADV_CLASS_12_acid_spitter_create_armature_does_not_call_wrong_builder(self):
        """
        BPG-ADV-CLASS-12: AnimatedAcidSpitter.create_armature source does NOT
        reference create_quadruped_armature or create_humanoid_armature.

        Mutation surface: Copy-paste from ClawCrawler or EmberImp.
        """
        source = inspect.getsource(AnimatedAcidSpitter.create_armature)
        self.assertNotIn(
            'create_quadruped_armature',
            source,
            "AnimatedAcidSpitter.create_armature calls create_quadruped_armature.",
        )
        self.assertNotIn(
            'create_humanoid_armature',
            source,
            "AnimatedAcidSpitter.create_armature calls create_humanoid_armature.",
        )

    def test_BPG_ADV_CLASS_13_claw_crawler_create_armature_does_not_call_wrong_builder(self):
        """
        BPG-ADV-CLASS-13: AnimatedClawCrawler.create_armature source does NOT
        reference create_blob_armature or create_humanoid_armature.
        """
        source = inspect.getsource(AnimatedClawCrawler.create_armature)
        self.assertNotIn(
            'create_blob_armature',
            source,
            "AnimatedClawCrawler.create_armature calls create_blob_armature.",
        )
        self.assertNotIn(
            'create_humanoid_armature',
            source,
            "AnimatedClawCrawler.create_armature calls create_humanoid_armature.",
        )

    def test_BPG_ADV_CLASS_14_carapace_husk_create_armature_does_not_call_wrong_builder(self):
        """
        BPG-ADV-CLASS-14: AnimatedCarapaceHusk.create_armature source does NOT
        reference create_blob_armature or create_quadruped_armature.
        """
        source = inspect.getsource(AnimatedCarapaceHusk.create_armature)
        self.assertNotIn(
            'create_blob_armature',
            source,
            "AnimatedCarapaceHusk.create_armature calls create_blob_armature.",
        )
        self.assertNotIn(
            'create_quadruped_armature',
            source,
            "AnimatedCarapaceHusk.create_armature calls create_quadruped_armature.",
        )

    def test_BPG_ADV_CLASS_15_all_new_classes_are_concrete_subclasses_not_abstract(self):
        """
        BPG-ADV-CLASS-15: None of the 3 new classes have unresolved abstract methods.

        Mutation surface: If any required abstract method is left unimplemented,
        the class cannot be instantiated. The primary suite checks method presence
        via hasattr — this verifies the ABC machinery agrees the class is concrete
        by checking __abstractmethods__ is empty or absent.
        """
        import abc
        for cls in [AnimatedAcidSpitter, AnimatedClawCrawler, AnimatedCarapaceHusk]:
            with self.subTest(cls=cls.__name__):
                abstract_methods = getattr(cls, '__abstractmethods__', frozenset())
                self.assertEqual(
                    abstract_methods,
                    frozenset(),
                    f"{cls.__name__} has unresolved abstract methods: {abstract_methods}",
                )


if __name__ == '__main__':
    unittest.main()
