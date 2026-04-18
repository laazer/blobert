"""Mouth, tail, eye/pupil, and rig rotation control defs (extracted for module size limits)."""

from __future__ import annotations

from typing import Any

# Per-part rotation controls (M25-04).
_RIG_ROT_MIN = -180.0
_RIG_ROT_MAX = 180.0
_RIG_ROT_STEP = 1.0


def _rig_rotation_control_defs() -> list[dict[str, Any]]:
    """Return 6 per-part rotation float controls (head X/Y/Z, body X/Y/Z) in degrees."""
    _parts = (
        ("HEAD", "Head"),
        ("BODY", "Body"),
    )
    _axes = ("X", "Y", "Z")
    return [
        {
            "key": f"RIG_{part}_ROT_{axis}",
            "label": f"Rig {part_label.lower()} rotation {axis}",
            "type": "float",
            "min": _RIG_ROT_MIN,
            "max": _RIG_ROT_MAX,
            "step": _RIG_ROT_STEP,
            "default": 0.0,
            "unit": "deg",
            "hint": f"Cosmetic rotation of the {part_label.lower()} mesh around the {axis}-axis (degrees).",
        }
        for part, part_label in _parts
        for axis in _axes
    ]


# Eye / pupil shape options.
_EYE_SHAPE_OPTIONS: tuple[str, ...] = ("circle", "oval", "slit", "square")
_PUPIL_SHAPE_OPTIONS: tuple[str, ...] = ("dot", "slit", "diamond")
_DEFAULT_EYE_SHAPE = "circle"
_DEFAULT_PUPIL_SHAPE = "dot"

# Mouth shape options (MTE-1)
_MOUTH_SHAPE_OPTIONS: tuple[str, ...] = ("smile", "grimace", "flat", "fang", "beak")
_DEFAULT_MOUTH_SHAPE = "smile"

# Tail shape options (MTE-1)
_TAIL_SHAPE_OPTIONS: tuple[str, ...] = ("spike", "whip", "club", "segmented", "curled")
_DEFAULT_TAIL_SHAPE = "spike"

# Tail length bounds and step (MTE-1)
_TAIL_LENGTH_MIN = 0.5
_TAIL_LENGTH_MAX = 3.0
_TAIL_LENGTH_STEP = 0.05
_TAIL_LENGTH_DEFAULT = 1.0

# NOTE: "custom" is intentionally excluded from _TEXTURE_MODE_OPTIONS. It is a
# client-side-only upload mode (blob URL via URL.createObjectURL) and is NOT a
# valid Blender build option. The frontend injects "custom" into the texture_mode
# selector without modifying this tuple. See ticket M25-03.
_TEXTURE_MODE_OPTIONS: tuple[str, ...] = ("none", "gradient", "spots", "stripes", "assets")
_GRAD_DIRECTION_OPTIONS: tuple[str, ...] = ("horizontal", "vertical", "radial")

_TEXTURE_SPOT_DENSITY_MIN = 0.1
_TEXTURE_SPOT_DENSITY_MAX = 5.0
_TEXTURE_SPOT_DENSITY_STEP = 0.05
_TEXTURE_SPOT_DENSITY_DEFAULT = 1.0

_TEXTURE_STRIPE_WIDTH_MIN = 0.05
_TEXTURE_STRIPE_WIDTH_MAX = 1.0
_TEXTURE_STRIPE_WIDTH_STEP = 0.01
_TEXTURE_STRIPE_WIDTH_DEFAULT = 0.2

_TEXTURE_ASSET_TILE_REPEAT_MIN = 0.5
_TEXTURE_ASSET_TILE_REPEAT_MAX = 8.0
_TEXTURE_ASSET_TILE_REPEAT_STEP = 0.5
_TEXTURE_ASSET_TILE_REPEAT_DEFAULT = 1.0


def _eye_shape_pupil_control_defs() -> list[dict[str, Any]]:
    """Return the three eye-shape + pupil control defs shared by every animated slug."""
    return [
        {
            "key": "eye_shape",
            "label": "Eye shape",
            "type": "select_str",
            "options": list(_EYE_SHAPE_OPTIONS),
            "default": _DEFAULT_EYE_SHAPE,
            "segmented": True,
        },
        {
            "key": "pupil_enabled",
            "label": "Pupil",
            "type": "bool",
            "default": False,
        },
        {
            "key": "pupil_shape",
            "label": "Pupil shape",
            "type": "select_str",
            "options": list(_PUPIL_SHAPE_OPTIONS),
            "default": _DEFAULT_PUPIL_SHAPE,
            "segmented": True,
        },
    ]


