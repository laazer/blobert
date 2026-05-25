# TICKET: 04_attack_resource

**Milestone:** M11 Base Mutation Attacks (Core Foundation)  
**Status:** Ready  
**Type:** Implementation

## Title

Implement AttackResource Godot resource class

## Description

Create the data model for all attacks (base and fused). AttackResource is a Godot Resource that defines:
- Effect type (MELEE_SWIPE, PROJECTILE_SPIT, etc.)
- Core parameters (damage, cooldown, range, knockback)
- Visual feedback (color, VFX scale)
- Extensible modifiers (poison duration, acid DPS, etc.)

This is the foundation for data-driven attack dispatch — no code changes to handlers needed for new attacks.

## Acceptance Criteria

- [x] `AttackResource` class created (`scripts/attacks/attack_resource.gd`)
- [x] All properties exported and typed:
  - `attack_id: int`
  - `attack_name: String`
  - `effect_type: String` (enum-like: "MELEE_SWIPE", "PROJECTILE_SPIT", etc.)
  - `damage: float`
  - `cooldown: float`
  - `range: float`
  - `startup_frames: int`
  - `knockback_magnitude: float`
  - `knockback_direction: String` ("away", "toward", "none")
  - `projectile_speed: float` (if applicable)
  - `color: Color`
  - `vfx_scale: float`
  - `modifiers: Dictionary` (extensible key-value pairs)
- [x] Class documented with examples (Claw, Acid, Carapace, Adhesion)
- [x] Modifiers system documented (poison, acid, slow, etc.)
- [x] Tests validate property access and serialization
- [x] `run_tests.sh` exits 0

## Dependencies

- None (foundational)

## Example Resource Properties

**Claw Swipe:**
```
attack_id: 101
attack_name: "Claw Swipe"
effect_type: "MELEE_SWIPE"
damage: 2.0
cooldown: 0.8
range: 1.5
knockback_magnitude: 100.0
knockback_direction: "away"
color: Color(0.8, 0.2, 0.1)
modifiers: {}
```

**Acid Spit:**
```
attack_id: 102
attack_name: "Acid Spit"
effect_type: "PROJECTILE_SPIT"
damage: 1.5
cooldown: 1.2
projectile_speed: 250.0
knockback_magnitude: 50.0
color: Color(0.2, 0.8, 0.1)
modifiers: {
  "acid_on_hit": true,
  "acid_duration": 2.0,
  "acid_dps": 0.3
}
```

## Notes

- Resource can be instantiated in code or created as .tres files (decide later)
- Modifiers are schemaless (any key-value pair allowed) for flexibility
- Future: charge scaling can be added as optional `is_chargeable` and `max_charge_mult`

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
7

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: GREEN (133 primary + 122 adversarial = 255 total assertions passed, 0 failed). Full suite (`run_tests.gd`) exit 0 confirmed during pre-push hook.
- Static QA: PASS (gd-review + gd-organization clean on `scripts/attacks/attack_resource.gd`)
- Integration: PASS — commit `be206a7` pushed to `origin/main`. Pre-push hook ran full Godot test suite, all PASS.

## Blocking Issues
- None

## Escalation Notes
- None

---

# EXECUTION PLAN

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Freeze AttackResource property list, defaults, and modifiers contract | Spec Agent | Ticket AC, design spec (`project_board/specs/mutation_attack_system_design_spec.md`), existing enemy attack scripts | Spec at `project_board/specs/m11_04_attack_resource_spec.md` | None | All properties frozen with types, defaults, and rationale. Reconcile ticket vs design spec discrepancies (knockback_direction, range shadowing, description/projectile_lifetime). Modifiers contract defined. | `range` may shadow GDScript built-in — must test or rename to `attack_range`. knockback_direction placement ambiguous between ticket and design spec. |
| 2 | Write behavioral test suite for AttackResource | Test Designer Agent | Frozen spec from T1 | Test file at `tests/scripts/attacks/test_attack_resource.gd` — RED until implementation | T1 | Tests cover: instantiation, class_name, extends Resource, all property defaults, typed access, serialization round-trip (Resource.duplicate), modifier dictionary read/write, four example configs (Claw, Acid, Carapace, Adhesion). | Data-only Resource tests can't verify runtime behavior — only property contracts. |
| 3 | Adversarial test deepening | Test Breaker Agent | T2 test suite, frozen spec | Extended test file or adversarial file — RED | T1, T2 | Edge cases: zero/negative damage, empty attack_name, unknown effect_type, very large modifier dictionaries, nested modifier values, Color boundary values, duplicate attack_ids. | Some edge cases may be valid (e.g., zero damage for utility attacks). Spec should clarify. |
| 4 | Implement AttackResource class | Gameplay Systems Agent | Frozen spec, RED tests from T2+T3 | `scripts/attacks/attack_resource.gd` — all tests GREEN | T1, T2, T3 | File created with `class_name AttackResource`, `extends Resource`, all exported properties with correct types and defaults. `run_tests.sh` exit 0. | First file in `scripts/attacks/` — directory must be created. First custom Resource in project. |
| 5 | Static QA review | Static QA Agent | Implementation from T4 | Review findings or clean pass | T4 | `task hooks:gd-review` passes on new/changed files. No unexplained tuning literals. Proper typing on all exports. | Minimal risk — data-only class. |
| 6 | AC Gatekeeper validation | AC Gatekeeper Agent | All prior artifacts | Ticket ACs verified with evidence | T4, T5 | All 6 ticket ACs satisfied with test output evidence. `run_tests.sh` exit 0 confirmed. | None — straightforward verification. |

## Notes
- Tasks are independent once dependencies are satisfied; each is small enough for one agent run.
- T1 (Spec) must reconcile three discrepancies between ticket AC and design spec before TEST_DESIGN.
- Spec exit type: `generic` (no destructive/randomness/load-open concerns).
- No Python code involved — diff-cover preflight not applicable.
- Downstream: M11-05 (AttackExecutor) consumes AttackResource but is not gated by this ticket.

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
- None

## Status
Complete

## Reason
All 6 acceptance criteria verified with explicit evidence. (1) AttackResource class exists at `scripts/attacks/attack_resource.gd` with `class_name AttackResource extends Resource`. (2) All 15 `@export`-typed properties match spec Section 5 frozen property list. (3) Four example configurations (Claw, Acid, Carapace, Adhesion) documented in spec ATK-09 and validated by tests test_atk09_*. (4) Modifiers system documented in spec ATK-07 with 13 known keys. (5) 75 tests, 255 assertions GREEN — covering property access (ATK-01–ATK-07), serialization round-trip (ATK-08), example configs (ATK-09), and adversarial edge cases (EC-01–EC-14, ADV-01–ADV-15). (6) Full suite (`run_tests.gd`) exit 0 confirmed during pre-push hook. Commit `be206a7` pushed to `origin/main`.
