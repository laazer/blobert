# Checkpoint log — registry-fix-versions-slots-load

**Run:** 2026-04-11T22-15-00Z-autopilot-description  
**Ticket:** `project_board/inbox/in_progress/registry-fix-versions-slots-load.md`

Orchestrator: ticket created from user description (registry: multiple versions, empty slots, load existing).

---

### [registry-fix-versions-slots-load] PLANNING — Scope and surfaces

**Would have asked:** Should acceptance criteria apply equally to **player** and **enemy** registry flows, or is the bug report enemy-only?

**Assumption made:** Spec and tests cover **both** enemy and player where the same JSON/API/UI patterns apply; if repro is enemy-only, implementation may still touch shared helpers (`validate_manifest`, load-existing candidates) and must not regress player.

**Confidence:** Medium

### [registry-fix-versions-slots-load] PLANNING — Root-cause ownership

**Would have asked:** Is the failure primarily **backend validation** (e.g. `put_enemy_slots`, `validate_manifest`), **frontend gating** (`SaveModelModal` draft/in_use checks, slot list handling), or **discovery/sync** (`sync_discovered_animated_glb_versions` / export refresh)?

**Assumption made:** Plan treats all three as **in-scope hypotheses** until spec/test narrow: align UI copy and API rules, ensure multi-version rows persist, empty slot placeholders round-trip, and load-existing remains coherent.

**Confidence:** Medium

### [registry-fix-versions-slots-load] PLANNING — “Easy load” definition

**Would have asked:** What minimal UX counts as “easy load” (Registry tab only vs Command Panel shortcuts)?

**Assumption made:** **Registry tab** “load existing” flow (`ModelRegistryPane`, `registryLoadExisting.ts`, backend candidate listing + `openExistingRegistryModel`) is the primary surface; spec may add one small affordance (e.g. refresh/sync before pick) if needed.

**Confidence:** High

---

### [registry-fix-versions-slots-load] SPECIFICATION — Player slot PUT exposure

**Would have asked:** Must the spec require a new or documented HTTP endpoint for `PUT` player slots if the UI currently only edits enemy slots in the pane?

**Assumption made:** R2/R3 require **player** slot rules to match **enemy** at the **service/API** layer where `put_player_slots` already exists; frontend work targets exposed routes. If player slot editing is not in the UI today, tests may target **Python service + router** only until the UI gains player slot editing—R2 acceptance item 4 is satisfied by backend tests if no player slot PUT is user-facing yet.

**Confidence:** Medium

### [registry-fix-versions-slots-load] SPECIFICATION — Auto-promote vs strict errors

**Would have asked:** Should `SaveModelModal` always auto-patch `in_use` before slotting, or only when the user clicks a specific action?

**Assumption made:** Spec allows **either** automatic promotion **or** disabled control + explicit error, as long as eligibility helpers and server rules agree (R3). Implementer picks one consistent approach per surface; tests lock the chosen behavior.

**Confidence:** High

### [registry-fix-versions-slots-load] TEST_DESIGN — Slot-eligibility test vs modal promotion

**Would have asked:** Should `canAddEnemySlot` stay permissive for not-in-use rows so **Add slot** opens the modal (which patches `in_use`), or should it require `in_use` and force promotion via spawn radios first?

**Assumption made:** Spec R3 requires the **same** predicate as `nextEnemySlotsAfterAdd` and PUT validation: non-empty slottable entries need `draft === false` and `in_use === true`. Tests encode that; **Add slot** is disabled until the user promotes via **In pool** radios, then the modal can append.

**Confidence:** High

### [registry-fix-versions-slots-load] TEST_DESIGN — Outcome

**Would have asked:** None.

**Assumption made:** New Python R1 tests and backend R2 PUT test are green against current code; Vitest fails on `canAddEnemySlot` / pane integration until Implementation Frontend aligns `registrySlotOps.canAddEnemySlot` with `nextEnemySlotsAfterAdd`.

**Confidence:** High

---
