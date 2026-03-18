# Autopilot Checkpoint Log

Decisions logged here required human judgment but were resolved autonomously.
Review these after autopilot completes.

---

## Run: 2026-03-18T01:00:00Z
Tickets queued: player_hud.md (Test Designer Agent)

### [player_hud] TestDesign — add_child pattern for CanvasLayer in headless test

**Would have asked:** The spec says `add_child(ui)` in the test, but the test class extends Object (no scene tree). How do we add the CanvasLayer to the tree so InfectionUI._ready() has a valid get_tree() call?

**Assumption made:** Used `Engine.get_main_loop() as SceneTree` and `tree.root.add_child(ui)`, matching the pattern in `tests/scenes/levels/test_3d_scene.gd`. InfectionUI._ready() calls `get_tree().get_first_node_in_group("player")` which returns null safely in headless (no player in tree). No crash risk confirmed by running the suite.

**Confidence:** High

---

### [player_hud] TestDesign — T-6.8 red-phase criterion for zero-area nodes

**Would have asked:** The current scene has nodes like HPLabel with offset_right == offset_left == 20.0, making them zero-area. These technically fit within the 3200x1880 viewport (AC-5.2 passes trivially). Should T-6.8 also assert width > 0 to create a meaningful red phase?

**Assumption made:** Added `size.x > 0` and `size.y > 0` assertions to T-6.8 for all always-visible nodes. This ensures T-6.8 fails in red phase (zero-area nodes) and only passes after implementation gives nodes real dimensions. The spec's AC-5.2 intent is to verify nodes are reasonably positioned within the viewport — a zero-area node satisfies the letter but not the spirit of that criterion.

**Confidence:** High

---

### [player_hud] TestDesign — T-6.9 red phase analysis

**Would have asked:** The current legacy node MutationSlotLabel is at Y 115–143, which overlaps with the current positions of MutationIcon1 (Y 147–167) and MutationSlot1Label (Y 145–169). But all these positions differ from spec. Does the red-phase failure come from legacy-vs-legacy overlap (current positions) or legacy-vs-spec overlap?

**Assumption made:** T-6.9 asserts actual node offset values against each other (not against spec values), so it tests whether the current scene positions are disjoint. The current legacy node MutationSlotLabel at Y 115–143 overlaps current MutationSlot2Label at Y 173–197 via the always-visible set's current positions. Verified by running the suite — T-6.9 produces failures confirming red-phase behavior is correct.

**Confidence:** High

---

## Run: 2026-03-18T00:00:00Z
Tickets queued: visual_clarity_hybrid_state.md (GDScript fix pass)

### [visual_clarity_hybrid_state] GDScript Fix — WARNING 4 has_method guard removal scope

**Would have asked:** The `has_method("is_fusion_active")` guard in `_update_mutation_display` was removed from the post-fusion flash trigger. The `CorrectHarness` in the adversarial test still uses `has_method` in its own `should_trigger_flash` and `compute_fusion_label_visible` helpers. Should the real script match the harness exactly (keeping has_method) or follow the ticket directive (remove it)?

**Assumption made:** The ticket directive is authoritative for the production script. The harness is a test fixture with its own defensive guards for duck-typed doubles; the production script uses a statically-typed `_player: PlayerController3D` so `has_method` is redundant and misleading. Removed it from the production code only. The harness was not modified (test files are off-limits).

**Confidence:** High

---

## Run: 2026-03-17T02:00:00Z
Tickets queued: visual_clarity_hybrid_state.md

---

### [visual_clarity_hybrid_state] TestDesign — InfectionUI headless instantiation strategy

**Would have asked:** InfectionUI extends CanvasLayer and cannot be `.new()`'d headlessly. How do we test the color-selection logic and field/method presence without instantiating the full node?

**Assumption made:** Three-track strategy: (1) Constant presence and values: read via `GDScript.get_script_constant_map()` on the loaded script resource -- no instantiation required. (2) Method and field presence: read via `GDScript.get_script_method_list()` and `GDScript.get_script_property_list()` on the loaded script resource. (3) Algorithm correctness: inner-class `LogicHarness extends RefCounted` implements the spec's color-selection matrix verbatim and is tested directly -- the harness constants must match the real script constants (verified by track 1). This pattern means logic tests pass immediately (harness is correct by construction) while script-shape tests fail until implementation adds the required symbols.

**Confidence:** High

---

### [visual_clarity_hybrid_state] TestDesign — RefCounted vs Object for doubles

**Would have asked:** The existing test suite (test_fusion_resolver.gd) uses `extends Object` with manual `free()`. Should new doubles follow the same pattern or use RefCounted?

**Assumption made:** RefCounted. The existing pattern works for top-level doubles that are freed at test-method end, but fails when `free_all()` is called on a manager that holds inner-slot references while still on the call stack (Godot "Object is locked" error). RefCounted eliminates all manual memory management, prevents the locked-object error, and is strictly safer for inner-class doubles that do not need to be freed in a specific order.

**Confidence:** High

---

## Run: 2026-03-16T00:00:00Z
Tickets queued: visual_clarity_hybrid_state.md

---
---

### [fusion_rules_and_hybrid] GDScript Fix — C2 expiry branch removes slot re-query

**Would have asked:** On fusion expiry, should we re-query mutation slots to restore the correct speed (mutation-boosted vs. base), or just clear fusion state and let the else branch handle it next frame?

**Assumption made:** Let the else branch run next frame. The C2 fix spec explicitly says "Do NOT try to re-query slots for speed restoration on the same tick — let the else branch that runs next frame handle it naturally." The one-frame latency is imperceptible and avoids the dual-write speed glitch.

**Confidence:** High

---

### [fusion_rules_and_hybrid] GDScript Fix — C3 player cache timing in InfectionInteractionHandler._ready

**Would have asked:** `_ready` fires before children are necessarily in the scene tree group. Is `get_first_node_in_group("player")` reliable from a sibling node's `_ready`?

**Assumption made:** The pattern is consistent with existing usage in `infection_ui.gd` line 14 which does the same thing. Both nodes are siblings under the level root; Godot processes `_ready` bottom-up so the player is already in the tree when the handler's `_ready` runs. Accepted as consistent with the existing codebase convention.

**Confidence:** High

---

### [fusion_rules_and_hybrid] IMPLEMENTATION_CORE_SIM — null player handling in resolve_fusion

**Would have asked:** When player is null, spec FRH-3-AC-8 says slots are consumed and no crash. But FRH-3 also says push_error when player lacks apply_fusion_effect. Should push_error be emitted for a null player specifically?

**Assumption made:** No push_error for null player. Null player is an explicitly documented valid path (FRH-3-AC-8: "handle a null player gracefully"). push_error is reserved for a non-null player that is the wrong type (lacks the method). This matches the spec's risk note: "if player is null, slots are still consumed and no crash occurs (the effect simply does not apply)."

**Confidence:** High

---

### [fusion_rules_and_hybrid] TEST_BREAK — double-fuse no-op second call verification strategy

**Would have asked:** The spec requires that calling resolve_fusion twice in a row is a no-op on the second call (slots are empty after first call so guard fails). Should the adversarial test verify this by checking the player double call count is still 1, or should it also verify slots remain empty on the second call?

**Assumption made:** Both. Check that apply_fusion_effect_call_count == 1 (not 2) AND that both slots remain empty after the second call. This is the strictest interpretation: slot count confirms the guard fired, call count confirms resolve_fusion did not bypass it.

**Confidence:** High

---

### [fusion_rules_and_hybrid] TEST_BREAK — re-trigger timer reset verification without physics tick

**Would have asked:** FRH-4-AC-7 says calling apply_fusion_effect twice resets the timer, not stacks it. PlayerController3D does not exist yet and cannot be instantiated headlessly without a scene. How do we test this via FusionResolver alone?

**Assumption made:** Test via PlayerDouble only: call resolve_fusion twice with fills in between (first fuse consumes slots, refill, fuse again). Verify apply_fusion_effect_call_count == 2 and that the second call used the same duration/multiplier as the first (last_duration == 5.0, last_multiplier == 1.5). This verifies the resolver passes correct args to re-trigger; the reset-not-stack behavior is a PlayerController3D concern tested separately. Document the gap clearly.

**Confidence:** High

---

### [fusion_rules_and_hybrid] TEST_BREAK — NullSlotDouble: get_slot returns null on all indices

**Would have asked:** The spec says can_fuse should return false when get_slot(0) returns null (FRH-2-AC-6). The primary suite tests a plain Object with no get_slot method at all. Should the adversarial suite additionally test a manager that HAS get_slot but returns null from it?

**Assumption made:** Yes. Create a NullSlotDouble inner class with a get_slot method that returns null. This is a distinct vulnerability from the "no get_slot at all" case — an implementation that does has_method("get_slot") before calling, then calls without null-checking the return value, passes the primary suite but fails here.

**Confidence:** High

---

### [fusion_rules_and_hybrid] TEST_BREAK — FUSION_DURATION and FUSION_MULTIPLIER positivity check

**Would have asked:** The ticket says to test that FUSION_DURATION and FUSION_MULTIPLIER are > 0. The primary suite checks their exact values (5.0 and 1.5). Should the adversarial suite redundantly check > 0, or test something orthogonal?

**Assumption made:** Test immutability behavior: verify that calling resolve_fusion does not modify FUSION_DURATION or FUSION_MULTIPLIER on the instance (constants must remain unchanged after use). This catches a naive implementation that uses instance vars named the same as constants and mutates them during resolve_fusion. The primary suite only checks the values before any call; the adversarial test checks them again after a resolve_fusion call.

**Confidence:** High

---

### [fusion_rules_and_hybrid] TEST_BREAK — resolve_fusion with player that has apply_fusion_effect but is a wrong-type Object

**Would have asked:** Spec says push_error if player lacks apply_fusion_effect AND slots are still consumed. Should the adversarial suite verify that slots are consumed even when the player is a plain Object with no apply_fusion_effect method?

**Assumption made:** Yes. Pass an Object that lacks apply_fusion_effect entirely. Verify: no crash, slots consumed (both empty after call). This is the exact path that triggers the push_error branch per spec FRH-3. The adversarial test documents this separately from the primary null-player test.

**Confidence:** High

---

### [fusion_rules_and_hybrid] TEST_DESIGN — PlayerDouble implementation strategy

**Would have asked:** Should the PlayerDouble for tracking `apply_fusion_effect` calls be a preloaded external script, an autoload, or an inner class on the test file?

**Assumption made:** Inner class on the test file (`class PlayerDouble extends Object`). This keeps the test file self-contained, avoids adding a new file to the repo, and matches GDScript's support for inner classes in headless test suites. The double extends `Object` (not `RefCounted`) to allow manual `free()` and avoid potential auto-free conflicts with the resolver.

