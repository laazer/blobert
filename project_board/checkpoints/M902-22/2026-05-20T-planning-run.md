# M902-22 Planning Run

**Run id:** `2026-05-20T-planning-run`  
**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/22_early_stop_detection.md`  
**Stage:** PLANNING → SPECIFICATION  
**Planner:** Planner Agent

---

## Outcome

Planning complete. Execution plan: `project_board/execution_plans/M902-22_early_stop_detection.md` (11 tasks). Handoff to Spec Agent.

---

### [M902-22] PLANNING — diff_hash source of truth

**Would have asked:** Should `diff_hash` be computed from live `git diff` after each agent run, or from orchestrator-supplied file hashes only?

**Assumption made:** Spec freezes a two-tier contract: prefer orchestrator-injected `diff_hash` + `modified_files` in `framework_kwargs` when present; otherwise compute from `git status --porcelain` + bounded `git diff` of tracked paths under repo root. Empty diff → stable sentinel hash documented in spec. Tests mock git subprocesses.

**Confidence:** Medium

---

### [M902-22] PLANNING — no-op vs escalate severity

**Would have asked:** Does "flag after 2 iterations" for no-op mean WARN-only or full loop break?

**Assumption made:** No-op pattern sets `should_escalate: false` with `no_op_streak: true` in iteration record for orchestrator logging; full **escalate** only when combined with max-iter or when spec defines no-op×2 + same agent stage as hard stop. Spec Agent must pick one rule and tests enforce it — default: no-op 2× contributes to stall signal but does not alone break loop unless iteration 5 max hit.

**Confidence:** Medium

---

### [M902-22] PLANNING — gate_runner vs orchestrator-direct

**Would have asked:** Should early-stop register as `early_stop_check` in `gate_registry.json`?

**Assumption made:** Core delivery is `evaluate_early_stop()` called from middleware/orchestrator on loop iterations. Optional gate module only if spec requires M902-01 handoff symmetry; default orchestrator-direct to avoid shadow-mode false sense of security. Todo validation pattern reused for remediation text only.

**Confidence:** High

---

### [M902-22] PLANNING — loop_mode activation

**Would have asked:** How does middleware distinguish autopilot multi-iteration loops from single planner/spec calls?

**Assumption made:** `framework_kwargs["loop_mode"] is True` required to run detectors; missing/false → record-only or skip per spec § activation. Autopilot implementation stage sets `loop_mode=true`; other stages omit.

**Confidence:** High

---

## Repo discovery summary

- **Hook site:** `ci/scripts/agent_invocation_middleware.py` (`_maybe_record_context_budget` pattern)
- **Persistence pattern:** `ci/scripts/context_budget_tracker.py` → `project_board/checkpoints/<ticket_id>/`
- **Gate patterns:** `ci/scripts/gates/todo_validation_check.py` (structure, path safety)
- **Gap:** No `agent_iterations.json` or early-stop module in tree; spec file absent
