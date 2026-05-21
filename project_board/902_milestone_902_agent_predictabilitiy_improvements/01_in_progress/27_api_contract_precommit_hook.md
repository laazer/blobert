# M902-27: API Contract Pre-Commit Hook

**Status:** PENDING  
**Target:** 2026-07-22

## Overview

Implement pre-commit hook that regenerates TypeScript types from OpenAPI spec and runs type-checking. Prevents commits with contract mismatches: if backend and frontend are out of sync, the hook fails and blocks the commit.

## Acceptance Criteria

### Hook Script

- [ ] Create `.lefthook/scripts/api-contract-check.sh`
  - [ ] Step 1: Regenerate TS types from OpenAPI spec
    ```bash
    npx openapi-typescript http://localhost:8000/openapi.json -o \
      asset_generation/web/frontend/src/api.types.ts
    ```
  - [ ] Step 2: Type-check frontend
    ```bash
    cd asset_generation/web/frontend && npx tsc --noEmit
    ```
  - [ ] Step 3: Run contract tests
    ```bash
    pytest tests/api/test_*_contract.py -v
    ```
  - [ ] Exits 0 if all pass, 1 if any fail

### Lefthook Configuration

- [ ] Register hook in `lefthook.yml`:
  ```yaml
  pre-commit:
    commands:
      api-contract-check:
        glob: "asset_generation/web/backend/routers/**/*.py"
        run: bash .lefthook/scripts/api-contract-check.sh
        stage: commit
  ```
  - [ ] Triggers only when backend files change
  - [ ] Runs before commit, blocks if fails

### Error Handling

- [ ] Backend not running:
  - [ ] Gracefully skip regeneration (use cached types)
  - [ ] Still run tsc and contract tests
  - [ ] Log warning: "Backend not reachable; using cached OpenAPI spec"
- [ ] Type errors:
  - [ ] Output `tsc` errors clearly
  - [ ] Point to exact files/lines with mismatches
- [ ] Contract test failures:
  - [ ] Show which tests failed and why
  - [ ] Hint: "Run `pytest tests/api/test_*_contract.py` to debug"

### Workflow

- [ ] Developer makes backend change (e.g., adds field to response)
- [ ] `git add` stages changes
- [ ] `git commit` triggers hook
- [ ] Hook regenerates types → types update
- [ ] `tsc --noEmit` detects type mismatch in frontend code
- [ ] Hook fails with error message
- [ ] Developer fixes frontend code
- [ ] `git add` stages fix
- [ ] `git commit` tries again → succeeds

### Documentation

- [ ] Runbook: What to do if hook fails
  - [ ] "Type mismatch" → Run `npx tsc` in frontend and fix types
  - [ ] "Backend unreachable" → Can bypass with `--no-verify` if intentional
  - [ ] "Contract test failed" → Run `pytest tests/api/` and debug
- [ ] Document how to bypass (if needed): `git commit --no-verify`
  - [ ] Note: Only as temporary workaround, must fix before merge
- [ ] Add to CLAUDE.md: Hook runs automatically, what it checks, how to fix

### Testing

- [ ] Dry-run tests:
  - [ ] Make a backend change (add/remove/rename field)
  - [ ] Try to commit → hook should fail
  - [ ] Fix frontend → retry commit → should succeed
- [ ] Test with 3 scenarios:
  - [ ] Add required field to response → should fail tsc
  - [ ] Change field type (string → int) → should fail tsc
  - [ ] Remove field → should fail tsc
- [ ] Test bypass:
  - [ ] `git commit --no-verify` bypasses hook
  - [ ] Commit succeeds but warns in output

## Implementation Notes

- Hook runs on pre-commit stage (after `git add`, before `git commit`)
- Uses existing `openapi-typescript`, `tsc`, `pytest`
- No new dependencies (everything already installed)
- Should complete in < 30 seconds for typical change
- Can be disabled temporarily with `--no-verify` if needed

## Example Hook Output

```
Running API contract check...
[1/3] Regenerating TypeScript types from OpenAPI spec...
  ✓ Generated: asset_generation/web/frontend/src/api.types.ts

[2/3] Type-checking frontend...
  ✗ ERROR in src/api.ts (line 42):
    Property 'new_field' does not exist on type 'AssetRegistry'
    
    Fix: Update frontend code or regenerate types

[3/3] Running contract tests...
  ✓ All contract tests passed (12 tests)

❌ Commit blocked: Type errors found. Fix and retry.
```

## Spec Reference

See: `project_board/specs/902_27_api_contract_precommit_spec.md`

## Dependencies

- M902-24 (OpenAPI → TypeScript Generation)
- M902-25 (Pydantic + Zod Dual Validation)
- M902-26 (API Contract Testing)
- Lefthook (already in project)

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
IMPLEMENTATION_BACKEND

## Revision
6

## Last Updated By
Test Breaker Agent

## Validation Status
- Tests: PASS — `uv run pytest tests/ci/test_api_contract_precommit_hook.py -q` (26 tests, 3 consecutive green runs 2026-05-21)
- Static QA: N/A
- Integration: N/A

## Blocking Issues
- None

## Escalation Notes
- Manual dry-run evidence (spec Req 07 D1–D5) deferred to Static QA / Integration checkpoint.

---

# NEXT ACTION

## Next Responsible Agent
Implementation Agent

## Required Input Schema
```json
{
  "ticket_path": "project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/27_api_contract_precommit_hook.md",
  "spec_path": "project_board/specs/902_27_api_contract_precommit_spec.md",
  "test_module": "tests/ci/test_api_contract_precommit_hook.py",
  "gaps_log": "project_board/checkpoints/M902-27/2026-05-21T-test-break-run.md"
}
```

## Status
Proceed

## Reason
Adversarial suite A1–A13 added; G1–G7 documented in test-break checkpoint. All 26 hook tests green (3 consecutive runs). Handoff: `project_board/checkpoints/M902-27/handoff-latest.yaml` (test_breaker→implementation). Orchestrator: `run_workflow_transition_gates.py --transition test_break_to_implementation`. Implementation: confirm AC-02.5 cache warning under load; complete Req 07 dry-run if not done.
