# TICKET: enemy_animation_per_type_policies_deferred

Title: Defer — split `EnemyAnimationController` only when per-enemy clip rules diverge

## Description

`scripts/enemies/enemy_animation_controller.gd` is intentionally shared across all generated enemies. Do **not** split it preemptively. When clip names, blend times, or state→clip mapping differ materially by family/slug, extract policies (e.g. `RefCounted` clip map per enemy, or small resource files) and keep the controller as a thin dispatcher.

## Acceptance Criteria

- Ticket used as **backlog placeholder**: no implementation until a concrete enemy needs non-shared animation logic.
- When implemented: controller shrink or policy injection documented; `run_tests.sh` exits 0.

## Dependencies

- Defer until gameplay or animation export forces per-type behavior

---

## Execution Plan

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Record planning outcome: defer-only scope, AC-1 vs AC-2 split, no preemptive controller split | Planner Agent | Ticket; `workflow_enforcement_v1.md` | Execution plan table in this section; workflow handoff to Spec | None | Table present; AC-1 described as satisfied without repo code changes until a concrete per-type need; AC-2 labeled future-only | Assumes maintenance queue allows waiving implementation stages for explicit placeholders (see checkpoint MAINT-EAPD). |
| 2 | Author specification: keep shared `EnemyAnimationController`; define “material divergence” triggers; document future policy patterns (e.g. `RefCounted` clip maps, small resources); map AC-2 to future work | Spec Agent | Ticket; optional read of `scripts/enemies/enemy_animation_controller.gd` for accurate references | `## Specification` populated (or linked spec path) with traceability to AC | 1 | Spec is unambiguous; does not imply immediate refactor; states closure for this ticket is policy documentation + AC-1 confirmation, not AC-2 | Spec could over-scope into implementation; keep narrative-only. |
| 3 | Verify AC-1: placeholder satisfied (no implementation required now); confirm AC-2 not a closure gate; update validation / stage per workflow | Acceptance Criteria Gatekeeper | Ticket after Spec | `Validation Status` and `Stage` / `NEXT ACTION` consistent with defer closure | 2 | AC-1 explicitly checked; no false requirement for tests or code under AC-2 | Gatekeeper must not demand `run_tests.sh` for pure-doc closure unless project policy requires it. |
| 4 | *(Future ticket — not executed for MAINT-EAPD closure)* When gameplay or animation export forces per-type clip rules: inject policies, shrink controller to dispatcher, document injection points | Implementation Generalist (or split backend/frontend per touchpoints) | New ticket referencing this decision; divergent enemy slug/family | Code + documented policy injection; `run_tests.sh` exits 0 | Concrete divergence requirement | AC-2 satisfied on that future ticket | Until then, shared controller remains correct by AC-1. |

**Pipeline note:** TEST_DESIGN, TEST_BREAK, and IMPLEMENTATION stages are **out of scope for closing this placeholder ticket**; they apply only to task 4 when filed.

---

## Specification

This ticket is a **deferral and policy record** for enemy animation architecture. **Closure of MAINT-EAPD is governed solely by Acceptance Criterion AC-1** (placeholder satisfied: no preemptive split of `EnemyAnimationController`). **AC-2** (implementation when divergence exists, `run_tests.sh` exits 0) applies **only to a future ticket** filed after a concrete per-enemy need; it is **not** a gate for completing this ticket.

---

### Requirement MAINT-EAPD-S1 — Shared `EnemyAnimationController` policy (no preemptive split)

#### 1. Spec Summary
- **Description:** `EnemyAnimationController` (`scripts/enemies/enemy_animation_controller.gd`) remains the **single shared** state-driven animation dispatcher for all generated enemies. It reads `EnemyStateMachine` (or stub) state each physics tick, resolves clips on the enemy’s `AnimationPlayer`, applies crossfade via configurable `blend_time`, and handles hit/death flows as already implemented. **Do not** fork this controller into per-enemy-type subclasses or duplicate files **until** a concrete enemy family/slug needs **different** clip naming, blend parameters, or state→clip mapping than the shared rules can express without `if slug == …` sprawl.
- **Constraints:** No change to production code is required or implied by this ticket. Existing call sites (scene generation, `setup()`, `notify_root_animation_wired()`, tests) remain authoritative for how the controller is wired today.
- **Assumptions:** “Generated enemies” continue to share one animation contract (same semantic states, same clip names or resolvable aliases) unless and until product or pipeline evidence says otherwise.
- **Scope:** Architectural policy and backlog placeholder only; applies to all current and future enemies **until** MAINT-EAPD-S2 triggers.

#### 2. Acceptance Criteria
- **S1-AC-a:** Written policy states explicitly that a **shared** controller is the default and splitting is **deferred** until material divergence (see S2).
- **S1-AC-b:** Policy does **not** require any repository code change for MAINT-EAPD closure.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Teams may confuse “defer” with “forbidden forever.” Mitigation: S2 defines when a **new** ticket is warranted.
- **Edge case:** Minor per-enemy tuning (e.g. speed scale) that stays within one formula may remain in shared code; only **material** mapping/naming/blend differences trigger extraction.

#### 4. Clarifying Questions
- *None for this ticket; any slug-specific contract is resolved on the future implementation ticket.*

---

### Requirement MAINT-EAPD-S2 — “Material divergence” (triggers future work, not this ticket)

