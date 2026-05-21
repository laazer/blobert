# M902-26 — PLANNING run

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/26_api_contract_testing.md`

**Agent:** Planner Agent

**Date:** 2026-05-21

---

## Outcome

Planning complete. Execution plan: `project_board/execution_plans/M902-26_api_contract_testing.md`. Ticket advanced to SPECIFICATION → Spec Agent.

---

### [M902-26] PLANNING — Contract test path ambiguity

**Would have asked:** Ticket AC names `tests/api/test_registry_contract.py` at repo root; existing backend tests live under `asset_generation/web/backend/tests/` and `asset_generation/python/tests/web/`. Which directory is normative for CI?

**Assumption made:** Place contract suite at `asset_generation/python/tests/api/` so `ci/scripts/run_tests.sh` → `py-tests.sh` → `pytest tests/` picks it up without a new runner. Split modules per router (`test_registry_contract.py`, etc.) rather than a single registry-only file.

**Confidence:** High

---

### [M902-26] PLANNING — SSE and binary responses

**Would have asked:** Should `GET /api/run/stream` (SSE) and GLB `GET /api/assets/{path}` use the same jsonschema response validation as JSON endpoints?

**Assumption made:** Spec Agent defines hybrid contracts: JSON endpoints use full OpenAPI-derived jsonschema; SSE documents per-event schema or a scoped test exemption; binary routes assert status + Content-Type + minimal headers only.

**Confidence:** Medium

---

### [M902-26] PLANNING — Overlap with M902-25 pilot tests

**Would have asked:** Do OpenAPI contract tests supersede `test_response_models_pilot.py` and `tests/web/test_registry_api.py`?

**Assumption made:** Keep existing behavioral/delegation tests; add contract layer for OpenAPI enforcement. Spec documents overlap policy; no mass deletion in this ticket.

**Confidence:** High
