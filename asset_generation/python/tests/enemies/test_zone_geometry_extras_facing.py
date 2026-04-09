"""Zone geometry extras: facing filter (surface normal vs world axes)."""

from mathutils import Vector

from src.enemies.zone_geometry_extras_attach import _facing_allows_normal


def _only_top() -> dict:
    return {
        "place_top": True,
        "place_bottom": False,
        "place_front": False,
        "place_back": False,
        "place_left": False,
        "place_right": False,
    }


def test_facing_all_default_accepts_any_normal() -> None:
    assert _facing_allows_normal({}, Vector((1.0, 0.0, 0.0))) is True
    assert _facing_allows_normal({}, Vector((0.0, 0.0, -1.0))) is True


def test_facing_all_explicit_true_accepts_any() -> None:
    spec = {k: True for k in _only_top()}  # all six facings enabled
    assert _facing_allows_normal(spec, Vector((0.0, 1.0, 0.0))) is True


def test_facing_top_only_accepts_upward_normal() -> None:
    spec = _only_top()
    assert _facing_allows_normal(spec, Vector((0.0, 0.0, 1.0))) is True
    assert _facing_allows_normal(spec, Vector((0.2, 0.2, 0.95)).normalized()) is True


def test_facing_top_only_rejects_side_and_down() -> None:
    spec = _only_top()
    assert _facing_allows_normal(spec, Vector((1.0, 0.0, 0.0))) is False
    assert _facing_allows_normal(spec, Vector((0.0, 0.0, -1.0))) is False


def test_facing_none_enabled_falls_back_to_all() -> None:
    spec = {k: False for k in _only_top()}
    assert _facing_allows_normal(spec, Vector((0.0, 0.0, -1.0))) is True
