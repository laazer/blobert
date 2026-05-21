"""
OpenAPI contract tests for the Blobert Asset Editor FastAPI backend (M902-26).

These tests assert HTTP status codes and JSON shapes against the **live** OpenAPI
document from ``app.openapi()``. They complement behavioral tests in
``tests/web/`` and ``asset_generation/web/backend/tests/`` — they do not replace them.

Schema authority: live OpenAPI at pytest session start; optional drift check against
``asset_generation/web/frontend/scripts/fixtures/openapi.cached.json`` (regen via
``npm run sync-api-types`` in the frontend package).

Runbook: add a backend route → ``npm run sync-api-types`` → add happy + error tests
in the matching ``test_*_contract.py`` module → ``uv run pytest tests/api/ -q``.

Spec: ``project_board/specs/902_26_api_contract_testing_spec.md``
"""