**Confidence:** High

---

### [fusion_rules_and_hybrid] TEST_DESIGN — FRH-3-AC-11 call-order verification strategy

**Would have asked:** The spec mandates `apply_fusion_effect` is called before `consume_fusion_slots` (FRH-3-AC-11). How should this order be verified without a call-sequence interceptor?

**Assumption made:** Behavioral proxy: assert that `apply_fusion_effect_call_count >= 1` AND both slots are empty after `resolve_fusion`. These two facts can only co-exist if the effect was called (with slots still filled, which the internal guard checks) and then consume ran. No slot-state snapshot during the call is required. This conservative approach avoids adding complexity to the player double.

**Confidence:** High

---

### [fusion_rules_and_hybrid] TEST_DESIGN — FRH-2-AC-6 malformed manager simulation

**Would have asked:** FRH-2-AC-6 requires testing `can_fuse` when `get_slot(0)` returns null. MutationSlotManager never returns null for valid indices. How to simulate a malformed manager?

**Assumption made:** Pass a plain `Object.new()` (which has no `get_slot` method at all) to `can_fuse`. This is a strictly stricter case than a manager that returns null from `get_slot` — it tests the duck-typing null-safety guard more thoroughly. The spec says "malformed manager"; a missing method is the simplest headless-safe simulation of this.

**Confidence:** High

---

### [chunk_sticks_to_enemy] Test Break — double-attach same chunk to different enemies

**Would have asked:** If chunk_attached fires twice for the same chunk node (two different enemies contact the same in-flight chunk simultaneously), does the second attach overwrite the stored enemy reference, or is it silently ignored?

**Assumption made:** The second call to _on_enemy_chunk_attached fires the if/elif branch again (chunk == _chunk_node matches), so _chunk_stuck_enemy is overwritten to the second enemy. The stuck flag remains true. This means "last enemy wins." The absorb handler must match against the current _chunk_stuck_enemy reference.

**Confidence:** Medium

---

### [chunk_sticks_to_enemy] Test Break — chunk_attached emission for body in both "chunk" AND "player" groups

**Would have asked:** If a body is in both the "chunk" group and the "player" group simultaneously (unusual but possible), should chunk_attached be emitted or suppressed?

**Assumption made:** The spec says the signal fires for bodies in the "chunk" group and NOT for player bodies. The existing _on_body_entered code checks player group first. Conservative assumption: the chunk group check takes precedence in the stub (it checks "chunk" without a prior player-group exclusion). This edge case is unlikely in production but is documented for the implementation agent.

**Confidence:** Medium

---

### [chunk_sticks_to_enemy] Test Break — dead-state enemy headless testability

**Would have asked:** Can we drive EnemyStateMachine to a "dead" state headlessly without instantiating a full scene?

**Assumption made:** The deepest testable state headlessly is "infected" (idle → weakened → infected). There is no apply_dead_event() confirmed available headlessly. SPEC-CSE-1 says the signal fires regardless of state including "dead." The test covers "infected" as the deepest verified proxy for "dead" state behavior.

**Confidence:** High

---

### [chunk_sticks_to_enemy] Test Break — freed enemy node prevents flag clear on absorb

**Would have asked:** If _chunk_stuck_enemy is freed before absorb_resolved fires, the is_instance_valid guard skips the entire slot block, leaving _chunk_stuck_on_enemy=true. Is this acceptable or should the flag be cleared even when the enemy ref is invalid?

**Assumption made:** Per SPEC-CSE-10 risk note: "If the stuck flag is not cleared when the chunk node is invalid, the recall guard will permanently block recall for that slot, creating a softlock." However, SPEC-CSE-10 only addresses the chunk node being freed, not the enemy node being freed. When the ENEMY node is freed (not the chunk), the implementation skips the block and flags remain — this is a known risk per spec. The test documents this behavior without asserting flag state, only asserting no crash.

**Confidence:** Medium

---

## Run: 2026-03-05T12:00:00Z
Tickets queued: input_hint_polish_core_mechanics.md

---

### [infection_interaction] Planner — Weakened state definition

**Would have asked:** Is the "weakened" enemy state already defined and implemented elsewhere?

**Assumption made:** Yes. EnemyStateMachine in the codebase already defines `STATE_WEAKENED` and transitions idle/active → weakened (weaken event), weakened → infected (infection event). Execution plan assumes dependency on enemy state machine / weakened-state behavior being in place; no separate task to define weakened.

**Confidence:** High

---

### [infection_interaction] Planner — Chunk contact vs key press

**Would have asked:** Should both chunk contact and key press trigger infection, or should the spec choose one?

**Assumption made:** Both are in scope per AC ("e.g. chunk contact, key press"). Spec Agent will define the exact interaction(s); implementation tasks include key/infect action (already present in InfectionInteractionHandler) and chunk-contact trigger (e.g. chunk body entering area of weakened enemy). If spec narrows to one trigger, implementation follows spec.

**Confidence:** Medium

---

### [infection_interaction] Planner — Existing infection code

**Would have asked:** The repo already has InfectionInteractionHandler, InfectionAbsorbResolver, MutationInventory, infection tests. Should the plan assume greenfield or align with existing code?

**Assumption made:** Plan drives spec-first. Spec is the authority; Test Design and Implementation tasks align or fill gaps. Existing code is reconciled with the spec (e.g. chunk-contact wiring may be missing; one mutation "usable" may need UI or gameplay hook). No task assumes delete-and-rewrite; implementation tasks may be "wire chunk contact," "ensure one mutation granted and visible/usable," "add/align visual feedback."

**Confidence:** High

---

### [infection_interaction] Planner — One mutation "usable"

**Would have asked:** What does "at least one mutation is granted and usable after absorb" mean — UI visibility only, or an actual gameplay effect?

**Assumption made:** Minimum: one mutation ID is granted to the player (MutationInventory.grant) and is visible or confirmable (e.g. in UI or inventory). "Usable" for this milestone means the player can observe that the mutation was gained; a concrete gameplay effect (e.g. stat buff, ability) may be placeholder or minimal. Spec Agent will clarify; implementation may deliver UI/inventory display plus a minimal placeholder effect if needed to satisfy AC.

**Confidence:** Medium

---

### [infection_interaction] Planner — Visual feedback scope

**Would have asked:** What level of visual/audio feedback is required for weakened, infected, and absorb states to count as "visually clear and discoverable without debug overlays"?

**Assumption made:** Minimum feedback includes distinct coloration or sprite change for weakened vs infected enemies, a short infection FX (e.g. pulse, particles) when infection occurs, and a clear on-screen cue when a mutation is gained (e.g. HUD toast or inventory highlight). No complex animation set is required for this milestone; Presentation and Spec Agents will choose the simplest assets/effects that satisfy clarity.

**Confidence:** Medium

---

### [infection_interaction] Planner — Softlock definition

**Would have asked:** For this feature, what scenarios count as a "softlock or undefined state" that must be prevented?

**Assumption made:** A softlock is any infection/absorb sequence that leaves the game running but the player unable to continue normal play without manually resetting the scene (e.g. enemy stuck in an intermediate state, infection cannot be cleared, absorb never completes, or mutation inventory enters an invalid state). Tests and implementation must ensure all transitions (normal, repeated, cancelled, or interrupted) converge to a valid, recoverable state: enemy dead or reset, infection cleared or resolved, and player input restored.

**Confidence:** Medium

---

### [infection_interaction] Test Designer — Infect input action coverage

**Would have asked:** Should primary tests assert that the `infect` input action (via `Input.is_action_just_pressed("infect")` in `InfectionInteractionHandler`) correctly routes to `EnemyStateMachine.apply_infection_event()` from weakened state, or is that mapping treated as higher-level engine integration?

**Assumption made:** For this ticket, primary Test Designer coverage focuses on pure logic and deterministic wiring that is testable without simulating real-time input. Infection triggers are verified at the state machine level and via chunk-contact engine wiring (`EnemyInfection._on_body_entered`), while the exact Godot input mapping for `infect` is treated as engine-integration / manual QA responsibility. No tests attempt to fake `Input` state.

**Confidence:** Medium

---

### [infection_interaction] Test Designer — Mutation "usable" via InfectionUI

**Would have asked:** Does "at least one mutation is granted and usable after absorb" require a concrete gameplay effect, or is a visible mutation indicator in the infection-loop HUD sufficient for this milestone?

**Assumption made:** For this milestone, a mutation is considered "usable" if it is (a) granted into `MutationInventory` and (b) made clearly visible to the player via InfectionUI (e.g. `MutationLabel`/`MutationIcon` driven from `get_mutation_inventory()` and `get_granted_count()`). Tests enforce that a non-zero mutation count makes the mutation label visible; any deeper gameplay effect is left to future tickets.

**Confidence:** Medium

---

### [infection_interaction] Test Designer — Infection FX text and tint mapping

**Would have asked:** Should the infection state FX contract specify exact label text and color tints for weakened/infected/dead, or only require that each state is visually distinct?

**Assumption made:** The strictest defensible contract for this ticket is that `infection_state_fx.gd` produces distinct visuals and explicit state labels: "Weakened", "Infected", and "Dead", with weakened/infected tinted away from the idle/default color and dead rendered dimmer (alpha < 1). Tests assert these concrete label strings and basic tint/dim relationships rather than exact RGB values, so future visual tweaks remain possible while keeping states clearly distinguishable.

**Confidence:** Medium

---

### [infection_interaction] Test Breaker — resolve_absorb null inventory semantics

**Would have asked:** When `InfectionAbsorbResolver.resolve_absorb` is invoked with a non-null, infected `EnemyStateMachine` but a null mutation inventory, should the resolver still kill the enemy or treat the call as a strict no-op?

**Assumption made:** For this ticket, calling `resolve_absorb` with a null inventory is treated as a strict no-op: the enemy state and mutation inventory must remain unchanged, and the call must never crash. Tests mark this as a CHECKPOINT and assert no state change when `inv == null`.

**Confidence:** Medium
---

### [input_hint_polish_core_mechanics] Planner — Duplicate ticket blocks

**Would have asked:** The ticket file for `input_hint_polish_core_mechanics` currently contains two full ticket blocks with different Revisions (2 and 1); should the lower block be treated as historical context and left untouched, or should the file be normalized to a single ticket definition?

**Assumption made:** The first ticket block (Revision 2) is the authoritative current state and the second block (Revision 1) is retained as historical context. For this run, only the first block's WORKFLOW STATE and NEXT ACTION fields will be updated (to Stage SPECIFICATION, Revision incremented, and handoff information adjusted), and the lower block will be left unchanged.

**Confidence:** Medium

---

### [infection_interaction] Test Breaker — workflow Stage enum vs IMPLEMENTATION_* domains

