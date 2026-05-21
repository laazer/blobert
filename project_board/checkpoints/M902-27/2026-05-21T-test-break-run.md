# M902-27 Test Break Run Checkpoint

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/27_api_contract_precommit_hook.md`

**Stage:** TEST_BREAK → IMPLEMENTATION_BACKEND

**Date:** 2026-05-21

**Agent:** Test Breaker Agent

**Status:** COMPLETE

---

## Summary

Extended `tests/ci/test_api_contract_precommit_hook.py` with adversarial class `TestApiContractPrecommitHookAdversarial` (A1–A13) per execution plan Task 3 and spec Req 06. Fixed brittle H7/A6 grep traps and npx PATH stub so Step 1 delegates real `openapi-typescript` while still mocking `tsc`/`uv`.

**Module:** `tests/ci/test_api_contract_precommit_hook.py` — **26 tests** (13 baseline H1–H8 + Req 04, **13 adversarial**).

---

## # CHECKPOINT — Gaps documented for Implementation

| ID | Category | Finding | Test / mitigation |
|----|----------|---------|-------------------|
| G1 | Assumption / grep | Naive `task editor` substring in H7 false-fails frozen Fix echo (Req 03). | H7 now allows `task editor` only in `echo` lines. |
| G2 | Mock trap | PATH `npx` stub that exits 127 for non-`tsc` broke sync Step 1 (`openapi-typescript exited non-zero`). | Stub delegates via `exec "$(command -v npx)" "$@"`; **A13** guards. |
| G3 | Determinism | `stdout + stderr` concat broke H5 ordering assertion (buffers are not temporal). | H5 checks `proc.stderr` for warning + script source order before `[2/3]`. |
| G4 | Structure | `openapi-typescript` in hook **comments** must not fail A6. | A6 skips `#` lines only. |
| G5 | Ordering | Step 1 failure must not invoke pytest (F8 isolation). | **A9** `uv.marker` file. |
| G6 | SETUP | Missing `uv` on PATH must block before `[1/3]` (F9). | **A3** + `_BLOCKED_SETUP`. |
| G7 | Parallel | Glob must stay `backend/**/*.py`, not routers-only ticket example. | **A11** |

No open RED tests after adversarial hardening (implementation script + lefthook already present in tree).

---

## Pytest evidence (3 consecutive green runs)

```text
=== run 1 ===
26 passed in 25.45s
=== run 2 ===
26 passed in 24.82s
=== run 3 ===
26 passed in 24.96s
```

Command:

```bash
uv run pytest tests/ci/test_api_contract_precommit_hook.py -q
```

---

## Handoff

**Next agent:** Implementation Agent (Generalist)

**Artifacts:** `project_board/checkpoints/M902-27/handoff-latest.yaml` (test_breaker→implementation)

**Orchestrator:** `python ci/scripts/run_workflow_transition_gates.py --ticket-id M902-27 --transition test_break_to_implementation`
