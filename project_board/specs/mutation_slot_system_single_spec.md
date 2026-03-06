# Mutation Slot System (Single Slot) — Functional and Non-Functional Specification

**Ticket:** mutation_slot_system_single.md  
**Epic:** Milestone 2 – Infection Loop  
**Revision:** 1 (Spec Agent)

---

## 1. Scope and Assumptions

- **Scope:** Introduce a single active mutation slot layered on top of the existing infection and mutation system. The slot tracks one currently active mutation (by ID) granted via absorbs, exposes its state and active mutation to gameplay/UI, and guarantees no duplicate or lost mutations in normal flow. This ticket does not introduce multi-slot selection, persistence across scenes, or new mutation types beyond those already defined for the infection loop.
- **Assumptions (from `[mutation_slot_system_single]` checkpoints):**
  - The mutation slot system is a thin layer over `MutationInventory`: absorbs continue to grant mutations into `MutationInventory`, and the slot tracks which single mutation ID is currently active/equipped; the slot never owns data independently of the inventory.
  - The slot represents a persistent, always-on mutation once filled. Using the mutation expresses its effect (passive or repeatable ability) but does **not** automatically clear the slot; the slot is changed only when a new mutation is equipped or when reset/cleared explicitly by systems or tests.
  - When the player gains multiple mutations over time, the active slot always tracks the most recently granted compatible mutation (last-wins). Inventory may contain a history of granted mutations; the slot exposes only one active mutation at a time.
  - Slot contents and effects are scoped to the current play session/scene. Save/load or cross-level persistence is out of scope.
- **Additional assumptions:**
  - For this milestone there is effectively one concrete mutation ID already used by the infection system (see `InfectionAbsorbResolver.DEFAULT_MUTATION_ID`). The slot must still be expressed in terms of generic mutation IDs to allow future extension.
  - Existing mutation gameplay effect semantics from the `infection_interaction` ticket remain authoritative. The slot reflects which mutation is active; it does **not** introduce new effect types or complexity beyond what is already defined.
- **Scope boundaries:**
  - In scope: pure-logic slot model and invariants; integration with `MutationInventory` and absorb flow; UI exposure of slot state and active mutation identity; minimal linkage between slot state and the already-implemented mutation effect so that the effect is clearly "usable in gameplay" while the slot is filled.
  - Out of scope: multiple simultaneous slots or builds, persistence across scenes, in-game mutation selection menus, respec flows, or advanced stacking/combination rules.

---

## Requirement SLOT-1 — Single active mutation slot data model

### 1. Spec Summary

- **Description:** Define a deterministic, pure-logic data model representing a **single active mutation slot** that can be empty or filled with exactly one mutation ID. The slot provides a small API to query whether it is filled, which mutation is active, and to reset/clear the slot when needed. It is designed to be testable in isolation (no Node or scene dependencies).
- **Constraints:**
  - The slot is implemented as a pure-logic object (e.g. `MutationSlot` extending `RefCounted` or `Object`), not tied to Nodes or scenes.
  - The slot stores at most **one** mutation ID at a time; it does not track counts or historical lists.
  - All mutation IDs are represented as `String`, consistent with `InfectionAbsorbResolver.DEFAULT_MUTATION_ID`.
  - Slot state transitions are explicit and finite: `EMPTY` and `FILLED(mutation_id)`.
- **Assumptions:** Tests and gameplay may construct and drive a `MutationSlot` instance directly; scene-level systems will hold references or accessors to the same slot instance created for the player.
- **Scope:** Pure logic only; integration with `MutationInventory` and gameplay/UI is covered in SLOT-2 and SLOT-3.

### 2. Acceptance Criteria

- **AC-SLOT-1.1:** A pure-logic class exists (e.g. `MutationSlot`) with no Node, scene, or singleton dependencies; it can be instantiated in tests without loading scenes.
- **AC-SLOT-1.2:** The class exposes, at minimum:
  - `is_filled() -> bool` — returns `true` if and only if the slot currently holds a mutation ID.
  - `get_active_mutation_id() -> String` — returns the active mutation ID when filled; returns an empty string or a documented sentinel when empty.
  - `clear() -> void` — transitions the slot to `EMPTY` regardless of previous contents.
