# Spec: Automated Governance Checks for Handoffs — Rule Catalog, Enforcement, and Integrity

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/03_handoff_governance_rule_enforcement.md`

**Milestone:** 902 — Agent Predictability Improvements

**Agent:** Spec Agent

**Date:** 2026-05-15

**Status:** SPECIFICATION

**Revision:** 1

---

## Executive Summary

This specification defines **automated governance rule enforcement** for multi-agent handoffs in blobert. It encodes six categories of governance rules (architecture, exception safety, reflection safety, async safety, observability, and governance integrity) into deterministic, automatable checks using semgrep, import-linter, eslint, ruff, and custom gate modules.

The specification freezes:
- **Architecture boundaries** in Python backend (routers, services, adapters, domain layers) and React component hierarchy.
- **Allowed reflection zones** (routers, serializers, utilities, tests) with explicit suppressibility mechanisms.
- **Async blocking patterns** that are forbidden in FastAPI endpoints (sync network I/O, unbounded sleep).
- **Observability minimum fields** for critical backend flows (operation_id, duration_ms, error_type).
- **Governance bypass detection** (--no-verify flags, blanket linter disables, suppressions without issue links).

All rules are instrumentable via semgrep, import-linter, eslint, or custom Python gate modules. Rules are versioned and support suppressibility via `# nosemgrep <rule-id> <issue-link>` comments (Python) and eslint equivalents (TypeScript).

---

## Architecture & Layer Definitions

### Python Backend Layers (asset_generation/web/backend)

**Layer 1: Router (HTTP Boundary)**
- Files: `routers/*.py`
- Scope: Request parsing, path parameter extraction, HTTP status mapping, type coercion.
- Allowed Patterns: Direct `getattr`/`hasattr` for path handling, Pydantic model instantiation, exception mapping.
- Forbidden: Complex business logic, state mutation beyond request context.

**Layer 2: Service (Business Logic)**
- Files: `services/*.py`
- Scope: Core business rules, registry operations, error classification, Python asset module imports.
- Examples: `registry_mutation.py` (state updates), `registry_query.py` (read logic), `error_mapping.py` (exception classification).
- Allowed Patterns: Exception raising with semantic context, logging, type validation, delegation to domain/adapter layers.
- Forbidden: Direct HTTP response construction, unlogged state changes.

**Layer 3: Core/Adapter (Cross-Cutting & Boundaries)**
- Files: `core/*.py`, integration adapters (e.g., `services/python_bridge.py`)
- Scope: Configuration, environment resolution, cross-layer communication, Python runtime bootstrap.
- Allowed Patterns: Reflection (`importlib`, `sys.modules` patching), environment variable access, exception wrapping.
- Forbidden: Silently ignoring import errors, losing error context during re-raises.

**Layer 4: Domain (Pure Logic)**
- Imported modules (not in backend): `asset_generation/python/src/model_registry/*`, `blobert_asset_gen/*`.
- Scope: Data structures, validation rules, registry schema manipulation.
- Allowed: Type definitions, validation functions, data transformation (no HTTP, no environment).
- Forbidden: Importing FastAPI, HTTP libraries, or reaching back to backend routers.

### Python Asset Pipeline Layers (asset_generation/python/src)

**Layer 1: Domain (Core Model Logic)**
- Scope: Blender procedural generation, schema validation, material/animation systems, enemy/player builders.
- Examples: `model_registry/`, `enemies/`, `player/`, `materials/`, `core/rig_models/`.
- Allowed: Pure functions, type validation, exception raising with semantic context.
- Forbidden: I/O operations (files, network) outside of designated adapter layers.

**Layer 2: Adapter/Integration**
- Scope: Blender integration (`core/blender_utils.py`), Godot export (`blobert_asset_gen/`), file I/O.
- Allowed: Exception wrapping, logging, unvalidated dict/JSON at parsing boundaries.
- Forbidden: Reflection for domain object construction; use factories instead.

### TypeScript/React Component Boundaries (asset_generation/web/frontend)

**Layer 1: Route/Page Components**
- Scope: Entry points (e.g., `App.tsx`), route registration, top-level layout.
- Allowed Patterns: State initialization via hooks, API calls, error boundaries.

