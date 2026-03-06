# Infection Interaction — Functional and Non-Functional Specification

**Ticket:** infection_interaction.md  
**Epic:** Milestone 2 – Infection Loop  
**Revision:** 1 (Spec Agent)

---

## 1. Scope and Assumptions

- **Scope:** End-to-end flow from weakened enemy → infected → absorb → mutation granted and usable. At least one real mutation with a noticeable gameplay effect. No persistence across runs; no multi-mutation selection UI.
- **Assumptions:** Enemy lifecycle is governed by existing `EnemyStateMachine` (idle, active, weakened, infected, dead). Weakening is triggered by a defined interaction (chunk contact or key press). Infection is only valid when enemy state is `weakened`. Absorb applies death to the enemy and grants one mutation. Single mutation type for this milestone; interfaces allow extension later.

---

## 2. Requirement: Weakening and Weaken Trigger

### 2.1 Spec Summary

- **Description:** An enemy becomes "weakened" when a defined interaction occurs (e.g. chunk contact or key press). Weakening is implemented by calling `apply_weaken_event()` on that enemy's `EnemyStateMachine` instance. Only enemies in `idle` or `active` may transition to `weakened`; already weakened or infected or dead enemies are unchanged (no-op).
- **Constraints:** Uses existing `EnemyStateMachine.apply_weaken_event()`. At least one trigger must be implemented: chunk contact with enemy and/or dedicated key when in range.
- **Assumptions:** Chunk contact is the primary option for "slime/chunk interacts"; key-based weaken is allowed as alternative or supplement. Gameplay/engine layer is responsible for detecting the trigger and invoking the state machine.
- **Scope:** Gameplay systems and engine integration; core state machine is already specified.

### 2.2 Acceptance Criteria

- AC-W1: When the chosen trigger (chunk contact or key) occurs with respect to an enemy in `idle` or `active`, that enemy's state machine receives `apply_weaken_event()` and transitions to `weakened`.
- AC-W2: When the trigger occurs with respect to an already `weakened` or `infected` or `dead` enemy, no state change occurs (no-op).
- AC-W3: Only the enemy that is the target of the interaction is affected; other enemies' state machines are unchanged.

### 2.3 Risk & Ambiguity

- **Risk:** Multiple simultaneous contacts could cause duplicate weaken calls; idempotent (weaken-from-weakened no-op) is already defined by ESM.
- **Edge case:** Trigger when no enemy in range: no apply_weaken_event() called; no error state.

### 2.4 Clarifying Questions

- Resolved by checkpoint: at least one trigger (chunk contact or key); chunk contact primary.

---

## 3. Requirement: Infection Trigger and Infected State

### 3.1 Spec Summary

- **Description:** A weakened enemy can be infected via a defined interaction (e.g. chunk contact or key press). Infection is implemented by calling `apply_infection_event()` on that enemy's `EnemyStateMachine`. Only when state is `weakened` does the enemy transition to `infected`; otherwise the call is a no-op.
- **Constraints:** Uses existing `EnemyStateMachine.apply_infection_event()`. Infection trigger must be implementable in the infection loop scene (chunk contact and/or key).
- **Assumptions:** Same trigger options as weakening; infection and weaken may share the same key (e.g. "interact") with logic: if weakened then infect, else if not weakened then weaken, or separate keys.
- **Scope:** Gameplay systems and engine integration.

### 3.2 Acceptance Criteria

- AC-I1: When the infection trigger occurs with respect to an enemy in state `weakened`, that enemy's state machine receives `apply_infection_event()` and transitions to `infected`.
- AC-I2: When the infection trigger occurs with respect to an enemy not in `weakened` (idle, active, already infected, dead), no state change occurs.
- AC-I3: Infected state is distinct and queryable via `get_state() == "infected"` for UI and absorb logic.

### 3.3 Risk & Ambiguity

- **Edge case:** Double infection attempt on same enemy: ESM already defines no-op (infected → infected).
- **Risk:** Confusion between "weaken" and "infect" in one key: spec allows either one key (with branch on state) or two keys.

