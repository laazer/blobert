### [M9-EGMS] TEST_DESIGN — enemy slots persisted readback API shape
**Would have asked:** Should tests verify post-save slot persistence only via `GET /api/registry/model`, or is a dedicated read endpoint for slots required?
**Assumption made:** Use the strictest defensible UI-facing contract: require `GET /api/registry/model/enemies/{family}/slots` to return `{family, version_ids, resolved_paths}` and assert no partial writes after validation failures.
**Confidence:** Medium

### [M9-EGMS] TEST_DESIGN — backend evidence under architecture-mismatch environment
**Would have asked:** Should I block on fixing local Python architecture mismatch, or proceed with deterministic tests that prove the backend contract via service-level coverage and existing router tests?
**Assumption made:** Proceed conservatively by adding strict deterministic service tests that encode player/slot happy + validation behavior and verifying diff-cover gate recovery, while documenting the unchanged environment blocker for backend router collection.
**Confidence:** High
