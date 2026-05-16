# Pattern Mapping Audit: Blobert Milestones vs. Battle-Tested Architecture

**Date:** 2026-05-16  
**Goal:** Map kirby64's architectural patterns onto blobert's current milestone plan to identify:
1. What patterns are already aligned
2. What gaps exist in current specs
3. Which milestones benefit most from enriched specs
4. How to integrate patterns without breaking existing tickets

---

## Current Blobert Scope Overview

**Core gameplay milestones (M1–M3, M11–M12):**
- ✅ M1: Core Movement (DONE) — player controller, jump, wall cling, camera
- ✅ M2: Infection Loop (DONE) — mutation slots, infection state machine
- ✅ M3: Dual Mutation Fusion (DONE) — fusion combinations, slot interaction
- 📋 M11: Base Mutation Attacks (BACKLOG) — 4 base attacks + input/cooldown framework
- 📋 M12: Fused Mutation Attacks (BACKLOG) — attack combos from fusion

**Enemy systems (M5–M10, M18):**
- Procedural enemy generation, animation wiring, attacks, AI

**Polish & tools (M13–M20, M21–M29):**
- Visual identity, terrain, menus, tutorial, camera juice, editors

---

## Pattern 1: State Machine

### Current State
**M1 (Movement) spec status:** ✅ Exists (`jump_tuning`, `wall_cling`, `movement_controller`)

**What exists:**
- Player controller (CharacterBody3D)
- Jump mechanics with tuning
- Wall cling

**What's missing:**
- **No explicit state machine** — jump/walk/etc. are ad-hoc conditionals
- **No defined state list** — unclear what states player can be in
- **No transition rules** — no guard against invalid transitions (e.g., can jump while wall-clinging?)
- **No specs for:** INHALE, ABILITY_USE, CHARGE_UP, HURT states

### Blobert's Attack Model (M11)
**Ticket: `attack_input_and_cooldown_framework`**
```
Current: Per-mutation cooldown timer. Pressing attack:
  1. Check if active mutation exists
  2. Check if cooldown expired
  3. Fire that mutation's attack
  4. Start cooldown timer

Missing: No state blocking for attacks.
  - Can attack while being damaged?
  - Can attack while wall-clinging?
  - Can attack while... [unknown, no state machine]
```

### Recommendation

**Gap:** M1's player controller lacks an explicit state machine. Before M11 attacks can be properly scoped, we need:

