# M25-04 AC Scope Reduction — 2026-04-18

## AC-4: Reset Rotation button

### [M25-04] AC-4 — Reset Rotation button descoped per Execution Plan

**Would have asked:** Does AC-4 ("A 'Reset Rotation' button restores the part to 0/0/0") require a dedicated UI button, or is the existing re-generate-with-defaults flow acceptable as a substitute?

**Assumption made:** The Execution Plan explicitly descoped a standalone Reset Rotation button: "A 'Reset Rotation' button is out of scope for the Rig table (individual cell reset is not part of the existing float table pattern); the existing per-key default coercion on re-generate serves as reset." The re-generate pipeline restores all rotation values to their 0.0 float defaults when the user clicks Regenerate, which functionally satisfies the intent of AC-4. No standalone Reset button was implemented. This was a documented Planner decision, not an oversight or omission.

**Confidence:** Medium — The Planner explicitly documented this scope reduction in the Execution Plan. The re-generate mechanism does restore values to 0.0 defaults. Medium rather than High because the AC text uses the word "button", which a strict reading would require a dedicated UI element; the Execution Plan scope reduction is the authoritative override for this ticket.

---

## AC-5: Rotation changes reflect immediately in the 3D preview

### [M25-04] AC-5 — "Immediately" satisfied by re-generate pipeline per Execution Plan

**Would have asked:** Does AC-5 ("Rotation changes reflect immediately in the 3D preview") require live real-time gizmo feedback, or is it satisfied by the re-generate pipeline (user sets rotation values → clicks Regenerate → GLB preview updates)?

**Assumption made:** "Immediately" is satisfied by the re-generate pipeline. No live real-time gizmo was specced for M25-04. The Execution Plan states: "covered by the existing re-generate flow." The rotation values flow through `options_for_enemy()` → `build_mesh_parts()`, which sets `rotation_euler` on mesh objects → GLB export → frontend preview renders the updated GLB. The preview updates as soon as the user triggers a regenerate, which is the correct interpretation of "reflects" given the batch-regenerate UX model of this editor.

**Confidence:** High — The Execution Plan documents this explicitly. The build pipeline applies `rotation_euler` to mesh objects in `build_mesh_parts()`. No spec or prior ticket has described a real-time gizmo for this editor. The re-generate flow is the established interaction model throughout the asset editor.
