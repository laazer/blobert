# M902-26: API Contract Testing

**Status:** COMPLETE  
**Target:** 2026-07-15

## Overview

Implement automated contract tests that verify backend responses match frontend expectations and vice versa. Catches API drift before deployment: if backend changes shape, tests fail immediately.

## Acceptance Criteria

### Test Coverage

- [ ] Contract test file: `tests/api/test_registry_contract.py` (Python)
- [ ] Tests for all public endpoints in `asset_generation/web/backend/routers/`:
  - [ ] Each endpoint has at least one happy-path test
  - [ ] Each endpoint has at least one error-path test
- [ ] For each endpoint, verify:
  - [ ] Response status code is as documented (200, 404, 422, etc.)
  - [ ] Response JSON shape matches schema (all required fields present, correct types)
  - [ ] No unexpected fields in response
  - [ ] Field values are reasonable (strings non-empty, uuids valid format, etc.)

### Test Structure

- [ ] Use pytest + `jsonschema` for validation
- [ ] Load OpenAPI spec (or JSON Schema) as source of truth
- [ ] Each test:
  1. Call API endpoint (with valid/invalid input)
  2. Get response
  3. Validate response against schema with jsonschema
  4. Assert validation passed/failed as expected
- [ ] Example test:
  ```python
  def test_get_registry_returns_valid_schema(client):
      response = client.get("/api/registry")
      assert response.status_code == 200
      validate(response.json(), schema=REGISTRY_SCHEMA)
      # ^ Raises if response doesn't match schema
  ```

### Error Cases

- [ ] Test invalid inputs return expected error shape:
  - [ ] Malformed JSON → 400 with error detail
  - [ ] Missing required field → 422 with validation error
  - [ ] Type mismatch (string when int expected) → 422
- [ ] All error responses have consistent schema (e.g., `{"detail": "..."}`)

### Documentation

- [ ] Comment in test file explaining contract testing purpose
- [ ] Runbook: How to add new contract tests when endpoints change
- [ ] Link to schema/OpenAPI spec from test comments

### Integration

- [ ] Contract tests run in CI (part of `ci/scripts/run_tests.sh`)
- [ ] Part of pre-commit checks (optional but recommended)
- [ ] Failure blocks merge (enforced in CI)

### Baseline

- [ ] Test suite passes against current backend (baseline)
- [ ] Document any known schema issues or deviations in checkpoint

## Testing Checklist

```
[ ] Happy path: valid request → 200 + valid response
[ ] Empty input: empty body → 400 or 422
[ ] Missing field: required field omitted → 422
[ ] Type mismatch: string instead of int → 422
[ ] Extra field: unexpected field in request → ignored or error (spec-dependent)
[ ] Error response: invalid input → error response matches error schema
[ ] Large input: request with many items → success or reasonable error
[ ] Special chars: name with unicode/quotes → handled correctly
```

## Implementation Notes

- Use `jsonschema.validate(instance, schema)` to check response
- Schema source: OpenAPI spec from FastAPI, or pull from `GET /openapi.json`
- Keep tests focused on contract (shape, type), not business logic
- Business logic tests belong in unit tests, not contract tests

## Example: Full Contract Test

```python
import pytest
from jsonschema import validate, ValidationError

REGISTRY_SCHEMA = {
    "type": "object",
    "properties": {
        "asset_id": {"type": "string", "format": "uuid"},
        "name": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"}
    },
    "required": ["asset_id", "name", "created_at"]
}

def test_registry_happy_path(client):
    """Verify GET /api/registry returns valid AssetRegistry schema."""
    response = client.get("/api/registry")
    assert response.status_code == 200
    validate(response.json(), schema=REGISTRY_SCHEMA)

def test_registry_invalid_input(client):
    """Verify GET /api/registry with invalid input returns 422."""
    response = client.get("/api/registry?invalid_param=true")
    # Spec-dependent: may ignore unknown params or return 400
    assert response.status_code in [200, 400, 422]

def test_registry_error_response_shape(client):
    """Verify error responses have consistent schema."""
    # Assuming endpoint validates something
    response = client.get("/api/registry/invalid-uuid")
    assert response.status_code == 404
    error = response.json()
    assert "detail" in error  # Standard FastAPI error shape
```

## Spec Reference

See: `project_board/specs/902_26_api_contract_testing_spec.md`

## Dependencies

- M902-24 (OpenAPI → TypeScript Generation) — provides schema
- M902-25 (Pydantic + Zod Dual Validation) — ensures models are well-defined
- Backend with Pydantic response models

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
8

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: PASS — gatekeeper re-run 2026-05-21: `uv run pytest tests/api/ -q` → 87 passed; log `project_board/checkpoints/M902-26/pytest-api-2026-05-21.txt`
- Static QA: PASS — Ruff clean (`ruff-impl-2026-05-21.txt`); review `project_board/checkpoints/M902-26/2026-05-21T-static-qa-run.md`; live OpenAPI harness (no hand-written normative schemas)
- Integration: N/A
- AC coverage (spec Req 01–12): `asset_generation/python/tests/api/` harness + per-router modules including `test_registry_contract.py`; 29 contract targets with happy+error paths; `jsonschema>=4.23,<5` in dev deps; module docstring + OpenAPI cache links in `tests/api/__init__.py`; runbook § in `asset_generation/web/backend/AGENTS.md`; CI via `ci/scripts/run_tests.sh` → `.lefthook/scripts/py-tests.sh` (`pytest tests/`); Tier B anchor deviations in `project_board/checkpoints/M902-26/2026-05-21T-implementation-run.md`; pre-commit optional per spec A8
- Testing checklist (ticket §): addressed by contract + `test_api_contract_adversarial.py` suite

## Blocking Issues
- None (commits `cdec959`, `fd3b555`, `da5711d`; push to origin pending Human)

## Escalation Notes
- Tier B legacy routes use OpenAPI anchor validation until full Pydantic `response_model` migration

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{}
```

## Status
Proceed

## Reason
All acceptance criteria evidenced; contract suite committed. Push `main` when ready.
