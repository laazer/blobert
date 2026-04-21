"""
Contract + adversarial tests for enemy slug registry (MAINT-ETRP).

Slug tuples and labels live in ``src.utils.config`` after M901-04 consolidation.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

from src.utils import config
from src.utils.config import EnemyTypes

# Frozen snapshots — must match pre-refactor get_animated / get_static order.
_EXPECTED_ANIMATED = [
    "spider",
    "slug",
    "imp",
    "spitter",
    "claw_crawler",
    "carapace_husk",
]
_EXPECTED_STATIC = [
    "glue_drone",
    "melt_worm",
    "frost_jelly",
    "stone_burrower",
    "ferro_drone",
]


def test_ETRP_01_registry_tuples_match_frozen_lists() -> None:
    assert list(config.ANIMATED_SLUGS) == _EXPECTED_ANIMATED
    assert list(config.STATIC_SLUGS) == _EXPECTED_STATIC


def test_ETRP_06_animated_enemies_for_api_matches_registry_order() -> None:
    meta = config.animated_enemies_for_api()
    assert [e["slug"] for e in meta] == _EXPECTED_ANIMATED
    assert all(e.get("label") for e in meta)
    assert {e["slug"] for e in meta} == set(config.ANIMATED_ENEMY_LABELS.keys())


def test_ETRP_02_enemy_types_class_attributes_unchanged() -> None:
    assert EnemyTypes.SPIDER == "spider"
    assert EnemyTypes.SLUG == "slug"
    assert EnemyTypes.IMP == "imp"
    assert EnemyTypes.SPITTER == "spitter"
    assert EnemyTypes.CLAW_CRAWLER == "claw_crawler"
    assert EnemyTypes.CARAPACE_HUSK == "carapace_husk"
    assert EnemyTypes.GLUE_DRONE == "glue_drone"
    assert EnemyTypes.MELT_WORM == "melt_worm"
    assert EnemyTypes.FROST_JELLY == "frost_jelly"
    assert EnemyTypes.STONE_BURROWER == "stone_burrower"
    assert EnemyTypes.FERRO_DRONE == "ferro_drone"


def test_ETRP_03_get_methods_match_registry_and_get_all_concat() -> None:
    assert EnemyTypes.get_animated() == _EXPECTED_ANIMATED
    assert EnemyTypes.get_static() == _EXPECTED_STATIC
    assert EnemyTypes.get_all() == _EXPECTED_ANIMATED + _EXPECTED_STATIC
    assert EnemyTypes.get_all() == EnemyTypes.get_animated() + EnemyTypes.get_static()


def test_ETRP_05_animated_enemy_builder_matches_registry() -> None:
    """AnimatedEnemyBuilder.ENEMY_CLASSES keys/order match ANIMATED_SLUGS."""
    from src.enemies.animated import AnimatedEnemyBuilder

    assert list(AnimatedEnemyBuilder.ENEMY_CLASSES.keys()) == list(config.ANIMATED_SLUGS)
    assert set(AnimatedEnemyBuilder.ENEMY_CLASSES.keys()) == set(config.ANIMATED_SLUGS)


def test_ETRP_04_import_order_main_style_no_cycle() -> None:
    """Same sys.path as main.py: single-module config import in a fresh process."""
    root = Path(__file__).resolve().parents[2]
    src = root / "src"
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(src)!r})\n"
        "import utils.config\n"
        "from utils.config import EnemyTypes, ANIMATED_SLUGS, STATIC_SLUGS\n"
        "assert EnemyTypes.get_animated() == list(ANIMATED_SLUGS)\n"
        "assert EnemyTypes.get_static() == list(STATIC_SLUGS)\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)


# --- Adversarial (Test Breaker) ---


def _config_py_path() -> Path:
    return Path(__file__).resolve().parents[2] / "src" / "utils" / "config.py"


def test_ETRP_ADV_01_config_ast_no_legacy_split_or_forbidden_utils_deps() -> None:
    """config must not import deprecated split modules or other utils layers (M901-04 DAG)."""
    path = _config_py_path()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name
                assert mod not in (
                    "utils.constants",
                    "utils.enemy_slug_registry",
                ), f"forbidden import: {mod!r}"
                assert not mod.endswith(".constants"), f"forbidden import: {mod!r}"
                assert not mod.startswith("src.utils.build_options"), f"forbidden import: {mod!r}"
                assert not mod.startswith("src.utils.export"), f"forbidden import: {mod!r}"
                assert not mod.startswith("src.utils.materials"), f"forbidden import: {mod!r}"
                assert not mod.startswith("src.utils.validation"), f"forbidden import: {mod!r}"
        elif isinstance(node, ast.ImportFrom):
            mod = node.module
            if mod in ("constants", "utils.constants", "enemy_slug_registry", "utils.enemy_slug_registry"):
                raise AssertionError(f"forbidden ImportFrom module: {mod!r}")
            if mod == "utils":
                for alias in node.names:
                    if alias.name in ("constants", "enemy_slug_registry", "build_options", "export"):
                        raise AssertionError(f"forbidden: from utils import {alias.name}")


def test_ETRP_ADV_02_registry_disjoint_animated_static() -> None:
    """Mutation: duplicate slug in both tuples must fail."""
    animated = set(config.ANIMATED_SLUGS)
    static = set(config.STATIC_SLUGS)
    assert animated.isdisjoint(static), animated & static
