# Spec: test_suite_green_and_runner_exit_codes (MAINT-TSGR)

**Ticket:** `project_board/maintenance/in_progress/test_suite_green_and_runner_exit_codes.md`  
**Spec Date:** 2026-04-05  
**Spec Agent Revision:** 1  

**Related scripts (baseline):** `ci/scripts/run_tests.sh`, `.lefthook/scripts/godot-tests.sh`, `.lefthook/scripts/py-tests.sh`  
**Godot runner contract:** `tests/run_tests.gd` (exit `0` all pass, `1` one or more failures; unloadable suite → `quit(1)`).

**Traceability (ticket acceptance criteria):**

| Ticket AC | Spec coverage |
|-----------|----------------|
| Combined runner exits non-zero on Godot failure, Python failure, timeouts, import/reimport failure; no silent `|| true` without narrow documented bypass + logging | TSGR-2, TSGR-3, TSGR-4, TSGR-5 |
| Full run exit `0` on clean tree (all tests passing) | TSGR-7 |
| `CLAUDE.md` + lefthook / CI consistency | TSGR-6 |
| Closure evidence (command + output / touched files) | TSGR-8 (process requirement for gatekeeper; not implementation code) |

---

## Ticket linkage (Specification)

- **Authoritative requirements** for MAINT-TSGR are the numbered items **TSGR-1**–**TSGR-8** in this file. The ticket’s Description and Acceptance Criteria are the business intent; where they conflict, **this spec wins** until a Planner revises the ticket.
- **Bidirectional link:** The ticket MUST retain a `## Specification` section pointing to this path until the ticket is **COMPLETE** or **BLOCKED** with an explicit superseding spec path. Implementers and Test Designer map work to **TSGR-*** IDs; gatekeeper evidence references those IDs in the AC matrix.
- **Revision discipline:** Spec content changes after this handoff require a **Spec Agent** (or Planner-authorized) revision bump in this header and a ticket note if acceptance scope shifts.

---

## Background and Context

- **Today:** `ci/scripts/run_tests.sh` runs bounded `godot --headless --import` with `2>/dev/null || true`, then `timeout 300 godot --headless -s tests/run_tests.gd`. The import step **never fails the script** and **hides stderr**.
- **Lefthook:** `godot-tests.sh` runs `bin/godot --import` with `2>/dev/null || true` then `timeout 300` test run. `py-tests.sh` runs `pytest` with `.venv` → `uv run --extra dev` → `python3` fallback; exits `1` if pytest is missing.
- **Gap:** Python tests are **not** invoked from `ci/scripts/run_tests.sh`, so “run all tests” via CI script can miss `asset_generation/python/tests/`. Pre-push and CI can drift if two code paths implement the same policies differently.

---

## Requirement TSGR-1: Canonical combined test entry point

### 1. Spec Summary

**Description:** The repository MUST expose **one** documented primary command that runs **both** (a) the headless Godot suite via `tests/run_tests.gd` under a bounded `timeout`, and (b) the `asset_generation/python` pytest suite using the same effective policy as **TSGR-3**. The implementation MAY extend `ci/scripts/run_tests.sh` and/or add a thin repo-root wrapper, but **exactly one** command MUST be named as canonical in **TSGR-6**.

**Constraints:** The canonical entry point MUST be invocable from repo root (after normal project setup: `direnv` / `bin/godot` on PATH per `CLAUDE.md` where applicable). Godot MUST remain headless for the automated gate.

**Assumptions:** CI and local developers use the same script or wrapper once implemented; environment may or may not have `uv` or `.venv`—TSGR-3 defines required behavior.

**Scope:** Shell entry points and documentation only for this requirement; individual test file fixes are **TSGR-7**.

### 2. Acceptance Criteria

- **TSGR-1.1:** A single documented command runs Godot tests then Python tests **or** defines an explicit order if the spec mandates parallelism (default **sequential**: Godot then Python unless a later revision documents parallel and aggregation rules).
- **TSGR-1.2:** Running the canonical command without installing Python test deps fails in a way consistent with **TSGR-3** (clear message; non-zero exit).

### 3. Risk & Ambiguity Analysis

- **Risk:** Doubling runtime if both suites are always run—acceptable for quality gate; optimization is out of scope unless ticket expands.
- **Edge case:** Partial install (Godot OK, pytest missing)—must not report success.

### 4. Clarifying Questions

- None.

---

## Requirement TSGR-2: Import / reimport phase — bounded, fail-fast, observable

### 1. Spec Summary

**Description:** Any **import** or **reimport** step executed as part of the canonical combined run MUST use a **bounded** `timeout` (duration is implementation-chosen but MUST be documented in script comments and in **TSGR-6** summary; planning baseline cited **120s** for import in CI script—final value may match or be justified if changed). If the import process exits non-zero or is killed by `timeout`, the **combined script MUST exit non-zero** and MUST **not** proceed to the Godot test run as if import succeeded.