**New spec:** `player_state_machine_spec.md`
- Define Blobert's states (IDLE, WALK, JUMP, FALL, WALL_CLING, ABSORB, MUTATE, ATTACK_USE, HURT, DEAD, etc.)
- Define transition rules (can't attack while HURT, can attack while FALL, etc.)
- Encode this in a RefCounted FSM (like kirby64)
- Add to M1 as a **refactor** (non-breaking, just codifies existing behavior)

**Impact on M11:** Attack framework ticket becomes simpler — just checks `state_machine.can_transition_to(ATTACK_USE)` instead of ad-hoc guards.

---

## Pattern 2: Physics Frame Order

### Current State
**M1 specs:** Jump, wall cling, movement controller exist but no frame-order spec.

**What's missing:**
- **No documented order:** gravity before input? collision mask before move? renderer sync when?
- **No coyote time mentioned** — can the player jump after walking off a ledge?
- **No jump buffer** — frame-perfect jumps?
- **No one-way platform spec** — how do we handle jumping through platforms from below?

### Blobert's Current Jump (from `jump_tuning` spec)
Likely: jump velocity set, gravity applied, move_and_slide() called. But no spec for:
- Jump buffer (0.1s before landing to queue jump)
- Coyote time (0.1s after leaving ground to still jump)
- Collision mask behavior (one-way platforms)

### Recommendation

**Update:** `movement_controller.md` or new `player_physics_frame_order_spec.md`
- Document the exact _physics_process order (currently ad-hoc in code)
- Define JUMP_BUFFER_TIME = 0.1s AC
- Define COYOTE_TIME = 0.1s AC
- Define one-way platform behavior AC

**Impact on M1:** Refactor only (no feature change), but clarifies expected behavior for M11+ (attacks need to work mid-air, during wall cling, etc.).

---

## Pattern 3: Data-Driven Ability Dispatch

### Current State
**M11: Base Mutation Attacks**
- 4 mutation attacks: Claw, Acid, Carapace, Adhesion
- Current model: **per-mutation method** (e.g., `claw_attack()`, `acid_attack()`)

**Ticket example (Claw):**
```
Acceptance Criteria:
- Swipe hitbox activates in front of player (~1.5 units)
- Animation plays (VFX placeholder OK)
- On hit: deal damage
- If enemy WEAKENED → directly transition to INFECTED
- Cooldown: 0.8s
- Hitbox active one frame only
```

**What's missing:**
- No **EffectType** enum (PROJECTILE, MELEE_CLOSE, AURA, etc.)
- No **data model** (attack properties live in code, not in a resource)
- No **charge scaling** (all attacks are non-chargeable currently)
- No **sustained/channeled abilities** (beam, sleep, etc.)
- Scaling to **M12 fused attacks** unclear (do we write per-combo code, or data-driven?)

### M12: Fused Mutation Attacks
- "One fused attack per fusion combination"
- Unclear how many combos: 4 base = C(4,2) = 6 combos? Or 16 (4×4)?
- **No spec** for how fused attacks differ from base

### Recommendation

**Critical gap:** M11 needs a **data-driven ability system spec** before tickets can be finalized.

**New spec:** `mutation_attack_system_design_spec.md`
- Define EffectType enum (specific to blobert: PROJECTILE_SPIT, MELEE_SWIPE, LUNGE, SLAM, etc.)
- Define AttackResource (damage, cooldown, effect_type, range, knockback)
- Design dispatch: match on effect_type, not mutation ID
- Document how fused attacks are combos: base_1 + base_2 → new effect_type or parameter override

**Example:** Claw + Acid = "Poisoned Swipe" (MELEE_SWIPE with poison_duration param)

**Impact on M11:**
- Refactor attack input framework to use new data model
- M11 tickets become shorter (data lives in resource, not code)
- M12 scales cleanly (add new resource, no new code paths)

---

## Pattern 4: Charge Scaling

### Current State
**None.** M11 attacks have fixed cooldowns, no mention of charging.

### Recommendation

**Deferred to M12 or later** — but spec should reserve the mechanism.

**In `mutation_attack_system_design_spec.md`:**
```
Future: Chargeable attacks (M12+)
- Each attack can have is_chargeable: bool
- Charge level: 0.0–1.0 while button held
- Damage multiplier: 1.0 + charge_level * (MAX_MULT - 1.0)
- UI shows charge bar

Not in M11 (no charging), but system designed to support it.
```

---

## Pattern 5: Sustained / Channeled Abilities

### Current State
**None.** All M11 attacks are instant or short-duration.

### Recommendation

**Deferred to M12+.** Spec should allow for it.

**In system design:**
```
Sustained ability example: "Carapace Charge"
- effect_type: CHANNELED (new)
- Hold attack → state = CHARGE_UP, timer increments
- Release → state = ATTACK_USE, execute charge, timer counts down to 0

Beam-channel example (for later combos):
- Hold attack → sustained laser
- Ticks per frame, deal damage to enemies in cone
- Release → end ability
```

---

## Pattern 6: Input Handling & Action-Based Input

### Current State
**M11 ticket:** `attack_input_and_cooldown_framework`
```
- Register "attack" action
- Press attack → fire active mutation's attack (if not on cooldown)
- Input consumed (doesn't trigger infect/absorb)
```

**What's missing:**
- No InputMapper spec (actions registered where?)
- No input action list spec
- No documentation of which states permit attack input

### Recommendation

**New spec:** `input_action_mapping_spec.md`
- List all input actions: move_left, move_right, jump, absorb, mutate, attack, swap_mutation, menu
- Centralize in InputMapper autoload (already exists, just not documented)
- Document which states permit which actions:
  - IDLE/WALK: all actions
  - JUMP/FALL: move, jump (float), attack
  - WALL_CLING: move, jump, attack, detach
  - ABSORB: none (animation lock)
  - HURT: none (stun lock)

**Impact on M11:** Clarifies attack input blocking.

---

## Pattern 7: Renderer Sync (One-Way Data Flow)

### Current State
**M1 (Camera, Visuals):** Likely ad-hoc sync.

**What's missing:**
- No spec for renderer state updates
- No guarantee of one-way data flow (renderer → controller checks?)
- No documentation of which state properties renderer reads

### Recommendation

**New spec:** `player_renderer_sync_spec.md`
- Controller syncs to renderer each _physics_process
- Renderer reads: facing, current_state, charge_level (if applicable), animation_frame
- Renderer writes: nothing (read-only from controller's perspective)
- Examples of what breaks: renderer emitting signals back to controller

**Impact on M11+:** Attack animations don't break gameplay (renderer is read-only).

---

## Pattern 8: Enemy Interaction (Groups, Distance Queries, Knockback)

### Current State
**M8 (Enemy Attacks) and M5+ specs** — exists but likely ad-hoc.

**What's missing:**
- No spec for how attacks query enemies (group names, distance checks?)
- No spec for knockback model (static or dynamic?)
- No spec for damage call signature (damage + knockback vector?)

### Recommendation

**New spec:** `attack_enemy_interaction_spec.md`
- Enemies are in "enemy" group
- Attacks query with: get_tree().get_nodes_in_group("enemy")
- Distance check via vector.length() or Area3D overlap?
- Damage signature: `enemy.take_damage(damage: float, knockback: Vector3 = Vector3.ZERO)`
- Knockback is independent of damage (can have damage=0, knockback=X for push effects)
- Dynamic knockback examples: push away from player, pull toward player

**Impact on M11+:** Consistent attack-to-enemy interface across all mutations.

---

## Pattern 9: Cooldown Semantics (Use Duration Only)

### Current State
**M11:** Per-mutation cooldown (e.g., Claw cooldown = 0.8s)

**Model:** Cooldown = time before next use (standard game design)

**Potential issue:** If we shift to a data-driven system, we need to clarify:
- Is cooldown separate from ability duration?
- Can ability be interrupted?
- Does unfinished duration refund the cooldown?

### Recommendation

**Clarify in M11 spec:** Which model do we use?

**Option A: Simple Cooldown (current)**
```
Press attack → starts cooldown timer
Timer counts down
When expired, attack available again
```

**Option B: Use Duration (kirby64 pattern)**
```
Press attack → ability becomes "active"
Active ability plays for use_duration
After use_duration, ability ends, can attack again immediately
```

**Recommendation:** Stick with **Option A for M11** (simpler, matches current design).  
Document in spec. If M12+ wants to shift, it's a conscious decision.

---

## Pattern 10: Knockback and Dynamic Enemy Interaction

### Current State
**M8 (Enemy Attacks):** Likely each enemy has hardcoded attack behavior.

**What's missing:**
- No spec for how player attacks push/pull enemies
- No spec for dynamic knockback (e.g., Claw knocks back farther if enemy is weak)

### Recommendation

**In `attack_enemy_interaction_spec.md`:**
- Static knockback: (X, Y, 0) applied to all hit enemies
- Dynamic knockback example: Claw knocks back farther if enemy is WEAKENED
  ```gdscript
  var knockback = Vector3(facing * 100.0, 80.0, 0.0)
  if enemy.state == WEAKENED:
    knockback *= 1.5
  ```

**Impact on M11:** Claw can have special interaction with WEAKENED enemies (documented in spec).

---

## Recommended Spec Creation Order

**Phase 1: Foundation (Needed for M11)**
1. ✅ `player_state_machine_spec.md` — Define states, transitions (refactor M1)
2. ✅ `player_physics_frame_order_spec.md` — Coyote, jump buffer, collision order (refactor M1)
3. ✅ `mutation_attack_system_design_spec.md` — EffectType, data model, dispatch (critical for M11)
4. ✅ `input_action_mapping_spec.md` — Input actions, which states permit which actions (clarify M11)
5. ✅ `attack_enemy_interaction_spec.md` — Enemy queries, knockback, damage signature (critical for M11)

**Phase 2: Polish (Nice-to-have for M11, critical for M12+)**
6. ✅ `player_renderer_sync_spec.md` — Renderer read-only, sync order
7. ✅ `mutation_cooldown_semantics_spec.md` — Use duration vs. cooldown clarity

**Phase 3: Extended Features (M12+)**
8. ⏱️ `charge_scaling_spec.md` — Charge level, damage multiplier (if charging added)
9. ⏱️ `sustained_attack_spec.md` — Hold-to-channel attacks (if added)

---

## Ticket Enrichment Plan

### M11: Base Mutation Attacks

**Current ticket:** `attack_input_and_cooldown_framework`
- ➕ Add AC: "State machine blocks attack input in HURT, DEAD, ABSORB states"
- ➕ Add AC: "Attack dispatch is data-driven; new attacks require no framework code changes"

**Current tickets:** `claw_player_attack`, `acid_player_attack`, etc.
- ➕ Add EffectType to each spec (MELEE_SWIPE for Claw, PROJECTILE_SPIT for Acid, etc.)
- ➕ Add knockback vector (static or dynamic)
- ➕ Add damage formula (base damage, scaling if applicable)
- ➕ Clarify cooldown semantics (active for 0.3s, then available)

### M12: Fused Mutation Attacks

**New tickets needed:**
1. **Fused attack system design** — How does 4×4 (or C(4,2)) combo matrix map to attacks?
   - Option A: Hardcode each combo's behavior
   - Option B: Data-driven (combo_a + combo_b = new EffectType, inherit or override params)
   - Recommendation: **Option B** (extensible, data-driven)

2. **Per-combo attack specs** — Once model is clear, spec each attack

---

## Dependency Graph: What Needs What

```
M1 (DONE)
└── player_state_machine_spec (NEW — refactor M1)
    └── player_physics_frame_order_spec (NEW — refactor M1)
        └── M11: attack_input_and_cooldown_framework
            ├── input_action_mapping_spec (NEW)
            ├── mutation_attack_system_design_spec (NEW — critical blocker)
            ├── attack_enemy_interaction_spec (NEW)
            ├── M11 base attack tickets (4 tickets: claw, acid, carapace, adhesion)
            │   └── M12: fused_attack_system (NEW — combo matrix)
            │       └── M12 fused attack tickets (6–16 tickets depending on combo count)
```

---

## Implementation Order

1. **Week 1:** Write M1 refactor specs (state machine, frame order)
   - Non-breaking, codifies existing behavior
   - Small refactor to controller: add RefCounted FSM, document order

2. **Week 2:** Write M11 foundation specs (attack system, input, enemy interaction)
   - Critical for unblocking M11 tickets
   - Refactor attack framework to use data-driven dispatch

3. **Week 3:** Enrich M11 attack tickets with new specs
   - Each mutation attack gets EffectType, knockback, etc.
   - Implement 4 base attacks using new framework

4. **Week 4:** Design M12 fused attack system
   - Decide: hardcoded vs. data-driven
   - Write fused_attack_system spec
   - Implement first few fused combos

---

## Risk Assessment

### Low Risk (Refactors)
- Adding FSM to M1 (already does this implicitly)
- Documenting physics frame order (already follows it)

### Medium Risk (M11 Framework)
- Shifting from per-method to data-driven dispatch
- Careful: must not break M1 progress
- Mitigation: refactor in a branch, validate no behavior change

### High Risk (M12 Scaling)
- Combo matrix size unclear (6 vs. 16 combos)
- If data-driven: must design params carefully to avoid explosion of special cases
- Mitigation: design matrix early, validate extensibility with 3–4 fused combos

---

## Metrics for Success

✅ **All M11 tickets have explicit EffectType**  
✅ **State machine blocks attack input in correct states**  
✅ **M12 can add a new fused combo with data-only change (no code)**  
✅ **All attack specs have knockback and damage vectors documented**  
✅ **Input action mapping is centralized and exhaustive**

---

## Next Steps

**Today:**
1. Read this audit
2. Decide: commit to data-driven attack system for M11, or defer to M12?
3. If yes → start writing `mutation_attack_system_design_spec.md`

**This week:**
1. Write M1 refactor specs (state machine, physics order)
2. Write M11 foundation specs (attack system, input, enemy interaction)
3. Refactor M1 controller to add FSM (non-breaking)

**Next week:**
1. Enrich M11 attack tickets with new data model
2. Implement first mutation attack using data-driven dispatch
3. Plan M12 combo matrix

