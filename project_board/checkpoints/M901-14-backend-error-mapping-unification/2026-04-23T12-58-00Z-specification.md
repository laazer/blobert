### [M901-14-backend-error-mapping-unification] SPECIFICATION — Error Taxonomy Baseline
**Would have asked:** If two routers currently map the same domain exception to different status codes, should unification normalize to one status or preserve router-local behavior?
**Assumption made:** Preserve current externally observable behavior per endpoint as the conservative parity baseline; any conflict is resolved in favor of endpoint-specific legacy semantics rather than cross-endpoint normalization.
**Confidence:** Medium

### [M901-14-backend-error-mapping-unification] SPECIFICATION — Logging Contract Scope
**Would have asked:** Should log field names and log levels be treated as strict API contract or only logging presence/semantic category?
**Assumption made:** Preserve or improve structured logging semantics (error category, route context, and exception identity) while allowing non-breaking key-name additions; do not require byte-for-byte log-message parity.
**Confidence:** Medium

### [M901-14-backend-error-mapping-unification] SPECIFICATION — Unknown Exception Fallback
**Would have asked:** Should unknown exceptions be surfaced with original message text or replaced with generic safe detail?
**Assumption made:** Fail closed for unhandled exceptions: return a generic internal-error payload safe for external clients, while logging full exception detail internally.
**Confidence:** High