**Layer 2: Feature Components**
- Scope: Domain-specific UI (model viewer, registry editor, material picker).
- Allowed: Internal state (useState), side effects (useEffect with dependency arrays).
- Forbidden: Circumventing dependency array rules, hard-coded API paths.

**Layer 3: Presentational Components**
- Scope: Reusable UI primitives (buttons, forms, cards).
- Allowed: Props-driven rendering, no side effects (pure components).
- Forbidden: State management, API calls.

**Layer 4: Utilities/Hooks**
- Scope: Shared logic (custom hooks, API clients, formatters).
- Allowed: Custom hooks with proper cleanup, API abstraction layers.
- Forbidden: Direct DOM manipulation, untracked async operations.

---

## Governance Rule Catalog

### Category 1: Architecture (Dependency Direction & Layer Enforcement)

| # | Rule ID | Rule Name | Tool | Scope | Pattern | Severity | Suppressible |
|---|---------|-----------|------|-------|---------|----------|--------------|
| AR-01 | `arch-no-domain-http` | Domain code must not import HTTP libraries | semgrep + import-linter | `asset_generation/python/src/{model_registry,enemies,player,materials,core}/**/*.py` | No imports of `fastapi`, `flask`, `requests`, `urllib` from domain modules | ERROR | No (structural violation) |
| AR-02 | `arch-no-router-logic` | Router files must delegate to service layer | sempreg (custom pattern) | `asset_generation/web/backend/routers/*.py` | Complex logic (>10 LOC) in router handlers; must call service functions | WARN | Yes (with design review link) |
| AR-03 | `arch-service-not-http` | Service layer must not construct HTTP responses | import-linter | `asset_generation/web/backend/services/*.py` | No direct `fastapi.Response` or `JSONResponse` construction outside core/error_mapping | ERROR | No (structural) |
| AR-04 | `arch-forbidden-reverse-imports` | Services/adapters must not import from routers | import-linter | `asset_generation/web/backend/**/*.py` | No imports from `routers` module in `services/` or `core/` | ERROR | No (structural) |
| AR-05 | `arch-react-hook-deps` | React hooks must include proper dependency arrays | eslint-plugin-react-hooks | `asset_generation/web/frontend/src/**/*.{ts,tsx}` | All `useEffect`, `useCallback`, `useMemo` have explicit dependency arrays matching closure captures | ERROR | Yes (with performance review) |
| AR-06 | `arch-feature-boundary` | Feature components must not directly import from other features | eslint-plugin-boundaries | `asset_generation/web/frontend/src/features/**/*.tsx` | No cross-feature imports except via shared/lib | WARN | Yes (with refactoring plan) |

### Category 2: Exception Safety (Error Handling & Propagation)

| # | Rule ID | Rule Name | Tool | Scope | Pattern | Severity | Suppressible |
|---|---------|-----------|------|-------|---------|----------|--------------|
| EX-01 | `except-no-bare` | No bare `except:` clauses | semgreg + ruff (E722) | All Python code | All exception handlers must specify exception type: `except SpecificError:` | ERROR | No (correctness) |
| EX-02 | `except-no-silent-swallow` | Exception handlers must log or re-raise | sempreg (custom) | `asset_generation/web/backend/**/*.py`, `asset_generation/python/src/**/*.py` | `except ... : pass` or single-line handlers that do not log/re-raise | ERROR | No (safety) |
| EX-03 | `except-preserve-context` | Re-raised exceptions must preserve context via `from e` | sempreg (custom) | All Python code | `raise NewException(...)` without `from original_exception` when inside except block | WARN | Yes (design context needed) |
| EX-04 | `except-handler-must-log` | Critical handlers must log before returning/re-raising | sempreg (custom) | `asset_generation/web/backend/routers/*.py`, `services/*.py` | Exception handlers in routes/services without prior `logger.*` call | WARN | Yes (with logging context) |
| EX-05 | `except-no-bare-promise-reject` | TypeScript: no bare Promise rejections | sempreg (custom TS) | `asset_generation/web/frontend/src/**/*.tsx` | `catch(e) { /* no rethrow */ }` without re-throw or proper handling | WARN | Yes (with flow documentation) |

