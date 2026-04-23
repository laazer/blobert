"""Centralized adapter for asset-generation Python import/bootstrap behavior."""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from threading import Lock
from types import ModuleType

BACKEND_DIR = Path(__file__).resolve().parent.parent
_ROOT_OVERRIDE_ENV = "BLOBERT_ASSET_PYTHON_ROOT"
_ROOT_STRATEGY_ENV = "BLOBERT_ASSET_PYTHON_ROOT_STRATEGY"
_ROOT_STRATEGY_SRC = "src"
_ROOT_STRATEGY_PACKAGE = "blobert_asset_gen"
_ALLOWED_ROOT_STRATEGIES = frozenset({_ROOT_STRATEGY_SRC, _ROOT_STRATEGY_PACKAGE})

_bootstrap_lock = Lock()
_bootstrapped = False
_cached_root: Path | None = None


class PythonBridgeError(ImportError):
    """Base class for backend-python adapter failures."""


class UnresolvedPythonRootError(PythonBridgeError):
    """No valid asset-generation python root could be resolved."""


class InvalidPythonRootLayoutError(PythonBridgeError):
    """Python root was configured but does not point at a valid directory."""


class BlenderBootstrapError(PythonBridgeError):
    """Blender stub bootstrap failed."""


class AssetModuleImportError(PythonBridgeError):
    """Importing a python asset module failed."""


def _python_container_root() -> Path:
    asset_generation_root = BACKEND_DIR.parent.parent
    return asset_generation_root / "python"


def _normalize_strategy(value: str | None) -> str:
    strategy = (value or _ROOT_STRATEGY_SRC).strip().lower()
    if strategy not in _ALLOWED_ROOT_STRATEGIES:
        raise InvalidPythonRootLayoutError(
            f"unsupported python root strategy {strategy!r}; "
            f"expected one of {sorted(_ALLOWED_ROOT_STRATEGIES)!r}",
        )
    return strategy


def _candidate_roots_for_strategy(python_container: Path, strategy: str) -> tuple[Path, ...]:
    if strategy == _ROOT_STRATEGY_PACKAGE:
        return (python_container / "blobert_asset_gen",)
    return (python_container / "src",)


def resolve_python_root() -> Path:
    """Resolve the single active python import root for backend runtime."""
    override = os.getenv(_ROOT_OVERRIDE_ENV)
    if override:
        candidate = Path(override).expanduser()
        if not candidate.is_dir():
            raise InvalidPythonRootLayoutError(
                f"override root is not a directory: {candidate}",
            )
        return candidate.resolve()

    strategy = _normalize_strategy(os.getenv(_ROOT_STRATEGY_ENV))
    python_container = _python_container_root()
    for candidate in _candidate_roots_for_strategy(python_container, strategy):
        if candidate.is_dir():
            return candidate.resolve()

    raise UnresolvedPythonRootError(
        f"no resolvable python root for strategy {strategy!r} under {python_container}",
    )


def bootstrap_python_runtime() -> Path:
    """Ensure import path + blender stubs are initialized exactly once."""
    global _bootstrapped, _cached_root
    if _bootstrapped and _cached_root is not None:
        _ensure_blender_stubs(_cached_root)
        return _cached_root

    with _bootstrap_lock:
        if _bootstrapped and _cached_root is not None:
            return _cached_root

        root = resolve_python_root()
        for injection_path in _injection_paths(root):
            path_text = str(injection_path)
            if path_text not in sys.path:
                sys.path.insert(0, path_text)

        try:
            _ensure_blender_stubs(root)
        except Exception as exc:
            _bootstrapped = False
            _cached_root = None
            raise BlenderBootstrapError(f"blender bootstrap failed: {exc}") from exc

        _cached_root = root
        _bootstrapped = True
        return root


def _validate_module_name(module_name: str) -> None:
    if not module_name or module_name.startswith(".") or ".." in module_name:
        raise AssetModuleImportError(f"invalid module import target: {module_name!r}")


def _resolve_import_name(module_name: str, root: Path) -> str:
    if root.name == "blobert_asset_gen" and module_name.startswith("src."):
        return f"blobert_asset_gen.{module_name[len('src.'):]}"
    return module_name


def _injection_paths(root: Path) -> tuple[Path, ...]:
    if root.name == "src":
        return (root.parent, root)
    return (root,)


def _ensure_blender_stubs(root: Path) -> None:
    try:
        blender_stubs_module = "utils.blender_stubs" if root.name == "src" else "src.utils.blender_stubs"
        blender_stubs = importlib.import_module(blender_stubs_module)
        blender_stubs.ensure_blender_stubs()
    except ModuleNotFoundError as exc:
        parent_package = blender_stubs_module.split(".", maxsplit=1)[0]
        if exc.name not in {blender_stubs_module, parent_package}:
            raise
        # Minimal-contract tests can bootstrap against an empty root tree.
        return


def import_asset_module(module_name: str) -> ModuleType:
    """Bootstrap runtime and import an asset-generation python module."""
    _validate_module_name(module_name)
    root = bootstrap_python_runtime()
    normalized_module_name = _resolve_import_name(module_name, root)
    try:
        return importlib.import_module(normalized_module_name)
    except Exception as exc:
        raise AssetModuleImportError(
            f"asset module import failed for {module_name!r}: {exc}",
        ) from exc
