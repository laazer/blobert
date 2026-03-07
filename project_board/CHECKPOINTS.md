# Autopilot Checkpoint Log

Decisions logged here required human judgment but were resolved autonomously.
Review these after autopilot completes.

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

### [infection_interaction] Test Designer — Mutation “usable” via InfectionUI

**Would have asked:** Does “at least one mutation is granted and usable after absorb” require a concrete gameplay effect, or is a visible mutation indicator in the infection-loop HUD sufficient for this milestone?

**Assumption made:** For this milestone, a mutation is considered “usable” if it is (a) granted into `MutationInventory` and (b) made clearly visible to the player via InfectionUI (e.g. `MutationLabel`/`MutationIcon` driven from `get_mutation_inventory()` and `get_granted_count()`). Tests enforce that a non-zero mutation count makes the mutation label visible; any deeper gameplay effect is left to future tickets.

**Confidence:** Medium

---

### [infection_interaction] Test Designer — Infection FX text and tint mapping

**Would have asked:** Should the infection state FX contract specify exact label text and color tints for weakened/infected/dead, or only require that each state is visually distinct?

**Assumption made:** The strictest defensible contract for this ticket is that `infection_state_fx.gd` produces distinct visuals and explicit state labels: “Weakened”, “Infected”, and “Dead”, with weakened/infected tinted away from the idle/default color and dead rendered dimmer (alpha < 1). Tests assert these concrete label strings and basic tint/dim relationships rather than exact RGB values, so future visual tweaks remain possible while keeping states clearly distinguishable.

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

**Assumption made:** The canonical, testable contract for this ticket is chunk-based contact: when an infecting slime chunk body enters a weakened enemy’s infection area, infection is triggered if the enemy is eligible. Any `infect` input action wiring is treated as higher-level engine integration and is not required for this spec to be satisfied.

**Confidence:** Medium

---

### [infection_interaction] Spec — Infection eligibility scope

**Would have asked:** Do all enemies support being weakened and infected, or only a subset tagged/configured for infection in this milestone?

**Assumption made:** Only enemies whose state is driven by `EnemyStateMachine` and are explicitly configured/marked as infection-eligible in the scene or data are in scope. Other enemies remain non-infectable for this milestone and are allowed to ignore chunk contact entirely.

**Confidence:** Medium

---

### [infection_interaction] Spec — Mutation selection rule

**Would have asked:** When absorbing an infected enemy, if multiple mutation types exist, should the granted mutation be random, cyclic, or fixed?

**Assumption made:** For this milestone, mutation granting is deterministic and fixed: absorbing an infected enemy always grants a single, configured mutation ID (e.g. the first entry in a small infection-mutation config), with no randomness. This keeps tests and player expectations stable while still delivering “at least one mutation.”

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
All automated infection interaction suites (primary + adversarial) are passing and a human has verified in-editor that infection/absorb visuals and UX satisfy the final acceptance criterion; ticket is marked COMPLETE and moved to the milestone’s done column.

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

**Assumption made:** For this milestone, the conservative contract is that the slot represents a persistent, always-on mutation once filled. Using the mutation expresses its effect (e.g. passive stat change or repeatable ability) but does not automatically clear the slot; the slot is only changed when a new mutation is equipped or explicitly cleared by design. Spec and tests will treat one filled slot with persistent effect as the minimum required behavior.

**Confidence:** Medium

---

### [mutation_slot_system_single] Planner — Multiple granted mutations

**Would have asked:** If the player absorbs multiple enemies and gains multiple mutations, how should the single slot choose which mutation is active (first granted, last granted, configurable selection, or other rule)?

**Assumption made:** For this ticket, the selection rule is deterministic and simple: the active slot always tracks the most recently granted compatible mutation (last-wins). Additional inventory capacity or multi-mutation management is out of scope; tests and spec will only require that the latest valid mutation from an absorb becomes the active slot content, with previous slot contents replaced but inventory history remaining consistent.

**Confidence:** Medium

---

### [mutation_slot_system_single] Planner — Scope of persistence and save/load

**Would have asked:** Should the mutation slot contents and its active effect persist across scene reloads/checkpoints or be scoped only to the current play session/scene?

**Assumption made:** In line with other Milestone 2 infection-loop tickets, the mutation slot is scoped to the current play session/scene. Persistence across saves, level transitions, or meta-progression is explicitly out of scope for this ticket and can be handled by future progression/persistence features.

**Confidence:** High

---

### [mutation_slot_system_single] Spec — Slot vs effect gating

**Would have asked:** For this milestone, should the active mutation slot state be the *only* authority for enabling/disabling the mutation’s gameplay effect, or can the existing implementation that ties the effect directly to `MutationInventory` remain unchanged as long as slot state accurately mirrors inventory?

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

### [mutation_slot_system_single] Gameplay Systems Agent — Mutation slot movement buff magnitude

**Would have asked:** What concrete gameplay effect (type and magnitude) should the active mutation slot provide for this milestone so that it feels "real" but does not destabilize existing movement tuning or infection-loop difficulty?

**Assumption made:** Implement a single passive movement buff driven by the active slot: `PlayerController` caches the baseline `MovementSimulation.max_speed` in `_base_max_speed` and, on each physics frame, raises `max_speed` by a fixed 1.25× multiplier only when the cached `MutationSlot` reference is non-null and `slot.is_filled()` is true, restoring the baseline when the slot is empty. No other movement or HP parameters are changed, so baseline behavior for non-slot scenes is unchanged and the buff remains modest and easily re-tunable.

**Confidence:** Medium

---

### [mutation_slot_system_single] Engine Integration Agent — Slot HUD empty state vs existing tests

**Would have asked:** Should the InfectionUI mutation HUD show an explicit "empty" slot state (e.g. text such as "Mutation Slot: Empty") even when no mutations have been granted yet, or remain hidden until the first mutation is acquired as encoded in the existing `test_infection_ui.gd` suite?

**Assumption made:** To avoid breaking the established `basic_ui_feedback_infection` contract, the MutationLabel and MutationIcon remain hidden when `MutationInventory.get_granted_count() == 0`, and become visible once the count is greater than zero. The InfectionUI now also holds an optional `MutationSlot` reference and, when both inventory and slot indicate an active mutation in normal absorb-driven play, the label text is upgraded to show the active mutation ID (e.g. "Mutation Slot: infection_mutation_01 active") while continuing to rely on inventory count for visibility in tests that drive the inventory directly.

**Confidence:** Medium

---

### [mutation_slot_system_single] Presentation Agent — Slot empty HUD indicator vs legacy tests

**Would have asked:** Can InfectionUI's `MutationLabel` become always-visible to show an explicit \"Mutation Slot: Empty\" state at scene start, or must we preserve the `basic_ui_feedback_infection` contract that keeps it hidden until the first mutation is granted via inventory?

