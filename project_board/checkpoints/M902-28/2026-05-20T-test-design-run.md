# M902-28 Test Design Run Checkpoint

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/28_parallel_hook_execution.md`

**Stage:** TEST_DESIGN → TEST_BREAK handoff

**Date:** 2026-05-20

**Agent:** Test Designer Agent

**Status:** COMPLETE

---

## Summary

Behavioral CI contract tests added per `project_board/specs/902_28_parallel_hook_execution_spec.md` Requirement 10.

**Module:** `tests/ci/test_parallel_hook_execution.py`

**Test count:** 11 (T1–T6 + markdown-prose guard)

---

## Spec traceability (T1–T6)

| ID | Test | Spec / AC |
|----|------|-----------|
| T1 | `test_t1_pre_push_parallel_is_true` | Req 03 AC-03.1 |
| T2 | `test_t2_pre_commit_parallel_is_true` | Req 03 AC-03.1, Req 06 AC-06.3 |
| T3 | `test_t3_*` (delegation + globs) | Req 03 AC-03.2–03.3 |
| T4 | `test_t4_godot_hook_script_*` | Req 01 AC-01.3 |
| T5 | `test_t5_py_hook_coverage_xml_*` | Req 01 AC-01.3 |
| T6 | `test_t6_*` (TSGR path, run_tests order, contract exit 0) | Req 07 AC-07.1–07.2 |

**T7 (optional overlap stub):** Not implemented — full Godot timing deferred to Integration per spec.

**No markdown prose assertions:** `TestNoMarkdownProseContract` guards module source; tests parse `lefthook.yml` and shell scripts only.

---

## Pytest execution (expected TDD red)

```text
============================= test session starts ==============================
collected 11 items

FAILED tests/ci/test_parallel_hook_execution.py::TestLefthookParallelSchedulingContract::test_t1_pre_push_parallel_is_true
========================= 1 failed, 10 passed in 0.43s ==========================
```

**Failure (verbatim):**

```text
tests/ci/test_parallel_hook_execution.py:89: in test_t1_pre_push_parallel_is_true
    assert pre_push.get("parallel") is True
E   AssertionError: assert False is True
E    +  where False = {'commands': {...}, 'parallel': False}.get
```

**Interpretation:** `lefthook.yml` still has `pre-push.parallel: false` (pre-implementation). Implementation Generalist must flip to `true` in Task 4.

---

## Spec gaps

None. All Requirement 10 obligations covered without reading ticket/spec markdown bodies as golden output.

---

## Handoff

**Next agent:** Test Breaker Agent (execution plan Task 3)

**Suggested adversarial cases:** YAML regression (`parallel: false`, missing key), indentation drift, concurrent coverage write simulation if spec allows temp paths.