- **AC-SLOT-1.3:** Immediately after construction or `clear()`, `is_filled()` returns `false` and `get_active_mutation_id()` returns the documented empty value.
- **AC-SLOT-1.4:** Setting/filling the slot with a mutation ID makes `is_filled()` return `true` and `get_active_mutation_id()` return exactly that ID.
- **AC-SLOT-1.5:** All slot operations are deterministic and side-effect free beyond updating the slot’s own internal state; repeated reads of `is_filled()` and `get_active_mutation_id()` with no intervening writes always return the same values.

### 3. Risk & Ambiguity Analysis

- **Risk:** Over-designing the slot (e.g. adding stacks, priorities, or cooldowns) would expand scope and make tests brittle.
  - **Mitigation:** This requirement limits the slot to a single ID with trivial semantics (empty or filled).
- **Risk:** Using an empty string sentinel for "no active mutation" could collide with a future legitimate mutation ID.
  - **Mitigation:** AC-SLOT-1.2 requires the behavior to be documented; tests will assert exact behavior so that any future change to the sentinel is explicit.

### 4. Clarifying Questions

- None beyond the stated assumptions; any richer state machine or multi-slot design is explicitly deferred to future tickets.

---

## Requirement SLOT-2 — Integration with `MutationInventory` and absorb flow

### 1. Spec Summary

- **Description:** The single mutation slot is a thin, authoritative view over the mutations granted via the existing `MutationInventory`. Whenever an absorb successfully grants a mutation, the slot is updated in a **last-wins** fashion: it becomes filled with the latest granted compatible mutation ID. The slot never references a mutation ID that is not present in the inventory, and inventory/slot state never diverges in normal game flow.
- **Constraints:**
  - Absorb logic remains centralized in `InfectionAbsorbResolver.resolve_absorb(esm, inv)`, which already grants exactly one mutation via `inv.grant(DEFAULT_MUTATION_ID)` when absorb is valid.
  - Integration must be implemented in a way that preserves the pure-logic nature of both `MutationInventory` and the slot (e.g. the resolver or a small coordinator object calls into both `inv.grant(id)` and `slot.on_mutation_granted(id)`).
  - The slot **must not** own its own separate mutation history; it reflects the active choice over inventory state.
- **Assumptions:**
  - For this milestone, all mutations granted via `InfectionAbsorbResolver` are considered compatible with the slot; no "incompatible" mutation types exist yet.
  - There is still exactly one grant per successful absorb and no grants when absorb is invalid, as enforced by the infection interaction spec and tests.
- **Scope:** Pure logic and gameplay wiring responsible for updating the slot in lockstep with `MutationInventory`.

### 2. Acceptance Criteria

- **AC-SLOT-2.1:** When the game starts (before any absorbs), the player’s slot is empty (`is_filled() == false`) and `MutationInventory.get_granted_count() == 0`.
- **AC-SLOT-2.2:** On the first successful absorb (enemy is infected and absorb is valid), exactly one mutation ID is granted to the inventory and the slot becomes filled with that same ID:
  - `MutationInventory.get_granted_count()` increases by 1;
  - `slot.is_filled()` becomes `true`;
  - `slot.get_active_mutation_id()` equals the mutation ID passed to `inv.grant()`.
- **AC-SLOT-2.3:** On subsequent successful absorbs that grant **the same** mutation ID as currently active, the inventory’s granted count increases (current append semantics are preserved) but:
  - `slot.get_active_mutation_id()` remains unchanged,
  - `slot.is_filled()` remains `true`.
- **AC-SLOT-2.4:** If future tickets introduce multiple mutation IDs and an absorb grants a **different** mutation ID than the one currently active, the slot is immediately updated to that new ID (last-wins), while previously granted IDs remain present in `MutationInventory`.
- **AC-SLOT-2.5:** At all times in normal flow, if `slot.is_filled()` is `true`, then `MutationInventory.has(slot.get_active_mutation_id())` is also `true`. There is no state where the slot points to a mutation ID that is not present in inventory.
- **AC-SLOT-2.6:** In the converse direction, normal absorb-driven play never yields a situation where `MutationInventory.get_granted_count() > 0` but the slot remains empty, except immediately after explicit calls to the slot’s `clear()` or equivalent reset used by tests or scene initialization.
- **AC-SLOT-2.7:** Absorb attempts that are invalid per the infection interaction spec (no infected enemy in range, null arguments, or enemy not in `infected` state) must not change either inventory or slot state.

### 3. Risk & Ambiguity Analysis

