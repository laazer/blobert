"""Pure geometry helpers for zone-geometry extras placement."""

from __future__ import annotations

import math
from collections.abc import Mapping as _Mapping
from typing import Any as _Any
from typing import Protocol as _Protocol

from ...utils.build_options import OFFSET_XYZ_MAX, OFFSET_XYZ_MIN


class _VectorLike(_Protocol):
    x: float
    y: float
    z: float


def vec_xyz(v: _VectorLike | tuple[float, float, float] | list[float] | object) -> tuple[float, float, float]:
    """Coerce vector-like values to a numeric xyz tuple."""
    if hasattr(v, "x"):
        return (float(v.x), float(v.y), float(v.z))
    inner = getattr(v, "_t", None)
    if inner is not None and len(inner) >= 3:
        return (float(inner[0]), float(inner[1]), float(inner[2]))
    if isinstance(v, (tuple, list)) and len(v) >= 3:
        return (float(v[0]), float(v[1]), float(v[2]))
    return (0.0, 0.0, 0.0)


def ellipsoid_point_at(
    cx: float,
    cy: float,
    cz: float,
    a: float,
    b: float,
    h: float,
    theta: float,
    phi: float,
) -> tuple[float, float, float]:
    """Compute a point on an ellipsoid surface in Cartesian coordinates."""
    x = cx + a * math.sin(phi) * math.cos(theta)
    y = cy + b * math.sin(phi) * math.sin(theta)
    z = cz + h * math.cos(phi)
    x = float(round(x, 12))
    y = float(round(y, 12))
    z = float(round(z, 12))
    return (x, y, z)


def ellipsoid_normal(
    cx: float,
    cy: float,
    cz: float,
    a: float,
    b: float,
    h: float,
    point: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Compute outward ellipsoid normal with deterministic degenerate fallback."""
    vx, vy, vz = point[0] - cx, point[1] - cy, point[2] - cz
    nx, ny, nz = vx / (a * a), vy / (b * b), vz / (h * h)
    ln = math.sqrt(nx * nx + ny * ny + nz * nz)
    if ln < 1e-9:
        return (0.0, 0.0, 1.0)
    return (nx / ln, ny / ln, nz / ln)


def body_ref_size(a: float, b: float, h: float) -> float:
    """Characteristic length from body semi-axes."""
    ax = max(1e-6, abs(a))
    ay = max(1e-6, abs(b))
    az = max(1e-6, abs(h))
    return float((ax * ay * az) ** (1.0 / 3.0))


def head_ref_size(ax: float, ay: float, az: float) -> float:
    """Characteristic length from head ellipsoid radii."""
    u = max(1e-6, abs(ax), abs(ay), abs(az))
    return float(u)


def zone_extra_scale(
    spec: _Mapping[str, _Any],
    key: str,
    default: float = 1.0,
    lo: float = 0.25,
    hi: float = 3.0,
) -> float:
    """Read a bounded scalar from a zone-extra spec with fail-closed coercion."""
    try:
        s = float(spec.get(key, default))
    except (TypeError, ValueError):
        s = default
    if math.isnan(s):
        s = default
    elif math.isinf(s):
        s = lo if s < 0 else hi
    return max(lo, min(hi, s))


def zone_extra_offset(spec: _Mapping[str, _Any], axis: str) -> float:
    """Read and clamp xyz placement offset from zone-extra spec."""
    try:
        v = float(spec.get(axis, 0.0))
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(v):
        return 0.0
    clamped = max(OFFSET_XYZ_MIN, min(OFFSET_XYZ_MAX, v))
    return max(-1.0, min(1.0, clamped))
