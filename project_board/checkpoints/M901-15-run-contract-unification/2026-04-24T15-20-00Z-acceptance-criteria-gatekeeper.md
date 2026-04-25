# [M901-15-run-contract-unification] ACCEPTANCE_CRITERIA_GATEKEEPER — complete-state folder consistency gate

- **Ticket:** `project_board/901_milestone_901_asset_generation_refactoring/in_progress/15_run_contract_unification.md`
- **Stage found:** `INTEGRATION` (Revision 5)
- **Decision:** Hold at `INTEGRATION`, increment revision to 6, route to `Human`.

## Evidence assessment

- Shared run-contract module + router delegation are documented in ticket state and implementation handoff notes.
- Regression evidence is documented for run-contract behavior, router parity semantics, and variant-index handling.
- Validation Status was updated to explicitly map evidence to AC-level claims.

## Blocking rationale

- Workflow enforcement requires Stage `COMPLETE` tickets to live under milestone `done/`.
- This ticket is still under `in_progress/`, so `COMPLETE` would be non-compliant even with technical evidence satisfied.

## Checkpoint protocol (ambiguity logging)

- **Would have asked:** "Can I set Stage COMPLETE now that AC evidence is present, even though the ticket file has not been moved to `done/`?"
- **Assumption made:** No. Enforce stage-folder consistency strictly; keep `INTEGRATION` and escalate human-owned folder/state finalization.
- **Confidence:** High
