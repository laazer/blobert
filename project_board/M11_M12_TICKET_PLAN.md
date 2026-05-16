# M11 & M12 Ticket Plan: Data-Driven Attack System

**Decision:** Dynamic knockback direction from M11 (pull-toward abilities planned)  
**Model:** Resource-based, single-dispatch, extensible modifiers  
**Timeline:** 8–10 weeks total (M1 refactor + M11 implementation + M12 prep)

---

## Phase 1: Foundation (M1 Refactor) — Weeks 1–2

These are non-breaking refactors that codify existing behavior.

| Ticket | Status | Type | Description | Dependencies | Est. Effort |
|--------|--------|------|-------------|--------------|-------------|
| **1.1** Add explicit state machine to PlayerController3D | NEW (ready) | Refactor | Extract implicit states (IDLE, WALK, JUMP, FALL, WALL_CLING, HURT, DEAD) into RefCounted FSM with transition rules. No behavior change, just codification. | None | 4h |
| **1.2** Document physics frame order in PlayerController3D | NEW (ready) | Refactor | Document _physics_process order: state update → timers → state dispatch → collision mask → sync renderer → move_and_slide. Add coyote time (0.1s) and jump buffer (0.1s) ACs. | 1.1 | 2h |
| **1.3** Add input action mapping spec | NEW (ready) | Spec | Centralize input actions (move_left, move_right, jump, attack, absorb, mutate, swap_mutation, menu). Document which states permit which actions. | None | 1h |

---

## Phase 2: Attack System Foundation (M11 Core) — Weeks 3–4

These tickets implement the data-driven architecture and integrate with M1.

| Ticket | Status | Type | Description | Dependencies | Est. Effort |
|--------|--------|------|-------------|--------------|-------------|
| **2.1** Implement AttackResource class | NEW (ready) | Implementation | Create Godot Resource with properties: attack_id, effect_type, damage, cooldown, range, startup_frames, knockback_magnitude, knockback_direction, color, vfx_scale, modifiers (Dictionary). Tests validate property access. | None | 3h |
| **2.2** Implement AttackExecutor with MELEE_SWIPE handler | NEW (ready) | Implementation | Create AttackExecutor node (child of PlayerController3D). Implement single dispatch function `execute_attack(attack: AttackResource)`. Implement `_handle_melee_swipe()` handler: startup wait, hitbox query, damage, knockback, modifiers, VFX. Tests cover: basic hit, no hit, knockback application. | 2.1 | 5h |
| **2.3** Implement AttackExecutor with PROJECTILE_SPIT handler | NEW (ready) | Implementation | Implement `_handle_projectile_spit()` handler: create projectile, set velocity, attach modifiers, add to scene. Reuse existing projectile system (from M8 enemy attacks). Tests cover: projectile creation, velocity, modifier attachment. | 2.1, 2.2 | 4h |
| **2.4** Implement AttackDatabase (resource files approach) | NEW (ready) | Implementation | Create directory structure: `res://attacks/base/` and `res://attacks/fused/`. Implement AttackDatabase autoload that loads .tres files on startup. Implement `get_base_attack(mutation_id)` and `get_fused_attack(slot_a, slot_b)`. Tests validate lookup and fallback behavior. | 2.1 | 3h |
| **2.5** Integrate AttackExecutor into PlayerController3D | NEW (ready) | Integration | Wire `_try_attack()` in PlayerController3D to call `AttackDatabase.get_base_attack()` and `AttackExecutor.execute_attack()`. Track per-mutation cooldowns in `_mutation_cooldowns` dict. Tests cover: input triggers attack, cooldown blocks next attack, wrong state blocks attack. | 1.1, 1.2, 2.1, 2.2, 2.3, 2.4 | 4h |
| **2.6** Implement dynamic knockback direction system | NEW (ready) | Implementation | Add knockback_direction property to AttackResource ("away", "toward", "none"). In handlers, calculate direction based on knockback_direction. Tests cover: push-away, pull-toward, zero knockback. | 2.1, 2.2, 2.3 | 3h |
| **2.7** Populate base attack resources (4 files) | NEW (ready) | Data | Create `.tres` files: claw_swipe.tres, acid_spit.tres, carapace_slam.tres, adhesion_lunge.tres. Set all properties (damage, cooldown, range, effect_type, modifiers). | 2.1, 2.4 | 2h |