### Category 3: Reflection Safety (Type Introspection & Mutation Boundaries)

| # | Rule ID | Rule Name | Tool | Scope | Pattern | Severity | Suppressible |
|---|---------|-----------|------|-------|---------|----------|--------------|
| RF-01 | `reflect-getattr-scoped` | `getattr`/`hasattr` must be in allowed zones | sempreg (custom) | All Python code | `getattr(obj, name)` only in: routers, serializers (utilities/), tests | WARN | Yes (allow-zone review) |
| RF-02 | `reflect-setattr-forbidden` | No `setattr` on domain objects | sempreg (custom) | `asset_generation/python/src/{model_registry,enemies,player,materials}/**/*.py` | `setattr(domain_obj, ...)` forbidden; use factory/builder pattern | ERROR | No (API integrity) |
| RF-03 | `reflect-dict-mutation-forbidden` | No `__dict__` direct mutation | sempreg (custom) | All Python code | `obj.__dict__[...] = ...` only in tests, adapters | WARN | Yes (refactor review) |
| RF-04 | `reflect-import-validation` | Dynamic imports must validate module names | sempreg (custom) | `asset_generation/web/backend/services/python_bridge.py` and equivalents | `importlib.import_module(name)` must validate `name` against allowlist before import | ERROR | No (security) |
| RF-05 | `reflect-type-check-explicit` | Type checks must use `isinstance`, not `type(x) ==` | sempreg (custom) | All Python | Forbidden: `type(obj) == ClassName`; required: `isinstance(obj, ClassName)` | INFO | No (style) |

### Category 4: Async Safety (Blocking Patterns in Async Contexts)

| # | Rule ID | Rule Name | Tool | Scope | Pattern | Severity | Suppressible |
|---|---------|-----------|------|-------|---------|----------|--------------|
| AS-01 | `async-no-sync-network` | FastAPI routes must use async HTTP clients | sempreg (custom) | `asset_generation/web/backend/routers/*.py`, `services/*.py` | Forbidden: `requests.get/post/put/delete()`, `urllib.request.urlopen()` in async functions | ERROR | No (performance) |
| AS-02 | `async-no-unbounded-sleep` | FastAPI routes must not sleep without timeout | sempreg (custom) | `asset_generation/web/backend/routers/*.py` | Forbidden: `time.sleep(duration)` where `duration` is not a small constant (<1s) | ERROR | Yes (with timeout context) |
| AS-03 | `async-subprocess-timeout` | Subprocess calls must include timeout parameter | sempreg (custom) | `asset_generation/web/backend/**/*.py` | `subprocess.run/call/Popen(...)` must include `timeout=` parameter (unless specifically allowlisted) | WARN | Yes (with timeout justification) |
| AS-04 | `react-hook-effect-cleanup` | useEffect cleanup must be registered | eslint-plugin-react-hooks | `asset_generation/web/frontend/src/**/*.tsx` | `useEffect` with network/subscription must return cleanup function | ERROR | No (correctness) |
| AS-05 | `react-hook-missing-deps` | useEffect dependency arrays must be complete | eslint-plugin-react-hooks | `asset_generation/web/frontend/src/**/*.tsx` | All captured variables in effect body must appear in dependency array | ERROR | No (correctness) |

### Category 5: Observability (Structured Logging & Tracing)

| # | Rule ID | Rule Name | Tool | Scope | Pattern | Severity | Suppressible |
|---|---------|-----------|------|-------|---------|----------|--------------|
| OB-01 | `obs-critical-flows-log` | Critical backend flows must log operation_id and duration | custom Python gate | `asset_generation/web/backend/routers/*.py` POST/PUT/DELETE routes | Must contain: `logger.info(...operation_id=..., duration_ms=...)` or equivalent structured field | WARN | Yes (with logging context) |
| OB-02 | `obs-error-type-logged` | Exception handlers must log error_type | sempreg (custom) | `asset_generation/web/backend/**/*.py` exception handlers | `logger.error(..., error_type=..., exc_info=True)` or structured equivalent | WARN | Yes (with context) |
| OB-03 | `obs-user-context-if-applicable` | Routes handling user-scoped operations must log user_context | custom Python gate | `asset_generation/web/backend/routers/**/*.py` | Routes that act on user data must include `user_context=` in logs if session/auth present | INFO | Yes (optional for MVP) |
| OB-04 | `obs-no-bare-print` | No bare `print()` statements in backend | sempreg (custom) | `asset_generation/web/backend/**/*.py` | Forbidden: `print(...)` in routers/services; use `logger` | WARN | No (hygiene) |
| OB-05 | `obs-console-use-discouraged` | Discourage bare `console.log` in React | eslint | `asset_generation/web/frontend/src/**/*.tsx` | `console.log()` in production code; acceptable in tests | WARN | Yes (enable per-file) |

