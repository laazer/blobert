"""Animated enemy build options package API."""

from __future__ import annotations

from typing import Any

from .schema import *  # noqa: F403
from .schema import __all__ as _schema_all
from .schema import (
    _eye_shape_pupil_control_defs,  # noqa: F401
    _mouth_control_defs,  # noqa: F401
    _tail_control_defs,  # noqa: F401
    animated_build_controls_for_api,
    options_for_enemy,
    parse_build_options_json,  # noqa: F401
)
from .validate import coerce_validate_enemy_build_options


def get_control_definitions() -> dict[str, list[dict[str, Any]]]:
    """Return per-enemy control definitions for UI and validation."""
    return animated_build_controls_for_api()


def normalize_controls(enemy_type: str, raw: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize user payload into validated build options for an enemy."""
    return options_for_enemy(enemy_type, raw)


def validate_build_options(enemy_type: str, raw: dict[str, Any] | None) -> dict[str, Any]:
    """Validate/coerce an already-merged or partial options payload."""
    return coerce_validate_enemy_build_options(enemy_type, dict(raw or {}))


__all__ = sorted(
    set(_schema_all)
    | {
        "get_control_definitions",
        "normalize_controls",
        "validate_build_options",
        "coerce_validate_enemy_build_options",
        "_eye_shape_pupil_control_defs",
        "_mouth_control_defs",
        "_tail_control_defs",
    }
)