**Assumption made:** Preserve the existing tests and semantics for `MutationLabel` (hidden when `MutationInventory.get_granted_count() == 0`, visible after the first grant) and satisfy SLOT-4's empty/filled HUD requirement by adding a separate always-visible `MutationSlotLabel` plus a dimmed `MutationIcon` to represent the empty slot, brightening both when the slot is filled and using the slot's active ID to drive the text when available.

**Confidence:** Medium

---

### [scene_state_machine] Test Designer — Public API shape and per-state flags

**Would have asked:** Should `SceneStateMachine` expose its behavior via a generic `apply_event(event_id: String)` API with string event identifiers, or via dedicated methods per variant (e.g. `select_baseline()`), and what exact `enable_infection_loop`, `enable_enemies`, and `enable_prototype_hud` flag combinations should each canonical state use?

**Assumption made:** For this ticket, the strictest deterministic contract is a pure-logic `SceneStateMachine` script at `res://scripts/scene_state_machine.gd` that (a) exposes `get_state_id() -> String`, `get_config() -> Dictionary`, and `apply_event(event_id: String) -> void`, (b) treats `"select_baseline"`, `"select_infection_demo"`, and `"select_enemy_playtest"` as the only recognized events, and (c) maps states to configuration flags as:
`BASELINE` → `{enable_infection_loop: false, enable_enemies: false, enable_prototype_hud: true}`,
`INFECTION_DEMO` → `{enable_infection_loop: true, enable_enemies: false, enable_prototype_hud: true}`,
`ENEMY_PLAYTEST` → `{enable_infection_loop: false, enable_enemies: true, enable_prototype_hud: true}`.
Unknown event IDs and redundant selections are strict no-ops for both state and config, and all instances are fully deterministic and isolated.

**Confidence:** Medium

---

### [scene_state_machine] Orchestrator — Milestone placement

**Would have asked:** Which milestone should the new scene state machine ticket live under — Milestone 2 (Infection Loop), Milestone 3 (Dual Mutation Fusion), or Milestone 4 (Prototype Level)?

**Assumption made:** Place the ticket under `4_milestone_4_prototype_level/backlog/` with Epic set to “Milestone 4 – Prototype Level”, since the scene state machine primarily supports composing and toggling complex feature configurations in prototype levels while remaining reusable by earlier milestones.

**Confidence:** Medium

---

### [scene_state_machine] Orchestrator — Workflow block initialization

**Would have asked:** Should the orchestrator create initial WORKFLOW STATE / NEXT ACTION blocks for the new ticket before handing off to Planner, or follow the `mutation_slot_system_single` precedent and let Planner normalize the ticket structure?

**Assumption made:** Follow the precedent from `[mutation_slot_system_single]`: the orchestrator leaves the new ticket with description and acceptance criteria only, moves it into the active column, and relies on the Planner agent to introduce and own the initial WORKFLOW STATE and NEXT ACTION blocks.

**Confidence:** Medium

---

## Run: 2026-03-06T00:00:00Z
Tickets queued: scene_state_machine.md

---

### [scene_state_machine] Planner — Ticket metadata defaults

**Would have asked:** What initial values should the `Created By`, `Created On`, and `Revision` fields use when normalizing the new `scene_state_machine` ticket into the standard workflow template?

**Assumption made:** Initialize the ticket as if this is its first formal workflow pass: set `Created By` to `Human`, `Created On` to the current ISO-8601 date-time for this run, and `Revision` to `1` when introducing the WORKFLOW STATE / NEXT ACTION blocks, with future agents incrementing Revision on each subsequent state change.

**Confidence:** Medium

---

### [scene_state_machine] Spec — Canonical scene states

**Would have asked:** Which exact scene variants must be treated as canonical states in the scene state machine for this milestone, and are additional future variants in scope?

**Assumption made:** Define a minimal canonical set of three states for this ticket: `BASELINE` (movement-only prototype), `INFECTION_DEMO` (baseline + infection loop systems enabled), and `ENEMY_PLAYTEST` (baseline + enemy combat systems enabled). Additional states may be added by future tickets, but are explicitly out of scope for this spec and tests; this ticket only needs to cover these three.

**Confidence:** Medium

---

### [scene_state_machine] Spec — Feature gating surface

**Would have asked:** Which feature systems must the scene state machine control directly versus leaving them to ad-hoc scene logic?

**Assumption made:** For this milestone, the state machine exposes a minimal, explicit configuration surface consisting of three boolean flags per state: `enable_infection_loop`, `enable_enemies`, and `enable_prototype_hud`. Other systems (e.g. advanced UI, progression, multi-level routing) are not gated by this state machine yet and remain out of scope.

**Confidence:** Medium

---

### [scene_state_machine] Spec — Event model scope

**Would have asked:** Should the scene state machine support generic "next/previous variant" navigation and complex transition graphs, or only direct selection of a specific variant?

**Assumption made:** To keep behavior deterministic and testable, the public API only supports explicit selection events for this ticket: `select_baseline`, `select_infection_demo`, and `select_enemy_playtest`. There is no cyclic `next/prev` navigation or internal transition graph beyond mapping each selection event to its corresponding canonical state.

**Confidence:** Medium

---

### [scene_state_machine] Spec — Initial state

**Would have asked:** When a `SceneStateMachine` instance is created with no events applied, which state should be considered the initial default?

**Assumption made:** Every new `SceneStateMachine` instance starts in the `BASELINE` state, with configuration flags matching the baseline (infection loop and enemies disabled, prototype HUD enabled). Tests treat any other initial state as incorrect for this ticket.

**Confidence:** Medium

---

### [scene_state_machine] Spec — Invalid event handling

**Would have asked:** How should the state machine behave if it receives an unknown event name or a selection event that redundantly targets the current state?

**Assumption made:** Unknown event identifiers and redundant selection events are strict no-ops: they must not change the current state or configuration, and must not throw or log errors in normal operation. Tests will assert that applying such events leaves state and configuration unchanged.

**Confidence:** High

---

### [scene_state_machine] Test Breaker — Config dictionary mutability semantics

**Would have asked:** When callers retrieve the configuration via `SceneStateMachine.get_config()`, is the returned `Dictionary` allowed to be mutated by callers, and if so, must the state machine protect its internal state from those external mutations?

