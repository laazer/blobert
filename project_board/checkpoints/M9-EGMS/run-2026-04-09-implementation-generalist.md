### [M9-EGMS] IMPLEMENTATION_GENERALIST — frontend slot UI evidence strategy
**Would have asked:** Should I add React DOM integration harnesses, or keep this pass minimal and close only gatekeeper blockers with focused contract tests?
**Assumption made:** Keep implementation minimal by exporting pure slot-state helpers from `ModelRegistryPane` and asserting add/remove/full-replacement + empty-slot fallback behavior in targeted Vitest cases, avoiding framework expansion.
**Confidence:** High

### [M9-EGMS] IMPLEMENTATION_GENERALIST — API validation evidence under router env blocker
**Would have asked:** Is router-suite re-execution mandatory in this environment despite persistent `pydantic_core` architecture mismatch?
**Assumption made:** Provide explicit API/UI validation-error coverage evidence via frontend client contract tests (400/404 paths) and carry forward the known router blocker note for gatekeeper disposition.
**Confidence:** Medium
