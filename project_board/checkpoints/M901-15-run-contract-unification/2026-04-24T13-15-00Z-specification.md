# Spec Checkpoint Log — M901-15

- Run timestamp (UTC): 2026-04-24T13:15:00Z
- Ticket: `project_board/901_milestone_901_asset_generation_refactoring/in_progress/15_run_contract_unification.md`
- Stage: SPECIFICATION
- Agent: Spec Agent

### [M901-15-run-contract-unification] SPECIFICATION — level-all output prediction ambiguity
**Would have asked:** Should this ticket redefine `level enemy=all` output prediction to represent multiple generated files rather than a single predicted path?
**Assumption made:** Preserve current compatibility behavior and keep single-string predictor contract (including compatibility treatment for `level all`), deferring any multi-output redesign to a separate ticket.
**Confidence:** Medium

### [M901-15-run-contract-unification] SPECIFICATION — command support boundary
**Would have asked:** Should the shared run contract expand to include CLI-only commands (`list`, `prefabs`, `view`, `import`) while unifying logic?
**Assumption made:** Limit shared run contract scope strictly to API-exposed command set (`animated`, `player`, `level`, `smart`, `stats`, `test`) to avoid accidental API-surface expansion.
**Confidence:** High
