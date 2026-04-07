"""
Behavioral tests for uniform geometry scale on ModelTypeFactory / BaseModelType.

Spec: project_board/specs/enemy_model_scale_input_spec.md (EMSI-1..EMSI-4).

Patches the same archetype module bindings as test_base_models_factory.py so
create_model runs headless without Blender.
"""

from __future__ import annotations

import inspect
import math
import random
import unittest
from contextlib import ExitStack, contextmanager
from unittest.mock import MagicMock, patch

import src.enemies.base_models as bm

_FIXED_SEED = 42


def _mesh_object_mock() -> MagicMock:
    obj = MagicMock()
    obj.type = "MESH"
    obj.data = MagicMock()
    obj.data.materials = []
    return obj


_MATERIAL_MAP = {"body": object(), "head": object(), "limbs": object(), "extra": object()}


@contextmanager
def _capture_primitive_calls():
    """Patch archetype modules; record ordered create_sphere / create_cylinder kwargs."""
    log: list[tuple[str, dict]] = []
    apply_mock = MagicMock()

    def _sphere(**kwargs) -> MagicMock:
        log.append(("sphere", dict(kwargs)))
        return _mesh_object_mock()

    def _cylinder(**kwargs) -> MagicMock:
        log.append(("cylinder", dict(kwargs)))
        return _mesh_object_mock()

    get_mats = MagicMock(return_value=_MATERIAL_MAP)
    archetype_modules = (
        "src.enemies.base_models.insectoid_model",
        "src.enemies.base_models.blob_model",
        "src.enemies.base_models.humanoid_model",
    )
    with ExitStack() as stack:
        for mod in archetype_modules:
            stack.enter_context(
                patch.multiple(
                    mod,
                    create_sphere=_sphere,
                    create_cylinder=_cylinder,
                    get_enemy_materials=get_mats,
                    apply_material_to_object=apply_mock,
                )
            )
        stack.enter_context(
            patch.multiple(
                "src.enemies.base_models.base_model_type",
                get_enemy_materials=get_mats,
                apply_material_to_object=apply_mock,
            )
        )
        yield apply_mock, log


def _scale_loc_scale_kwargs(log: list[tuple[str, dict]], factor: float) -> list[tuple[str, dict]]:
    """EMSI-3: expected kwargs if legacy tuples are uniformly multiplied by factor."""
    out: list[tuple[str, dict]] = []
    for kind, kw in log:
        new_kw = dict(kw)
        loc = new_kw.get("location")
        sc = new_kw.get("scale")
        if loc is not None:
            new_kw["location"] = (loc[0] * factor, loc[1] * factor, loc[2] * factor)
        if sc is not None:
            new_kw["scale"] = (sc[0] * factor, sc[1] * factor, sc[2] * factor)
        out.append((kind, new_kw))
    return out


class TestEMSI1FactoryAndInstanceScaleAPI(unittest.TestCase):
    """EMSI-1: scale parameter and public instance.scale."""

    def test_EMSI_1_1_create_model_accepts_default_and_explicit_one(self):
        materials = {"a": object()}
        with _capture_primitive_calls():
            rng_a = random.Random(_FIXED_SEED)
            m_default = bm.ModelTypeFactory.create_model(
                "blob", "s", materials, rng_a
            )
            rng_b = random.Random(_FIXED_SEED)
            m_explicit = bm.ModelTypeFactory.create_model(
                "blob", "s", materials, rng_b, scale=1.0
            )
        self.assertEqual(m_explicit.scale, 1.0)
        self.assertEqual(m_default.scale, 1.0)

    def test_EMSI_1_2_instance_scale_reflects_passed_value_after_geometry_and_materials(self):
        materials = {"a": object()}
        with _capture_primitive_calls():
            rng = random.Random(_FIXED_SEED)
            model = bm.ModelTypeFactory.create_model(
                "humanoid", "named", materials, rng, scale=2.5
            )
        self.assertEqual(model.scale, 2.5)

    def test_EMSI_1_3_signatures_and_docstrings_mention_scale(self):
        cm_sig = inspect.signature(bm.ModelTypeFactory.create_model)
        self.assertIn("scale", cm_sig.parameters)
        self.assertEqual(cm_sig.parameters["scale"].default, 1.0)

        init_sig = inspect.signature(bm.BaseModelType.__init__)
        self.assertIn("scale", init_sig.parameters)
        self.assertEqual(init_sig.parameters["scale"].default, 1.0)

        for doc in (
            bm.ModelTypeFactory.create_model.__doc__ or "",
            bm.BaseModelType.__init__.__doc__ or "",
        ):
            self.assertIn("scale", doc.lower(), msg=f"doc fragment missing scale: {doc!r}")