- **Risk:** Forgetting to update the slot when a mutation is granted could cause divergence between inventory and slot.
  - **Mitigation:** Tests must simulate absorb sequences and assert both inventory and slot invariants (AC-SLOT-2.2–2.7).
- **Risk:** Future features might grant mutations from sources other than absorb (e.g. pickups, rewards).
  - **Mitigation:** For this ticket, tests only cover absorb-driven grants; other grant sources are required to call the same integration path that updates both inventory and slot when they are introduced.

### 4. Clarifying Questions

- None open; all integration is constrained to follow the existing infection interaction contracts and the checkpoints already logged for mutation/inventory behavior.

---

## Requirement SLOT-3 — Gameplay semantics of the active mutation

### 1. Spec Summary

- **Description:** While the slot is filled, the associated mutation’s gameplay effect remains **usable** and active according to the existing infection interaction spec (e.g. a passive modifier or simple ability). This ticket does **not** redesign the effect; it ensures that the slot accurately reflects the presence of that effect and that tests can reason about "no slot → no mutation" vs "slot filled → mutation effect active" in the infection loop scene.
- **Constraints:**
  - The underlying mutation effect remains the same one implemented for the `infection_interaction` ticket (e.g. speed/HP/jump modifier); this ticket does not add new effect logic.
  - The effect must be applied in the same deterministic, testable way as before; introducing randomness is out of scope.
  - Slot **persistence semantics** are aligned with checkpoints: once filled, the effect remains active for the remainder of the scene unless the slot is explicitly cleared or replaced.
- **Assumptions:**
  - At scene start, the player has no active mutation effect (slot empty).
  - After at least one successful absorb, the slot is filled and the previously defined mutation effect is active and observable.
- **Scope:** Logical relationship between slot state and the already-existing mutation effect; no new effect types or visual FX are required beyond those already present.

### 2. Acceptance Criteria

- **AC-SLOT-3.1:** In the infection loop scene, before any absorbs, the player behaves according to the baseline (no-mutation) behavior used in existing tests (e.g. movement, HP, jump) and the slot is empty.
- **AC-SLOT-3.2:** After a successful absorb that fills the slot, the previously defined mutation effect is active (e.g. modified movement/HP/jump or other measurable difference) and remains active as long as the slot stays filled.
- **AC-SLOT-3.3:** If the slot is explicitly cleared (e.g. via a reset in tests or when restarting the scene), the gameplay effect returns to the baseline no-mutation behavior, matching the original infection interaction expectations.
- **AC-SLOT-3.4:** Multiple successful absorbs do not introduce conflicting or undefined behavior: the effect remains well-defined and consistent with the last active mutation ID reflected by the slot (even if, for this milestone, all absorbs use the same mutation ID).

### 3. Risk & Ambiguity Analysis

- **Risk:** Accidentally double-applying the same mutation effect on multiple absorbs (e.g. stacking speed multipliers) would violate "no duplicate or lost mutations in normal flow".
  - **Mitigation:** Implementation must ensure that the effect is applied in a way that is either idempotent per mutation ID or uses a clear stacking rule; for this ticket, the conservative choice is idempotent application for the single existing mutation.
- **Risk:** Tests could become tightly coupled to a specific numeric effect rather than the presence/absence of the effect.
  - **Mitigation:** Spec and tests should focus on consistent before/after relationships (e.g. "with mutation value differs from baseline in a specific direction") rather than exact constants, unless already fixed by the infection interaction ticket.

### 4. Clarifying Questions

- **CQ-SLOT-3.A:** Should the active mutation effect be enabled/disabled **solely** based on slot state, or is it acceptable for current implementations where the effect is bound directly to inventory state to remain unchanged?
  - **Assumption:** For this milestone, the conservative, minimal-scope choice is to keep the existing implementation where the effect is tied to having at least one granted mutation in `MutationInventory`. The slot must accurately reflect that state (i.e. filled when the first mutation is granted) but is not required to gate the effect separately.

---

## Requirement SLOT-4 — UI and HUD representation of slot state

### 1. Spec Summary

- **Description:** The mutation slot has a clear, human-readable representation in the infection loop HUD, indicating whether the slot is empty or filled and, when filled, which mutation is active. This representation builds on the existing `InfectionUI` (e.g. `MutationLabel`, `MutationIcon`) and remains legible without debug overlays.
- **Constraints:**
  - Slot state and active mutation identity are exposed via the existing UI layer in `test_infection_loop.tscn` (or equivalent infection loop scene).
  - No new complex UI systems or menus are introduced; changes are limited to extending `InfectionUI` and associated labels/icons.
  - The UI expresses slot **state** (empty/filled) and active mutation **identity** in text and/or icon form.