### 3.4 Clarifying Questions

- None open.

---

## 4. Requirement: Absorb and Absorb Resolution

### 4.1 Spec Summary

- **Description:** The player can perform an absorb action (e.g. key press) when an infected enemy is in range. Absorb resolution: (1) the absorbed enemy's state machine receives `apply_death_event()` so the enemy transitions to `dead`, (2) the player is granted one mutation (see Mutation requirement), (3) any absorb-availability UI is updated. Absorb when no infected enemy in range is a no-op (no death, no mutation grant).
- **Constraints:** Absorb must not leave the enemy in an undefined state; using `apply_death_event()` satisfies this. Existing `InfectionUI.set_absorb_available(bool)` and "Press E to Absorb" are used for feedback.
- **Assumptions:** Absorb applies death to the absorbed enemy (checkpoint). One absorb per infected enemy; after absorb the enemy is dead and no longer a valid absorb target.
- **Scope:** Gameplay systems, core mutation module, engine integration, presentation.

### 4.2 Acceptance Criteria

- AC-A1: When the player triggers absorb and an infected enemy is in range, that enemy's state machine receives `apply_death_event()` and state becomes `dead`.
- AC-A2: When absorb is triggered and an infected enemy is in range, the player is granted exactly one mutation (see Mutation requirement).
- AC-A3: When absorb is triggered and no infected enemy is in range, no enemy state change and no mutation grant.
- AC-A4: Absorb does not softlock: after absorb, no enemy remains in `infected` for the absorbed target; no undefined or stuck state.
- AC-A5: Absorb feedback is visible (e.g. absorb prompt visibility, mutation HUD) without debug overlays.

### 4.3 Risk & Ambiguity

- **Edge case:** Two infected enemies in range: spec does not mandate which is absorbed; implementation may choose nearest or first. At least one must be absorbed (one absorb action → one death, one mutation grant).
- **Risk:** Rapid double key press: implementation should ensure one absorb consumes one infected enemy and one mutation grant.

### 4.4 Clarifying Questions

- Resolved by checkpoint: absorb resolution applies apply_death_event() to the absorbed enemy.

---

## 5. Requirement: Mutation Granting and Single Usable Mutation

### 5.1 Spec Summary

- **Description:** On successful absorb of an infected enemy, the player is granted exactly one mutation. The mutation has a concrete, measurable gameplay effect (e.g. movement speed, jump height, or HP-related modifier). The mutation is "usable" in the sense that the effect is applied for the remainder of the session and the player can observe or use it in the infection loop scene. At least one mutation type is implemented; the data model allows future extension (e.g. list of mutation ids).
- **Constraints:** One mutation minimum for this milestone. Mutation state must be queryable for tests and for application of effects. No persistence across game runs in scope.
- **Assumptions:** One mutation type with one observable effect; exact effect is implementation choice (checkpoint). Interface allows list/set of mutation ids later.
- **Scope:** Core logic (mutation module), gameplay (apply effect), presentation (HUD/UX for "mutation acquired and active").

### 5.2 Acceptance Criteria

- AC-M1: After a valid absorb, the player has exactly one mutation of the implemented type (e.g. query returns true for "has mutation X").
- AC-M2: The mutation has a measurable effect: tests or play can observe a before/after difference (e.g. movement sim output, jump height, or HUD value).
- AC-M3: The mutation is applied for the rest of the session (no removal in scope).
- AC-M4: No duplicate mutation grant for the same absorb event; no grant when absorb is invalid (no infected in range).
- AC-M5: Simple HUD/UX indicates mutation acquired and active/usable (per ticket Task 10).

### 5.3 Risk & Ambiguity

- **Edge case:** Multiple absorbs (multiple infected enemies): each valid absorb grants one mutation; if only one mutation type exists, "grant" may be idempotent (already have it) or stack; spec requires at least "one mutation granted and usable" so first absorb must grant it; subsequent absorbs may grant same type again or be no-op—implementation choice, but no softlock.
- **Risk:** Mutation effect coupling to movement sim: effect must be observable; prefer a single mutation that modifies a well-defined parameter (e.g. speed, jump_height) so tests can assert value change.