### Category 6: Governance Integrity (Bypass Prevention & Suppression Abuse)

| # | Rule ID | Rule Name | Tool | Scope | Pattern | Severity | Suppressible |
|---|---------|-----------|------|-------|---------|----------|--------------|
| GV-01 | `gov-no-git-no-verify` | No `--no-verify` in committed source | grep-based gate | All committed files | Forbidden: `--no-verify` in scripts, CI files, deployment instructions | ERROR | No (enforcement) |
| GV-02 | `gov-suppression-requires-issue` | Suppressions must cite issue or ticket | sempreg + custom | All suppressions in code | Every `# nosemgrep`, `# noqa`, `# eslint-disable` must include issue link (URL or ticket id) | WARN | No (accountability) |
| GV-03 | `gov-no-blanket-linter-disable` | Linter disables must be granular | sempreg + eslint-custom | All code | Forbidden: `# eslint-disable` (bare); required: `# eslint-disable <rule-names>` | ERROR | No (clarity) |
| GV-04 | `gov-no-sempreg-disable-all` | No blanket semgrep disables | grep-based | All code | Forbidden: `# nosemgrep` (bare); required: `# nosemgrep <rule-id>` | WARN | No (audit trail) |
| GV-05 | `gov-gate-bypass-detection` | No attempts to bypass gate runner | custom gate | CI scripts, pre-commit hooks, task definitions | Forbidden: Direct invocation of linters without gate runner; forbidden: conditional skips of gates | WARN | No (process integrity) |
| GV-06 | `gov-process-audit-trail` | Gate execution must be logged | custom gate | Gate runner invocations | All gate executions (shadow or blocking) must record: gate name, mode, result file path, timestamp | WARN | No (auditability) |

---

## Allowed Reflection Zones & Suppressibility

### Python Allowed Zones (Explicitly Permitted)

**Zone A: Routers (HTTP Parameter Handling)**
- File pattern: `asset_generation/web/backend/routers/*.py`
- Allowed operations: `getattr(request_obj, param_name)`, `hasattr(obj, "field")` for optional field checks, `getattr(obj, "__name__")` for introspection.
- Example: `entity_type = getattr(request, "kind", "player")` for optional query params.
- Suppression: `# nosemgrep RF-01 M902-03-architectural-review`

**Zone B: Serializers/Schema Mappers (Validation Helpers)**
- File pattern: `asset_generation/web/backend/routers/*.py` (Pydantic models), utilities for schema validation.
- Allowed operations: `getattr(model, "__fields__")` for schema introspection, mapping dicts to objects.
- Example: Building dict from model via field iteration.
- Suppression: `# nosemgrep RF-01 M901-18-json-schema-mapper`

**Zone C: Utilities (Generic Helpers)**
- File pattern: `asset_generation/python/src/utils/*.py`, `asset_generation/web/backend/core/*.py`
- Allowed operations: Generic validation functions that introspect any object type.
- Example: `_validate_module_name()` checking attribute existence.
- Suppression: `# nosempreg RF-01 M902-03-utility-pattern`

**Zone D: Tests (Mocking & Fixtures)**
- File pattern: `**/tests/**/*.py`, `**/__tests__/**/*.tsx`
- Allowed operations: Unrestricted reflection for mocking, monkeypatching, fixture setup.
- Example: Test mocking via `patch("module.name")`, monkeypatching instance attributes.
- Suppression: Not required; tests are exempt from RF-01/RF-02 checks.

