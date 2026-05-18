# M902-09: Stage 0 — Diff Classification Gate — PLANNING Checkpoint

**Ticket:** project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/09_stage_0_diff_classification_gate.md  
**Stage:** PLANNING → SPECIFICATION  
**Revision:** 1 → 2  
**Date:** 2026-05-18

---

## Clarifications & Assumptions (Checkpoint Protocol)

### [M902-09] PLANNING — Specification Source

**Would have asked:** The ticket references `project_board/specs/902_09_diff_classification_gate_spec.md`, but this spec file does not exist in the repository. Should the Spec Agent create a net-new spec from the ticket's acceptance criteria, or does reference material exist elsewhere?

**Assumption made:** The Spec Agent will author the spec from scratch using the ticket's acceptance criteria (Gate classifies staged changes into 6 categories, early exits for trivial, reduced pipeline for tests-only/migration-only, full pipeline for runtime code). The governance adoption plan at `project_board/plans/governance-adoption-phase1-precommit.md` provides context but is not the authoritative spec.

**Confidence:** High. The ticket explicitly references an expected spec path and lists detailed AC. The governance plan confirms this as "Phase 1.1: Add Diff Classification (Stage 0)" with shell script scope, but the ticket's AC and structure override — the spec will define Python module requirements consistent with the gate framework (M902-01).

---

### [M902-09] PLANNING — Gate Implementation Pattern

**Would have asked:** Should the diff classification gate follow the same pattern as other M902 gates (gate module under `ci/scripts/gates/`, entry in `gate_registry.json`), or is this "Stage 0" distinct from the rest of the pipeline because it is invoked first?

**Assumption made:** The diff classification gate follows the **same gate framework pattern** established in M902-01:
  - Module: `ci/scripts/gates/diff_classification.py`
  - Registry entry in `ci/scripts/gate_registry.json`
  - Inputs: none required (analyzes staged files via `git diff --cached`)
  - Output: result dict conforming to gate success/failure schemas
  - Mode: shadow (non-blocking, advisory)

The "Stage 0" label refers to its position in the **logical pipeline** (runs first to route traffic), not a separate implementation approach.

**Confidence:** High. The ticket's implementation notes say "Implemented as `ci/scripts/gates/diff_classification_check.py`" (confirms gate module), "Integrated into gate registry in `ci/scripts/gate_runner.py`" (confirms registry entry). This aligns with M902-01 framework.

---

### [M902-09] PLANNING — Output Contract

**Would have asked:** The AC say "Output: classification enum + recommended pipeline route." Should the gate module return a Python enum, a string, or a structured dict? How are "pipeline routes" represented in the output?

**Assumption made:** The gate output conforms to the gate success/failure schemas from M902-01 (M902-01 Req. 02 and 03). The classification is **returned in the success record's message field or a `classification` field** in the dict. "Routes" are documented as advisory text in the record, not machine-callable directives (routing logic is deferred to M903 or pipeline orchestrator).

Example output (success case):
```json
{
  "status": "PASS",
  "gate": "diff_classification_check",
  "classification": "runtime-code",
  "recommended_route": "full_pipeline",
  "message": "Staged changes include runtime code (scripts/, src/). Recommended: execute all gates."
}
```

The test suite will validate this structure.

**Confidence:** Medium. The output contract is not yet frozen in the governance plan or gate framework. The spec will define the exact field names and values.

---

### [M902-09] PLANNING — Category Definitions

**Would have asked:** The AC list 6 categories: docs-only, formatting-only, lockfile-only, tests-only, migration-only, runtime-code. What defines each? For example, is `tests/ui/test_*.gd` a test-only change, or if it imports `scripts/` (non-test code), is it mixed and thus routed to runtime-code?

**Assumption made:** Classification is **file-path based** with a priority hierarchy:
  1. Check all staged files' paths and extensions.
  2. **Categorize each file** into a category (docs, formatting, lockfile, test, migration, runtime).
  3. **Determine the overall category** by taking the "highest priority" category present:
     - runtime-code (highest) > migration > test > lockfile > formatting > docs (lowest)
  4. Special case: if **all files fit a single category**, return that category exactly. If mixed, return the highest-priority.

This defers implementation details (exact file patterns, extension rules) to the spec.

**Confidence:** Medium-High. The governance plan suggests this approach ("Categorize by file extension and path patterns"). The spec will provide the authoritative rules.

---

### [M902-09] PLANNING — Early Exit Behavior

**Would have asked:** The AC say "Early exit routes: docs-only → SKIP, formatting-only → Stage 1". Should SKIP be a gate result status (e.g., `status: "SKIP"`), or should the gate exit 0 with a message that downstream orchestration interprets?

**Assumption made:** The gate follows the **gate framework output contract** (M902-01). All outputs conform to success/failure schemas. A "SKIP" or "advisory-only" status is represented in the `status` field (e.g., `status: "ADVISORY"` or `status: "PASS"` with a `routing_recommendation` field). The gate **always exits 0** (shadow mode by default in M902). Blocking/routing logic is deferred to downstream orchestrators.

**Confidence:** Medium. The gate framework doesn't yet define a SKIP status. The spec will clarify this, or the spec will define SKIP as a valid status extending M902-01.

---

## Summary

The Spec Agent will author a spec for diff classification gate that:
1. Defines classification categories with file-path rules.
2. Specifies output contract (gate result dict with classification, recommendation).
3. Lists detailed acceptance criteria (20+ test vectors covering all categories).
4. Specifies the gate module (`ci/scripts/gates/diff_classification.py`), registry entry, and shadow mode default.
5. Defers orchestration logic (actual early-exit behavior) to M903 or downstream pipeline, focusing on classification logic only.

This is consistent with the "advisory; helps agents understand impact scope" note in the ticket.

---

## Next Action

→ Spec Agent reads this checkpoint and the ticket, then authors `project_board/specs/902_09_diff_classification_gate_spec.md` from scratch. No blocking issues.
