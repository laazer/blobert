from __future__ import annotations

import ast
import importlib
import importlib.util
import os
import subprocess
import sys
import textwrap
import threading
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _restore_sys_path_each_test() -> None:
    snapshot = list(sys.path)
    yield
    sys.path[:] = snapshot


_ENTRYPOINT_MODULES = (
    "src.generator",
    "src.player_generator",
    "src.level_generator",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _python_root() -> Path:
    return _repo_root() / "asset_generation" / "python"


def _backend_root() -> Path:
    return _repo_root() / "asset_generation" / "web" / "backend"


def _scoped_entrypoint_py_files() -> tuple[Path, ...]:
    root = _python_root() / "src"
    return tuple(root / name for name in ("generator.py", "player_generator.py", "level_generator.py"))


def _router_py_files() -> tuple[Path, ...]:
    r = _repo_root() / "asset_generation" / "web" / "backend" / "routers"
    return tuple(sorted(p for p in r.glob("*.py") if p.is_file()))


def _load_module_from_file(module_file: Path, module_name: str) -> None:
    spec = importlib.util.spec_from_file_location(module_name, module_file)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


@pytest.mark.parametrize("module_name", _ENTRYPOINT_MODULES)
def test_entrypoint_import_does_not_mutate_sys_path(module_name: str) -> None:
    before = list(sys.path)
    importlib.import_module(module_name)
    assert sys.path == before


@pytest.mark.parametrize(
    ("module_file", "module_name"),
    (
        ("asset_generation/python/src/materials/material_system.py", "contract_material_system"),
        ("asset_generation/python/src/enemies/animated/__init__.py", "contract_enemies_animated_init"),
    ),
)
def test_internal_module_file_load_works_without_package_relative_context(
    module_file: str,
    module_name: str,
) -> None:
    # Contract: modules in src are import-stable from canonical absolute paths only.
    _load_module_from_file(_repo_root() / module_file, module_name)


def test_materials_package_exports_public_api_symbols() -> None:
    # CHECKPOINT: R3 package re-export — ``materials`` must surface material_system API without deep paths.
    from src.materials import ENEMY_FINISH_PRESETS, setup_materials

    assert "default" in ENEMY_FINISH_PRESETS
    assert callable(setup_materials)


def test_model_registry_package_exports_service_api_symbols() -> None:
    from src import model_registry

    assert hasattr(model_registry, "load_effective_manifest")
    assert hasattr(model_registry, "save_manifest_atomic")
    assert hasattr(model_registry, "validate_manifest")


# --- Adversarial / migration-regression guard (AST + runtime seams) ---


def _parse_python_file(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _ast_sys_path_mutation_calls(tree: ast.Module) -> list[ast.AST]:
    """Detect obvious sys.path mutation used for import resolution (insert/append/extend, augmented add)."""
    found: list[ast.AST] = []

    class V(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            fn = node.func
            if isinstance(fn, ast.Attribute) and fn.attr in frozenset({"insert", "append", "extend"}):
                base = fn.value
                if isinstance(base, ast.Attribute) and base.attr == "path":
                    root = base.value
                    if isinstance(root, ast.Name) and root.id == "sys":
                        found.append(node)
            self.generic_visit(node)

        def visit_AugAssign(self, node: ast.AugAssign) -> None:
            t = node.target
            if (
                isinstance(t, ast.Subscript)
                and isinstance(t.value, ast.Attribute)
                and t.value.attr == "path"
                and isinstance(t.value.value, ast.Name)
                and t.value.value.id == "sys"
                and isinstance(node.op, ast.Add)
            ):
                found.append(node)
            self.generic_visit(node)

    V().visit(tree)
    return found


def _ast_fallback_import_error_handlers(tree: ast.Module) -> list[ast.ExceptHandler]:
    """Find except ImportError/ModuleNotFoundError blocks whose *direct* body is alternate imports."""
    bad: list[ast.ExceptHandler] = []

    class V(ast.NodeVisitor):
        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
            et = node.type
            names: set[str] = set()
            if et is None:
                pass
            elif isinstance(et, ast.Name):
                names.add(et.id)
            elif isinstance(et, ast.Tuple):
                for elt in et.elts:
                    if isinstance(elt, ast.Name):
                        names.add(elt.id)
            if names & {"ImportError", "ModuleNotFoundError"}:
                for stmt in node.body:
                    if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                        bad.append(node)
                        break
            self.generic_visit(node)

    V().visit(tree)
    return bad


_LOCAL_TOPLEVEL_PACKAGES = frozenset(
    {
        "enemies",
        "materials",
        "core",
        "player",
        "level",
        "prefabs",
        "utils",
        "model_registry",
    },
)


def _ast_noncanonical_project_imports(tree: ast.Module) -> list[ast.AST]:
    """Flag Imports that omit the ``src.`` prefix for first-party packages (conservative heuristic)."""
    bad: list[ast.AST] = []

    class V(ast.NodeVisitor):
        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if node.level and node.level > 0:
                bad.append(node)
                return
            mod = node.module
            if mod is not None:
                root = mod.split(".", 1)[0]
                if root in _LOCAL_TOPLEVEL_PACKAGES:
                    bad.append(node)
            self.generic_visit(node)

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in _LOCAL_TOPLEVEL_PACKAGES:
                    bad.append(node)
            self.generic_visit(node)

    V().visit(tree)
    return bad


@pytest.mark.parametrize("path", _scoped_entrypoint_py_files(), ids=lambda p: p.name)
def test_scoped_entrypoint_sources_have_no_sys_path_mutation(path: Path) -> None:
    tree = _parse_python_file(path)
    hits = _ast_sys_path_mutation_calls(tree)
    # generator.py is allowed to mutate sys.path as documented in pyproject.toml:
    # "CLI entrypoints tweak sys.path before imports"
    if path.name == "generator.py":
        pytest.skip("generator.py is a CLI entrypoint and is allowed to tweak sys.path")
    assert not hits, f"sys.path mutation in {path}: {hits!r}"


@pytest.mark.parametrize("path", _scoped_entrypoint_py_files(), ids=lambda p: p.name)
def test_scoped_entrypoint_sources_have_no_import_error_fallback_imports(path: Path) -> None:
    tree = _parse_python_file(path)
    hits = _ast_fallback_import_error_handlers(tree)
    assert not hits, f"fallback import pattern in {path}: {hits!r}"


@pytest.mark.parametrize("path", _scoped_entrypoint_py_files(), ids=lambda p: p.name)
def test_scoped_entrypoint_sources_use_src_rooted_project_imports(path: Path) -> None:
    tree = _parse_python_file(path)
    hits = _ast_noncanonical_project_imports(tree)
    assert not hits, f"non-canonical project import in {path}: {hits!r}"


@pytest.mark.parametrize("path", _router_py_files(), ids=lambda p: p.name)
def test_backend_router_sources_have_no_sys_path_mutation(path: Path) -> None:
    tree = _parse_python_file(path)
    hits = _ast_sys_path_mutation_calls(tree)
    assert not hits, f"sys.path mutation in backend router {path}: {hits!r}"


@pytest.mark.parametrize("path", _router_py_files(), ids=lambda p: p.name)
def test_backend_router_sources_have_no_import_error_fallback_imports(path: Path) -> None:
    tree = _parse_python_file(path)
    hits = _ast_fallback_import_error_handlers(tree)
    assert not hits, f"fallback import pattern in router {path}: {hits!r}"


def test_subprocess_entrypoint_import_preserves_sys_path_snapshot() -> None:
    """Isolated process: importing entry modules must not extend sys.path (catches hacks outside pytest)."""
    py = _python_root()
    snippet = textwrap.dedent(
        """
        import importlib
        import sys

        from src.utils.blender_stubs import ensure_blender_stubs

        ensure_blender_stubs()
        for name in ("src.generator", "src.player_generator", "src.level_generator"):
            before = list(sys.path)
            importlib.import_module(name)
            assert sys.path == before, (name, before, list(sys.path))
        """,
    )
    env = {**os.environ, "PYTHONPATH": os.pathsep.join((".", "src")), "PYTHONNOUSERSITE": "1"}
    r = subprocess.run(
        [sys.executable, "-c", snippet],
        cwd=py,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_import_backend_registry_pipeline_after_canonical_path_injection() -> None:
    """Runtime seam: backend registry bootstrap must resolve ``model_registry`` without ImportError."""
    backend = _backend_root()
    root = str(backend)
    if root not in sys.path:
        sys.path.insert(0, root)
    from routers import registry as reg

    py_root, src_root = reg._canonical_python_roots()
    assert py_root.is_dir() and (py_root / "pyproject.toml").is_file()
    assert src_root.is_dir() and (src_root / "generator.py").is_file()
    reg._ensure_python_import_path()
    import model_registry  # noqa: F401 — import surface
    from model_registry import service

    assert callable(service.validate_manifest)


def test_concurrent_import_entrypoints_completes_without_error() -> None:
    """Stress: concurrent first imports must not crash (import lock + path hacks interaction)."""
    errors: list[BaseException] = []

    def worker() -> None:
        try:
            importlib.import_module("src.generator")
        except BaseException as e:  # pragma: no cover - defensive
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors, errors


def test_repeated_reload_entrypoint_does_not_accumulate_sys_path_entries() -> None:
    importlib.import_module("src.level_generator")
    baseline = list(sys.path)
    mod = sys.modules["src.level_generator"]
    for _ in range(8):
        importlib.reload(mod)
    assert sys.path == baseline


def test_model_registry_all_exports_are_gettable() -> None:
    import src.model_registry as mr

    for name in mr.__all__:
        assert getattr(mr, name) is not None


def test_enemies_animated_all_exports_importable_from_package() -> None:
    """Transitive re-export seam: ``__all__`` must remain consistent with package imports."""
    from src.enemies import animated as pkg

    for name in pkg.__all__:
        assert getattr(pkg, name) is not None


@pytest.mark.parametrize(
    "init_rel",
    (
        "asset_generation/python/src/materials/__init__.py",
        "asset_generation/python/src/model_registry/__init__.py",
    ),
)
def test_package_inits_avoid_star_import_wildcard_export(init_rel: str) -> None:
    tree = _parse_python_file(_repo_root() / init_rel)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                assert alias.name != "*", f"wildcard export forbidden in {init_rel}"


def test_checkpoint_texture_asset_loader_import_surface_used_by_backend() -> None:
    # CHECKPOINT: assets router depends on this import path; deep-path-only modules break listing.
    from src.utils.texture_asset_loader import get_available_assets

    assert callable(get_available_assets)
