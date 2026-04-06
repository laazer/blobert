# attack_telegraph_system — Planning (2026-04-06)

## Execution plan (contract for downstream agents)

**Project:** attack_telegraph_system — Enemy attack telegraphing (wind-up before damage-active phase)

**Description:** Unify and harden telegraph behavior so every enemy family’s attack has a minimum wind-up, a visible cue, and no damage-dealing (projectile spawn, melee hit resolution, or future Area3D hitbox) until wind-up completes. Build on existing `EnemyAnimationController.begin_ranged_attack_telegraph()` / `ranged_attack_telegraph_finished` and per-attack `telegraph_fallback_seconds` in `AcidSpitterRangedAttack` and `AdhesionBugLungeAttack`.

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Author formal specification (timing, visuals, exports, integration points, test obligations) | Spec Agent | Ticket AC; this plan; `scripts/enemies/enemy_animation_controller.gd`; `scripts/enemy/acid_spitter_ranged_attack.gd`; `scripts/enemy/adhesion_bug_lunge_attack.gd`; `project_board/8_milestone_8_enemy_attacks/backlog/hitbox_and_damage_system.md` | `project_board/specs/attack_telegraph_system_spec.md` (or equivalent path per repo convention); ticket **Specification** section filled with normative IDs (e.g. ATS-1..n) | None | Spec defines: min 0.3s wind-up before active phase; visual requirement; exported duration per family (not hardcoded in attack logic); semantic mapping of “hitbox” (Area3D vs radius/proc until hitbox ticket lands); dependency boundary with `hitbox_and_damage_system` | **Risk:** `hitbox_and_damage_system` is backlog and `enemy_attack_hitbox.gd` does not exist yet — spec must define telegraph→active contract so hitbox work can plug in without rework. **Assumption:** “Four families” = same four as M5/M7 (e.g. acid, adhesion, carapace husk, claw crawler); spec names concrete scene/script targets per family. |
| 2 | Author primary behavioral tests from spec | Test Designer Agent | Spec from task 1 | New tests under `tests/` (Godot GDScript per project norms) | 1 | Tests fail on pre-implementation where expected; encode min wind-up, no-damage-during-wind-up, exported-var contract | Tests may need scene doubles or headless-friendly harness if full `.tscn` not ready for all families. |
| 3 | Adversarial / edge-case tests | Test Breaker Agent | Tests from task 2, spec | Extended tests with `# CHECKPOINT` where assumptions are structural | 2 | Mutation-style edge cases (missing Attack clip, death mid-telegraph, timer vs animation race) | Overfitting to current implementation details. |
| 4 | Implement unified telegraph API and family wiring | Implementation Generalist Agent (or Backend + Frontend split if Planner escalates) | Spec; tests | Shared pattern: exported `telegraph_duration_seconds` (or renamed per spec) with `max(export, 0.3)` or clamp policy; refactor acid/adhesion; add or align attack entry points for remaining families per spec | 3 | All AC satisfied; `EnemyAnimationController` extended or wrapped per spec; no damage/projectile/lunge-hit before telegraph end | **Risk:** Other families lack attack scripts — may require minimal attack stub or document “N/A until follow-up ticket” only if spec allows. |
| 5 | Static QA + full test gate | AC Gatekeeper / Integration | Green local runs | Validation evidence on ticket | 4 | `timeout 300 ci/scripts/run_tests.sh` exit 0 | Flaky timing tests — prefer deterministic signals/timers in tests. |

## Notes

- Tasks are sequential where noted; Spec has no upstream dependency.
- Verification: tests + `run_tests.sh` are the contract; implementation must not ship without green suite.

---

### [attack_telegraph_system] PLANNING — Dependency hitbox_and_damage_system

**Would have asked:** Should `hitbox_and_damage_system` be implemented before this ticket, or can telegraph ship with radius/projectile timing only until Area3D hitboxes exist?

**Assumption made:** Telegraph semantics apply to **when damage can begin** (projectile instantiation, melee hit registration, or `Area3D.monitoring`); spec task will explicitly sequence integration with the backlog hitbox ticket and avoid duplicating that ticket’s deliverables.

**Confidence:** Medium

---

### [attack_telegraph_system] PLANNING — “Four families” scope

**Would have asked:** Confirm the exact four family slugs/scenes that must pass AC (vs six animated types in asset pipeline).

**Assumption made:** Align with milestone language (four prototype families: acid, adhesion, carapace husk, claw crawler); spec agent verifies against `enemy_mutation_map` / generated scenes and lists paths.

**Confidence:** Medium

---

### [attack_telegraph_system] PLANNING — Visual telegraph channel

**Would have asked:** Prefer mandatory `Attack` animation only, or require additive color flash / indicator node for families without Attack?

**Assumption made:** Spec defaults to **Attack clip via `EnemyAnimationController`** where present; fallback wall-clock telegraph must still apply a **documented** visual (e.g. material flash or placeholder `MeshInstance3D`) when Attack is missing — exact choice is for Spec Agent with simplest consistent approach.

**Confidence:** Medium
