# Scoped checkpoint — 02_backend_blocking_or_polled_run_endpoint

**Run:** 2026-04-13 autopilot (single ticket)

### [M23-02] IMPLEMENTATION — timeout strategy
**Would have asked:** 504 vs 202 when `max_wait_ms` exceeded?
**Assumption made:** **504** with partial `log_text`, `timed_out: true`, and background drain of stdout until the subprocess exits (documented in APMCP spec).
**Confidence:** High

### [M23-02] IMPLEMENTATION — single-flight HTTP code
**Would have asked:** 409 vs 429 for concurrent `/complete`?
**Assumption made:** **409 Conflict** with `detail` + `run_id` (frozen in spec).
**Confidence:** High
