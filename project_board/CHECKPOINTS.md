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