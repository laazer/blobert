# Blog context — registry-fix-versions-slots-load

- **Ticket id:** registry-fix-versions-slots-load
- **Goal:** Fix asset editor model registry: multiple versions per family, saving into empty slots, easier load-existing flow.
- **Outcome:** COMPLETE (`project_board/inbox/done/registry-fix-versions-slots-load.md`).
- **Git (best effort):** `223e509` (planner), `80c458b` (failing-first tests), `af84245` (adversarial tests), `95ad53a` (player slot GET/PUT API), `bd61c8f` (frontend R3 fixes + unrelated shell failing-first tests — mixed commit), `6fdec1f` + `1410c4a` (board/spec closure + CHECKPOINTS outcome).
- **Scoped checkpoint log:** `project_board/checkpoints/registry-fix-versions-slots-load/run-2026-04-11-ac-gatekeeper-complete.md`
- **Rework / surprises:**
  - Vitest encoded `canAddEnemySlot` vs `nextEnemySlotsAfterAdd` mismatch before implementation; fixed via shared `isEnemySlotEligible` and spawn radio tri-state (draft / in pool / neither).
  - `slotListHasDuplicates` ignored empty placeholders so multiple `""` slots are valid per spec.
  - Python already had `put_player_slots`; product gap was HTTP — added FastAPI routes mirroring enemy slots.
  - Full `ci/scripts/run_tests.sh` exits 1 on this branch due to unrelated failing-first shell/spike tests (`bd61c8f`), not registry code; scoped pytest/Vitest green for registry paths.
