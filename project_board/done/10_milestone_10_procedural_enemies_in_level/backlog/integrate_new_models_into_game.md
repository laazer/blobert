Title:
Integrate new enemy/player models into shipping game paths
---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | BACKLOG |
| Status | Backlog |
| Revision | 3 |
| Last Updated By | Human |
| Next Responsible Agent | Planner Agent |
| Validation Status | Backlog — M10 follow-up; blocked on M9 mesh/material audit exit (ticket 02) |

---

Description:
Wire the reviewed and procedurally placed enemy models (and any player mesh/material updates from the asset pipeline) into default run entry points, main scenes, and build/export assumptions so “play the game” always uses the new art — not legacy placeholders or editor-only paths.

**Milestone:** M10 follow-up (moved from M11 combat scope). Extends the original M10 wiring with current registry exports and player visuals once M9 audit completes.

Acceptance Criteria:
- New enemy scenes used in procedural run assembly match M10 deliverables; no duplicate legacy-only enemy paths in the default run.
- Player model/material updates from M9 are active in `player_3d` (or successor) in normal play.
- `timeout 300 ci/scripts/run_tests.sh` passes after integration.
- Short note in ticket on any feature flags or menu toggles if dual paths are temporarily required.

---

Blocking issues:
- **M9** — `in_progress/02_mesh_and_material_audit_enemy_families_and_player.md` and any open material/color fixes from that audit must complete (or be explicitly waived with owner sign-off) before promoting this ticket to `ready/`.

Unblock when M9 audit exit criteria are met.

## NEXT ACTION
- Planner: confirm integration choke points (`RunSceneAssembler`, `player_3d`, registry active paths) and move to `ready/` when M9 ticket 02 completes.