**Constraints:** Critical path steps MUST NOT use `|| true`, `set +e` swallowing, or equivalent **unless** a **narrow, documented bypass** exists per **TSGR-2.4**. Discarding **all** stderr for the import phase (`2>/dev/null` without tee/log) is **not allowed** on the fail-fast path—errors that determine failure MUST be visible in invoking terminal or a documented log file.

**Assumptions:** Godot `--import` may hang in pathological cases; `timeout` is mandatory.

**Scope:** Import/reimport only; test run timeouts are **TSGR-4**.

### 2. Acceptance Criteria

- **TSGR-2.1:** Import failure (non-zero exit) → combined entry point exits non-zero; Godot tests are not reported as the sole source of failure in a way that implies import succeeded.
- **TSGR-2.2:** Import killed by `timeout` → non-zero exit; same “no silent continue” rule as **TSGR-2.1**.
- **TSGR-2.3:** With successful import, test phase runs as today unless superseded by TSGR-1 ordering including Python.
- **TSGR-2.4 (narrow bypass):** If a bypass is required, it MUST be: (i) commented in shell with **why** and **scope** (e.g. single platform or CI flake); (ii) still **log** Godot stderr to a file or stdout; (iii) referenced from **TSGR-6** / `CLAUDE.md` in one sentence so contributors know success may mask import. Default expectation: **no bypass**.

### 3. Risk & Ambiguity Analysis

- **Risk:** Flaky import in CI—bypass temptation; spec prefers explicit logged bypass over silent `|| true`.
- **Edge case:** Godot writes warnings but exits 0—spec does not require failing on warnings unless ticket expands.

### 4. Clarifying Questions

- None.

---

## Requirement TSGR-3: Python test phase — parity with lefthook resolver

### 1. Spec Summary

**Description:** The Python phase MUST resolve the interpreter and pytest invocation **equivalently** to `.lefthook/scripts/py-tests.sh`: prefer `asset_generation/python/.venv/bin/python` if executable **and** `import pytest` succeeds; else if `uv` is on PATH, `uv run --extra dev pytest tests/ -q` from `asset_generation/python/`; else `python3 -m pytest tests/ -q` if `python3` can `import pytest`; else print install hint and exit **non-zero**.

**Constraints:** DRY is required at implementation time: **either** the canonical runner **sources/calls** `py-tests.sh`, **or** shared logic lives in one neutral script both lefthook and CI call—**no** duplicated resolver blocks that can drift (per planning assumption).

**Assumptions:** Test path remains `asset_generation/python/tests/` with pytest discovery as today.

**Scope:** Resolver and invocation only.

### 2. Acceptance Criteria

- **TSGR-3.1:** Given only `.venv` with dev deps, canonical run uses that Python (same as py-tests).
- **TSGR-3.2:** Given `uv` and no usable `.venv`, canonical run uses `uv run --extra dev` equivalent.
- **TSGR-3.3:** Missing pytest → exit non-zero and message mentioning `uv sync --extra dev` (or equivalent project standard).

### 3. Risk & Ambiguity Analysis

- **Edge case:** CI without `uv` and without `.venv`—must fail clearly or document required CI setup in **TSGR-6**.

### 4. Clarifying Questions

- None.

---

## Requirement TSGR-4: Exit code aggregation and timeouts

### 1. Spec Summary

**Description:** The canonical combined entry point MUST exit **non-zero** if any of: Godot import phase fails per **TSGR-2**; Godot test run returns non-zero; Godot test run is killed by `timeout`; Python phase returns non-zero; Python phase is killed by `timeout`. When both phases run sequentially, **any** failure MUST yield final non-zero. Successful phases MUST NOT reset or hide a prior failure (no overwriting `$?` without intentional aggregation).

**Constraints:** Godot test run MUST use a bounded `timeout` (planning baseline **300s**; document if changed).

**Assumptions:** `timeout` returns non-zero when it kills a process (standard GNU/coreutils behavior on Unix).

**Scope:** Shell-level aggregation; does not redefine `tests/run_tests.gd` internal exit codes.

### 2. Acceptance Criteria

- **TSGR-4.1:** Godot failures → final exit non-zero.
- **TSGR-4.2:** Python failures → final exit non-zero even if Godot passed.
- **TSGR-4.3:** `timeout` expiration on either phase → final exit non-zero.

### 3. Risk & Ambiguity Analysis

- **Edge case:** Signal handling / `130` from interrupt—acceptable as non-success for local use; CI uses non-interactive runs.

### 4. Clarifying Questions

- None.

---

## Requirement TSGR-5: Failure observability (crash vs assertion vs pytest)

### 1. Spec Summary

**Description:** **Assertion / test failures:** Covered by `tests/run_tests.gd` exit `1` and pytest non-zero—must propagate per **TSGR-4**. **Engine crash / abort** (signal, segfault, Godot panic): the shell MUST surface non-zero (typically from Godot process exit or `timeout`); the spec does not require parsing Godot logs if exit status is non-zero. **Unloadable suite** in `run_tests.gd`: already `quit(1)`—must not be masked by outer script.

**Constraints:** Do not add `|| true` around the Godot test invocation on the canonical path.

**Assumptions:** CI captures stdout/stderr from the script invocation.