### 5.4 Clarifying Questions

- Resolved by checkpoint: one concrete mutation with measurable effect; observable in tests/play.

---

## 6. Requirement: No Softlock or Undefined State

### 6.1 Spec Summary

- **Description:** No sequence of interactions may leave the game in a softlock or undefined state. Specifically: no enemy may remain in a state that blocks progress without a defined transition out; no mutation or infection state may be inconsistent (e.g. "infected" enemy that cannot be absorbed); absorb always resolves the absorbed enemy to `dead`.
- **Constraints:** All transitions are defined by EnemyStateMachine and the mutation module; invalid inputs are no-ops.
- **Assumptions:** "Undefined state" means an enemy state not in {idle, active, weakened, infected, dead} or a state from which no defined action can transition; mutation state is either "has" or "has not" for the single type.
- **Scope:** Full loop.

### 6.2 Acceptance Criteria

- AC-S1: Every enemy state is one of idle, active, weakened, infected, dead.
- AC-S2: Infected enemies are always valid absorb targets (in range) until absorbed; after absorb they are dead.
- AC-S3: No transition leaves an enemy in a state that is not in the canonical set.
- AC-S4: Repeated infection attempts, absorb with no target, and weaken on already weakened do not create inconsistent state (all no-ops per ESM and spec).

### 6.3 Risk & Ambiguity

- **Edge case:** All enemies dead and no more spawns: not a softlock if design allows; player can still move and use mutation. Optional "win" or "no more targets" is out of scope unless specified elsewhere.

### 6.4 Clarifying Questions

- None.

---

## 7. Requirement: Human-Playable and Discoverable Feedback

### 7.1 Spec Summary

- **Description:** The infection interaction is human-playable in-editor in the infection loop test scene. Weakened, infected, and absorb feedback are visually (and optionally audibly) clear and discoverable without debug overlays. The player can identify: which enemy is weakened vs infected, when absorb is available, and when absorb succeeded (mutation gained).
- **Constraints:** Uses existing infection loop scene (e.g. test_infection_loop.tscn). Feedback via existing or new visual/audio cues; no requirement for specific assets beyond clarity.
- **Assumptions:** "Discoverable" means a first-time player can infer state from visuals (e.g. color shift, icon, prompt text). Absorb prompt (e.g. "Press E to Absorb") and mutation HUD suffice for absorb feedback.
- **Scope:** Presentation, engine integration (scene setup).

### 7.2 Acceptance Criteria

- AC-H1: In the infection loop scene, the player can perform weaken (and see or infer weakened state), infect (and see or infer infected state), and absorb (and see absorb success).
- AC-H2: Weakened and infected states are visually distinct from each other and from idle/active.
- AC-H3: Absorb availability is indicated (e.g. absorb prompt visible when an infected enemy is in range).
- AC-H4: Successful absorb is indicated (e.g. mutation HUD or icon shows mutation acquired/active).
- AC-H5: No debug overlay is required to understand the loop.

### 7.3 Risk & Ambiguity

- **Risk:** Subjective "clear" and "discoverable"; tests may assert presence of distinct visuals (e.g. modulate or label text) rather than aesthetic quality.

### 7.4 Clarifying Questions

- None.

---

## 8. API and Data Model Contracts (Task 2)

### 8.1 EnemyStateMachine (Existing)

- **Location:** `scripts/enemy_state_machine.gd`, class `EnemyStateMachine` (RefCounted).
- **API:**  
  - `get_state() -> String`  
  - `apply_weaken_event() -> void`  
  - `apply_infection_event() -> void`  
  - `apply_death_event() -> void`  
  - `reset() -> void`  
- **States:** `"idle"`, `"active"`, `"weakened"`, `"infected"`, `"dead"`.  
- **Contract:** Callers (gameplay/engine) invoke event methods; state transitions are as specified in enemy_state_machine tests. No Node or scene dependency.

### 8.2 Infection / Absorb Events (Gameplay → Core)

