# Run Log: M9-LEMA / run-2026-04-09-autopilot

## Context
- Ticket: `project_board/9_milestone_9_enemy_player_model_visual_polish/in_progress/06_editor_load_existing_models_allowlist.md`
- Mode: Autopilot single-ticket
- Stage at start: PLANNING (bootstrapped)

## Checkpoints

### 2026-04-09T11:52:08Z
**Would have asked:** The ticket stub lacks required workflow state blocks (Stage/Revision/Next Action). Should I reconstruct the full ticket template before running Planner?

**Assumption made:** Bootstrap the ticket minimally by adding `WORKFLOW STATE` + `NEXT ACTION` sections with Stage `PLANNING`, Revision `1`, Last Updated By `Autopilot Orchestrator`, and Next Responsible Agent `Planner Agent`, then continue normal staged execution.

**Confidence:** High

### [M9-LEMA] PLANNING — canonical roots and visibility contract
**Would have asked:** Should "in-use" scope include both active game-model selections and any registry references in draft slots, and should unrelated `.glb` files under allowlisted folders be hidden rather than selectable?

**Assumption made:** Treat "in-use" as entries currently referenced by active game-model registry selections, keep draft entries visible, and require the picker to show only registry-backed draft/in-use rows (never raw filesystem listing), with non-registry files excluded even inside canonical roots.

**Confidence:** Medium

### [M9-LEMA] SPECIFICATION — non-registry files in canonical roots
**Would have asked:** Inside allowlisted roots, should `.glb` files not present in registry be shown as disabled rows for discoverability or omitted entirely?

**Assumption made:** Omit non-registry files entirely from the Load/Open candidate list for this ticket; list responses are registry-backed only (`draft` or `in_use`) and never expose raw on-disk extras.

**Confidence:** High

### [M9-LEMA] TEST_DESIGN — load/open endpoint contract shape
**Would have asked:** The spec defines constrained load/open behavior but does not freeze exact endpoint names or payload envelope; should tests enforce a single explicit backend contract now?

**Assumption made:** Encode the strictest defensible contract: `GET /api/registry/model/load_existing/candidates` and `POST /api/registry/model/load_existing/open`, with identity-first payloads (`kind`, `family`, `version_id`) and optional guarded path payloads validated under the same jail/error layering.

**Confidence:** Medium

### [M9-LEMA] IMPLEMENTATION_BACKEND — stale-file contract fixture coherence
**Would have asked:** The stale-file test expects `404` after deleting `alpha_live_00.glb`, but fixture setup did not create that file while other tests expected successful open for the same identity; should fixture include it?

**Assumption made:** Choose the conservative implementation aligned with "missing file returns 404" by preserving file-existence checks in backend open flow and adding `animated_exports/alpha_live_00.glb` to fixture setup so success and stale-file behaviors are both deterministic.

**Confidence:** High
