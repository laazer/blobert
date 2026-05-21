"""
OpenAPI → JSON Schema harness for contract tests (M902-26 Req 01).

Loads live ``app.openapi()``; resolves ``$ref`` / ``allOf``; validates responses with
``jsonschema``. Tier A routes use full component schemas; Tier B uses structural anchors
when OpenAPI documents an empty ``{}`` response schema.
"""

from __future__ import annotations

import copy
import json
import pathlib
import sys
from typing import Any, Literal

import jsonschema
from jsonschema import Draft202012Validator

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[2].parent / "web" / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

_OPENAPI_CACHE = (
    pathlib.Path(__file__).resolve().parents[2].parent
    / "web"
    / "frontend"
    / "scripts"
    / "fixtures"
    / "openapi.cached.json"
)

TIER_A_OPERATIONS: frozenset[tuple[str, str]] = frozenset(
    {
        ("GET", "/api/health"),
        ("GET", "/api/registry/model"),
        ("GET", "/api/meta/enemies"),
    }
)

HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete", "head", "options"})


class OpenAPIResolutionError(KeyError):
    """Missing path, operation, status, or unresolvable ``$ref``."""


def load_live_spec() -> dict[str, Any]:
    from main import app  # noqa: WPS433 — backend bootstrap via sys.path

    return app.openapi()


def load_cached_spec() -> dict[str, Any]:
    if not _OPENAPI_CACHE.is_file():
        raise FileNotFoundError(f"OpenAPI cache not found: {_OPENAPI_CACHE}")
    return json.loads(_OPENAPI_CACHE.read_text(encoding="utf-8"))


def _resolve_ref(spec: dict[str, Any], node: Any) -> Any:
    if not isinstance(node, dict):
        return node
    if "$ref" in node:
        ref = node["$ref"]
        if not ref.startswith("#/"):
            raise OpenAPIResolutionError(f"unsupported ref prefix: {ref}")
        parts = ref.lstrip("#/").split("/")
        target: Any = spec
        for part in parts:
            if not isinstance(target, dict) or part not in target:
                raise OpenAPIResolutionError(f"unresolvable ref: {ref}")
            target = target[part]
        return _resolve_ref(spec, copy.deepcopy(target))
    return {k: _resolve_ref(spec, v) for k, v in node.items()}


def _merge_allof(schemas: list[dict[str, Any]]) -> dict[str, Any]:
    merged: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
    required: list[str] = []
    for schema in schemas:
        if schema.get("type") and schema["type"] != "object":
            return schema
        props = schema.get("properties", {})
        if isinstance(props, dict):
            merged["properties"].update(props)
        req = schema.get("required", [])
        if isinstance(req, list):
            required.extend(str(r) for r in req)
        if schema.get("additionalProperties") is False:
            merged["additionalProperties"] = False
    if required:
        merged["required"] = sorted(set(required))
    if not merged["properties"]:
        merged.pop("properties", None)
    return merged


def _normalize_schema(spec: dict[str, Any], schema: Any) -> dict[str, Any]:
    resolved = _resolve_ref(spec, schema)
    if not isinstance(resolved, dict):
        raise OpenAPIResolutionError("response schema must resolve to object")
    if "allOf" in resolved:
        parts = [_normalize_schema(spec, part) for part in resolved["allOf"]]
        merged = _merge_allof(parts)
        for key, value in resolved.items():
            if key != "allOf":
                merged[key] = value
        return merged
    return resolved


def resolve_response_schema(
    spec: dict[str, Any],
    method: str,
    path: str,
    status_code: int | str,
) -> dict[str, Any]:
    method_key = method.lower()
    if method_key not in HTTP_METHODS:
        raise OpenAPIResolutionError(f"unsupported method: {method}")
    paths = spec.get("paths", {})
    if path not in paths:
        raise OpenAPIResolutionError(f"path not in OpenAPI: {path}")
    operation = paths[path].get(method_key)
    if operation is None:
        raise OpenAPIResolutionError(f"{method} not defined for {path}")
    status_key = str(status_code)
    responses = operation.get("responses", {})
    if status_key not in responses:
        raise OpenAPIResolutionError(f"status {status_key} not documented for {method} {path}")
    response = responses[status_key]
    content = response.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema", {})
    return _normalize_schema(spec, schema)


