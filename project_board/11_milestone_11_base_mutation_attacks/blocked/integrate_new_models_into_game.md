Title:
Integrate new enemy/player models into shipping game paths
---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | BLOCKED |
| Revision | 1 |
| Last Updated By | Human |
| Next Responsible Agent | Planner Agent |
| Validation Status | Blocked — waiting on M9 and M10 exit criteria |

---

Description:
Wire the reviewed and procedurally placed enemy models (and any player mesh/material updates from the asset pipeline) into default run entry points, main scenes, and build/export assumptions so “play the game” always uses the new art — not legacy placeholders or editor-only paths.

Acceptance Criteria:
- New enemy scenes used in procedural run assembly match M9 deliverables; no duplicate legacy-only enemy paths in the default run.
- Player model/material updates from M10 are active in `player_3d` (or successor) in normal play.
- `timeout 300 ci/scripts/run_tests.sh` passes after integration.
- Short note in ticket on any feature flags or menu toggles if dual paths are temporarily required.

---

Blocking issues:
- **M9** — Procedural Enemies in Level & Attack Loop: exit criteria not met.
- **M10** — Enemy & Player Model Review / Materials: exit criteria not met (or explicitly waived with owner sign-off).

Unblock when both milestones above are complete or the scope of this ticket is revised by explicit ticket update.
