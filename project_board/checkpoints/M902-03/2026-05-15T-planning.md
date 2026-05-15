# M902-03 Handoff Governance Rule Enforcement — Planning

## Run Details

- **Ticket:** project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/03_handoff_governance_rule_enforcement.md
- **Ticket ID:** M902-03-handoff-governance-rule-enforcement
- **Stage:** PLANNING → SPECIFICATION
- **Agent:** Planner Agent
- **Run ID:** 2026-05-15T-planning
- **Date:** 2026-05-15

## Execution Plan Frozen

Decomposed ticket into 10 sequential tasks:

1. **Spec Agent:** Governance rule specification (rule catalog, architecture boundaries, design freezes)
2. **Spec Agent:** Baseline audit (violation inventory, severity tiers, remediation roadmap)
3. **Spec Agent:** Semprep rule implementation (YAML configs, Python/TS patterns)
4. **Spec Agent:** Gate module design (governance_check.py integration, JSON schema, modes)
5. **Spec Agent:** Documentation (rule catalog, architecture doc, invocation guide, M903 roadmap)
6. **Test Designer:** Behavioral test suite (rule correctness, suppression, schema, modes, edge cases)
7. **Test Breaker:** Adversarial test suite (evasion attempts, suppression abuse, config mutations)
8. **Implementation Agent:** Gate module implementation (parse/map/emit, register, test fixes)
9. **Implementation Agent:** Workflow integration (gate_registry.json, Taskfile task)
10. **Acceptance Gatekeeper:** Final validation (baseline counts, AC verification, ticket closure)

## Dependency Verification

- **M902-01 (Validation Gate Framework):** COMPLETE
  - gate_runner.py ✓
  - gate_registry.json structure ✓
  - gate result JSON schema (failure, success) ✓
  - 220 behavioral tests PASS ✓

- **M902-02 (Static Analysis Gate Tooling):** COMPLETE
  - Python tools (ruff, mypy, bandit, vulture, import-linter, semgrep, wemake) ✓
  - TypeScript tools (eslint, typescript-eslint, plugins) ✓
  - Semprep framework available ✓
  - Static analysis orchestrator (ci/scripts/gates/static_analysis_check.py) ✓
  - Taskfile hooks in place ✓

## Key Design Decisions Frozen

### Governance Categories & Automation

1. **Architecture Enforcement**
   - Tool: semprep + import-linter + eslint-plugin-boundaries
   - Scope: Python routers, services, adapters; TS component imports
   - Rule IDs: ARCH-001 through ARCH-00N

2. **Exception Safety**
   - Tool: semprep + pylint
   - Patterns: bare except, exception-only handlers, swallowed exceptions
   - Rule IDs: EXSAFE-001 through EXSAFE-00N

3. **Reflection Safety**
   - Tool: semprep (scoped to allowed zones)
   - Allowed zones: routers, serializers, utilities, tests
   - Forbidden: domain layer mutation
   - Rule IDs: REFL-001 through REFL-00N

4. **Async Safety**
   - Tool: semprep (Python), eslint-plugin-react-hooks (TS)
   - Patterns: blocking I/O in async endpoints, missing cleanup
   - Rule IDs: ASYNC-001 through ASYNC-00N

5. **Observability**
   - Tool: Custom Python checks + semprep pattern matching
   - Minimum fields: operation_id, duration_ms, error_type, (optional) user_context
   - Rule IDs: OBS-001 through OBS-00N

6. **Governance Integrity**
   - Tool: Grep-based + semprep patterns
   - Patterns: --no-verify, # eslint-disable (bare), # nosemprep (bare)
   - Rule IDs: GOV-001 through GOV-00N

### Architecture Boundaries (Frozen)

**Python Backend Layers:**
- **Routers** (asset_generation/web/backend/routers/): HTTP entry points, path/query parsing
  - Allowed: getattr, type coercion, schema validation via Pydantic
  - Forbidden: domain logic, business rule enforcement
- **Services** (asset_generation/web/backend/services/): Business logic, state mutation
  - Allowed: logging, data transformation
  - Forbidden: reflection outside serializers
- **Adapters** (asset_generation/web/backend/core/): Boundary crossings, registry, config
  - Allowed: reflection for dynamic loading
  - Forbidden: hard dependencies on domain
- **Domain** (asset_generation/python/src/model_registry, combat, etc.): Pure business logic
  - Forbidden: reflection, I/O, HTTP dependencies

**React Components:**
- Allowed: useEffect cleanup, useMemo dependencies, React hooks patterns
- Forbidden: untracked side effects, missing dependency arrays

