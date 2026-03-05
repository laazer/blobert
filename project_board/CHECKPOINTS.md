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
