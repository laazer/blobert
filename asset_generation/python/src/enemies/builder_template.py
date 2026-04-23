"""Template base for animated enemy builders with deterministic phase ordering."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from .animated_enemy import AnimatedEnemy


class AnimatedEnemyBuilderBase(AnimatedEnemy, ABC):
    """Shared phased build pipeline for animated enemies."""

    def __init__(
        self,
        name: str,
        materials: Mapping[str, Any],
        rng: Any,
        scale: float = 1.0,
        build_options: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, materials, rng, scale=scale, build_options=build_options)

    def build_mesh_parts(self) -> None:
        self._build_body_mesh()
        self._build_limbs()

    def apply_themed_materials(self) -> None:
        self._apply_materials()
        self._add_zone_extras()

    @abstractmethod
    def _build_body_mesh(self) -> None:
        """Build body/head/feature meshes before limbs."""

    @abstractmethod
    def _build_limbs(self) -> None:
        """Build appendage meshes after body meshes."""

    @abstractmethod
    def _apply_materials(self) -> None:
        """Apply materials after all geometry is created."""

    @abstractmethod
    def _add_zone_extras(self) -> None:
        """Attach zone extras after material assignment."""