def resolve_request_schema(
    spec: dict[str, Any],
    method: str,
    path: str,
) -> dict[str, Any] | None:
    method_key = method.lower()
    paths = spec.get("paths", {})
    operation = paths[path][method_key]
    body = operation.get("requestBody")
    if not body:
        return None
    content = body.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema")
    if schema is None:
        return None
    return _normalize_schema(spec, schema)


def resolve_component_schema(spec: dict[str, Any], name: str) -> dict[str, Any]:
    components = spec.get("components", {}).get("schemas", {})
    if name not in components:
        raise OpenAPIResolutionError(f"component schema missing: {name}")
    return _normalize_schema(spec, components[name])


def _tier_for(method: str, path: str) -> Literal["A", "B"]:
    return "A" if (method.upper(), path) in TIER_A_OPERATIONS else "B"


def _schema_is_empty(schema: dict[str, Any]) -> bool:
    return schema == {} or (set(schema.keys()) <= {"title"} and not schema.get("properties"))


def _inline_all_refs(spec: dict[str, Any], node: Any) -> Any:
    if isinstance(node, list):
        return [_inline_all_refs(spec, item) for item in node]
    if isinstance(node, dict):
        if "$ref" in node:
            return _inline_all_refs(spec, _resolve_ref(spec, node))
        return {key: _inline_all_refs(spec, value) for key, value in node.items()}
    return node


def validate_instance(instance: Any, schema: dict[str, Any], *, spec: dict[str, Any] | None = None) -> None:
    resolved = _inline_all_refs(spec, schema) if spec is not None else schema
    Draft202012Validator(resolved).validate(instance)


def validate_tier_b_body(body: Any) -> None:
    if not isinstance(body, dict):
        raise jsonschema.ValidationError("Tier B JSON response must be an object")
    if len(body) == 0:
        raise jsonschema.ValidationError("Tier B JSON response must be non-empty")


def assert_error_detail(body: Any) -> None:
    if not isinstance(body, dict) or "detail" not in body:
        raise AssertionError("error response must include 'detail' key")


def validate_error_response(
    spec: dict[str, Any],
    body: Any,
    status_code: int,
    *,
    strict_validation_error: bool = True,
) -> None:
    assert_error_detail(body)
    if status_code == 422 and strict_validation_error:
        schema = resolve_component_schema(spec, "HTTPValidationError")
        validate_instance(body, schema, spec=spec)
        return
    if status_code in {400, 403, 404, 409, 500, 503}:
        if "HTTPValidationError" in spec.get("components", {}).get("schemas", {}):
            detail_schema = resolve_component_schema(spec, "HTTPValidationError")
            if isinstance(body.get("detail"), list):
                validate_instance(body, detail_schema, spec=spec)
                return
        detail_only = {
            "type": "object",
            "required": ["detail"],
            "properties": {"detail": {}},
            "additionalProperties": True,
        }
        validate_instance(body, detail_only, spec=spec)


def validate_response(
    spec: dict[str, Any],
    *,
    method: str,
    path: str,
    status_code: int,
    body: Any,
    content_type: str | None = None,
) -> None:
    if status_code >= 400:
        validate_error_response(spec, body, status_code)
        return

    tier = _tier_for(method, path)
    schema = resolve_response_schema(spec, method, path, status_code)

    if content_type and "application/json" not in content_type:
        return

    if tier == "A" and not _schema_is_empty(schema):
        validate_instance(body, schema, spec=spec)
        if schema.get("additionalProperties") is False and isinstance(body, dict):
            inlined = _inline_all_refs(spec, schema)
            extra = set(body) - set(inlined.get("properties", {}))
            if extra:
                raise jsonschema.ValidationError(f"unexpected top-level keys: {sorted(extra)}")
        return

    if not _schema_is_empty(schema):
        validate_instance(body, schema, spec=spec)
        return

    validate_tier_b_body(body)


class OpenAPIContract:
    """Session-scoped helper bound to one OpenAPI document."""

    def __init__(self, spec: dict[str, Any]) -> None:
        self.spec = spec

    def validate(
        self,
        response: Any,
        *,
        method: str,
        path: str,
        expected_status: int,
    ) -> Any:
        if response.status_code != expected_status:
            raise AssertionError(
                f"expected status {expected_status}, got {response.status_code}: {response.text[:500]}"
            )
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type or expected_status == 422:
            body = response.json()
            validate_response(
                self.spec,
                method=method,
                path=path,
                status_code=expected_status,
                body=body,
                content_type=content_type,
            )
            return body
        return None
