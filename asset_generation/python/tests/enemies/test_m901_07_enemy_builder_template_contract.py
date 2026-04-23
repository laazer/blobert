"""
M901-07 enemy builder template extraction — primary behavioral contracts.

Runtime-oriented assertions only:
- template module/base-class contract and typed hook surface
- strict deterministic phase order orchestration
- animated registry entrypoint compatibility for 5 target enemies
- fail-closed behavior for unknown enemy slug
"""

from __future__ import annotations

import inspect
import random

import pytest

from src.enemies.animated import (
    AnimatedCarapaceHusk,
    AnimatedClawCrawler,
    AnimatedEnemyBuilder,
    AnimatedImp,
    AnimatedSlug,
    AnimatedSpider,
)
from src.enemies.builder_template import AnimatedEnemyBuilderBase

_TARGET_SLUGS = ("spider", "imp", "slug", "carapace_husk", "claw_crawler")


def test_R1_template_module_exports_abstract_base_with_typed_hooks() -> None:
    assert inspect.isclass(AnimatedEnemyBuilderBase)
    assert inspect.isabstract(AnimatedEnemyBuilderBase)

    for hook_name in (
        "_build_body_mesh",
        "_build_limbs",
        "_apply_materials",
        "_add_zone_extras",
    ):
        hook = getattr(AnimatedEnemyBuilderBase, hook_name)
        sig = inspect.signature(hook)
        assert tuple(sig.parameters.keys()) == ("self",)
        assert sig.return_annotation is not inspect.Signature.empty


def test_R1_template_orchestration_order_is_body_limbs_materials_zone_extras() -> None:
    class _ProbeBuilder(AnimatedEnemyBuilderBase):
        body_height = 1.0

        def __init__(self, rng_seed: int = 11) -> None:
            super().__init__("probe", materials={}, rng=random.Random(rng_seed), build_options={})
            self.events: list[str] = []
            self.sampled: list[float] = []

        def _build_body_mesh(self) -> None:
            self.events.append("body")
            self.sampled.append(self.rng.random())

        def _build_limbs(self) -> None:
            self.events.append("limbs")
            self.sampled.append(self.rng.random())

        def _apply_materials(self) -> None:
            self.events.append("materials")

        def _add_zone_extras(self) -> None:
            self.events.append("zone_extras")

        def finalize(self):
            return "mesh"

        def get_body_type(self):
            return "probe"

        def get_rig_definition(self):
            return None

        def create_armature(self):
            return None

    first = _ProbeBuilder(rng_seed=123)
    second = _ProbeBuilder(rng_seed=123)

    assert first.build() == "mesh"
    assert second.build() == "mesh"
    assert first.events == ["body", "limbs", "materials", "zone_extras"]
    assert second.events == ["body", "limbs", "materials", "zone_extras"]
    assert first.sampled == second.sampled


def test_R1_template_runtime_stops_at_failing_phase_without_fallback() -> None:
    class _FailingBuilder(AnimatedEnemyBuilderBase):
        body_height = 1.0

        def __init__(self) -> None:
            super().__init__("probe", materials={}, rng=random.Random(9), build_options={})
            self.events: list[str] = []

        def _build_body_mesh(self) -> None:
            self.events.append("body")

        def _build_limbs(self) -> None:
            self.events.append("limbs")
            raise RuntimeError("limb-phase-failure")

        def _apply_materials(self) -> None:
            self.events.append("materials")

        def _add_zone_extras(self) -> None:
            self.events.append("zone_extras")

        def finalize(self):
            return "mesh"

        def get_body_type(self):
            return "probe"

        def get_rig_definition(self):
            return None

        def create_armature(self):
            return None

    builder = _FailingBuilder()
    with pytest.raises(RuntimeError, match="limb-phase-failure"):
        builder.build()
    assert builder.events == ["body", "limbs"]


def test_R1_template_runtime_invokes_zone_extras_once_after_materials() -> None:
    class _ZoneCounterBuilder(AnimatedEnemyBuilderBase):
        body_height = 1.0

        def __init__(self) -> None:
            super().__init__("probe", materials={}, rng=random.Random(13), build_options={})
            self.events: list[str] = []

        def _build_body_mesh(self) -> None:
            self.events.append("body")

        def _build_limbs(self) -> None:
            self.events.append("limbs")

        def _apply_materials(self) -> None:
            self.events.append("materials")

        def _add_zone_extras(self) -> None:
            self.events.append("zone_extras")

        def finalize(self):
            return "mesh"

        def get_body_type(self):
            return "probe"

        def get_rig_definition(self):
            return None

        def create_armature(self):
            return None

    builder = _ZoneCounterBuilder()
    assert builder.build() == "mesh"
    assert builder.events.count("zone_extras") == 1
    assert builder.events.index("zone_extras") > builder.events.index("materials")


def test_R1_target_enemy_classes_subclass_template_base() -> None:
    for cls in (
        AnimatedSpider,
        AnimatedImp,
        AnimatedSlug,
        AnimatedCarapaceHusk,
        AnimatedClawCrawler,
    ):
        assert issubclass(cls, AnimatedEnemyBuilderBase)


def test_R2_target_enemy_registry_entrypoints_remain_callable(monkeypatch: pytest.MonkeyPatch) -> None:
    for slug in _TARGET_SLUGS:
        enemy_cls = AnimatedEnemyBuilder.ENEMY_CLASSES[slug]
        monkeypatch.setattr(enemy_cls, "create_armature", lambda self: None)

        prefab_mesh = object()
        result = AnimatedEnemyBuilder.create_enemy(
            slug,
            materials={},
            rng=random.Random(77),
            prefab_mesh=prefab_mesh,
            build_options={},
        )
        assert result.mesh is prefab_mesh
        assert result.attack_profile is not None


def test_R2_enemy_class_mapping_remains_complete_for_required_target_slugs() -> None:
    for slug in _TARGET_SLUGS:
        assert slug in AnimatedEnemyBuilder.ENEMY_CLASSES


def test_R2_unknown_enemy_slug_remains_fail_closed() -> None:
    with pytest.raises(ValueError):
        AnimatedEnemyBuilder.create_enemy(
            "not_a_registered_enemy",
            materials={},
            rng=random.Random(1),
            prefab_mesh=object(),
            build_options={},
        )


def test_R2_unknown_enemy_slug_error_does_not_depend_on_slug_shape() -> None:
    for slug in ("", " ", "SPIDER", "spider\n", "../spider", "123"):
        with pytest.raises(ValueError):
            AnimatedEnemyBuilder.create_enemy(
                slug,
                materials={},
                rng=random.Random(2),
                prefab_mesh=object(),
                build_options={},
            )