- **Infection attempt:** Gameplay layer detects trigger (chunk contact or key) and calls `apply_weaken_event()` and/or `apply_infection_event()` on the target enemy's state machine instance. No new core module required for "infection attempt"; it is the invocation of these two methods in the correct order (weaken then infect) for the same enemy.
- **Absorb:** Gameplay layer detects absorb key and that an infected enemy is in range; then (1) calls `apply_death_event()` on that enemy's state machine, (2) calls into the mutation module to grant the mutation (see 8.3).

### 8.3 Mutation Module (New Pure Logic)

- **Purpose:** Deterministic, testable mutation state: grant and query mutations without Node/scene.
- **Recommended shape:** A RefCounted (or Object) class, e.g. `MutationRegistry` or `PlayerMutationState`, with no Godot node dependency.
- **Required API (minimal):**
  - **Grant:** `grant_mutation(mutation_id: String) -> void` (or equivalent id/type). For this milestone, at least one mutation id is defined (e.g. `"mutation_speed"`); calling grant adds that mutation to the set of owned mutations.
  - **Query:** `has_mutation(mutation_id: String) -> bool`. Returns true if the mutation was granted.
  - **List (for effect application):** `get_granted_mutation_ids() -> Array[String]` or `get_granted_mutation_ids() -> Array` of strings. Allows gameplay/simulation to apply effects (e.g. read list and apply speed modifier).
- **Contract:** Pure logic; no I/O. Multiple grants of same id may be idempotent (set semantics) or allow stacking—implementation choice; at least one grant must make `has_mutation` true and the effect applicable.
- **Effect application:** Not part of the pure module. Gameplay or simulation code reads `get_granted_mutation_ids()` and applies the corresponding effect (e.g. multiply speed by 1.2). Tests can assert that after `grant_mutation("x")`, `has_mutation("x")` is true and that a downstream system would see the id in the list.

### 8.4 Presentation / UI Contracts

- **Absorb prompt:** Existing `InfectionUI.set_absorb_available(available: bool)` and `AbsorbPromptLabel`; gameplay sets `absorb_available` true when an infected enemy is in range, false otherwise.
- **Mutation HUD:** A simple indicator that at least one mutation is acquired and active (e.g. icon or text). Implementation may query the mutation module (via a reference held by the scene or player) to show "Mutation: Active" or list mutation names.

### 8.5 Naming and Types

- **Mutation id:** String type; at least one constant or literal for the single mutation (e.g. `"mutation_speed"`). Exact name is implementation choice; tests must target the same id.
- **Enemy reference:** Gameplay must associate each enemy node with one `EnemyStateMachine` instance; how (e.g. node script variable, group, or dictionary) is implementation detail. Spec only requires that the correct instance receives events for the enemy that is the target of the interaction.

---

## 9. Failure and Edge Cases (Summary)

| Scenario | Expected behavior |
|--------|-------------------|
| Infection trigger on non-weakened enemy | No-op (ESM apply_infection_event) |
| Weaken on already weakened enemy | No-op (ESM apply_weaken_event) |
| Absorb with no infected enemy in range | No death, no mutation grant |
| Absorb with infected enemy in range | That enemy → dead, one mutation granted |
| Double absorb on same frame / same enemy | One absorb consumes one enemy; no double grant or double death for same entity |
| Multiple infected in range | One absorb consumes one (e.g. nearest); one mutation grant |
| Chunk contact with no enemy | No state change |
| Death event on already dead enemy | No-op (ESM) |

---

## 10. Non-Functional Requirements

- **Testability:** Core infection flow (weaken → infect → absorb → grant) must be testable via pure logic: state machine + mutation module. Scene-level tests may use test_infection_loop.tscn with player and at least one enemy.
- **Performance:** No hard latency or frame budget; avoid per-frame scans over large enemy counts where possible (e.g. range check only for nearby bodies).
- **Architecture:** Infection and mutation logic in deterministic modules; gameplay/engine wires input and collisions to those modules. Presentation reacts to state (absorb_available, mutation list) without driving state.

---

End of specification.