def _texture_control_defs() -> list[dict[str, Any]]:
    """Return the texture control defs shared by every animated slug."""
    return [
        {
            "key": "texture_mode",
            "label": "Texture mode",
            "type": "select_str",
            "options": list(_TEXTURE_MODE_OPTIONS),
            "default": "none",
        },
        {
            "key": "texture_grad_color_a",
            "label": "Gradient color A",
            "type": "str",
            "default": "",
        },
        {
            "key": "texture_grad_color_b",
            "label": "Gradient color B",
            "type": "str",
            "default": "",
        },
        {
            "key": "texture_grad_direction",
            "label": "Gradient direction",
            "type": "select_str",
            "options": list(_GRAD_DIRECTION_OPTIONS),
            "default": "horizontal",
        },
        {
            "key": "texture_spot_color",
            "label": "Spot color",
            "type": "str",
            "default": "",
        },
        {
            "key": "texture_spot_bg_color",
            "label": "Spot background color",
            "type": "str",
            "default": "",
        },
        {
            "key": "texture_spot_density",
            "label": "Spot density",
            "type": "float",
            "min": _TEXTURE_SPOT_DENSITY_MIN,
            "max": _TEXTURE_SPOT_DENSITY_MAX,
            "step": _TEXTURE_SPOT_DENSITY_STEP,
            "default": _TEXTURE_SPOT_DENSITY_DEFAULT,
        },
        {
            "key": "texture_stripe_color",
            "label": "Stripe color",
            "type": "str",
            "default": "",
        },
        {
            "key": "texture_stripe_bg_color",
            "label": "Stripe background color",
            "type": "str",
            "default": "",
        },
        {
            "key": "texture_stripe_width",
            "label": "Stripe width",
            "type": "float",
            "min": _TEXTURE_STRIPE_WIDTH_MIN,
            "max": _TEXTURE_STRIPE_WIDTH_MAX,
            "step": _TEXTURE_STRIPE_WIDTH_STEP,
            "default": _TEXTURE_STRIPE_WIDTH_DEFAULT,
        },
        {
            "key": "texture_asset_id",
            "label": "Asset texture",
            "type": "str",
            "default": "",
        },
        {
            "key": "texture_asset_tile_repeat",
            "label": "Tile repeat",
            "type": "float",
            "min": _TEXTURE_ASSET_TILE_REPEAT_MIN,
            "max": _TEXTURE_ASSET_TILE_REPEAT_MAX,
            "step": _TEXTURE_ASSET_TILE_REPEAT_STEP,
            "default": _TEXTURE_ASSET_TILE_REPEAT_DEFAULT,
        },
    ]

def _mouth_control_defs() -> list[dict[str, Any]]:
    """Return the mouth control defs (MTE-1)."""
    return [
        {
            "key": "mouth_enabled",
            "label": "Mouth",
            "type": "bool",
            "default": False,
        },
        {
            "key": "mouth_shape",
            "label": "Mouth shape",
            "type": "select_str",
            "options": list(_MOUTH_SHAPE_OPTIONS),
            "default": _DEFAULT_MOUTH_SHAPE,
        },
    ]


def _tail_control_defs() -> list[dict[str, Any]]:
    """Return the tail control defs (MTE-1)."""
    return [
        {
            "key": "tail_enabled",
            "label": "Tail",
            "type": "bool",
            "default": False,
        },
        {
            "key": "tail_shape",
            "label": "Tail shape",
            "type": "select_str",
            "options": list(_TAIL_SHAPE_OPTIONS),
            "default": _DEFAULT_TAIL_SHAPE,
        },
        {
            "key": "tail_length",
            "label": "Tail length",
            "type": "float",
            "min": _TAIL_LENGTH_MIN,
            "max": _TAIL_LENGTH_MAX,
            "step": _TAIL_LENGTH_STEP,
            "default": _TAIL_LENGTH_DEFAULT,
        },
    ]
