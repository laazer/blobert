# Checkpoint Log: M8-SEFI (Enemy Status Effect Indicators) — SPECIFICATION Stage

**Ticket:** project_board/8_milestone_8_enemy_attacks/in_progress/02_enemy_status_effect_indicators.md  
**Stage:** SPECIFICATION  
**Date:** 2026-05-17  
**Agent:** Spec Agent  

---

## Completion Summary

Specification complete and finalized. Ticket advanced from PLANNING to SPECIFICATION (now ready for TEST_DESIGN).

**Deliverable:** `project_board/specs/enemy_status_effect_indicators_spec.md` (1.0)

---

## Specification Contents

### Sections Delivered
- Executive Summary (design decisions frozen)
- 7 Functional Requirements (FR1-FR7), each with details, acceptance criteria, and rationale
- 5 Non-Functional Requirements (NFR1-NFR5)
- 10 Detailed Acceptance Criteria (AC1-AC10), measurable and testable
- Risk & Ambiguity Analysis (5 risks, 3 ambiguities, all documented)
- Testing Strategy (35-50 tests total: 15-20 primary + 20-30 adversarial)
- Implementation Checklist (files, @export properties, quality gates)
- Traceability Matrix (AC × FR × NFR × Test mappings)
- Outstanding Items & Deferred Decisions (clarity on implementation handoff points)
- Specification Sign-Off (version 1.0, complete, no TBD sections)
- Appendix: Checkpoint Assumptions Summary (6 ambiguities documented)

### Key Design Decisions Frozen

| Decision | Choice | Confidence |
|----------|--------|------------|
| Icon container architecture | HBoxContainer child of EnemyHealthBar3D Control | HIGH |
| Sort order policy | Static enum: stun (0) > weaken (1) > poison (2) > slow (3) > infection (4) | HIGH |
| Max visible count | @export configurable, default 5 | HIGH |
| Overflow badge | "+N" where N = (active_count - max_visible) | HIGH |
| Status effect interface | Conservative polling with fallback to EnemyBase.State enum | MEDIUM |
| Signal vs polling | Assume polling (conservative); design supports both | MEDIUM |
| Icon asset strategy | Fallback to unknown_effect.png for missing assets | MEDIUM |

---

## Checkpoint Assumptions (6 Total)

### Assumption 1: Status Effect Interface Contract

**Would have asked:** What is the enemy node's contract for exposing active status effects?

**Assumption made:** Conservative polling approach with priority order:
1. Try array property: `enemy.active_status_effects` (Array[String] or Array[Dictionary] with "id" key)
2. Try meta property: `enemy.get_meta("active_status_effects")`
3. Try getter method: `enemy.get_active_status_effects()`
4. Fallback: Map enemy `EnemyBase.State` enum to effect IDs (WEAKENED → "weaken", INFECTED → "infection")

**Rationale:** EnemyBase state system confirmed to exist (weakening_system_spec.md); full status effect gameplay system (poison, slow, stun) not yet confirmed. Conservative polling unblocks display layer without gating on status system.

**Confidence:** MEDIUM

**Source:** Reviewed `scripts/enemies/enemy_base.gd` (State enum: NORMAL, WEAKENED, INFECTED) and `scripts/enemy/enemy_state_machine.gd` (pure simulation, states: idle, active, weakened, infected, dead). No status effect array currently exposed.

---

### Assumption 2: Signal vs Polling for Real-Time Updates

**Would have asked:** Should status indicator subscribe to enemy signals or poll each frame?

**Assumption made:** Assume polling (conservative, does not require enemy scripts to define signals). Design supports both approaches; polling is primary implementation path.

**Confidence:** MEDIUM

**Mitigation:** Specification allows signal-based subscription as optional enhancement; Test Designer can implement polling in primary suite and add signal variant in adversarial suite.

---

### Assumption 3: Icon Asset Paths and Format

**Would have asked:** Where do status effect icons live? What is the naming scheme?

**Assumption made:** Icons stored at `res://assets/ui/status_effects/{effect_id}.png` (effect_id = "poison", "stun", "slow", "weaken", "infection"). Fallback: `res://assets/ui/status_effects/unknown_effect.png`. If assets missing, use Godot PlaceholderTexture2D.

**Confidence:** MEDIUM

**Evidence:** Glob search found no existing status effect icon assets. Specification allows placeholders per ticket scope note: "Precise icon art polish can iterate later; placeholders are acceptable initially."

**Mitigation:** Test suites will mock/provide placeholder textures. Implementation can defer icon polish to future ticket.

---

### Assumption 4: Deterministic Sort Order

**Would have asked:** Should status effect indicator order be static or dynamic?

**Assumption made:** Static, enum-backed priority order (stun > weaken > poison > slow > infection). Deterministic, testable, matches ticket wording exactly.

**Confidence:** HIGH

**Rationale:** Ticket explicitly states: "stable sort policy for icon ordering (for example: stun > weaken > poison > slow > infection)". This is frozen in spec FR3.

---

### Assumption 5: Overflow Badge Threshold and Count

**Would have asked:** Should overflow badge show count of hidden effects?