---

## Phase 3: M11 Tickets (Base Mutation Attacks) — Weeks 5–7

**Important:** These tickets are UPDATED from current backlog, not brand new.

### Tickets to UPDATE (from current M11 backlog)

| Ticket | Current Name | Update | Change |
|--------|-------------|--------|--------|
| **3.1** | attack_input_and_cooldown_framework | UPDATE | Remove mention of "per-mutation cooldown timer logic" — that's now in PlayerController3D.attack_input. Add AC: "Attack dispatch is data-driven; new attacks require no framework code changes." Reference mutation_attack_system_design_spec.md. |
| **3.2** | claw_player_attack | UPDATE | Add section "Attack Definition": attack_id=101, effect_type=MELEE_SWIPE, damage=2.0, cooldown=0.8, range=1.5, knockback_magnitude=100.0, knockback_direction="away". Remove implementation details; reference spec for how MELEE_SWIPE is handled. Update AC to reference attack_id instead of method names. |
| **3.3** | acid_player_attack | UPDATE | Add section "Attack Definition": attack_id=102, effect_type=PROJECTILE_SPIT, damage=1.5, cooldown=1.2, projectile_speed=250, modifiers={acid_on_hit: true, acid_duration: 2.0, acid_dps: 0.3}. Reference spec for handler. Update AC. |
| **3.4** | carapace_player_attack | UPDATE | Add section "Attack Definition": attack_id=103, effect_type=MELEE_SWIPE, damage=2.5, cooldown=1.3, range=2.0, knockback_magnitude=150.0, knockback_direction="away", startup_frames=4 (slower, heavier). Update AC. |
| **3.5** | adhesion_player_attack | UPDATE | Add section "Attack Definition": attack_id=104, effect_type=PROJECTILE_SPIT or LUNGE (TBD). If LUNGE: damage=1.8, cooldown=1.0, lunge_distance=3.0, range=1.2 (melee after landing). Modifiers: adhesion_stun (TODO define). Update AC. |

### New Integration Tickets (M11)

| Ticket | Status | Type | Description | Dependencies | Est. Effort |
|--------|--------|------|-------------|--------------|-------------|
| **3.6** (NEW) | Verify base attack cooldown behavior | NEW (ready) | Test that each of 4 base attacks has correct cooldown, can be used again after cooldown expires, and correct state blocks allow/deny attack input. Verify HUD displays remaining cooldown. | 3.1–3.5, 2.5 | 2h |
| **3.7** (NEW) | Verify base attack damage and knockback | NEW (ready) | Test that each base attack deals correct damage to enemies, applies correct knockback (direction + magnitude), and modifiers (poison, acid, etc.) apply correctly. | 3.1–3.5, 2.2, 2.3, 2.6 | 3h |

---

## Phase 4: M12 Tickets (Fused Mutation Attacks) — Weeks 8–10

**Important:** M12 tickets are mostly data creation (no code changes needed).

### Tickets to UPDATE (from current M12 backlog)

| Ticket | Current Name | Update | Change |
|--------|-------------|--------|--------|
| **4.1** | (New ticket needed) | Fused attack system integration | Spec how fused attacks are triggered: check if both slots filled, lookup `AttackDatabase.get_fused_attack(slot_a, slot_b)`, call `AttackExecutor.execute_attack()`. Reference mutation_attack_system_design_spec.md. No code implementation needed (uses existing framework from M11). |

### New Data Tickets (M12)

| Ticket | Status | Type | Description | Dependencies | Est. Effort |
|--------|--------|------|-------------|--------------|-------------|
| **4.2** | Create fused attack resources (6 combos) | NEW (ready) | Create `.tres` files for unordered pairs: claw_acid, claw_carapace, claw_adhesion, acid_carapace, acid_adhesion, carapace_adhesion. Each file defines unique effect_type, damage, cooldown, modifiers. Example: claw_acid = Poison Claw (MELEE_SWIPE + poison modifier). | 2.1, 2.4, 3.1–3.5 | 4h |
| **4.3** | Create fused attack resources (ordered pairs, optional) | NEW (backlog) | *Optional.* If order matters (Claw+Acid ≠ Acid+Claw), create 10 more `.tres` files for reversed pairs (acid_claw, carapace_claw, adhesion_claw, etc.). Each has distinct behavior. Defer to M12 phase 2 if scope grows. | 4.2 | 5h |
| **4.4** | Verify fused attacks with new combos | NEW (ready) | Test that each fused attack loads correctly, dispatches to correct handler, deals correct damage, applies modifiers. Verify cooldown tracking doesn't interfere with base attack cooldowns. | 4.1, 4.2, 2.5 | 3h |

