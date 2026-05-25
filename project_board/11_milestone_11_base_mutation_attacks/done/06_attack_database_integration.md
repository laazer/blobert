# TICKET: 06_attack_database_integration

**Milestone:** M11 Base Mutation Attacks (Core Foundation)  
**Status:** Ready  
**Type:** Implementation

## Title

Implement AttackDatabase and integrate with PlayerController3D

## Description

AttackDatabase loads all attack resources (base + fused) and provides lookups:
- `get_base_attack(mutation_id)` → AttackResource for that mutation
- `get_fused_attack(slot_a, slot_b)` → AttackResource for that combo

Integrate with PlayerController3D to:
1. Load attacks from AttackDatabase
2. Execute via AttackExecutor
3. Track per-mutation cooldowns
4. Gate input by state (use state machine from prereq 1)

## Acceptance Criteria

- [x] `AttackDatabase` autoload created (`scripts/attacks/attack_database.gd`)
- [x] Loads attack resources from `res://attacks/base/*.tres` and `res://attacks/fused/*.tres`
- [x] Methods:
  - `get_base_attack(mutation_id: int) → AttackResource`
  - `get_fused_attack(slot_a: int, slot_b: int) → AttackResource`
  - Graceful fallback if attack not found (warning, return null)
- [x] PlayerController3D wired:
  - `_try_attack()` method checks:
    1. State machine permits attack input
    2. Active mutation exists
    3. Cooldown not active
  - Calls `AttackDatabase.get_base_attack(mutation_id)`
  - Calls `AttackExecutor.execute_attack(attack_resource)`
  - Sets `_mutation_cooldowns[mutation_id] = attack_resource.cooldown`
- [x] Cooldown tracking in `_physics_process`:
  - Decrement all active cooldowns by delta
  - When cooldown reaches 0, attack available again
- [x] Input gating by state (from prereq 1):
  - Attack input only checked in states that permit it (IDLE, WALK, JUMP, FALL, WALL_CLING)
  - Attack input NOT checked in HURT, DEAD, ABSORB, MUTATE states
- [x] Tests:
  - Attack resource loads correctly
  - Fused attack lookup works (and handles missing combos)
  - Cooldown blocks attack, then allows after expiry
  - State machine blocks attack in correct states
- [x] `run_tests.sh` exits 0

## Dependencies

- M11_prereq_1_player_state_machine (state gating)
- M11_prereq_3_input_action_mapping (input action semantics)
- M11_core_1_attack_resource (attack data model)
- M11_core_2_attack_executor_handlers (execution logic)

## Integration Pseudocode

**PlayerController3D:**
```gdscript
func _physics_process(delta: float) -> void:
  state_machine.update(delta)
  _update_timers(delta)
  _handle_state(delta)  # Includes input checks
  # ... rest of physics ...

func _handle_state(delta: float) -> void:
  match state_machine.current:
    # ... IDLE, WALK, JUMP, etc. ...
    # Input checks happen here, including attack
    if Input.is_action_just_pressed("attack"):
      if state_machine.can_transition_to(ATTACK_USE):  # NEW: state gating
        _try_attack()

func _try_attack() -> void:
  var active_mutation = GameState.get_active_mutation()
  if active_mutation == NONE:
    return
  
  var cooldown_remaining = _mutation_cooldowns.get(active_mutation, 0.0)
  if cooldown_remaining > 0.0:
    return  # On cooldown
  
  var attack = AttackDatabase.get_base_attack(active_mutation)
  if not attack:
    push_error("No attack resource for mutation %d" % active_mutation)
    return
  
  AttackExecutor.execute_attack(attack)
  _mutation_cooldowns[active_mutation] = attack.cooldown

func _update_timers(delta: float) -> void:
  for mutation_id in _mutation_cooldowns:
    _mutation_cooldowns[mutation_id] = max(0.0, _mutation_cooldowns[mutation_id] - delta)
```

## Notes

- M11 core tickets don't add new states (ATTACK_USE, CHARGE_UP) yet — M11 attack tickets will do that
- AttackDatabase can load from code (in _register_base_attacks) or .tres files (decide in implementation)
- Fused attacks stored with key like "slot_a_slot_b" (e.g., "1_2" for Claw+Acid)
- If M1 already has implicit cooldown tracking, replace it with explicit per-mutation tracking

---

# EXECUTION PLAN

**Ticket ID:** M11-06
**Planning revision:** 1
**Date:** 2026-05-25
**Next agent:** Spec Agent (Task 1)

## Executive Summary

