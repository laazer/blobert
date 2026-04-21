"""M25-05 — body_type select_str on all animated slugs; coercion to default."""

from __future__ import annotations

import pytest

from src.utils.body_type_presets import BODY_TYPE_OPTIONS
from src.utils.build_options import (
    animated_build_controls_for_api,
    options_for_enemy,
)
from src.utils.config import ANIMATED_SLUGS


@pytest.mark.parametrize("slug", list(ANIMATED_SLUGS))
def test_all_animated_slugs_expose_body_type_control(slug: str) -> None:
    ctrl = animated_build_controls_for_api()[slug]
    keys = [c["key"] for c in ctrl]
    assert "body_type" in keys
    row = next(c for c in ctrl if c["key"] == "body_type")
    assert row["type"] == "select_str"
    assert row.get("options") == list(BODY_TYPE_OPTIONS)
    assert row.get("default") == "default"


def test_options_for_enemy_invalid_body_type_coerces_to_default() -> None:
    out = options_for_enemy("imp", {"body_type": "INVALID"})
    assert out["body_type"] == "default"


@pytest.mark.parametrize("slug", list(ANIMATED_SLUGS))
@pytest.mark.parametrize("preset", ("standard_biped", "no_leg_biped"))
def test_standard_and_no_leg_valid_for_all_slugs(slug: str, preset: str) -> None:
    out = options_for_enemy(slug, {"body_type": preset})
    assert out["body_type"] == preset