### Suppression Format (Python sempreg Rules)

Standard suppression syntax:
```python
# nosempreg <rule-id> <justification-id>
# Example: nosempreg RF-01 M902-03-zone-A-router-getattr
getattr(obj, "param")
```

Justification IDs must reference:
1. Zone name (Zone A, B, C, D)
2. Ticket ID (e.g., M902-03)
3. Brief context (what justifies the exception)

Invalid suppressions:
```python
# nosemprep  # INVALID: no rule-id
# nosemprep RF-01  # INVALID: no justification
# nosemprep RF-01 "This one time"  # INVALID: not an issue/ticket reference
```

### TypeScript Allowed Zones

**Zone A: Feature Components (State Management)**
- Pattern: useState, useCallback, useMemo allowed per dependency rules.
- Suppression: `// eslint-disable-line react-hooks/exhaustive-deps -- <issue-id>`

**Zone B: API Client Utilities**
- Pattern: Async data fetching, cache invalidation.
- Suppression: `// eslint-disable-next-line no-console -- <ticket-id>`

---

## Async Blocking Patterns Checklist

### Forbidden in FastAPI Endpoints

1. **Synchronous Network I/O**
   - `requests.get/post/put/delete()` → Use `httpx.AsyncClient` or `aiohttp`
   - `urllib.request.urlopen()` → Use `httpx` async
   - `socket.socket().connect()` → Use async TCP libraries

2. **Unbounded Sleep**
   - `time.sleep(5)` → Use `asyncio.sleep(5)` with timeout context
   - Exception: Small delays (<100ms) for polling are okay; must be in loop with timeout

3. **Blocking Subprocess Calls**
   - `subprocess.run(...)` without `timeout` → Must include `timeout=` (e.g., `timeout=30`)
   - Exception: Subprocess with timeout is allowed; timeout-less is error

4. **Database Calls Without Async Driver**
   - `sqlite3.connect().execute()` → Use async library (asyncpg, motor, etc.)
   - Exception: Read-only context manager with short duration is warning-only

### Allowed Patterns

1. **Async I/O**
   - `async with httpx.AsyncClient() as client: await client.get(url)`
   - `async with asyncio.timeout(30): ...`

2. **CPU-Bound Operations (If Brief)**
   - Calculation, hashing, JSON parsing: allowed (no I/O overhead)

3. **Coroutine Yields**
   - `await asyncio.sleep(0)` for yielding control: allowed

---

## Observability Minimum Fields (Structured Logging)

### Required Fields for Critical Backend Flows

**Critical flows:** FastAPI POST/PUT/DELETE routes, registry mutations, asset generation triggers.

**Minimum structured log fields:**

```python
{
    "operation_id": "uuid-or-request-id",      # Trace identifier
    "duration_ms": 145,                          # Elapsed time
    "error_type": "ValueError | None",           # Exception class name (on error)
    "status": "success | error",                 # Overall outcome
    "severity": "INFO | WARN | ERROR",           # Log level
    # Optional:
    "user_context": "user-id | session-id",     # If applicable
    "resource_type": "enemy | player | registry" # What was affected
    "action": "create | update | delete"        # What happened
}
```

### Implementation Pattern

```python
import logging
import time
from uuid import uuid4

logger = logging.getLogger(__name__)

async def create_player(request: PlayerCreateRequest):
    op_id = str(uuid4())
    start = time.time()
    try:
        # ... business logic ...
        duration_ms = int((time.time() - start) * 1000)
        logger.info(
            "player created",
            extra={
                "operation_id": op_id,
                "duration_ms": duration_ms,
                "status": "success",
                "resource_type": "player"
            }
        )
        return result
    except ValueError as e:
        duration_ms = int((time.time() - start) * 1000)
        logger.error(
            "player creation failed",
            exc_info=True,
            extra={
                "operation_id": op_id,
                "duration_ms": duration_ms,
                "error_type": "ValueError",
                "status": "error"
            }
        )
        raise HTTPException(status_code=400, detail=str(e)) from e
```

---

## Governance Bypass Detection Rules

### Detection Patterns (Grep-Based Gate)

The governance gate scans changed/committed files for:

