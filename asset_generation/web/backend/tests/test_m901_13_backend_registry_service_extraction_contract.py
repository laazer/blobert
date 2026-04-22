from __future__ import annotations

import ast
from importlib.util import find_spec
from pathlib import Path

import services.registry_mutation as registry_mutation
import services.registry_query as registry_query
from routers import registry as registry_router


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _top_level_defined_names(source: str) -> set[str]:
    tree = ast.parse(source)
    out: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.add(node.name)
    return out


def test_extracted_service_modules_export_expected_surface() -> None:
    assert hasattr(registry_mutation, "load_model_registry_service")
    assert hasattr(registry_query, "load_existing_candidates_from_registry")
    assert hasattr(registry_query, "load_registry_json_unvalidated")
    assert hasattr(registry_query, "normalize_registry_relative_glb_path_for_http")
    assert hasattr(registry_query, "safe_is_file_under_python_root")
    assert hasattr(registry_query, "resolve_enemy_identity_path")
    assert hasattr(registry_query, "resolve_player_identity_path")


def test_registry_router_does_not_embed_query_workflow_helpers() -> None:
    # This is a mechanical guardrail: load-existing query helpers were extracted to
    # `services.registry_query` to keep the router transport-only.
    source = _read_text(Path(registry_router.__file__).resolve())
    defined = _top_level_defined_names(source)
    not_allowed = {
        "load_registry_json_unvalidated",
        "load_existing_candidates_from_registry",
        "player_export_rows_for_load_existing",
        "resolve_enemy_identity_path",
        "resolve_player_identity_path",
    }
    assert defined.isdisjoint(not_allowed)


def test_import_package_layout_is_resolvable() -> None:
    assert find_spec("services.registry_query") is not None
    assert find_spec("services.registry_mutation") is not None
