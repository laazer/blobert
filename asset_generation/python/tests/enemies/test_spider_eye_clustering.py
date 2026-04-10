"""Spider multi-eye clustering (ticket 15)."""

from __future__ import annotations

import random
from types import SimpleNamespace

from src.enemies.animated_spider import AnimatedSpider


def test_eye_clustering_tightens_multi_eye_arc() -> None:
    mats: dict[str, object] = {}
    s0 = AnimatedSpider("spider", mats, random.Random(0), build_options={"eye_count": 6, "eye_clustering": 0.0})
    s1 = AnimatedSpider("spider", mats, random.Random(0), build_options={"eye_count": 6, "eye_clustering": 1.0})
    hc = SimpleNamespace(x=1.2, y=0.0, z=0.4)
    hs = 0.9
    dirs0 = s0._eye_dirs_uniform(6, hc, hs)
    dirs1 = s1._eye_dirs_uniform(6, hc, hs)
    ys0 = [float(v.y) for v in dirs0]
    ys1 = [float(v.y) for v in dirs1]
    assert max(ys0) - min(ys0) > max(ys1) - min(ys1) + 1e-5


def test_eye_clustering_invalid_string_uses_default() -> None:
    mats: dict[str, object] = {}
    s = AnimatedSpider("spider", mats, random.Random(0), build_options={"eye_clustering": "bad"})
    assert s._eye_clustering() == 0.5


def test_build_mesh_parts_random_eye_distribution_branch() -> None:
    mats: dict[str, object] = {}
    s = AnimatedSpider(
        "spider",
        mats,
        random.Random(2),
        build_options={"eye_distribution": "random", "eye_count": 4, "placement_seed": 9},
    )
    s.parts = []
    s.build_mesh_parts()
    assert s._eye_count == 4
    assert len(s.parts) >= 12