**Scope:** Observable behavior at process boundary.

### 2. Acceptance Criteria

- **TSGR-5.1:** Simulated Godot exit `1` (or failing test) from canonical command → non-zero shell exit.
- **TSGR-5.2:** Simulated pytest failure → non-zero shell exit.
- **TSGR-5.3:** Canonical script does not treat Godot non-zero as success.

### 3. Risk & Ambiguity Analysis

- **Risk:** Some crashes may hang—mitigated by `timeout` on test run.

### 4. Clarifying Questions

- None.

---

## Requirement TSGR-6: `CLAUDE.md`, lefthook, and CI alignment

### 1. Spec Summary

**Description:** **`CLAUDE.md`:** “Common Commands” MUST document the **canonical** combined command (from **TSGR-1**), the Godot-only one-liner if still useful, and the **import** policy (bounded timeout, fail-fast summary in one sentence). Any statement that `run_tests.sh` is Godot-only MUST be removed or replaced when the script runs Python too. **`lefthook.yml` / hooks:** `godot-tests` and `py-tests` MUST either call the same shared implementation as CI or remain thin wrappers that **cannot diverge** in timeout, import policy, or resolver without updating the shared path. **CI:** Any workflow that runs `ci/scripts/run_tests.sh` MUST need no second hidden step to run Python tests (once this spec is implemented).

**Constraints:** Blog hook and other pre-push steps that intentionally always exit `0` are out of scope; only **godot-tests** and **py-tests** behavior must align with this spec’s runner policy.

**Assumptions:** `bin/godot` vs `godot` on PATH: CI script may keep using `godot` headless; lefthook uses `bin/godot`—both acceptable if documented and both obey TSGR-2/4.

**Scope:** Docs and hook/CI references; not blog generation.

### 2. Acceptance Criteria

- **TSGR-6.1:** `CLAUDE.md` names the single canonical full-suite command after implementation.
- **TSGR-6.2:** `.lefthook/scripts/godot-tests.sh` import + test behavior matches TSGR-2/4 **or** delegates to shared script updated in same change set.
- **TSGR-6.3:** `.lefthook/scripts/py-tests.sh` matches TSGR-3 **or** shared neutral script is the single resolver.

### 3. Risk & Ambiguity Analysis

- **Risk:** Contributors run `pytest` manually only—still OK if canonical command is clearly documented.

### 4. Clarifying Questions

- None.

---

## Requirement TSGR-7: Green suites — fix, skip, or quarantine

### 1. Spec Summary

**Description:** On `main` (or target branch for the ticket), the canonical combined run MUST complete with exit **0** when the tree is clean and all committed tests are in force. Any failing test MUST be **fixed in place** by default. **Skips/quarantines** are allowed only with a **tracked follow-up** (ticket ID or issue reference in skip reason or adjacent comment) and MUST NOT silently widen without Planner approval.

**Constraints:** Do not disable entire suites to green the runner without ticket-level justification.

**Assumptions:** Current failures (if any) are listed at implementation time; this spec does not name specific tests.

**Scope:** Test bodies and runner only as needed to achieve green; policy for future failures.

### 2. Acceptance Criteria

- **TSGR-7.1:** Canonical combined command exits `0` on clean branch after work completes.
- **TSGR-7.2:** Any `@pytest.mark.skip`, Godot early-return skip, or quarantine lists a follow-up reference or is absent (preferred: no skips).

### 3. Risk & Ambiguity Analysis

- **Risk:** Flaky tests—address with stability fix or documented quarantine per policy above.

### 4. Clarifying Questions

- None.

---

## Requirement TSGR-8: Closure evidence (gatekeeper)

### 1. Spec Summary

**Description:** Ticket closure MUST attach: exact command(s) run, last lines of output showing success **or** failure diagnosis, and list of touched test/runner files. Map results to **TSGR-*** IDs in the ticket Validation Status or checkpoint.

**Constraints:** Human gatekeeper or AC Gatekeeper agent per project workflow.

**Assumptions:** None.

**Scope:** Process only.

### 2. Acceptance Criteria

- **TSGR-8.1:** Validation Status or closure checkpoint cites the canonical command and exit code evidence.
- **TSGR-8.2:** TSGR-2 bypass (if any) is explicitly mentioned in evidence or “none” stated.

### 3. Risk & Ambiguity Analysis

- None.

### 4. Clarifying Questions

- None.

---

## Summary checklist (implementation / gatekeeper)

| ID | Verifiable outcome |
|----|--------------------|
| TSGR-1 | One canonical command runs Godot + Python suites |
| TSGR-2 | Bounded import; fail-fast; no silent stderr discard; bypass only per TSGR-2.4 |
| TSGR-3 | Python resolver matches lefthook / shared script |
| TSGR-4 | Aggregated non-zero on any failure or timeout |
| TSGR-5 | Crashes/failures surface as non-zero at shell |
| TSGR-6 | `CLAUDE.md` + hooks + CI aligned |
| TSGR-7 | Full combined run green on target branch |
| TSGR-8 | Closure evidence complete |
