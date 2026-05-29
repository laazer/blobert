# Checkpoint Log: M12-03 — Static QA Run
**Run ID:** 2026-05-29T-static-qa-run
**Stage:** STATIC_QA
**Agent:** Static QA (Claude Sonnet 4.6)
**Ticket:** project_board/12_milestone_12_fused_mutation_attacks/in_progress/03_fusion_attack_framework.md
**Spec:** project_board/specs/fusion_attack_framework_spec.md

---

## Summary

Reviewed 4 files for M12-03 (fusion attack dispatch framework):

- `scripts/player/player_controller_3d.gd` — specifically the 2-line FAF-FM-3 guard at lines 481-482
- `tests/scripts/attacks/test_fusion_attack_routing.gd` — 14 behavioral tests
- `tests/scripts/attacks/test_fusion_attack_routing_adversarial.gd` — 10 adversarial tests
- `tests/scripts/attacks/test_fusion_attack_routing_adversarial2.gd` — 9 adversarial tests (includes FAF-FM-3 regression)

**Outcome: No CRITICAL issues found. 2 WARNING findings, 3 INFO findings.**

---

## Findings

### CRITICAL

None.

---

### WARNING

**W-1: Stale agent-process checkpoint prose embedded in production test file**
File: `tests/scripts/attacks/test_fusion_attack_routing_adversarial2.gd`, lines 117-120 and 177-178

Comments reading "CHECKPOINT: Spec says cooldown NOT set; code at line 481-482 sets it unconditionally. This test may RED if the implementation does not check executor return." and "CHECKPOINT: This assertion will FAIL if _try_attack sets cooldown unconditionally (current code at line 482 does exactly that). Marking spec gap." are pre-fix discovery artifacts from the Test Breaker agent. These describe a state that no longer exists. Per CLAUDE.md Agent Checkpoints policy, checkpoint prose belongs in `project_board/checkpoints/<ticket-id>/<run-id>.md`, not in test source files. The test now passes; this comment actively misleads future readers about the implementation's correctness.

Required action: Remove lines 117-120 and 177-178 from `test_fusion_attack_routing_adversarial2.gd`. The test itself (FAF-ADV2-1) is correct behavior and should be kept; only the now-false CHECKPOINT comments should be removed.

---

**W-2: Significant helper duplication across three test files**
Files: all three test files under `tests/scripts/attacks/test_fusion_attack_routing*.gd`

`_make_resource()`, `_get_autoload_db()`, `_composite_key()`, `_make_pipeline()`, and `_free_pipeline()` are copied verbatim in all three files. This is 60+ lines duplicated three times. If `_make_pipeline` needs a bug fix or a new field in the returned dict (e.g., a future `msm` key was added only in the adversarial files, not in the behavioral file), the divergence will silently produce inconsistent test behavior. This already happened: `test_fusion_attack_routing.gd`'s `_make_pipeline` does not return `"msm"` in its dict while `adversarial.gd` and `adversarial2.gd` do.

The project pattern for shared test helpers is `tests/utils/test_utils.gd` (already used as the base class). A `_make_pipeline` helper belongs there or in a dedicated `tests/utils/attack_test_utils.gd` if it is attack-specific.

Not required to block merge, but should be addressed in a follow-on cleanup ticket.

---

### INFO

**I-1: Test file suffix `adversarial2` does not describe behavior**
File: `tests/scripts/attacks/test_fusion_attack_routing_adversarial2.gd`

CLAUDE.md requires test file names to describe behavior and location. The suffix `adversarial2` is a sequence number. A name like `test_fusion_attack_routing_executor_gaps.gd` or `test_fusion_attack_routing_timing.gd` would better describe the content (executor-active guard, slot-clear transitions, sequential fire, cooldown magnitude). This does not embed milestone IDs but it also does not satisfy the spirit of the naming policy.

Non-blocking. Address in a follow-on rename if the file grows or is renamed for other reasons.

---

**I-2: `_make_pipeline` in `test_fusion_attack_routing.gd` does not return `"msm"` key**
File: `tests/scripts/attacks/test_fusion_attack_routing.gd`, line 99

The behavioral test file's `_make_pipeline` returns `{"root", "controller", "executor"}`. The adversarial files return `{"root", "controller", "executor", "msm"}`. Tests in the behavioral file that need to call `msm.clear_slot()` would get `null` from `pipeline.get("msm")` and fail. Currently no behavioral test needs that, but it is a silent structural divergence. Consolidated helper would prevent this.

---

**I-3: Untyped loop variable in `_tick_enemy_acid_dots` (pre-existing, not M12-03)**
File: `scripts/player/player_controller_3d.gd`, line 658

`var d: Dictionary = _enemy_acid_dots[idx]` — `_enemy_acid_dots` is declared as `Array` (untyped), so `d` requires a cast or typed array declaration to satisfy strict mode. Pre-existing pattern; not introduced by M12-03. Noted for completeness; out of scope for this review.

---

## Correctness Assessment of the M12-03 Change

The 2-line `is_active()` guard at `scripts/player/player_controller_3d.gd` lines 481-482 is correct:

1. Placement is between the resource/cooldown null check and the `execute_attack()` call — exactly where it must be to prevent a phantom cooldown write on executor rejection.
2. `AttackExecutor.is_active()` is a pure accessor (`return _is_active`) with no side effects — safe to call before dispatch.
3. The guard is symmetric: it applies to both fused and base paths since both converge to the same `execute_attack` + cooldown write at lines 483-484.
4. The fix is minimal (2 lines) and does not alter any other control flow.

The test FAF-ADV2-1 in `test_fusion_attack_routing_adversarial2.gd` provides direct regression coverage for this exact code path.

---

## Assumptions Made

- `AttackExecutor._is_active` set to `true` via `executor.set("_is_active", true)` in the test is a valid test pattern since `_is_active` is a plain `var` on a `Node` subclass.
- The `"msm"` key divergence between `_make_pipeline` implementations is intentional (behavioral tests don't need slot mutation access) but should be consolidated.

---

## Merge Readiness

WARNING W-1 (stale CHECKPOINT prose in test file) is the only item that requires action before merge. It is confined to comment removal in one file.

WARNING W-2 and all INFO findings are improvements, not blockers.