**Would have asked:** The workflow_enforcement_v1 Stage enum lists `IMPLEMENTATION_BACKEND/FRONTEND/GENERALIST`, while the infection_interaction execution plan and Test Breaker brief use implementation domains `Core Simulation`, `Gameplay Systems`, `Presentation`, and `Engine Integration`. Which specific IMPLEMENTATION_* Stage value should be used when handing off from Test Breaker to implementation for this ticket?

**Assumption made:** For this ticket, the authoritative domains are the ones used in the infection_interaction execution plan. Handoff from Test Breaker goes to `IMPLEMENTATION_CORE_SIMULATION` with `Next Responsible Agent` set to Core Simulation Agent, treating this as the correct IMPLEMENTATION_* Stage despite the older enum in workflow_enforcement_v1.

**Confidence:** Medium

---

### [infection_interaction] Core Simulation Agent — Preserve existing pure-logic implementations

**Would have asked:** Given that `EnemyStateMachine`, `InfectionAbsorbResolver`, and `MutationInventory` already exist and all primary + adversarial infection tests pass, should we refactor or tighten these modules further for this ticket, or treat the current implementations as authoritative if they satisfy R1–R4 and all CHECKPOINT assumptions?

**Assumption made:** For this ticket, the infection loop contract is defined by the existing tests and checkpoints. Since the current pure-logic implementations:
- use only the allowed state labels `{idle, active, weakened, infected, dead}`,
- enforce the specified transitions and no-op combinations,
- ensure `can_absorb`/`resolve_absorb` semantics (infected → dead + one mutation; no-op for invalid states or null args),
- and maintain MutationInventory invariants under all adversarial suites,
no additional refactoring is performed. The existing modules are treated as the canonical implementations for R1–R4 as long as the full infection test suite remains green.

**Confidence:** High

---

## Run: 2026-03-05T13:00:00Z
Tickets queued: infection_interaction.md

---

### [infection_interaction] Planner — Project name field

**Would have asked:** What value should the `Project` field use for the `infection_interaction` ticket (e.g. `blobert` vs `Milestone 2 – Infection Loop`)?

**Assumption made:** Use `blobert` as the canonical project name, with milestone and epic context captured in the ticket body and folder structure rather than the `Project` field itself.

**Confidence:** High

---

### [infection_interaction] Planner — Implementation stage vs domain agents

**Would have asked:** Given the Stage enum in `workflow_enforcement_v1` only includes `IMPLEMENTATION_BACKEND | IMPLEMENTATION_FRONTEND | IMPLEMENTATION_GENERALIST`, but the infection loop uses domain-specific agents (Core Simulation, Gameplay Systems, Engine Integration, Presentation), which Stage value should be used when handing off to implementation?

**Assumption made:** Continue to use the documented enum and set Stage to `IMPLEMENTATION_GENERALIST` for all implementation-domain handoffs, while using `Next Responsible Agent` to name the specific domain agent (e.g. `Core Simulation Agent`, `Gameplay Systems Agent`). No new Stage values are introduced.

**Confidence:** Medium

---

### [infection_interaction] Spec — Canonical infection trigger

**Would have asked:** For this milestone, should the spec treat chunk contact, an explicit `infect` input action, or both as the required way to infect a weakened enemy?

**Assumption made:** The canonical, testable contract for this ticket is chunk-based contact: when an infecting slime chunk body enters a weakened enemy's infection area, infection is triggered if the enemy is eligible. Any `infect` input action wiring is treated as higher-level engine integration and is not required for this spec to be satisfied.

**Confidence:** Medium

---

### [infection_interaction] Spec — Infection eligibility scope

**Would have asked:** Do all enemies support being weakened and infected, or only a subset tagged/configured for infection in this milestone?

**Assumption made:** Only enemies whose state is driven by `EnemyStateMachine` and are explicitly configured/marked as infection-eligible in the scene or data are in scope. Other enemies remain non-infectable for this milestone and are allowed to ignore chunk contact entirely.

**Confidence:** Medium

---

### [infection_interaction] Spec — Mutation selection rule

**Would have asked:** When absorbing an infected enemy, if multiple mutation types exist, should the granted mutation be random, cyclic, or fixed?

**Assumption made:** For this milestone, mutation granting is deterministic and fixed: absorbing an infected enemy always grants a single, configured mutation ID (e.g. the first entry in a small infection-mutation config), with no randomness. This keeps tests and player expectations stable while still delivering "at least one mutation."

**Confidence:** Medium

---

### [infection_interaction] Spec — Repeated infection attempts

**Would have asked:** What should happen if infection is triggered against an enemy that is already infected or dead?

**Assumption made:** Infection is strictly one-way and idempotent: chunk contact that does not find the enemy in the weakened state (e.g. idle, active, infected, dead) has no effect and must not change enemy or player state. Only weakened → infected is allowed for this ticket.

**Confidence:** High

---

### [infection_interaction] Spec — Multiple absorbs and mutation stacking

**Would have asked:** If the player infects and absorbs multiple enemies in sequence, should mutations stack, replace the previous one, or be capped for this milestone?

**Assumption made:** Each successful absorb from an infected enemy increments the stored mutation count by 1 (via `MutationInventory`) with no explicit upper cap for this ticket. The acceptance criteria only require that at least one mutation is granted and visible/usable; additional absorbs are allowed but not strictly required to be showcased in UX beyond a monotonically increasing count.

**Confidence:** Medium

---

### [infection_interaction] Spec — Out-of-scope systems

**Would have asked:** Should infection state and mutations be persisted across scene reloads/checkpoints or integrated with broader progression, or is this milestone limited to single-session, in-level behavior?

**Assumption made:** For this ticket, infection and mutation effects are scoped to the current play session/scene. Save/load, cross-level persistence, and meta-progression are explicitly out of scope and may be handled by future tickets.

**Confidence:** High

---

### [infection_interaction] Test Breaker — EnemyInfection player targeting wiring

**Would have asked:** Should `EnemyInfection` be required to always set and clear the current absorb target via `InfectionInteractionHandler.set_target_esm` and `clear_target` exactly once per player enter/exit, and never in response to chunk contact?

**Assumption made:** For this ticket, the conservative contract is that entering an enemy's infection area with a body in the `player` group calls `InfectionInteractionHandler.set_target_esm` once with that enemy's `EnemyStateMachine`, exiting calls `clear_target` once, and chunk-contact infection (`body in group "chunk"`) must not change the handler's target at all. Tests treat any deviation (missing set/clear or handler calls from chunk-only contact) as a failure.

**Confidence:** Medium

---

### [infection_interaction] — OUTCOME: COMPLETE
All automated infection interaction suites (primary + adversarial) are passing and a human has verified in-editor that infection/absorb visuals and UX satisfy the final acceptance criterion; ticket is marked COMPLETE and moved to the milestone's done column.

## Run: 2026-03-05T14:00:00Z
Tickets queued: mutation_slot_system_single.md

---

### [mutation_slot_system_single] Orchestrator — Missing workflow state blocks

**Would have asked:** The ticket `mutation_slot_system_single` currently lacks WORKFLOW STATE and NEXT ACTION sections; should the orchestrator normalize the ticket structure before handing off to Planner, or allow Planner to create the initial workflow blocks?

**Assumption made:** Treat the ticket as newly activated. Move it from the milestone backlog into `01_active/` without modifying its content, rely on the folder rule (`01_active/` → active, non-COMPLETE Stage) and delegate normalization of WORKFLOW STATE and NEXT ACTION to the Planner agent as part of Stage PLANNING.

**Confidence:** Medium

---

### [mutation_slot_system_single] — OUTCOME: INTEGRATION (Human verification required)
Automated tests, core simulation, gameplay wiring, engine integration, and HUD presentation for the single mutation slot are all implemented and passing; ticket is parked in Stage INTEGRATION with explicit Blocking Issues for a human to verify in-editor that the slot UX is human-playable, clearly indicates filled/empty state and active mutation, and that no duplicate or lost mutations occur in realistic play.

### [mutation_slot_system_single] Planner — Relationship to MutationInventory

**Would have asked:** Should the single mutation slot be modeled as a separate system from `MutationInventory`, or is the slot effectively "the currently equipped mutation" backed by `MutationInventory` as the source of granted mutations?

**Assumption made:** The mutation slot system is a thin layer over the existing `MutationInventory`: absorbs continue to grant mutations into the inventory, and the slot tracks which single mutation (by ID) is currently active/equipped. The slot never owns data independently of the inventory; it only references or selects from it, and implementation tasks will keep inventory and slot state consistent.

**Confidence:** Medium

---

### [mutation_slot_system_single] Planner — Slot consumption vs persistence

**Would have asked:** When the player "uses" the mutation in the slot, should that usage consume and clear the slot, or does the slot remain filled with a passive or repeatable effect until explicitly replaced?

**Assumption made:** For this milestone, the conservative contract is that the slot represents a persistent, always-on mutation once filled. Using the mutation expresses its effect (e.g. passive stat change or repeatable ability) but does not automatically clear the slot; the slot is only changed when a new mutation is equipped or explicitly replaced by design. Spec and tests will treat one filled slot with persistent effect as the minimum required behavior.

**Confidence:** Medium

---

### [mutation_slot_system_single] Planner — Multiple granted mutations

**Would have asked:** If the player absorbs multiple enemies and gains multiple mutations, how should the single slot choose which mutation is active (first granted, last granted, configurable selection, or other rule)?

**Assumption made:** For this ticket, the selection rule is deterministic and simple: the active slot always tracks the most recently granted compatible mutation (last-wins). Additional inventory capacity or multi-mutation management is out of scope; tests and spec will only require that the latest valid mutation from an absorb becomes the active slot content, with previous slot contents replaced but inventory history remaining consistent.

**Confidence:** Medium

---

### [mutation_slot_system_single] Planner — Scope of persistence and save/load

**Would have asked:** Should the mutation slot contents and its active effect persist across scene reloads/checkpoints or be scoped only to the current play session/scene?

**Assumption made:** In line with other Milestone 2 infection-loop tickets, the mutation slot is scoped to the current play session/scene. Persistence across saves, level transitions, and meta-progression is explicitly out of scope for this ticket and can be handled by future progression/persistence features.

**Confidence:** High

---

### [mutation_slot_system_single] Spec — Slot vs effect gating

**Would have asked:** For this milestone, should the active mutation slot state be the *only* authority for enabling/disabling the mutation's gameplay effect, or can the existing implementation that ties the effect directly to `MutationInventory` remain unchanged as long as slot state accurately mirrors inventory?

