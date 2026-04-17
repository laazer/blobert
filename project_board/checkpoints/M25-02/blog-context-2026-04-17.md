# Blog Context Capsule — M25-02 Procedural Texture Presets

- **Ticket ID:** M25-02
- **Goal:** Add gradient / spots / stripes procedural texture presets to all animated enemies; mode selector + per-mode params exposed in the editor; Three.js shader overlay applies in real time without GLB regeneration; all params serialize to enemy config JSON
- **Outcome:** COMPLETE
- **Commit SHAs:** f474d40 (RED test suites), 77e2954 (adversarial cases), 93561a0 (implementation), 112dd95 (ticket close), cc83491 (docs/learnings)
- **Checkpoint log:** project_board/checkpoints/M25-02/

## Surprises / Rework

- **UV availability assumption** — spec agent flagged mid-authoring that generated/primitive GLBs may have no UV attribute; shader GLSL was required to fall back to object-space position coordinates when `vUv` is absent, rather than break on meshes without UV data.
- **Non-finite float coercion** — test breaker adversarial pass added `NaN`, `+inf`, `-inf`, and `None` inputs for `texture_spot_density` and `texture_stripe_width`; the initial validator used bare `float(value)` which would emit non-JSON-serializable values for these inputs; fixed with `math.isfinite()` guard before clamping.
- **Material restore keying** — Three.js `Model` component stores original materials keyed by `mesh.uuid`; on GLB URL change the map must be cleared and re-populated; this edge case was not in the initial spec and was added during test-break adversarial review.
- **10 control defs, all slugs** — texture controls follow the same `_texture_control_defs()` + `static_defs.extend()` + `allowed_non_mesh` wiring pattern established by mouth/tail extras (M25-06); no new pattern invented.
