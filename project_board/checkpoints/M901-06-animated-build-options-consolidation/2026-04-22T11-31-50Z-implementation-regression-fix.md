### [M901-06] IMPLEMENTATION — compatibility export scope under consolidated boundaries

**Would have asked:** Should this regression fix expose only `_mouth_control_defs`, or restore all helper symbols depended on by existing adversarial contract tests?

**Assumption made:** Preserve backward-compatible package-level helper imports used by active tests by explicitly re-exporting `_mouth_control_defs`, `_tail_control_defs`, and `_eye_shape_pupil_control_defs` from `src.utils.build_options.__init__`, without reintroducing legacy modules or changing schema/validate ownership.

**Confidence:** High

---

### [M901-06] IMPLEMENTATION — gate evidence after regression fix

**Would have asked:** Is targeted pytest evidence sufficient for handoff, or should full diff-cover preflight be re-run after compatibility patch?

**Assumption made:** Re-run required targeted suites plus `bash ci/scripts/diff_cover_preflight.sh` to provide complete gatekeeper evidence for regression closure.

**Confidence:** High