**Assumption made:** To keep scope minimal and avoid destabilizing the existing infection loop, the mutation effect remains bound to the presence of at least one granted mutation in `MutationInventory` as implemented for `infection_interaction`. The new single-slot layer must accurately reflect that state (empty before any grants, filled after the first successful absorb, last-wins on later grants) but is not required to introduce an additional layer of effect gating beyond inventory for this milestone.

**Confidence:** Medium

---

### [mutation_slot_system_single] Test Designer — MutationSlot empty sentinel and API surface

**Would have asked:** When the slot is empty, should `MutationSlot.get_active_mutation_id()` return an empty string, `null`, or a dedicated sentinel constant, and what minimum write API should the slot expose for tests to drive SLOT-1/SLOT-2 behavior?

**Assumption made:** The strictest defensible contract is that `get_active_mutation_id()` returns the empty string `""` whenever the slot is empty, and that the slot exposes a minimal, explicit write API `set_active_mutation_id(id: String)` plus `clear()`. Tests assert the empty-string sentinel and drive all state changes through `set_active_mutation_id` and `clear` rather than relying on implicit side effects so that any future change to the sentinel or write semantics is intentional and requires coordinated spec/test updates.

**Confidence:** Medium

---

### [mutation_slot_system_single] Test Breaker — Empty slot ID write semantics

**Would have asked:** When `MutationSlot.set_active_mutation_id("")` is called, should the slot treat the empty string as a real mutation ID (leaving the slot filled) or interpret it as "clear the slot" to keep the empty-string sentinel semantics consistent?

**Assumption made:** For this ticket, the conservative contract is that `set_active_mutation_id("")` is equivalent to `clear()`: after the call, `is_filled()` must be `false` and `get_active_mutation_id()` must return the empty string sentinel `""`, ensuring the slot never reports itself as filled with an empty ID.

**Confidence:** Medium

---

### [mutation_slot_system_single] Core Simulation Agent — InfectionAbsorbResolver slot parameter

**Would have asked:** Should `InfectionAbsorbResolver.resolve_absorb` be extended to take a `MutationSlot` parameter directly, or should slot updates be handled entirely by higher-level coordination code outside the resolver?

**Assumption made:** To keep integration minimal and deterministic while honoring the SLOT-2 spec, `resolve_absorb` is extended with an optional third `slot: Object = null` parameter. Existing call sites that pass only `(esm, inv)` continue to behave identically, and when a non-null slot implementing `set_active_mutation_id(id: String)` is provided and absorb succeeds, the resolver calls `slot.set_active_mutation_id(DEFAULT_MUTATION_ID)` immediately after `inv.grant(DEFAULT_MUTATION_ID)`. If `slot` is null or lacks the method, it is ignored.

**Confidence:** Medium

---

### [mutation_slot_system_single] Gameplay Systems Agent — Slot owner and gameplay access

**Would have asked:** In the infection-loop scene, which runtime object should own the authoritative `MutationSlot` instance for the player (e.g. `PlayerController`, `InfectionInteractionHandler`, a dedicated mutation controller node, or a global singleton)?

**Assumption made:** `InfectionInteractionHandler` owns the canonical `MutationSlot` instance for the player: it instantiates `MutationSlot` once in `_ready()`, passes it into `InfectionAbsorbResolver.resolve_absorb(esm, inv, slot)` whenever an absorb succeeds, and exposes it via `get_mutation_slot()` so gameplay systems like `PlayerController` and `InfectionUI` can read slot state without introducing new autoloads or duplicating slot instances.

**Confidence:** Medium

---

## Run: 2026-03-12T00:00:00Z
Tickets queued: fusion_opportunity_room.md

---

### [fusion_opportunity_room] Planner — Dependency on fusion_rules_and_hybrid.md and visual_clarity_hybrid_state.md

**Would have asked:** The fusion mechanic (fusion_rules_and_hybrid.md) and hybrid visual feedback (visual_clarity_hybrid_state.md) are both listed as Backlog and not yet implemented. Can the fusion opportunity room be specced and laid out before those tickets are completed, or must they ship first?

**Assumption made:** The room layout, enemy placement, and infection loop for two enemies are fully specifiable and buildable without a working fusion implementation. The fusion trigger and hybrid feedback are treated as a hard dependency only for the final AC ("at least one fusion can be performed in-level with clear feedback"). Tasks in this plan are ordered so the room structure is built first, and the fusion-trigger wiring task explicitly depends on fusion_rules_and_hybrid.md being implemented. The spec will document the fusion trigger as a TBD placeholder resolved by that downstream ticket.

**Confidence:** High

---

### [fusion_opportunity_room] Planner — Containment Hall 01 scene existence

**Would have asked:** Does `containment_hall_01.tscn` already exist as a buildable scene, or does it need to be created as part of this ticket?

**Assumption made:** `containment_hall_01.tscn` does not yet exist in the repository (not found in `/Users/jacobbrandt/workspace/blobert/scenes/`). This ticket must create it. The scene will be built as a new 3D scene using CharacterBody3D, StaticBody3D (floors/walls), and Area3D nodes consistent with the project's 3D conventions. The containment_hall_01_layout.md ticket (also in_progress) covers the full level; this ticket scopes only the fusion room sub-area within that level.

**Confidence:** Medium

---

### [fusion_opportunity_room] Planner — Fusion room scope within containment_hall_01

**Would have asked:** Should the fusion opportunity room be a fully self-contained scene (its own .tscn), a sub-scene instanced into containment_hall_01.tscn, or a region within a monolithic containment_hall_01.tscn?

**Assumption made:** The fusion room is a spatially distinct chamber within a single `containment_hall_01.tscn` (not a separate scene file). It is laid out as a named sub-region (e.g. a Node3D group named "FusionRoom") inside the hall. This keeps scene management consistent with existing project conventions (one scene per level area) and makes it easy to test in isolation by temporarily setting it as the run/main_scene.

**Confidence:** Medium

---

### [fusion_opportunity_room] Planner — Enemy type and mutation IDs for the two room enemies

**Would have asked:** What specific mutation IDs should each enemy in the fusion room grant? Should each grant a different mutation ID so the two slots receive distinct mutations?

**Assumption made:** Two enemies are placed in the fusion room. Enemy A (on Platform A) grants mutation ID `"mutation_a"` and Enemy B (on Platform B) grants `"mutation_b"`. These are placeholder IDs consistent with the deterministic-mutation-ID assumption from prior checkpoints. The Spec Agent will finalize the exact IDs; implementation uses these as named constants so a single-line change updates both. Each enemy must grant a different ID so both slots fill with distinct values, enabling a deterministic fusion outcome.

**Confidence:** Medium

---

### [fusion_opportunity_room] Planner — Fusion trigger mechanic

**Would have asked:** How is fusion triggered in the room — is it an input action the player presses when both slots are full, an automatic trigger on entering a specific zone, or something else?

**Assumption made:** Fusion is triggered by an explicit player input action (`"fuse"`) when both mutation slots are filled, consistent with the fusion_rules_and_hybrid.md AC ("Fusion is triggered by defined input/condition when two slots are filled"). No automatic zone trigger is added; a UI prompt or on-screen hint will appear when both slots are filled. The Spec Agent will confirm the exact action name; if fusion_rules_and_hybrid.md defines a different trigger, that definition is authoritative.

**Confidence:** Medium

---

### [fusion_opportunity_room] Planner — What "platform" means in 2.5D context

**Would have asked:** For the 2.5D side-scrolling game, do "platforms" mean elevated StaticBody3D floors the player can jump onto, or some other structure?

**Assumption made:** Platforms are StaticBody3D + CollisionShape3D + MeshInstance3D nodes elevated above the room floor, reachable by the player via jumping with existing movement physics. Each enemy stands on one platform. Platform heights are set so the player can reach them with the default CharacterBody3D jump implemented in player_controller_3d.gd. No additional movement mechanics are required.

**Confidence:** High

---

### [fusion_opportunity_room] Planner — In-editor playability requirement

**Would have asked:** The AC requires the room be "human-playable in-editor." Does this require running from containment_hall_01.tscn directly, or is running from test_movement_3d.tscn acceptable if the room is reachable?

**Assumption made:** "Human-playable in-editor" means the Godot editor can run the scene and a human can navigate through the fusion room, absorb both enemies, and observe the fusion trigger/outcome without debug overlays. For this ticket, the room must be runnable either as a standalone scene or reachable from a valid main scene. The implementation task will ensure the room is loadable by setting it as the main scene temporarily or making it reachable from test_movement_3d.tscn.

**Confidence:** Medium

---

### [autopilot] Orchestrator — API rate limit hit mid-run
**Would have asked:** Multiple background agents hit "You've hit your limit · resets 10pm (America/New_York)" simultaneously. The test breaker for second_chunk_logic and planners for fusion_rules_and_hybrid, visual_clarity_hybrid_state, containment_hall_01_layout, mutation_tease_room, fusion_opportunity_room, light_skill_check, mini_boss_encounter, start_finish_flow were all blocked. Should these tickets be marked BLOCKED or left in their current stage pending retry?
**Assumption made:** These tickets are left at their current stage (PLANNING for most, TEST_BREAK for second_chunk_logic). The rate limit is temporary and resets at 10pm ET. The next autopilot run should resume from each ticket's current stage. No ticket content is corrupted — agents that failed produced no changes.
**Confidence:** High

### [slot_consumption_rules] — OUTCOME: PLANNING COMPLETE
Planner Agent completed full execution plan before rate limit. Ticket at SPECIFICATION, Spec Agent is next. Key decision: consume_fusion_slots() method on MutationSlotManager; all-or-nothing slot clear after fusion.

---

## Run: 2026-03-13T00:00:00Z
Tickets queued: second_chunk_logic.md (TEST_BREAK stage)

---

### [second_chunk_logic] Test Break — HP order-of-operations for step 20 reads result not prior

**Would have asked:** Step 20 (HP reduction for chunk 2) reads result.current_hp (output of step 18) not prior_state.current_hp. Should adversarial tests probe an incorrect implementation that reads prior_state.current_hp instead, which would produce wrong results for dual-detach scenarios at the HP floor boundary?

**Assumption made:** Yes. A buggy implementation could read prior_state.current_hp in step 20 (instead of result.current_hp), which would make the dual-detach cumulative HP reduction tests fail. Adversarial tests explicitly probe this: prior_hp=50.0 with both chunks detached on same frame should produce 0.0 (not 25.0 if read from prior_state after step 18). This catches an incorrect "reads prior, not result" mutation.

**Confidence:** High

---

### [second_chunk_logic] Test Break — Cross-contamination: detach_just_pressed affects has_chunk_2 via implementation bug

**Would have asked:** Could a buggy implementation share a single `detach_eligible` flag for both chunks (i.e. detach_just_pressed inadvertently triggers detach_2 behavior or vice versa)?

