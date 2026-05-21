"""Harness unit tests for OpenAPI ``$ref`` / ``allOf`` resolution (M902-26 Req 01)."""

from __future__ import annotations

import pytest

from tests.api.openapi_contract import (
    OpenAPIResolutionError,
    _merge_allof,
    _normalize_schema,
    _resolve_ref,
    load_live_spec,
    resolve_component_schema,
    resolve_response_schema,
    validate_instance,
)


def test_resolve_ref_component_schema():
    spec = {
        "components": {
            "schemas": {
                "Child": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
            }
        }
    }
    resolved = _resolve_ref(spec, {"$ref": "#/components/schemas/Child"})
    assert resolved["required"] == ["id"]


def test_merge_allof_combines_required_fields():
    merged = _merge_allof(
        [
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]},
            {"type": "object", "properties": {"b": {"type": "integer"}}, "required": ["b"]},
        ]
    )
    assert set(merged.get("required", [])) == {"a", "b"}
    assert "a" in merged["properties"] and "b" in merged["properties"]


def test_live_health_response_schema_round_trip():
    spec = load_live_spec()
    schema = resolve_response_schema(spec, "GET", "/api/health", 200)
    validate_instance({"status": "ok"}, schema)


def test_resolve_component_http_validation_error():
    spec = load_live_spec()
    schema = resolve_component_schema(spec, "HTTPValidationError")
    assert "detail" in schema.get("properties", {})


def test_missing_path_raises():
    spec = load_live_spec()
    with pytest.raises(OpenAPIResolutionError):
        resolve_response_schema(spec, "GET", "/api/no-such-route", 200)
