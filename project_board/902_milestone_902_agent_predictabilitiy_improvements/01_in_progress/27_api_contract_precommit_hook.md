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
INTEGRATION

## Revision
7

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: PASS — `uv run pytest tests/ci/test_api_contract_precommit_hook.py -q` (26 passed, 2026-05-21); `cd asset_generation/python && uv run pytest tests/api/ -q` (87 passed). CI suite covers Req 01–06: lefthook registration (H6), 3-step pipeline exit codes (H1–H5), cache-fallback warning (H5), adversarial A1–A13; no live backend required.
- Static QA: PASS — `.lefthook/scripts/api-contract-check.sh` exists (sync-api-types → tsc → contract pytest; `set -euo pipefail`; no backend auto-start); `lefthook.yml` `api-contract-check` glob `asset_generation/web/backend/**/*.py`, `stage: commit`; Ruff clean per `project_board/checkpoints/M902-27/2026-05-21T-static-qa-run.md`.
- Integration (manual, partial): Spec Req 07 dry-run D1–D5 **deferred** — documented in `project_board/checkpoints/M902-27/2026-05-21T-implementation-run.md` § Deferred; no `<run-id>-dry-run.md` yet. Subprocess CI tests encode D1–D3 (`test_h3` tsc block, `test_h4` pytest block) and D5 success path (`test_h1`); D4 bypass relies on Lefthook/stderr docs in `CLAUDE.md` and `asset_generation/web/backend/AGENTS.md` (not live `git commit` evidence).
- Documentation: PASS — runbook table + bypass in `asset_generation/web/backend/AGENTS.md` § API contract pre-commit; `CLAUDE.md` Hooks § api-contract-check; spec Appendix C cross-linked.
- Git closure (mandatory before COMPLETE): **FAIL** — working tree dirty/untracked (e.g. `.lefthook/scripts/api-contract-check.sh`, `asset_generation/web/frontend/src/api.types.ts`, `lefthook.yml`, `CLAUDE.md`, backend `AGENTS.md`); branch `main` ahead of `origin/main` (44 commits) — commit all M902-27 artifacts and push before Stage COMPLETE per `workflow_enforcement_v1.md`.

## Blocking Issues
- Work not committed/pushed: M902-27 implementation files remain modified or untracked; `git status` must be clean and `git push` must succeed before Stage COMPLETE (non-negotiable per workflow enforcement).
- Ticket folder: still under `01_in_progress/` — move to `02_complete/` only after COMPLETE gate passes.

## Escalation Notes
- Automated acceptance criteria (hook script, lefthook config, error handling, documentation, CI/adversarial tests) have objective evidence. COMPLETE withheld solely for git closure and standard folder move after push.
- Optional Human follow-up: Req 07 D1–D5 live dry-run checkpoint (`project_board/checkpoints/M902-27/<run-id>-dry-run.md`) — not required to unblock commit/push if CI evidence is accepted.

---

# NEXT ACTION

## Next Responsible Agent
Implementation Agent

## Required Input Schema
```json
{
  "ticket_path": "project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/27_api_contract_precommit_hook.md",
  "spec_path": "project_board/specs/902_27_api_contract_precommit_spec.md",
  "actions": [
    "git add .lefthook/scripts/api-contract-check.sh lefthook.yml CLAUDE.md asset_generation/web/backend/AGENTS.md asset_generation/web/frontend/src/api.types.ts",
    "git commit -m \"feat(web): M902-27 api-contract pre-commit hook\"",
    "git push origin main",
    "git mv ticket to 02_complete/ after AC Gatekeeper re-run sets COMPLETE"
  ]
}
```

## Status
Blocked

## Reason
AC Gatekeeper: hook/lefthook/docs/tests evidenced (26+87 PASS); Req 07 dry-run D1–D5 deferred with checkpoint note (acceptable). Stage held at INTEGRATION — cannot set COMPLETE until git working tree clean and pushed per workflow enforcement; then re-run AC Gatekeeper for COMPLETE + `02_complete/` move.