#### 1. Spec Summary
- **Description:** **Material divergence** means at least one of the following is true for a **specific enemy family or slug** (or export pipeline segment) such that the shared controller would need **enemy-identity-conditioned** logic for correctness or maintainability:
  - **Clip identity:** Different **canonical clip names** or library paths for the same logical state (e.g. one enemy uses `"Walk"` vs `"Move"`, or different GLB library layout) such that a single static mapping table is misleading or incomplete.
  - **Blend / timing:** **Materially different** default crossfade or transition durations **per type** (not a single global `blend_time` export), where hardcoding multiple constants in the shared script would obscure intent.
  - **State→clip mapping:** Different **rules** tying `EnemyStateMachine` states (or velocity thresholds) to clips—e.g. one enemy skips Hit recovery differently, uses a unique Death sequence name, or maps “alert” to a different animation set.
  - **Pipeline contract:** Export or rig tooling produces **incompatible** animation lists for one enemy class unless the controller accepts **injected** per-type metadata.
- **Constraints:** Cosmetic-only differences (scale, playback speed multiplier) that can remain **data** on the same code path **without** branching on enemy identity do **not** alone constitute material divergence. Isolated one-off hacks in the shared file **do** count as divergence if they require **ongoing** slug checks.
- **Assumptions:** “Concrete need” is evidenced by design, gameplay, or export artifacts—not hypothetical future enemies.
- **Scope:** Defines when to **file and execute** a follow-up ticket; **out of scope** for MAINT-EAPD implementation.

#### 2. Acceptance Criteria
- **S2-AC-a:** Triggers are listed as **testable descriptions** (reviewer can answer yes/no: “Does this enemy need a distinct mapping?”).
- **S2-AC-b:** Spec states that satisfying S2 is **not** required to close MAINT-EAPD.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Subjective “material.” Mitigation: use the bulleted categories; if two reviewers disagree, default to **no split** until one category clearly applies.
- **Edge case:** Two enemies share names but different **meanings** for a clip—treat as clip identity / mapping divergence.

#### 4. Clarifying Questions
- *Deferred to the follow-up ticket that cites this spec.*

---

### Requirement MAINT-EAPD-S3 — Future policy patterns (implementation guidance for AC-2)

#### 1. Spec Summary
- **Description:** When a follow-up ticket is filed under AC-2, prefer **policy injection** over copying the controller:
  - **`RefCounted` clip / transition policy:** A small per-type object (or struct-like class) holding map `state → clip name`, optional per-transition `blend_time`, and optional speed overrides. `EnemyAnimationController` becomes a **thin dispatcher**: read state from `EnemyStateMachine`, ask policy for clip + blend, invoke `AnimationPlayer`.
  - **Resource files:** Optional `.tres` / custom `Resource` definitions per enemy type for clip maps and blend curves—editable without code, versioned with assets.
  - **Registration:** Generator or scene factory attaches the correct policy instance to the controller (or passes it through `setup()`-style API) so the controller stays free of slug `match` trees.
- **Constraints:** Patterns are **non-normative** for MAINT-EAPD (no implementation now). Chosen pattern must preserve existing behaviors for enemies still on the default policy.
- **Assumptions:** Godot 4.x `RefCounted` / `Resource` usage matches project conventions when implemented.
- **Scope:** Guidance for the **future** AC-2 ticket only.

#### 2. Acceptance Criteria
- **S3-AC-a:** At least two pattern classes (in-memory `RefCounted` map vs file-backed `Resource`) are named with their roles.
- **S3-AC-b:** Explicit statement that controller should **shrink** to dispatch + shared edge behavior (e.g. death latch) while **policies** own variation.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Over-engineering on first divergence. Mitigation: start with smallest injectable policy that removes slug branching; escalate to resources if designers need iteration without code.
- **Edge case:** Shared death/hit semantics might stay in the controller while only locomotion clips vary—spec allows **partial** policy ownership.

#### 4. Clarifying Questions
- *None; implementation ticket chooses concrete APIs.*

---

### Non-functional requirements (MAINT-EAPD-NF)

| ID | Requirement |
|----|-------------|
| **NF-1 Traceability** | This specification SHALL be readable without external links; AC-1 and AC-2 trace to sections S1 and S2/S3 respectively. |
| **NF-2 Stability** | Completing MAINT-EAPD SHALL NOT require running `run_tests.sh` or modifying `scripts/`, `scenes/`, or `tests/` solely to satisfy AC-1. |
| **NF-3 Explicit closure** | **THIS ticket closes** when AC-1 is verified: defer-only scope is documented, shared controller policy is explicit, and AC-2 is scoped to future work. **AC-2 is explicitly out of closure scope for MAINT-EAPD.** |

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
STATIC_QA

## Revision
6

## Last Updated By
Implementation Generalist

## Validation Status

- Tests: PASS — MAINT-EAPD policy invariants + adversarial suite (`test_maint_eapd_shared_enemy_animation_policy.gd` EAPD-P1..P22); `timeout 300 godot -s tests/run_tests.gd` exit 0 (2026-04-05, re-run by Implementation Generalist)
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues

- None

## Escalation Notes

- None

---

# NEXT ACTION

## Next Responsible Agent
Acceptance Criteria Gatekeeper Agent

## Status
Proceed

## Reason

Implementation Generalist confirmed AC-1: no preemptive `EnemyAnimationController` split or policy injection; no production code changes required. Full suite `timeout 300 godot -s tests/run_tests.gd` exit 0 (2026-04-05). Handoff to Acceptance Criteria Gatekeeper for AC-1 verification and closure per spec; AC-2 remains future-only.