1. **Git Hook Bypass Flag**
   - Pattern: `--no-verify` in scripts, CI/CD instructions, documentation
   - Severity: ERROR
   - Confidence: 100% (string literal match)

2. **Blanket Linter Disables**
   - Pattern: `# eslint-disable\s*$` (no rule name)
   - Pattern: `# noqa\s*$` (bare, no codes)
   - Severity: ERROR
   - Confidence: 90% (may have false positives on comments)

3. **Blanket Sempreg Disables**
   - Pattern: `# nosempreg\s*$` (no rule-id)
   - Pattern: `# nosemprep` (typo detection)
   - Severity: WARN
   - Confidence: 95%

4. **Suppressions Without Issue Links**
   - Pattern: `# nosempreg <rule> (?!https?:// | M\d{3}-\d{2} | JIRA- | GH-\d+)`
   - Pattern: `# eslint-disable-line (?!.*https?:// | .*M\d{3})`
   - Severity: WARN
   - Confidence: 85%

5. **Gate Runner Bypass Attempts**
   - Pattern: Direct sempreg/eslint/ruff invocation in shell scripts (outside gate runner)
   - Pattern: Conditional skips: `if [ ... ]; then skip_gate`
   - Severity: WARN
   - Confidence: 70% (heuristic)

---

## Tool Selection Justification

| Tool | Category | Why Selected | Constraints |
|------|----------|--------------|-------------|
| **sempreg** | Architecture, Exception, Reflection, Async, Governance | Cross-language patterns, complex logic detection, custom rules, suppressible | Requires local rule authoring; initial false-positive risk |
| **import-linter** | Architecture | Dependency direction enforcement, layer boundary validation | Python-only; requires explicit configuration of layers |
| **ruff** | Exception (bare except) | Built-in E722 rule, fast, already in project | Limited to simple syntax checks; sempreg handles logic |
| **eslint-plugin-react-hooks** | Async (React) | Official React linting, catches dependency array violations | Requires eslint config; may conflict with other plugins |
| **eslint-plugin-boundaries** | Architecture (React) | Feature boundary enforcement via config | Requires careful setup to avoid false positives |
| **custom Python gate** | Observability, Governance | Domain-specific checks that linters can't express (e.g., logging patterns, process integrity) | Requires custom implementation; harder to maintain |
| **grep-based gate** | Governance | Bypass detection (--no-verify, blanket disables) | Simple pattern matching; low false-positive rate for governance patterns |

---

## Assumptions & Checkpoint Resolutions

| # | Ambiguity | Assumption | Confidence |
|---|-----------|-----------|------------|
| A1 | What counts as a "router"? | Files in `routers/*.py` with request handlers decorated with `@app.post`, `@app.get`, etc. Functions that are HTTP entry points. | High |
| A2 | What counts as "domain"? | Files in `asset_generation/python/src/{model_registry,enemies,player,materials,core/rig_models}` and their imported modules (no HTTP, no environment). | High |
| A3 | Can reflection be used in adapters? | Yes, adapters (integration layer, core/config) are allowed to use reflection for environment resolution, module bootstrap, and exception wrapping. Must log errors. | High |
| A4 | Does "async blocking" apply to all Python? | Only FastAPI route handlers and their direct callees in `routers/*.py` and `services/*.py` when called from routes. Does not apply to background tasks (Celery, etc.) or CLI scripts. | High |
| A5 | What is the "observability minimum"? | At least operation_id, duration_ms, error_type, and status in structured logs for mutation routes (POST/PUT/DELETE). Applies to FastAPI backends; not Godot/frontend. | High |
| A6 | Can tests bypass governance rules? | Yes, tests are exempt from RF-01, RF-02, EX-01 checks. Tests use mocking and reflection freely. | High |
| A7 | What severity mapping applies? | ERROR = blocking in `blocking` mode, non-blocking in `shadow` mode. WARN = advisory in both modes. INFO = informational only. | High |
| A8 | How are baseline violations handled in M902? | All violations are captured in shadow mode (non-blocking). Task 2 audit identifies suppressible vs. unsuppressible. Suppressible violations are grandfathered with issue links in M902; unsuppressible are fixed incrementally or deferred to M903. | Medium |

