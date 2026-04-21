"""
M901-02 — Runtime contracts for layered ``model_registry`` (schema / store / migrations / service).

These tests encode spec R1–R8 behaviors: dependency direction, store I/O without MRVC
validation, single ``SCHEMA_VERSION`` source, and frozen service orchestration surface.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _model_registry_dir() -> Path:
    return _repo_root() / "asset_generation" / "python" / "src" / "model_registry"


@pytest.fixture(autouse=True)
def _require_layering_module_files_exist() -> None:
    """M901-02 gate: schema/store/migrations must exist before runtime or AST contracts run."""
    base = _model_registry_dir()
    missing = [n for n in ("schema.py", "store.py", "migrations.py") if not (base / n).is_file()]
    if missing:
        pytest.fail(f"expected M901-02 module file(s) under {base}: {missing}")


def _parse_py(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _import_layer_submodules() -> tuple[Any, Any, Any]:
    """Import layering modules (fails until M901-02 extraction lands)."""
    import importlib

    schema = importlib.import_module("src.model_registry.schema")
    store = importlib.import_module("src.model_registry.store")
    migrations = importlib.import_module("src.model_registry.migrations")
    return schema, store, migrations


def test_store_module_has_registry_io_surface() -> None:
    """Spec R3: path helper plus raw read/write without MRVC validation in the store layer."""
    _, store, _ = _import_layer_submodules()
    assert callable(getattr(store, "registry_path", None))
    write = getattr(store, "write_registry_json_atomic", None)
    read = getattr(store, "read_registry_object", None)
    assert callable(write), "store must expose write_registry_json_atomic (atomic JSON, no MRVC)"
    assert callable(read), "store must expose read_registry_object (parse-only / missing-file signal)"


def test_store_write_does_not_apply_validate_manifest(tmp_path: Path) -> None:
    """Spec R3/R8 — store passes through parsed dict; MRVC lives in schema/service only."""
    schema_mod, store, _ = _import_layer_submodules()
    validate_manifest = schema_mod.validate_manifest
    junk: dict[str, Any] = {"not_a_manifest": True}
    with pytest.raises(ValueError):
        validate_manifest(junk)  # type: ignore[arg-type]

    store.write_registry_json_atomic(tmp_path, junk)
    path = store.registry_path(tmp_path)
    assert path.is_file()
    round_trip = json.loads(path.read_text(encoding="utf-8"))
    assert round_trip == junk

    raw_read = store.read_registry_object(tmp_path)
    assert raw_read == junk


def test_store_read_registry_object_missing_file_is_none(tmp_path: Path) -> None:
    _, store, _ = _import_layer_submodules()
    assert store.read_registry_object(tmp_path) is None


def test_store_json_writes_use_indent_two_sort_keys_and_trailing_newline(tmp_path: Path) -> None:
    """Spec R3 — deterministic formatting unless tests assert otherwise."""
    _, store, _ = _import_layer_submodules()
    payload = {"z": 1, "a": 2}
    store.write_registry_json_atomic(tmp_path, payload)
    text = store.registry_path(tmp_path).read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert json.loads(text) == {"a": 2, "z": 1}
    assert text.index('"a"') < text.index('"z"')


def test_registry_path_matches_between_store_and_service(tmp_path: Path) -> None:
    """Spec R3/R5 — single canonical ``registry_path`` (store owns definition or shared delegate)."""
    _, store, _ = _import_layer_submodules()
    from src.model_registry import service

    assert store.registry_path(tmp_path) == service.registry_path(tmp_path)


def test_service_validate_manifest_is_schema_api() -> None:
    """Spec R2/R5 — callers keep using ``service.validate_manifest`` as a thin delegate."""
    schema_mod, _, _ = _import_layer_submodules()
    from src.model_registry import service

    assert service.validate_manifest is schema_mod.validate_manifest


def test_schema_schema_version_matches_migrations() -> None:
    """Spec R1/R2 — ``SCHEMA_VERSION`` is owned by migrations; schema imports the same value."""
    schema_mod, _, migrations_mod = _import_layer_submodules()
    assert migrations_mod.SCHEMA_VERSION == 1
    sv = getattr(schema_mod, "SCHEMA_VERSION", None)
    assert sv is not None
    assert sv == migrations_mod.SCHEMA_VERSION


def test_default_migrated_manifest_matches_service_and_migrations() -> None:
    _, _, migrations_mod = _import_layer_submodules()
    from src.model_registry import service

    a = service.default_migrated_manifest()
    b = migrations_mod.default_migrated_manifest()
    assert a == b


def test_private_migration_helpers_alias_between_service_and_migrations() -> None:
    """Spec R4/R5 — legacy PAV helpers remain importable from service for compatibility."""
    _, _, migrations_mod = _import_layer_submodules()
    from src.model_registry import service

    assert (
        service._derive_player_active_visual_from_block
        is migrations_mod._derive_player_active_visual_from_block
    )
    assert service._legacy_pav_to_player_block is migrations_mod._legacy_pav_to_player_block


def test_schema_defines_at_least_one_public_typeddict() -> None:
    """Spec R2 — manifest / row TypedDict (or equivalent) surfaces live in schema."""
    from typing import is_typeddict

    schema_mod, _, _ = _import_layer_submodules()
    public = (n for n in dir(schema_mod) if not n.startswith("_"))
    typed = [n for n in public if is_typeddict(getattr(schema_mod, n))]
    assert typed, "schema must define at least one TypedDict for manifest shapes"


def test_layer_import_order_succeeds_migrations_store_schema_service() -> None:
    """Spec R1 — directed acyclic graph; safe reload order must not deadlock."""
    env = {**os.environ, "PYTHONPATH": os.pathsep.join((".", "src")), "PYTHONNOUSERSITE": "1"}
    py_root = _repo_root() / "asset_generation" / "python"
    snippet = textwrap.dedent(
        """
        import importlib

        import src.model_registry.migrations  # noqa: F401
        import src.model_registry.store  # noqa: F401
        import src.model_registry.schema  # noqa: F401
        import src.model_registry.service  # noqa: F401

        importlib.invalidate_caches()
        import src.model_registry.migrations as m1
        import src.model_registry.store as s1
        import src.model_registry.schema as c1
        import src.model_registry.service as v1

        assert m1.SCHEMA_VERSION == 1
        assert callable(s1.write_registry_json_atomic)
        assert callable(c1.validate_manifest)
        assert callable(v1.load_effective_manifest)
        """,
    )
    proc = subprocess.run(
        [sys.executable, "-c", snippet],
        cwd=py_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_src_model_registry_import_smoke_matches_spec_r1() -> None:
    env = {**os.environ, "PYTHONPATH": os.pathsep.join((".", "src")), "PYTHONNOUSERSITE": "1"}
    py_root = _repo_root() / "asset_generation" / "python"
    snippet = textwrap.dedent(
        """
        from src.model_registry import service
        from src.model_registry.service import load_effective_manifest, validate_manifest

        assert callable(validate_manifest)
        assert callable(load_effective_manifest)
        assert callable(service.registry_path)
        """,
    )
    proc = subprocess.run(
        [sys.executable, "-c", snippet],
        cwd=py_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_migrations_source_does_not_import_schema_module() -> None:
    """Spec R1/R4 — migrations is a pure transform layer; no schema/service/store imports."""
    path = _model_registry_dir() / "migrations.py"
    tree = _parse_py(path)
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module
            if node.level >= 1 and mod in frozenset({"schema", "service", "store"}):
                bad.append(f"relative import to sibling .{mod}")
            if mod in frozenset(
                {
                    "src.model_registry.schema",
                    "src.model_registry.service",
                    "src.model_registry.store",
                },
            ):
                bad.append(mod)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("src.model_registry."):
                    tail = alias.name.split("src.model_registry.", 1)[1]
                    if tail.split(".", 1)[0] in frozenset({"schema", "service", "store"}):
                        bad.append(alias.name)
    assert not bad, f"unexpected imports in migrations.py: {bad}"


def test_store_source_does_not_import_model_registry_layers() -> None:
    """Spec R1/R3 — store is stdlib + pathlib I/O only (no schema / migrations / service)."""
    path = _model_registry_dir() / "store.py"
    tree = _parse_py(path)
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module
            if node.level >= 1 and mod in frozenset({"schema", "migrations", "service"}):
                bad.append(f"relative import to sibling .{mod}")
            if mod in frozenset(
                {
                    "src.model_registry.schema",
                    "src.model_registry.migrations",
                    "src.model_registry.service",
                },
            ):
                bad.append(mod)
            elif mod is not None and mod.startswith("src.model_registry."):
                bad.append(mod)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name.startswith("src.model_registry."):
                    bad.append(name)
    assert not bad, f"store.py must not import model_registry layers: {bad}"


def test_model_registry_layers_avoid_sys_path_mutation() -> None:
    """Spec R1 — align with M901-01: no sys.path hacks inside model_registry."""
    base = _model_registry_dir()
    for fname in ("service.py", "schema.py", "store.py", "migrations.py"):
        path = base / fname
        tree = _parse_py(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                if isinstance(fn, ast.Attribute) and fn.attr in {"insert", "append", "extend"}:
                    if isinstance(fn.value, ast.Attribute) and fn.value.attr == "path":
                        if isinstance(fn.value.value, ast.Name) and fn.value.value.id == "sys":
                            pytest.fail(f"{fname} mutates sys.path: {ast.dump(node)}")
            if isinstance(node, ast.AugAssign):
                t = node.target
                if (
                    isinstance(t, ast.Attribute)
                    and t.attr == "path"
                    and isinstance(t.value, ast.Name)
                    and t.value.id == "sys"
                ):
                    pytest.fail(f"{fname} augments sys.path")


def test_model_registry_python_sources_do_not_import_pydantic() -> None:
    """Spec R6 — pydantic stays in backend routers; domain package stays lean."""
    base = _model_registry_dir()
    for path in sorted(base.glob("*.py")):
        tree = _parse_py(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module in frozenset({"pydantic", "pydantic_settings"}):
                    pytest.fail(f"{path.name} imports {node.module}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    if root == "pydantic":
                        pytest.fail(f"{path.name} imports pydantic")


def test_schema_imports_migrations_for_schema_version_only_no_cycle() -> None:
    """Spec R1 — schema imports SCHEMA_VERSION from migrations; migrations never imports schema."""
    sch = _model_registry_dir() / "schema.py"
    tree = _parse_py(sch)
    imports_sv = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        mod = node.module
        targets = {a.name for a in node.names}
        if "SCHEMA_VERSION" not in targets:
            continue
        if mod in frozenset({"src.model_registry.migrations", "migrations"}):
            imports_sv = True
            break
        if node.level >= 1 and mod == "migrations":
            imports_sv = True
            break
    assert imports_sv, "schema.py must import SCHEMA_VERSION from migrations (single source of truth)"
