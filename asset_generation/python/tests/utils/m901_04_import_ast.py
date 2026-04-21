"""AST helpers for M901-04 import-DAG and legacy-import scans."""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path


def _iter_import_from_edges(path: Path) -> Iterable[tuple[str | None, int, tuple[str, ...]]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names = tuple(alias.name for alias in node.names)
            yield node.module, node.level, names


def assert_config_import_dag(path: Path) -> None:
    """R1: ``config`` must not import any ``src.utils`` subtree (except stdlib / body_families)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("src.utils"):
                    raise AssertionError(f"{path}: config must not import {alias.name!r}")
        elif isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                continue
            mod = node.module
            if mod and mod.startswith("src.utils"):
                raise AssertionError(f"{path}: config must not import from {mod!r}")
            if mod == "src.utils":
                for alias in node.names:
                    raise AssertionError(
                        f"{path}: config must not import from src.utils: {alias.name!r}"
                    )
            if mod is None and node.level and node.level > 0:
                for alias in node.names:
                    if alias.name in (
                        "build_options",
                        "export",
                        "materials",
                        "validation",
                        "simple_viewer",
                    ):
                        raise AssertionError(
                            f"{path}: forbidden relative import of {alias.name!r}"
                        )
            if mod and node.level and node.level > 0 and mod in (
                "build_options",
                "export",
                "materials",
                "validation",
                "simple_viewer",
            ):
                raise AssertionError(f"{path}: forbidden relative ImportFrom module {mod!r}")


def assert_export_import_dag(path: Path) -> None:
    """R1: ``export`` must not import ``build_options`` or ``materials``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(
                    ("src.utils.build_options", "src.utils.materials")
                ):
                    raise AssertionError(f"{path}: export must not import {alias.name!r}")
        elif isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                continue
            mod = node.module
            if mod and (
                mod.startswith("src.utils.build_options")
                or mod.startswith("src.utils.materials")
            ):
                raise AssertionError(f"{path}: export must not import from {mod!r}")
            if mod == "src.utils":
                for alias in node.names:
                    if alias.name in ("build_options", "materials", "animated_build_options"):
                        raise AssertionError(
                            f"{path}: export must not import from src.utils: {alias.name!r}"
                        )
            if mod is None and node.level and node.level > 0:
                for alias in node.names:
                    if alias.name in ("build_options", "materials"):
                        raise AssertionError(
                            f"{path}: forbidden relative import of {alias.name!r}"
                        )
            if mod and node.level and node.level > 0 and mod in ("build_options", "materials"):
                raise AssertionError(f"{path}: forbidden relative ImportFrom module {mod!r}")


def assert_validation_only_stdlib(path: Path) -> None:
    """R1: ``validation`` — stdlib + ``typing`` only; no ``src.`` or relative imports."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("src."):
                    raise AssertionError(f"{path}: validation must not import {alias.name!r}")
        elif isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                continue
            if node.level and node.level > 0:
                raise AssertionError(f"{path}: validation must not use relative imports")
            mod = node.module
            if mod and mod.startswith("src."):
                raise AssertionError(f"{path}: validation must not import from {mod!r}")


def assert_materials_import_dag(path: Path) -> None:
    """R1: ``materials`` must not import ``build_options`` or ``export``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(("src.utils.build_options", "src.utils.export")):
                    raise AssertionError(f"{path}: materials must not import {alias.name!r}")
        elif isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                continue
            mod = node.module
            if mod and (
                mod.startswith("src.utils.build_options")
                or mod.startswith("src.utils.export")
            ):
                raise AssertionError(f"{path}: materials must not import from {mod!r}")
            if mod == "src.utils":
                for alias in node.names:
                    if alias.name in ("build_options", "export", "animated_build_options"):
                        raise AssertionError(
                            f"{path}: materials must not import from src.utils: {alias.name!r}"
                        )
            if mod is None and node.level and node.level > 0:
                for alias in node.names:
                    if alias.name in ("build_options", "export"):
                        raise AssertionError(
                            f"{path}: forbidden relative import of {alias.name!r}"
                        )
            if mod and node.level and node.level > 0 and mod in ("build_options", "export"):
                raise AssertionError(f"{path}: forbidden relative ImportFrom module {mod!r}")


def assert_build_options_package_import_dag(path: Path) -> None:
    """R1: ``build_options`` package surface must not import ``export`` or ``materials``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(("src.utils.export", "src.utils.materials")):
                    raise AssertionError(
                        f"{path}: build_options must not import {alias.name!r}"
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                continue
            mod = node.module
            if mod and (
                mod.startswith("src.utils.export") or mod.startswith("src.utils.materials")
            ):
                raise AssertionError(f"{path}: build_options must not import from {mod!r}")
            if mod == "src.utils":
                for alias in node.names:
                    if alias.name in ("export", "materials"):
                        raise AssertionError(
                            f"{path}: build_options must not import from src.utils: {alias.name!r}"
                        )
            if mod is None and node.level and node.level > 0:
                for alias in node.names:
                    if alias.name in ("export", "materials"):
                        raise AssertionError(
                            f"{path}: forbidden relative import of {alias.name!r}"
                        )
            if mod and node.level and node.level > 0 and mod in ("export", "materials"):
                raise AssertionError(f"{path}: forbidden relative ImportFrom module {mod!r}")


def legacy_utils_import_violations(path: Path) -> list[str]:
    """Return human-readable violations for forbidden legacy ``src.utils.*`` import paths."""
    out: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name.startswith("src.utils.animated_build_options"):
                    out.append(f"{path}: Import {name!r}")
                if name in {
                    "src.utils.constants",
                    "src.utils.enemy_slug_registry",
                    "src.utils.export_naming",
                    "src.utils.export_subdir",
                }:
                    out.append(f"{path}: Import {name!r}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module
            if mod in (
                "src.utils.constants",
                "src.utils.enemy_slug_registry",
                "src.utils.export_naming",
                "src.utils.export_subdir",
            ):
                out.append(f"{path}: ImportFrom {mod!r}")
            if mod and mod.startswith("src.utils.animated_build_options"):
                out.append(f"{path}: ImportFrom {mod!r}")
            if mod == "src.utils":
                for alias in node.names:
                    if alias.name in (
                        "constants",
                        "enemy_slug_registry",
                        "export_naming",
                        "export_subdir",
                        "animated_build_options",
                    ):
                        out.append(f"{path}: from src.utils import {alias.name!r}")
    return out