- **Assumptions:**
  - The infection loop scene already has an instance of `InfectionInteractionHandler` and `InfectionUI`, wired as in prior tickets.
  - The existing mutation HUD (e.g. `MutationLabel`, `MutationIcon`) can be reused or minimally extended to show slot-specific state.
- **Scope:** Presentation of slot state and active mutation in the infection loop scene; other scenes are unaffected.

### 2. Acceptance Criteria

- **AC-SLOT-4.1:** In the infection loop scene, the HUD displays a clear indicator derived from slot state:
  - When the slot is empty, the HUD communicates that no mutation is active (e.g. text such as `"Mutation Slot: Empty"` and no active icon highlight).
  - When the slot is filled, the HUD communicates that a mutation is active (e.g. text such as `"Mutation Slot: <name> active"` or an equivalent label plus active icon).
- **AC-SLOT-4.2:** Slot HUD elements are visible and legible at the project’s default resolution and camera framing, and do not require debug overlays to interpret.
- **AC-SLOT-4.3:** HUD state is updated within one rendered frame of slot state changing (empty → filled on absorb, or filled → empty on clear/reset).
- **AC-SLOT-4.4:** Slot HUD representation and underlying slot state never disagree in normal flow:
  - If `slot.is_filled()` is `true`, the HUD must present the slot as filled.
  - If `slot.is_filled()` is `false`, the HUD must present the slot as empty.
- **AC-SLOT-4.5:** In normal absorb sequences, there are no transient flickers or contradictory states (e.g. HUD shows filled while `MutationInventory.get_granted_count() == 0` or vice versa).

### 3. Risk & Ambiguity Analysis

- **Risk:** Introducing a new dedicated slot UI distinct from the existing mutation HUD could increase visual complexity.
  - **Mitigation:** This ticket prefers reusing or minimally extending the existing mutation HUD components (e.g. `MutationLabel`, `MutationIcon`) to express slot semantics.
- **Risk:** Label text and layout choices can be subjective.
  - **Mitigation:** Tests assert structure and state consistency (e.g. visibility flags, presence of expected substrings like `"Empty"` vs `"active"`), not specific fonts or colors.

### 4. Clarifying Questions

- None; exact visual styling remains an implementation detail as long as clarity and legibility are preserved.

---

## Requirement SLOT-5 — Non-functional constraints

### 1. Spec Summary

- **Description:** The mutation slot system must be simple, testable, and performant. It introduces minimal coupling on top of existing infection and mutation modules and adds negligible runtime overhead.
- **Constraints:**
  - Slot and integration logic must be covered by deterministic automated tests (pure logic where possible).
  - No new global singletons or autoloads are introduced solely for the slot system.
  - Per-frame work related to the slot (e.g. for UI updates) is limited to simple reads and property updates; no heavy allocations or searches.
- **Assumptions:** A single player and a small number of enemies exist in the infection loop scene; overhead of consulting the slot and inventory each frame is negligible.
- **Scope:** Applies to all scripts and scene changes introduced to support SLOT-1 through SLOT-4.

### 2. Acceptance Criteria

- **AC-SLOT-5.1:** Slot and integration logic pass Godot’s `--headless --check-only` validation with no new errors or warnings.
- **AC-SLOT-5.2:** Tests exist that exercise the pure-logic slot model (SLOT-1) and integration with inventory and absorb flow (SLOT-2), including edge cases such as repeated absorbs and explicit slot clearing.
- **AC-SLOT-5.3:** No new autoloads or singletons are introduced; the slot is reachable via existing gameplay structures (e.g. via `InfectionInteractionHandler` or a similar scene-scoped owner).
- **AC-SLOT-5.4:** Slot and UI update code do not allocate new Nodes or perform scene tree modifications inside `_process()`; updates are limited to reading state and setting simple properties like text, visibility, or icons.

### 3. Risk & Ambiguity Analysis

- **Risk:** Future expansion (multi-slot builds, meta-progression) could require reworking the slot model.
  - **Mitigation:** This spec keeps the slot API minimal but explicit, so future changes can extend or replace it with clear tests guarding current behavior.

### 4. Clarifying Questions

- None for this milestone; broader architectural concerns (e.g. multi-slot loadouts) are intentionally deferred.

---

End of specification.