class TestEMSI2ScaleValidation(unittest.TestCase):
    """EMSI-2: finite strictly positive scale only."""

    def test_EMSI_2_1_invalid_scales_raise_value_error_with_scale_message(self):
        materials = {"a": object()}
        invalid = (
            0.0,
            -1.0,
            float("nan"),
            float("inf"),
            float("-inf"),
        )
        for bad in invalid:
            with self.subTest(scale=bad):
                with _capture_primitive_calls():
                    rng = random.Random(_FIXED_SEED)
                    with self.assertRaises(ValueError) as ctx:
                        bm.ModelTypeFactory.create_model(
                            "blob", "bad", materials, rng, scale=bad
                        )
                self.assertIn("scale", str(ctx.exception).lower())

    def test_EMSI_2_2_fractional_and_greater_than_one_accepted(self):
        materials = {"a": object()}
        with _capture_primitive_calls():
            for s in (0.5, 2.0):
                with self.subTest(scale=s):
                    rng = random.Random(_FIXED_SEED)
                    m = bm.ModelTypeFactory.create_model(
                        "insectoid", "ok", materials, rng, scale=s
                    )
                    self.assertEqual(m.scale, s)

    def test_EMSI_2_3_invalid_scale_fail_fast_no_primitive_calls(self):
        """EMSI-2: reject before geometry; mutants that validate late still leave log empty."""
        materials = {"a": object()}
        for bad in (-0.0, -1e-300):
            with self.subTest(scale=bad):
                with _capture_primitive_calls() as (_, log):
                    rng = random.Random(_FIXED_SEED)
                    with self.assertRaises(ValueError):
                        bm.ModelTypeFactory.create_model(
                            "blob", "x", materials, rng, scale=bad
                        )
                self.assertEqual(
                    log,
                    [],
                    msg="invalid scale must not invoke create_sphere/create_cylinder",
                )

    def test_EMSI_2_4_subnormal_and_large_finite_accepted(self):
        """EMSI-2 edge notes: subnormal >0 and huge finite scales are valid."""
        materials = {"a": object()}
        tiny = math.nextafter(0.0, 1.0)  # smallest positive float (often subnormal)
        huge = 1e12
        self.assertTrue(math.isfinite(tiny) and tiny > 0)
        self.assertTrue(math.isfinite(huge) and huge > 0)
        with _capture_primitive_calls():
            for s in (tiny, huge):
                with self.subTest(scale=s):
                    rng = random.Random(_FIXED_SEED)
                    m = bm.ModelTypeFactory.create_model(
                        "blob", "edge", materials, rng, scale=s
                    )
                    self.assertEqual(m.scale, s)