Create `AttackDatabase` as a Godot autoload that provides mutation→attack lookups (base and fused). Wire `PlayerController3D` with `_try_attack()`: state-gated attack input → AttackDatabase lookup → AttackExecutor dispatch → per-mutation cooldown tracking. Register `attack` InputMap action in `project.godot`. All four dependencies satisfied (M11-01 state machine, M11-03 input mapping, M11-04 AttackResource, M11-05 AttackExecutor).

## Dependency Matrix

| Dependency | Folder / State | Blocks M11-06? | Notes |
|------------|----------------|----------------|-------|
| M11-01 player state machine | `done/01_player_state_machine.md` | **No** (satisfied) | `PlayerStateMachine` + `PlayerController3D` wiring complete |
| M11-03 input action mapping | `done/03_input_action_mapping.md` | **No** (satisfied) | `PlayerInputActionPolicy` with `ACTION_ATTACK` defined |
| M11-04 attack resource | `done/04_attack_resource.md` | **No** (satisfied) | `AttackResource` at `scripts/attacks/attack_resource.gd` |
| M11-05 attack executor | `done/05_attack_executor_handlers.md` | **No** (satisfied) | `AttackExecutor` at `scripts/attacks/attack_executor.gd` |
| `attack_database.gd` | **Absent** | N/A | Greenfield deliverable |

**Umbrella ticket:** No. **Cycles:** None.

## Spec Exit Gate

```bash
python ci/scripts/spec_completeness_check.py \
  project_board/specs/attack_database_integration_spec.md \
  --type generic
```

## Estimated Effort (Agent Runs)

| Phase | Agent | Runs | Notes |
|-------|-------|------|-------|
| Specification | Spec Agent | 1 | Freeze AttackDatabase API, cooldown contract, state gating, mutation_id mapping, fused key format |
| Test design | Test Designer Agent | 1 | `tests/scripts/attacks/test_attack_database.gd` + controller integration tests |
| Test break | Test Breaker Agent | 1 | Missing combos, timer precision, concurrent attacks, null mutation |
| Implementation | Gameplay Systems Agent | 1–2 | AttackDatabase + PlayerController3D wiring + project.godot updates |
| Static QA | GDScript Reviewer | 1 | `task hooks:gd-review` on changed `.gd` |
| AC gatekeeper | AC Gatekeeper | 1 | AC matrix; `run_tests.sh` exit 0; commit/push before COMPLETE |

