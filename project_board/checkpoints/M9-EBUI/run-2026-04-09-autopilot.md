# M9-EBUI — Extras editor tab

### [M9-EBUI] IMPLEMENTATION — mergeCanonicalZoneControls
**Would have asked:** Should synthetic `extra_zone_*` defs live only in API or also in frontend offline merge?
**Assumption made:** Mirror `feat_*` pattern: `syntheticExtraZoneDefsForSlug` appended in `mergeCanonicalZoneControls` so Extras works when meta is empty/partial.
**Confidence:** High

### [M9-EBUI] COVERAGE — diff-cover vs origin/main
**Would have asked:** Commit frontend-only vs fix Python attach coverage in same PR?
**Assumption made:** Repaired `zone_geometry_extras_attach.py` import order; expanded attach tests so combined diff meets diff-cover gate.
**Confidence:** High