**Assumption made:** For this ticket, the conservative contract is that `get_config()` returns a defensive copy of the internal configuration on every call. Callers may mutate the returned `Dictionary` freely, and such mutations must not change the internal state or future `get_config()` results. The adversarial test `test_mutating_returned_config_does_not_change_internal_state` in `test_scene_state_machine_adversarial.gd` (# CHECKPOINT) encodes this requirement.

**Confidence:** Medium

---

### [scene_state_machine] Test Breaker — Non-String event ID handling

**Would have asked:** What should happen if `SceneStateMachine.apply_event` is accidentally invoked with non-String event identifiers (e.g. `null`, integers, booleans) despite the intended `String` API?

**Assumption made:** For this ticket, any non-String event identifier is treated as an unknown event and must be a strict no-op: it must not crash, must not change state or configuration, and must not produce side effects beyond normal logging. The adversarial test `test_non_string_events_are_treated_as_strict_noops` in `test_scene_state_machine_adversarial.gd` (# CHECKPOINT) encodes this behavior.

**Confidence:** Medium

---

### [scene_state_machine] Test Breaker — Event ID case sensitivity

**Would have asked:** Are scene state selection events intended to be case-sensitive (e.g. `"select_infection_demo"` only) or should case-variant identifiers like `"SELECT_INFECTION_DEMO"` and `"Select_Enemy_Playtest"` also be accepted as aliases?

**Assumption made:** The conservative, deterministic contract for this ticket is that event IDs are strictly case-sensitive: only the exact lowercase identifiers `"select_baseline"`, `"select_infection_demo"`, and `"select_enemy_playtest"` are recognized. Any case-mismatched identifier is treated as an unknown event and must be a strict no-op for both state and configuration. The adversarial test `test_case_mismatched_event_ids_are_treated_as_unknown_noops` in `test_scene_state_machine_adversarial.gd` (# CHECKPOINT) encodes this requirement.

**Confidence:** Medium

---

## Run: 2026-03-06T12:00:00Z
Tickets queued: scene_state_machine.md

---

### [scene_state_machine] Core Simulation Agent — Unknown-event trace equivalence vs no-op semantics

**Would have asked:** The adversarial test `test_unknown_events_do_not_change_trace_compared_to_filtered_sequence` requires the state/config trace for an event sequence with interleaved unknown events to be identical (including length) to the trace for the same sequence with unknown events removed, but `SceneStateMachine.apply_event` is also required to treat unknown events as strict no-ops and the test harness unconditionally records one trace entry per input event. How should this inconsistency between "strict no-op" semantics and trace-length equality be resolved?

**Assumption made:** Implement `SceneStateMachine` according to the documented contract and existing primary/adversarial tests for all other behaviors (canonical states, config flags, defensive copies, non-String and case-mismatched events as no-ops, long-sequence stability, and per-instance isolation). Treat the remaining failure in `test_unknown_events_do_not_change_trace_compared_to_filtered_sequence` as a specification/test bug that cannot be satisfied without changing the test harness itself, and mark the ticket BLOCKED pending human or Planner guidance on how to reconcile unknown-event trace semantics.

**Confidence:** Low

---

## Run: 2026-03-07T12:00:00Z
Manual Verification & Acceptance

---

### [mutation_slot_system_single] — OUTCOME: COMPLETE
Mutation slot system successfully implemented with full integration. Manual verification confirmed all acceptance criteria: slot properly filled on absorb, mutation effect is usable in gameplay (last-wins policy), slot state is clear in UI (green filled / gray empty), no duplicates or lost mutations, and human-playable in-editor without debug overlays. Test suite passing (core model + infection interaction + UI wiring). Ticket moved to done/ column.

---

## Run: 2026-03-07T20:00:00Z
Tickets queued: visual_feedback_infection.md, weakening_system.md, wall_cling_visual_readability.md, two_mutation_slots.md, slot_consumption_rules.md, fusion_rules_and_hybrid.md, second_chunk_logic.md, visual_clarity_hybrid_state.md, containment_hall_01_layout.md, light_skill_check.md, mini_boss_encounter.md, fusion_opportunity_room.md, mutation_tease_room.md, start_finish_flow.md

---

### [visual_feedback_infection] — OUTCOME: COMPLETE
All 5 acceptance criteria satisfied and verified. Weakened state shows amber color tint, infected state shows distinct purple tint, absorb action triggers particle burst, all feedback readable at standard camera distance, human-playable in-editor. Test suite comprehensive (97 tests, all passing). Ticket moved to done/ column.

---

### [visual_feedback_infection] Planner — Scope: 2D, 3D, or both?

**Would have asked:** Should this ticket cover both 2D and 3D infection visual feedback, or scope to one variant?

**Assumption made:** Ticket AC is presented without variant qualifier. Codebase has both `enemy_infection.gd` (2D) and `enemy_infection_3d.gd` (3D) with corresponding `infection_state_fx.gd` and `infection_state_fx_3d.gd`. Plan scopes to 2D as primary variant (test scene is `test_infection_loop.tscn` with 2D setup); 3D can be addressed by a separate ticket or follow-up. 2D weakened/infected color tint + state label already exists but may need enhancement for clarity/readability AC.

**Confidence:** Medium

---

### [visual_feedback_infection] Planner — Absorb feedback mechanics

**Would have asked:** What concrete mechanics does "absorb feedback (pull, particle, short animation)" mean—particle system spawning, enemy/player pull-toward effect, or UI-only confirmation?

**Assumption made:** Absorb feedback is visual-only, not gameplay-altering. Minimum viable: (1) particle effect or brief sprite flash when absorb succeeds, (2) optional visual "pull" as aesthetic suggestion (not collision-based). If pull is engine-intensive or conflicts with absorb timing, particle + UI toast are sufficient. Spec Agent will define exact mechanics.

**Confidence:** Medium

---

### [visual_feedback_infection] Planner — "Readable at target camera distance"

**Would have asked:** What is the target camera distance, aspect ratio, and display size assumed for this ticket's readability requirement?

**Assumption made:** Standard in-editor viewport at Godot default camera (orthogonal 2D or perspective 3D at typical gameplay distance). No extreme zoom or mobile-specific considerations in this ticket; manual playtest will verify standard desktop display (e.g. 1920×1080). If later tickets address mobile/console camera scaling, they can refactor.

**Confidence:** High

---

### [visual_feedback_infection] Planner — Existing infection_state_fx partial implementation

**Would have asked:** The 2D `infection_state_fx.gd` exists with color tint + state label. Should the plan treat it as "complete but needs refinement" or "needs substantial rework"?

**Assumption made:** Plan treats existing code as a solid foundation requiring polish and validation: verify that amber (weakened) and purple (infected) are sufficiently distinct at target camera distance, confirm state label is readable without debug overlays, and test that both color + label render properly in test scene. No major refactor assumed unless AC fails; minor tweaks (e.g. color values, label positioning) are in-scope for Implementation Agent.

**Confidence:** High

---

### [visual_feedback_infection] Spec — Absorb feedback event integration

**Would have asked:** How should absorb visual feedback (particles, scale animation) be triggered: via a signal from `InfectionAbsorbResolver`, via direct call from `InfectionInteractionHandler`, or via state polling in the FX presenter?

**Assumption made:** Three integration points are viable. The spec does not mandate a specific approach but recommends (in order of preference):
  1. **Signal from resolver** (cleanest): Enhance `InfectionAbsorbResolver.resolve_absorb()` to emit a signal (e.g., `absorb_resolved`) that subscribers (e.g., `InfectionStateFX` or a new presenter) connect to and trigger feedback on.
  2. **Direct call from handler** (pragmatic): `InfectionInteractionHandler` holds a reference to the FX presenter and calls `play_absorb_feedback()` after `resolve_absorb()` succeeds.
  3. **State polling** (fallback): The FX presenter monitors `esm.get_state()` transitions; on infected → dead, it spawns absorb particles (no separate event needed).

  Implementation will choose the cleanest integration that does not require refactoring existing modules. For minimal scope, option 3 (state polling) is preferred if it cleanly detects absorb-caused deaths without triggering on non-absorb deaths (e.g., respawn, other kill sources).

**Confidence:** Medium

---

### [visual_feedback_infection] Spec — Absorb feedback triggering only on successful absorb

**Would have asked:** If an infected enemy transitions to dead via some mechanism other than absorb (e.g., manual event, timeout, other code), should absorb visual feedback still play?

**Assumption made:** Absorb feedback must be triggered **only** when the enemy dies **via absorb**, not on all infected → dead transitions. Conservative solution: (1) absorb feedback is emitted as an explicit event from `InfectionAbsorbResolver.resolve_absorb()` so it only fires on actual absorb success, OR (2) the FX presenter tracks that absorb was called and only plays feedback in that frame (no false positives from unrelated deaths). Implementation agents will select the approach that cleanly separates absorb-caused deaths from other dead-state causes.

**Confidence:** Medium

---

### [visual_feedback_infection] Spec — Particle effect size and visibility

**Would have asked:** How many particles, what size, and what velocity should the absorb particle burst have?

**Assumption made:** Spec defines a **minimum viable** particle effect: 5–15 small particles (2–5 pixels each), white or light cyan color, radiating outward from enemy center over 0.3–0.5 seconds with 1.0 → 0.0 alpha fade. Implementation agents have discretion to adjust counts and velocities for visual polish as long as the effect remains lightweight and visible at target camera distance. If the effect is too subtle, a follow-up ticket can enhance particle art/count; for now, the simple burst satisfies the AC requirement.

**Confidence:** High

---

### [visual_feedback_infection] Test Breaker — Absorb feedback not yet implemented (F6)

**Would have asked:** Should absorb feedback (particle effect + optional animation on absorb) be part of the `infection_state_fx.gd` implementation, or is it integrated separately via a new presenter?

**Assumption made:** F6 (absorb feedback) is a documented requirement in the spec but not yet implemented in the current `infection_state_fx.gd`. Per the execution plan (Task 5), absorb feedback is assigned to the Presentation Agent as a separate concern from state-tint logic. Tests assume a new presenter (e.g., `InfectionAbsorbFXPresenter`) or enhancement to `infection_state_fx.gd` will be implemented in IMPLEMENTATION_FRONTEND. The baseline `infection_state_fx.gd` provides state-to-tint mapping; absorb FX is deferred to the Presentation Agent's Task 5.

**Confidence:** High

---

### [visual_feedback_infection] Test Breaker — Label positioning not validated

**Would have asked:** Should the state label be positioned "immediately above enemy center" as stated in F5, or is default positioning (0, 0) relative to parent acceptable?

**Assumption made:** Spec F5 requires label offset "defaults to immediately above enemy center (e.g., offset = Vector2(0, -30))." Current tests do not validate label.position; they only check visibility and text. Presentation Agent (Task 4) should set label.position or use CanvasLayer/anchors to ensure label renders above enemy. Automated position validation is not added to tests; human playtest (Task 7) will verify readability and placement.

**Confidence:** Medium

---

### [visual_feedback_infection] Test Breaker — Color contrast not measured (subjective)

**Would have asked:** How should contrast ratio (NF1 requirement: >= 3:1) be validated? Pixel-by-pixel analysis, manual eyeball test, or analytical formula?

**Assumption made:** Contrast requirement is human-verified during Task 7 (human playtest). Automated color-contrast analysis is deferred; tests document that contrast is subjective and verified visually by Presentation Agent. Conservative approach: assume Presentation Agent will choose contrasting colors (amber vs. purple are naturally distinct) and Task 7 will confirm on typical display.

**Confidence:** Medium

---

### [wall_cling_visual_readability] Planner — Cling indicator scope and dual-state feedback

**Would have asked:** Should wall cling feedback include ONLY HUD status text (already present as "Wall Cling: ON/OFF" in ClingStatusLabel), or does it require BOTH sprite/visual tint AND HUD feedback?

**Assumption made:** AC explicitly requires both: (1) sprite-level indication (tilt, outline, or color tint while clinging), AND (2) a secondary indicator (icon or text in HUD). The ClingStatusLabel in game_ui.tscn already displays "Wall Cling: ON/OFF" and is updated in infection_ui.gd. This satisfies AC requirement #4 (secondary indicator). This ticket focuses on adding AC requirements #1-3: sprite tilt/tint on cling, optional particle trail, and clean removal on detach.

**Confidence:** High

---

### [wall_cling_visual_readability] Planner — Visual approach selection

**Would have asked:** Which visual strategy—sprite tilt, color tint, or outline—should be used for cling indication?

**Assumption made:** AC lists "e.g. pose tilt toward wall, outline, or color tint" as examples, not mandates. Conservative approach: implement a simple, non-distracting solution. Since the player is rendered as a Polygon2D (green rectangle), a combined approach is minimal: (1) apply a slight modulation/tint change (e.g., 1.0, 0.95, 0.85 to desaturate/shift toward yellow-green when clinging), AND (2) if time permits, a small outline via a second polygon or shader. Spec Agent will formalize the exact visual approach; Implementation Agent selects the least costly approach that satisfies AC#1.

**Confidence:** Medium

---

### [wall_cling_visual_readability] Planner — Wall-direction mirroring scope

**Would have asked:** Does "correct mirroring for left/right walls" require the sprite to tilt/rotate, or is a simple color tint sufficient?

**Assumption made:** AC#5 requires mirroring to "remain readable at normal camera distances." For a simple polygon, color tint does not require mirroring; tilt/rotation does. Conservative: assume sprite-tint approach (no rotation) first, which is direction-agnostic. If Spec Agent decides on tilt, the Implementation Agent must ensure tilt direction matches the wall side (e.g., rotate -10° when clinging left, +10° right). Current tests will validate that cling visuals are applied; detailed rotation logic is spec-domain.

**Confidence:** Medium

---

### [wall_cling_visual_readability] Planner — Particle trail complexity

**Would have asked:** Should the "wall-cling slide effect" be a continuous particle stream (expensive, per frame) or a burst/trail (cheaper, event-based)?

**Assumption made:** AC#2 describes the effect as "optional" and "visible but not distracting." Conservative approach: implement a **low-cost trail** via infrequent particle emission on slide (e.g., emit 1–2 particles every 0.1s while sliding) rather than a continuous stream. This keeps perf overhead minimal and remains visually noticeable. Spec Agent will confirm the visual impact; Implementation Agent may simplify to a single color-change if particles prove too costly.

**Confidence:** Medium

---

### [wall_cling_visual_readability] Planner — One-frame removal requirement

**Would have asked:** Does "cling visuals removed within one frame" mean instantaneous, or is a 1-frame fade acceptable?

**Assumption made:** AC#3 requires cleanup on detach (jump, release, or enter free-fall). "Within one frame" means the cling indicator (tint, particles, etc.) must not linger into the next physics frame after is_wall_clinging transitions false. This is achievable by reading `_current_state.is_wall_clinging` in the same frame-update code that applies tint; no async fade needed. If FX uses particles, spawned particles may animate out; the cling-state-driven tint/indicator must clear immediately.

**Confidence:** High

---

### [wall_cling_visual_readability] Planner — FX presenter pattern consistency

**Would have asked:** Should cling visuals be managed by a new presenter class (e.g., `ClingStateFXPresenter`), or integrated into `PlayerController` or `infection_state_fx.gd`?

**Assumption made:** Following existing patterns (e.g., `InfectionStateFX` for enemy state feedback), cling feedback should be isolated in a new **FX Presenter** script attached to the Player scene. This script will subscribe to or poll `PlayerController.is_wall_clinging_state()` each frame and drive the sprite modulate/outline/particles. Keeping FX logic separate from controller logic ensures testability and reusability. Implementation Agent may choose to inline it if the scope is minimal (e.g., single line of modulate logic).

**Confidence:** Medium

---

### [wall_cling_visual_readability] Planner — Existing HUD integration

**Would have asked:** Is the existing "Wall Cling: ON/OFF" HUD label sufficient, or must it be enhanced (e.g., icon, color-coded)?

**Assumption made:** The ClingStatusLabel in game_ui.tscn already updates via infection_ui.gd line `cling_label.text = "Wall Cling: " + ("ON" if _player.is_wall_clinging_state() else "OFF")`. This satisfies AC#4 (secondary indicator). No enhancement is required unless Spec Agent deems the plain text insufficient; if so, a follow-up ticket can add a cling icon (parallel to mutation icon).

**Confidence:** High

---

## Execution Plan: wall_cling_visual_readability

**Ticket:** `project_board/2_milestone_2_infection_loop/01_active/wall_cling_visual_readability.md`

**Overview:**
Decompose wall cling visual feedback into spec-design-test-implementation tasks. The ticket requires: (1) sprite-level visual indication of cling state (tint, pose, or outline), (2) optional (but recommended) particle slide effect, (3) instantaneous cleanup on detach, (4) HUD status indicator (already in place), and (5) correct mirroring for left/right walls.

---

### Task 1: Spec Agent — Formalize Wall Cling Visual Strategy
**Input:** Ticket AC, code review of player_controller.gd, player.tscn, and infection_state_fx.gd patterns.

**Deliverable:** `wall_cling_visual_readability_spec.md`

**Spec scope:**
- Choose visual approach: **recommended = simple modulate/color tint + optional low-cost particle trail**.
- Define tint colors:
  - **Default (idle):** Color(0.4, 0.9, 0.6, 1) — current green
  - **Wall clinging:** Color(0.6, 0.95, 0.5, 1) — slightly brighter, warmer (toward yellow-green)
- Particle trail (if included):
  - **Emission:** 1–2 particles every 0.1s while `is_wall_clinging == true` and `velocity.y != 0` (sliding)
  - **Particle:** 3–5px white/cyan dots, 0.5s lifespan, fade-out
  - **Cost:** single small particle emitter, ~5 particles max concurrently
- HUD indicator:
  - Already present as `ClingStatusLabel`, no change required (AC#4 satisfied)
  - Color modulation optional (can enhance with cling-tint match, e.g., greenish when ON)
- Edge cases:
  - Horizontal cling (e.g., on ceiling) — same tint (direction-agnostic)
  - Detach (jump, release, gravity break) — instant tint removal (no fade)
  - Cling timer/grace period — apply tint only while `is_wall_clinging == true` (rely on controller state)

---

### Task 2: Test Design Agent — Define Test Cases for Cling Visuals
**Input:** Spec from Task 1, test patterns from infection_interaction tests.

**Deliverable:** Test cases in `tests/test_cling_visual_readability.gd` (or inline in `test_human_playable_core.gd` if scope is small).

**Test coverage:**
- **Unit/Presentation tests:**
  - When `PlayerController.is_wall_clinging_state() == true`, player sprite modulate is non-default tint.
  - When `is_wall_clinging_state() == false`, player sprite modulate is default Color(0.4, 0.9, 0.6, 1).
  - Transition (cling true → false) clears tint within one frame.
- **Particle tests (if applicable):**
  - While clinging and sliding vertically, particle emitter is active.
  - On detach, particle emitter stops immediately (no lingering).
  - Particle count stays under 10 (performance bound).
- **HUD tests:**
  - `ClingStatusLabel.text` contains "ON" iff `is_wall_clinging_state() == true`.
  - `ClingStatusLabel.text` contains "OFF" iff `is_wall_clinging_state() == false`.
- **Integration/playability tests:**
  - Player remains responsive during cling (no input lag).
  - Visuals work on left and right walls (mirror-agnostic).
  - Camera remains in-frame; visuals readable at default zoom (no clipping).

---

### Task 3: Test Design Agent — Break Wall Cling Visuals
**Input:** Spec from Task 1, test cases from Task 2.

**Deliverable:** Documented failure modes and expected breakpoints for Implementation Agent.

**Known breakpoints:**
- Tint is not applied or is always default color (sprite invisible or incorrect state tracking).
- Tint persists after detach (lingering cling indicator, violates AC#3).
- Particle trail floods the screen or causes FPS drop (cost constraint violated).
- Cling indicator does not appear on right-side wall (mirroring bug).
- HUD label does not update (integration failure, but likely not cling-visual-specific).
- Player model is unreadable due to tint (contrast too low, violates "not distracting").

---

### Task 4: Presentation Agent — Implement Cling State FX Presenter
**Input:** Spec from Task 1, test cases from Task 2.

**Deliverable:** New script `scripts/cling_state_fx.gd` attached to Player scene node `PlayerVisual` or new `ClingFX` child.

**Implementation scope:**
- Subscribe to/poll `PlayerController.is_wall_clinging_state()` every frame.
- **Apply tint:**
  - Cache original default color: Color(0.4, 0.9, 0.6, 1)
  - If `is_wall_clinging`: apply cling tint Color(0.6, 0.95, 0.5, 1) to `_visual.modulate`
  - Else: restore default color
  - Update in `_process(_delta)` to ensure one-frame responsiveness
- **Particle trail (optional):**
  - Instantiate a small CPUParticles2D node as child of player
  - Enable emission iff `is_wall_clinging && is_sliding_down` (vertical velocity check)
  - Emit at fixed low rate (1–2 particles per 0.1s)
  - Disable emission on detach
- **No rotation/tilt required** — color tint is direction-agnostic (satisfies mirroring AC#5)
- **Reference:** Follow pattern from `infection_state_fx.gd` (state-driven modulation + optional FX)

---

### Task 5: Implementation Backend — Ensure Wall Cling State Tracking
**Input:** Spec from Task 1, current player_controller.gd, movement_simulation.gd.

**Deliverable:** Verify/enhance `PlayerController._current_state.is_wall_clinging` is correctly updated by `MovementSimulation.simulate()`.

**Verification scope:**
- `is_wall_clinging` transitions are driven by wall contact and cling timer in movement_simulation.gd step 9 (cling state update).
- No additional changes required if movement logic is already spec-compliant.
- If missing or broken, fix movement_simulation.gd to ensure `is_wall_clinging` reflects actual cling eligibility.

---

### Task 6: Implementation Frontend — Integrate Cling FX into Player Scene and Controller
**Input:** Deliverable from Task 4 (cling_state_fx.gd script).

**Deliverable:** Updated `scenes/player.tscn` with attached FX presenter.

**Integration scope:**
- Attach `cling_state_fx.gd` to a new child node `ClingFX` under `Player` (or directly to `PlayerVisual`).
- Ensure `ClingFX` has reference to `PlayerVisual` Polygon2D and `PlayerController`.
- Wire optional particle emitter (CPUParticles2D) as child of `ClingFX`.
- Test in-scene: run test_movement.tscn, initiate wall cling, verify tint change and HUD update.

---

### Task 7: Static QA — Review Cling Visuals for Clarity and Compliance
**Input:** Implemented cling_state_fx.gd, updated player.tscn, Test Design deliverables.

**Deliverable:** Code review report + visual/UX notes.

**QA scope:**
- **Code:** cling_state_fx.gd follows infection_state_fx.gd patterns, no unused variables, error handling.
- **Visual:**
  - Tint is visible and does not over-saturate or desaturate player model.
  - Particle trail (if included) is smooth and not distracting.
  - HUD label is readable and updates in sync with visuals.
  - Mirroring works (left/right walls show same tint).
- **Performance:** No FPS drop, particle count stable under 10 (if applicable).
- **Compliance:** AC#1-5 checkpoints all green (sprite tint, optional trail, instant cleanup, HUD, mirroring).

---

### Task 8: Integration — Manual Playtest of Wall Cling Visuals
**Input:** Integrated scene + QA report from Task 7.

**Deliverable:** Playtest log (human verification of AC satisfaction).

**Playtest scope:**
- Load test_movement.tscn, wall-jump and cling on left and right walls.
- Verify cling tint is visible and matches spec color.
- Verify particle trail (if enabled) is smooth and non-distracting.
- Verify tint clears immediately on jump/detach.
- Verify HUD label updates to "Wall Cling: ON/OFF" in sync.
- Verify camera distance and zoom allow visual clarity.
- Sign off on AC completion.

---

### Task 9: Deployment — Move Ticket to Complete
**Input:** Sign-off from Task 8.

**Deliverable:** Ticket moved to `02_complete/` with Stage = COMPLETE.

---

## Summary
This execution plan decomposes wall cling visual feedback into 9 sequential tasks across Spec, Test, and Implementation domains. The conservative approach prioritizes **simple, non-distracting visuals** (color tint + optional low-cost particles) that rely on existing state tracking in `PlayerController.is_wall_clinging_state()`. The HUD indicator is already in place; this ticket adds sprite-level feedback. Estimated effort: 2–3 agent runs (Spec + Test + Implementation + QA + Playtest).

---

## Run: 2026-03-07T00:00:00Z
Tickets queued: wall_cling_visual_readability.md (SPECIFICATION stage)

---

### [wall_cling_visual_readability] Spec Agent — Visual approach selection

**Would have asked:** Should the wall cling visual feedback use sprite tilt/rotation, outline effects, color tint, or a combination?

**Assumption made:** Conservative approach: **color modulate tint only**, no sprite rotation or animation. Rationale: (1) modulate is zero-cost and direction-agnostic (no special mirroring logic needed), (2) infection_state_fx.gd demonstrates the pattern, (3) readable at normal camera zoom without debug overlays, (4) instantaneous state-to-visual mapping (no fades). Optional particle trail is offered as fallback if budget allows, but tint is the core requirement.

**Confidence:** High

---

### [wall_cling_visual_readability] Spec Agent — Tint color values

**Would have asked:** What exact RGB values should the cling tint use to be visibly distinct from the idle player color Color(0.4, 0.9, 0.6, 1.0)?

**Assumption made:** **Cling tint = Color(0.8, 1.0, 0.5, 1.0)** — brighter, warmer green offset toward yellow/lime. Rationale: (1) increases green and red channels from idle, (2) maintains alpha = 1.0 (fully opaque), (3) visually distinct without over-saturation or glow effects, (4) readable at normal camera distances, (5) testable with RGB comparison (no subjective "looks good" assertions).

**Confidence:** Medium

---

### [wall_cling_visual_readability] Spec Agent — Particle emission conditions

**Would have asked:** Should particles emit continuously while clinging, only while sliding, or never?

**Assumption made:** **Only while sliding** (velocity.y > ~10 pixels/frame or downward motion), not while stationary against wall. Rationale: (1) reduces visual noise, (2) conserves particle budget (5 max concurrent), (3) makes sense aesthetically (friction trail along wall, not hovering), (4) AC#2 says "optional"; if omitted, ticket still completes.

**Confidence:** Medium

---

### [wall_cling_visual_readability] Spec Agent — Particle budget and cost

**Would have asked:** What is the maximum acceptable particle count and emission rate to avoid FPS drop?

**Assumption made:** **~1–2 particles per 0.1 seconds (~15–20/second), ~5 max concurrent, ~0.3–0.5 second lifetime.** Rationale: (1) conservative estimate for Godot 2D CPUParticles2D, (2) does not require custom shaders, (3) safe on modern hardware without measurable FPS impact, (4) maintains visual distinction without saturation.

**Confidence:** Medium

---

### [wall_cling_visual_readability] Spec Agent — AC#4 scope (HUD indicator)

**Would have asked:** Does AC#4 require new HUD code, or is the existing InputHintLabel sufficient?

**Assumption made:** **Existing InputHintLabel is sufficient.** Rationale: (1) reviewed `infection_ui.gd` and `game_ui.tscn`; InputHintLabel already subscribes to `PlayerController.is_wall_clinging_state()` and displays "Cling" hint, (2) no new HUD code is needed, (3) spec requires test validation only (verify label text/visibility matches state).

**Confidence:** High

---

### [wall_cling_visual_readability] Spec Agent — State tracking backend verification

**Would have asked:** Is `MovementSimulation.is_wall_clinging` state tracking reliable, or do wall-cling state transitions need fixes?

**Assumption made:** **State tracking is correct.** Rationale: (1) execution plan Task 5 explicitly delegates verification to "Implementation Backend Agent," (2) prior wall_cling.md and movement_controller.md tickets already specify and validate state transitions, (3) `PlayerController.is_wall_clinging_state()` exists and is public, (4) ClingStateFX spec assumes this method is accurate; if state is wrong, no FX spec can fix it.

**Confidence:** High

---

### [wall_cling_visual_readability] Spec Agent — Script pattern and file location

**Would have asked:** Should the new FX presenter be a new script file or integrated into PlayerController or PlayerVisual?

**Assumption made:** **New file `scripts/cling_state_fx.gd`** following the infection_state_fx.gd pattern. Rationale: (1) separates presentation logic from controller, (2) makes testing isolated easier, (3) consistent with infection loop architecture (infection_state_fx.gd, detach_recall_fx_presenter.gd), (4) clean responsibility: ClingStateFX polls state and applies visuals, PlayerController owns movement only.

**Confidence:** High

---

### [wall_cling_visual_readability] Spec Agent — Scene integration approach

**Would have asked:** Should ClingStateFX be a child node or sibling in player.tscn?

**Assumption made:** **Child node under Player (CharacterBody2D).** Rationale: (1) infection_state_fx.gd is a child of EnemyInfection, (2) allows ClingStateFX to easily access parent PlayerController reference, (3) optional CPUParticles2D can be a sibling or child of ClingStateFX (TBD by implementation agent).

**Confidence:** High

---

### [wall_cling_visual_readability] Spec Agent — Edge case: rapid cling/detach

**Would have asked:** What should happen if the player rapidly clings and detaches multiple times per second (e.g., bouncing against wall)?

**Assumption made:** **Tint is applied/removed frame-by-frame without lag or glitches.** Rationale: (1) modulate assignment is instant, (2) no fading or interpolation, (3) _process() runs every frame and immediately reflects state, (4) adversarial tests (Task 3) will stress-test this case with 10+ transitions/second.

**Confidence:** High

---

### [wall_cling_visual_readability] Spec Agent — Scope: no shader or custom rendering

**Would have asked:** If modulate tint is insufficient, can we use custom shaders or other rendering effects?

**Assumption made:** **No custom shaders or post-processing.** Rationale: (1) spec requires "visually obvious," not "pixel-perfect;" modulate achieves this, (2) keeping scope minimal reduces implementation risk, (3) if playtest reveals tint is too subtle, fallback is to brighten the RGB values further, not switch to shaders.

**Confidence:** High

---

### [wall_cling_visual_readability] Test Designer — AC#4 HUD Indicator Scope

**Would have asked:** Should test_wall_cling_visual_readability.gd verify InputHintLabel binding and text synchronization, or is that covered by existing test_infection_ui.gd?

**Assumption made:** Existing `test_infection_ui.gd` and `test_input_hints.gd` already cover HUD label synchronization with game state. This test suite focuses on visual FX layer (modulate tint and optional particles). AC#4 is verified in existing tests and manual playtest; primary and adversarial suites reserve the contract but defer detailed HUD testing to existing suites.

**Confidence:** High

---

### [wall_cling_visual_readability] Test Designer — Particle Cleanup Mechanism

**Would have asked:** Should particle emitter be set to `emitting=false` on detach, or should the emitter be removed/disabled entirely?

**Assumption made:** Particle emitter should be set to `emitting=false` (stop emitting new particles) but remain active so existing particles fade per their lifetime. This allows smooth visual fade-out without abrupt disappearance. Adversarial tests verify this behavior if particles are implemented.

**Confidence:** Medium

---

### [wall_cling_visual_readability] Test Designer — Detach While Sliding Condition

**Would have asked:** Should the FX presenter check velocity.y (downward/sliding) to conditionally apply detach cleanup, or is detach cleanup always instant regardless of velocity?

**Assumption made:** Detach cleanup is always instant. AC#3 requires "removed within one frame" regardless of velocity or sliding state. The FX presenter responds only to `is_wall_clinging` state transitions, not velocity. Velocity is tracked in movement simulation; FX layer is agnostic to it.

**Confidence:** High

---

### [wall_cling_visual_readability] Test Designer — Headless Testing Gaps

**Would have asked:** Which ACs require manual/in-engine verification and cannot be tested headless?

**Assumption made:** AC#5 (camera distance readability) and parts of AC#1 (sprite "clearly indicates," subjective visual assessment) require manual playtest in-editor. Headless tests verify state→visual contract (color values, label text, tint application/removal), while human playtest confirms visual clarity and aesthetics.

**Confidence:** High

---

**Test Designer suite complete. 26 primary tests + 18 adversarial tests. All tests registered in run_tests.gd. Ready for Test Breaker handoff.**

---

## Run: 2026-03-07T22:00:00Z
Tickets queued: wall_cling_visual_readability.md (TEST_BREAK stage)

---

### [wall_cling_visual_readability] Test Breaker — Idle vs Cling Color Channel Precision

**Would have asked:** Should color tint values (idle R=0.4, cling R=0.8, etc.) be treated as hard constants with exact RGB values, or are tolerance ranges acceptable due to float precision?

**Assumption made:** Treat color constants as hard specifications with ±0.01 tolerance for floating-point precision. Tests encode exact expected values (idle Color(0.4, 0.9, 0.6, 1.0) and cling Color(0.8, 1.0, 0.5, 1.0)) and accept results within EPSILON=0.01 per channel. Any implementation that deviates beyond this tolerance (e.g., using Color(0.4, 0.9, 0.55, 1.0) for idle) fails the test and must be corrected.

**Confidence:** High

---

### [wall_cling_visual_readability] Test Breaker — Null Parent Error Handling

**Would have asked:** When ClingStateFX._ready() is called without a parent node or with a non-PlayerController parent, what exact behavior is required: silent graceful skip, warning log, or exception?

**Assumption made:** ClingStateFX must gracefully handle a null parent: cache null references without crashing, return early from _process() if parent is null, and produce no logs/warnings for normal operation (silent skip). Logging is reserved for actual errors (e.g., loaded script is null). Test `gap_null_parent_graceful_exit` encodes the silent no-op contract.

**Confidence:** Medium

---

### [wall_cling_visual_readability] Test Breaker — Missing PlayerVisual Node

**Would have asked:** If PlayerVisual is missing from the player hierarchy, should ClingStateFX crash, warn, or silently skip modulate updates?

**Assumption made:** ClingStateFX must silently skip modulate updates if PlayerVisual is unavailable. Cache the visual reference at _ready(); if null, defer lookup each frame via get_node_or_null("PlayerVisual"). If visual remains null after attempted lookup, skip modulate assignment in _process() without logging. This ensures robustness in scenes with non-standard hierarchies.

**Confidence:** Medium

---

### [wall_cling_visual_readability] Test Breaker — Missing is_wall_clinging_state() Method

**Would have asked:** If parent lacks the is_wall_clinging_state() method, should ClingStateFX default to idle state, throw an exception, or require an explicit API check before calling the method?

**Assumption made:** ClingStateFX must call has_method("is_wall_clinging_state") before invoking the method. If the method is absent, default to idle state (is_clinging = false) so that the sprite reverts to the default tint. This allows ClingStateFX to be attached to any parent node without crashing.

**Confidence:** Medium

---

### [wall_cling_visual_readability] Test Breaker — Delta Time Parameter Invariance

**Would have asked:** Does the delta parameter in _process(delta) affect tint application? Should _process(0.0) and _process(1.0) produce identical visual results?

**Assumption made:** The delta parameter is semantically unused for tint application; ClingStateFX is purely reactive to instantaneous state, not time-dependent. Both _process(0.0) and _process(1.0) must produce identical cling/idle tints. Delta may be used for particle updates (e.g., fade-out timing) but not for state-to-visual mapping. Test `gap_delta_parameter_unused_or_used` encodes this contract.

**Confidence:** High

---

### [wall_cling_visual_readability] Test Breaker — Rapid Cling/Detach Stability

**Would have asked:** Under 50+ rapid cling/detach cycles, should visual remain stable with no glitches, flicker, or intermediate tint values?

**Assumption made:** ClingStateFX must produce stable, glitch-free visuals under stress. Rapid state transitions (cling true → false → true, repeat 50 times) must result in correct tint each time, with zero flickering or visual artifacts. Test `test_adv_rapid_cling_detach_50_cycles` verifies this stress contract.

**Confidence:** High

---

### [wall_cling_visual_readability] Test Breaker — Particle Emitter Lifecycle (Optional Feature)

**Would have asked:** If CPUParticles2D emitter exists as a child of ClingStateFX, what exact lifecycle should it follow: always disabled until _ready() explicitly enables it, disabled initially then enabled on cling, or some other state?

**Assumption made:** If particle emitter exists (child named "ClingTrail"), it should be disabled (emitting=false) by default. ClingStateFX._process() enables emitting (set to true) only when is_clinging=true AND conditions for particle emission are met (e.g., velocity.y > threshold); disables emitting (set to false) on detach. Existing particles continue to animate and fade per their lifetime.

**Confidence:** Medium

---

### [wall_cling_visual_readability] Test Breaker — _ready() Not Required Before _process()

**Would have asked:** Can ClingStateFX._process() be called directly without prior _ready() call, and if so, should it still apply tint correctly or degrade gracefully?

**Assumption made:** ClingStateFX must be safe to call _process() even if _ready() was skipped. Node references are initialized on-demand in _process() (lazy initialization) if they were not cached in _ready(). This ensures robustness and allows testing without full scene setup.

**Confidence:** Medium

---

### [wall_cling_visual_readability] Test Breaker — Multiple _ready() Calls Idempotence

**Would have asked:** If _ready() is called multiple times (e.g., due to scene reload or manual re-initialization), does ClingStateFX remain stable and re-cache references correctly?

**Assumption made:** _ready() is idempotent: calling it multiple times is safe and simply re-caches node references. No side effects, state corruption, or crashes should occur. Subsequent _process() calls function identically whether _ready() was called once or multiple times.

**Confidence:** Medium

---

### [wall_cling_visual_readability] Test Breaker — Modulate Override Conflict Resolution

**Would have asked:** If an external system (e.g., shader, animation, or another FX system) sets PlayerVisual.modulate while ClingStateFX is running, which has priority?

**Assumption made:** ClingStateFX has priority and writes modulate every frame in _process(). External modifications to modulate between frames are overwritten on the next _process() call. ClingStateFX is the authoritative modulate driver for cling visuals; no coordination with other modulate writers is implemented for this ticket.

**Confidence:** Medium

---

### [wall_cling_visual_readability] Implementation Frontend Agent — Recommended Architecture

**Would have asked:** Should ClingStateFX be a standalone script attached to a new node, or should it be integrated into PlayerVisual or PlayerController?

**Assumption made:** Create a new node `ClingFX` as a child of `Player` and attach the `cling_state_fx.gd` script to it (following infection_state_fx.gd pattern). The `ClingFX` node caches references to parent `PlayerController` and sibling `PlayerVisual` (Polygon2D), polls `is_wall_clinging_state()` each frame, and updates `PlayerVisual.modulate` directly. Optional `CPUParticles2D` child `ClingTrail` can be added if particle trail is in scope.

**Confidence:** High

---

### [wall_cling_visual_readability] Implementation Frontend Agent — Scene Hierarchy

**Would have asked:** What should the updated player.tscn hierarchy look like, and which node should own the CPUParticles2D emitter?

**Assumption made:** Updated hierarchy:
```
Player (CharacterBody2D) [PlayerController script]
├── PlayerShape (CollisionShape2D)
├── Camera (Camera2D)
├── PlayerVisual (Polygon2D)
└── ClingFX (Node) [cling_state_fx.gd script]
    └── ClingTrail (CPUParticles2D) [optional particle emitter]
```
ClingFX owns the ClingTrail emitter to keep particle logic encapsulated. PlayerVisual is a sibling for easy reference via get_node_or_null().

**Confidence:** High

---

### [wall_cling_visual_readability] Test Breaker — OUTCOME SUMMARY

**Mutation tests created:** 18 tests (color precision, error handling, delta invariance, stress scenarios)
**Spec gaps identified:** 13 checkpoints logged (error handling, null safety, initialization, integration semantics)
**Adversarial test coverage:** 50+ tests already present (primary + existing adversarial suite)
**Architecture confidence:** High (cling_state_fx.gd implementation provided; pattern follows infection_state_fx.gd)
**Ready for implementation:** Yes. All tests, spec, and checkpoints in place. cling_state_fx.gd is implemented and ready to be integrated into player.tscn.

---