**Total:** 6–7 agent runs

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Author normative spec: AttackDatabase Node API (`get_base_attack(mutation_id)`, `get_fused_attack(slot_a, slot_b)`, `register_base_attack()`, `register_fused_attack()`), autoload contract, .tres scanning vs code registration, fused attack key format (`"a_b"`), graceful null fallback, mutation_id derivation from `_mutation_slot`, cooldown tracking contract (`_mutation_cooldowns: Dictionary`, per-frame delta decrement), state gating rules (IDLE/WALK/JUMP/FALL/WALL_CLING/FLOAT permit attack; ABSORB/MUTATE/HURT/DEAD deny per IAM-5.2), `_try_attack()` integration contract in `PlayerController3D`, AttackExecutor child-node wiring, `attack` InputMap action registration (default: F key per IAM-3.1), PFO frame placement (attack input read in Step 0, cooldown decrement in Step 2c or Step 8) | Spec Agent | Ticket AC; `attack_executor_spec.md`; `attack_resource_spec.md`; `input_action_mapping_spec.md`; `player_state_machine_spec.md`; `player_controller_3d.gd`; `attack_executor.gd`; `attack_resource.gd`; `player_input_action_policy.gd` | `project_board/specs/attack_database_integration_spec.md` | — | Spec completeness check PASS (`--type generic`); every AC maps to spec section | **Risk:** mutation_id derivation ambiguous — `_mutation_slot` system doesn't expose numeric IDs. Spec must define mapping. **Risk:** Fused attack lookup requires both slots filled; spec must define behavior when only one slot filled. **Assume:** `attack` default binding = F key per IAM-3.1 |
| 2 | Write behavioral test suite: AttackDatabase instantiation, `register_base_attack` + `get_base_attack` round-trip, `register_fused_attack` + `get_fused_attack` round-trip, missing mutation_id returns null + warning, missing combo returns null + warning, `_try_attack()` succeeds (state permits, mutation active, cooldown clear), `_try_attack()` blocked by state (HURT/DEAD/ABSORB/MUTATE), `_try_attack()` blocked by no active mutation, `_try_attack()` blocked by active cooldown, cooldown decrement over delta ticks, cooldown expiry re-enables attack, AttackExecutor `execute_attack` called with correct resource | Test Designer Agent | Approved spec from T1 | `tests/scripts/attacks/test_attack_database.gd` (RED until implementation) | T1 | Tests fail RED before implementation; assert runtime behavior not prose; cover all 11 ticket AC items | **Risk:** Controller integration tests may need scene tree setup for AttackExecutor child node. **Assume:** Mock/stub approach for mutation_id and AttackExecutor |
| 3 | Adversarial test deepening: duplicate mutation_id registration (overwrite vs error), fused lookup with slot order swapped (a,b vs b,a — symmetric?), zero/negative cooldown in AttackResource, cooldown precision at floating-point boundary, rapid sequential attack attempts, attack during executor `_is_active` (re-entrancy guard), null AttackResource in database, empty database get_base_attack, fused key collision with base key, simultaneous attack + detach input consumption | Test Breaker Agent | Spec + T2 tests | `tests/scripts/attacks/test_attack_database_adversarial.gd` (RED) | T1, T2 | New failures encode conservative assumptions; `# CHECKPOINT` where spec ambiguous | **Assume:** Strictest defensible: duplicate = overwrite, fused lookup is order-independent (sort keys) |
| 4 | Implement `AttackDatabase` Node class at `scripts/attacks/attack_database.gd`: `_base_attacks: Dictionary` (mutation_id → AttackResource), `_fused_attacks: Dictionary` (key → AttackResource), register/get methods, null fallback with `push_warning`. Wire `PlayerController3D`: instantiate `AttackExecutor` as child node, add `_mutation_cooldowns: Dictionary`, implement `_try_attack()` per spec contract, add cooldown decrement in `_post_slide_housekeeping` or timer tick method, read `attack` input in `_read_player_input()`, gate by `PlayerInputActionPolicy.is_action_permitted()` or direct state check, call `AttackDatabase.get_base_attack()` → `AttackExecutor.execute_attack()`. Register `AttackDatabase` autoload in `project.godot`. Register `attack` InputMap action in `project.godot` (F key). | Gameplay Systems Agent | Spec; red tests from T2+T3 | `scripts/attacks/attack_database.gd`, updated `scripts/player/player_controller_3d.gd`, updated `project.godot` | T3 | All T2–T3 tests GREEN; `run_tests.sh` exit 0 | **Risk:** Large `PlayerController3D` diff — keep minimal, add only attack-related code. **Risk:** project.godot autoload and input entries must be syntactically correct for Godot parser. |
| 5 | Run GDScript review on new/changed files | GDScript Reviewer (Static QA) | Tasks 4 output | `task hooks:gd-review` evidence; findings resolved | T4 | No high-priority review blockers; no unexplained tuning literals | **Risk:** Minimal — data lookup + controller wiring |
| 6 | AC gatekeeper: verify all AC checkboxes with test output evidence, `run_tests.sh` exit 0, git clean + pushed | AC Gatekeeper | Ticket AC; test evidence from T4 | Stage COMPLETE; ticket → `done/` | T5 | All 11 AC items met with evidence; commit/push verified | Per workflow enforcement |

## Notes

- **Spec exit type:** `generic` (no destructive/randomness/load-open concerns).
- **No Python code involved** — diff-cover preflight not applicable.
- **InputMap registration:** M11-06 is the first ticket to register the `attack` action in `project.godot`, per IAM spec deferred boundary.
- **Autoload:** AttackDatabase must be registered in `project.godot` `[autoload]` section — this is a Godot project config edit.
- **mutation_id mapping:** The existing `_mutation_slot` system in PlayerController3D does not expose a numeric mutation ID directly. Spec must freeze how mutation type (from `InfectionInteractionHandler`) maps to `attack_id` in `AttackResource`. This is the highest-ambiguity item.
- **Downstream:** M11 attack tickets (charge, lunge, etc.) will add new attack types and states (CHARGE_UP, ABILITY_USE); M11-06 lays the foundation.
- **Reference read-only:** `reference_projects/`, `3D-Platformer-Kit/`.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
7

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: ALL PASS — exit code 0 from `godot --headless -s tests/run_tests.gd` (98 M11-06 tests + full suite)
  - Primary: 48 tests (test_attack_database.gd, test_attack_database_controller_integration.gd)
  - Adversarial: 50 tests (test_attack_database_adversarial.gd, test_attack_database_controller_adversarial.gd)
- Static QA: PASS (gd-review clean, gd-organization clean — all files under 900 lines)
- Integration: PASS (all ACs verified with test evidence)

## Blocking Issues
None

## Escalation Notes
None

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
None

## Status
Proceed

## Reason
All 7 acceptance criteria verified with test evidence. AttackDatabase autoload + methods (ADB-1..ADB-6), PlayerController3D wiring (ADB-7..ADB-15), cooldowns, state gating, tests, and run_tests.sh exit 0. EC-20 test setup bug fixed (added dummy_slot_a fill before clear). All hooks pass.