### Allowed Reflection Zones (Frozen)

```
routers/        ✓ path parameter extraction
serializers     ✓ schema mapping
utilities/      ✓ generic validation
tests/          ✓ mocking, fixtures
domain/         ✗ forbidden (fail on getattr/setattr in services, models)
```

### Async Blocking Patterns (Frozen)

**Block on:**
- requests.get(), urllib3 calls
- time.sleep() in async context
- subprocess.run() / os.system() without timeout
- Sync DB queries without async driver

**Allow:**
- Lightweight CPU operations
- Coroutine yields (await, await asyncio.gather())
- FastAPI background tasks (fire-and-forget)
- Timeout-bounded subprocess

## Assumptions & Checkpoints

### Assumption 1: Architecture Boundaries Are Derivable
**Would have asked:** Are the existing routers/services/adapters/domain layers the correct model?
**Assumption made:** Yes; codebase structure matches layered patterns (routers = HTTP entry, services = logic, adapters = bridge, domain = pure).
**Confidence:** High. Ticket context mentions "routers", "services", "adapters" explicitly. Existing code aligns.

### Assumption 2: Allowed Reflection Zones Are Complete
**Would have asked:** Are there other zones (middleware, decorators, config loaders) that need reflection?
**Assumption made:** No; four zones (routers, serializers, utilities, tests) cover 99% of legitimate use cases.
**Confidence:** High. Reflection in FastAPI is typically routers (Pydantic) + serializers (JSONEncoder). Custom utilities are rare.

### Assumption 3: Async Blocking Patterns Are Machine-Detectable
**Would have asked:** Can semprep reliably detect time.sleep() vs legitimate CPU ops?
**Assumption made:** Yes, for common patterns (requests.*, time.sleep, subprocess, DB libs). Edge cases documented for manual review.
**Confidence:** Medium. Semprep patterns may need tuning based on Task 2 audit; false-positive mitigation in Task 3.

### Assumption 4: Sempreg Is Available in M902-02 Tools
**Would have asked:** Is sempreg installed and working?
**Assumption made:** Yes; M902-02 evidence shows semprep.yml configs created, tests passing.
**Confidence:** High. Semprep is listed in pyproject.toml (M902-02).

### Assumption 5: Gate Registry Supports Custom Categories
**Would have asked:** Can gate_registry.json add new category "governance" or must we use "analysis"?
**Assumption made:** New category "governance" is allowed; gate runner from M902-01 supports heterogeneous categories.
**Confidence:** High. M902-01 gate runner is category-agnostic; registry is key-value, no enum constraint documented.

### Assumption 6: Suppressibility Mechanism Is --no-verify Equivalent
**Would have asked:** How do developers suppress governance violations (for transition period)?
**Assumption made:** Via `# nosemprep: issue=M903-XX` comment; mapped by gate module to valid suppression.
**Confidence:** Medium. Semprep standard is `# nosemgrep`; we add `issue=` metadata for traceability.

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| Semprep rule false-positives (e.g., reflection in utility helpers) | Medium | Medium | Task 2 audit baseline identifies patterns; Task 3 rules scoped narrowly; Task 6 tests validate |
| Architecture boundary ambiguity (what counts as "domain"?) | Low | High | Task 1 spec freezes layer definitions with file path examples; Task 2 audit validates |
| Tool unavailability (semprep, import-linter not in PATH) | Low | Medium | M902-02 dependency satisfies; gate gracefully skips missing tools and logs warning |
| Rule enforcement blocks CI prematurely | Low | High | Shadow mode by design (Task 4); enforcement deferred to M903; documented exit code behavior |
| Suppression abuse (developers bypass checks with fake issue links) | Medium | Medium | Task 7 adversarial tests cover evasion; Task 8 impl validates issue link format (optional in MVP) |
| Documentation drift (rules vs catalog mismatch) | Low | Low | Task 5 docs auto-generated from spec + gate module; tests validate consistency |

## Blockers & Unknowns

**None identified.** All dependencies are satisfied. Architecture boundaries are clear from codebase. Sempreg is available and tested.

## Next Steps

1. Spec Agent begins Tasks 1-5 (spec, audit, rules, gate design, docs)
2. Awaiting Task 1 spec completeness check before Test Designer begins Task 6
3. Acceptance validation (Task 10) deferred to end-of-cycle after all implementation tasks complete

## Commit Readiness

No code changes in this planning run; only ticket documentation updated.

Next commit (after Spec Agent tasks): `feat(ci): define governance rule catalog and baseline audit for M902-03`
