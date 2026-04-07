"""
Contract + adversarial tests for enemy slug registry (MAINT-ETRP).

Spec: project_board/maintenance/in_progress/enemy_types_registry_python.md
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

from src.utils import enemy_slug_registry
from src.utils.constants import EnemyTypes

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
    assert list(enemy_slug_registry.ANIMATED_SLUGS) == _EXPECTED_ANIMATED
    assert list(enemy_slug_registry.STATIC_SLUGS) == _EXPECTED_STATIC


def test_ETRP_06_animated_enemies_for_api_matches_registry_order() -> None:
    meta = enemy_slug_registry.animated_enemies_for_api()
    assert [e["slug"] for e in meta] == _EXPECTED_ANIMATED
    assert all(e.get("label") for e in meta)
    assert {e["slug"] for e in meta} == set(enemy_slug_registry.ANIMATED_ENEMY_LABELS.keys())


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

    assert list(AnimatedEnemyBuilder.ENEMY_CLASSES.keys()) == list(enemy_slug_registry.ANIMATED_SLUGS)
    assert set(AnimatedEnemyBuilder.ENEMY_CLASSES.keys()) == set(enemy_slug_registry.ANIMATED_SLUGS)


def test_ETRP_04_import_order_main_style_no_cycle() -> None:
    """Same sys.path as main.py: import utils.constants then registry in a fresh process."""
    root = Path(__file__).resolve().parents[2]
    src = root / "src"
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(src)!r})\n"
        "import utils.constants\n"
        "import utils.enemy_slug_registry\n"
        "from utils.constants import EnemyTypes\n"
        "from utils import enemy_slug_registry as reg\n"
        "assert EnemyTypes.get_animated() == list(reg.ANIMATED_SLUGS)\n"
        "assert EnemyTypes.get_static() == list(reg.STATIC_SLUGS)\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)


# --- Adversarial (Test Breaker) ---


def _registry_py_path() -> Path:
    return Path(__file__).resolve().parents[2] / "src" / "utils" / "enemy_slug_registry.py"


def test_ETRP_ADV_01_registry_ast_never_imports_constants() -> None:
    """Mutation: adding `from utils.constants import X` reintroduces a cycle."""
    path = _registry_py_path()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name
                assert mod != "utils.constants", f"forbidden import: {mod!r}"
                assert not mod.endswith(".constants"), f"forbidden import: {mod!r}"
        elif isinstance(node, ast.ImportFrom):
            mod = node.module
            if mod in ("constants", "utils.constants"):
                raise AssertionError(f"forbidden ImportFrom module: {mod!r}")
            if mod == "utils":
                for alias in node.names:
                    if alias.name == "constants":
                        raise AssertionError("forbidden: from utils import constants")


def test_ETRP_ADV_02_registry_disjoint_animated_static() -> None:
    """Mutation: duplicate slug in both tuples must fail."""
    animated = set(enemy_slug_registry.ANIMATED_SLUGS)
    static = set(enemy_slug_registry.STATIC_SLUGS)
    assert animated.isdisjoint(static), animated & static