class TestEMSI3UniformGeometryScaling(unittest.TestCase):
    """EMSI-3: primitive location/scale kwargs; rotation_euler unchanged for humanoid arms."""

    def test_EMSI_3_1_scale_one_matches_omitted_scale_primitive_kwargs_all_archetypes(self):
        materials = {"x": object()}
        for model_type in ("insectoid", "blob", "humanoid"):
            with self.subTest(model_type=model_type):
                with _capture_primitive_calls() as (_, log_omit):
                    rng_a = random.Random(_FIXED_SEED)
                    bm.ModelTypeFactory.create_model(
                        model_type, "p", materials, rng_a
                    )
                    expected = list(log_omit)
                with _capture_primitive_calls() as (_, log_explicit):
                    rng_b = random.Random(_FIXED_SEED)
                    bm.ModelTypeFactory.create_model(
                        model_type, "p", materials, rng_b, scale=1.0
                    )
                self.assertEqual(log_explicit, expected)

    def test_EMSI_3_2_scale_two_multiplies_location_and_scale_kwargs_all_archetypes(self):
        materials = {"x": object()}
        for model_type in ("insectoid", "blob", "humanoid"):
            with self.subTest(model_type=model_type):
                with _capture_primitive_calls() as (_, log_one):
                    rng_a = random.Random(_FIXED_SEED)
                    bm.ModelTypeFactory.create_model(
                        model_type, "p", materials, rng_a, scale=1.0
                    )
                with _capture_primitive_calls() as (_, log_two):
                    rng_b = random.Random(_FIXED_SEED)
                    bm.ModelTypeFactory.create_model(
                        model_type, "p", materials, rng_b, scale=2.0
                    )
                expected_two = _scale_loc_scale_kwargs(log_one, 2.0)
                self.assertEqual(
                    log_two,
                    expected_two,
                    msg=f"scale=2.0 must match scaled location/scale kwargs vs scale=1.0 for {model_type}",
                )
                self.assertEqual(len(log_one), len(log_two))
                for (_, kw1), (_, kw2) in zip(log_one, log_two):
                    self.assertEqual(
                        {k: v for k, v in kw1.items() if k not in ("location", "scale")},
                        {k: v for k, v in kw2.items() if k not in ("location", "scale")},
                    )

    def test_EMSI_3_2b_fractional_scale_matches_tuple_multiply_contract(self):
        """Non-power-of-two fractional s; catches implementations that round or skip axes."""
        materials = {"x": object()}
        factor = 0.25
        with _capture_primitive_calls() as (_, log_one):
            rng_a = random.Random(_FIXED_SEED)
            bm.ModelTypeFactory.create_model(
                "blob", "p", materials, rng_a, scale=1.0
            )
        with _capture_primitive_calls() as (_, log_frac):
            rng_b = random.Random(_FIXED_SEED)
            bm.ModelTypeFactory.create_model(
                "blob", "p", materials, rng_b, scale=factor
            )
        self.assertEqual(log_frac, _scale_loc_scale_kwargs(log_one, factor))

    def test_EMSI_3_3_humanoid_arm_rotation_euler_unchanged_when_scale_doubles(self):
        # CHECKPOINT: assumes arms are parts[2] and parts[4] and are the only rotation_euler sets in humanoid_model.
        """Arms are parts[2] and parts[4]; only those set rotation_euler in humanoid_model."""
        materials = {"a": object()}

        def _run(scale: float):
            with _capture_primitive_calls():
                rng = random.Random(_FIXED_SEED)
                return bm.ModelTypeFactory.create_model(
                    "humanoid", "h", materials, rng, scale=scale
                )

        m1 = _run(1.0)
        m2 = _run(2.0)
        for idx in (2, 4):
            with self.subTest(part_index=idx):
                self.assertEqual(m1.parts[idx].rotation_euler, m2.parts[idx].rotation_euler)


class TestEMSI4Determinism(unittest.TestCase):
    """EMSI-4: scale does not perturb RNG-driven geometry sequence for fixed inputs."""

    def test_EMSI_4_1_identical_inputs_produce_identical_primitive_logs(self):
        materials = {"q": object()}
        scale = 1.25

        def _once():
            with _capture_primitive_calls() as (_, log):
                rng = random.Random(_FIXED_SEED)
                bm.ModelTypeFactory.create_model(
                    "blob", "d", materials, rng, scale=scale
                )
                return list(log)

        self.assertEqual(_once(), _once())

    def test_EMSI_4_2_different_valid_scales_same_primitive_kind_sequence(self):
        """Scale must not insert/remove/reorder primitives vs baseline for same seed."""
        materials = {"q": object()}

        def kinds(scale: float) -> list[str]:
            with _capture_primitive_calls() as (_, log):
                rng = random.Random(_FIXED_SEED)
                bm.ModelTypeFactory.create_model(
                    "humanoid", "d", materials, rng, scale=scale
                )
                return [k for k, _ in log]

        base = kinds(1.0)
        self.assertEqual(kinds(0.5), base)
        self.assertEqual(kinds(3.0), base)