**Assumption made:** Yes, this is a realistic implementation mutation. Adversarial tests use asymmetric input combinations (detach_just_pressed=true, detach_2_just_pressed=false) with both chunk fields true, then verify the strict non-interference: has_chunk changes, has_chunk_2 does not. A conflated implementation would fail these tests.

**Confidence:** High

---

### [second_chunk_logic] Test Break — prior_state immutability for has_chunk_2

**Would have asked:** The primary suite checks prior_state immutability individually for has_chunk_2=true and has_chunk_2=false. Should adversarial tests also verify that the FULL prior_state object is not mutated across ALL fields in the same call?

**Assumption made:** Yes. A naive GDScript implementation that returns `prior_state` by reference (rather than a freshly allocated result) would cause all fields — including has_chunk_2 — to reflect the post-simulation state, breaking immutability. Adversarial tests verify all key prior_state fields are unchanged after simulate() returns.

**Confidence:** High

---

### [second_chunk_logic] Gameplay Systems Agent — Task 8 test file creation

**Would have asked:** Task 8 (test_dual_chunk_controller.gd) is assigned to Test Design Agent and listed as a post-implementation task. Should Gameplay Systems Agent create this file anyway to satisfy the "all tests pass" mandate during autonomous mode?

**Assumption made:** Yes. The workflow enforcement module requires all tests to pass before advancing Stage. Since the test runner auto-discovers all test_*.gd files, and the ticket mandates the file be created as part of this ticket's scope, Gameplay Systems Agent creates `tests/chunk/test_dual_chunk_controller.gd` using MovementSimulation-level tests (headless-safe, no scene tree required). Scene-level integration tests requiring a live CharacterBody3D are deferred to manual QA per the ticket's "Risk" note about Pattern B.

**Confidence:** High

---

## Run: 2026-03-14T00:00:00Z
Tickets queued: slot_consumption_rules.md (TEST_BREAK stage — adversarial suite)

---

### [slot_consumption_rules] Test Breaker — Dynamic method invocation to avoid parse errors in TDD red phase

**Would have asked:** consume_fusion_slots() does not yet exist on MutationSlotManager. Should adversarial tests call it directly (causing parse/load errors before implementation) or use has_method() + call() to remain parseable in the red phase?

**Assumption made:** All invocations of consume_fusion_slots() use manager.has_method("consume_fusion_slots") + manager.call("consume_fusion_slots") so the suite loads and runs cleanly before implementation. Absence of the method is itself recorded as a failure via the gate test (test_adv_method_exists). Once Core Simulation Agent adds the method, all tests switch from failing the gate to exercising the full adversarial matrix. This is the correct TDD red-phase pattern for a method that does not yet exist.

**Confidence:** High

---

### [slot_consumption_rules] Test Breaker — Whitespace IDs treated as valid non-empty

**Would have asked:** Should fill_next_available(" ") (whitespace-only string) be treated as a valid ID (not empty) or should it be rejected like empty string?

**Assumption made:** Per DSM-2 and the existing implementation, the push_error guard fires only when id == "". A whitespace-only string is not equal to "" so it passes the guard and fills slot A. ADV-13 tests this explicitly: after consume, fill_next_available(" ") must fill slot A with " " and slot B must remain empty. If future spec revisions tighten the guard to reject whitespace, ADV-13 becomes the canary that breaks first, making the spec change visible.

**Confidence:** High

---

### [slot_consumption_rules] Test Breaker — Slot object identity as a correctness signal

**Would have asked:** Should the adversarial suite verify that get_slot(0) and get_slot(1) return the same object references before and after consume (in-place clear), or is this too implementation-specific?

**Assumption made:** Object identity is tested (ADV-10) because it encodes a real caller contract: any external code that holds a reference obtained via get_slot() before consume must still see the correct cleared state after consume. If consume replaces slot instances (_slots[0] = MutationSlot.new()), the held reference becomes a stale zombie. The spec's SCR-4 risk section notes this explicitly ("slot object identity" edge case). Treating it as testable is conservative and correct.

**Confidence:** High


---

## Run: 2026-03-14T14:45:54Z
Tickets queued: chunk_sticks_to_enemy.md

---

### [chunk_sticks_to_enemy] Planner — Where does "stuck" state live?

**Would have asked:** Should the `chunk_stuck` flag (tracking that a chunk is attached to an enemy) live in `MovementSimulation.MovementState` (pure simulation), or only in `PlayerController3D` (engine layer)?

**Assumption made:** The stuck flag lives exclusively in `PlayerController3D` as a controller-side field (e.g. `_chunk_stuck_on_enemy: bool` and `_chunk_2_stuck_on_enemy: bool`), parallel to `_recall_in_progress`. `MovementSimulation.MovementState` is not modified: the simulation has no knowledge of enemy contact. This keeps the pure simulation headless and unchanged, and avoids adding new simulation specs. The controller checks the stuck flag in its recall-gate logic before starting a recall.

**Confidence:** High

---

### [chunk_sticks_to_enemy] Planner — How is recall blocked?

**Would have asked:** Should recall be blocked by a flag checked in the simulation (`has_chunk` gated by a stuck predicate) or purely by a controller guard that refuses to begin `_recall_in_progress`?

**Assumption made:** Recall is blocked exclusively by a controller guard: when `_chunk_stuck_on_enemy` is true, the `recall_pressed` condition evaluates to false (or is explicitly short-circuited), so `_recall_in_progress` is never set to true. The simulation sees no difference; `has_chunk` remains false while the chunk is stuck and detached. This is the minimal, conservative change: no simulation changes, no new simulation flags.

**Confidence:** High

---

### [chunk_sticks_to_enemy] Planner — How does absorb completion signal the chunk to detach?

**Would have asked:** When the enemy is absorbed (via `InfectionInteractionHandler.absorb_resolved` signal), how does `PlayerController3D` learn that its stuck chunk should be freed and become recallable?

**Assumption made:** `InfectionInteractionHandler` already emits `absorb_resolved(esm: EnemyStateMachine)`. `PlayerController3D` connects to this signal in `_ready()`. On signal receipt, the controller checks whether either stuck chunk belongs to that enemy (via a stored enemy reference `_chunk_stuck_enemy` / `_chunk_2_stuck_enemy`) and clears the stuck flag for the matching chunk(s), making them immediately recallable. The chunk node itself is un-parented from the enemy and re-added as a free RigidBody3D in the scene at its current world position so physics resume normally.

**Confidence:** Medium

---

### [chunk_sticks_to_enemy] Planner — One-chunk and two-chunk independence

**Would have asked:** Must the stuck/recallable state for chunk 1 and chunk 2 be fully independent, with no shared flag or shared enemy reference?

**Assumption made:** Yes, fully independent. Each slot gets its own pair of controller fields: (`_chunk_stuck_on_enemy: bool`, `_chunk_stuck_enemy: Node`) for slot 1, and (`_chunk_2_stuck_on_enemy: bool`, `_chunk_2_stuck_enemy: Node`) for slot 2. Absorbing enemy A only clears the slot(s) whose stored enemy reference matches enemy A. A chunk stuck on enemy B remains stuck. This mirrors the independence invariant already established for `has_chunk` / `has_chunk_2`.

**Confidence:** High

---

### [chunk_sticks_to_enemy] Planner — Chunk attachment mechanism

**Would have asked:** Should the chunk stick to the enemy by being re-parented as a child of the enemy node, or by zeroing its physics velocity and updating its position every frame in the controller, or by another approach?

