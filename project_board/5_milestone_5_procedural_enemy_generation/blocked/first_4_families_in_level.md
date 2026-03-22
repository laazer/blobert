Title:
Place first 4 enemy families in prototype level
---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | BLOCKED |
| Revision | 1 |
| Last Updated By | Autopilot Orchestrator |
| Next Responsible Agent | Human |
| Validation Status | Not started |
| Blocking Issues | Requires Blender installation / generated GLB assets. Cannot proceed without external tool. |

---


Description:
Place at least one variant from each of the first 4 families (adhesion, acid, claw, carapace)
in the prototype level. Verify mutation drops, collision, weakening, and infection all work
end-to-end with the generated scenes.

Acceptance Criteria:
- One variant each of adhesion_bug, acid_spitter, claw_crawler, carapace_husk placed in level
- Each enemy can be weakened and infected via existing infection loop
- Correct mutation is granted on absorption
- No visual or collision regressions
- Playable without debug tools
