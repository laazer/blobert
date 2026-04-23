from __future__ import annotations

import pytest

from src.model_registry import service as registry_service


def _policy_api():
    fn = getattr(registry_service, "normalize_registry_relative_glb_path", None)
    assert callable(fn)
    return fn


def test_service_exposes_authoritative_path_policy_api() -> None:
    normalize = _policy_api()
    assert normalize("animated_exports/spider_animated_00.glb") == "animated_exports/spider_animated_00.glb"


@pytest.mark.parametrize(
    ("raw_path", "expected"),
    [
        ("animated_exports/./spider_animated_00.glb", "animated_exports/spider_animated_00.glb"),
        ("exports//imp_animated_00.glb", "exports/imp_animated_00.glb"),
    ],
)
def test_policy_canonicalizes_safe_equivalent_paths(raw_path: str, expected: str) -> None:
    normalize = _policy_api()
    assert normalize(raw_path) == expected


@pytest.mark.parametrize(
    "raw_path",
    [
        "../animated_exports/spider_animated_00.glb",
        "animated_exports/%2e%2e/spider_animated_00.glb",
        "animated_exports/%252e%252e/spider_animated_00.glb",
        "/tmp/escape.glb",
        "res://animated_exports/spider_animated_00.glb",
        "animated_exports/spider_animated_00.gltf",
        "animated_exports/spider_animated_00.glb%00.png",
        "concept_art/spider_animated_00.glb",
        r"animated_exports\spider_animated_00.glb",
        "",
        "   ",
    ],
)
def test_policy_rejects_forbidden_or_malformed_path_classes(raw_path: str) -> None:
    normalize = _policy_api()
    with pytest.raises(ValueError):
        normalize(raw_path)


def test_policy_is_deterministic_for_repeated_input() -> None:
    normalize = _policy_api()
    raw_path = "exports//spider_animated_00.glb"
    first = normalize(raw_path)
    second = normalize(raw_path)
    third = normalize(raw_path)
    assert first == second == third