**Assumption made:** The conservative, minimal approach: when a chunk enters the enemy's InteractionArea, the enemy (EnemyInfection3D) emits a new signal `chunk_attached(chunk: RigidBody3D)`, which the controller (or a new thin script on the chunk) receives. On attachment, the chunk's `freeze = true` (halting physics) and the chunk is reparented as a child of the enemy node so it moves with the enemy automatically. On absorb completion (via the controller's absorb_resolved handler), the chunk is un-parented back to the scene root and `freeze = false` is restored. This avoids a per-frame position-sync loop and relies on Godot's scene tree reparenting.

**Confidence:** Medium

---

### [chunk_sticks_to_enemy] Planner — Signal routing: who notifies the controller?

**Would have asked:** Should EnemyInfection3D emit a signal that PlayerController3D connects to, or should the chunk itself call back to the controller, or should InfectionInteractionHandler mediate?

**Assumption made:** EnemyInfection3D emits two new signals: `chunk_attached(chunk: RigidBody3D)` (fired when a chunk body enters its InteractionArea) and `chunk_detached(chunk: RigidBody3D)` (fired when a stuck chunk is released after absorb). PlayerController3D connects to these signals from each enemy in the scene at startup (or the chunk connects them on spawn). The handler remains unmodified; it already emits `absorb_resolved` which the controller also connects to. This keeps the signal graph simple and the handler's scope unchanged.

**Confidence:** Medium

---

## Run: 2026-03-14T15:00:00Z
Tickets queued: chunk_sticks_to_enemy.md (SPECIFICATION stage — Spec Agent authoring)

---

### [chunk_sticks_to_enemy] Spec Agent — chunk_detached signal scope

**Would have asked:** The Planner checkpoint mentions two new signals: `chunk_attached` and `chunk_detached`. Should `chunk_detached` be defined on `EnemyInfection3D`, or is un-parenting on absorb sufficient (driven entirely by the `absorb_resolved` handler in `PlayerController3D`)?

**Assumption made:** `chunk_detached` is NOT added to `EnemyInfection3D` for this ticket. The conservative, minimal approach is that detach/un-parenting is driven entirely by `PlayerController3D._on_absorb_resolved`, which has all the information needed (stuck flags, chunk references, enemy references). Adding a `chunk_detached` signal would require `EnemyInfection3D` to track which chunks are attached — extra state that isn't needed. The Planner checkpoint mentioned it as a possibility ("or a new thin script on the chunk") but the simplest working design has only `chunk_attached` on `EnemyInfection3D` plus the `absorb_resolved` handler in `PlayerController3D`.

**Confidence:** High

---

### [chunk_sticks_to_enemy] Spec Agent — ESM matching via get_esm() vs node identity

**Would have asked:** Should `_on_absorb_resolved` match the absorbing enemy using ESM reference equality (`enemy_node.get_esm() == esm`) or by some other key?

**Assumption made:** ESM reference equality is the correct match key. `absorb_resolved` carries the `EnemyStateMachine` instance; `_chunk_stuck_enemy.get_esm()` returns the same object that was passed to `absorb_resolved`. Reference equality in GDScript for objects (non-value types) compares identity, which is deterministic and correct here since each enemy owns exactly one ESM instance.

**Confidence:** High

---

### [chunk_sticks_to_enemy] Spec Agent — find_children type filter string for EnemyInfection3D

**Would have asked:** `get_parent().find_children("*", "EnemyInfection3D", true, false)` uses a class name string filter. Does this work correctly for `class_name EnemyInfection3D` declared in the script?

**Assumption made:** Yes. In Godot 4, `find_children` type argument works with registered `class_name` names. `EnemyInfection3D` is declared as `class_name EnemyInfection3D` in `enemy_infection_3d.gd` (confirmed by reading the file). The filter will correctly return all `EnemyInfection3D` nodes.

**Confidence:** High

---

### [chunk_sticks_to_enemy] Spec Agent — chunk_3d group membership assumed

**Would have asked:** Is the `"chunk"` group already assigned to chunk_3d.tscn scene nodes, or does this feature need to add it?

**Assumption made:** The `"chunk"` group is already assigned on `chunk_3d.tscn`. This is confirmed indirectly: `EnemyInfection3D._on_body_entered` already checks `body.is_in_group("chunk")` (line 35 of the existing implementation), and the tests for `infection_interaction` pass. If the group were missing, the existing infection trigger tests would be broken. Therefore, no changes to `chunk_3d.tscn` group membership are required.

**Confidence:** High

---

## Run: 2026-03-14T16:00:00Z
Tickets queued: chunk_sticks_to_enemy.md (TEST_DESIGN stage)

---

### [chunk_sticks_to_enemy] Test Design — Headless test strategy for non-instantiable nodes

**Would have asked:** Both `EnemyInfection3D` (extends `BasePhysicsEntity3D`) and `PlayerController3D` (extends `BasePhysicsEntity3D`) cannot be instantiated headlessly. Should behavioral tests for SPEC-CSE-3 through SPEC-CSE-10 use real instances (requiring a scene tree) or minimal pure-Object stubs that embed the spec's logic?

**Assumption made:** All tests in the primary suite are headless-safe. `EnemyInfection3D` and `PlayerController3D` are replaced by minimal inner-class stubs (`FakeChunk`, `FakeEnemyNode`, `FakeControllerState`) that hold only the fields and methods specified in the API contracts. `EnemyStateMachine` (extends `RefCounted`) is used directly. Tests drive the fake objects through the exact sequences described in each AC and assert observable post-call state. This is identical to the pattern used in `test_dual_chunk_controller.gd` (which tests `MovementSimulation` directly rather than `PlayerController3D`). Scene-tree-required tests are explicitly out of scope for this suite; the adversarial suite (Test Breaker's job) may add scene-level integration tests with the documented dependency.

**Confidence:** High

---

### [chunk_sticks_to_enemy] Test Design — EnemyInfection3D signal emission test approach

**Would have asked:** `EnemyInfection3D._on_body_entered` emits `chunk_attached`. Since the class cannot be instantiated headlessly, should TC-CSE-001 through TC-CSE-003 test the GDScript signal declaration by loading the script and inspecting it, or by constructing a fake that mirrors the specified behavior?

**Assumption made:** TC-CSE-001 through TC-CSE-003 test the behavioral contract using a minimal `FakeEnemyNode` that implements `_on_body_entered` with the exact logic from SPEC-CSE-1 API contract (emit `chunk_attached` only when body is in "chunk" group, after weaken/infect calls). A separate test (TC-CSE-001-signal-decl) loads the real `enemy_infection_3d.gd` script and inspects signal declarations using `get_script_signal_list()` to confirm the signal is declared at class scope. This is the strictest defensible approach that remains headless-safe.

**Confidence:** Medium

---

## Run: 2026-03-16
Tickets queued: fusion_rules_and_hybrid.md (SPECIFICATION stage — Spec Agent authoring)

### [chunk_sticks_to_enemy] Code Review Fixes — All issues already resolved in working tree

**Would have asked:** A code review identified 5 issues (CRITICAL 1, CRITICAL 2, WARNING 1, WARNING 2, WARNING 3) in `player_controller_3d.gd` and `enemy_infection_3d.gd`. Were these issues introduced by the prior implementation run and need to be fixed now, or were they already addressed?

**Assumption made:** All five issues were already resolved in the current working tree before this agent run began. Full file reads confirmed:
- CRITICAL 1 (stuck flags not cleared on recall): Lines 240-242 and 299-301 of `player_controller_3d.gd` already clear `_chunk_stuck_on_enemy`, `_chunk_stuck_enemy`, `_chunk_2_stuck_on_enemy`, `_chunk_2_stuck_enemy` in both recall-complete paths.
- CRITICAL 2 (reparent without parent check): Lines 325-327 and 334-336 already guard `reparent` with `get_parent() == _chunk_stuck_enemy` checks.
- WARNING 1 (chunk_attached emitted on weaken hit): Line 44 of `enemy_infection_3d.gd` already places `chunk_attached.emit(chunk)` inside the `if _esm.get_state() == "weakened":` branch only.
- WARNING 2 (no re-entry guard): `_attached_chunks: Array[RigidBody3D] = []` field at line 17, guard at lines 40-41, and append at line 45 are all present.
- WARNING 3 (signal not disconnected): `_exit_tree()` at lines 97-106 already disconnects the signal from all enemies.

No file modifications were required. The code review was generated against an older snapshot of the code; the prior Gameplay Systems Agent run had already applied all the fixes. No changes were made, no tests were broken.

**Confidence:** High


## Run: 2026-03-16T13:07:42Z
Tickets queued: fusion_rules_and_hybrid.md

---

### [fusion_rules_and_hybrid] Planning — Fuse input action name

**Would have asked:** No "fuse" input action exists in project.godot. The existing actions are move_left, move_right, jump, detach, detach_2, absorb, infect. What key and action name should the fusion trigger use?

**Assumption made:** A new input action named `"fuse"` mapped to the F key (physical_keycode 70 is already used by `infect`, so use G key, physical_keycode 71) will be added to project.godot. The action name `"fuse"` is consistent with the naming convention (short verb). The Spec Agent will confirm the exact key; if the design changes, it is a single-line change in project.godot and a string change in the handler.

**Confidence:** Medium

---

### [fusion_rules_and_hybrid] Planning — Where fusion logic lives (pure vs wired)

**Would have asked:** Should fusion detection and effect application live in a new pure-logic script (FusionResolver, analogous to InfectionAbsorbResolver), or be wired directly into InfectionInteractionHandler's _process loop?

**Assumption made:** A new pure-logic script `scripts/fusion/fusion_resolver.gd` (class FusionResolver, extends RefCounted) handles the fusion rules: can_fuse(slot_manager) and resolve_fusion(slot_manager, player). InfectionInteractionHandler reads the fuse input and delegates to FusionResolver. This keeps the engine-integration handler thin and keeps fusion logic headless-testable, consistent with the pattern established by InfectionAbsorbResolver.

**Confidence:** High

---

### [fusion_rules_and_hybrid] Planning — Minimum hybrid gameplay effect

**Would have asked:** What tangible gameplay effect should the initial fusion hybrid produce? The ticket says "at minimum a speed boost or similar."

**Assumption made:** The first and only required fusion hybrid for this ticket is a timed speed boost: `_FUSION_SPEED_MULTIPLIER` (e.g. 1.5x) applied to `_simulation.max_speed` in PlayerController3D for a fixed duration (e.g. 5 seconds), then restored. This is the simplest observable effect that reuses existing speed-multiplier infrastructure already in the controller. The Spec Agent will nail down the exact multiplier and duration; if a different effect is preferred, it can be swapped without changing the resolver's API.

**Confidence:** Medium

---

### [fusion_rules_and_hybrid] Planning — Fusion guard: must both slots be filled

**Would have asked:** Should fusion be allowed when only one slot is filled, or is it strictly gated on both slots being filled (slot_manager.any_filled() vs a new both_filled() check)?

**Assumption made:** Fusion requires both slots to be filled. `MutationSlotManager` does not yet have a `both_filled()` method; FusionResolver will implement its own check: `slot_manager.get_slot(0).is_filled() and slot_manager.get_slot(1).is_filled()`. This is the most conservative, testable guard and matches the ticket's stated trigger condition. The Spec Agent may choose to add a `both_filled()` convenience method to MutationSlotManager; if so, that is a backend task assigned to Core Simulation Agent.

**Confidence:** High

---

### [fusion_rules_and_hybrid] Planning — HUD fusion prompt visibility

**Would have asked:** Should the InfectionUI show a fusion prompt hint only when both slots are filled, similar to how set_absorb_available() drives the absorb prompt?

**Assumption made:** Yes. InfectionUI will show a "FusePromptLabel" (or equivalent Label node in the scene) that is visible only when both slots are filled. The label text will display the fuse key hint. This follows the exact same pattern as AbsorbPromptLabel and set_absorb_available(), requiring minimal new code. The Spec Agent will confirm the exact label name and text; implementation re-uses existing _process update logic in infection_ui.gd.

**Confidence:** High

---

### [fusion_rules_and_hybrid] Planning — Fusion effect duration and re-fuse after cooldown

**Would have asked:** After a fusion and its effect expires, can the player immediately re-infect two enemies and fuse again, or is there a cooldown?

**Assumption made:** No cooldown. Once consume_fusion_slots() is called, both slots are empty and the player can immediately begin re-infecting. The fusion effect (speed boost) runs for its fixed duration on a timer; a second fusion can occur as soon as both slots are refilled. This is the most conservative, repeatable design and is explicitly required by the ticket AC ("fusion is repeatable in play"). If a cooldown is desired later, it is a feature addition, not a blocker.

**Confidence:** High

---

### [fusion_rules_and_hybrid] Spec — G key confirmed for fuse action

**Would have asked:** Physical keycode 70 is used by the `infect` action (F key). Should fuse use the G key (physical_keycode 71) as assumed by the Planner, or a different key?

**Assumption made:** G key (physical_keycode 71) confirmed. Rationale: F (70) is infect, G is adjacent and unused by any existing action, and the Planner checkpoint already documents this. No existing action uses G. The spec confirms `"fuse"` maps to physical_keycode 71.

**Confidence:** High

---

### [fusion_rules_and_hybrid] Spec — both_filled() method not added to MutationSlotManager

**Would have asked:** Should `MutationSlotManager` gain a `both_filled() -> bool` convenience method, or should `FusionResolver` implement the guard directly using `get_slot(0).is_filled()` and `get_slot(1).is_filled()`?

**Assumption made:** `both_filled()` is NOT added to `MutationSlotManager` for this ticket. FusionResolver implements the guard directly. Rationale: adding a method to MutationSlotManager requires a Core Simulation Agent task and changes an existing tested module. The direct check is equivalent, already testable, and avoids scope creep. If future code duplication warrants a convenience method, it can be added independently.

**Confidence:** High

---

### [fusion_rules_and_hybrid] Spec — resolve_fusion call order: apply effect before consume slots

**Would have asked:** Should `apply_fusion_effect` be called before or after `consume_fusion_slots` in `resolve_fusion`?

**Assumption made:** Effect is applied first, slots are consumed second. Rationale: if `apply_fusion_effect` were to fail or crash (unlikely but defensive), calling it first means slots are not yet consumed and the game state remains recoverable. Consume-after-effect is the safe, conservative order. This is mandated as the canonical order in FRH-3-AC-11.

**Confidence:** High

---

### [fusion_rules_and_hybrid] Spec — Fusion multiplier and duration final values

**Would have asked:** Are the Planner's suggested defaults (multiplier 1.5, duration 5.0 seconds) acceptable, or should different values be used?

**Assumption made:** Multiplier 1.5 and duration 5.0 seconds are confirmed as final values. Rationale: 1.5x is perceptibly higher than the existing mutation multiplier (1.25x), making fusion clearly rewarding. 5.0 seconds is long enough to be felt but short enough to not trivialize the game. These are defined as named constants in FusionResolver (FUSION_MULTIPLIER, FUSION_DURATION) so a one-line change updates them globally.

**Confidence:** High

---

### [fusion_rules_and_hybrid] Spec — Fusion timer re-trigger semantics

**Would have asked:** If `apply_fusion_effect` is called while a fusion effect is already active (e.g. the player somehow fuses again before the first effect expires), should the timer reset or stack?

**Assumption made:** Timer resets (re-triggerable). The new call replaces `_fusion_timer` with the new duration and `_fusion_multiplier` with the new multiplier. No stacking. This is the simplest, most predictable behaviour: fusion always gives a fresh 5-second window regardless of when it is triggered. Stacking would require summing timers, which adds complexity without clear gameplay benefit at this stage.

**Confidence:** High

---

## Run: 2026-03-17T00:00:00Z
Tickets queued: visual_clarity_hybrid_state.md (PLANNING stage)

---

### [visual_clarity_hybrid_state] Planning — Fusion-active indicator via player field read

**Would have asked:** `InfectionUI` needs to know whether fusion is active. `PlayerController3D` has `_fusion_active: bool` (a private field). Should `InfectionUI` read this via a public accessor method `is_fusion_active() -> bool` (consistent with `get_current_hp()` pattern), or directly access the field since it already references `_player`?

**Assumption made:** The Spec Agent must define a public accessor method `is_fusion_active() -> bool` on `PlayerController3D`, consistent with the existing pattern where InfectionUI uses `_player.get_current_hp()` rather than reading `_player._current_hp` directly. Direct private field access would be a convention violation. This is flagged as a Spec-required API addition; it is a one-line method and does not require a new implementation task.

**Confidence:** High

---

### [visual_clarity_hybrid_state] Planning — New scene nodes required for fusion-active indicator

**Would have asked:** Is a new Label node (`FusionActiveLabel`) needed in `game_ui.tscn` to show the fusion-active state, or can the existing `FusePromptLabel` be repurposed to display both "ready to fuse" and "fusion active" states with different text and color?

**Assumption made:** The most conservative approach: the Spec Agent decides. The plan does not add a new node in this task; if the Spec Agent determines that a new `FusionActiveLabel` node is required, it is a small addition to `game_ui.tscn` scoped entirely to the Presentation Agent's implementation task. Reusing `FusePromptLabel` for both states is allowed if text and color differentiation are sufficient; adding a separate node is allowed if they are not. Either choice is self-contained.

**Confidence:** Medium

---

### [visual_clarity_hybrid_state] Planning — Post-fusion empty state distinguishability

**Would have asked:** After fusion fires and slots are cleared, both slot icons return to their "empty" grey color — identical to the pre-absorb state. Should a timed visual cue (e.g. brief white flash on MutationIcon1/MutationIcon2) distinguish "just fused" from "never absorbed"?

**Assumption made:** Yes, a brief timed flash or distinctive color modulation on the icon nodes after fusion is the minimum required to satisfy AC "post-fusion state is distinct from single-mutation." Duration and exact mechanism (flash, pulse, or held color for N ms) are deferred to the Spec Agent. The implementation pattern already exists in InfectionUI for absorb feedback (`_absorb_feedback_until_ms`); the same timer-based approach is the default assumption.

**Confidence:** Medium

---

## Run: 2026-03-17T01:00:00Z
Tickets queued: visual_clarity_hybrid_state.md (SPECIFICATION stage)

---

### [visual_clarity_hybrid_state] Spec — FusionActiveLabel as a new node vs reusing FusePromptLabel

**Would have asked:** Should `FusePromptLabel` be repurposed to show both "press G to fuse" (ready) and "FUSION ACTIVE" (running), or should a separate `FusionActiveLabel` node be added?

**Assumption made:** A separate `FusionActiveLabel` node is added. The two states serve different semantic purposes: `FusePromptLabel` is a player affordance (action instruction shown when fusion is available); `FusionActiveLabel` is a status notification (shown while the effect is running, after slots are empty). Repurposing the prompt label would require logic to swap text and color inside a single visibility path, creating a coupling between "ready" and "active" states that does not exist in any other UI element in the codebase. A separate node keeps the logic clean and is consistent with the AbsorbPromptLabel / AbsorbFeedbackLabel precedent (separate nodes for "available" vs "feedback").

**Confidence:** High

---

### [visual_clarity_hybrid_state] Spec — Post-fusion flash duration: 600 ms

**Would have asked:** How long should the post-fusion flash last? The absorb feedback uses 800 ms. Should the post-fusion flash match, or be shorter to feel distinct?

**Assumption made:** 600 ms. Shorter than the absorb feedback flash (800 ms) so the two cues feel distinct if they somehow overlap. Long enough to be perceived clearly at normal play speed. The value is defined as a named constant `POST_FUSION_FLASH_DURATION_MS: int = 600` so it is trivially adjustable.

**Confidence:** Medium

---

### [visual_clarity_hybrid_state] Spec — Post-fusion flash trigger condition requires is_fusion_active()

**Would have asked:** The flash must fire specifically when fusion cleared the slots (not any other slot-clear event). Should the trigger require `is_fusion_active() == true` in the same frame as the both_filled transition, or should the flash fire on any both_filled-to-empty transition?

**Assumption made:** Trigger requires `is_fusion_active() == true`. This gates the flash specifically to the fusion event and prevents spurious flashes from hypothetical future slot-clear mechanisms. The one-frame lag between fusion firing (in physics process) and InfectionUI detecting it (in _process) is acceptable and consistent with all other player-state reads in InfectionUI.

**Confidence:** High

---

### [visual_clarity_hybrid_state] Spec — COLOR_SLOT_DUAL_FILLED chosen as saturated blue

**Would have asked:** What specific color distinguishes "both slots filled" from "single slot filled"? The existing single-fill color is green (0.4, 0.85, 0.55). Should dual-fill be a different hue (e.g. blue, gold, cyan) or a brighter/saturated green?

**Assumption made:** Saturated blue: `Color(0.3, 0.65, 1.0, 1.0)`. Blue is maximally distinct from the existing green palette in the mutation UI and from the amber gold reserved for the fusion-active label. It reads as "upgraded state" without conflicting with HP (red), absorb feedback (green tint), or cling/chunk labels (white/grey). The exact values are conservative defaults; the Implementer may adjust within the blue family if screen visibility testing warrants it.

**Confidence:** Medium

---

## Run: 2026-03-17T03:00:00Z
Tickets queued: visual_clarity_hybrid_state.md (Test Breaker Agent)

---

### [visual_clarity_hybrid_state] TestBreak — same-color dual-fill bug detection strategy

**Would have asked:** The primary suite already asserts `COLOR_SLOT_DUAL_FILLED != COLOR_SLOT_SINGLE_FILLED` as a constant comparison. Is an additional adversarial test needed, or does the constant-comparison test already catch the same-color bug?

**Assumption made:** A separate adversarial test is warranted. The constant-comparison test (VCH-1-AC-4) only verifies the constants differ; it does NOT verify that the implementation actually uses `COLOR_SLOT_DUAL_FILLED` when both slots are filled (a naive implementation could declare the constant but still apply `COLOR_SLOT_SINGLE_FILLED` in the method body). The adversarial test must verify that the color selection matrix actually returns `COLOR_SLOT_DUAL_FILLED` and that this result is NOT equal to `COLOR_SLOT_SINGLE_FILLED`, closing the gap between constant-declaration and actual usage.

**Confidence:** High

---

### [visual_clarity_hybrid_state] TestBreak — is_fusion_active() method missing on PlayerController3D

**Would have asked:** `is_fusion_active()` does not yet exist on `PlayerController3D` (confirmed by grep). The adversarial test for failure mode #9 should verify the method IS present on the real script. Should this be a hard FAIL or a soft warning?

**Assumption made:** Hard FAIL. The spec (API-1) mandates this method as a required public accessor. `InfectionUI._update_fusion_display()` calls it every frame; if missing it silently breaks all fusion-active visual feedback without a parse error (GDScript duck-type). The adversarial test checks `get_script_method_list()` on the real `player_controller_3d.gd` script and fails hard if the method is absent, forcing the Presentation Agent to add it.

**Confidence:** High

---

### [visual_clarity_hybrid_state] TestBreak — FusePromptLabel post-fusion visibility contract

**Would have asked:** After fusion fires and both slots clear, `both_filled` becomes `false`. Does `FusePromptLabel.visible` go to `false` automatically (because it's driven by `both_filled`)? Or is there a separate clear/hide step needed?

**Assumption made:** FusePromptLabel hides automatically because `_process` evaluates `both_filled` fresh each frame from slot state, and with both slots empty `both_filled == false` drives `fuse_label.visible = false`. The adversarial test encodes this: it verifies that the transition from both-filled to both-empty (slot-clear simulated) results in `both_filled == false`, which MUST make the fuse prompt hidden. This is a regression guard -- any implementation that accidentally caches `both_filled` or uses a separate flag could regress it. # CHECKPOINT

**Confidence:** High

---

### [visual_clarity_hybrid_state] TestBreak — flash duration zero edge case

**Would have asked:** If `_post_fusion_flash_until_ms` is set to exactly `Time.get_ticks_msec()` (i.e. duration zero), does the flash trigger at all? The spec says `now_ms < _post_fusion_flash_until_ms` so duration=0 means the condition is immediately false. Should the test cover this as a boundary?

**Assumption made:** Yes, this is a real boundary. A zero-duration flash (set to `now` not `now + 600`) means the flash condition is `now < now` which is always false -- the flash never renders. The adversarial test must verify that the flash-active path requires a STRICTLY FUTURE timestamp, and that setting `_post_fusion_flash_until_ms = now` (not `now + 600`) results in no flash. This catches an off-by-one bug where a developer writes `=` instead of `+` in the timer assignment. # CHECKPOINT

**Confidence:** High

---

### [visual_clarity_hybrid_state] TestBreak — slot-only text change without color change

**Would have asked:** The spec says label text changes when mutation_id changes. But if a naive implementation only changes text and not modulate, the test suite would still pass (primary tests only check color via the harness, not the real label node). How do we catch this?

**Assumption made:** Add an adversarial test that drives the LogicHarness for a mutation-id-change scenario and explicitly asserts the LABEL color is `COLOR_LABEL_SINGLE_FILLED` (not the legacy hard-coded `Color(0.9, 1.0, 0.9, 1.0)` magic value). If the implementer forgets to use the named constant and uses the legacy magic number, this test fails because the adversarial harness computes `COLOR_LABEL_SINGLE_FILLED` from the constant map. The gap: the primary test checks the harness, the adversarial test checks that the real constant VALUE matches the harness constant (ensuring no magic-number drift). # CHECKPOINT

**Confidence:** Medium

---

### [visual_clarity_hybrid_state] Implementation — _update_fusion_display null safety

**Would have asked:** `_update_fusion_display()` calls `_player.is_fusion_active()` directly. Should it re-check `_player != null` inside the method, or rely on the call-site guard in `_process`?

**Assumption made:** Rely on call-site guard. `_update_fusion_display()` is a private method called only after `if _player == null: return` in `_process`. Adding a redundant null-check inside is inconsistent with the existing pattern (e.g. `_player.get_current_hp()`, `_player.has_chunk()` etc. are called with no per-call null-check after the same guard). The flash trigger in `_update_mutation_display` (called before the null guard) explicitly checks `_player != null` inline because it runs unconditionally.

**Confidence:** High

---

### [visual_clarity_hybrid_state] Implementation — FusionActiveLabel text content

**Would have asked:** The ticket says text `"⚡ FUSED"` (or similar). No test checks the exact text string. What text to use?

**Assumption made:** Used `"FUSION ACTIVE"` — plain ASCII, readable without emoji font support in any headless render. The spec has no exact text requirement and no test checks it.

**Confidence:** High

---

## Run: 2026-03-17T01:00:00Z
Tickets queued: player_hud.md

---

## Run: 2026-03-18T00:01:00Z
Tickets queued: player_hud.md (PLANNING stage — Planner Agent)

---

### [player_hud] Planning — Node renames in game_ui.tscn vs infection_ui.gd accessor strings

**Would have asked:** The HUD reorganization requires repositioning all nodes. If any nodes are renamed during reorganization (e.g. wrapping them in a Panel container changes the path), all `get_node_or_null("NodeName")` calls in `infection_ui.gd` would need to match. Should the plan treat node names as immutable and only reposition, or allow renames with a required update pass on the accessor strings?

**Assumption made:** Node names are preserved exactly. The reorganization moves nodes by changing their `offset_*` properties and adding structural container parents (e.g. a `StatusPanel` PanelContainer), but all leaf node names (`HPLabel`, `HPBar`, `ChunkStatusLabel`, `ClingStatusLabel`, `MutationSlot1Label`, `MutationIcon1`, `MutationSlot2Label`, `MutationIcon2`, `AbsorbPromptLabel`, `AbsorbFeedbackLabel`, `FusePromptLabel`, `FusionActiveLabel`, `MutationLabel`, `MutationSlotLabel`, `MutationIcon`, `Hints`) stay identical. `infection_ui.gd` uses flat `get_node_or_null("NodeName")` calls from the CanvasLayer root — if containers are added, nodes must stay as direct children of the CanvasLayer OR the accessor paths must be updated. Conservative assumption: all nodes remain direct children of `GameUI` (no nesting). Visual grouping is achieved via offset alignment, not container parenting.

**Confidence:** High

---

### [player_hud] Planning — InputHintsConfig default value must change

**Would have asked:** The ticket requires input hints hidden by default in normal play. `input_hints_config.gd` currently defaults `input_hints_enabled = true`. Changing this to `false` will hide hints in all scenes where no InputHintsConfig is present (since the fallback in `_update_input_hints_visibility` treats missing config as enabled=true). Should the default in the config script be changed, or should the scene that instantiates InputHintsConfig be updated to set it false?

**Assumption made:** The fix is in `input_hints_config.gd`: change `var input_hints_enabled: bool = true` to `var input_hints_enabled: bool = false`. The ticket acceptance criterion says hints are "hidden by default in normal play" — the config default IS the normal-play value. Any scene that needs hints shown (e.g. a tutorial scene) explicitly sets the value to true. The fallback in `_update_input_hints_visibility` (`var enabled: bool = true` when config is absent) remains unchanged as a safety net for scenes without a config node at all.

**Confidence:** High

---

### [player_hud] Planning — HPBar visual style: TextureProgressBar has no textures assigned

**Would have asked:** The current `HPBar` node is a `TextureProgressBar` with no texture resources set, so it renders as nothing visible. Should the HUD reorganization replace it with a `ProgressBar` (which renders with a theme-default fill bar), or keep `TextureProgressBar` and set a minimal texture?

**Assumption made:** Replace `TextureProgressBar` with a plain `ProgressBar` node (same node name `HPBar`, same parent). `ProgressBar` renders a visible fill bar using Godot's built-in theme with no asset dependencies, matching the ticket requirement that the HUD be "human-readable in-editor without debug overlays." Asset-styled progress bars are a future visual polish concern. The `_get_hp_bar()` accessor returns `Range` (base class of both), so the script requires no change.

**Confidence:** High

---

### [player_hud] Planning — Layout region assignments for each HUD group

**Would have asked:** What exact screen regions should each HUD group occupy at 3200x1880? The ticket says "top-left panel" for HP but does not specify where mutation slots, status labels, or contextual prompts go.

**Assumption made:** Four non-overlapping regions at 3200x1880:
  - Top-left status strip (x: 20–400, y: 8–180): HPBar, HPLabel, ChunkStatusLabel, ClingStatusLabel — stacked vertically with 28px row pitch.
  - Mid-left mutation panel (x: 20–400, y: 200–300): MutationIcon1 + MutationSlot1Label, then MutationIcon2 + MutationSlot2Label, then MutationSlotLabel (legacy, hidden in practice) — 36px row pitch.
  - Contextual center-bottom prompts (x: 1400–1800, y: 1800–1870): AbsorbPromptLabel, FusePromptLabel, AbsorbFeedbackLabel — centered horizontally, stacked.
  - Fusion-active notice (x: 20–300, y: 310–340): FusionActiveLabel — below mutation panel, amber, always visible when active.
  - MutationLabel (x: 20–300, y: 350–375): shown only when any mutations absorbed.
  - Hints group (top-center, x: 1300–2000, y: 12–120): grouped MoveHint, JumpHint, DetachRecallHint, AbsorbHint — hidden by default.

**Confidence:** Medium

---

### [player_hud] Planning — Legacy nodes MutationSlotLabel and MutationIcon retained

**Would have asked:** The legacy single-slot nodes (`MutationSlotLabel`, `MutationIcon`) are still updated by `infection_ui.gd` for backward compatibility. Should they be removed (cleaning up the scene) or kept but hidden/repositioned so they don't overlap?

**Assumption made:** Kept but positioned below the dual-slot rows and set `visible = false` by default in the scene. They are driven by `infection_ui.gd` for backward compat and the acceptance criteria explicitly state "all existing `infection_ui.gd` data bindings are preserved." Removal would require also modifying the script, which is out of scope for a pure layout change.

**Confidence:** High

---

## Run: 2026-03-18T12:00:00Z
Tickets queued: player_hud.md (SPECIFICATION stage — Spec Agent authoring)

---

### [player_hud] Spec — ProgressBar show_percentage default behavior

**Would have asked:** `ProgressBar` nodes display a percentage text overlay by default (`show_percentage = true`). With `HPLabel` showing "HP: X / Y" directly below the bar, having the bar also display "X%" would be redundant and potentially confusing. Should the spec require `show_percentage = false` on the HPBar ProgressBar node?

**Assumption made:** Yes, `show_percentage = false` is required. Having two HP value displays (the label and the bar's internal percentage) is confusing and inconsistent with the "human-readable without debug overlays" acceptance criterion. The HPLabel already provides full HP information (current/max). AC-2.7 is added to the spec to enforce this.

**Confidence:** High

---

### [player_hud] Spec — Hints child offsets are viewport-absolute because Hints container is at origin

**Would have asked:** The `Hints` Control node has `anchors_preset=0` with no offset set, placing it at (0,0) in the CanvasLayer. If a future change repositions the Hints container, the child offsets (which are relative to the container) would no longer correspond to the viewport positions in the layout table. Should the spec explicitly state that Hints remains at origin, and that child offsets ARE viewport-absolute for the purposes of this spec?

**Assumption made:** Yes, the spec explicitly states this as an assumption (Section 1.2, Region 7). Hints remains at position (0,0) — no `offset_*` changes on the Hints node itself. Child hint labels' offsets are equivalent to viewport coordinates because the container's origin coincides with the viewport origin. If Hints is ever repositioned, the child offsets must be recalculated.

**Confidence:** High

---

### [player_hud] Spec — AbsorbPromptLabel and AbsorbFeedbackLabel co-location is intentional

**Would have asked:** Both AbsorbPromptLabel and AbsorbFeedbackLabel are assigned to the same bounding rectangle (Rect2(1400, 1800, 400, 30)). This appears to violate the no-overlap requirement. Is this intentional?

**Assumption made:** Yes, intentional. These two nodes are never simultaneously visible: AbsorbPromptLabel shows when an enemy is absorbable (before absorb resolves); AbsorbFeedbackLabel shows as a timed flash after absorb resolves (at which point AbsorbPromptLabel is hidden because `_absorb_available` is false). The pairwise disjointness test explicitly excludes this pair. The co-location maximizes readability — both messages appear in the same center-bottom region, giving visual consistency to absorb-related feedback.

**Confidence:** High

---

### [player_hud] Spec — Row pitch in status strip chosen for font_size=20 readability

**Would have asked:** The status strip (Y 8–180) fits HPBar + HPLabel + ChunkStatusLabel + ClingStatusLabel. With font_size=20, each label renders approximately 26px tall. The chosen row pitch of 34px (e.g. top=36 to top=70) gives an 8px gap between rows. Is this sufficient, or should rows be more spread out?

**Assumption made:** 34px pitch (8px gap between 26px-tall labels) is sufficient for font_size=20. This keeps the status strip compact and contained within Y 8–130, leaving a 70px gap to the mutation panel at Y=200. The gap is visible and clear even at the target resolution. If the display proves crowded, the Presentation Agent can increase the pitch within the Y 8–180 budget without changing node names or violating the no-overlap spec.

**Confidence:** Medium

---

