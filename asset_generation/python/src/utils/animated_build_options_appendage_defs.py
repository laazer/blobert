"""Mouth, tail, and eye/pupil control defs (extracted for module size limits)."""

from __future__ import annotations

from typing import Any

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
