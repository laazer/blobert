# M902-23: Atomic Handoff Checkpoint

**Status:** PENDING  
**Target:** 2026-08-05

## Overview

Formalize the contract between agents at each handoff point. Each agent must produce a checklist of required outputs before the next agent can start. Prevents rework and reduces ambiguity about what "done" means at each stage.

## Acceptance Criteria

- [ ] Define per-agent handoff checklist (what must be done before handoff):
  - [ ] **Planner** → **Spec:** ticket decomposed, dependencies clear, timeline estimated
  - [ ] **Spec** → **Test Designer:** acceptance criteria defined, test strategy documented, edge cases listed
  - [ ] **Test Designer** → **Test Breaker:** test suite complete, coverage > 80%, all tests runnable
  - [ ] **Test Breaker** → **Implementation:** all discovered gaps documented, implementation notes created
  - [ ] **Implementation** → **Review:** code complete, all tests passing, no linter violations, checkpoint logged
  - [ ] **Review** → **Learning:** feedback incorporated, code reviewed, merge-ready
  - [ ] **Learning** → **Complete:** insights documented, decision rationale recorded, checklist validated
- [ ] Checklist format: YAML in checkpoint, structured for validation
- [ ] Gate function: `validate_handoff_checklist(ticket_id, from_agent, to_agent) -> GateResult`
- [ ] FAIL if any required item missing; includes list of gaps
- [ ] Tested with 3+ agent pairs; checklists validated end-to-end
- [ ] Agent runbook: expected checklist items for each handoff
- [ ] Documentation: examples of good/bad checkpoints at each stage

## Handoff Checklist Schema

```yaml
handoff:
  from_agent: "implementation"
  to_agent: "review"
  checklist:
    - item: "All acceptance criteria implemented"
      status: "complete"
      evidence: "Checkpoint entry AC-001 through AC-005 all marked complete"
    - item: "All tests passing"
      status: "complete"
      evidence: "Test run 2026-05-18T14:30:00Z, all 42 tests PASS"
    - item: "No linter violations"
      status: "complete"
      evidence: "ruff: 0 errors, mypy: 0 errors (gate_results/static_analysis_2026-05-18.json)"
    - item: "Code complexity within bounds"
      status: "complete"
      evidence: "cyclomatic complexity avg 2.1 (target < 5)"
  required_items_met: 4
  total_required_items: 4
  validated_at: "2026-05-18T14:35:00Z"
```

## Implementation Notes

- Checklists live in checkpoint logs alongside iteration tracking
- Each item includes status (complete/incomplete/deferred/blocked) and evidence (file path, test result, etc.)
- Gate validates before agent transition
- Supports **deferred items** with clear reason (e.g., "defer performance optimization to M903")
- Blocked items escalate (never proceed with required items blocked)

## Example: Implementation → Review Handoff

| Item | Required? | Status | Evidence |
|------|-----------|--------|----------|
| Code written for all AC | Yes | Complete | AC-001, AC-002, AC-003 checkpoint entries |
| Tests written | Yes | Complete | `tests/test_feature.py` exists, 8 tests |
| Tests passing | Yes | Complete | `pytest tests/test_feature.py -v` [PASS](link) |
| No linter errors | Yes | Complete | `ruff check .` [0 errors](link) |
| Type checks passing | Yes | Complete | `mypy .` [0 errors](link) |
| Docstrings/comments | No | Complete | Inline comments on complex logic |
| Performance baseline | No | Deferred | Defer to M903 (issue #456) |

## Spec Reference

See: `project_board/specs/902_23_atomic_handoff_spec.md`

## Dependencies

- M902-01 (Validation Gate Framework)
- M902-20 (TODO Validation Gates)
- Checkpoint infrastructure