---

## Phase 5: Extended Handlers (Future, M12+) — Weeks 11+

These are future tickets for new effect types (not in M11 or M12 Phase 1).

| Ticket | Status | Type | Description | Dependencies | Est. Effort |
|--------|--------|------|-------------|--------------|-------------|
| **5.1** | Implement CHARGE effect type handler | FUTURE (backlog) | Implement `_handle_charge()`: hold to accumulate charge, release to execute at current charge level. Scale damage by charge level (1.0–2.2×). Allows chargeable attacks in M12+. | 2.1, 2.2 | 4h |
| **5.2** | Implement LUNGE effect type handler | FUTURE (backlog) | Implement `_handle_lunge()`: short dash forward + melee hit at end. Useful for combos like Adhesion+Claw. | 2.1, 2.2, 2.3 | 3h |
| **5.3** | Add new modifiers (freeze, weaken, etc.) | FUTURE (backlog) | As needed: freeze (prevent movement), weaken (setup for direct infection), stun (disable input), etc. Each adds to handlers' `_apply_modifiers()`. | 2.1, 2.2 | 2–3h per modifier |

---

## Summary Table: Total Scope

| Phase | Tickets | Type | Total Effort | Timeline |
|-------|---------|------|--------------|----------|
| **Phase 1: M1 Refactor** | 1.1–1.3 | Refactor + Spec | 7h | Weeks 1–2 |
| **Phase 2: M11 Core** | 2.1–2.7 | Implementation + Data | 24h | Weeks 3–4 |
| **Phase 3: M11 Base Attacks** | 3.1–3.7 | Update + Integration | 12h | Weeks 5–7 |
| **Phase 4: M12 Fused Attacks** | 4.1–4.4 | Integration + Data | 12h | Weeks 8–10 |
| **Phase 5: Extended Handlers** | 5.1–5.3 | Future (backlog) | TBD | Weeks 11+ |
| **TOTAL (M11+M12)** | 19 | Mix | ~55h | 10 weeks |

---

## Dependency Graph

```
Phase 1 (Refactor M1)
├── 1.1: State Machine
├── 1.2: Physics Frame Order
└── 1.3: Input Mapping

Phase 2 (M11 Core)
├── 2.1: AttackResource
├── 2.2: MELEE_SWIPE handler (→ 2.1)
├── 2.3: PROJECTILE_SPIT handler (→ 2.1, 2.2)
├── 2.4: AttackDatabase (→ 2.1)
├── 2.5: PlayerController3D integration (→ 1.1, 1.2, 2.1–2.4)
├── 2.6: Dynamic knockback (→ 2.1, 2.2, 2.3)
└── 2.7: Base attack resources (→ 2.1, 2.4)

Phase 3 (M11 Attacks)
├── 3.1–3.5: UPDATE existing tickets (→ 2.1–2.7)
├── 3.6: Cooldown verification (→ 3.1–3.5, 2.5)
└── 3.7: Damage/knockback verification (→ 3.1–3.5, 2.2, 2.3, 2.6)

Phase 4 (M12 Fused)
├── 4.1: Fused attack integration spec (→ Phase 2, Phase 3)
├── 4.2: Fused attack resources (→ 2.1, 2.4, 3.1–3.5)
├── 4.3: Optional reversed pairs (→ 4.2)
└── 4.4: Verification (→ 4.1, 4.2, 2.5)

Phase 5 (Future)
├── 5.1: CHARGE handler (→ 2.1, 2.2)
├── 5.2: LUNGE handler (→ 2.1, 2.2, 2.3)
└── 5.3: New modifiers (→ 2.1, 2.2)
```

---

## Implementation Order (Week by Week)

### Week 1–2: Foundation (Phase 1)
- Write/review: 1.1 (state machine spec + implementation)
- Write/review: 1.2 (physics frame order spec)
- Write/review: 1.3 (input mapping spec)
- **Blocker check:** Can M1 move to "testing" or does M1 refactor break gameplay?

