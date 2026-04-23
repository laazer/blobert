"""Animated enemy build options package API."""

from __future__ import annotations

from .schema import (
    RIG_ROT_MAX,
    RIG_ROT_MIN,
    RIG_ROT_STEP,
    animated_build_controls_for_api,
    defaults_for_slug,
    eye_shape_pupil_control_defs,
    feature_zones,
    mouth_control_defs,
    options_for_enemy,
    parse_build_options_json,
    rig_rotation_control_defs,
    tail_control_defs,
    texture_control_defs,
    zone_texture_control_defs,
)
from .validate import coerce_validate_enemy_build_options, validate_build_options

get_control_definitions = animated_build_controls_for_api
normalize_controls = options_for_enemy

__all__ = sorted(
    {
        "animated_build_controls_for_api",
        "options_for_enemy",
        "parse_build_options_json",
        "defaults_for_slug",
        "eye_shape_pupil_control_defs",
        "mouth_control_defs",
        "tail_control_defs",
        "get_control_definitions",
        "normalize_controls",
        "validate_build_options",
        "coerce_validate_enemy_build_options",
        "feature_zones",
        "zone_texture_control_defs",
        "texture_control_defs",
        "rig_rotation_control_defs",
        "RIG_ROT_MIN",
        "RIG_ROT_MAX",
        "RIG_ROT_STEP",
    }
)
