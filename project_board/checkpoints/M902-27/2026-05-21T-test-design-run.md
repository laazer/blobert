# M902-27 Test Design Run Checkpoint

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/27_api_contract_precommit_hook.md`

**Stage:** TEST_DESIGN → TEST_BREAK

**Date:** 2026-05-21

**Agent:** Test Designer Agent

**Status:** COMPLETE

---

## Summary

Behavioral RED tests added per `project_board/specs/902_27_api_contract_precommit_spec.md` Requirement 06 (H1–H8).

**Module:** `tests/ci/test_api_contract_precommit_hook.py`

**Test count:** 13 (12 expected RED pre-implementation; 1 green parallel guard)

---

## Spec traceability (H1–H8)

| ID | Test | Spec / AC |
|----|------|-----------|
| H1 | `test_h1_all_steps_success_exit_zero` | Req 02–03 success footer |
| H2 | `test_h2_sync_failure_exit_one_and_step_one_template` | Req 03 Step 1 failure |
| H3 | `test_h3_tsc_failure_exit_one_type_mismatch_banner` | Req 03 TYPE_MISMATCH |
| H4 | `test_h4_pytest_failure_exit_one_hint_line` | Req 03 CONTRACT_TEST_FAILED |
| H5 | `test_h5_cache_fallback_warning_line_on_success` | Validation Precedence cache warning |
| H6 | `test_h6_*` (4 tests) | Req 01 AC-01.1–01.4 |
| H7 | `test_h7_script_forbids_backend_auto_start` | Req 02 AC-02.6 |
| H8 | `test_h8_skip_fetch_deterministic_step_one` | Req 06 H8 / A9 |

**Req 04:** `test_pre_commit_parallel_still_true` (AC-04.1)

**Mocking:** PATH stubs for `npx`/`uv`; Step 1 via `BLOBERT_SYNC_SKIP_FETCH` or dead URL + cache fixture; no live :8000.

---

## Pytest execution (expected TDD red)

```text
============================= test session starts ==============================
collected 13 items
========================= 12 failed, 1 passed in 0.10s ==========================
```

**Representative failures (verbatim):**

```text
E   AssertionError: pre-commit.commands must define 'api-contract-check'
    assert {}
tests/ci/test_api_contract_precommit_hook.py:201: AssertionError

E   AssertionError: Missing /Users/jacobbrandt/workspace/blobert/.lefthook/scripts/api-contract-check.sh
tests/ci/test_api_contract_precommit_hook.py:229: AssertionError

E   AssertionError: Hook script missing (implementation pending): .../api-contract-check.sh
tests/ci/test_api_contract_precommit_hook.py:145: AssertionError
```

**Interpretation:** `lefthook.yml` lacks `api-contract-check`; hook script not yet implemented (Tasks 4+).

---

## Spec gaps

None for Req 06 minimum scenarios.

---

## Handoff

**Next agent:** Test Breaker Agent

**Suggested adversarial cases:** YAML drift (wrong glob/run), missing `stage: commit`, hook starts backend, cache warning omitted when sync uses cache, step 2 runs after step 1 failure.