---

## Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Semprep rule false-positive rate | Excessive noise → team ignores violations | Start with narrow scopes (routers only), audit baseline (Task 2), refine rules based on feedback |
| Import-linter layer configuration complexity | Misconfiguration → rules don't enforce | Use simple, explicit layer definitions; test configuration on codebase before committing |
| Async blocking patterns may be too strict | Valid patterns flagged (e.g., short polling loops) | Support suppressibility with `# nosempreg AS-02 <issue>`; reviewers validate during handoff |
| Observability minimum fields not enforced in all routes | Incomplete tracing data | Custom gate checks routes that mutate state; reviewers validate during code review |
| Suppression abuse (blanket `# nosempreg` without links) | Governance integrity deteriorates | GV-02 gate detects bare suppressions; pre-commit gate blocks commits without issue links in M903 |
| Baseline violations not tracked → hard to remediate | Drift over time; unclear what to fix first | Task 2 audit creates inventory with file/line; Task 10 validates shadow mode baseline |
| Tool version drift (semprep, ruff, eslint updates) | Rule behavior changes unexpectedly | Pin tool versions in pyproject.toml, package.json, .semprep.yml; M903 includes update policy |

---

## Clarifying Questions & Decisions Frozen

**Q1: Should adapters be allowed to import from routers?**
- Decision (Frozen): No. Adapters (core/, services/) must not import routers. Routers import from services; services may import from adapters if needed for configuration/bootstrap, but not for handling requests. Violates AR-04.

**Q2: Should reflection in __init__ module constructors be allowed?**
- Decision (Frozen): Reflection is forbidden for domain object construction (RF-02). Use factory pattern instead. Reflection in __init__ is allowed only for configuration/bootstrap in adapters (core/config.py) with suppression.

**Q3: Can async functions sleep for test purposes?**
- Decision (Frozen): No bare `time.sleep()` in FastAPI routes (AS-02). Use `asyncio.sleep()` with timeout context. Test fixtures may use sleep with explicit timeout.

**Q4: What if observability minimum fields conflict with existing logging?**
- Decision (Frozen): All routes must have structured fields (operation_id, duration_ms). Existing logging is augmented; no breaking changes required. Suppressible with OB-01 until M903.

**Q5: Should Godot GDScript be included in governance?**
- Decision (Frozen): Out of scope for M902. Godot code is not included in semprep/eslint/ruff scans. M903 evaluates GDScript governance rules.

---

## Spec Completeness Checklist

- [x] All six governance categories have rule definitions (AR-01..06, EX-01..05, RF-01..05, AS-01..05, OB-01..05, GV-01..06)
- [x] Each rule specifies: rule_id, scope (file patterns), pattern (what is forbidden/required), severity, suppressibility
- [x] Architecture boundaries are documented with explicit file paths and allowed patterns
- [x] Allowed reflection zones (A, B, C, D) are defined with examples and suppression format
- [x] Async blocking patterns are enumerated with allowed exceptions
- [x] Observability minimum fields are specified with example implementation
- [x] Governance bypass detection patterns are defined (git --no-verify, blanket disables, etc.)
- [x] Tool selection is justified (why each tool for each category)
- [x] All assumptions are stated and resolved
- [x] Risks and ambiguities are analyzed with mitigations
- [x] Clarifying questions are resolved and frozen
- [x] Spec is deterministic and actionable for semprep rule authoring, gate implementation, and test design

---

## Next Actions (Task Decomposition)

1. **Task 2 (Spec Agent):** Audit Python and TypeScript codebases against rules; create baseline violation inventory.
2. **Task 3 (Spec Agent):** Implement sempreg YAML rules for Python/TypeScript patterns not covered by native linters.
3. **Task 4 (Spec Agent):** Design gate module (`governance_check.py`) that orchestrates sempreg, import-linter, eslint, and custom checks.
4. **Task 5 (Spec Agent):** Create comprehensive documentation (rule catalog, architecture boundaries, gate invocation guide, M903 roadmap).
5. **Task 6+ (Test Designer, Implementation, Acceptance):** Implement gate, tests, integration, and final validation per execution plan.

---

**End of Specification Document**
