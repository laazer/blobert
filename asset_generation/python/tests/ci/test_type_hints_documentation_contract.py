from __future__ import annotations

import ast
import shutil
import subprocess
from pathlib import Path

import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _python_root() -> Path:
    return _repo_root() / "asset_generation" / "python"


_SCOPED_MODULES: tuple[Path, ...] = (
    _python_root() / "src" / "generator.py",
    _python_root() / "src" / "materials" / "gradient_generator.py",
    _python_root() / "src" / "model_registry" / "migrations.py",
    _python_root() / "src" / "model_registry" / "schema.py",
    _python_root() / "src" / "model_registry" / "service.py",
)


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _annotation_is_bare_dict(node: ast.AST | None) -> bool:
    if node is None:
        return False
    if isinstance(node, ast.Name):
        return node.id == "dict"
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.strip() == "dict"
    return False


def _iter_annotations(tree: ast.Module) -> list[tuple[str, ast.AST]]:
    out: list[tuple[str, ast.AST]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            all_args = (
                list(node.args.posonlyargs)
                + list(node.args.args)
                + list(node.args.kwonlyargs)
            )
            if node.args.vararg and node.args.vararg.annotation is not None:
                all_args.append(node.args.vararg)
            if node.args.kwarg and node.args.kwarg.annotation is not None:
                all_args.append(node.args.kwarg)
            for arg in all_args:
                if arg.annotation is not None:
                    out.append((f"arg:{arg.arg}", arg.annotation))
            if node.returns is not None:
                out.append((f"return:{node.name}", node.returns))
        elif isinstance(node, ast.AnnAssign):
            out.append(("annassign", node.annotation))
    return out


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _function_annotation_stats(tree: ast.Module) -> tuple[int, int]:
    total = 0
    typed = 0
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if _is_dunder(node.name):
            continue
        total += 1

        args_to_check = list(node.args.posonlyargs) + list(node.args.args) + list(node.args.kwonlyargs)
        if node.args.vararg is not None:
            args_to_check.append(node.args.vararg)
        if node.args.kwarg is not None:
            args_to_check.append(node.args.kwarg)

        args_ok = True
        for arg in args_to_check:
            if arg.arg in {"self", "cls"}:
                continue
            if arg.annotation is None:
                args_ok = False
                break

        if args_ok and node.returns is not None:
            typed += 1
    return total, typed


def test_scoped_modules_have_module_docstrings() -> None:
    missing: list[str] = []
    for path in _SCOPED_MODULES:
        doc = ast.get_docstring(_parse(path))
        if doc is None or not doc.strip():
            missing.append(path.name)
    assert not missing, f"missing module docstrings: {missing}"


def test_scoped_modules_use_no_bare_dict_annotations() -> None:
    hits: list[str] = []
    for path in _SCOPED_MODULES:
        tree = _parse(path)
        for label, annotation in _iter_annotations(tree):
            if _annotation_is_bare_dict(annotation):
                hits.append(f"{path.name}:{label}")
    assert not hits, f"bare dict annotation(s) detected: {hits}"


@pytest.mark.parametrize(
    ("module_name", "function_name"),
    (
        ("model_registry/schema.py", "validate_manifest"),
        ("model_registry/schema.py", "_normalize_registry_family_block"),
        ("model_registry/service.py", "patch_player_active_visual"),
        ("model_registry/service.py", "sync_discovered_animated_glb_versions"),
        ("generator.py", "_build_options_for_current_enemy"),
    ),
)
def test_complex_scoped_functions_have_docstrings(module_name: str, function_name: str) -> None:
    path = _python_root() / "src" / module_name
    tree = _parse(path)
    func_node = next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name
        ),
        None,
    )
    assert func_node is not None, f"missing function {function_name!r} in {module_name}"
    assert ast.get_docstring(func_node), f"missing docstring for {module_name}:{function_name}"


def test_scoped_function_annotation_ratio_is_at_least_ninety_percent() -> None:
    total = 0
    typed = 0
    for path in _SCOPED_MODULES:
        t, y = _function_annotation_stats(_parse(path))
        total += t
        typed += y
    assert total > 0
    ratio = typed / total
    assert ratio >= 0.90, f"annotation coverage below threshold: {typed}/{total} ({ratio:.2%})"


def test_generator_build_options_parser_isolated_by_enemy_type(monkeypatch: pytest.MonkeyPatch) -> None:
    from src import generator

    calls: list[object] = []

    def fake_parse(raw_json: str | None) -> dict[str, object]:
        calls.append(raw_json)
        return {"imp": {"count": 2}, "slug": {"count": 3}}

    def fake_for_enemy(enemy_type: str, raw: dict[str, object]) -> dict[str, object]:
        return {"enemy_type": enemy_type, "raw_keys": sorted(raw.keys())}

    monkeypatch.setenv("BLOBERT_BUILD_OPTIONS_JSON", '{"imp":{"count":2},"slug":{"count":3}}')
    monkeypatch.setattr(generator, "parse_build_options_json", fake_parse)
    monkeypatch.setattr(generator, "options_for_enemy", fake_for_enemy)

    out = generator._build_options_for_current_enemy("slug")

    assert calls == ['{"imp":{"count":2},"slug":{"count":3}}']
    assert out == {"enemy_type": "slug", "raw_keys": ["imp", "slug"]}


def test_mypy_strict_passes_for_scoped_modules() -> None:
    if shutil.which("mypy") is None:
        pytest.skip("mypy is not installed in this environment")
    cmd = [
        "mypy",
        "--strict",
        *[str(path.relative_to(_python_root())) for path in _SCOPED_MODULES],
    ]
    run = subprocess.run(
        cmd,
        cwd=_python_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 0, run.stdout + run.stderr