class TestEMSI5RegistryUnchanged(unittest.TestCase):
    """EMSI-5.2: MODEL_TYPES and get_available_types unchanged by scale feature."""

    def test_EMSI_5_2_registry_keys_and_order_unchanged(self):
        # CHECKPOINT: encodes BMSBA-era registry snapshot; if MODEL_TYPES grows, update intentionally.
        self.assertEqual(
            set(bm.ModelTypeFactory.MODEL_TYPES.keys()),
            {"insectoid", "blob", "humanoid"},
        )
        self.assertEqual(
            bm.ModelTypeFactory.get_available_types(),
            ["insectoid", "blob", "humanoid"],
        )


class TestEMSIAdversarialCallStyleAndFallback(unittest.TestCase):
    """Positional API, int coercion, unknown model_type path, direct constructor validation."""

    def test_EMSI_ADV_01_positional_scale_after_rng(self):
        """EMSI-1: fifth positional arg is scale (call sites may omit keyword)."""
        materials = {"a": object()}
        with _capture_primitive_calls():
            rng = random.Random(_FIXED_SEED)
            m = bm.ModelTypeFactory.create_model(
                "blob", "pos", materials, rng, 1.75
            )
        self.assertEqual(m.scale, 1.75)

    def test_EMSI_ADV_02_int_scale_matches_float_geometry(self):
        """Spec allows int where coerced; geometry must match float multiplier."""
        materials = {"a": object()}
        with _capture_primitive_calls() as (_, log_int):
            rng_i = random.Random(_FIXED_SEED)
            bm.ModelTypeFactory.create_model(
                "insectoid", "i", materials, rng_i, scale=3
            )
        with _capture_primitive_calls() as (_, log_float):
            rng_f = random.Random(_FIXED_SEED)
            bm.ModelTypeFactory.create_model(
                "insectoid", "i", materials, rng_f, scale=3.0
            )
        self.assertEqual(log_int, log_float)

    def test_EMSI_ADV_03_unknown_model_type_scales_like_insectoid_fallback(self):
        # CHECKPOINT: relies on current factory fallback to InsectoidModel for unknown keys.
        """EMSI-5 compatibility: unknown type still applies same scale contract as insectoid."""
        materials = {"x": object()}
        unknown_key = "__maint_emsi_unknown__"
        self.assertNotIn(unknown_key, bm.ModelTypeFactory.MODEL_TYPES)
        with _capture_primitive_calls() as (_, log_insect):
            rng_a = random.Random(_FIXED_SEED)
            bm.ModelTypeFactory.create_model(
                "insectoid", "p", materials, rng_a, scale=2.0
            )
        with _capture_primitive_calls() as (_, log_unknown):
            rng_b = random.Random(_FIXED_SEED)
            bm.ModelTypeFactory.create_model(
                unknown_key, "p", materials, rng_b, scale=2.0
            )
        self.assertEqual(log_unknown, log_insect)

    def test_EMSI_ADV_04_unknown_type_invalid_scale_fail_fast(self):
        materials = {"x": object()}
        unknown_key = "__maint_emsi_unknown__"
        with _capture_primitive_calls() as (_, log):
            rng = random.Random(_FIXED_SEED)
            with self.assertRaises(ValueError):
                bm.ModelTypeFactory.create_model(
                    unknown_key, "p", materials, rng, scale=0.0
                )
        self.assertEqual(log, [])

    def test_EMSI_ADV_05_direct_archetype_init_rejects_invalid_scale(self):
        """EMSI-2 single validation point must cover direct construction, not only factory."""
        materials = {"a": object()}
        rng = random.Random(_FIXED_SEED)
        with _capture_primitive_calls():
            with self.assertRaises(ValueError):
                bm.HumanoidModel("h", materials, rng, scale=-0.5)


if __name__ == "__main__":
    unittest.main()