### Week 3–4: M11 Core (Phase 2)
- Implement: 2.1 (AttackResource)
- Implement: 2.2 (MELEE_SWIPE handler)
- Implement: 2.3 (PROJECTILE_SPIT handler)
- Implement: 2.4 (AttackDatabase)
- Integrate: 2.5 (PlayerController3D)
- Implement: 2.6 (Dynamic knockback)
- Create: 2.7 (4 base attack resources)
- **Blocker check:** Run tests, verify no regressions from M1 refactor

### Week 5–7: M11 Attacks (Phase 3)
- Review + update: 3.1 (framework spec)
- Review + update: 3.2–3.5 (4 base attack tickets with new format)
- Implement attack-specific logic if needed (modifiers, special behavior)
- Create: 3.6 (cooldown verification tests)
- Create: 3.7 (damage/knockback verification tests)
- **Exit criteria:** 4 base attacks are playable, all tests pass, no regressions

### Week 8–10: M12 Fused (Phase 4)
- Write: 4.1 (fused attack integration spec)
- Create: 4.2 (6–16 fused attack resource files, depending on ordered vs. unordered)
- Create: 4.3 (optional: reversed pairs if ordered)
- Create: 4.4 (verification tests)
- **Exit criteria:** At least 1 fused combo is playable, all 6–16 combos load without error

---

## Key Decisions Needed

| Decision | Recommendation | Impact |
|----------|-----------------|--------|
| **Knockback direction** | Dynamic from M11 (away, toward, none) | Enables pull-toward abilities early; adds ~2h to Phase 2 |
| **Ordered vs. unordered combos** | Unordered (Claw+Acid = Acid+Claw) | Simplifies M12: 6 combos instead of 12. Can upgrade to ordered later if desired. |
| **Resource files vs. centralized DB** | Resource files (Option A) | Easier iteration, visual inspection, version control. +1h in Phase 2. |
| **Effect types in M11** | MELEE_SWIPE, PROJECTILE_SPIT only | Defer CHARGE, LUNGE to Phase 5 (M12+ or later). Keeps Phase 2 focused. |
| **Modifiers validation** | Allow arbitrary keys (no validation) | Faster iteration. Document known modifiers, add validation in Phase 5 if needed. |

---

## Blockers & Risks

| Risk | Mitigation |
|------|-----------|
| **M1 refactor breaks existing gameplay** | Test extensively after Phase 1. If issues, revert refactor and keep implicit state machine. |
| **Projectile system integration (2.3)** | Verify projectiles created by PROJECTILE_SPIT handler work with existing enemy collision. Reuse existing projectile class. |
| **Resource file loading (2.4)** | Test that AttackDatabase loads all `.tres` files at startup. Handle missing files gracefully. |
| **Modifier system extensibility** | Start with 5–6 known modifiers (poison, acid, slow, etc.). Add others as-needed in Phase 5. |
| **M12 ordered vs. unordered decision** | Recommend unordered for Phase 4 (6 combos). If team wants ordered (16 combos), decision must be made by Week 8. |

---

## Deliverables Checklist

- [ ] Phase 1: M1 refactor specs + implementation (state machine, physics order, input mapping)
- [ ] Phase 2: AttackResource, AttackExecutor, AttackDatabase, 4 base attacks (all .tres files)
- [ ] Phase 3: Updated M11 tickets (3.1–3.5) + verification tests (3.6–3.7)
- [ ] Phase 4: Fused attack spec (4.1) + 6–16 fused attack resources (4.2–4.3) + verification (4.4)
- [ ] Phase 5: Backlog for CHARGE, LUNGE, new modifiers

---

## Success Metrics

✅ **Phase 1:** M1 gameplay unchanged; refactor improves code clarity (state machine, physics order documented)

✅ **Phase 2:** AttackExecutor dispatches all 4 base attacks correctly; all tests pass; no new bugs introduced

✅ **Phase 3:** All 4 base attacks are playable in sandbox; cooldowns work; damage/knockback/modifiers apply correctly

✅ **Phase 4:** At least 3 fused combos are playable; all 6–16 combos load without error; fused attacks feel distinct from base attacks

✅ **Overall:** New mutation can be added with zero code changes (just add base attack resource + combos)

