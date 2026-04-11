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