**Assumption made:** Yes. Overflow badge displays "+N" where N = (active_count - max_visible_count). Simple, clear, testable.

**Confidence:** HIGH

**Rationale:** Ticket states: "overflow is represented with a `+N` badge". Spec FR4 details this explicitly.

---

### Assumption 6: Handling of Duplicate Effects in Array

**Would have asked:** If same effect ID appears twice in array, should it render once or twice?

**Assumption made:** Preserve duplicates. Render multiple icons if array contains duplicates. Overflow badge count includes duplicates.

**Confidence:** HIGH

**Rationale:** Future status effect system may need to display duplicate effects (e.g., two poison instances with different durations). Approach is explicit, testable, and future-proof.

---

## Requirements Traceability

### Acceptance Criteria (10)
AC1 through AC10 mapped to Functional Requirements (FR1-FR7) and Acceptance Criteria sections with measurable test conditions.

### Functional Requirements (7)
- FR1: Status Icon Container Creation and Lifecycle
- FR2: Status Effect Array Interface Contract (Checkpoint Assumption 1)
- FR3: Deterministic Status Effect Sort Order (Checkpoint Assumption 4)
- FR4: Max Visible Count Enforcement and Overflow Badge (Checkpoint Assumption 5)
- FR5: Real-Time Indicator Updates on Effect State Changes
- FR6: Unknown Effect ID Fallback Handling (Checkpoint Assumption 3)
- FR7: Scene Integration with Enemy Health Bar

### Non-Functional Requirements (5)
- NFR1: Performance and Responsiveness
- NFR2: Determinism and Idempotency
- NFR3: Robustness and Null Safety
- NFR4: Configuration and Tuning
- NFR5: Code Quality and Maintainability

---

## Risk Mitigation Summary

| Risk | Severity | Mitigation Strategy |
|------|----------|---|
| Status effect interface undefined | HIGH | Conservative polling + fallback to EnemyBase.State enum; Test Designer creates mock fixture |
| Icon assets missing | MEDIUM | Fallback icon path + PlaceholderTexture2D; tests use mocks; placeholders acceptable |
| Performance impact | MEDIUM | Caching via `_last_seen_effects`; reuse TextureRect nodes; tests verify idempotency |
| Scene hierarchy changes | MEDIUM | Leverage parent-child lifecycle; no hardcoded path queries; integration tests verify |
| Sort order non-determinism | MEDIUM | Pure function design; `_sort_effects()` is deterministic; tests verify stability |

---

## Quality Gates Passed

- Specification complete (no TBD sections)
- All ambiguities documented with checkpoint entries and mitigation strategies
- Acceptance criteria measurable and testable (10 criteria)
- Functional requirements detailed with acceptance criteria and rationale (7 FR)
- Non-functional requirements specified (5 NFR)
- Risk analysis complete (5 risks, all mitigated)
- Traceability matrix links AC → FR → NFR → Tests
- Implementation checklist provided (files, @exports, quality gates)
- Testing strategy outlined (35-50 tests: 15-20 primary + 20-30 adversarial)

---

## Specification Sign-Off

**Spec Version:** 1.0  
**Status:** COMPLETE  
**No TBD Sections:** ✓  
**Ambiguities Resolved:** 6 (all documented with checkpoint entries)  
**Ready for Test Designer:** Yes  

---

## Handoff Checklist

- [x] Specification file created: `project_board/specs/enemy_status_effect_indicators_spec.md`
- [x] Ticket updated: Stage → TEST_DESIGN, Revision 3, Last Updated By → Spec Agent
- [x] Checkpoint entry created: this file
- [x] All ambiguities documented with assumptions and confidence levels
- [x] Status effect interface contract defined (FR2 + Assumption 1)
- [x] Icon asset strategy defined (FR6 + Assumption 3)
- [x] Sort order frozen (FR3 + Assumption 4)
- [x] Max visible count with rationale (FR4 + Assumption 5)
- [x] Overflow badge spec detailed (FR4 + Assumption 5)
- [x] Test strategy outlined (primary 15-20 + adversarial 20-30)
- [x] Risk mitigation strategies documented
- [x] Implementation notes provided for Test Designer and Implementation Agent

---

## Next Steps (Test Designer Agent)

1. Read specification: `project_board/specs/enemy_status_effect_indicators_spec.md`
2. Review checkpoint assumptions (Appendix in spec) and this checkpoint log
3. Create test design document with primary test suite (15-20 tests)
4. Primary test coverage targets:
   - Container initialization (AC1)
   - Multi-effect sort order (AC2, FR3)
   - Overflow badge (AC3, FR4)
   - Fallback icon (AC4, FR6)
   - Real-time updates (AC5, FR5)
   - Max visible count (AC6, FR4)
   - Health bar integration (AC7, FR7)
   - Null enemy handling (AC8, FR2)
   - Empty effect list (AC9, FR5)
   - Boundary values (AC10)
5. Create mock enemy fixture with assumed `active_status_effects` interface (per FR2)
6. Organize tests by concern: lifecycle, sorting, overflow, fallback, integration, edge cases

---

**Prepared by:** Spec Agent  
**Date:** 2026-05-17  
**Status:** READY FOR TEST_DESIGN  
