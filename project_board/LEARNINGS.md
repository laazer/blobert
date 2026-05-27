# Autopilot Learnings Log

Structured insights extracted after each completed ticket.

---

## [M902-12] — Late Specification Contradictions Require Systematic Multi-Domain Alignment
*Completed: 2026-05-19*

### Critical Learning

**Specification contradictions discovered during implementation validation (not design review) expose misalignment between formal requirements, test vectors, and code. Resolving these requires systematic re-verification across all three domains, not just fixing one artifact.** The contradiction in M902-12 was caught late because test vectors and band definitions lived in the same spec document but were evaluated in isolation.

### Learnings

- **category: testing**
  **insight:** Test vectors can contradict formal requirements even when both are in the same spec document. Test vectors are often written from intuition or prior examples, while formal requirements may be written more rigorously. Contradictions surface only when implementation forces a choice.
  **impact:** Test vectors (TV-02, TV-03, TV-04, TV-09, TV-14) expected score-based band classification (weight 3 → score 15 → band EXIT), while Requirement 03 clearly stated weight-based thresholds. Implementation correctly chose weight-based (per spec intent), but 10+ test assertions had to be corrected post-implementation.
  **prevention:** At spec freeze (before Test Designer), run a consistency check: pick 5–10 test vectors and manually compute expected outputs using the formal formula. If results don't match test vector expectations, route to Spec Agent for contradiction resolution before Test Designer begins.
  **severity:** high

- **category: architecture**
  **insight:** Semantic domain boundaries (weight scale [0-20] vs score scale [0-100]) are easy to confuse when both scales are present in the same module. Mapping band thresholds to the wrong scale is a subtle but high-impact mistake.
  **impact:** Requirement 03 text said "classifies risk_score into a band" (ambiguous: could mean score-based), but implementation comment and code governance used weight-based. This dual interpretation persisted until AC Gatekeeper verified the implementation and discovered test assertion mismatches.
  **prevention:** When defining thresholds or classification rules: (1) state the input domain explicitly ("band thresholds apply to WEIGHT scale [0-20]"), (2) verify the formula makes the mapping unambiguous, (3) include example calculations at boundaries in the spec, (4) implementation code should document which domain is used.
  **severity:** high

- **category: process**
  **insight:** Spec contradiction between Requirement 03 (band definitions) and Requirement 05 (test vectors) was only discovered when Implementation Agent tested both, not when Spec Agent reviewed consistency. Spec review does not catch logical contradictions if both statements are individually plausible.
  **impact:** Specification v1.0 was marked COMPLETE and frozen, but contained contradictory band classification semantics. This forced a revision cycle (v1.0 → v1.1) and test fixes post-implementation.
  **prevention:** Add a "cross-requirement consistency check" step in spec review: identify overlapping domains (e.g., Req-03 and Req-05 both reference bands), then verify 3–5 test vector calculations against the formula. Use the Spec Agent's checkpoint protocol to resolve ambiguities before freezing.
  **severity:** high

- **category: testing**
  **insight:** When test suite is large (144 tests), assertion failures are expected and easily attributed to "edge cases" or "environmental factors" rather than systematic misalignment. Investigating the root cause required examining the pattern: 10 tests all failed in the same direction (wrong band prediction), pointing to a systematic issue, not isolated bugs.
  **impact:** If the test suite had been smaller (30–40 tests), the pattern would be harder to hide. With 144 tests, individual failures seemed like isolated test bugs. Only when Implementation Agent examined ALL failing tests together did the contradiction become obvious.
  **prevention:** When implementing against a large test suite, group test failures by assertion type (band classification, score computation, schema validation). If all failures of one type fail in the same direction, suspect systematic contradiction, not isolated bugs. Escalate to Spec Agent for contradiction resolution.
  **severity:** medium

### Anti-Patterns

1. **Ambiguous requirement + plausible test vector:** A requirement can be written in a way that sounds correct ("classify risk_score into a band") but is ambiguous about which scale to apply. Test vectors that contradict it sound equally plausible because they don't reference the ambiguity explicitly. Both seem correct until one is proven wrong.

2. **No consistency-check gate between Spec and Test Design:** Spec is frozen without validating test vectors against the formula. Test Designer is handed test vectors without checking whether they're consistent with Requirement 03. Contradiction discovered during Implementation, after test effort is spent.

3. **Test assertions as informal documentation:** Test vectors (Requirement 05) are often treated as informal "examples" rather than formal contracts. This allows contradictions to persist: if a test vector contradicts a formal requirement, the test vector is assumed to be wrong (or vice versa) without systematic resolution.

4. **Single-domain verification:** Spec Agent reviews spec, Test Designer reviews tests, Implementation Agent reviews code—each in isolation. Contradictions between domains are discovered late by accident.

### Prompt Patches (For Agent Instructions)

**Spec Agent (post-spec-freeze):**
- Add: "Before marking Specification COMPLETE, perform a spot-check consistency review: (1) Pick 3–5 test vectors from Requirement 05, (2) Manually compute expected outputs using formulas from Requirement 02, (3) If vectors match, note confidence 'consistent'. If vectors contradict Requirement 02–04, escalate to contradiction resolution checkpoint BEFORE freezing. Do not hand off to Test Designer with known contradictions."
- Add: "When defining thresholds or classification rules: explicitly state the input domain. Example: 'Band thresholds apply to the WEIGHT scale [0-20], not the RISK_SCORE scale [0-100]. Mapping: weight 0-2 → score 0-10 → band EXIT'."

**Test Designer (pre-test-design):**
- Add: "Read Spec Requirement 02 (formula) and Requirement 03 (thresholds) before implementing tests. For each test vector in Requirement 05, manually compute expected output using the spec formula. If your computation differs from the expected output in the test vector, document the contradiction in a checkpoint and route to Spec Agent for resolution. Do not implement contradictory assertions."

**AC Gatekeeper (final validation):**
- Add: "If test assertions fail in a systematic pattern (e.g., all band-classification tests fail in the same direction), do not treat as isolated bugs. Investigate root cause: check if there's a semantic domain mismatch (e.g., weight vs score scale). Escalate to Spec Agent if spec contradiction is suspected."

### Workflow Improvement

**Add to `agent_context/agents/common_assets/workflow_enforcement_v1.md` or `spec_exit_gate.md`:**

```markdown
## Spec-to-Test Consistency Gate (Specification Stage)

Before a spec is handed off to Test Designer:

1. **Cross-requirement domain review:** Identify all numerical scales, thresholds, and classification rules.
2. **Spot-check test vectors:** Pick 3–5 test vectors. Manually compute expected outputs using formulas in Requirement 02.
3. **If vectors contradict formula:**
   - Log contradiction in checkpoint
   - Route to Spec Agent contradiction resolution
   - Do not freeze spec with known contradictions
4. **Confidence rating:** "Consistent" if spot-check passes; "Requires clarification" if any contradiction found.
5. **Handoff:** Test Designer receives spec marked "Consistent" or "Contradiction Resolved (v1.x)".

**Rationale:** Discovering contradictions at Test Design time costs 0 rework. Discovering during Implementation costs test fixes + spec revision. Discovering during AC Gatekeeper costs full cycle revision.
```

**Consider adding a `spec-test-consistency` agent skill or checkpoint protocol** that validates test vectors against spec before Test Designer begins.

### Keep / Reinforce

1. **Implementation Agent's testing philosophy:** Implement code against tests, then run full suite to discover contradictions. This is how M902-12's contradiction was discovered. The contradiction would have persisted in spec and tests without implementation validation.

2. **AC Gatekeeper's systematic verification:** AC Gatekeeper investigated all 7 ACs and discovered that band-classification tests had a systematic contradiction. This thorough approach caught the root cause.

3. **Checkpoint protocol for contradiction resolution:** Spec Agent's v1.1 revision using checkpoint protocol (documenting options, choosing one, explaining evidence) made the contradiction explicit and traceable. Future agents can understand why the choice was made.

4. **Spec versioning (v1.0 → v1.1):** Marking spec revisions with "contradiction resolved" notes clarifies that the spec was inconsistent and has been corrected. This helps future agents understand the history.

---

## [M902-18-T5] — Framework Integration at External Boundaries Requires Test-Driven Middleware Isolation
*Completed: 2026-05-20*

### Critical Learning

**When integrating with external (unmodifiable) frameworks, test-driven development with mock isolation and determinism-focused adversarial testing prevents silent failures at the invocation boundary. Regex-based extraction, tool schema assumptions, and parameter-naming contracts are high-risk seams that must be validated before production use.**

### Learnings

- **category: architecture**
  **insight:** Framework integration patterns differ fundamentally from internal refactoring. When framework code is external and not modifiable within project scope, the integration layer must be wrapped as middleware with clear contracts (function signatures, parameter names, return types) rather than attempting to hook into or modify the framework itself.
  **impact:** Middleware approach (`invoke_agent_with_category_filtering()`) at the blobert → framework boundary enabled testability without access to Claude Code SDK internals. This decoupling allowed 72 deterministic tests to validate the contract before production use.
  **prevention:** For external framework integration: (1) Create middleware wrapper at logical invocation boundary, (2) Define explicit function signature with full type hints, (3) Mock the external framework for testing, (4) Test all contracts without depending on real external system.
  **severity:** high

- **category: testing**
  **insight:** Regex extraction patterns for configuration/declaration require fine-grained adversarial mutation testing to prevent silent failures. A regex that appears correct (passes happy-path tests) can have subtle vulnerabilities in keyword specificity, colon requirements, whitespace handling, and multiline behavior.
  **impact:** Test Break phase revealed 8 regex mutation vulnerabilities: colon requirement, keyword precision ("I declare tool category" vs partial matches), whitespace variations (spaces vs tabs after colon), and multiline prompt handling. These mutations would create silent false positives or false negatives in production.
  **prevention:** For any regex-based extraction (especially configuration parsing): (1) Create mutation tests that flip each regex requirement (remove colon, loosen keyword, change whitespace tolerance), (2) Verify each mutation causes a test failure, (3) Test boundary cases (empty categories, multiline prompts, case sensitivity). At least 8 mutation tests per regex pattern.
  **severity:** high

- **category: testing**
  **insight:** Tool schema type assumptions (string vs list, missing keys, empty structures) create silent bug vectors. Tools passed through filtering pipelines must have explicit type validation tests for malformed schemas.
  **impact:** Test Break phase added boundary-condition tests for schema variations: tools missing 'categories' key (KeyError without .get() check), categories as string instead of list (substring match works differently), empty categories list (orphaned tools), case sensitivity mismatches. These would cause runtime failures or incorrect tool selection if not caught.
  **prevention:** For tool filtering pipelines: (1) Define ToolDefinition TypedDict with required fields, (2) Add tests for each missing/wrong-type field variant, (3) Test empty structures and boundary values, (4) Validate that your filtering logic matches the actual tool schema you're receiving.
  **severity:** high

- **category: process**
  **insight:** Zero-flake determinism validation requires 5-invocation loops and repeated full test runs (4+ runs minimum). This level of rigor is necessary for infrastructure-critical code paths (middleware, frameworks, tool filtering).
  **impact:** M902-18-T5 verified determinism by running same test suite 4 consecutive times (38 original tests, then 72 total after adversarial additions). All 72/72 tests passed all 4 runs with zero flakes. This confidence is necessary for framework-integration code that will be used by downstream agents.
  **prevention:** For all middleware and framework-integration code: (1) Require 5-invocation determinism loops within tests, (2) Run full test suite 4+ consecutive times before accepting, (3) Checkpoint flake rate explicitly, (4) Log execution time and variance. Only accept when variance <5% across runs.
  **severity:** high

- **category: architecture**
  **insight:** Parameter naming and order in framework delegation are a high-risk contract seam. Framework expects specific parameter names (tools, not tool), types (list not dict), and order. These are easy to get wrong and create silent failures.
  **impact:** Test Break phase included 4 parameter-variation tests: wrong parameter name ('tool' vs 'tools'), wrong parameter type (single dict vs list), order preservation, kwargs passthrough. Implementation correctly used tools=tools_to_use; these tests would catch any deviation.
  **prevention:** When delegating to external frameworks: (1) Document framework signature explicitly (parameter names, types, order), (2) Test each parameter variant (wrong name, wrong type, order change), (3) Add a pass-through test for framework kwargs, (4) Type-hint everything in your wrapper.
  **severity:** high

- **category: testing**
  **insight:** Backward compatibility requires more than "agents without category declaration work." It requires scale testing (100+ agents) and evolution testing (category filtering can be toggled off and on without breaking existing flows).
  **impact:** Backward compatibility tests included 100-agent stress test confirming all agents without category declarations receive all tools unchanged. This proves zero impact on existing agent behavior when feature is added.
  **prevention:** For any framework feature addition with backward-compatibility requirements: (1) Add scale test (100+ no-category agents), (2) Verify old-behavior codepath unchanged, (3) Test feature can be disabled/enabled without state pollution, (4) Explicit checkpoint: "Existing agents receive identical tool sets with/without feature."
  **severity:** medium

### Anti-Patterns

1. **External framework integration without isolation:** Attempting to modify or hook into external frameworks directly creates scope creep and blocks testing. Always wrap with middleware at the boundary.

2. **Regex pattern validation with happy-path tests only:** A regex that passes "normal" test cases can have subtle keyword/whitespace/multiline vulnerabilities. Mutation-based adversarial tests are necessary.

3. **Type assumptions in tool filtering:** Assuming tools always have a 'categories' key as a list, or that the framework always passes tools in a specific format. These assumptions create silent failures. Use TypedDict, explicit validation, and schema tests.

4. **Single-run determinism validation:** Running tests once and assuming determinism. Infrastructure-critical code requires 4+ full runs with zero variance. Flakes are easy to miss on single runs.

5. **Parameter contract drift in framework delegation:** Framework expects tools=..., but implementation passes tool=... or passes wrong type. These slip through code review. Parameterized tests catch this.

### Prompt Patches

- **agent: Spec Agent**
  **change:** "When specifying framework integration at external boundaries, define a mandatory 'Integration Contract' section that names: (1) exact function signature with parameter names and types, (2) framework invocation protocol, (3) error handling fallback behavior, (4) backward compatibility requirements. If framework code is external/unmodifiable, assume middleware-wrapper approach and document integration point at blobert → framework boundary."
  **reason:** Prevents integration design ambiguity and forces explicit contract definition before Test Designer and Implementation agents begin.

- **agent: Test Designer Agent**
  **change:** "For regex-based extraction patterns, require at least 8 mutation tests per pattern covering: keyword specificity, colon requirement, whitespace variations, multiline handling, case sensitivity, empty/malformed input. Each mutation test should flip one regex requirement and verify test failure. Do not accept regex without mutation coverage."
  **reason:** Catches hidden regex vulnerabilities that happy-path tests miss and prevents false positives/negatives in production.

- **agent: Test Designer Agent**
  **change:** "For tool filtering / schema-manipulation code, add boundary-condition tests for each required field in the tool schema: missing key, wrong type (string vs list), empty structure, case sensitivity. If schema is not explicitly validated in implementation, create TypedDict definition and contract tests. Assume worst-case malformed input."
  **reason:** Tool schemas are often externally-sourced and may not match implementation assumptions. Explicit schema validation prevents silent filtering failures.

- **agent: Test Breaker Agent**
  **change:** "For infrastructure-critical code (middleware, frameworks, tool filtering), require determinism validation at 5-invocation granularity within tests, plus full test suite execution 4+ consecutive times before accepting zero-flake claim. Log execution time and variance. Flake rate acceptance threshold: zero flakes across all 4 runs."
  **reason:** Flakes in infrastructure code create downstream cascading failures. Aggressive determinism validation prevents false confidence.

- **agent: Implementation Agent**
  **change:** "When implementing framework delegation or middleware invocation, explicitly document: (1) framework parameter names and types via type hints, (2) error handling fallback logic, (3) logging levels and message fields, (4) backward-compatibility code paths. Use TypedDict for tool schemas. Add comments on high-risk seams (parameter names, tool schema assumptions)."
  **reason:** Makes contract dependencies explicit and auditable. Reduces silent failures when framework behavior or tool schema changes.

### Workflow Improvements

- **issue:** External framework integration creates scope ambiguity about what's testable without framework source code access.
  **improvement:** Add a required SPECIFICATION section "Integration Boundary & Testability" that declares: (1) Is framework external/unmodifiable? (2) If so, middleware-wrapper approach with mock framework in tests. (3) Define exact function contracts. (4) Identify high-risk seams (regex, parameter names, tool schema) requiring adversarial testing. (5) Document backward-compatibility strategy.
  **expected_benefit:** Eliminates scope drift and forces test strategy decisions early. Framework integrators know what's safe to test without real framework access.

- **issue:** Determinism validation for infrastructure code can be weak ("tests passed") without explicit multi-run protocol.
  **improvement:** Add a required "Determinism Evidence" section in TEST_BREAK checkpoint for any infrastructure-critical code: (1) 5-invocation loops within tests, (2) Full suite execution count and flake rate, (3) Execution time variance, (4) Acceptance threshold (zero flakes across 4+ runs). Checkpoint failure if flake rate > 0%.
  **expected_benefit:** Creates explicit determinism standards and prevents shipping flaky infrastructure code.

- **issue:** Backward compatibility can appear satisfied ("tests pass") without proving non-impact on existing agents/flows.
  **improvement:** For any feature addition with backward-compatibility requirements, require explicit scale test (100+ agents without new feature) and comparison test (identical behavior with/without feature). Checkpoint evidence of both before acceptance.
  **expected_benefit:** Prevents silent regressions in existing agent behavior when new features are added.

### Keep / Reinforce

1. **Middleware-wrapper approach for external framework integration:** Instead of trying to modify or hook into external frameworks, wrap at a logical boundary with explicit contracts. This is testable, maintainable, and isolates blobert from framework changes.

2. **Adversarial mutation testing for regex patterns:** M902-18-T5 added 8 regex mutation tests as part of adversarial phase. This approach should be standard for any regex-based extraction (configuration parsing, declarations, headers, etc.).

3. **TypedDict enforcement for tool schemas:** Implementation defined `ToolDefinition` TypedDict and used it consistently. This makes schema expectations explicit and testable. Schema validation should be a standard tool-manipulation contract.

4. **Test-first evidence for infrastructure code:** All 8 acceptance criteria were verified by concrete test evidence (line numbers, test class names, explicit assertions). This evidence-first approach makes infrastructure code auditable and reproducible.

5. **Multi-run determinism validation:** Running test suite 4+ consecutive times is expensive but necessary for infrastructure code. Zero-flake evidence is worth the extra test execution cost because infrastructure failures have cascading impact.

---

## [M902-18] — Deferred Work Requires Explicit Downstream Ticket Updates
*Completed: 2026-05-18*

### Critical Learning

**When an agent defers acceptance criteria or work to a future task, that future task's ticket MUST be explicitly updated.** Silent deferral leads to downstream tasks not knowing they have inherited work, resulting in surprise dependencies and missed scope.

### Learnings

- **category: workflow**
  **insight:** Deferred work is invisible to downstream tasks unless the downstream ticket is explicitly updated with the dependency and requirement.
  **impact:** M902-18's AC-4, AC-5, AC-7, AC-8 were deferred to "Task 5 (Integration Agent)" without updating M902-09-M902-17 active tickets or M902-19+ backlog tickets. Downstream tasks would not discover these requirements unless they read M902-18 checkpoints explicitly.
  **prevention:** **Mandatory pattern:** When any agent defers work, the orchestrator or deferring agent MUST immediately update the receiving task's description with: (1) what work is deferred, (2) why, (3) where the requirements are documented, (4) what's blocking implementation.
  **severity:** high

- **category: architecture**
  **insight:** Task sequencing (Task 5 must complete before M902-19 can use categorization) is implicit in execution plans but not discoverable from the forward-referenced tickets.
  **impact:** M902-19 had no cross-reference to M902-18 framework integration dependency until manually added.
  **prevention:** Create bidirectional pointers: upstream ticket (M902-18) → downstream task (Task 5), AND downstream ticket (M902-19) → upstream blocker (M902-18 framework integration). Use INTEGRATION_GUIDE.md pattern.
  **severity:** high

- **category: process**
  **insight:** AC Gatekeeper's "deferred to later task" decision is correct per execution plan, but requires explicit documentation in the downstream ticket for future agents to understand the intent.
  **impact:** Without INTEGRATION_GUIDE.md and cross-references, Task 5 agent would not know M902-18 implementation was ready and waiting.
  **prevention:** Gatekeeper (or orchestrator after Gatekeeper) must update downstream tickets when deferring ACs. Provide: ticket path, what's deferred, checkpoint reference, integration guide link.
  **severity:** high

### Anti-Patterns

1. **Silent deferral:** Deferring work without updating downstream ticket description or acceptance criteria.
2. **Unidirectional dependencies:** Upstream task (M902-18) knows about downstream (Task 5), but downstream doesn't know about upstream.
3. **Execution-plan-only documentation:** Sequencing documented in execution plan checkpoints but not reflected in actual ticket descriptions.
4. **Implicit task names:** Referencing "Task 5" without explaining what "Task 5" is or where the Task 5 work will be defined.

### Prompt Patches (For Agent Instructions)

**Spec Agent:**
- When deferring SDK/framework dependencies: "Create a cross-reference in downstream tickets that depend on these deferred items. Update their DEPENDENCIES section explicitly."

**AC Gatekeeper:**
- When setting Stage to INTEGRATION/BLOCKED due to deferred ACs: "Immediately update each downstream ticket (by ticket path) with: (1) what AC is deferred, (2) why, (3) where implementation is ready (checkpoint/spec link), (4) integration guide path if created."

**Orchestrator (Autopilot/ap-continue):**
- After any agent defers work: "Verify the downstream ticket (if it exists in backlog/in_progress) has been updated with the deferred requirement. If not, update it now with explicit cross-reference."

**All agents (General):**
- "If your work depends on or defers to another task/ticket, BOTH the upstream and downstream tickets must be updated. One-way pointers create invisible dependencies."

### Workflow Improvement

**Add to `agent_context/agents/common_assets/workflow_enforcement_v1.md`:**

```markdown
## Deferred Work Rule (Cross-Task Coupling)

When an agent defers acceptance criteria, implementation, or testing to a future task:

1. **Document in current ticket:** Mark deferred ACs with reason, target task, and checkpoint reference
2. **Update downstream ticket:** Add explicit DEPENDENCIES section noting:
   - What is deferred from upstream
   - Why (architectural, sequencing, external dependency)
   - Where implementation is ready (checkpoint path, spec path, code path)
   - Integration guide or next steps
3. **Create integration guide (if complex):** For multi-phase work (backend + framework + live testing), document phases in INTEGRATION_GUIDE.md
4. **Bidirectional pointers:** Upstream → downstream AND downstream → upstream, so no task is surprised

**Objective:** Make deferred work visible and actionable to downstream agents without requiring them to read full checkpoint logs.
```

### Practices to Reinforce

1. **Mandatory cross-references:** Deferred work = mandatory downstream ticket update
2. **Bidirectional pointers:** Both tickets reference each other
3. **Integration guides for distributed work:** When work spans multiple tasks, create INTEGRATION_GUIDE.md
4. **Explicit dependency chains:** "Task 5 must complete before M902-19 implementation begins" should appear in both ticket descriptions

---

## [M902-19] — Multi-Format Parsing + Layered Repairs Require Mutation Testing and Idempotency Proof
*Completed: 2026-05-20*

### Critical Learning

**Tool error recovery middleware requires adversarial mutation testing to ensure repair logic is not over-permissive, and idempotency validation to guarantee repair(repair(X)) == repair(X). Type safety via TypedDict and tuple-based error returns prevent silent type corruption. Code review findings (5 MEDIUM issues caught pre-deployment) and layered validation (parsing → repair → whitelist gate) are load-bearing patterns.**

### Learnings

- **category: testing**
  **insight:** Repair logic appears "correct" on happy-path tests but can fail under mutation: repair skips type checks, over-coerces values (accepting "yes"/"no" for bool), returns wrong types, or applies repairs when disabled. Mutation tests flip each assumption and verify tests fail, catching over-permissive implementations.
  **impact:** Test Break phase added 11 mutation tests (test_mutation_repair_skips_bool_type_check, test_mutation_validator_always_approves, etc.) that would have escaped happy-path validation. Example: test_mutation_coercion_too_permissive verifies that accepting "yes" → bool is caught as a violation.
  **prevention:** For any multi-step repair or validation logic: (1) Create explicit mutation tests that flip each repair assumption (disable type check, omit defaults, invert validation logic), (2) Verify each mutation causes test failure, (3) Add "negative mutation" tests where mutation should NOT cause failure (e.g., disabled-for-reason cases). Target: at least 10 mutation tests per repair category.
  **severity:** high

- **category: architecture**
  **insight:** Layered validation (parse → repair → validate → execute) is safer than monolithic repair. Each layer isolates responsibility: parser handles syntax, repair handles type/structure, validation gate handles semantic safety. Violations at any layer are caught and logged separately.
  **impact:** Implementation defined 3 distinct functions: `parse_tool_call()` (format detection), `repair_tool_call()` (orchestration + repair logic), `validate_repair_safety()` (whitelist + dangerous pattern rejection). Logging at each layer provides audit trail granularity (INFO for attempts, WARNING for success, ERROR for rejection). This separation enabled 78 tests to target each layer independently.
  **prevention:** For error recovery systems: (1) Define discrete repair categories (type coercion, missing fields, typo, quoting, nesting), (2) Create separate functions per category, (3) Validate input at layer entry, (4) Log before/after at each layer, (5) Combine with middleware orchestrator that calls layers in order and combines results.
  **severity:** high

- **category: code-quality**
  **insight:** Code review findings (5 MEDIUM issues) were caught before deployment and prevented shipping bugs. Review flagged: (1) lazy-import anti-pattern (fixed with inline import + documentation), (2) untyped dict for tool schema (enforced via TypedDict), (3) missing docstring on helper, (4) type hint on return tuple, (5) error message clarity. These are not blocking issues but represent code-quality debt that compounds in infrastructure code.
  **impact:** Python Reviewer Agent found 5 MEDIUM findings; all were fixed before AC Gatekeeper approval. Implementation went from COMPLETE to code-quality-compliant in one iteration. This prevents accumulating tech debt in infrastructure-critical middleware.
  **prevention:** For infrastructure code (middleware, frameworks, validation): (1) Code review is mandatory before AC Gatekeeper (add to workflow), (2) Type hints on all functions (no bare Any), (3) TypedDict for dict-based contracts (no untyped dicts), (4) Docstrings with Args/Returns/Raises, (5) Explicit error messages with context. Consider: require code review before STATIC_QA → COMPLETE transition.
  **severity:** high

- **category: testing**
  **insight:** Idempotency (repair(repair(X)) == repair(X)) is critical for destructive operations or retry-safe code, but easy to violate. Quoted-path repair must check if inner string starts with quote to avoid double-unwrapping. Tests must verify idempotency explicitly: apply repair 5+ times, assert identical output.
  **impact:** Idempotency is validated in implementation via comment: "idempotent: checks if inner starts with quote to avoid double-unwrap." Tests include explicit idempotency loops: `for _ in range(5): result = repair_quoted_string_path(result, schema)` followed by assertion that results are identical. This prevents silent double-unwrapping bugs.
  **prevention:** For any repair function that might be called multiple times (retry loops, cascading repairs): (1) Add idempotency validation explicitly in tests (5+ invocation loops), (2) Document idempotency assumption in implementation docstring, (3) For stateful repairs, add checks to detect "already repaired" condition (e.g., "path already unwrapped, skip"). (4) Benchmark: idempotency must hold at both single and 1000+ sequential calls.
  **severity:** high

- **category: architecture**
  **insight:** TypedDict for tool schemas enables static type checking and explicit contract validation. Implementation defined `ToolCallDict` and `ParamInfo` TypedDict classes to represent tool-call structure and parameter metadata. This prevents silent failures from missing keys or wrong types in tool schema.
  **impact:** Tool schemas are externally-sourced (from M902-18 tool categorization) and may not match implementation assumptions. TypedDict provides explicit contracts: which keys are required, which types are expected, which are optional with defaults. Type checking catches schema mismatches early.
  **prevention:** For any external data contracts (tool schemas, API payloads, config files): (1) Define TypedDict with explicit required/optional fields, (2) Use total=False for optional, (3) Type-hint all schema-handling functions with TypedDict, (4) Add contract tests for missing/wrong-type fields, (5) Assume worst-case malformed input and validate at entry points.
  **severity:** medium

- **category: testing**
  **insight:** Tuple-based error returns `(dict | None, list[str])` prevent silent type corruption. Implementation returns repaired dict (or None on failure) + list of error messages. Caller must check for None before using dict, preventing downstream silent failures from "unrepaired" calls treated as repaired.
  **impact:** Function signature `repair_tool_call(...) -> tuple[dict | None, list[str]]` forces caller to pattern-match on error. Tests verify both success and error paths explicitly. Logging tuple messages ensure audit trail is always captured. This is safer than returning modified dict with side-effect logging.
  **prevention:** For error-recovery functions: (1) Return explicit error/success indicators (None for failure, not empty dict or falsy value), (2) Combine with error messages in tuple, (3) Require caller to check return value before using (no implicit truthy checks), (4) Type-hint the tuple explicitly, (5) Log all error messages to audit trail. Consider: ban silent failures (missing None check = type error at review stage).
  **severity:** medium

### Anti-Patterns

1. **Happy-path-only testing for repair logic:** Repairs work on normal inputs but fail under mutation (type checks disabled, over-permissive coercion). Happy-path tests don't catch these. Adversarial mutation layer is necessary.

2. **Monolithic repair function:** Single function handles parsing, type coercion, typo correction, validation, logging. Changes to one repair category risk breaking others. Layered, single-responsibility functions are safer.

3. **Over-permissive type coercion:** Accepting "1"/"0" or "yes"/"no" for bool coercion seems helpful but creates ambiguity. Spec constraint: only "true"/"false" (case-insensitive). Overly permissive repairs invite injection vectors.

4. **Idempotency not tested:** Repair functions look idempotent (no side effects) but double-unwrapping or repeated coercion can fail. Idempotency must be validated explicitly with 5+ invocation loops.

5. **Untyped dicts in schema handling:** Tool schemas as plain `dict` without TypedDict contract. Missing keys, wrong types, and malformed schemas silently slip through. TypedDict makes contracts explicit and testable.

### Prompt Patches

- **agent: Test Designer Agent**
  **change:** "For any multi-step repair or validation middleware, require mutation testing as a standard suite: flip each assumption (disable type check, omit defaults, invert validation), verify tests fail. Minimum 10 mutation tests per repair category. All mutation tests should document what assumption they flip and why the flip should cause failure."
  **reason:** Catches over-permissive logic that happy-path tests miss. Mutation tests are the strongest validation for deterministic repair functions.

- **agent: Test Designer Agent**
  **change:** "For any function that might be called multiple times or in retry loops, include explicit idempotency validation tests: invoke 5+ times with identical input, assert identical output. For destructive operations (repairs, modifications), idempotency is a requirement, not optional."
  **reason:** Prevents silent double-unwrapping, repeated coercion, or compounding state changes. Idempotency testing is cheap insurance for high-impact bugs.

- **agent: Implementation Agent**
  **change:** "For error-recovery functions, use tuple returns `(result | None, errors: list[str])` instead of throwing exceptions or side-effect logging. Type-hint the tuple explicitly. In docstring, document: (1) what causes None return, (2) what errors list contains, (3) idempotency assumptions, (4) mutation safeguards. Use TypedDict for all dict-based contracts."
  **reason:** Tuple returns force caller to handle both success and error paths. TypedDict makes schema expectations explicit. Documentation prevents misuse.

- **agent: Python Reviewer Agent**
  **change:** "For infrastructure code (middleware, frameworks, tool handling), enforce: (1) all functions have type hints (no bare Any unless documented), (2) TypedDict for dict schemas, (3) docstrings with Args/Returns/Raises, (4) explicit error messages with context. Code review is MANDATORY before AC Gatekeeper approval. Report MEDIUM findings as blocking for infrastructure code."
  **reason:** Infrastructure code is used by downstream agents and systems. Code quality debt accumulates quickly. Type safety and documentation prevent misuse and bugs.

### Workflow Improvements

- **issue:** Repair logic appears correct without mutation testing; over-permissive implementations escape detection.
  **improvement:** Add required "Adversarial Testing" section in TEST_BREAK checkpoint for middleware/repair code: (1) Define 10+ mutation tests per repair category, (2) For each mutation, document which assumption is flipped and why test should fail, (3) Verify all mutations cause test failure, (4) Add "negative mutation" tests (mutations that should NOT break tests). Require mutation test coverage documented in checkpoint.
  **expected_benefit:** Prevents shipping over-permissive or disabled-logic bugs. Adversarial testing is standard for security-sensitive and infrastructure-critical code.

- **issue:** Code review findings for infrastructure code are caught post-implementation, requiring iteration.
  **improvement:** Require code review (Python Reviewer Agent) as mandatory gate before STATIC_QA → COMPLETE transition. For infrastructure code (middleware, frameworks, validation), code review findings at MEDIUM+ severity block AC Gatekeeper approval. Document review findings in checkpoint.
  **expected_benefit:** Infrastructure code quality is verified before shipping. Prevents accumulating tech debt in code used by downstream systems.

- **issue:** Idempotency assumptions are implicit; double-unwrapping or repeated coercion bugs can slip through.
  **improvement:** For any repair or modification function, add explicit idempotency contract in spec and tests: (1) Documented assumption in implementation docstring, (2) Explicit idempotency tests with 5+ invocation loops in test suite, (3) If not idempotent, document reason and expected failure mode. Checkpoint evidence: function docstring + test class + invocation count.
  **expected_benefit:** Idempotency failures are caught early. Repair functions are proven safe for retry loops and cascading repairs.

### Keep / Reinforce

1. **Layered validation pattern (parse → repair → validate):** Clear separation of concerns, enables independent testing of each layer, provides granular audit trail. Use this pattern for any multi-step error recovery.

2. **TypedDict for external contracts:** Tool schemas, API payloads, config structures should be defined with TypedDict. This makes expectations explicit and testable. Prevents silent failures from schema mismatches.

3. **Tuple-based error returns:** `(result | None, errors)` is safer than exceptions or silent failures. Forces caller to handle both paths. Combined with type hints, this is a high-confidence pattern.

4. **Mutation testing for repair logic:** Adversarial mutation layer (11 tests) is more valuable than adding more happy-path tests. Each mutation should flip one assumption and cause test failure.

5. **Code review as mandatory infrastructure gate:** Python Reviewer Agent findings (5 MEDIUM issues) prevent shipping code quality debt. Code review before AC Gatekeeper approval is worth the iteration cost for infrastructure-critical code.

---

## [body-part-image-not-applied] — Preserve identity fields across UI-to-payload boundaries
*Completed: 2026-04-27*

### Learnings
- category: testing
  insight: UI regressions involving "state appears correct but backend behavior is unchanged" are often identity-propagation failures, so tests must assert semantic identifiers (not only preview/display fields) at component boundaries.
  impact: The selected image preview propagated, but the required `assetId` did not, so regeneration could not resolve the intended texture and silently kept prior material behavior.
  prevention: For mode-based pickers, require regression tests that assert both presentation fields and execution-critical ids survive each callback hop.
  severity: high

- category: architecture
  insight: Typed multi-mode value objects need an explicit per-mode required-field contract to prevent silent drops of execution-critical properties during adapter forwarding.
  impact: One intermediary transformed image-mode data without preserving `assetId`, creating a partial state object that looked valid in UI but was invalid for downstream material application.
  prevention: Define and enforce mode contracts where image mode requires id semantics for preloaded assets, and validate these contracts at translation points.
  severity: high

- category: process
  insight: Frontend bugfix closeout quality improves when verification includes both direct regression scope and adjacent integration surfaces that consume the same value shape.
  impact: Running regression plus related color-picker and zone-texture suites provided strong evidence that the fix restored behavior without cross-mode regressions.
  prevention: Standardize post-fix validation bundles that include the failing path, sibling mode tests, and the payload/persistence integration boundary.
  severity: medium

### Anti-Patterns
- description: Treating UI preview correctness as sufficient evidence that a selection will apply in generated output.
  detection_signal: UI reflects the newly selected asset, but regenerate payload lacks the corresponding id field and output remains unchanged.
  prevention: Add assertions on serialized payload keys for execution-critical fields whenever a visual picker changes state.

- description: Forwarding callback payloads through intermediary components without a declared "must-preserve" field list.
  detection_signal: Callback signatures support richer data than intermediary handlers pass onward.
  prevention: For each mode callback, document required pass-through fields and add contract tests on intermediary adapters.

### Prompt Patches
- agent: Test Designer Agent
  change: "For any UI selection bugfix that affects generation or persistence, include at least one regression assertion on execution-critical identifier fields (e.g., asset/resource ids) at both component-callback and serialized payload boundaries; preview-only assertions are insufficient."
  reason: Prevents false confidence from visual-state-only tests when downstream systems require stable ids.

- agent: Spec Agent
  change: "When specifying union/mode-based frontend value shapes, add a 'Mode Field Contract' subsection that explicitly marks required vs optional fields per mode and identifies which fields are mandatory for downstream execution."
  reason: Reduces intermediary translation ambiguity and catches partial-object propagation defects earlier.

- agent: Implementation Frontend Agent
  change: "When adapting mode callbacks, preserve all execution-critical fields defined by the mode contract; if any required field is intentionally dropped, add an explicit guard/test explaining why."
  reason: Makes silent data loss at component boundaries an intentional, reviewable decision rather than an accidental regression.

### Workflow Improvements
- issue: Acceptance checks can pass visual behavior while missing whether the regenerate payload contains required identity keys.
  improvement: Add an AC template item for generator-affecting UI bugs: "serialized payload includes execution-critical identifiers for selected mode."
  expected_benefit: Catches identity-propagation regressions before implementation handoff and reduces rework.

- issue: Intermediary component adapters are under-tested compared with leaf-mode components.
  improvement: Require at least one adapter-contract test whenever a leaf component callback includes optional metadata used downstream.
  expected_benefit: Detects field-loss regressions at the exact seam where they are introduced.

### Keep / Reinforce
- practice: Pairing a bug-specific regression with broader related-scope test execution for nearby components.
  reason: Confirms the fix and guards against mode/cross-component regressions in one validation pass.

- practice: Conservative gatekeeping when workflow helper modules are missing, while still enforcing explicit acceptance evidence.
  reason: Maintains delivery continuity without lowering validation rigor.

---

## [M901-14-backend-error-mapping-unification] — Centralized fallback contracts need cross-router proof and bootstrap-aware regressions
*Completed: 2026-04-23*

### Learnings
- category: testing
  insight: Error-mapping unification is incomplete unless unknown-exception fallback behavior is asserted across every in-scope router family, not just the first refactored path.
  impact: Structured fallback logging and safe-generic response parity needed explicit coverage for `assets`, `registry`, and `run` to prove no observability regressions after consolidation.
  prevention: Make cross-router fallback contract tests mandatory for all router families named in scope, including route context and exception-category logging fields.
  severity: high

- category: architecture
  insight: Router-scope assumptions drift when "included in milestone" is treated as "requires mapper refactor" without proving whether the router actually performs domain-exception translation.
  impact: The `files` route required explicit scope reasoning (transport/path-validation only) to avoid false AC gaps and scope creep during gate closure.
  prevention: Add a required "router role classification" artifact before implementation: transport-only vs domain-delegating vs mixed, and tie refactor obligations to that classification.
  severity: medium

- category: process
  insight: Boundary extractions that touch startup/import paths need companion compatibility tests for minimal-root environments, even when the ticket focus is HTTP error mapping.
  impact: A bootstrap fallback compatibility fix in `python_bridge` was required to restabilize the backend import-adapter contract suite after refactor adjacency effects.
  prevention: For backend service-boundary refactors, require one environment-minimal boot/import regression suite rerun as a hard quality gate before acceptance closure.
  severity: high

### Anti-Patterns
- description: Treating shared error mapping as complete based on status-code parity alone while omitting structured-fallback observability assertions.
  detection_signal: Contract tests pass mapped exception statuses but do not assert route context + exception type fields for unknown-exception logs.
  prevention: Pair every fallback response assertion with a structured log-contract assertion for machine-parseable context keys.

- description: Expanding router-refactor scope from milestone wording instead of behavior classification evidence.
  detection_signal: Validation debates center on whether a router name appears in scope rather than whether it owns duplicated domain-exception translation logic.
  prevention: Require pre-implementation classification and evidence for each scoped router’s error-handling responsibility.

### Prompt Patches
- agent: Test Designer Agent
  change: "For any backend error-mapping consolidation ticket, include at least one unknown-exception fallback test per in-scope router family and assert both safe client payload semantics and structured log context (`route`, `exception_type`)."
  reason: Prevents silent observability and safety regressions that status-only tests cannot detect.

- agent: Spec Agent
  change: "Add a mandatory 'Router Responsibility Matrix' section listing each scoped router as transport-only, domain-delegating, or mixed; only domain-delegating/mixed routers require shared-mapper migration acceptance checks."
  reason: Reduces scope ambiguity and prevents false acceptance failures or unnecessary refactor churn.

- agent: Acceptance Criteria Gatekeeper Agent
  change: "When accepting backend boundary-refactor tickets, require evidence that adjacent import/bootstrap contract suites were rerun and stable in addition to targeted router tests."
  reason: Catches cross-boundary regressions that appear outside the immediate ticket module but are introduced by the same refactor.

### Workflow Improvements
- issue: Ticket closure required late clarification about whether all named routers were expected to migrate or only those with duplicated domain translation.
  improvement: Introduce an early scope-lock checkpoint requiring a per-router responsibility table before TEST_DESIGN handoff.
  expected_benefit: Eliminates late-stage acceptance ambiguity and reduces unnecessary adversarial test churn.

- issue: Adjacent import-boundary regressions surfaced after targeted suite stabilization.
  improvement: Add a standard "adjacent boundary smoke pack" (import/bootstrap + targeted contracts) to implementation exit criteria for backend refactor tickets.
  expected_benefit: Improves first-pass gate success by catching cross-cutting regressions earlier.

### Keep / Reinforce
- practice: Freezing fallback safety semantics (generic client detail + internal structured diagnostics) at specification time.
  reason: Maintains secure external behavior while preserving debuggability as mapping logic centralizes.

- practice: Evidence-first acceptance mapping from each AC to concrete test files and pass counts.
  reason: Keeps gate decisions objective and reproducible under refactor-heavy milestone work.

---

## [M901-12-registry-mutation-service-boundary] — Make service error contracts explicit before router-delegation refactors
*Completed: 2026-04-22*

### Learnings
- category: process
  insight: Entering the pipeline without initialized workflow metadata creates avoidable planning-stage assumption debt before technical decisions begin.
  impact: PLANNING required medium-confidence bootstrap assumptions for revision/state fields, adding non-technical ambiguity to checkpoint evidence.
  prevention: Add a mandatory pre-planning metadata normalization step that seeds and validates `WORKFLOW STATE`/`NEXT ACTION` blocks for all `ready/` tickets.
  severity: medium

- category: architecture
  insight: Service-owned mutation boundaries are safer when exception taxonomy is frozen as part of the service contract, not inferred during test design.
  impact: TEST_DESIGN had to assume `RuntimeError` for conflict-class failures to preserve 409 router mapping, increasing drift risk if implementation chose a different domain signal.
  prevention: Require spec-time declaration of service exception classes and router mapping expectations for each destructive failure class.
  severity: high

- category: process
  insight: Generic spec-gate routing for backend-touching refactors is acceptable only when compensating controls are explicitly documented.
  impact: The run skipped API-type completeness checks by assumption; confidence depended on downstream behavioral contract rigor rather than gate traceability.
  prevention: Record gate-type selection with explicit residual-risk controls whenever backend endpoint behavior is in scope but gate type remains generic.
  severity: medium

- category: process
  insight: Dependency statements in refactor tickets need stage-specific semantics to avoid inconsistent blocking behavior across agents.
  impact: PLANNING required a medium-confidence interpretation that dependency constraints apply mainly to implementation ordering, not early-stage progression.
  prevention: Standardize dependency annotations as `planning-blocking` vs `implementation-blocking` in ticket templates.
  severity: medium

### Anti-Patterns
- description: Allowing test contracts to infer service exception semantics for router mapping in destructive mutation flows.
  detection_signal: Test-design checkpoints include medium-confidence assumptions about exception type (for example conflict -> 409 mapping).
  prevention: Freeze service error taxonomy in specification before RED tests are authored.

- description: Treating workflow metadata initialization as ad hoc planner behavior instead of a required workflow precondition.
  detection_signal: Early checkpoints discuss revision/stage default assumptions instead of domain behavior.
  prevention: Enforce an explicit metadata normalization gate before PLANNING stage entry.

### Prompt Patches
- agent: Spec Agent
  change: "For service-boundary extraction tickets affecting HTTP endpoints, include a required 'Service Error Contract' subsection that names the exact exception taxonomy per failure class and the intended router status mapping."
  reason: Eliminates assumption-driven conflict/error mapping and keeps service-router behavior deterministic.

- agent: Test Designer Agent
  change: "Do not finalize RED assertions for router status mapping until the spec explicitly freezes service exception taxonomy; if missing, emit a blocking clarification checkpoint."
  reason: Prevents brittle tests that encode guessed error surfaces.

- agent: Orchestrator Agent
  change: "Before PLANNING, validate ticket workflow metadata (Stage, Revision, Last Updated By, NEXT ACTION). If missing, normalize these fields and checkpoint the normalization as a prerequisite."
  reason: Removes repeated startup ambiguity and keeps checkpoints focused on engineering risk.

### Workflow Improvements
- issue: Gate classification (generic vs API) was handled by assumption even though backend endpoint behavior was impacted by delegation refactor risk.
  improvement: Add a required orchestrator checkpoint line: `Gate type selected: <type>; compensating controls: <controls>`.
  expected_benefit: Improves auditability and ensures validation depth is explicitly tied to risk.

- issue: Dependency interpretation required agent judgment about whether progression should block prior to implementation.
  improvement: Add template-level dependency qualifiers (`planning-blocking`, `spec-blocking`, `implementation-blocking`) in ticket task headers.
  expected_benefit: Reduces cross-agent interpretation variance and avoids avoidable medium-confidence assumptions.

### Keep / Reinforce
- practice: Capturing "Would have asked" assumptions with confidence levels in planning and test-design checkpoints.
  reason: Surfaces uncertainty early and creates concrete targets for prompt/workflow hardening.

- practice: Closing boundary-refactor tickets with dual evidence suites (service contract tests plus router delegation/regression tests).
  reason: Confirms business-rule centralization while preserving endpoint-observable behavior.

---

## [M901-09-zone-geometry-extras-decomposition] — Freeze decomposition contracts with executable structural evidence
*Completed: 2026-04-22*

### Learnings
- category: process
  insight: Refactor tickets that begin without `WORKFLOW STATE` metadata create avoidable orchestration assumptions and weaken audit continuity.
  impact: The planner had to bootstrap revision/stage metadata before normal execution, adding non-product ambiguity to the run.
  prevention: Require a pre-planning normalization step that seeds missing workflow metadata (`Stage`, `Revision`, `NEXT ACTION`) for every `ready/` ticket.
  severity: medium

- category: architecture
  insight: In decomposition work, compatibility entrypoint retention must be frozen in spec before implementation to prevent import-surface regressions.
  impact: Specification had to explicitly assume retaining `zone_geometry_extras_attach` as the public dispatcher surface while internals moved to new modules.
  prevention: Mandate a Compatibility Boundary clause in spec for refactors, naming canonical external entrypoints and whether facade retention is required.
  severity: high

- category: testing
  insight: Structural quality claims like "thin dispatcher" are more reliable when encoded as executable invariants rather than prose review statements.
  impact: Acceptance closure depended on objective delegation/loop-absence contract tests, which made a subjective readability AC auditable.
  prevention: For decomposition tickets, require at least one executable structural-contract test per non-functional architecture AC.
  severity: medium

- category: infra
  insight: Local test-environment ambiguity at TEST_DESIGN stage causes false-negative execution signals and slows feedback.
  impact: RED test authoring completed, but local `pytest` evidence was blocked by missing environment setup (`No module named pytest`).
  prevention: Add a required environment handshake in TEST_DESIGN checkpoints that declares the exact runnable test command (or known local fallback constraints) before test execution attempts.
  severity: medium

### Anti-Patterns
- description: Treating algorithm-heavy decomposition tickets as implicitly "generic" without explicit rationale for gate classification.
  detection_signal: Orchestrator logs include "Would have asked" about specialized spec gate usage despite proceeding with generic path.
  prevention: Require gate-type justification plus residual-risk note when selecting generic classification for geometry/placement-sensitive refactors.

- description: Allowing helper-name assumptions to drift between stages instead of explicitly testing semantic role contracts.
  detection_signal: Test-design checkpoints mention uncertainty over strict helper-name freeze versus semantic callable behavior.
  prevention: Prefer role-based contract tests for extracted helpers unless the spec explicitly freezes concrete helper symbol names.

### Prompt Patches
- agent: Orchestrator Agent
  change: "When selecting `generic` gate classification for tickets with algorithmic geometry/placement logic, add one required line: `Gate rationale: <why generic is sufficient>; Residual risk review: <how risk is covered by tests/evidence>`."
  reason: Makes gate-depth decisions auditable and prevents silent under-scoping.

- agent: Spec Agent
  change: "For any decomposition/refactor ticket, include a mandatory `Compatibility Boundary` subsection that states preserved public entrypoints, allowed import-path changes, and whether a compatibility dispatcher/facade is required."
  reason: Prevents downstream import-surface regressions and removes implementation-stage ambiguity.

- agent: Test Designer Agent
  change: "For architecture ACs that use subjective terms (for example 'thin', 'readable', 'delegation-focused'), encode at least one executable structural invariant (delegation call path, banned loop constructs, or branch-count proxy) to produce objective pass/fail evidence."
  reason: Converts subjective ACs into deterministic, reproducible validation.

- agent: Test Designer Agent
  change: "Before running local RED evidence, record the exact environment-qualified test command; if unavailable, checkpoint the blocker and downstream execution owner explicitly."
  reason: Reduces wasted local retries and clarifies ownership for execution evidence.

### Workflow Improvements
- issue: Tickets entering autopilot without workflow metadata force bootstrap assumptions that are unrelated to product correctness.
  improvement: Introduce an automatic ticket-header normalization step before PLANNING that injects missing workflow blocks in a standardized format.
  expected_benefit: Cleaner stage transitions, fewer assumption logs, and stronger audit trace consistency.

- issue: Subjective architecture ACs required custom post-hoc justification to satisfy final validation.
  improvement: Add a "structural evidence required" checklist item in SPECIFICATION for any AC using adjectives like thin/readable/clean.
  expected_benefit: Faster gatekeeper decisions and less integration-stage interpretation churn.

### Keep / Reinforce
- practice: Recording "Would have asked" assumptions with confidence levels at each stage.
  reason: Exposes uncertainty early and creates actionable inputs for prompt/workflow hardening.

- practice: Combining decomposition contract tests with broad legacy regression suites before closure.
  reason: Preserves behavioral parity while validating the new module boundaries and architecture intent.

---

## [M901-08-blender-utilities-split] — Runtime seam contracts and environment evidence prevent split-refactor ambiguity
*Completed: 2026-04-22*

### Learnings
- category: testing
  insight: For module-split refactors, runtime seam contracts (importability, re-export identity, fallback behavior, and fail-safe flows) are a stronger primary gate than structural-only assertions.
  impact: Test design froze behavior-sensitive seams early, which reduced ambiguity about whether the split preserved actual runtime expectations.
  prevention: Require decomposition tickets to encode executable runtime contracts as first-class RED tests before implementation starts.
  severity: medium

- category: process
  insight: When local execution tooling is unavailable, blocked commands must be checkpointed with exact failure evidence so downstream stages can execute in the configured environment without rewriting intent.
  impact: Test design could proceed despite missing local `pytest`, while preserving deterministic handoff expectations instead of silently degrading coverage.
  prevention: Standardize environment-blocker reporting in checkpoints with exact command, error text, and explicit downstream execution owner.
  severity: medium

- category: architecture
  insight: Fixed-module-count acceptance criteria can force awkward ownership decisions; those decisions must be explicitly frozen in the spec to avoid late-stage scope churn.
  impact: Utility ownership for `clear_scene` required a medium-confidence assumption because introducing a fourth module was out of scope.
  prevention: Add a required "boundary exception rationale" clause whenever acceptance criteria constrain module count but a symbol spans responsibilities.
  severity: low

### Anti-Patterns
- description: Using file-organization checks as the primary refactor validation while leaving behavior seams implicitly assumed.
  detection_signal: Test plans focus on module presence/export lists but omit fallback dispatch, deterministic helpers, or fail-safe flow checks.
  prevention: Treat structure checks as secondary and require at least one executable behavioral contract per critical responsibility bucket.

- description: Logging environment blockers without a deterministic handoff contract.
  detection_signal: Checkpoint notes mention missing tooling but do not specify the exact failed command and required execution environment.
  prevention: Enforce a blocker template: failed command, exact error, expected runner (`uv`, CI, or container), and stage responsible for rerun.

### Prompt Patches
- agent: Test Designer Agent
  change: "For module decomposition tickets, include executable runtime seam tests (re-export identity, fallback behavior, deterministic helper behavior, and fail-safe paths) as mandatory primary contracts; do not rely on structural import assertions alone."
  reason: Prevents false-green outcomes where module layout passes but runtime behavior drifts.

- agent: Orchestrator Agent
  change: "If a stage is blocked by local environment/tooling, record a deterministic blocker handoff with exact command, exact error output, required execution environment, and explicit downstream owner before advancing the ticket."
  reason: Preserves test intent and avoids silent quality erosion when local runners are unavailable.

- agent: Spec Agent
  change: "When acceptance criteria constrain module count or fixed target files, add a required 'Boundary Exception Rationale' subsection for mixed-responsibility symbols and freeze ownership decisions before TEST_DESIGN."
  reason: Reduces medium-confidence ownership assumptions and prevents implementation-stage scope debates.

### Workflow Improvements
- issue: Workflow bootstrap and boundary assumptions were re-stated across multiple stages for this ticket.
  improvement: Add a pre-spec normalization step that records fixed constraints (module count, compatibility posture, gate type) into a reusable assumption block referenced by downstream stages.
  expected_benefit: Fewer repeated assumptions, faster stage handoffs, and more consistent validation narratives.

- issue: Environment blockers can let contract tests drift from executable reality if handoff is informal.
  improvement: Require a formal "execution transfer" artifact whenever authored tests are not run in-stage due to missing tooling.
  expected_benefit: Keeps coverage intent intact and improves first-pass success in static QA/integration.

### Keep / Reinforce
- practice: Capturing "Would have asked" assumptions with confidence levels in each stage checkpoint.
  reason: Makes uncertainty explicit and creates a reliable feedstock for prompt hardening and workflow improvements.

- practice: Pairing split-contract tests with broader regression suites and diff-cover/static evidence before ticket closure.
  reason: Balances targeted refactor safety with overall system regression protection.

---

## [M901-07-enemy-builder-template] — Convert ambiguous quality targets and tool availability into explicit, testable gate contracts
*Completed: 2026-04-22*

### Learnings
- category: process
  insight: Acceptance criteria that include both hard requirements and advisory quality targets (for example LOC bands) require explicit "blocking vs non-blocking" classification before integration evidence is collected.
  impact: Integration required a dedicated evidence-closure pass to restate that the 80-120 LOC band was guidance while deduplication/parity were the true gates.
  prevention: Require specification freeze to label each AC metric as hard gate or quality guidance, and enforce that classification in validation templates.
  severity: medium

- category: testing
  insight: Template-method refactors are safest when phase-order guarantees are validated through executable behavior probes rather than source-shape inspection.
  impact: Runtime hook-order tests gave deterministic proof of `body -> limbs -> materials -> zone extras` sequencing and avoided brittle structural assertions.
  prevention: Standardize probe-subclass event-trace tests for all template orchestration tickets and treat static/source checks as secondary evidence only.
  severity: medium

- category: infra
  insight: Static-analysis acceptance checks are fragile when they depend on optional local binaries unless fallback evidence policy is defined up front.
  impact: `mypy` executable unavailability forced medium-confidence assumptions and deferred closure to alternate evidence (scoped typing tests + AST checks).
  prevention: Add a preflight tool-availability check in TEST_DESIGN and require a declared fallback hierarchy for each static gate command.
  severity: high

### Anti-Patterns
- description: Deferring AC interpretation (hard vs guidance) until late integration validation.
  detection_signal: Checkpoints mention objective metric reporting but also note "non-blocking quality target" only after implementation evidence is compiled.
  prevention: Block implementation handoff unless AC semantics are explicitly typed as required, advisory, or informational.

- description: Treating local toolchain gaps as ad hoc exceptions instead of planned gate behavior.
  detection_signal: Integration logs include "Would have asked" entries about whether to block on missing static-analysis executables.
  prevention: Require per-ticket static-gate fallback policy in the spec/test-design artifacts before code validation begins.

### Prompt Patches
- agent: Spec Agent
  change: "For every numeric or threshold-style acceptance criterion, add a one-line gate classification: `blocking` or `quality guidance`; include the required evidence command for blocking metrics and note non-blocking metrics as advisory in Validation Status format."
  reason: Prevents late ambiguity during integration and reduces evidence-gap reruns.

- agent: Test Designer Agent
  change: "For template-method refactors, include at least one executable probe-subclass test that records phase events and asserts strict call order and single execution per phase; do not rely solely on source inspection for orchestration guarantees."
  reason: Makes orchestration contracts robust to internal refactors while preserving behavioral intent.

- agent: Orchestrator Agent
  change: "Before entering IMPLEMENTATION, run a static-gate preflight checklist (`tool exists`, `command path`, `fallback evidence path`) for each required static-analysis gate and record the selected fallback policy in checkpoints."
  reason: Converts tool availability surprises into deterministic workflow behavior.

### Workflow Improvements
- issue: Evidence closure required an additional integration checkpoint to reconcile advisory LOC targets with pass/fail ACs.
  improvement: Add an "AC Semantics Matrix" section to the ticket workflow state (criterion, blocking status, evidence source) immediately after SPECIFICATION.
  expected_benefit: Shorter integration cycles and fewer gatekeeper clarification loops.

- issue: Static gate reliability depended on environment-specific binaries without guaranteed availability.
  improvement: Introduce a shared static-validation adapter command (or documented fallback chain) used consistently across all tickets.
  expected_benefit: More predictable CI/local parity and fewer medium-confidence assumption checkpoints.

### Keep / Reinforce
- practice: Recording "Would have asked" assumptions with confidence labels at each stage.
  reason: Preserves uncertainty audit trails and creates direct input for prompt and workflow hardening.

- practice: Pairing runtime behavioral contract tests with objective static evidence scans for refactor acceptance.
  reason: Balances regression protection with maintainability proof without overfitting to file structure.

---

## [M901-02-model-registry-layering] — Ambiguous layer contracts create avoidable assumption loops
*Completed: 2026-04-21*

### Learnings
- category: architecture
  insight: Ownership of cross-cutting constants used by both validation and migration logic must be explicitly defined at spec time to prevent dependency-direction guesswork.
  impact: The pipeline required a checkpoint assumption for where `SCHEMA_VERSION` should live to avoid circular imports, introducing avoidable design uncertainty.
  prevention: Require every layering spec to include a symbol ownership table for shared constants/functions and an import-direction statement for each module pair.
  severity: medium

- category: testing
  insight: When specs define behavior but omit concrete API names for new modules, test design will invent naming contracts that may or may not match implementation intent.
  impact: Test design had to assume exact store function names and formatting guarantees, creating medium-confidence drift risk between spec and tests.
  prevention: Add a mandatory "public symbol list" section in specs for any new module so tests assert behavior and stable names intentionally, not by inference.
  severity: medium

- category: process
  insight: Ambiguous acceptance-criteria language around "no modification" constraints causes repeated interpretation checkpoints even when behavioral intent is clear.
  impact: Planning required an explicit assumption about whether router import-only edits were allowed, adding coordination overhead before implementation.
  prevention: Normalize AC wording to distinguish "no behavior change" from "no file edits"; ban overloaded phrasing in refactor tickets.
  severity: medium

### Anti-Patterns
- description: Defining module boundaries without explicitly assigning ownership of shared versioning symbols and dependency direction.
  detection_signal: Checkpoints include "Would have asked" about where a shared constant belongs or how to avoid cycles between adjacent layers.
  prevention: In spec review, block advancement until ownership and one-way import graph are explicit.

- description: Writing test tickets that specify capability ("load/save") but not canonical public symbol names for new seam modules.
  detection_signal: Test design logs medium-confidence assumptions about function names or persistence formatting details.
  prevention: Require spec and test design to share a fixed exported-symbol contract before adversarial test expansion.

- description: Using AC text that mixes contract stability intent with edit-prohibition language.
  detection_signal: Planning logs interpretation assumptions for phrases like "works without modification."
  prevention: Replace with explicit clauses: "HTTP behavior unchanged" and "import-path adjustments allowed/disallowed" as separate statements.

### Prompt Patches
- agent: Spec Agent
  change: "For any layering/refactor ticket, include a mandatory 'Shared Symbol Ownership' table (constant/function -> owning module) plus an explicit one-way import graph. Do not advance spec if any shared symbol ownership is implicit."
  reason: Eliminates repeated dependency-direction assumptions and prevents cycle-prone designs from reaching implementation.

- agent: Test Designer Agent
  change: "When a ticket introduces a new module seam, require a 'Public Symbol Contract' subsection listing exact callable names and observable I/O guarantees. If absent, stop and request spec amendment before authoring tests."
  reason: Prevents test/implementation drift caused by inferred naming contracts.

- agent: Planner Agent
  change: "Rewrite any AC phrase of the form 'X works without modification' into two explicit constraints: (1) behavior/contract invariants and (2) permitted edit scope (none/import-only/full), before handing off to spec."
  reason: Reduces ambiguity-driven checkpoint assumptions and improves downstream execution speed.

### Workflow Improvements
- issue: Multiple medium-confidence assumptions were logged for semantics, symbol placement, and API naming before implementation could proceed.
  improvement: Add an orchestrator pre-spec ambiguity gate that scans AC/spec drafts for overloaded terms ("without modification", "load/save only") and forces explicit rewrite before Stage SPECIFICATION completes.
  expected_benefit: Fewer assumption checkpoints and less rework risk from hidden contract divergence.

- issue: Test-break assumptions can target behaviors outside the ticket's explicit contract (e.g., extension-case handling) when normalization rules are not codified up front.
  improvement: Add a test-break input checklist item that enumerates normalization policies (case sensitivity, format canonicalization) from spec; disallow introducing them by inference.
  expected_benefit: Adversarial tests stay high-signal and reduce downstream disputes about intended behavior.

### Keep / Reinforce
- practice: Capturing unresolved ambiguities as explicit checkpoint assumptions with confidence levels.
  reason: Preserves auditability and prevents silent scope mutation when deterministic clarification is unavailable.

---

## [M9-02-mesh-material-audit] — Fail-closed assumptions prevented false pass, but revealed upstream ambiguity debt
*Completed: 2026-04-21*

### Learnings
- category: process
  insight: When workflow state fields are enum-constrained, stage completion must be represented through handoff metadata (`Next Responsible Agent`, validation notes) rather than inventing pseudo-stages.
  impact: Stage naming ambiguity at implementation handoff risked invalid workflow state transitions and required checkpoint clarification.
  prevention: Treat stage enums as immutable contract surface; encode completion semantics in dedicated handoff fields and gate on enum validity in tests/review.
  severity: medium

- category: architecture
  insight: For cross-ticket dependency decisions (like visual identity direction), missing authoritative guidance must default to non-pass classification with explicit ownership and follow-on linkage.
  impact: Player readability could have been incorrectly marked pass without M13 directives; fail-closed deferral preserved traceability and prevented contradictory art direction.
  prevention: Require an explicit "directive present vs absent" branch in spec for all external-dependency decisions; absent directive must force defer/fix-required path.
  severity: high

- category: testing
  insight: Adversarial coercion tests should be promoted from opportunistic checks to mandatory baseline whenever option parsing uses numeric conversion.
  impact: `stripe_width` type coercion and NaN/Inf rotation behavior required assumption-driven hardening during TEST_BREAK, signaling a recurring parser robustness gap.
  prevention: Establish a default mutation matrix (`non-numeric`, `None`, `NaN`, `±inf`) for all numeric option inputs before implementation begins.
  severity: medium

### Anti-Patterns
- description: Encoding completion with non-schema stage labels instead of using existing workflow handoff fields.
  detection_signal: Checkpoints debating whether to set stage names like `<STAGE>_COMPLETE` despite enum-defined allowed values.
  prevention: Enforce "enum-only stage values" as a hard rule and document completion only via validation + next-agent fields.

- description: Treating absence of cross-milestone directive as implicit approval to pass.
  detection_signal: A dependency field is unresolved (`no-directive-found`) while status remains `pass` or lacks follow-on owner.
  prevention: Add a fail-closed guard: unresolved external direction prohibits `pass` and requires linked owner/ticket.

- description: Leaving option sanitization policy implicit until TEST_BREAK introduces adversarial mutations.
  detection_signal: Test-design checkpoints discuss contract-only tests while coercion behavior (`float()`, non-finite handling) is unspecified.
  prevention: Make coercion policy explicit in spec and require adversarial parser tests during TEST_DESIGN, not only TEST_BREAK.

### Prompt Patches
- agent: Spec Agent
  change: "For every decision that depends on external milestone guidance, include an explicit unresolved-guidance branch: if authoritative directive is missing or conflicting, status must be non-pass (`deferred` or `fix-required`) with required owner and follow-on link."
  reason: Prevents speculative pass decisions and keeps cross-ticket alignment auditable.

- agent: Implementation Generalist Agent
  change: "Do not invent new Stage values to express completion. Keep Stage within the declared enum and encode completion in Validation Status plus `Next Responsible Agent`."
  reason: Eliminates handoff ambiguity and preserves workflow schema integrity.

- agent: Test Designer Agent
  change: "When any input is parsed with numeric coercion (`float`, int-like normalization, angle normalization), include adversarial tests for non-numeric values, `None`, `NaN`, and `±inf`, and specify expected reject/sanitize behavior."
  reason: Moves parser-hardening earlier and reduces assumption-driven rework in TEST_BREAK.

### Workflow Improvements
- issue: Checkpoint assumptions were needed to resolve stage-enum interpretation and external-directive absence during later stages.
  improvement: Add a mandatory pre-implementation "assumption closure" pass that converts Medium-confidence assumptions into explicit ticket/spec statements or explicit risk waivers.
  expected_benefit: Fewer late-stage interpretation debates and smoother acceptance gating.

- issue: TEST_DESIGN intentionally scoped to spec-contract checks, leaving coercion resilience to later adversarial discovery.
  improvement: Add a bifurcated test-design checklist: (1) contract/schema assertions and (2) input-sanitization adversarial cases for every parsed option.
  expected_benefit: Earlier detection of numeric parsing gaps, reducing implementation churn.

### Keep / Reinforce
- practice: Using fail-closed status semantics (`no-directive-found` => deferred with owner/link) for contentious player-readability decisions.
  reason: Preserves safety and traceability when external art-direction authority is unresolved.

- practice: Capturing checkpoint logs with "would-have-asked / assumption / confidence" structure at each stage.
  reason: Produces high-quality signals for systematic learning extraction and prompt improvements.

---

## [M25-02e_implement_stripes_texture] — Mirror proven texture modes; preview store vs feat keys
*Completed: 2026-04-19*

### Learnings
- category: architecture
  insight: Stripes reused spots’ PNG + material factory shape with a single algorithmic swap (1D `fract` period vs 2D distance field). Documenting the **UV period** semantics (0.05–1.0, 50/50 duty) in the ticket spec avoided the “stripe width” naming ambiguity between thickness-only and full-period models.
  impact: One coherent formula for Python pixel loop, Blender bake, and Three.js shader.
  severity: medium

- category: frontend
  insight: `GlbViewer` mixed **legacy** global `texture_*` keys (used by tests) with **live** `feat_body_texture_*` from `animatedBuildOptionValues`. Resolving mode/colors by “legacy defined → legacy wins, else feat” keeps tests stable while the Colors UI drives feat keys.
  impact: Exporting `normalizedTextureMode` from `ZoneTextureBlock` lets the viewer share the same mode normalization as controls without duplicating strings.
  severity: medium

---

## [M25-02d_implement_spots_texture] — PNG generation, test validation clarity, and adversarial test design
*Completed: 2026-04-19*

### Learnings
- category: testing
  insight: Specification test bugs (incorrect byte offsets, malformed color assumptions) are only detectable when tests are executed against a reference implementation or validated independently. A test that looks correct on paper may fail due to subtle format assumptions (PNG chunk layout, RGB color channel separability).
  impact: 4 spec-required tests failed (CRC-32 offset calculation, density pattern color counting) requiring rework to fix the test suite itself, not the implementation. AC Gatekeeper had to distinguish between implementation bugs and test suite bugs using independent validation (PNG format spec, color math).
  prevention: When writing specification tests for binary formats (PNG, JPEG, protocol buffers), include a validation reference (external decoder/encoder library, format specification citation, or fixed golden bytes) so test bugs are caught during TEST_DESIGN review, not after implementation.
  severity: high

- category: architecture
  insight: Procedural texture backends (PNG generator) benefit from a layered validation model where generator functions accept broad inputs (no dimension/density validation) and upstream callers enforce bounds. This mirrors gradient_generator.py pattern and reduces defensive code duplication.
  impact: Specification ambiguity about "who validates density bounds" (generator vs caller) required CHECKPOINT assumptions and would have caused integration bugs if split incorrectly. Material system layer (apply_zone_texture_pattern_overrides) owns density clamping [0.1, 5.0]; generator accepts any float.
  prevention: When designing texture generation pipelines, explicitly document input validation scope in spec: (a) which layer owns dimension validation, (b) which layer owns parameter clamping, (c) generator function docstring examples showing valid input ranges. Place validation closest to the source of invalid input (upstream API/form).
  severity: medium

- category: frontend / testing
  insight: Frontend test suites labeled "smoke tests" without explicit AC mapping can hide coverage gaps. Requirement 6 & 7 specified 30 detailed ACs (AC6.1–6.15, AC7.1–7.15) but implementation reported "19 smoke tests passing" without mapping tests to individual ACs.
  impact: AC Gatekeeper could not verify whether all 30 ACs were covered by tests. Required checkpoint annotation and clarification before advancement to COMPLETE.
  prevention: In TEST_DESIGN phase, Test Designer must map each test to at least one AC by ID. Create an AC→Test traceability matrix in the test file docstring or as a separate mapping artifact. Reject "smoke tests" labels that lack explicit AC enumeration.
  severity: medium

- category: code quality
  insight: Legacy debug logging (e.g., `/tmp/gradient_debug.log` writes in gradient_generator.py lines 469–491, 490–491) should not be carried forward into new similar features. When reusing patterns, audit for debug I/O before copying.
  impact: Spots implementation correctly had no debug logging, but gradient predecessor left logging in place that could interfere with production builds or expose I/O race conditions.
  prevention: When a specification says "no debug logging" (AC1.14), check reference implementations (gradient) and add a cleanup task if they violate the same constraint. Flag debug I/O in pattern reviews before code duplication.
  severity: low

### Anti-Patterns
- description: Assuming test failures are implementation bugs without validating against an independent reference (format spec, known-good encoder, external decoder).
  detection_signal: Multiple failing tests in same category (CRC-32, pixel counting) with same root cause, and implementation looks correct.
  prevention: For binary format tests, include a reference validator (e.g., PIL.Image, zlib, or format spec) and use it in at least one test to validate correct behavior independently of the test code itself.

- description: Labeling frontend test coverage as "smoke tests" without explicit acceptance criteria mapping.
  detection_signal: Spec has 20+ ACs but test report says "19 smoke tests passing" with no per-AC enumeration.
  prevention: Require every test file to include an AC→Test traceability header. Reject test reports without explicit AC coverage claims.

### Prompt Patches
- agent: Test Designer Agent
  change: "For binary format generation (PNG, JPEG, protocol buffers), include at least one independent validation test that uses a reference library (PIL.Image, zlib, etc.) to verify the output is correctly formed, independent of the generator's internal logic. Document this validation reference in the test suite docstring."
  reason: Catches test bugs early and prevents spec test failures from masking implementation issues.

- agent: Spec Agent
  change: "When specifying texture or binary generation, explicitly state which layer validates inputs: (a) generator function (no validation), (b) wrapper function (format validation), (c) caller (business logic bounds). Document with examples. For generated binary formats, cite the normative specification (e.g., PNG RFC or ISO standard) that test code will reference."
  reason: Eliminates ambiguity about validation scope and gives test designers concrete references to validate against.

- agent: Test Designer Agent
  change: "For frontend test suites exceeding 10 tests, create an AC→Test traceability matrix in the test file header or as a separate COVERAGE.md artifact. Reject coverage reports that use vague labels ('smoke tests', 'integration tests') without mapping to specific requirement IDs (AC6.1, AC7.3, etc.)."
  reason: Prevents coverage gaps and makes AC Gatekeeper validation deterministic instead of narrative.

### Workflow Improvements
- issue: AC Gatekeeper had to resolve test status discrepancies by reading checkpoint notes and implementation summaries, requiring manual interpretation of contradictory statements.
  improvement: Require Implementation Agent to run full test suite before declaring readiness and document results in a structured TEST_RESULTS table: test file, passing count, failing count, failure category (spec bug / adversarial / regression), and citations to fixes.
  expected_benefit: Gatekeeper has objective data instead of narrative claims, reducing ambiguity and rework cycles.

- issue: Spec test bugs (CRC-32 offset, color counting logic) were caught only after implementation, not during TEST_DESIGN.
  improvement: Add a "Format Validation Review" gate before TEST_BREAK: independent reviewer checks spec tests against normative format documentation (PNG RFC 2083, JPEG ISO 10918, etc.) and validates test assumptions via reference implementations.
  expected_benefit: Binary format test bugs caught during TEST_DESIGN, not after implementation and 4 test fixes.

### Keep / Reinforce
- practice: Specification clearly documented density as linear grid scaling (density=1 baseline, density=2 creates 2× more spots), which matched implementation model and avoided algorithm ambiguity.
  reason: Clear density semantics prevented backend rework and enabled simple test validation (count spots at two densities and verify direction of change).

- practice: Case-insensitive mode comparison (using `.strip().lower()` pattern) was established in gradient and reused consistently in spots, and specification explicitly required it.
  reason: Pattern consistency reduced implementation decisions and made adversarial tests deterministic.

---

## [M25-05_bipedal_body_presets] — rig tests without full enemy `build_options`
*Completed: 2026-04-19*

### Learnings
- category: python / rig
  insight: `HumanoidSimpleRig._segment_count` runs in lightweight import-rig tests on `_ImportHumanoidRig` instances that do not set `build_options`. Any preset hook that reads `self.build_options` must use `getattr(self, "build_options", None)` and tolerate missing dicts.
  impact: Prevents `AttributeError` in `tests/core/test_rig_ratios.py` and `test_humanoid_rig_segments.py` when adding body-type-aware leg segment logic.
  prevention: When extending `SimpleRigModel` subclasses used in bare rig tests, guard optional runtime state the same way as optional mesh overrides.
  severity: medium

---

## [M25-02b_integrate_universal_color_picker] — lockMode for embedded universal picker rows
*Completed: 2026-04-18*

### Learnings
- category: frontend
  insight: A tabbed `ColorPickerUniversal` must support `lockMode` when embedded in per-def `ControlRow`s so mode switching does not fight `feat_*_texture_mode` or duplicate UI; gradient A/B/direction collapse cleanly into one locked gradient block wired to three store keys.
  impact: Preserves spec tests that reason about visibility of gradient parameters without three duplicate labels.
  prevention: When reusing a multi-mode component inside forms with external mode selectors, add an explicit embed/single-mode API up front.
  severity: medium

### Anti-Patterns
- description: Expecting legacy test strings like `"Gradient color A"` after consolidating controls; update assertions to stable sublabels (`From Color`, `aria-label` on direction group).
  detection_signal: Tests pass only on old row-per-def layout.
  prevention: Prefer role/name queries aligned with the universal subcomponents.

---

## [M25-02a_color_picker_component] — Pipeline reconciliation when code lands before ticket state
*Completed: 2026-04-19*

### Learnings
- category: process
  insight: A backlog ticket without `WORKFLOW STATE` but with substantial implementation in `main` requires a reconciliation pass: treat as verify-and-close, not restart from PLANNING, unless ACs are unmet.
  impact: Avoids duplicate specs and re-implementation; focuses effort on tests, shared utilities, and AC evidence.
  prevention: On `ap-continue`, if filesystem shows the feature exists, run targeted tests first and only backfill pipeline artifacts (workflow table, `done/` move) after green.
  severity: medium

- category: testing
  insight: Importing helpers that were never exported (`hexForColorInput` from `clipboardHex`) fails at runtime in the browser but is easy to miss until Vitest executes the component tree.
  impact: 33 ColorPicker tests failed until shared helpers were added and aligned with blur semantics.
  prevention: After extracting shared UI, run the narrowest Vitest directory (`src/components/ColorPicker`) before full-suite claims.
  severity: medium

### Anti-Patterns
- description: Assuming file inputs expose `role="button"` in jsdom; tests must use `aria-label` + `getByLabelText` or `querySelector('input[type=file]')`.
  detection_signal: Accessibility query failures for upload controls in RTL.
  prevention: Add `aria-label` on file inputs and query by label in tests.

### Prompt Patches
- agent: Test Designer Agent
  change: "For shared hex/color inputs, assert imports resolve to real exports in `clipboardHex.ts` (or chosen util module); add a smoke test that mounts the component under Vitest."
  reason: Catches missing exports before merge.

### Workflow Improvements
- issue: Tickets in `backlog/` without workflow blocks cannot resume unambiguously.
  improvement: On first enqueue, write minimal `WORKFLOW STATE` with Stage `PLANNING` even if work is speculative.
  expected_benefit: `ap-continue` can branch on stage without heuristics.

---

## [02_wire_generated_enemies_combat_rooms] — Arbitration-to-closure requires explicit evidence contracts
*Completed: 2026-04-14*

### Learnings
- category: process
  insight: A `BLOCKED` ticket should not return to execution until arbitration output is transformed into an explicit closure contract (authority model, schema keys, test ownership, and stage order), not just a narrative decision.
  impact: Without converting arbitration into enforceable closure constraints, blocked tickets can re-enter with unresolved ambiguity and loop back into gate failures.
  prevention: Require a standardized `Arbitration Closure Contract` artifact in ticket state before any stage transition from `BLOCKED` to active execution.
  severity: high

- category: testing
  insight: Arbitration quality is only reusable when it names exact test groups to rewrite/remove and preserves strict assertions that stay canonical.
  impact: The unblock-to-complete transition succeeded because arbitration explicitly retained strict procedural assertions and targeted legacy tests for rewrite/removal.
  prevention: Treat "which tests are authoritative now" as mandatory arbitration output, with test IDs or suite names captured in the ticket workflow state.
  severity: high

- category: process
  insight: Completion claims after arbitration must include objective closure evidence (full-suite pass, subsystem pass, and stage-folder alignment) to avoid false-complete outcomes.
  impact: Ticket closure became defensible only after documented exits for `godot --headless -s tests/run_tests.gd`, `ci/scripts/run_tests.sh`, and done-folder/stage consistency.
  prevention: Add a completion checklist template that rejects `COMPLETE` without command-level exit evidence and workflow-location consistency.
  severity: medium

### Anti-Patterns
- description: Treating arbitration as advisory commentary instead of a binding migration contract.
  detection_signal: Ticket exits `BLOCKED` without an explicit list of canonical authority decisions and dependent test migration actions.
  prevention: Require a gatekeeper-validated arbitration memo with mandatory fields before unblocking.

- description: Declaring `COMPLETE` using only local implementation success while skipping workflow-state integrity checks.
  detection_signal: Tests pass but ticket stage, folder location, or NEXT ACTION metadata still imply non-terminal state.
  prevention: Enforce stage/folder/NEXT ACTION consistency checks as part of completion validation.

### Prompt Patches
- agent: Planner Agent
  change: "When a ticket enters `BLOCKED` due to contract conflict, do not reopen execution until an `Arbitration Closure Contract` is logged with: canonical authority model, required test migrations, strict assertions retained, and mandated stage execution order."
  reason: Converts arbitration outcomes into enforceable execution constraints instead of informal guidance.

- agent: Acceptance Criteria Gatekeeper Agent
  change: "For `BLOCKED` -> `COMPLETE` recoveries, require closure evidence bundle: (1) arbitration decisions mapped to concrete test-suite actions, (2) command-level pass evidence for subsystem and full regression gates, and (3) stage/folder/NEXT ACTION consistency."
  reason: Prevents premature closure and makes recovery path auditable.

- agent: Test Designer Agent
  change: "After arbitration on conflicting contracts, annotate each affected test group as `retain-strict`, `rewrite`, or `remove`, and link each label to the authoritative runtime model in the ticket."
  reason: Reduces ambiguity during post-arbitration test cleanup and protects canonical assertions.

### Workflow Improvements
- issue: Unblock criteria from arbitration were implicit and spread across notes.
  improvement: Introduce a structured `BLOCKED Recovery Checklist` template in workflow state fields.
  expected_benefit: Speeds recovery while keeping unblock decisions deterministic and reviewable.

- issue: Completion validation mixed technical and process checks informally.
  improvement: Split gatekeeper validation into two explicit sub-gates: `Behavioral Evidence` and `Workflow Integrity Evidence`.
  expected_benefit: Makes final closure criteria clearer and reduces reopen risk from metadata drift.

### Keep / Reinforce
- practice: Human arbitration captured explicit canonical decisions (authority model, schema key strictness, deterministic fallback policy, and stage order).
  reason: The explicit decision set made downstream completion verifiable rather than interpretive.

- practice: Gatekeeper required full command evidence plus workflow consistency before declaring terminal completion.
  reason: Preserved high-confidence closure after a previously blocked state.

---


## [18_registry_subtabs_by_pipeline_cmd] + [19_model_viewer_fullscreen_button] — Registry RunCmd tabs and GLB fullscreen
*Completed: 2026-04-11*

### Learnings
- category: infra
  insight: Vitest/Vite 5 on Node 16 fails at startup (`crypto.getRandomValues`); the frontend pins Node ≥18 in `package.json` and should treat Node 20 (`.nvmrc`) as the supported test/build runtime in ticket validation text.
  impact: Local/CI agents using system Node 16 see a cryptic Vite error instead of a clear engines mismatch.
  prevention: Document `nvm use` / `.nvmrc` in AC validation and optional CI `engines` enforcement; fail fast with a pretest script if needed.
  severity: medium
- category: testing
  insight: UI that persists enum-like keys in `localStorage` needs adversarial coverage for unknown tokens so the pane never mounts the wrong subtree or throws.
  impact: Invalid saved sub-tab could have caused wrong default until invalid-key test was added.
  prevention: Test Designer / Test Breaker: one test per persisted key with garbage + out-of-enum values.
  severity: low
- category: process
  insight: `workflow_enforcement_v1.md` references `ci/scripts/spec_completeness_check.py`, which is not present in the repo; the pipeline still advanced with specs authored and a note on the ticket.
  impact: Orchestrators may block waiting for a missing script.
  prevention: Add the script or amend workflow doc to mark the gate optional until implemented.
  severity: low

### Anti-Patterns
- description: Claiming Fullscreen API + OrbitControls ACs are fully proven by jsdom-only tests.
  detection_signal: No `resize`/`fullscreenchange` wiring and no note that WebGL interaction is smoke-tested elsewhere.
  prevention: Keep resize dispatch on fullscreen transitions and document manual or browser-automation smoke in validation when policy requires it.

### Prompt Patches
- agent: Planner
  change: When scheduling frontend Vitest work, require Node version alignment (read `asset_generation/web/frontend/.nvmrc` or `engines`) in the execution plan artifact paths.
  reason: Avoids false-red environments on older Node.

### Workflow Improvements
- issue: Spec exit gate script path is documented but missing from repository.
  improvement: Track a chore ticket to implement `spec_completeness_check.py` or remove the gate reference until it exists.
  expected_benefit: Clear handoff between Spec and TEST_DESIGN without agent confusion.

### Keep / Reinforce
- practice: Extract shared center-panel tab styles (`centerPanelTabBtnStyle`) instead of duplicating literals when adding a second tab strip inside a pane.
  reason: Keeps Registry sub-tabs visually aligned with Code/Build/Registry with a single source of truth.

---

## [01_spec_procedural_enemy_spawn_attack_loop] — Convert medium-confidence assumptions into explicit schema fixtures before adversarial tests
*Completed: 2026-04-14*

### Learnings
- category: process
  insight: When acceptance criteria reference stale paths, spec work must resolve canonical ownership immediately and propagate that canonical path into downstream test contracts.
  impact: A path mismatch (`scripts/level/...` vs `scripts/system/...`) created avoidable ambiguity during spec and test authoring.
  prevention: Add a mandatory "canonical path reconciliation" subsection in spec tickets before TEST_DESIGN, listing stale references and the chosen source-of-truth path.
  severity: medium

- category: testing
  insight: Medium-confidence assumptions about serialization shape should be codified as explicit schema examples in the spec before TEST_DESIGN writes strict assertions.
  impact: Tests enforced `enemy_spawn_declarations` metadata on room roots, then adversarial runs exposed deterministic gaps in room declaration metadata and legacy room seams that required implementation rework.
  prevention: For each contract key introduced in spec, include one valid and one invalid fixture snippet so test and implementation agents inherit identical structure expectations.
  severity: high

- category: architecture
  insight: Compatibility seams (legacy embedded enemies, missing spawn anchors, generated-scene path validity) must be treated as first-class contract requirements, not implementation details.
  impact: The first red cycle in TEST_BREAK clustered around backward-compatibility behavior rather than new happy-path logic, extending the implementation loop.
  prevention: Add a dedicated compatibility matrix in spec tickets that maps each legacy state to required runtime behavior and fallback.
  severity: high

- category: process
  insight: Workflow closure state must be validated as part of acceptance completion, including folder placement and stage value coherence.
  impact: Ticket validation was blocked by folder/state mismatch (`in_progress/` while functionally complete), creating non-product rework.
  prevention: Add a pre-close checklist item in gatekeeper handoff: verify milestone folder location and WORKFLOW STATE transition are both complete before declaring terminal status.
  severity: medium

### Anti-Patterns
- description: Writing strict contract tests from underspecified data-shape assumptions.
  detection_signal: TEST_DESIGN introduces exact metadata keys while spec has no fixture examples or explicit serialization schema.
  prevention: Require spec fixture blocks for every asserted metadata key before tests can move to TEST_BREAK.

- description: Treating legacy compatibility as an implementation afterthought.
  detection_signal: Initial failing tests center on fallback/legacy room behavior instead of new declared contract paths.
  prevention: Add compatibility requirements as numbered contract clauses with dedicated adversarial tests.

- description: Declaring completion without workflow-state hygiene.
  detection_signal: AC evidence is green but ticket still sits in `in_progress/` or stage is not terminal.
  prevention: Gatekeeper must check ticket path/state coherence as a hard close condition.

### Prompt Patches
- agent: Spec Agent
  change: "For every new contract key, include one canonical valid fixture and one invalid fixture snippet in the spec; do not leave serialization shape implicit when downstream tests will assert exact keys."
  reason: Prevents medium-confidence assumptions from becoming red-cycle rework in TEST_BREAK/implementation.

- agent: Test Designer Agent
  change: "Before writing strict schema assertions, verify the spec contains explicit fixture examples for each asserted key; if absent, block and request spec clarification instead of inferring shape."
  reason: Reduces false certainty and avoids enforcing guessed metadata structures.

- agent: Acceptance Criteria Gatekeeper Agent
  change: "When AC evidence is complete, also validate closure hygiene: ticket file is in the correct milestone `done/` folder and WORKFLOW STATE is terminal; if either is missing, return a closure action instead of terminal pass."
  reason: Eliminates avoidable final-step rework unrelated to product behavior.

### Workflow Improvements
- issue: Assumption capture exists in checkpoints but is not converted into explicit schema artifacts before tests.
  improvement: Add a micro-gate between SPECIFICATION and TEST_DESIGN: convert all medium-confidence assumptions into either spec fixture examples or explicit unresolved questions.
  expected_benefit: Fewer deterministic red cycles caused by inferred data contracts.

- issue: Compatibility behavior is discovered reactively in TEST_BREAK.
  improvement: Add a required "legacy compatibility matrix" section for runtime-spec tickets that touch existing scenes or generated assets.
  expected_benefit: Earlier detection of fallback requirements and less implementation churn.

- issue: Ticket completion can stall on administrative state mismatch after technical AC success.
  improvement: Add an automated close checklist step in gatekeeper flow covering folder path, stage transition, and next-agent nulling.
  expected_benefit: Faster, cleaner ticket closure with fewer human cleanup passes.

### Keep / Reinforce
- practice: Scoped checkpoints captured `Would have asked` / `Assumption made` / `Confidence` at each stage.
  reason: Enabled precise extraction of root-cause uncertainty instead of relying on hindsight narratives.

- practice: Adversarial contract expansion (mutation/corrupt-manifest/schema/stress) surfaced hidden compatibility seams early.
  reason: Produced actionable failures tied directly to contract boundaries and improved implementation targeting.

---

## [registry-fix-versions-slots-load] — Align slot UI predicates, placeholder semantics, and scoped CI gates
*Completed: 2026-04-11*

### Learnings
- category: testing
  insight: Any UI helper that enables “add slot” or “save to slot” must implement the same eligibility rules as code that builds the PUT payload and as the server (`draft`/`in_use`, already assigned, etc.); otherwise Vitest goes red with no backend bug.
  impact: `canAddEnemySlot` diverged from `nextEnemySlotsAfterAdd` until frontend matched spec R3; rework in modal vs pane integration tests.
  prevention: Single shared predicate (or tests that assert two named helpers agree on a matrix of registry rows) before shipping either path.
  severity: medium
- category: architecture
  insight: Duplicate-slot validation for ordered slot arrays must apply only to non-empty assigned IDs; multiple `""` placeholders are valid and must not be treated as conflicting assignments.
  impact: Wrong duplicate logic rejects legitimate multi-placeholder payloads or blocks “add empty slot” flows.
  prevention: Spec and `validate_manifest` tests explicitly cover multiple `""` with mixed assigned ids; reviewers check duplicate detection scopes to non-empty entries only.
  severity: medium
- category: process
  insight: `ci/scripts/run_tests.sh` can fail in unrelated Godot modules on the same branch while registry/Python/frontend evidence is green; closure then depends on whether AC means full suite vs touched surfaces only.
  impact: 34 failures in shell geometry tests blocked a naive “integration = full CI green” interpretation without documented scope.
  prevention: Gatekeeper records failing modules and paths touched; if policy is “green where touched,” say so in validation and track full-suite repair separately.
  severity: medium
- category: architecture
  insight: Before spec’ing or implementing new HTTP slot APIs, inventory existing service methods (e.g. `put_player_slots` already in Python); gaps may be router exposure only, not new core logic.
  impact: Risk of duplicate endpoints or inconsistent contracts if planning starts at UI without reading `service.py` / existing routes.
  prevention: Spec/plan step: list current `put_*_slots` and router mappings, then require only deltas.
  severity: low

### Anti-Patterns
- description: Separate frontend helpers for “can user proceed?” vs “what will we send?” with different `draft`/`in_use` rules.
  detection_signal: Add-slot enabled while modal or PUT would 400; or Vitest passes one helper and fails integration on the other.
  prevention: One predicate or explicit test: `canAddEnemySlot` ≡ slottable-for-PUT.
- description: Treating repeated `""` in `version_ids` as duplicate slot assignments.
  detection_signal: 400 on payloads with multiple placeholders and one valid id; tests for `["", "", "id"]` missing.
  prevention: Align validation with spec: duplicates only among non-empty slot strings.
- description: Blocking ticket COMPLETE solely because full Godot CI is red when failures are outside changed areas and AC allows scoped green.
  detection_signal: Validation lists only unrelated test modules; no registry/web/python paths in failure output.
  prevention: AC gatekeeper documents out-of-scope failures and optional follow-up ticket for full-suite repair.

### Prompt Patches
- agent: Implementation Frontend
  change: Before completing slot/save UI, ensure `canAddEnemySlot` (and any player analogue) uses the exact same eligibility predicate as `nextEnemySlotsAfterAdd` and server PUT rules for assigned IDs (non-draft, in-use, and any “already in slot” rule); if two functions remain, add a Vitest that asserts they agree on a fixed matrix of version rows.
  reason: Prevents permissive UI vs strict PUT drift that produced reds on this ticket.
- agent: Spec Agent
  change: For slot arrays that allow `""` placeholders, explicitly require that duplicate-slot detection applies only to non-empty assigned `version_id` values, and that all-`""` lists remain structurally valid where the spec allows.
  reason: Prevents implementers from over-applying duplicate-id rules to placeholders.
- agent: Planner / Spec Agent
  change: When the ticket mentions player + enemy slots, grep `asset_generation/python/src/model_registry/service.py` (and router) for existing `put_player_slots` / `put_enemy_slots` before proposing new HTTP surface; specify only missing routes or behavioral gaps.
  reason: Avoids redundant API design when service already supports the operation.
- agent: Acceptance Criteria Gatekeeper
  change: When `run_tests.sh` fails, classify failures by path/module; if none touch the ticket’s declared change surface and AC says full suite green “where touched,” document the unrelated failures in Validation Status and do not treat them as blocking this ticket unless release policy overrides.
  reason: Separates unrelated branch debt from ticket acceptance.

### Workflow Improvements
- issue: Frontend slot work planned without an explicit “predicate parity” checkpoint between gating helpers and PUT builders.
  improvement: Test Designer or Implementation Frontend checklist item: shared slottability helper + one adversarial test for disabled add-slot when promotion is required (radio/`in_use` path).
  expected_benefit: Catches draft/in_use UI radio state bugs before integration.
- issue: Single integration gate conflates scoped regression with repo-wide Godot health.
  improvement: Validation template lists targeted commands (pytest/Vitest paths) plus optional full `run_tests.sh` with explicit in-scope vs out-of-scope failure buckets.
  expected_benefit: Clearer COMPLETE vs follow-up work for unrelated reds.

### Keep / Reinforce
- practice: Execution plan row calling out `canAddEnemySlot` vs `nextEnemySlotsAfterAdd` mismatch as a known risk before implementation.
  reason: Surfacing predicate drift early reduces surprise rework; keep similar “helper A vs helper B” callouts for paired UI/server concepts.

---

## [17_zone_extras_offset_xyz_controls] — Greedy regex in suffix parsers
*Completed: 2026-04-11*

### Learnings
- category: testing
  insight: A `suffixRank` regex of the form `^extra_zone_\w+_(\w+)$` is unsafe when suffixes contain underscores (e.g. `offset_x`): the middle `\w+` can greedily eat part of the suffix, so the captured token no longer matches `SUFFIX_ORDER` entries and tests fall back to rank 99.
  impact: Vitest AC-7.3 failed until the zone segment was pinned to the known zone alternation (matching `EXTRA_ZONE_PREFIX_RE`).
  prevention: For `extra_zone_<zone>_<suffix>` keys, parse zone with a fixed alternation (or split on the first two delimiters) instead of a single greedy `\w+` bridge.
  severity: medium

---

## [16_random_vs_uniform_distribution_eyes_and_extras] — Stub Vector iteration + diff-cover
*Completed: 2026-04-09*

### Learnings
- category: testing
  insight: `AnimatedSpider.build_mesh_parts` uses `tuple(body_center)` on a `mathutils.Vector`; the headless stub `Vector` lacked `__iter__`, so an integration-style spider build test could not run until the stub matched iterable Blender behavior.
  impact: Local spider build smoke and diff-cover for the random eye branch were blocked without stub parity or heavy patching.
  prevention: When procedural builders use `tuple(vector)` or unpacking, ensure `blender_stubs._Vector` supports iteration (or document that all such tests must patch constructors).
  severity: medium
- category: ci
  insight: `ci/scripts/run_tests.sh` enforces diff-cover vs `origin/main` at 85%; new branches in `zone_geometry_extras_attach` need several small procedural tests (uniform ring, head random spikes/bulbs) to stay above the gate.
  impact: CI failed at 75% until placement/attach tests were expanded.
  prevention: After large branching changes in attach modules, add one test per major branch (uniform ring, random loop) early.
  severity: low

---

## [M9-EPEC / 15_eye_extras_clustering] — Stub Vector parity
*Completed: 2026-04-10*

### Learnings
- category: testing
  insight: `zone_geometry_extras_attach._facing_allows_normal` uses `Vector.dot` and `bc.x` style access; the mathutils stub lacked `dot` and `x`/`y`/`z`, so unrelated facing tests failed once attach code exercised those paths consistently.
  impact: CI red on `test_zone_geometry_extras_facing` and slug/spider attach tests until stub matches minimal Blender `mathutils.Vector` surface.
  prevention: When adding geometry code that uses `dot` or axis properties, extend `blender_stubs._Vector` in the same change.
  severity: medium

---

## [14_preview_collapse] — jsdom and scrollIntoView
*Completed: 2026-04-09*

### Learnings
- category: testing
  insight: `Terminal`’s auto-scroll called `scrollIntoView` unconditionally; jsdom’s `Element` stub lacks it, breaking any RTL mount of the real `Terminal`.
  impact: New layout tests that render `Terminal` failed until guarded with `typeof el.scrollIntoView === "function"`.
  prevention: Guard DOM APIs that are browser-only when components are tested under jsdom.
  severity: low

---

## [13_registry_paths] — Draft subtree + patch-time relocate
*Completed: 2026-04-09*

### Learnings
- category: architecture
  insight: Keep a single module (`path_layout`) for managed `*/draft/*.glb` rules and sidecar suffixes so registry patch and future tooling stay aligned.
  impact: Relocate must move `.attacks.json`, `.player.json`, `.object.json` with the GLB or downstream paths break.
  prevention: Extend `_sidecar_names` when new companion formats appear.
  severity: medium

- category: product
  insight: Editor export target follows the preview URL (`/draft/` segment) and run-stream `output_draft`; CLI default stays live-root for backward compatibility.
  impact: Users load a draft preview to regenerate into `draft/` unless a future explicit toggle is added.
  prevention: Spec + milestone README document the layout.
  severity: low

---

## [M9-EBUI] — Center panel enum + synthetic control merge for new tab
*Completed: 2026-04-09*

### Learnings
- category: architecture
  insight: New build-option families should be stripped from the Build tab explicitly (`feat_*` and `extra_zone_*`) so each center tab owns one concern.
  impact: Without filtering, `extra_zone_*` floats appeared alongside mesh sliders after ticket 11.
  prevention: When adding meta-driven rows, decide primary surface in layout and filter `BuildControls` defs accordingly.
  severity: medium

- category: testing
  insight: `diff-cover` against `origin/main` aggregates all commits ahead plus unstaged lines; partial Python coverage from a prior commit can block a frontend-only ticket until attach tests catch up.
  impact: Required expanding `test_slug_zone_extras_attach` and fixing a broken import order in `zone_geometry_extras_attach.py` surfaced during the same run.
  prevention: Keep attach/helper modules syntactically linted and maintain coverage when adding generator paths.
  severity: medium

### Anti-Patterns
- description: Relying on API-only `extra_zone_*` defs with empty `animated_build_controls` fallback (offline editor).
  detection_signal: Extras tab empty hint with no rows for slug despite ticket 11 backend contract.
  prevention: Mirror Python defaults via `syntheticExtraZoneDefsForSlug` in `mergeCanonicalZoneControls`, same as coarse `feat_*` zones.

---

## [M9-EBPE] — Zone extras: stub mathutils vs Blender and diff-cover on new modules
*Completed: 2026-04-09*

### Learnings
- category: testing
  insight: Geometry attach code that runs under pytest uses `mathutils` stubs without `.normalize()`, `.x`, or `Quaternion.to_euler()`; normalize with scalar math and guard optional Blender APIs.
  impact: First attach tests failed until Vector/rotation paths were stub-safe.
  prevention: For Blender-adjacent modules imported in CI pytest, prefer scalar fallbacks or `getattr` guards for mathutils-only methods.
  severity: medium

- category: process
  insight: `diff-cover` against `origin/main` required narrow unit tests for `create_cone`, `material_for_zone_geometry_extra`, merge branches, and `apply_themed_materials` hook coverage.
  impact: Full suite green was insufficient until diff-cover thresholds met on changed lines.
  prevention: After adding new Python surface area, plan companion tests alongside implementation to satisfy org diff-cover gates early.
  severity: medium

### Anti-Patterns
- description: Assuming nested slug JSON envelope includes root-level flat keys in the same `src` dict used for merges.
  detection_signal: Tests expect root `extra_zone_*` to override nested `zone_geometry_extras` but `options_for_enemy` only forwarded nested `src`.
  prevention: Document and implement explicit second-pass merge from raw root for flat `extra_zone_*` keys when a nested slug object is present.

---

## [M9-RSEVV] — Freeze selector contract and spawn seam boundaries before test authoring
*Completed: 2026-04-09*

### Learnings
- category: process
  insight: Runtime randomness features need policy freeze (uniform vs weighted) in planning/spec before test design.
  impact: Medium-confidence assumptions were required to proceed, which increases contract drift risk even when implementation succeeds.
  prevention: Add a specification gate requiring explicit selection policy, weighting scope, and fallback behavior before TEST_DESIGN.
  severity: medium

- category: architecture
  insight: Cross-flow runtime features should define one authoritative integration seam and ownership boundary up front.
  impact: Sandbox/procedural choke-point ownership had to be assumption-driven during planning, creating avoidable integration uncertainty.
  prevention: Require planner output to name the single choke point (or state deferred boundary) and record whether wiring is in-scope now vs future milestone handoff.
  severity: medium

- category: testing
  insight: Deterministic RNG injection is a required contract surface for non-flaky behavioral validation of random selectors.
  impact: Deterministic evidence quality depended on introducing an injectable RNG seam rather than relying on global randomness.
  prevention: Treat deterministic hook design as mandatory in spec for any runtime behavior that includes randomness and must satisfy acceptance criteria.
  severity: high

- category: architecture
  insight: Fail-closed semantics for malformed eligibility metadata must be explicit and non-coercive in runtime selectors.
  impact: Adversarial tests had to lock rejection behavior for missing/non-boolean `draft` and `in_use` fields to prevent ineligible leakage.
  prevention: Standardize metadata-validation rules: malformed eligibility fields are invalid candidates, never coerced to truthy/falsy defaults.
  severity: high

### Anti-Patterns
- description: Letting random-selection policy remain ambiguous until downstream stages.
  detection_signal: Planning/spec checkpoints contain "would have asked" about uniform vs weighted semantics.
  prevention: Block test design until selection policy and optional-weighting conditions are explicitly documented.

- description: Defining selector APIs in tests before canonical seam naming is frozen.
  detection_signal: Test-design assumptions include file/function naming decisions that were not specified earlier.
  prevention: Require spec to publish canonical selector module/function contract and integration callers before test authoring.

- description: Coercing malformed eligibility metadata instead of rejecting it.
  detection_signal: Tests accept or rely on truthy/falsy interpretation of missing or non-boolean eligibility fields.
  prevention: Enforce fail-closed malformed-metadata rejection in both spec language and adversarial baseline tests.

### Prompt Patches
- agent: Planner Agent
  change: "For randomness-driven runtime tickets, include a `Selection Policy Freeze` block that explicitly states default policy (uniform/weighted), weighting scope (in/out), deterministic test hook requirement, and fail-closed fallback rules before handoff to Spec."
  reason: Removes medium-confidence policy assumptions that otherwise propagate into test and implementation stages.

- agent: Spec Agent
  change: "Before handing off to Test Design, declare the canonical selector seam contract (module path, function name/signature, and authoritative integration caller[s]) and mark any deferred cross-milestone wiring boundaries explicitly."
  reason: Prevents test-side API naming assumptions and reduces integration ambiguity across spawn flows.

- agent: Test Breaker Agent
  change: "For selector eligibility logic, always include adversarial cases for missing/non-boolean status fields and assert strict fail-closed rejection with no ineligible fallback selection."
  reason: Catches metadata-coercion bugs that can silently leak draft or out-of-policy variants.

### Workflow Improvements
- issue: Stage transitions allowed unresolved policy and seam-contract ambiguity into TEST_DESIGN.
  improvement: Add a pre-test-design readiness checklist for randomness features: policy freeze, deterministic hook contract, canonical seam naming, and malformed-metadata behavior.
  expected_benefit: Fewer assumption-driven decisions and more stable cross-stage contracts.

- issue: Cross-milestone integration boundaries were handled by assumption instead of standardized declaration.
  improvement: Add a required "Deferred Boundary Statement" field in planner/spec outputs when current ticket depends on future wiring.
  expected_benefit: Cleaner scope control and lower risk of duplicate or diverging integration logic.

### Keep / Reinforce
- practice: Scoped checkpoint capture of `Would have asked` / `Assumption made` / `Confidence`.
  reason: It exposes uncertainty early and produces actionable prompt/workflow improvements post-closure.

- practice: AC evidence mapping to specific primary and adversarial tests plus full-suite rerun.
  reason: It keeps closure decisions test-grounded even when design choices were assumption-constrained earlier.

---

## [M9-ATRAD] — Cross-cutting contract tests exposed confirmation and status-taxonomy drift risks
*Completed: 2026-04-09*

### Learnings
- category: testing
  insight: Cross-cutting regression suites should intentionally include both “blocked safety” and “allowed success” invariant paths for destructive operations.
  impact: Requiring both blocked and allowed delete scenarios prevented one-sided coverage that would miss either over-permissive or over-restrictive regressions.
  prevention: Treat destructive-operation contracts as two-sided by default: one deterministic guardrail rejection and one deterministic success with post-state assertions.
  severity: high

- category: architecture
  insight: Confirmation inputs in destructive APIs need explicit semantics for “present but blank” values instead of relying on implicit truthiness behavior.
  impact: Adversarial tests surfaced a backend contract gap around blank `confirm_text`, forcing explicit rejection behavior to avoid intent-check bypass ambiguity.
  prevention: Add explicit request-schema rules that distinguish omitted confirmation fields from whitespace-only confirmation payloads and bind each to deterministic status outcomes.
  severity: high

- category: process
  insight: Status-code taxonomy for security/path validation should be fixed at spec stage, not inferred during test authoring.
  impact: Medium-confidence assumptions were needed to pin exact `400` vs `403` outcomes for traversal vs allowlist-prefix violations.
  prevention: Require a “failure taxonomy” table in specs for path-security endpoints before test design begins.
  severity: medium

### Anti-Patterns
- description: Testing only one side of delete invariants (only blocked or only allowed) and calling contract coverage complete.
  detection_signal: Delete test suites lack either a successful post-delete invariant assertion or a blocked-state no-mutation assertion.
  prevention: Enforce a two-scenario minimum for delete invariants in primary test design checklists.

- description: Leaving blank-but-explicit confirmation payload behavior unspecified for destructive endpoints.
  detection_signal: Checkpoints or tests debate whether whitespace confirmation should pass or fail.
  prevention: Define confirmation-field normalization and reject-class behavior explicitly in the API contract.

### Prompt Patches
- agent: Spec Agent
  change: "For any destructive endpoint with confirmation semantics, include a `Confirmation Input Contract` section that explicitly defines outcomes for omitted, empty-string, and whitespace-only confirmation values with exact status classes."
  reason: Prevents late discovery of ambiguity that can weaken safety guarantees.

- agent: Test Breaker Agent
  change: "Always add adversarial tests for destructive endpoints that cover blank/whitespace confirmation payloads and assert deterministic rejection plus no state mutation."
  reason: Catches intent-check bypass gaps that primary happy-path tests often miss.

- agent: Test Designer Agent
  change: "For path-security contracts, include one explicit assertion per rejection class (`400` normalization failure vs `403` allowlist violation) rather than broad class assertions, when the router contract is deterministic."
  reason: Locks status taxonomy so security regressions are caught early and unambiguously.

### Workflow Improvements
- issue: Critical status semantics and destructive-confirmation edge cases were finalized through assumptions during test stages.
  improvement: Add a spec exit gate requiring explicit failure-taxonomy and confirmation-input tables before test design.
  expected_benefit: Fewer medium-confidence assumptions and less implementation churn from late contract clarification.

- issue: Cross-cutting tickets can unintentionally under-cover destructive invariants when they focus mainly on rejection vectors.
  improvement: Add a mandatory “safety pair” checklist item in planning/spec for all delete/update invariants: blocked case + allowed case + post-read verification.
  expected_benefit: Better regression resistance against both permissive and restrictive drift.

### Keep / Reinforce
- practice: Backend-first contract testing for security-critical allowlist/traversal behavior.
  reason: It validates enforcement at the authoritative layer and avoids false confidence from UI-only coverage.

- practice: Scoped checkpoint logging of `Would have asked` / `Assumption made` / `Confidence`.
  reason: It made autonomy decisions auditable and enabled high-signal post-ticket learning extraction.

---
## [M9-DDIM] — Freeze destructive API contract details before test design to avoid medium-confidence assumption drift
*Completed: 2026-04-09*

### Learnings
- category: process
  insight: Destructive-operation tickets need endpoint shape and payload contract freeze in spec, not test design.
  impact: Test design had to proceed on medium-confidence assumptions about DELETE endpoint paths and request envelope semantics, increasing avoidable contract risk.
  prevention: Add a spec exit gate for destructive APIs requiring explicit URI(s), method(s), required fields, and deterministic status-class mapping before test authoring begins.
  severity: medium

- category: architecture
  insight: Confirmation booleans alone are insufficient for high-risk deletes; confirmation must be bound to target identity.
  impact: Adversarial coverage had to assert that mismatched `confirm_text` versus request target hard-fails with no mutation to prevent intent spoofing.
  prevention: Standardize an "intent-binding" rule for destructive endpoints: explicit confirmation plus target-identity match must be validated server-side.
  severity: high

- category: testing
  insight: Repeat-delete and malformed-confirmation paths should be first-class deterministic contract tests for delete endpoints.
  impact: Test-break added these adversarial cases late, revealing they are core safety behavior rather than optional edge coverage.
  prevention: Require a baseline adversarial set for every destructive endpoint: stale-target repeat, encoded traversal, malformed confirmation, and no-side-effect assertions.
  severity: medium

### Anti-Patterns
- description: Letting endpoint naming and payload strictness remain ambiguous until test design.
  detection_signal: Test-design checkpoints include "would have asked" items about route shape or required confirmation fields.
  prevention: Block transition to TEST_DESIGN until destructive API contract fields are explicit in the spec.

- description: Treating operator confirmation as a generic boolean without validating target identity binding.
  detection_signal: Requests with `confirm=true` but mismatched target text are not explicitly rejected in tests/spec.
  prevention: Make target-bound confirmation validation mandatory and assert hard-failure/no-mutation behavior in backend tests.

### Prompt Patches
- agent: Spec Agent
  change: "For every destructive endpoint, include a `Destructive Contract Freeze` subsection with exact method+URI, required confirmation fields, and deterministic status-class outcomes before handing off to Test Design."
  reason: Eliminates medium-confidence test-authoring assumptions that create downstream contract drift.

- agent: Test Designer Agent
  change: "For each destructive API, include mandatory tests for (1) stale-target repeat delete determinism and (2) confirmation payload rejection when confirmation text does not match the requested target identity."
  reason: Locks the two highest-risk safety behaviors early instead of relying on late adversarial discovery.

- agent: Test Breaker Agent
  change: "Always attempt intent-spoofing payloads on destructive routes (confirm true + mismatched target identity) and require explicit no-mutation assertions after rejection."
  reason: Catches confirmation-bypass classes before implementation is accepted.

### Workflow Improvements
- issue: Spec-to-test handoff allowed unresolved destructive API contract details.
  improvement: Add a handoff checklist item that fails SPECIFICATION completion if destructive route method/URI/payload/status taxonomy are not fully explicit.
  expected_benefit: Reduces medium-confidence assumptions and rework pressure in TEST_DESIGN/TEST_BREAK.

- issue: Safety-critical adversarial cases were discovered in TEST_BREAK rather than codified as baseline delete contract tests.
  improvement: Promote a shared destructive-endpoint adversarial template into TEST_DESIGN stage requirements.
  expected_benefit: Earlier detection of destructive-flow weaknesses with fewer late-stage adjustments.

### Keep / Reinforce
- practice: Recording `Would have asked` / `Assumption made` / `Confidence` for each ambiguity in scoped checkpoints.
  reason: Makes assumption risk auditable and directly translatable into prompt and workflow improvements.

- practice: Treating dependency spec as authoritative when ticket text can be interpreted multiple ways.
  reason: Prevents local tickets from silently diverging from milestone-level safety policy.

---

## [M9-EUDS] — Model registry draft / in-use UI + API

*Completed: 2026-04-08*

### Learnings

- category: architecture
  insight: When `settings.python_root` is monkeypatched to a tmp dir for manifest I/O tests, pipeline imports (`utils`, `model_registry`) must still resolve from the real checkout. A small `_canonical_python_roots()` helper (derived from `routers/registry.py` location) avoids coupling imports to the writable root.
  impact: ASGI tests can isolate `model_registry.json` without stubbing `src`.
  prevention: Any future router that imports from `asset_generation/python` should use the same split: canonical import path vs configurable data root.
  severity: medium

- category: dependencies
  insight: HTTP contract tests for the web backend fit naturally under `asset_generation/python/tests/web/` with optional `dev` extras (FastAPI, httpx, sse-starlette) so `pytest tests/` stays the single CI gate; local `.venv` arch mismatches (x86_64 vs arm64 wheels) require a clean `uv sync` on the host arch.
  impact: Developers hitting `ImportError` on `pydantic_core` should recreate the venv rather than dropping integration tests.
  severity: low

### Anti-Patterns

- description: Using `settings.python_root` alone on `sys.path` for registry code when tests patch it to an empty tree — breaks `from utils...` imports.
  detection_signal: `503` from `/api/registry/*` with `ModuleNotFoundError: utils` in logs.
  prevention: Canonical import roots vs I/O root (as implemented in `registry.py`).

---

## [M9-PMCP] — Procedural material pipeline + diff-cover on template module

*Completed: 2026-04-08*

### Learnings

- category: testing
  insight: Procedural shader helpers that only run inside Blender are still testable with thin fake `nodes`/`links` fakes; assert **absence** of socket links (e.g. no noise → Roughness) to lock PBR export contracts.
  impact: `test_material_system_principled_pipeline.py` guards PMCP-1/2 without a real Blender binary.
  prevention: When adding texture handlers, extend the fake-graph tests alongside `create_material` integration checks.
  severity: medium

- category: ci
  insight: diff-cover aggregates **all** lines in `git diff` vs compare branch; a one-line `from __future__` in a reference module can sink the 85% gate if nothing imports that module in tests.
  impact: Added `test_example_new_enemy_module_importable` to cover the template import path.
  prevention: For doc/template `.py` files in `src/`, either exclude from coverage diff scope or add a one-shot import test when the file appears in PR diffs.
  severity: low

### Anti-Patterns

- description: Driving Principled **Roughness** from raw noise `Fac` (0–1) while also setting a numeric roughness preset — the link wins, washing out intended PBR.
  detection_signal: Exported GLB looks uniformly rough or ignores `ENEMY_FINISH_PRESETS` / per-type defaults.
  prevention: Remove or remix roughness links; use `_force_principled_value` after handlers when finish overrides apply.

---

## [M9-BPCLJH] — Body-part color hierarchy + diff-cover on mesh apply paths

*Completed: 2026-04-08*

### Learnings

- category: testing
  insight: New Blender-facing `apply_themed_materials` branches rarely execute in pytest without bpy; diff-cover on those files requires lightweight instance `__new__` tests with `_mesh` / `_mesh_str` stubs plus `material_for_zone_part` mocked.
  impact: Added `test_*_feature_materials_apply.py` suites to satisfy 85% diff-cover alongside pure `material_system` unit tests.
  prevention: When extending procedural material assignment, add a mocked apply-loop test in the same PR as the mesh code.
  severity: medium

- category: frontend
  insight: Python API uses `type: "str"` for freeform fields; TS components that check `=== "string"` silently degrade controls to numeric inputs — always align control-renderer discriminated unions with the backend schema.
  impact: Hex/finish rows were broken until `str` handling and `AnimatedBuildControlDef` union were fixed; `BuildControls` now reuses `BuildControlRow`.
  prevention: Add a meta-router or snapshot test that asserts at least one `str` / `select_str` control round-trips through the client type guard.
  severity: high

### Anti-Patterns

- description: Duplicating `ControlRow` in `BuildControls.tsx` with a narrower type union than the shared component, causing runtime mis-rendering that TypeScript only catches after widening the union.
  detection_signal: New API control types render as number inputs in the build panel but correctly in other panes.
  prevention: Single `ControlRow` implementation for all panels; extend the union once when Python adds control `type` values.

---

## [sse_run_endpoint_and_terminal] — Malformed ticket bootstrap and endpoint-evidence closure boundary

*Completed: 2026-04-07*

### Learnings

- category: process
  insight: Tickets missing a valid `WORKFLOW STATE` should be treated as malformed workflow artifacts and routed through a documented bootstrap/closure path rather than forcing a full re-run by default.
  impact: This ticket resumed from a backlog stub with no state block; the run required planner escalation assumptions before closure could proceed.
  prevention: Add a standard malformed-ticket branch: classify as bootstrap candidate, require explicit evidence checklist, then write canonical state blocks before moving to `done/`.
  severity: medium

- category: testing
  insight: For long-running external-process features (SSE + subprocess manager), autonomous closure can rely on deterministic endpoint/runtime probes plus code-path mapping when interactive tool execution is inherently environment-dependent.
  impact: Closure used `/status`, `/kill` idle behavior, and allowlist error-stream checks, while Blender interactive generation remained an optional manual verification step.
  prevention: Define a two-tier validation rule in spec/tests: tier 1 deterministic API-stream probes required for closure; tier 2 interactive process run explicitly marked manual/optional unless CI harness exists.
  severity: medium

- category: architecture
  insight: Command allowlists for process-launch endpoints are a security contract, not an implementation detail, and should be validated at stream-protocol level (SSE `error` event) instead of only status codes.
  impact: Runtime evidence confirmed `/api/run/stream?cmd=evil` emitted protocol-correct SSE `error`, proving both input hardening and frontend-consumable failure semantics.
  prevention: Require one negative-path streaming test per run-capable endpoint that asserts event type and error message shape, not just HTTP acceptance.
  severity: high

### Anti-Patterns

- description: Treating malformed backlog tickets as normal in-progress work without explicit bootstrap semantics, causing ambiguous stage ownership and ad-hoc assumptions.
  detection_signal: Ticket lacks `WORKFLOW STATE` but pipeline resumes directly at arbitrary stages.
  prevention: Enforce a gatekeeper/planner bootstrap step that writes normalized state metadata before any closure decision.

- description: Declaring streaming process features complete from code inspection alone when no runtime protocol evidence exists.
  detection_signal: AC claims for SSE output, kill behavior, or error handling without captured endpoint probe results.
  prevention: Require minimal runtime probe set (`status`, `kill`, invalid-cmd stream) in every closure log for subprocess-backed SSE endpoints.

### Prompt Patches

- agent: Planner Agent
  change: "If a ticket is missing `WORKFLOW STATE`, mark it `MALFORMED_BOOTSTRAP` and produce a bootstrap mini-plan: (1) verify implementation presence, (2) collect deterministic runtime evidence, (3) write normalized WORKFLOW STATE/NEXT ACTION, then hand off to Gatekeeper for closure."
  reason: Removes stage ambiguity and makes malformed-ticket handling consistent.

- agent: Acceptance Criteria Gatekeeper Agent
  change: "For subprocess-backed SSE ACs, require evidence of three probes before COMPLETE: `GET /status`, `POST /kill` in idle or active-safe state, and invalid-command stream asserting SSE `error` event payload; if live external tool execution is unavailable, record it explicitly as manual optional validation."
  reason: Ensures closure is evidence-driven without blocking on nondeterministic external tooling.

- agent: Spec Agent
  change: "When an AC depends on external interactive tools (e.g., Blender run output), split acceptance into deterministic API/protocol checks vs manual interactive checks, and label which tier is mandatory for autonomous closure."
  reason: Prevents mid-pipeline uncertainty about what evidence is sufficient.

### Workflow Improvements

- issue: Current workflow does not define a first-class path for malformed ticket files with missing state metadata.
  improvement: Add a formal `BOOTSTRAP_MALFORMED_TICKET` transition in workflow docs and checkpoint templates with required evidence fields.
  expected_benefit: Faster, lower-ambiguity recoveries when historical ticket files are incomplete.

- issue: SSE endpoint tickets can blur protocol verification and interactive external-process validation.
  improvement: Add a reusable closure checklist template for streaming endpoints that separates protocol-contract checks from environment-dependent manual checks.
  expected_benefit: Consistent closure quality and fewer medium-confidence assumptions.

### Keep / Reinforce

- practice: Combining runtime probes with AC code-path mapping for closure on already-implemented tickets.
  reason: Balances execution speed with defensible evidence when reimplementation is unnecessary.

- practice: Explicitly logging optional manual verification steps instead of silently treating them as completed.
  reason: Preserves audit clarity and prevents overstating validation coverage.

---

## [frontend_react_scaffold_and_editor] — Bootstrap-closure tickets need explicit metadata and evidence tiers

*Completed: 2026-04-07*

### Learnings

- category: process
  insight: Tickets missing a valid WORKFLOW STATE force late-stage routing assumptions and add avoidable planner/gatekeeper churn even when implementation already exists.
  impact: This ticket required bootstrap handling from a malformed backlog stub before closure logic could proceed.
  prevention: Add a pre-routing metadata validation gate that blocks advancement until required workflow fields are present.
  severity: medium

- category: testing
  insight: Proxy/CORS acceptance criteria require a declared evidence tier; config plus dev-server startup proves setup, but not end-to-end browser behavior against a live backend.
  impact: Autonomous closure used code-path and runtime startup evidence, but still needed manual follow-up for live no-CORS confirmation.
  prevention: Encode ACs with explicit proof mode labels (config/static, runtime command, browser-live) during spec so gatekeepers do not infer sufficiency ad hoc.
  severity: medium

- category: process
  insight: "Scaffold already implemented" tickets are best treated as verification-and-closure work items rather than implementation work, with a deterministic closure checklist.
  impact: The run succeeded by switching to install/build/dev verification and AC mapping, not by coding.
  prevention: Introduce a standard "existing implementation closure" path that requires dependency install, build, bounded dev startup, and AC-to-evidence mapping before `done`.
  severity: low

### Anti-Patterns

- description: Advancing malformed ticket stubs through normal stage transitions without first validating required workflow metadata.
  detection_signal: Missing WORKFLOW STATE block, absent stage/revision fields, or ambiguous "next agent" handoff at resume time.
  prevention: Fail fast on ticket schema validation and require a metadata repair step before planner routing.

- description: Treating infrastructural ACs (like CORS/proxy) as fully proven by static config alone.
  detection_signal: AC marked complete without evidence of requests exercised in a browser against a running backend.
  prevention: Split AC evidence into setup proof vs live-behavior proof and require both when AC wording is behavioral.

### Prompt Patches

- agent: Planner Agent
  change: "Before decomposing a ticket, validate that the ticket contains a WORKFLOW STATE block with stage, revision, next responsible agent, and status. If missing, emit a 'metadata repair required' checkpoint and do not continue normal stage routing."
  reason: Prevents malformed-ticket churn and ambiguous resume behavior.

- agent: Acceptance Criteria Gatekeeper Agent
  change: "For ACs about CORS/proxy/network behavior, explicitly classify evidence as (A) config/static, (B) runtime service startup, and (C) live browser request behavior. Mark the AC complete only when required tiers are satisfied by the AC wording; otherwise leave a precise manual follow-up."
  reason: Removes evidence ambiguity and reduces false-complete decisions on network-facing criteria.

- agent: Spec Agent
  change: "When drafting frontend ACs with infrastructure semantics, annotate each AC with required verification mode (`static`, `runtime`, `browser-live`) so downstream test design and gatekeeping apply the same evidence bar."
  reason: Aligns proof expectations across pipeline stages.

### Workflow Improvements

- issue: Workflow currently allows malformed ticket stubs to reach resume/gatekeeper paths where assumptions are made late.
  improvement: Add an explicit preflight stage (ticket-schema validation) before PLANNING for dequeued backlog items.
  expected_benefit: Cleaner routing, fewer assumption checkpoints, and faster closure for pre-implemented work.

- issue: AC validation does not consistently distinguish "implemented correctly" from "observed working in environment."
  improvement: Add AC evidence-tier tags to ticket/spec templates and require gatekeeper reporting by tier.
  expected_benefit: Higher confidence in closure decisions and fewer post-close manual surprises.

### Keep / Reinforce

- practice: Bounded runtime commands (`npm run build`, timed `npm run dev`) were used before closure.
  reason: Provides fast, reproducible baseline confidence without waiting for full manual UX pass.

- practice: ACs were mapped to concrete code paths and explicit runtime evidence.
  reason: Improves auditability of why a ticket was closed when implementation predated the run.

## [M19-ARGLB] — Path-jail hardening and clip-state ownership must be explicitly tested

*Completed: 2026-04-07*

### Learnings

- category: testing
  insight: HTTP client normalization can hide traversal payloads before the app handler runs, so security assertions tied to literal `..` URLs are not reliable as primary evidence.
  impact: Literal traversal tests produced route-level misses while encoded traversal cases exposed the real guard behavior; this created rework in test intent and interpretation.
  prevention: Treat encoded traversal vectors as the canonical app-layer security tests, and keep literal-dot requests as transport-behavior documentation only.
  severity: high

- category: architecture
  insight: Path-jail guards must wrap both path resolution and file-type checks, not only ancestry checks, because error modes occur before or after `relative_to` in real payloads.
  impact: Null-byte and directory-path inputs triggered unhandled exceptions until `resolve()` guarding and explicit `is_file()` handling were added.
  prevention: Standardize secure file-serving guard order as: resolve safely -> enforce jail ancestry -> enforce allowed top-level directory -> enforce `is_file()` -> serve.
  severity: high

- category: process
  insight: Pre-scaffolded tickets still need full spec-and-test passes because "mostly implemented" code hides contractual drift and state-model mistakes.
  impact: A functional UI path still had incorrect clip-state ownership (`setAvailableClips` behavior conflated with active animation), discovered only during gap analysis.
  prevention: For scaffold-first tickets, require a mandatory gap table that validates state ownership, not just acceptance-criteria surface behavior.
  severity: medium

### Anti-Patterns

- description: Using literal `..` requests as the sole traversal proof in ASGI/httpx tests.
  detection_signal: Traversal tests fail with route misses/non-200 while encoded-path tests exercise handler logic and produce different status semantics.
  prevention: Pair every traversal test set with encoded equivalents and label which layer (client normalization vs app guard) each test validates.

- description: Collapsing "available options" and "selected option" into one UI store field.
  detection_signal: New model loads force a default selection regardless of actual loaded data, or controls render fallback options despite real runtime data existing.
  prevention: Keep separate store slices/actions for inventory/exposure (`availableClips`) versus selection (`activeAnimation`) and test both transitions.

### Prompt Patches

- agent: Test Designer Agent
  change: "For path traversal/security routes tested through httpx/ASGITransport, include both literal-dot and percent-encoded traversal cases, and annotate each test with the validation layer it targets (transport normalization vs app guard)."
  reason: Prevents false confidence from client-side URL normalization.

- agent: Implementation Agent
  change: "When implementing file-serving path jails, guard `resolve()` exceptions and enforce `is_file()` before `FileResponse`; do not rely solely on `relative_to` ancestry checks."
  reason: Captures common real-world failure paths that bypass naive jail logic.

- agent: Planner Agent
  change: "If a ticket starts from pre-existing scaffold code, add an explicit 'state ownership and data-flow gap audit' task before implementation, even when ACs appear mostly covered."
  reason: Reduces late-cycle discovery of architectural miswiring hidden by superficially working behavior.

### Workflow Improvements

- issue: Security tests initially mixed transport-normalization behavior and app-guard behavior under one expectation.
  improvement: Add a workflow convention that security-related test IDs must declare the layer under test in test comments and AC mapping notes.
  expected_benefit: Faster debugging and fewer red/green misreads during Test Design and Test Breaker stages.

- issue: "Preferred" vs "required" status-code semantics for directory-path handling created inconsistent assertions until implementation tightened behavior.
  improvement: During spec stage, convert ambiguous status-code language into mandatory or optional clauses with explicit test strategy (strict vs permissive assertions).
  expected_benefit: Fewer assertion rewrites and cleaner handoff from spec to test suites.

### Keep / Reinforce

- practice: Adversarial expansion beyond happy-path ACs (null-byte, double-encoded traversal, case-variant extensions, stress list cardinality).
  reason: Exposed implementation gaps quickly and produced durable regression coverage.

- practice: AC gatekeeping that ties each acceptance criterion to concrete test evidence or explicit manual-verification notes.
  reason: Enables honest completion decisions without claiming unproven browser behavior.

---

## [carapace_enemy_attack] — Telegraph floor extended via optional parameter

*Completed: 2026-04-06*

### Learnings

- category: gameplay
  insight: `ATS2_MIN_TELEGRAPH` (0.3s) is a global floor for all ranged telegraphs; families that need a longer wind-up (carapace 0.6s) should pass `min_hold_seconds` into `begin_ranged_attack_telegraph` so the controller stores `_telegraph_min_hold_sec = max(ATS2_MIN_TELEGRAPH, requested)` without duplicating timer logic in each attack script.
  impact: Acid/adhesion default call sites unchanged; carapace meets AC without a second post-signal timer.
  prevention: When adding a third telegraphed attack with a custom minimum hold, use the same parameter rather than stacking SceneTreeTimers on the attack node.
  severity: low

- category: engine_integration
  insight: The adhesion `enemy_writes_velocity_x_this_frame` gate on `EnemyInfection3D` composes additively: a second attack family (carapace) needs the same check so horizontal velocity from charge/decel is not cleared before `move_and_slide()`.
  impact: Any future dash attack must register in this gate or extract a single helper that ORs child overrides.
  severity: low

---

## [hitbox_and_damage_system] — Tests cannot reference `class_name` before global registration

*Completed: 2026-04-06*

### Learnings

- category: testing
  insight: Godot test scripts loaded by `run_tests.gd` may parse before global `class_name` symbols from other scripts are visible, producing "Could not find type X in the current scope" even when the implementation script exists.
  impact: Primary hitbox tests failed to load until `EnemyAttackHitbox` references were replaced with `preload("res://scripts/enemies/enemy_attack_hitbox.gd").new()` and `Area3D`-typed locals.
  prevention: For new `class_name` types consumed only from tests, prefer `preload` + `.new()` or defer typed hints until the type is guaranteed registered.
  severity: medium

---

## [adhesion_enemy_attack] — Enemy body must cooperate with child-driven lunge velocity

*Completed: 2026-04-07*

### Learnings

- category: engine_integration
  insight: `EnemyInfection3D._physics_process` unconditionally zeroed `velocity.x` every frame, so any child attack script could not move the enemy horizontally without changing the base class. A narrow gate (`enemy_writes_velocity_x_this_frame` on `AdhesionBugLungeAttack` + lower `process_physics_priority`) lets the child set `velocity.x` before `move_and_slide()` without forking the enemy scene per attack type.
  impact: Lunge works with existing generated enemy scenes; acid spitter unchanged.
  prevention: Future melee dashes should reuse the same pattern or extract a small “locomotion override” API on the enemy body.
  severity: medium

- category: gameplay
  insight: Player “root” is implemented as zero horizontal input, blocked jump press for the window, and `velocity.x = 0` after `simulate` and after `move_and_slide`, with a monotonic timer decremented at end of `_physics_process` so the full frame is rooted.
  impact: Avoids friction-only drift and avoids consuming the root timer before movement logic runs.
  prevention: If wall-cling or knockback is added, re-validate that rooted frames cannot gain horizontal speed from non-input sources.
  severity: low

---

## [acid_enemy_attack] — DoT tick count vs time_left; integrate acid attack after GLB animation wiring

*Completed: 2026-04-06*

### Learnings

- category: gameplay
  insight: Modeling enemy acid DoT as `time_left` plus `accum` with a `while` loop risks an off-by-one on the final tick (sixth 0.5s tick in a 3s window) and, with pathological `delta`/`interval` values, an unbounded inner loop. A `ticks_remaining` budget derived from `round(duration / interval)` is deterministic and matches the AC wording.
  impact: AEAA-02 initially failed until the tick-count model replaced time-window gating on the last tick.
  prevention: For interval-based effects over a fixed duration, prefer explicit tick budgets or integration tests that assert total tick count, not only total damage.
  severity: medium

- category: engine_integration
  insight: Spawning the acid attack controller in `EnemyInfection3D._ready()` runs before GLB libraries are merged onto the root `AnimationPlayer`, so `Attack` may be missing and telegraph falls back to a timer. Deferring attachment to `_wire_and_notify_animation()` ensures `begin_ranged_attack_telegraph()` can use the real clip when present.
  impact: Reliable telegraph in generated acid spitter scenes; gobot placeholder still uses fallback if `Attack` is absent.
  prevention: Any feature that depends on post-import animation libraries should wire after the same deferred path that copies libraries to the root player.
  severity: medium

---

## [death_animation_playthrough] — Completion-gated despawn must handle missing clips; `_ready`/`get_tree` guards for testable handlers

*Completed: 2026-04-04*

### Learnings

- category: architecture
  insight: Any lifecycle that waits on `animation_finished` (or similar) after latching “death” state must still call `play()` on a real clip, or the signal never fires and the entity can remain in a half-torn-down state (e.g. collision cleared, never freed).
  impact: GDScript review flagged a critical bug: missing `Death` clip left collision-disabled enemies stuck in the tree until review added an immediate `queue_free` path when `has_animation(&"Death")` is false.
  prevention: For completion-driven teardown, branch explicitly: if the clip does not exist, run the same post-death cleanup and despawn synchronously; do not assume assets always contain the clip.
  severity: high

- category: testing
  insight: In Godot 4.6.x headless tests, lambdas capturing a plain `int` may not observe increments across concurrent `animation_finished`-style emissions; mutable state for demos should live in a `RefCounted` helper, `Array`, or `Dictionary` that the closure closes over by reference.
  impact: Test Breaker’s concurrent-signal adversarial case needed a non-primitive capture pattern to assert ordering reliably.
  prevention: When authoring multi-emission signal tests, use reference types or documented container captures; avoid primitive-only closure state for mutation across frames.
  severity: medium

- category: architecture
  insight: `Node._ready()` that calls `get_tree()` without checking `is_inside_tree()` produces engine errors and brittle behavior when the node is constructed for unit tests that call `_ready()` before `add_child`.
  impact: Checkpoint noted orphan-handler noise; implementation added `is_inside_tree()` guard so headless infection/absorb suites stay clean.
  prevention: Guard `get_tree()` / tree queries in `_ready()` with `is_inside_tree()`, or defer tree access to `NOTIFICATION_ENTER_TREE` / first frame.
  severity: medium

- category: process
  insight: Spec left “end of Death play” as abstract completion semantics; behavior was locked by tests + implementation binding to `animation_finished`. Naming the concrete signal in the spec would reduce implementer ambiguity.
  impact: Low rework cost here, but increases review surface until tests exist.
  prevention: When AC is “plays to completion,” spec should cite the bound Godot API (signal or method) once the engine version is fixed.
  severity: low

### Anti-Patterns

- description: Latching a disabled-collision or no-interaction “dying” state then awaiting a completion signal without guaranteeing `play()` runs for that animation.
  detection_signal: Enemy never freed after death; `animation_finished` never logged; assets missing the expected clip name.
  prevention: Pair latch with `has_animation` check and a synchronous fallback teardown path.

- description: `_ready()` assumes the node is already in the scene tree.
  detection_signal: Headless test logs show `get_tree()` on orphan node; handler tests use manual `_ready()` before `add_child`.
  prevention: `is_inside_tree()` guard or defer tree coupling.

### Prompt Patches

- agent: Engine Integration Agent
  change: Whenever despawn or teardown is gated on `AnimationPlayer` completion signals, require a documented branch: if the target animation name is missing from the player, perform the same collision/targeting teardown and schedule `queue_free()` immediately—never wait for a signal that cannot fire.
  reason: Prevents stuck half-dead entities when clips or exports are incomplete.

- agent: GDScript Reviewer Agent
  change: Flag `_ready()` implementations that call `get_tree()` (or other tree APIs) without `is_inside_tree()` when the class appears in unit tests or may be instanced off-tree.
  reason: Matches headless test patterns and avoids error-level noise masking real failures.

- agent: Test Breaker Agent
  change: For adversarial tests that simulate concurrent or repeated completion signals, prefer closure capture over `Array`, `Dictionary`, or small `RefCounted` helpers when mutating counters across emissions; document if primitives are insufficient for the engine version.
  reason: Reduces flaky or false-green concurrent-signal tests in headless Godot.

### Workflow Improvements

- issue: Animation-completion ACs sometimes stay API-agnostic in spec while tests mandate a specific binding.
  improvement: After spec freeze, add a single “Bound API” line (signal name + disconnect/cleanup rules) for animation-driven lifecycles.
  expected_benefit: Faster implementation alignment and fewer review iterations on “which signal?”

### Keep / Reinforce

- practice: GDScript review escalated missing-clip teardown to CRITICAL and blocked shipping a collision-disabled zombie state.
  reason: Lifecycle bugs that strand invisible collider-off actors are high player-visible impact; severity matches.

- practice: Splitting coverage into scene/EAC tests, infection/handler tests, and a dedicated adversarial file mapped cleanly to DAP clusters and CHECKPOINTS index.
  reason: Makes AC traceability and gatekeeper validation straightforward.

---

## [wire_animations_to_generated_scenes] — Root AnimationPlayer wired from GLB; Godot lifecycle and `run_tests.sh` import hang

*INTEGRATION (manual AC pending): 2026-04-03*

### Learnings

- category: testing
  insight: After `add_child`, Godot runs `_ready()` deferred; assertions that read script state immediately after `add_child` see pre-`_ready()` values unless the test calls `_ready()` once or awaits a frame.
  impact: WAGS tests initially failed on `_ready_ok` / `animation_player` despite correct scene structure; resolution required aligning test timing with engine semantics.
  prevention: For “controller wired at load” tests, either await `process_frame` (async runner) or call `_ready()` explicitly after tree insertion when the suite is synchronous.
  severity: medium

- category: architecture
  insight: In GDScript 2 on Godot 4.6.x, comparing `what == NOTIFICATION_ENTER_TREE` inside `_notification` can fail even when the engine sends `what == 24`; use an explicit numeric constant (or verify the enum resolves) when enter-tree side effects must run.
  impact: AnimationPlayer resolution never ran; all WAGS controller checks failed until equality used literal `24`.
  prevention: When depending on `Object` notification IDs in `_notification`, log or unit-check the constant once per engine version or use documented `Object.NOTIFICATION_*` only after confirming it matches runtime.
  severity: high

- category: infra
  insight: `godot --import` without a timeout can block CI and local scripts indefinitely; wrapping it preserves the “reimport before tests” intent without hanging the pipeline.
  impact: `ci/scripts/run_tests.sh` appeared stuck; AC “run_tests.sh exits 0” was not reliably testable.
  prevention: Always bound import and test invocations with `timeout` (and prefer `--headless` for CI) per project CLAUDE guidance.
  severity: medium

### Anti-Patterns

- description: Treating `NOTIFICATION_ENTER_TREE` and unqualified `NOTIFICATION_ENTER_TREE` as identical in GDScript without verifying the numeric value.
  detection_signal: `_notification` body never runs the expected branch; headless logs show `what=24` but no side effects.
  prevention: Use a class-level `const _NOTIF_ENTER_TREE := 24` (with engine-version comment) or assert equality once in a tiny diagnostic script.

### Prompt Patches

- agent: Test Designer Agent
  change: For any test that `add_child`s a PackedScene root and reads `_ready()`-initialized state, document whether the suite is sync or async; if sync, require an explicit `_ready()` call or a documented one-frame pump after add_child.
  reason: Avoid false failures from deferred ready semantics.

### Workflow Improvements

- issue: Tickets mix “in-editor visual” ACs with headless-only automation; Gatekeeper correctly blocks COMPLETE without human evidence, leaving the ticket in INTEGRATION with an easy-to-miss next step.
  improvement: Add a one-line “Manual QA” subsection template on tickets that require editor verification, with checkbox and date field for the human signer-off.
  expected_benefit: Clear closure path and fewer stalled INTEGRATION tickets.

### Keep / Reinforce (closure)

- practice: After human confirms the editor AC, AC Gatekeeper immediately promoted ticket to `COMPLETE`, recorded sign-off in `Validation Status`, and `git mv` to `done/` — no extra spec churn.
  reason: Closes the loop the gatekeeper opened at INTEGRATION without leaving orphan “pending manual” state.

---

## [containment_hall_01_layout] — 3D scene construction for a linear level with four gameplay zones

*Completed: 2026-03-17*

### Learnings

- category: architecture
  insight: Enemy mesh height is not encoded in the enemy scene's name or ticket metadata; placing enemies at the correct Y requires inspecting the actual scene or making an assumption with tolerance.
  impact: The Spec Agent assumed enemy origin = vertical center of ~1.0 m mesh and added ±0.1 m tolerance to all position tests. If the actual mesh height differs, enemies clip into geometry or float above it.
  prevention: Add an "enemy collision height" field to the enemy scene's canonical ticket or to a shared project constants file so any agent that places enemies can read it without inspection.
  severity: medium

- category: testing
  insight: NodePath-typed properties (e.g. RespawnZone.spawn_point) cannot be structurally verified via get_node() in headless tests because the node is not in the scene tree. The only safe headless assertion is that the path string is non-empty and targets the expected node name.
  impact: Full resolution testing was deferred; a misconfigured path would pass all tests and only fail at runtime.
  prevention: When a spec requires a wired NodePath, include a tree-insertion integration test (add_child the root scene) that calls get_node(spawn_point) and asserts non-null. Add a dedicated integration test class for scene-wiring assertions.
  severity: medium

- category: architecture
  insight: Spec agents must compute jump physics before finalizing platform gap widths. The initial layout used 3 m gaps but derived max jump range was only ~1.98 m — meaning the level was untraversable as specced.
  impact: Gap was revised to 1.0 m before implementation began; caught in spec phase with no rework cost. If missed, all test phases would have passed but the level would be physically unplayable.
  prevention: Add a required "traversability check" section to any scene-construction spec that involves platforms or gaps: derive max jump range from player_controller_3d.gd constants and confirm every gap < 80% of that range.
  severity: high

- category: testing
  insight: Thin visual-separator walls that are also StaticBody3D nodes can block player traversal, making them a Low-confidence design decision. The spec acknowledged this conflict but defaulted to StaticBody3D anyway.
  impact: Confidence was explicitly flagged Low. If the wall blocked traversal the Implementer was instructed to convert it to a MeshInstance3D — delegating a geometry decision to the implementation phase.
  prevention: When a spec cannot resolve whether a node should have collision, declare it collision-free (MeshInstance3D only) by default and document the trade-off. Never leave a StaticBody3D with a "maybe remove collision" qualifier in the spec.
  severity: low

### Anti-Patterns

- description: Compound test assertions (e.g. T-11 checks non-zero extents AND BoxShape3D type in one pass) can mask individual mutation targets. A SphereShape3D with non-zero radius satisfies a naive "extents != 0" check.
  detection_signal: A single test method asserts both a type property and a value property in the same loop iteration.
  prevention: Separate shape-type enforcement (is BoxShape3D) from value enforcement (extents > 0) into distinct adversarial tests so each mutation target has its own named failure.

- description: Using a ticket's prose task description as the authoritative node name when a separate spec document also defines the name leads to divergence. "GameUI" in the task vs "InfectionUI" in the spec forced the Test Designer to arbitrate.
  detection_signal: A test is written using a node name that does not appear verbatim in the spec's node tree table.
  prevention: Spec document node tree table is always authoritative over ticket task prose. If they conflict, the Spec Agent must update the ticket task description to match the spec before handing off.

### Prompt Patches

- agent: Spec Agent
  change: Before finalizing any platform layout, compute max_jump_range = (2 * jump_velocity * horizontal_speed) / gravity using constants from player_controller_3d.gd, and assert every inter-platform gap < 0.8 * max_jump_range. Document the computed value in the spec's GEO section.
  reason: Prevents specs that describe untraversable levels; caught at spec phase instead of QA.

- agent: Spec Agent
  change: When a visual-separator node is added for level readability, default to MeshInstance3D (no collision). Only use StaticBody3D if the separator must block the player. Never leave a StaticBody3D with a comment saying "remove collision if it blocks traversal."
  reason: Eliminates Low-confidence geometry decisions from being delegated to the implementation agent.

- agent: Test Design Agent
  change: When a spec includes any NodePath-typed property wired between nodes (e.g. spawn_point, target_node), add at least one test that inserts the scene root into a temporary SceneTree and calls get_node(path), asserting non-null. Label this test as a "wiring integration test" and mark it headless-safe only if the NodePath can be verified without tree entry.
  reason: Headless NodePath string checks give a false sense of coverage; a misconfigured path only fails at runtime.

### Workflow Improvements

- issue: AC-5 ("human-playable in-editor without debug overlays") has no automated proxy test and was still open when all 38 automated tests passed, leaving the ticket BLOCKED on manual verification with no clear owner or schedule.
  improvement: For scene-construction tickets, add a required AC at the spec phase: "A documented manual QA checklist exists as a section in the ticket." The checklist should enumerate exact steps (open scene, press Play, confirm N items) so the human reviewer can execute it deterministically.
  expected_benefit: Prevents tickets from reaching BLOCKED state on an undocumented manual step after all automated gates pass.

- issue: The Test Breaker added T-ADV-31 through T-ADV-38 as adversarial extensions, but several of these (T-ADV-32, T-ADV-35, T-ADV-37) guarded invariants that were implicit in the spec and not stated as acceptance criteria. This required the Test Breaker to re-derive intent from spec prose.
  improvement: The Spec Agent should include a "Structural invariants" subsection listing non-AC invariants (e.g. "exactly one WorldEnvironment", "all gameplay floor tops >= -3.0 m") so the Test Breaker has explicit targets rather than rediscovering them from prose.
  expected_benefit: Reduces Test Breaker inference work and makes adversarial test selection deterministic.

---

## [fusion_opportunity_room] — Validation-only ticket: all 33 tests passed first run, no scene changes needed.

*Completed: 2026-03-19*

### Learnings

- category: testing
  insight: RefCounted subclasses (e.g. FusionResolver, MutationSlotManager) must never have `.free()` called; doing so raises a Godot runtime error. This is a silent correctness hazard in test teardown.
  impact: The existing `test_fusion_resolver.gd` already called `.free()` on RefCounted objects throughout the suite, polluting test output with runtime errors. T-39/T-40 were written correctly by explicitly avoiding this pattern.
  prevention: Add a Static QA rule: any test teardown calling `.free()` on an object must first assert the object extends Object (not RefCounted). Explicitly document in test design templates that RefCounted instances are auto-freed and `.free()` must not be called.
  severity: medium

- category: testing
  insight: Validation-only tickets (spec+test against a pre-built scene) still surface real cross-file duplication risks: test numbers assigned in the ticket task description can collide with assertions already covered by prior test files, requiring remapping before any test is written.
  impact: Three planned test IDs (T-34 collision_mask, T-35/T-36 enemy positions, T-37 node existence) would have been exact duplicates of T-25, T-24, T-9/T-16 in `test_containment_hall_01.gd`. Remapping was caught autonomously at spec time with no rework cost, but only because the Spec Agent cross-referenced the existing test file.
  prevention: Before a Test Designer writes any tests for a validation-only ticket, require an explicit "duplication audit" step: list every existing test file covering the same scene, enumerate their assertion subjects, and document which new test IDs are remapped and why.
  severity: medium

- category: testing
  insight: `get_scene_file_path()` returns a non-empty string only for the root node of an instanced PackedScene. Tests that call this method on a non-root instanced node will always get an empty string, producing a silent false-positive or false-negative depending on assertion direction.
  impact: T-35/T-36 relied on this method. The Spec Agent verified correctness by tracing the scene file's `[node ... instance=ExtResource(...)]` declaration confirming EnemyFusionA/B are scene roots. Without this check, the test would have passed vacuously.
  prevention: When speccing tests that use `get_scene_file_path()`, require the spec to explicitly identify whether the target node is the root of its instanced scene. Document this in the test comment. If uncertain, add a fallback assertion on the node class name.
  severity: low

- category: testing
  insight: `_ready()` does not automatically fire on `add_child()` in headless Godot test runs. Tests that depend on `_ready()` side effects (e.g. slot manager instantiation) must call `handler._ready()` explicitly after tree insertion.
  impact: T-38 required explicit `handler._ready()` to initialize the slot manager; omitting it would have caused a null-dereference assertion failure. The fix is a one-liner but is non-obvious and not documented in earlier test files.
  prevention: Add to the Test Design Agent prompt: "In headless tests, after `tree.root.add_child(node)`, always call `node._ready()` explicitly if the test depends on any state initialized in `_ready()`. Do not assume `add_child` triggers lifecycle callbacks."
  severity: medium

- category: process
  insight: A validation-only ticket (scene pre-built, no code to write) still generates meaningful agent work: one spec document, two test files, one static QA pass, and 21 adversarial cases. The "zero implementation effort" framing can cause the planner to underestimate agent runtime budget and underspec the test scope.
  impact: The ticket was correctly scoped here, but the planner's initial assumption that the scene did not yet exist (checkpoint: "Containment Hall 01 scene existence") created a mismatch that required a correction before spec work could begin.
  prevention: Planners must verify scene/file existence via glob or explicit path check before writing an execution plan. If the file exists, the ticket should be labeled "validation-only" in its description and the execution plan must omit any implementation task.
  severity: low

### Anti-Patterns

- description: Test IDs assigned in ticket task prose collide with IDs in existing test files covering the same scene. The ticket author does not cross-reference existing tests when assigning numbers.
  detection_signal: A new test file's T-N covers the same node property (position, collision_mask, script path) as a test in a sibling file for the same scene.
  prevention: The Spec Agent must open and read all test files for the target scene before assigning test IDs. Any collision must be resolved with a remapping note in the spec before the Test Designer begins.

- description: Calling `.free()` on RefCounted objects in test teardown is a recurring error that appears across multiple test files without being caught by Static QA.
  detection_signal: Any `.free()` call in a test file where the freed object's class is not explicitly verified to extend Object (not RefCounted).
  prevention: Static QA Agent must flag `.free()` calls in test files and verify the target class. Add a lint rule or explicit check step.

### Prompt Patches

- agent: Test Design Agent
  change: In headless tests, after `tree.root.add_child(node)`, always call `node._ready()` explicitly if the test depends on any state initialized in `_ready()`. Do not assume `add_child` alone triggers lifecycle callbacks in headless mode.
  reason: In headless Godot, `_ready()` does not fire automatically on `add_child`. Missing this causes null-dereference failures on any state set up in `_ready()`.

- agent: Test Design Agent
  change: Never call `.free()` on objects whose class extends RefCounted. RefCounted instances are auto-freed when they go out of scope. Calling `.free()` explicitly raises a Godot runtime error that pollutes test output.
  reason: This is a recurring error across multiple test files. It is non-fatal but produces confusing runtime errors that obscure real test failures.

- agent: Spec Agent
  change: Before writing any test IDs for a validation-only ticket, open every existing test file that targets the same scene. Build a list of already-asserted (node, property) pairs. Any planned test that duplicates a pair from that list must be remapped to a new, genuinely uncovered assertion. Document the remapping explicitly in the spec.
  reason: Three test IDs had to be remapped on this ticket. Without the cross-reference step, duplicate assertions would have been written and caught only at Static QA, requiring rework.

### Workflow Improvements

- issue: Planner agents assume scene files do not exist and plan an implementation task, then discover mid-run that the scene is pre-built. This wastes one round-trip and produces an incorrect execution plan that must be mentally corrected by the next agent.
  improvement: Add a mandatory "file existence check" step to the Planner Agent's execution plan template: before writing tasks, list the expected output files and state explicitly whether each already exists. If a key scene/script file exists, remove the implementation task and label the ticket "validation-only."
  expected_benefit: Eliminates the planner/reality mismatch that caused the checkpoint entry for "Containment Hall 01 scene existence." Saves one full agent invocation per miscategorized ticket.

- issue: AC-6 (human playthrough) has no documented manual QA checklist with atomic steps; it is described only as a free-form paragraph in the ticket. The same structural gap occurred in containment_hall_01_layout (noted in prior learnings) and recurred here.
  improvement: The Spec Agent must emit an explicit "Manual QA Checklist" section in the spec for any INTEGRATION-class AC. The checklist must enumerate exact numbered steps (open scene, move to X, perform action Y, observe Z) so the human reviewer can execute it without re-reading the full ticket.
  expected_benefit: Prevents tickets from stalling at INTEGRATION stage because the human reviewer must interpret prose rather than follow a checklist. Consistent with the workflow improvement noted in [containment_hall_01_layout] — this is a repeat failure mode.

### Keep / Reinforce

- practice: The adversarial suite included a "distinct node path" test (ADV-FOR-09) that verifies EnemyFusionA.get_path() != EnemyFusionB.get_path(). This catches the "duplicate node name" failure mode that individual per-enemy tests cannot detect.
  reason: Scene authoring errors can silently shadow a node with a duplicate name. Per-entity tests pass because they both resolve to the same (surviving) node. The path-inequality check is the only headless-safe way to catch this. Reinforce this pattern for any ticket that requires N distinct named instances.

- practice: Validation-only tickets correctly distinguished headless-testable ACs (AC-1 through AC-5) from INTEGRATION ACs (AC-6) in both the spec and the ticket status block, preventing the test phase from attempting to automate an unautomatable criterion.
  reason: This separation prevented wasted effort on phantom "run the game" tests and kept the INTEGRATION gating condition explicit and unambiguous.

---

## [light_skill_check] — Validation-only ticket: 253/253 tests passed first run, no scene changes needed.

*Completed: 2026-03-20*

### Learnings

- category: testing
  insight: A node's `.position.y` (the origin) can differ substantially from its effective top surface Y when the CollisionShape3D has a non-zero local offset. SkillCheckFloorBase sits at node Y=0 but its top surface is at Y=-4.0 due to a CollisionShape3D Y-offset of -4.5. Tests that assert surface geometry must compute `node.position.y + collision_shape_offset.y + box_half_height`, not `node.position.y` alone.
  impact: The Planner and Spec agents both flagged this explicitly (checkpoint [light_skill_check] Planning). If a test had asserted `node.position.y < -1.0` directly rather than computing the surface, it would have produced a false-negative (node origin is 0, which is >= -1.0, passing when it should not).
  prevention: Add to the Spec Agent prompt: "For any StaticBody3D floor or platform, compute and document the effective top surface Y = node.position.y + collision_shape_local_offset.y + (box.size.y / 2). Never assert raw node.position.y as a proxy for surface height."
  severity: medium

- category: testing
  insight: NodePath resolution in headless tests is reference-frame sensitive. A NodePath like `"../SpawnPosition"` must be resolved via `respawn_zone_node.get_node_or_null(path)`, not `root.get_node_or_null(path)`. The `..` segment is relative to the node that owns the property, not the scene root.
  impact: This was caught at spec time (checkpoint [light_skill_check] Spec). If the test had called `root.get_node(spawn_point_path)`, the `..` from root has no parent and returns null, causing a false test failure that masks whether the wiring is correct.
  prevention: The Spec Agent must annotate every NodePath-type property test with the correct resolution call site. When the NodePath starts with `..`, the test must call `.get_node_or_null()` on the owning node, not the scene root.
  severity: medium

- category: testing
  insight: Adversarial tests should be scoped to the single mutation they are designed to catch, even when a primary test covers a superset. ADV-SKC-06 was intentionally limited to P3>P1 (not P3>P2) because T-46 already covers both comparisons. Keeping adversarial tests narrowly focused prevents them from becoming redundant duplicates of primary tests.
  impact: If ADV-SKC-06 had also asserted P3>P2, it would overlap T-46 with no additional mutation-target coverage. The scoping decision was explicit (checkpoint [light_skill_check] TestBreak).
  prevention: The Test Breaker Agent should document for each adversarial test: "mutation target = [specific property or failure mode]" and verify no primary test already asserts the exact same (node, property, value) triple.
  severity: low

- category: process
  insight: A rate limit interruption during test design does not corrupt work product if agents record partial decisions in CHECKPOINTS.md before stopping. The light_skill_check test design survived a mid-session rate limit interruption cleanly because the checkpoint log captured all in-progress assumptions.
  impact: No rework was required after the interruption. However, the interruption itself is a workflow risk: if CHECKPOINTS.md is not written before a rate limit hits, the next agent invocation must re-derive decisions that were already made.
  prevention: Test Design Agents should write checkpoint entries immediately after each major scoping decision (e.g. after each ADV-SKC-* scope decision), not only at end of session. Treat CHECKPOINTS.md writes as synchronous, not batched.
  severity: low

### Anti-Patterns

- description: Asserting `node.position.y` directly as a proxy for surface height on StaticBody3D nodes. The raw position is the origin, not the surface — offset and shape dimensions must be included.
  detection_signal: Any test assertion of the form `node.position.y < threshold` for a floor or platform node, without a preceding computation of `position.y + offset.y + half_height`.
  prevention: Spec agents must compute and document effective surface Y for every geometry node. Test agents must use the computed value, not the raw position.

- description: The same recurring pattern of INTEGRATION-class ACs (subjective difficulty, human playability) reaching the human reviewer as ticket prose rather than a numbered checklist. This is the third consecutive ticket where this gap appeared.
  detection_signal: A ticket's INTEGRATION-class AC is described in prose without an explicit numbered step list labeled "Manual QA Checklist."
  prevention: Spec Agent must emit a "Manual QA Checklist" section for every INTEGRATION AC at spec time. This was flagged in [containment_hall_01_layout] and [fusion_opportunity_room] learnings and has still not been enforced at the Spec Agent prompt level.

### Prompt Patches

- agent: Spec Agent
  change: For any StaticBody3D floor, platform, or hazard zone, compute and document the effective top surface Y as `node.position.y + collision_shape_local_offset.y + (box.size.y / 2)`. State this value explicitly in the spec's GEO section. Never use raw `node.position.y` as the surface height.
  reason: The SkillCheckFloorBase checkpoint showed that node origin and surface height diverge whenever a CollisionShape3D has a local offset. Tests that use raw position fail silently with incorrect pass/fail behavior.

- agent: Spec Agent
  change: For every NodePath-type property test, annotate the resolution call site. If the path starts with `..`, the test must resolve it via `owning_node.get_node_or_null(path)`, not `scene_root.get_node_or_null(path)`. Include the correct call site verbatim in the spec's test traceability table.
  reason: Incorrect resolution reference frame produces silent null returns that make the test fail for the wrong reason, obscuring whether the wiring is actually correct.

- agent: Test Breaker Agent
  change: For each adversarial test, document its mutation target as a single (node, property, failure mode) triple and verify that no primary test (T-N) already asserts the identical triple. If overlap exists, redirect the adversarial test to a distinct failure mode before writing it.
  reason: ADV-SKC-06 scope decision showed that adversarial tests can silently duplicate primary test assertions when the adversarial agent does not cross-reference the primary suite. Narrow scope produces better mutation coverage per test.

- agent: Test Design Agent
  change: Write a CHECKPOINTS.md entry after each major adversarial scoping decision (e.g. each ADV-* scope choice), not only at session end. Each entry is a synchronous write — do not batch them.
  reason: Rate limit interruptions mid-session discard in-progress decisions if they have not been persisted. Incremental CHECKPOINTS writes ensure continuity regardless of when the session ends.

### Workflow Improvements

- issue: INTEGRATION-class ACs (subjective difficulty, human playability) reach the human reviewer as ticket prose for the third consecutive ticket. The prompt patches from [containment_hall_01_layout] and [fusion_opportunity_room] have not been applied to the Spec Agent's active prompt, causing the same gap to recur.
  improvement: Apply the "Manual QA Checklist" prompt patch from [fusion_opportunity_room] learnings to the Spec Agent's prompt immediately. The instruction should read: "For any INTEGRATION-class AC, emit a numbered Manual QA Checklist section with atomic, observable steps (open scene → navigate to location → perform action → observe expected outcome)."
  expected_benefit: Breaks the recurring cycle of tickets stalling at INTEGRATION with undocumented human steps. Two prior learnings identified this; without a prompt-level fix it will recur on every ticket with subjective ACs.

### Keep / Reinforce

- practice: The spec preemptively documented the SkillCheckFloorBase Y-interpretation risk (pit floor vs. walkable floor) in both the spec document and the ticket's Risks and Assumptions table. This prevented any downstream agent from misclassifying the node type.
  reason: Naming a node "SkillCheckFloorBase" does not communicate that it is 4 m below corridor level. Explicit documentation of the geometry interpretation at spec time prevented a category of test errors before they occurred.

- practice: Two consecutive validation-only tickets ([fusion_opportunity_room], [light_skill_check]) achieved 100% first-run test passes with zero scene modifications. The spec-to-test pipeline is functioning correctly for this ticket type.
  reason: Confirms the pattern of precise scene geometry read at spec time → deterministic test assertions → no integration surprises. This should be the expected baseline for all future validation-only tickets.

---

## [procedural_room_chaining] — Spec API churn and ticket description drift caused full test suite invalidation mid-cycle
*Completed: 2026-03-25*

### Learnings

- category: process
  insight: A ticket description that references an artifact (the "fusion room") that does not exist in the project forces a planning pivot that propagates a corrected scope to every downstream agent. The correction is cheap individually but compounds if it reaches the Spec Agent before validation.
  impact: The Planner had to file a checkpoint, annotate the ticket description, and document the corrected sequence. Any downstream agent that had not read the checkpoint would spec or test against the wrong sequence.
  prevention: Before the Planner writes an execution plan, require an explicit "dependency artifact check": verify that every scene, script, or asset named in the ticket description exists at the stated path. Treat any missing artifact as a spec gap that must be resolved in the planning document before execution begins.
  severity: high

- category: process
  insight: A mid-cycle API redesign (Spec Rev2 replacing Rev1) that changes function signature and return type voids every previously planned test ID. All PRC-SEQ-*, PRC-DEDUP-*, PRC-SCHEMA-*, PRC-POOL-* IDs from Rev1 were superseded, requiring the Test Designer to start from a clean test map.
  impact: This caused a full re-spec and re-test-design cycle. The root cause was that Rev1 was written against the ticket's prose schema ("generate(seed)") without validating consistency against the broader architecture spec that defined the authoritative API.
  prevention: The Spec Agent must resolve the authoritative API signature in the first revision pass, cross-checking the ticket's Required Input Schema against any referenced system spec documents. If a conflict exists between prose and schema, file a checkpoint and resolve before publishing Rev1. A second revision cycle is a workflow smell that indicates insufficient upfront API arbitration.
  severity: high

- category: testing
  insight: Randomized deduplication tests on small pools (e.g. exactly 2 items drawn from a 2-item combat pool) have an irreducible false-certainty problem: the no-repeat property is structurally guaranteed by pool exhaustion, not by the algorithm. A naive implementation would also pass.
  impact: PRC-GEN-3 ("no duplicate paths") passes even with a broken Fisher-Yates implementation because there are only 2 combat items. PRC-ADV-3 was added to test with a synthetic 4-item pool where a naive randi_range implementation would produce repeats, providing the only real coverage of the deduplication algorithm.
  prevention: When the production pool size equals the draw count for any category, the Test Designer must add a synthetic-pool adversarial test that uses a larger pool (e.g. 4 items, draw 2) to ensure the deduplication algorithm is independently verified. Document this as a mandatory companion test whenever pool_size == draw_count.
  severity: medium

- category: testing
  insight: Headless GDScript test runners cannot capture stdout, so any AC that requires observing console output (e.g. "RNG seed printed to console") cannot be verified by automated tests and must fall back to code inspection as its sole evidence basis.
  impact: PRC AC "RNG seed printed to console" was evidenced only by code review of the unconditional `print()` call. If the print is ever moved behind a conditional or removed, all existing tests continue to pass and the AC silently regresses with no detection.
  prevention: For any AC that requires observable console output, either: (a) add a testable side effect (e.g. expose a `last_seed` property on the class so tests can assert the value without stdout), or (b) explicitly label the AC as "code-inspection-only" in the ticket validation status and document the exact file and line number that satisfies it. Option (a) is preferred and should be spec'd as an explicit property on pure-logic classes.
  severity: medium

- category: architecture
  insight: When two coordinating systems (DeathRestartCoordinator and RunSceneAssembler) each own independent instances of the same state machine (RunStateManager), the two lifecycles are silently decoupled. A restart signal from DRC does not propagate to RSA; the room chain does not rebuild on run restart.
  impact: Integration between DRC restart and RSA room rebuild was explicitly deferred to a future ticket. This means the "restart" flow is architecturally incomplete — the room chain only assembles on first load, not on each run. The deferral was a reasonable short-term decision but creates a gap that is invisible to automated tests.
  prevention: When a spec makes a "defer integration to future ticket" decision that leaves a partial behavior (e.g. "room chain does not rebuild on restart"), the Spec Agent must add a concrete follow-up ticket reference or a failing test stub that documents the missing behavior. Deferral decisions without a test stub are invisible debt.
  severity: medium

### Anti-Patterns

- description: Ticket prose names a specific artifact (scene, resource, node name) that does not exist in the project at planning time. This causes a scope correction that must be manually propagated to every subsequent agent in the chain.
  detection_signal: Any artifact path or scene name in the ticket description that cannot be resolved by a glob or file check at planning time.
  prevention: Planner Agent must glob-check every artifact named in the ticket description before writing the execution plan. Unresolved artifacts must be flagged as blocking gaps — not silently worked around.

- description: An API spec revision that changes the function signature and return type mid-cycle, without a mechanism to invalidate or version-lock downstream test plans that referenced the old API.
  detection_signal: A checkpoint entry saying "Spec RevN supersedes RevM; all prior test IDs are voided."
  prevention: The Spec Agent must resolve the canonical API in Rev1 by explicitly cross-referencing the ticket schema, any referenced architecture documents, and existing implementations. Rev2 rewrites are a signal that Rev1 was published too early.

- description: Using a provisional (unverified) seed pair in a deterministic-output test when the pool is small enough that the seeds may collide, without a verification step at any stage of the pipeline.
  detection_signal: A test comment noting that the seed pair has "~50% false-failure risk" or "provisional — must be verified at implementation."
  prevention: The Spec Agent must mark provisional seed pairs with a blocking TODO for the Implementation Agent or Test Breaker Agent to verify. If the agent cannot pre-compute the seed collision at spec time (red phase), the CHECKPOINTS.md must record the seed pair as unconfirmed with an explicit resolution gate.

### Prompt Patches

- agent: Planner Agent
  change: Before writing the execution plan, run a dependency artifact check: for every scene path, script path, and named resource in the ticket description, confirm the file exists at the stated location. If any artifact is missing, add a "missing artifact" section to the planning document that names the gap, blocks execution of dependent tasks, and proposes a resolution (add artifact, remove reference, or create follow-up ticket). Do not proceed to execution planning until all missing artifacts are resolved or explicitly scoped out.
  reason: The "fusion room" gap required a mid-cycle correction that propagated to spec, test, and checkpoint. An upfront artifact check at planning time eliminates this class of scope drift entirely.

- agent: Spec Agent
  change: When writing the first spec revision for a system ticket, resolve the authoritative function signature before publishing. Cross-check: (1) the ticket's Required Input Schema, (2) any referenced architecture or design documents, (3) any existing callers in the codebase. If two sources conflict, file a checkpoint with the conflict and resolution before publishing the spec. Do not publish a spec with an unresolved API conflict — a second revision that changes the signature and voids all prior test IDs is a workflow failure, not a refinement.
  reason: The PRC Rev1 → Rev2 API change voided all test IDs and required a full re-spec. The conflict between the ticket prose API and the Required Input Schema should have been resolved before Rev1 was published.

- agent: Spec Agent
  change: When a spec decision defers integration between two systems to a future ticket (e.g. "RSA does not rebuild on DRC restart — deferred"), add a failing test stub to the test suite that documents the missing behavior. Name the stub "TODO_[description]" and mark it with `pending()` or equivalent. This stub is not a test to be implemented now — it is executable documentation of the integration gap.
  reason: Deferral decisions without a test stub are invisible architectural debt. The PRC deferral of DRC-RSA restart integration left the behavior gap undocumented and undetectable by the test suite.

### Workflow Improvements

- issue: The INTEGRATION-class AC "Transitions between rooms feel seamless (no visible load pop)" was not accompanied by a Manual QA Checklist at spec time. This is the fourth consecutive ticket where this gap occurred. The prompt patches from [containment_hall_01_layout], [fusion_opportunity_room], and [light_skill_check] have not been applied to the Spec Agent's active prompt.
  improvement: The "Manual QA Checklist" prompt patch identified in [fusion_opportunity_room] learnings must be applied to the Spec Agent's prompt as a standing rule. The instruction must be: "For any AC that requires human observation (visual, audio, runtime behavior), emit a numbered Manual QA Checklist section with atomic steps in the format: open [scene] → trigger [action] → observe [exact expected output]. The checklist must appear in the spec document, not only in the ticket's Next Action block."
  expected_benefit: This has recurred on every ticket with a visual AC. A prompt-level rule is the only fix — individual learning entries have not stopped the recurrence.

- issue: The seed pair for PRC-SEED-2 was declared provisional at spec time, acknowledged as unverifiable in red phase, and passed through test design with a comment noting the risk. No agent in the chain was assigned ownership of resolving the provisional status before the test was finalized.
  improvement: When a spec creates a provisional assumption (seed pair, threshold value, path string) that requires verification at a later phase, the CHECKPOINTS.md entry must include an explicit "resolution owner" field naming the agent responsible for confirming or correcting the assumption. The Implementation Agent or Static QA Agent must check all open provisional assumptions before signing off.
  expected_benefit: Prevents provisional values from being silently locked in by the time the implementation is complete, where changing them requires a test suite update and a new checkpoint.

### Keep / Reinforce

- practice: Separating RoomChainGenerator (pure RefCounted, no SceneTree) from RunSceneAssembler (Node, SceneTree caller) allowed the entire generation logic to be tested headlessly with 34 tests, zero SceneTree dependencies, and high confidence in the algorithm's correctness.
  reason: This architectural split is a strong pattern for any system where a pure-logic computation must be combined with Godot scene graph operations. The pure layer is testable; the integration layer is audited by code review and manual playtest. Reinforce this pattern for all future systems that combine data generation with scene assembly.

- practice: The Fisher-Yates shuffle with a seeded RandomNumberGenerator, constructed fresh per call, guarantees cross-instance determinism without shared state. This was explicitly called out in the implementation notes and verified by the adversarial seed tests.
  reason: Shared RNG state across instances is a common source of non-determinism in procedural generation. The per-call construction pattern prevents this class of bug and should be the default for any new seeded random system in the project.

---

---

## [mini_boss_encounter] — 66 tests passing (T-53–T-62 + ADV-MBA-01–08); ticket at INTEGRATION pending human playtest.

*Completed: 2026-03-20*

### Learnings

- category: testing
  insight: `get_path()` returns an empty NodePath (`""`) for nodes that have not been added to a SceneTree. Equality comparisons between two empty NodePaths vacuously pass, making tests that assert "these two nodes have distinct paths" trivially pass even when both nodes are the same object.
  impact: T-57 was written to assert EnemyMiniBoss.get_path() != EnemyFusionA.get_path() (and the other two enemies). All four comparisons returned "" == "", causing the distinctness tests to pass unconditionally and fail to catch a duplicate-node scenario. The fix was to switch to `.name` comparisons, which are non-empty regardless of tree attachment.
  prevention: Never use `get_path()` on nodes that are not inserted into a SceneTree. For identity-distinctness tests on headless-loaded scene nodes, use `.name`. If path-based identity is required, add the node to a temporary root first and assert non-empty path before comparing.
  severity: high

- category: testing
  insight: Strict `>` boundary assertions fail silently when two adjacent geometry zones share an exact boundary value. A scene authored so that zone A ends at X=55.0 and zone B starts at X=55.0 will fail a test asserting `zone_b_left_edge > zone_a_right_edge` because the values are equal — even though the design intent (non-overlapping zones) is fully satisfied.
  impact: ADV-MBA-06 used strict `>` to assert MiniBossFloor left edge (55.0) > SkillCheckPlatform3 right edge (55.0). The test failed during red-phase integration; the zone boundary was valid but the operator was wrong. Required an operator change from `>` to `>=` to correctly express "no overlap."
  prevention: When asserting spatial non-overlap between zones, use `>=` (not `>`) for boundary comparisons. Document the exact boundary value and operator choice in the spec. A `>` is only correct when a gap between zones is required by design. Include a comment in the test identifying which operator was chosen and why.
  severity: medium

- category: architecture
  insight: Two geometry nodes with identical widths (e.g. FusionFloor and MiniBossFloor both 25 m) cannot be differentiated by a strict width comparison. A spec requirement for "arena distinctness" based purely on size.x fails when another zone shares the same dimension. Distinctness must be grounded in positional or contextual criteria, not width alone.
  impact: MBA-GEO-3 was originally framed as "MiniBossFloor is the widest floor segment." FusionFloor is also 25 m, so this argument broke down. The Spec Agent had to reframe distinctness as: dedicated single-enemy zone at a unique positional range with no platforming obstacles — which is a design distinction, not a metric one. The test was changed to assert `size.x >= 25` as a minimum threshold, not a uniqueness claim.
  prevention: Specs that argue "structural distinctness" via a single numeric property must verify that no other node in the scene shares that value. If uniqueness cannot be guaranteed by one property, use a positional + contextual distinctness argument and document the combination explicitly. Do not rely on width, height, or size alone as a proxy for "this zone is special."
  severity: medium

### Anti-Patterns

- description: Using `get_path()` on unparented nodes to assert node identity distinctness. All unparented nodes return `""`, making pairwise inequality tests pass vacuously.
  detection_signal: A test file calls `.get_path()` on nodes that are loaded from a PackedScene but not inserted into a SceneTree via `add_child()`.
  prevention: Replace `get_path()` distinctness checks with `.name` checks for headless-loaded nodes. If path-based testing is required, insert nodes under a temporary root before calling `get_path()`.

- description: Asserting zone non-overlap with strict `>` when the scene author intentionally places zones as adjacent (touching boundary). The correct intent is "not overlapping," which maps to `>=`, not `>`.
  detection_signal: A test assertion computes two zone edges and uses strict `>` to compare them; the test fails even though the scene geometry appears correct by inspection.
  prevention: The Spec Agent must state the intended spatial relationship precisely ("touching allowed" vs. "gap required") and choose the operator accordingly in the test specification. Use `>=` for "adjacent or gapped," `>` only for "strict gap required."

### Prompt Patches

- agent: Test Design Agent
  change: Never use `node.get_path()` to assert that two nodes are distinct when those nodes are loaded from a PackedScene without being added to a SceneTree. Use `node.name` for distinctness checks in headless tests. If path comparison is required, add the node to a temporary SceneTree root first and verify `get_path() != NodePath("")` before comparing.
  reason: `get_path()` on unparented nodes always returns `""`. Pairwise `!=` checks between two empty NodePaths pass unconditionally, giving a false sense of coverage. This caused T-57's distinctness assertions to be trivially vacuous until caught at integration time.

- agent: Spec Agent
  change: When writing a spatial non-overlap assertion between two adjacent zones, state explicitly whether a gap is required or whether touching boundaries are acceptable. Use `>=` in the test formula when touching is acceptable; use `>` only when a non-zero gap is a design requirement. Document the boundary value and chosen operator in the spec's test traceability table.
  reason: ADV-MBA-06 used `>` for a touching boundary (both edges == 55.0), causing a test failure that was a spec error, not a scene error. The operator choice encodes a design intent that must be explicit.

- agent: Spec Agent
  change: Before asserting that a node's geometry property (size.x, height, width) makes it structurally unique in the scene, grep the .tscn for all nodes of the same type and confirm the property value is not shared. If another node shares the value, reframe the distinctness argument using position, context, or combination of properties rather than the single metric.
  reason: MiniBossFloor and FusionFloor both have size.x == 25 m. The original MBA-GEO-3 "widest floor" argument was invalid and had to be replaced with a positional/contextual distinctness argument after the Spec Agent discovered the collision.

### Workflow Improvements

- issue: Two bugs (T-57 get_path() and ADV-MBA-06 strict >) were not caught at spec or test-design time — they were only surfaced by the Engine Integration Agent running the full suite. Both were caused by incorrect assumptions that could have been verified during spec or test-design with access to the .tscn file.
  improvement: The Test Design Agent should validate operator choices and comparison subject types against the live .tscn before finalizing test assertions. Specifically: (a) confirm that any node used in a `get_path()` call will be tree-attached at test time, and (b) verify exact boundary values from the scene file before choosing `>` vs `>=` for spatial assertions.
  expected_benefit: Catches the class of "vacuously correct" assertion errors and off-by-one operator errors in the test-design phase rather than at integration, eliminating a round-trip fix cycle.

### Keep / Reinforce

- practice: ADV-MBA-08 used a dual-assertion strategy: (1) exact expected name assertions (catching Godot auto-dedup renames) and (2) pairwise mutual distinctness assertions. This exposes the root cause (wrong name) separately from the symptom (duplicated name).
  reason: Single "all distinct" assertions mask which specific node was renamed. The two-tier approach (exact names + pairwise) provides both regression protection and precise failure attribution. Reinforce this pattern for all tickets requiring N distinct named instances.

- practice: The Engine Integration Agent resolved both bugs (T-57 operator, ADV-MBA-06 operator) with minimal, well-reasoned changes — switching `.get_path()` to `.name` and `>` to `>=` — without altering scene geometry or expanding test scope beyond the specific failure.
  reason: Fixing test logic errors at the integration phase rather than reverting to spec or restructuring the suite kept the ticket on track. Constraining fixes to the smallest correct change is the right default behavior for integration-phase corrections.

---

## [mutation_tease_room] — Clean run: prior learnings applied successfully (zone adjacency <=, .name not get_path()). No new significant learnings.

*Completed: 2026-03-20*

All 18 tests (T-63–T-72, ADV-MTR-01–ADV-MTR-06) passed first run with zero scene modifications. Ticket held at INTEGRATION pending human verification of AC-2 (visual tease clarity) and AC-5 (human-playable in-editor).

The two lessons from [mini_boss_encounter] were correctly applied by downstream agents before any failure occurred:

- **Zone adjacency `<=`**: T-69 and MTR-FLOW-1 used `<=` from the start (MutationTeaseFloor right edge = 10.0, FusionFloor left edge = 10.0 — touching boundary). No operator correction was needed at integration time. The spec explicitly documented the boundary value and operator choice.
- **`.name` not `get_path()`**: T-70 and ADV-MTR-04 used `node.name` for all four-enemy distinctness checks from the start. NFR-6 in the spec codified this rule. No vacuous-pass bug occurred.

Both fixes were applied at the spec phase (before test design), not discovered at integration. This is the correct phase for such corrections.

---

## [start_finish_flow] — Headless structural wiring proxies passed; subjective playability still gated on manual evidence

*Completed: 2026-03-20*

### Learnings
- category: testing
  insight: When a ticket relies on a conservative assumption about what gates completion (e.g., `LevelExit` should be unconditional and not depend on `EnemyMiniBoss` defeat), encode the assumption as an anti-gating structural test by parsing the level `.tscn` text and asserting both the positive trigger wiring and the absence of forbidden identifiers in the `LevelExit` inline script section.
  impact: Prevents a "structurally wired but logically blocked" failure mode where headless tests can pass even though runtime completion would hang until a hidden condition is met.
  prevention: For every acceptance-criteria assumption of the form "X should NOT be gated on Y", require a test that asserts the negative by static analysis (forbidden identifier absence) in addition to the positive wiring assertion.
  severity: high

- category: testing
  insight: Headless UI/signposting tests need coverage for verb-specific input hints for critical gameplay actions; asserting only prompt label existence and generic movement hints is insufficient to de-risk player misunderstanding.
  impact: `start_finish_flow` infection UI validation checks prompt labels and a generic hints set, but the original planning risk ("no explicit infect key hint") remained structurally under-validated, leaving AC-2/AC-5 vulnerable to confusion even when headless structural tests pass.
  prevention: Add a structural requirement for the critical verb's hint node (e.g. `InfectHint` under `InfectionUI/Hints`, or a text contract inside an existing hint label) and assert it headlessly.
  severity: medium

- category: process
  insight: A capability matrix in headless test files (explicitly stating what the suite can vs cannot verify relative to acceptance criteria) materially reduces "false confidence" and triage time when integration issues are still manual-only.
  impact: `test_start_finish_flow.gd` documents that it cannot prove human completion time or input-driven play, which keeps reviewers from assuming automated coverage extends to subjective ACs.
  prevention: For any headless integration test suite, require a short header that maps: (a) AC components you can deterministically verify, and (b) the specific AC components that remain manual-only.
  severity: low

### Anti-Patterns
- description: Treating "UI node exists in the scene" as proof of flow clarity.
  detection_signal: Structural UI tests check node existence and/or default visibility but do not require verb-specific input hint nodes or any deterministically testable link between gameplay verb and hint content.
  prevention: For each critical gameplay verb in the flow, assert the presence and implementation of the corresponding hint label in the relevant UI subtree (headless-safe).

- description: Encoding completion-trigger assumptions only in prose without a negative assertion in tests.
  detection_signal: Ticket/spec text includes "we assume completion is triggered by X and not gated by Y", but the test suite only asserts the positive wiring of X without forbidding references to Y.
  prevention: Add a static anti-gating test that checks the `X` trigger script section does not reference `Y` identifiers (or the specific state variables), in addition to the positive trigger wiring assertion.

### Prompt Patches
- agent: Test Design Agent
  change: "For any conservative assumption about completion triggers or gating (e.g. `LevelExit` completion is unconditional and must not depend on mini-boss defeat state), add an anti-gating structural test that statically parses the relevant `.tscn` (or attached inline script source) and asserts (1) positive wiring for `level_complete`/the expected trigger handler and (2) absence of forbidden identifiers (e.g. `miniboss`, `enemymonster`, `EnemyMiniBoss`, or any explicitly forbidden node/group/state names) within the completion trigger script section."
  reason: Positive wiring assertions alone can pass while runtime completion is still logically blocked by unintended state gating.

- agent: Test Design Agent
  change: "For any headless UI/signposting validation that targets flow clarity for critical gameplay verbs (infect/absorb/fuse/etc.), require verb-specific input hints under the relevant UI container (e.g. `InfectionUI/Hints`) and assert headlessly that each required hint node exists and is implemented via the standard input-hint label script (or matches an agreed text contract). Do not rely on generic move/jump hints to cover verb discoverability."
  reason: It is possible for structural UI tests to pass while the specific verb the player must perform remains under-specified or undiscoverable.

- agent: Test Design Agent
  change: "At the top of every headless integration test file, add a brief capability matrix comment listing what the suite can verify deterministically vs what remains manual-only relative to the ticket's acceptance criteria."
  reason: Prevents reviewers from assuming automated gates cover subjective AC aspects (time, comprehension, input-driven success).

### Workflow Improvements
- issue: Integration tickets can become blocked with "headless suite passed" while the remaining subjective AC components are not clearly mapped to which parts are verified vs manual-only.
  improvement: Require every integration ticket status update to include an explicit mapping from each AC to either (a) the specific automated test(s) that validate its deterministic proxy, or (b) the exact manual-only sub-steps that must be recorded.
  expected_benefit: Reduces ambiguity and review churn when tickets hit INTEGRATION but still require human evidence.

### Keep / Reinforce
- practice: Use a negative/anti-gating assertion by parsing the level `.tscn` text to ensure completion wiring does not reference forbidden mini-boss identifiers.
  reason: This catches the "looks wired but is logically blocked" failure mode without needing runtime input simulation.

- practice: Validate UI signposting structurally (prompt label presence + hint subtree existence + default visibility expectations) even when the human-playable AC cannot be fully automated.
  reason: This reduces the search space for manual verification by ruling out missing UI nodes as a first-order failure cause.

---

## [soft_death_and_restart] — 21 SDR-* tests passing; ticket at INTEGRATION pending scene wiring and human visual verification.

*Completed (headless phase): 2026-03-21*

### Learnings

- category: testing
  insight: In Godot 4.6.1 headless mode, `global_position` getter and setter are unreliable on CharacterBody3D nodes even when the node is added to a Node3D scene tree via `add_child()`. The property appears to read/write a stale or zero transform. `position` is fully reliable in the same context when the parent node has an identity transform (position == global_position when parent = identity).
  impact: SDR-CORE-6 (`reset_position()` asserts player position equals spawn position) required a fallback from `global_position` to `position`. If undetected, the test would have passed vacuously (global_position always returning Vector3.ZERO, matching a zero spawn point), masking a real implementation defect.
  prevention: In headless tests that verify node position after a reset, always use `position` when the parent's transform is identity. Never use `global_position` in headless test assertions for CharacterBody3D or similar physics nodes. Document this in a comment in the test file.
  severity: high

- category: testing
  insight: GDScript 4.6.1 lambda capture semantics for primitive types (`bool`, `int`, `float`) prevent lambdas from updating outer local variables. A lambda like `func(): fired = true` captures the value of `fired` at creation time — it does not hold a reference to the outer variable. The outer variable is never mutated.
  impact: Pre-existing RSM-SIGNAL-* tests in `test_run_state_manager.gd` use this pattern to assert signal emission by checking a `fired` bool after `await`. All 7 RSM-SIGNAL-* tests fail for this reason — not because RunStateManager is broken. These failures were misread as regressions when first encountered during the SDR ticket, causing diagnostic effort before the root cause was confirmed as a known GDScript limitation.
  prevention: Never use `func(): local_bool = true` to test signal emission in GDScript 4. Use a counter on an Object (`class Counter extends RefCounted: var n = 0`) or connect to a method on a RefCounted that mutates an array/dict (reference types are captured by reference). Document this constraint in the Test Design Agent prompt.
  severity: high

- category: testing
  insight: Calling `.free()` on a RefCounted object generates a "Can't free a RefCounted object" runtime error in Godot. In `test_run_state_manager.gd`, `rsm.free()` was called in teardown despite RunStateManager extending RefCounted. The error fires after test assertions and therefore does not flip any test from pass to fail, but it pollutes output and delays diagnosis of real failures.
  impact: Noise in test output caused confusion during SDR ticket integration phase when 7 pre-existing failures appeared alongside this error. The error had appeared in prior runs but was not cleaned up, compounding across tickets.
  prevention: Static QA Agent must flag any `.free()` call in test files where the freed object's class extends RefCounted (not Object). This pattern was already documented in [fusion_opportunity_room] learnings but the existing test file was not corrected. Add a one-time cleanup task for `test_run_state_manager.gd` teardown.
  severity: medium

- category: architecture
  insight: RSM's internal MutationSlotManager and the scene InfectionInteractionHandler's MutationSlotManager are separate object instances with independent state. A reset that calls `rsm.apply_event("restart")` only clears RSM's internal slot manager; the handler's slots remain dirty until explicitly cleared via `handler_node.get_mutation_slot_manager().clear_all()`.
  impact: This caused a spec-phase escalation. If the coordinator had only cleared the RSM internal instance, mutation UI would have appeared empty to the logic layer but visually populated to the player after restart. The Spec Agent caught and resolved this before any test was written.
  prevention: When a feature creates multiple instances of the same service class (e.g. slot manager) with no shared reference, document all instance boundaries explicitly in the spec's Architecture section. Any "reset" or "clear" operation must enumerate which instances it touches — not just the one accessible through the primary coordinator path.
  severity: medium

- category: process
  insight: Ticket revision numbers reaching 6+ with INTEGRATION-blocking issues remaining at scene-wiring (Engine Integration Agent not yet invoked) indicate a workflow sequencing gap. The headless phase completed correctly but the ticket has no mechanism to automatically hand off to the Engine Integration Agent; it waits in INTEGRATION status with a documented "Next Responsible Agent" that must be invoked externally.
  impact: SDR ticket is structurally complete at headless scope but not progressing. Human visual verification cannot begin until scene wiring is done, and scene wiring cannot begin until the Engine Integration Agent is invoked. Each waiting step adds latency with no automated trigger.
  prevention: When a ticket's NEXT ACTION names a specific agent, the Acceptance Criteria Gatekeeper should explicitly tag the ticket for that agent's queue rather than leaving it in a generic INTEGRATION status. The project board should distinguish "INTEGRATION — waiting for Engine Integration Agent" from "INTEGRATION — waiting for human."
  severity: low

### Anti-Patterns

- description: Using `global_position` in headless CharacterBody3D tests to assert reset behavior. The property is unreliable in headless mode even with a valid scene tree parent.
  detection_signal: A test for a position-reset method asserts `node.global_position == expected_vector` on a CharacterBody3D that was added to a Node3D root, but the assertion always passes even with the reset logic commented out.
  prevention: Replace `global_position` with `position` in headless position assertions when the parent has an identity transform. Add a comment citing Godot 4.6.1 headless compatibility as the reason.

- description: Lambda-based signal detection (`func(): fired = true`) for bool variables in GDScript 4.6.1. The lambda captures the primitive value, not a reference to the outer variable. Signal emissions are silently missed.
  detection_signal: A test asserts `assert(fired == true)` after `await some_signal` but the assertion fails intermittently or always, even though the signal is confirmed to be emitted by other means.
  prevention: Use a reference-type counter (RefCounted with a field, or an Array with one element) for signal detection in lambdas. Never use a bare bool/int local variable as the capture target.

### Prompt Patches

- agent: Test Design Agent
  change: "In headless tests that assert node position after a reset, use `node.position` instead of `node.global_position` for CharacterBody3D nodes. `global_position` getter and setter are unreliable in Godot 4.6.1 headless mode even when the node is added to a Node3D parent. This equivalence holds when the parent has an identity transform. Add a comment: # global_position unreliable in headless (Godot 4.6.1); use position when parent = identity."
  reason: SDR-CORE-6 required this fallback at test-write time. Without this rule, position tests pass vacuously in headless mode, masking real implementation defects.

- agent: Test Design Agent
  change: "Never use a `bool`, `int`, or `float` local variable as the capture target in a GDScript lambda to detect signal emission. GDScript 4.6.1 lambdas capture primitive types by value, not by reference. The outer variable is never mutated. Use instead: `var counter = [0]` (array) and `func(): counter[0] += 1` inside the lambda, then assert `counter[0] == expected_count`."
  reason: RSM-SIGNAL-* failures in test_run_state_manager.gd are all caused by this exact pattern. 7 tests are permanently broken because of it. The fix is a one-line pattern change.

- agent: Static QA Agent
  change: "When reviewing test files, flag any `.free()` call where the target object's class (or its ancestor) extends RefCounted. RefCounted objects must not be manually freed. Add a Static QA check: grep test files for `.free()` and verify the freed object's class hierarchy. Report any RefCounted `.free()` call as a defect even if it does not flip test pass/fail."
  reason: RefCounted `.free()` errors are non-fatal but generate persistent noise in test output that obscures real failures. The error has appeared across multiple tickets without being cleaned up.

### Workflow Improvements

- issue: The ticket reached INTEGRATION state with headless coverage complete, but no automated mechanism exists to invoke the Engine Integration Agent. The "Next Responsible Agent" field in the ticket is documentation only — it does not trigger any action.
  improvement: When a ticket transitions to INTEGRATION with a named Next Responsible Agent, the project board workflow should create an explicit task entry or flag in the agent queue for that agent. The distinction between "waiting for Engine Integration Agent" and "waiting for human" should be reflected in the ticket's Stage field (e.g. INTEGRATION:engine-wiring vs INTEGRATION:human-verification).
  expected_benefit: Prevents tickets from sitting in INTEGRATION indefinitely with completed headless coverage. Reduces latency between headless completion and scene wiring.

- issue: Pre-existing test failures (RSM-SIGNAL-*) in sibling test files were encountered during the SDR integration run and required diagnostic effort to confirm they were pre-existing and unrelated, not regressions introduced by SDR changes.
  improvement: The test runner output should include a comparison against a known-failing baseline list. Pre-existing failures should be annotated as such in the run report so the Integration Agent does not need to re-diagnose them on each ticket. The known-failing list should be maintained in a file (e.g. `tests/known_failures.txt`) with a brief note per entry.
  expected_benefit: Eliminates recurring diagnostic effort for the same pre-existing failures. Keeps Integration Agent focus on net-new failures only.

### Keep / Reinforce

- practice: The coordinator node uses a `_dead` flag guard on the death detection path to prevent double-fire when `_on_player_died()` is called from both the polling path and an external caller during the same frame.
  reason: Without the guard, two rapid HP=0 frames could trigger two restart cycles, resulting in corrupted state. The double-fire guard was explicitly tested (SDR-CORE-8 / ADV-SDR-01) and passed. This pattern should be reused in any state transition coordinator that detects conditions via polling.

- practice: The ticket explicitly staged the visual (tween/dissolve) work as Part 2 after the core logic was verified headlessly, and the integration test plan enumerated exactly which ACs are headless-testable vs human-only. This clean separation prevented wasted effort automating unautomatable criteria.
  reason: Consistent with the pattern established in [fusion_opportunity_room] and [light_skill_check]. The separation is working and should be enforced as a default for all tickets with mixed headless/visual ACs.

---

## [room_template_system] — 5 room .tscn files authored; all primary RTS-* tests pass; RTS-ADV-16 revealed a test design defect in recursive node-name counting.

*Completed (headless phase): 2026-03-21*

### Learnings

- category: testing
  insight: Recursive scene-tree searches for a node-name substring (e.g. `find_nodes("*Enemy*")`) false-positive when instanced sub-scenes contain child nodes whose names also match the substring. In this ticket, `enemy_infection_3d.tscn` has a child named `EnemyVisual`; a recursive count of "Enemy" in the room tree returned 2 instead of the expected 1 per combat/boss room.
  impact: RTS-ADV-16 failed for all 4 rooms that contain enemies. The rooms were correctly authored per spec; the defect was entirely in the test. This was not caught by the Test Designer Agent because the internal structure of the enemy sub-scene was not examined before writing the count assertion.
  prevention: When writing node-count assertions for instanced sub-scenes, restrict the search to direct children of the query root (e.g. iterate `root.get_child(i)` and check name, rather than using `find_nodes` or recursive `get_all_children`). Before finalizing a count assertion, inspect the target sub-scene to identify any child nodes whose names would match the search pattern.
  severity: high

- category: testing
  insight: The RTS-ADV-6 collision_mask check was correctly scoped to direct StaticBody3D children of the room root (not a full recursive walk) because the enemy sub-scene has its own StaticBody3D nodes with a different collision_mask contract. The spec's risk note explicitly governed over the general "every StaticBody3D in the tree" language in the acceptance criteria.
  impact: If the full recursive walk had been used, every room with an enemy would have generated a false failure on RTS-ADV-6 because the enemy's collision layers differ from the floor's. The correct direct-child scoping was used and all RTS-ADV-6 assertions passed.
  prevention: Any spec that mixes room-geometry nodes with instanced enemy sub-scenes must explicitly state whether structural assertions (collision_mask, node type, count) apply to the full tree or only to direct children. The risk note takes precedence; the Test Design Agent must read spec risk notes before writing structural count or property assertions.
  severity: medium

- category: architecture
  insight: Instanced sub-scenes introduce invisible child nodes into the parent scene's runtime tree. Node names, collision properties, and script attachments from the sub-scene's interior are present at runtime even though they are not authored as direct children of the parent. Test assertions that assume a flat tree silently include these inherited nodes.
  impact: Across this ticket and prior ones, the sub-scene interior has caused false failures in count assertions, collision assertions, and name-substring checks. The pattern recurs whenever a new sub-scene type is introduced.
  prevention: When authoring tests for any scene that instances a sub-scene, first enumerate the sub-scene's complete node tree and identify all nodes whose properties (name, type, script, collision_mask) could satisfy a search condition intended only for the parent scene's own nodes. Explicitly scope all assertions to the correct tree depth.
  severity: high

- category: process
  insight: The Test Designer Agent used `FileAccess.open` + text substring search on the .tscn source file to verify enemy scene path (RTS-ENC). This is the only headless-safe method since no runtime API exposes an instanced node's source .tscn path. The approach was explicitly recommended by the spec and worked correctly.
  impact: RTS-ENC-2 through RTS-ENC-5 all passed in green phase. The file-text approach is deterministic and does not require physics ticks or scene tree wiring.
  prevention: Document this pattern as the canonical approach for verifying instanced sub-scene identity in headless tests. Do not attempt to infer scene path from runtime node properties (class name, script methods) — these are indirect and can be shared across scene variants.
  severity: low

### Anti-Patterns

- description: Using `find_nodes("*Substring*")` or any recursive name-search to count expected nodes when the target nodes are instances of a sub-scene that has children with overlapping name patterns.
  detection_signal: A count assertion for N expected instances of a node type returns N*K where K > 1 — the extra counts come from children inside the sub-scene's interior. The rooms are correctly authored but the test fails.
  prevention: Replace `find_nodes` with a direct-child iteration (`for i in root.get_child_count(): var c = root.get_child(i)`) and apply the name/type filter only at depth 1. Add a comment explaining the scope restriction and which sub-scene prompted it.

- description: Writing structural property assertions (collision_mask, node type, count) for scenes with instanced sub-scenes without first auditing the sub-scene's internal node tree.
  detection_signal: A test passes in isolation when the sub-scene is absent but fails after the sub-scene is instanced into the parent. The test failure message shows unexpected extra nodes or unexpected property values that were not authored in the parent scene.
  prevention: Before finalizing any structural test for a scene that instances sub-scenes, open each sub-scene and list all nodes at all depths. Tag which assertions need depth scoping. This step takes under 2 minutes and prevents rework.

### Prompt Patches

- agent: Test Design Agent
  change: "Before writing any `find_nodes`, recursive tree walk, or node-count assertion for a scene that instances sub-scenes, read each sub-scene file and list its complete node tree. If any child node's name, type, or property would satisfy the search condition, restrict the assertion to direct children only using `root.get_child(i)` iteration instead of `find_nodes`. Add a comment explaining the depth restriction and citing the sub-scene that prompted it."
  reason: RTS-ADV-16 failed for 4 rooms because the Test Designer Agent did not inspect `enemy_infection_3d.tscn` before writing the recursive "Enemy" substring count. The rooms were correctly authored; only the test was wrong. This added a blocker that required escalation to the Acceptance Criteria Gatekeeper.

- agent: Test Design Agent
  change: "To verify that a room scene instances a specific sub-scene (e.g. an enemy), use `FileAccess.open(room_path, FileAccess.READ).get_as_text()` and check for the sub-scene filename as a substring. Do not attempt to infer sub-scene identity from runtime node class names, script methods, or exported properties — these are indirect and non-deterministic. Call this pattern 'file-text scene-path verification'."
  reason: There is no runtime API in Godot 4 that returns an instanced node's source .tscn path. The file-text approach is the only headless-safe, deterministic method confirmed to work in this project.

- agent: Spec Agent
  change: "For every structural assertion in a spec (count, property, collision_mask), explicitly state the tree depth scope: 'direct children of room root only' or 'full recursive tree'. When the assertion targets parent-scene nodes that could be confused with sub-scene interior nodes, mandate direct-child-only scope in the test requirement and add a risk note naming the sub-scene and its conflicting child node names."
  reason: RTS-ADV-6 was correctly scoped because the spec's risk note explicitly governed; RTS-ADV-16 was not because the spec lacked an explicit depth scope for the enemy count. Explicit scoping in the spec prevents the Test Design Agent from defaulting to recursive search.

### Workflow Improvements

- issue: The Test Designer Agent wrote RTS-ADV-16 with a recursive count assertion without auditing the enemy sub-scene structure. This was only discovered after Engine Integration authored all 5 rooms and ran the full test suite — late in the pipeline.
  improvement: Add a mandatory pre-write step to the Test Design Agent workflow: for each test involving an instanced sub-scene, read the sub-scene file and enumerate its node tree before writing the assertion. This should be documented as a checklist item in the Test Design Agent prompt, not left to judgment.
  expected_benefit: Catches the recursive-count false-positive pattern before any implementation work begins. Eliminates a class of test design defects that only surface at green-phase validation.

- issue: RTS-ADV-16's test design defect required escalation to the Acceptance Criteria Gatekeeper Agent to resolve. Neither the Test Designer nor the Engine Integration Agent had authority to fix the test (Engine Integration must not modify existing files; Test Designer had already handed off). This created an unnecessary escalation step for a simple fix.
  improvement: Define a "test defect fix" authority rule: if a test assertion is demonstrably wrong (not an implementation issue), the Acceptance Criteria Gatekeeper Agent is authorized to fix the test directly without a full re-run of the Test Design Agent. Document this authority in the Acceptance Criteria Gatekeeper Agent prompt.
  expected_benefit: Reduces escalation latency. A one-line fix to a broken assertion should not require re-invoking the full Test Design Agent pipeline.

### Keep / Reinforce

- practice: Using `FileAccess.open` + text substring search on the .tscn source file to verify enemy scene path in headless tests (RTS-ENC). No runtime API equivalent exists; this is the only deterministic method.
  reason: RTS-ENC-2 through RTS-ENC-5 passed cleanly. The pattern is reusable for any ticket that needs to verify which sub-scene is instanced inside a room or level .tscn file without running physics.

- practice: Scoping collision_mask assertions to direct children of the room root only, not the full recursive tree, when the room contains instanced enemy sub-scenes with their own collision layer contract.
  reason: RTS-ADV-6 passed for all 5 rooms because of this correct scoping. Had the recursive walk been used, every room with an enemy would have generated a false failure. Direct-child scoping is the safe default for any room-geometry structural assertion.

---

## [BPG] — Read existing infrastructure before planning; reviewer catches copy-paste geometry bugs; AC Gatekeeper requires filesystem access
*Completed: 2026-03-24*

### Learnings

- category: process
  insight: Autopilot ran three full pipeline stages (Planner, Spec, Test Designer) on blender_parts_library before discovering the pipeline already existed in asset_generation/python. The root cause was that the Planner Agent did not read the existing directory structure before generating a plan. READMEs and existing source trees are the ground truth for "what already exists" — not the ticket description.
  impact: Stale spec and test artifacts were generated and then deleted. Three agent stages of work were wasted. The ticket had to be rewritten entirely.
  prevention: The Planner Agent must read the project's relevant directory tree and any README before authoring a plan for a ticket that involves adding to an existing system. If a README exists, it must be read first.
  severity: high

- category: testing
  insight: The Code Reviewer caught 9 critical geometry bugs (copy-paste errors, wrong primitive parameters) in AnimatedClawCrawler and AnimatedCarapaceHusk. These bugs would have silently produced wrong GLB outputs because Blender does not error on malformed geometry — it simply renders incorrectly. The pure-Python test suite could not catch them because tests were isolated from bpy and only verified structural registration, not rendered output.
  impact: If the reviewer stage had been skipped, 6 of 9 GLBs would have had incorrect geometry shipped to the game pipeline with no automated signal of failure.
  prevention: For code that generates binary assets (GLBs, blend files, images), the reviewer stage is mandatory even when all pure-Python tests pass. Test isolation from the rendering backend (bpy stubs) creates a coverage gap for geometry-correctness — reviewer inspection is the only in-pipeline safeguard before generation.
  severity: high

- category: infra
  insight: The AC Gatekeeper Agent issued a false BLOCKED verdict because it ran in a sandboxed context where it could not see GLB files that were confirmed on disk. The Gatekeeper was checking for file existence as part of AC verification, but its filesystem access was restricted. This produced a false negative that required orchestrator override.
  impact: A false BLOCKED created an unnecessary override step and undermined confidence in the Gatekeeper's verdict. If the override mechanism did not exist, the ticket would have stalled.
  prevention: The AC Gatekeeper must not issue a BLOCKED verdict based solely on file-not-found results when its filesystem access is sandboxed or restricted. It should log the access limitation as a CHECKPOINT and request human confirmation for filesystem-dependent ACs, rather than treating a failed file lookup as an AC failure.
  severity: high

- category: process
  insight: The blender_parts_library ticket described work that had already been done differently. The ticket backlog was based on an outdated picture of the codebase — the pipeline had been built independently of the ticket system. No agent checked whether the ticket's described deliverables already existed before starting pipeline execution.
  impact: Wasted three agent stages, required a ticket rewrite, and produced artifacts that had to be cleaned up. Discovery only happened when the Orchestrator intervened mid-run.
  prevention: Add a mandatory "existence check" step at the start of any implementation run: before the Planner Agent runs, verify that the primary deliverable files listed in the ticket's "Files to Modify / Create" section do not already exist with conflicting content. If they do, flag for human review before proceeding.
  severity: critical

### Anti-Patterns

- description: Planning and speccing a system that already exists. The pipeline proceeded through three stages generating plans and tests for blender_parts_library without any agent confirming whether the described pipeline was already present in the codebase.
  detection_signal: Ticket describes creating files that already exist in the codebase at the named paths, OR ticket describes functionality that is already exercised by existing tests.
  prevention: Planner Agent must run a targeted file existence check on all "Files to Create" entries before authoring any plan. If a named file already exists, halt and log a CHECKPOINT before proceeding.

- description: Using bpy stubs in pure-Python tests creates a false sense of test coverage for geometry-producing code. All structural tests pass even when the underlying Blender calls contain copy-paste bugs that produce visually wrong output.
  detection_signal: Test suite achieves full pass rate against bpy-mocked classes, but no test exercises actual rendered geometry dimensions or primitive parameter values.
  prevention: For each new enemy class or Blender geometry generator, require at least one source-inspection test (via inspect.getsource) that asserts the specific primitive type and scale parameters expected — not just that the method exists.

- description: AC Gatekeeper treating a file-not-found lookup failure as an AC failure when running in a restricted/sandboxed environment. The absence of a file in the Gatekeeper's view does not mean the file is absent on disk.
  detection_signal: AC Gatekeeper issues BLOCKED for a filesystem-existence AC, but there is no corroborating evidence (e.g., no build error, no generation error logged) that the file was not produced.
  prevention: AC Gatekeeper should cross-reference filesystem AC failures against the implementation agent's own logged evidence. A BLOCKED verdict for a file-existence AC requires at least one corroborating source beyond the Gatekeeper's own lookup.

### Prompt Patches

- agent: Planner Agent
  change: "Before authoring any plan for a ticket that adds to an existing system, read the project's relevant directory tree and any README file in that directory. If the README or existing source files describe functionality that overlaps with the ticket's deliverables, log a CHECKPOINT before proceeding. Do not generate a plan that assumes the described pipeline does not exist without first verifying."
  reason: The blender_parts_library autopilot ran 3 full stages before discovering the pipeline already existed. A pre-plan existence check would have prevented all wasted work.

- agent: AC Gatekeeper Agent
  change: "When verifying a filesystem-existence AC (e.g., 'file X exists on disk'), do not issue BLOCKED solely based on a failed file lookup. If your environment may be sandboxed or have restricted filesystem access, log the limitation as a CHECKPOINT and request human confirmation. A file-not-found result is only a valid BLOCKED signal if the implementation agent's own output also reported a generation failure."
  reason: The AC Gatekeeper issued a false BLOCKED for GLB file presence because it could not access the filesystem where the files were confirmed to exist. This required orchestrator override and undermined trust in the Gatekeeper verdict.

- agent: Code Reviewer Agent
  change: "For any code that invokes Blender geometry primitives (primitive_sphere_add, primitive_cylinder_add, primitive_cube_add, etc.), inspect each call site for copy-paste errors: verify that parameter values (radius, vertices, scale) are semantically correct for the named body part, not carried over from a similar-looking method in an adjacent class. Flag any call where the parameter values are identical to those in a sibling class that represents a visually distinct enemy part."
  reason: 9 geometry bugs in AnimatedClawCrawler and AnimatedCarapaceHusk were copy-paste errors where primitive parameters were not updated from the source class. The Reviewer catching these before GLB generation was the only in-pipeline safeguard.

### Workflow Improvements

- issue: No pipeline step verified whether the primary deliverables of a ticket already existed before Planner, Spec, and Test Designer ran. The discovery that blender_parts_library was superseded happened only when the Orchestrator intervened mid-run after three wasted stages.
  improvement: Add a pre-flight existence check as step 0 of autopilot execution for any ticket with a "Files to Create" section. The Orchestrator should confirm that the named files do not already exist with conflicting content before handing off to the Planner Agent. If they do, the ticket should be flagged NEEDS_REVIEW before any agent runs.
  expected_benefit: Prevents multiple agent stages of wasted work when the codebase has diverged from the ticket backlog. Saves time and eliminates stale artifact cleanup.

- issue: The AC Gatekeeper cannot reliably verify filesystem-existence ACs when running in a sandboxed context, but it issues definitive verdicts (BLOCKED) regardless. There is no mechanism for the Gatekeeper to signal "I could not verify this AC due to environment limitations."
  improvement: Add a CANNOT_VERIFY verdict state to the AC Gatekeeper's vocabulary. When a filesystem check fails in a context where sandbox restrictions may be present, the Gatekeeper issues CANNOT_VERIFY with a note, rather than BLOCKED. The Orchestrator then routes CANNOT_VERIFY items to human confirmation before deciding to block.
  expected_benefit: Eliminates false BLOCKED verdicts caused by environment restrictions. Keeps the BLOCKED signal meaningful — reserved for cases where the Gatekeeper has positive evidence of failure.

### Keep / Reinforce

- practice: Having the Code Reviewer Agent inspect Blender geometry generator classes before GLB generation runs. In this ticket, 9 critical bugs were caught that pure-Python tests could not detect due to bpy stub isolation.
  reason: Blender geometry code has a silent-failure mode: wrong primitive parameters produce wrong shapes but no error. The reviewer is the only agent in the pipeline that reads the source holistically and can catch copy-paste parameter errors across sibling classes.

- practice: Using inspect.getsource() in pure-Python tests to verify structural properties of bpy-dependent methods without invoking Blender. This is the correct tool for asserting that a method references a particular primitive type or key string when bpy is mocked.
  reason: BPG test suite used this pattern successfully for apply_materials and class registration checks. It provides meaningful structural coverage that complements the bpy-mocked isolation boundary.

---

## [MAINT-TUC] — GDScript 4 static analysis breaks spec-mandated dynamic dispatch; smoke/adversarial infra creates circular-extend trap
*Completed: 2026-03-28*

### Learnings

- category: architecture
  insight: GDScript 4 validates all referenced identifiers at parse time, not at runtime. A base class that references `_pass_count`/`_fail_count` without declaring them fails to load even if every subclass declares those variables. The spec's assumption that "GDScript resolves them via dynamic dispatch at runtime" is incorrect for the current GDScript 4 parser.
  impact: The spec mandated AC-3.1 (no `_pass_count`/`_fail_count` in `test_utils.gd`) and simultaneously required that base class helpers call those variables. The Implementation Agent had to use `get()`/`set()` as a workaround, which itself broke when `Object.set()` on an undeclared property was not retrievable via `Object.get()`. This required a second design pivot — declaring the counters in the base — which directly violated AC-3.1 and forced a spec revision.
  prevention: Before speccing any base class that references variables expected to live in subclasses, verify with a minimal test whether GDScript 4's parser accepts the reference. Do not assume runtime dynamic dispatch applies to identifier resolution at parse time. The safe design is either: (a) declare the variable in the base with a default, or (b) use a virtual getter method pattern (`func _get_pass_count() -> int: return 0`) that subclasses override.
  severity: high

- category: testing
  insight: Smoke and adversarial test files that test the utility file itself cannot extend the utility they are testing. Extending `test_utils.gd` from within `test_utils_smoke.gd` would create a circular dependency that makes the smoke suite responsible for calling `_pass`/`_fail` via the very file it is verifying. These files must `extends Object` and define their own local `_pass`/`_fail` helpers — which means they will appear in the `grep -r "func _pass\b" tests/` output and literally violate the letter of AC-4.1/4.2.
  impact: AC-4.1 and AC-4.2 stated that `func _pass` must appear ONLY in `test_utils.gd`. The smoke/adversarial infrastructure files were a structural exception that made these ACs unverifiable as written. The AC Gatekeeper had to accept this as an "accepted structural exception" rather than a literal pass.
  prevention: When writing ACs for a self-testing utility ticket, anticipate the self-test infrastructure's extends constraint. AC-4.1 should have read: "After migration, no migrated production test file defines `func _pass`. The smoke and adversarial self-test files for `test_utils.gd` itself are exempt as they cannot extend the file they test." The "migrated production test file" scope qualification makes the AC objectively verifiable.
  severity: medium

- category: testing
  insight: GDScript 4 coerces types in Variant equality: `1 == "1"` returns `true`. A test asserting that `_assert_eq(1, "1")` fails (ADV-TU-28) contradicts GDScript's actual behavior. Similarly, IEEE-754 representation of `0.1` means `absf(0.0 - 0.1) <= 0.1` is not reliably true at the boundary — the stored value of `0.1` may be slightly above or below the mathematical value (ADV-TU-32 with the `<=` vs `<` boundary).
  impact: Both ADV-TU-28 and ADV-TU-32 were written based on incorrect assumptions about language and floating-point behavior. They required fixes after the checkpoint logged them as known failures, adding a rework iteration to an otherwise complete implementation pass.
  prevention: For any test that asserts cross-type equality behavior or floating-point boundary conditions, the Test Breaker Agent must verify the assertion against the actual GDScript 4 runtime before publishing the test. The specific rules: (1) `Variant == Variant` coerces ints and strings — never assume an int vs. string comparison fails. (2) For `<=` boundary tests on float literals, use a value that is representable exactly in binary (e.g. `0.5`, `0.25`) rather than a decimal like `0.1` whose IEEE-754 representation introduces rounding uncertainty.
  severity: medium

- category: process
  insight: When a spec is authored before the test files are written, the spec's ACs can be staleness-trapped: the AC text is written against an imagined test that has not been run, making the AC a hypothesis rather than a verifiable contract. ADV-TU-28 and ADV-TU-32 were both hypotheses that turned out to be wrong about the runtime.
  impact: The AC Gatekeeper encountered test failures that were not implementation bugs but were spec/test design errors that should have been caught at the Test Breaker phase. This required a checkpoint entry and explicit documentation that these are "inherent GDScript 4 behavioral properties" rather than bugs.
  prevention: The Test Breaker Agent must run each adversarial test against a known-correct stub implementation before publishing the test suite. A test that is supposed to fail should fail for the right reason. If a test can't be green-verified (e.g., it only makes sense in the red phase), the checkpoint must record its expected failure mechanism and the spec must acknowledge the runtime assumption being tested.
  severity: medium

### Anti-Patterns

- description: Spec asserting counter ownership (no declaration in base) and base-class helpers that reference those counters simultaneously, without verifying that GDScript 4's parser permits undeclared identifier references in base class method bodies.
  detection_signal: A spec AC says "base class MUST NOT declare variable X" and a separate AC says "base class helpers call X." The Implementation Agent files a checkpoint noting the parse failure.
  prevention: These two ACs are contradictory in GDScript 4. The spec must choose: (a) declare X in the base with a default value, or (b) use a virtual method pattern. Mandate the chosen resolution in the spec before implementation begins.

- description: Smoke and adversarial test files for a shared utility are treated as regular migrated test files when checking post-migration grep assertions. The circular-extend constraint forces them to redefine the very functions the production files should have removed.
  detection_signal: Post-migration grep for `func _pass` in `tests/` finds hits in files named `test_*_smoke.gd` or `test_*_adversarial.gd` that are self-testing the utility.
  prevention: Any grep-based AC that enforces function removal must explicitly carve out the self-test infrastructure files. Name the exempt files in the AC text, not in an "accepted structural exception" note added at gatekeeper time.

- description: Adversarial tests that assert GDScript type-coercion behavior without empirical verification of the runtime. Assuming `int != string` in Variant comparison, or assuming a decimal literal boundary behaves as its mathematical value, produces tests that are structurally wrong about the language.
  detection_signal: A test assertion says "this call should fail" for a cross-type comparison (e.g. `_assert_eq(1, "1")` should produce FAIL) but there is no checkpoint confirming this was tested against a running interpreter.
  prevention: Any adversarial test that relies on type system behavior or IEEE-754 edge cases must be empirically verified in a minimal GDScript script before being committed to the test suite.

### Prompt Patches

- agent: Spec Agent
  change: "When designing a base class that provides shared helpers referencing subclass-declared variables, do NOT assume GDScript 4 dynamic dispatch applies at parse time. GDScript 4 validates identifier references at parse time, not at runtime. If a base class method body references a variable (e.g. `_pass_count`) that is only declared in subclasses, the script will fail to load. You must either: (a) declare the variable in the base with a default value and document that subclasses shadow it, or (b) use a virtual accessor method pattern. Do not write ACs that simultaneously prohibit a variable declaration in the base and require that variable to be referenced in base class method bodies."
  reason: The AC-3.1 vs. counter-access contradiction required two checkpoint entries, a `get()`/`set()` workaround that itself failed, and a final design pivot that violated the original AC. A correct spec would have never generated this contradiction.

- agent: Test Breaker Agent
  change: "For any adversarial test that asserts a call should produce a FAIL result based on type mismatch behavior (e.g. int vs. string, float boundary), verify the assertion against a live GDScript 4 interpreter before publishing. Specifically: (1) Do not assume `Variant == Variant` comparisons fail for int vs. string — GDScript 4 coerces them. (2) For floating-point boundary assertions using `<=` or `<`, use only exact binary-representable values (powers of 2 or their fractions) as test inputs. Decimal literals like 0.1 have IEEE-754 representations that make boundary behavior non-deterministic. Record each such verification in CHECKPOINTS.md."
  reason: ADV-TU-28 and ADV-TU-32 were both based on incorrect runtime assumptions. They required a rework iteration that could have been eliminated with a one-minute verification step.

- agent: Spec Agent
  change: "When writing grep-based acceptance criteria that enforce the absence of a function definition (e.g. 'grep for func _pass returns only results from X'), explicitly name every file that is structurally exempt from the rule. Do not rely on an 'accepted structural exception' note added at gatekeeper time. The AC text itself must read: 'After migration, func _pass appears only in test_utils.gd and the following exempt self-test files: [list them].' "
  reason: AC-4.1 and AC-4.2 were technically violated by the smoke/adversarial infrastructure files but declared satisfied via an accepted exception. Had this been written into the AC from the start, the Gatekeeper could have confirmed it objectively rather than issuing a judgment call.

### Workflow Improvements

- issue: The spec's assumption that GDScript 4 permits base-class references to subclass-declared variables was not challenged at any workflow stage before implementation. The Spec Agent published the assumption as a fact; the Test Breaker and Static QA Agents did not verify it; the Implementation Agent discovered the parse failure at implementation time.
  improvement: Add a "GDScript runtime assumptions" verification step to the Static QA Agent's checklist: for any spec that asserts a GDScript language behavior (dynamic dispatch, type coercion, signal capture semantics), require a reference to a concrete checkpoint or prior learnings entry confirming the behavior. If no confirmation exists, the Static QA Agent must file a checkpoint before handing off to the Implementation Agent.
  expected_benefit: Surfaces incorrect language-behavior assumptions before they cause implementation-time rework. Prevents the pattern where a spec's "GDScript will resolve X at runtime" assumption goes unchallenged through three agent stages.

- issue: The post-migration AC verification for "func _pass appears only in test_utils.gd" could not be confirmed by a literal grep because the smoke/adversarial self-test infrastructure files are a structural exception. The Gatekeeper issued a judgment-call pass rather than an objective verification.
  improvement: When a ticket's primary deliverable is a shared utility that must also be self-tested, the Spec Agent must write the self-test infrastructure plan alongside the utility spec — not leave it for the Test Designer to discover. The self-test files' circular-extend constraint is foreseeable at spec time. Specifying it upfront allows the ACs to be written correctly from the start.
  expected_benefit: Eliminates late-stage "accepted structural exception" verdicts. Keeps all AC verifications objective.

### Keep / Reinforce

- practice: The Implementation Agent used `Object.get()`/`Object.set()` as a first attempt to resolve the undeclared-identifier parse error, discovered it did not work for dynamic property creation, filed a detailed checkpoint, and pivoted to declaring the counters in the base. This systematic "attempt → observe → checkpoint → pivot" loop produced a traceable decision history.
  reason: Complex infrastructure tickets with contradictory ACs benefit from explicit checkpoint entries at each design pivot. The checkpoint log for this ticket is a complete audit trail of why the final design differs from the original spec. Future agents working on similar base-class utility infrastructure can read those checkpoints rather than re-discovering the same GDScript 4 constraints.

- practice: Using a `run_all() -> int: return 0` no-op in the shared utility to satisfy the auto-discovery runner without modifying `run_tests.gd`. This required identifying the naming conflict proactively (the CRITICAL Risk note in the execution plan) before any implementation began.
  reason: The runner discovery pattern (`test_*.gd` → call `run_all()`) is a fixed constraint that cannot be changed. Any shared utility file under `tests/` must account for it. Proactive identification and resolution at the planning phase with an explicit no-op is the correct pattern. It should be the standard approach for any future shared infrastructure file placed under `tests/`.

---

## [godot_scene_generator_validation] — Extract pipeline-convention-sensitive logic to testable utilities before integration, not after
*Completed: 2026-03-25*

### Learnings

- category: architecture
  insight: When a naming convention is defined by one pipeline stage (Python asset exporter) and consumed by another (Godot scene generator), the consuming code's parsing assumptions are the most fragile part. Inline private functions are opaque to tests and the first place mismatch hides.
  impact: `_extract_family_name` inside `load_assets.gd` silently produced `"acid_spitter_animated"` instead of `"acid_spitter"` for the entire `_animated_` family of filenames — a naming convention that the Python pipeline introduced but the Godot side was never updated to match. The bug was only discovered when the ticket explicitly required validation against real GLB output.
  prevention: Any function that parses filenames or tokens produced by an upstream pipeline must live in a standalone, headlessly-testable utility class from its first commit. Do not inline parsing logic in @tool or EditorScript classes where it cannot be reached by the test runner.
  severity: high

- category: testing
  insight: `@tool extends EditorScript` classes are structurally untestable in a headless Godot test suite. Any business logic inside them — regardless of how simple — is invisible to automated tests until extracted to a `RefCounted`-based utility.
  impact: Three acceptance criteria (generator runs without errors, .tscn node structure correct, metadata set correctly) were permanently deferred to PENDING_MANUAL because the only entry point is `File > Run` in the Godot editor. There is no headless equivalent.
  prevention: Tickets that involve EditorScript deliverables must explicitly label any AC that depends on editor execution as PENDING_MANUAL from the spec phase, not discovered at gatekeeper time. All logic that can be extracted (parsing, path construction, data mapping) must be extracted, leaving only the editor lifecycle calls inside the EditorScript itself.
  severity: medium

- category: architecture
  insight: Introducing a utility wrapper function (e.g. `_extract_family_name` that only calls `EnemyNameUtils.extract_family_name`) adds a call-site indirection layer with no benefit and creates a code review finding that requires a fix iteration.
  impact: The Code Reviewer flagged the wrapper as unnecessary; the Implementation Agent had to remove it and wire the call site directly. This added a revision pass that would not have existed if the utility had been called directly at the single call site from the start.
  prevention: When refactoring inline logic to an external utility, replace every call site with the direct utility call. Do not preserve a private wrapper function as a "compatibility shim" unless there are multiple call sites that would benefit from a shared local alias.
  severity: low

- category: testing
  insight: The "animated" infix removal algorithm is position-agnostic (removes all segments exactly equal to "animated"), not position-restricted (only removes it when it is the penultimate segment). This is a broader contract than the primary use case suggests, and implementations that use a fixed-offset removal pass the primary suite but fail the adversarial suite.
  impact: Eight adversarial edge cases were required to pin the contract: "animated" as the sole segment, "animated" in prefix position, case-sensitive rejection ("Animated" is not removed), negative trailing integers, and single-segment inputs. Without these, a fixed-offset implementation would have passed all primary tests.
  prevention: For any parsing algorithm, the Test Breaker Agent must enumerate mutation classes: positional assumptions, case sensitivity, boundary segment counts (0, 1, 2), and off-by-one positions. Primary tests cover the happy path; adversarial tests must cover each of these classes explicitly.
  severity: medium

### Anti-Patterns

- description: Pipeline-convention mismatches (where one tool outputs names in format A and a consumer assumes format B) are invisible to unit tests until real pipeline output is used as test fixtures.
  detection_signal: A function parses filenames using a strip/split algorithm but is only tested with manually authored strings that match the expected format, not actual output from the upstream tool.
  prevention: At spec time, examine a representative sample of actual upstream tool output (e.g. the real .glb filenames in `asset_generation/python/animated_exports/`) and include at least one verbatim upstream filename as a primary test case.

- description: Keeping a private wrapper function in the host class after extracting logic to a utility. The wrapper provides no value when there is only one call site and creates a reviewer finding.
  detection_signal: A private function whose entire body is a single delegating call to an external utility function and has exactly one call site in the file.
  prevention: When extracting logic to a utility, inline the utility call directly. Remove the private wrapper in the same commit.

- description: PENDING_MANUAL ACs discovered at gatekeeper time rather than designated at spec time, causing surprise at the end of the ticket workflow.
  detection_signal: An AC that requires editor execution (EditorScript, @tool script, scene generation into the file system) is written as a standard verifiable AC without a PENDING_MANUAL label in the spec's AC table.
  prevention: The Spec Agent must classify each AC by verification method (HEADLESS, MANUAL, SKIPPED_UNTIL) in the AC table. Any AC that depends on `File > Run` in the editor must be labeled MANUAL from the spec phase.

### Prompt Patches

- agent: Spec Agent
  change: "When speccing a ticket that involves a @tool or EditorScript class, classify each acceptance criterion by verification method in the AC table: HEADLESS (runnable in headless test suite), MANUAL (requires running in the Godot editor), or SKIPPED_UNTIL (conditional on prior step). Never write a MANUAL AC without a 'PENDING_MANUAL' label and an explicit escalation note describing who runs it and what to observe."
  reason: Three ACs were discovered to be PENDING_MANUAL only at gatekeeper time. Pre-labeling at spec time prevents surprise deferrals and makes the human's manual verification responsibilities clear from the beginning of the ticket.

- agent: Implementation Agent
  change: "When replacing inline logic with an external utility call, replace every call site with the direct utility invocation. Do not preserve a private wrapper method that solely delegates to the utility. If there is exactly one call site, the wrapper is unnecessary and will be flagged by the Code Reviewer."
  reason: The `_extract_family_name` wrapper finding required an additional review-fix iteration that would not have been needed if the call site had been wired directly to `EnemyNameUtils.extract_family_name`.

- agent: Test Breaker Agent
  change: "For any parsing or string-manipulation function, enumerate these mutation classes before writing adversarial tests: (1) positional assumptions (does the algorithm assume the target segment is at a fixed index?), (2) case sensitivity (does the algorithm handle mixed-case versions of a sentinel string?), (3) boundary segment counts (empty input, single-segment input, two-segment input), (4) sentinel in prefix vs. suffix vs. middle position. Write at least one adversarial test per class unless the spec explicitly excludes the variant."
  reason: The GSV adversarial suite required 8 edge cases to fully pin the `extract_family_name` contract. Without a structured enumeration of mutation classes, it is easy to write adversarial tests that all target the same failure mode while leaving other mutation paths uncovered.

### Workflow Improvements

- issue: The ticket's "Known Issues to Fix" section identified the naming mismatch and the EditorScript testability gap before any agent ran, but these were described as pre-work rather than triggering immediate AC classification (HEADLESS vs MANUAL) at spec time.
  improvement: When a ticket's description includes a "Known Issues" section that mentions @tool, EditorScript, or editor-only workflows, the Spec Agent must classify all dependent ACs as MANUAL at the beginning of spec authoring, before writing any other AC. Do not wait until the AC table is complete to apply classification.
  expected_benefit: Prevents late-stage discovery of PENDING_MANUAL verdicts after three other agents have already run. Surfaces the manual verification scope to the human at the earliest possible point.

- issue: Pre-existing parse warnings in `load_assets.gd` were confirmed out of scope but have no tracking mechanism; future agents will re-confirm the same findings as out-of-scope on subsequent tickets.
  improvement: When an Implementation Agent encounters pre-existing test failures or parse warnings confirmed out of scope, append a one-line entry to `project_board/KNOWN_ISSUES.md` (creating it if absent) noting the file, line range, and nature of the defect.
  expected_benefit: Prevents repeated re-discovery of the same pre-existing issues. Creates a lightweight defect backlog without blocking the current ticket.

### Keep / Reinforce

- practice: Extracting testable pure logic (family name parsing) into a `RefCounted`-based utility class (`EnemyNameUtils`) so it can be covered by the headless test suite, even when the host class (`load_assets.gd`) cannot be instantiated headlessly.
  reason: This is the correct architectural response to @tool and EditorScript testability constraints. The pattern is generalizable: any EditorScript that contains non-trivial logic should delegate to a plain utility class. The 20 primary and 15 adversarial tests that resulted would not have been possible without this extraction.

- practice: The stash/restore baseline comparison method used by the Implementation Agent to confirm that pre-existing test failures (RSM-SIGNAL, ADV-RSM) predated the current changes and were not regressions.
  reason: This is a reliable, deterministic method for distinguishing pre-existing failures from regressions introduced by the current ticket. It produces strong evidence for the gatekeeper without requiring manual bisection. Should be reinforced as standard practice when `run_tests.sh` exits non-zero.

---

## [missing-movement-simulation-path] — preload path mismatch caused by directory restructure without global reference update
*Completed: 2026-03-25*

### Learnings

- category: infra
  insight: A GDScript `preload()` call using an absolute `res://` path silently becomes a parse-time crash when the target file is moved to a subdirectory, because GDScript evaluates `preload()` at parse time — before any frame runs. The error surfaces only when the scene chain that attaches the script is loaded, not when the script file itself is opened or edited.
  impact: The player controller failed to load in `containment_hall_01.tscn` entirely, not with a graceful runtime error. The bad path was present in HEAD while the fix existed only in the working tree, creating a confusing split state where on-disk code appeared correct but runtime behavior matched the committed (broken) version.
  prevention: Whenever a script file is moved to a subdirectory, run a codebase-wide search for the old path across all `.gd`, `.tscn`, and `.tres` files before committing the move. Treat the move commit and the reference-update commit as an atomic pair — never separate them.
  severity: high

- category: testing
  insight: No existing test covered the `preload` path in `player_controller_3d.gd`. The test suite passed green even though the committed file contained a broken import path, because tests that did not instantiate the player controller did not trigger the parse-time failure.
  impact: The bug was only discovered at runtime, not by `run_tests.sh`. A regression test using `load()` plus `source_code` inspection would have caught this in CI before the bad commit was visible to anyone.
  prevention: For every core script that uses `preload()` to depend on another script, add a headless regression test that: (1) loads the script via `load()` with a null-guard, (2) reads `source_code` to assert the correct path string is present, and (3) asserts the wrong path string is absent. This test costs approximately 5 lines and directly prevents this class of bug.
  severity: high

- category: infra
  insight: The `.godot/uid_cache.bin` binary file can carry a stale UID-to-path mapping that causes Godot to resolve the old path even after the preload string in source is corrected. Text grep cannot validate the full binary content; the only reliable remediation is `godot --import` to force a cache rebuild.
  impact: The ticket had to document `godot --import` as a recommended post-fix step rather than a confirmed AC item, because the binary cache state was not provably clean through text inspection alone.
  prevention: After any resource move or path fix, include `godot --import` as a mandatory step in the implementation runbook — not an optional recommendation. Treat a non-rebuilt UID cache as a blocking risk until a successful headless run confirms it.
  severity: medium

### Anti-Patterns

- description: Moving a script file to a new directory without updating all `preload()` and `load()` references atomically in the same commit. The working tree carried the fix but HEAD did not, producing a "works on my machine" state that misled any agent reading file contents directly.
  detection_signal: `git status` shows a core script modified-not-staged, while `run_tests.sh` passes — meaning tests do not exercise the broken committed version.
  prevention: Any file move that changes a `res://` path must be accompanied by a codebase-wide reference update in the same commit. Search for the old path before committing and verify zero remaining references.

- description: The test suite provided false confidence that the codebase was runnable because tests avoided instantiating the component that was broken. Green CI did not mean the game would launch.
  detection_signal: A script central to gameplay (player controller, core system) has no test that performs even a `load()` on it.
  prevention: Every script under `scripts/player/` and `scripts/system/` should have at least one headless smoke test that calls `load()` and asserts non-null. This catches parse-time failures before any integration step.

### Prompt Patches

- agent: Implementation Agent
  change: "Before committing any file move or directory restructure, search all `.gd`, `.tscn`, and `.tres` files for the old path string and confirm zero matches. If any match is found, update all references in the same commit as the move. Never commit a file move and defer reference updates to a follow-up commit."
  reason: This bug was caused by a move that left a stale `preload()` path in a committed file. A single search-before-commit check would have prevented the bad state from entering HEAD.

- agent: Test Breaker Agent
  change: "For any test suite covering a core script (player controller, system coordinator, scene assembler), include at least one test that calls `load(\"res://path/to/script.gd\")`, asserts the result is non-null, and — if `source_code` is non-empty — asserts that every explicit `preload()` path string in the source corresponds to a file that actually exists. This is the minimum viable regression guard against parse-time import errors."
  reason: The missing-movement-simulation-path bug had zero test coverage that would have caught it. A load-and-source-inspect test is the lowest-cost prevention for this entire class of failure.

### Workflow Improvements

- issue: The Spec Agent observed a discrepancy between HEAD and working-tree state: the fix existed on disk but not in git. This is easy to misread — an agent inspecting file contents may conclude the bug is already resolved while the committed version seen by CI is still broken.
  improvement: When `git status` shows a core script as modified-not-staged, the Spec Agent must explicitly identify the committed vs working-tree discrepancy in the diagnosis section and confirm whether the reported error reproduces against HEAD or the working tree. This distinction must appear in the ticket before any other agent proceeds.
  expected_benefit: Prevents an agent from declaring a bug resolved based on working-tree contents while the committed version remains broken in CI and for other developers.

- issue: The workflow enforcement module's stage enum did not include `IMPLEMENTATION_COMPLETE`, but a task instruction directed the Engine Integration Agent to use that exact stage name. This caused a checkpoint deviation that had to be resolved by assumption.
  improvement: The stage enum in the workflow enforcement module must be kept in sync with all stage names used across all agent task instructions. Any new stage label introduced in a task instruction must also be added to the enforcement enum in the same update cycle.
  expected_benefit: Eliminates spurious checkpoint deviations caused by stale enum definitions, reducing noise in CHECKPOINTS.md.

### Keep / Reinforce

- practice: Using `script.source_code` inspection in headless tests to assert both the presence of correct path strings and the absence of incorrect path strings. This pattern is established in `test_soft_death_and_restart.gd` and was correctly applied as the regression mechanism for this bug.
  reason: It is the only headless-safe method to catch parse-time `preload()` path errors without triggering them. The absence assertion is the critical half — it would have made this bug a CI failure before it ever reached HEAD.

- practice: The stash/restore baseline method used by the Implementation Agent to confirm that 7 pre-existing RSM-SIGNAL failures predated the current fix and were not regressions introduced by it.
  reason: Deterministic and low-cost. Produces unambiguous evidence for the gatekeeper without requiring manual bisection. Should remain standard practice whenever `run_tests.sh` exits non-zero after a fix is applied.

---

## [FEAT-20260326-procedural-run-scene] — Recursive sub-scene descent produced an irreconcilable test defect; source-code substring checks must exclude comment lines
*Completed: 2026-03-26*

### Learnings

- category: testing
  insight: A recursive geometry check that descends into packed-sub-scene internals cannot coexist with a spec requirement that a specific sub-scene (e.g. the player) must remain unmodified. The test PRS-GEO-2 asserted zero MeshInstance3D nodes anywhere in the instantiated tree; the player_3d.tscn sub-scene expanded at runtime, exposing its internal SlimeVisual/MeshInstance3D. Satisfying the test required either removing the mesh (violating PRS-NFR-4) or writing the test differently. The scene was correctly authored; only the test was wrong.
  impact: One test was ruled a design defect and marked for future remediation. The Acceptance Criteria Gatekeeper had to adjudicate, consuming an escalation step. This is the third ticket in sequence (RTS-ADV-16, room_template_system, now PRS-GEO-2) to produce a false failure from recursive descent into sub-scene internals.
  prevention: Geometry and node-type absence assertions must never use full recursive tree walks when the scene instances a sub-scene with known internal nodes. Restrict the walk to direct children of root using `for i in root.get_child_count()` — unless the spec explicitly states "recursively including sub-scene internals." This is a pattern reinforcement of the room_template_system learning that was not applied when writing the PRS geometry spec.
  severity: high

- category: testing
  insight: A source-code substring check (`source_code.contains("reload_current_scene")`) is fragile when the implementation file may contain comments that reference the forbidden pattern. ADV-PRS-09 passed only because the implementation comment on run_scene_assembler.gd line 12 deliberately used the paraphrase "scene reload method" instead of the literal forbidden identifier. If the implementation had written "# Does NOT call reload_current_scene" as a natural comment, the test would have failed as a false positive despite correct implementation.
  impact: The spec noted "Already resolved" — the implementation author was aware of the risk and worked around it — but the test itself has no scoping to exclude comment lines. A future developer adding a clarifying comment using the literal method name would silently break a passing test with no implementation change.
  prevention: When using `source_code.contains(forbidden_string)` as an absence assertion, strip comment lines (lines that begin with `#` after whitespace trimming) before applying the check. Alternatively, assert on the call-site pattern specifically (e.g., `get_tree().reload_current_scene(` rather than bare `reload_current_scene`) to reduce false-positive surface area. The test must include a comment explaining this risk.
  severity: medium

- category: process
  insight: A CRITICAL-flagged GDScript code review finding (NodePath export using Godot 3 style in death_restart_coordinator.gd) was correctly deferred as out of scope because the script was authored under a prior ticket. However, the deferral left no downstream task or backlog entry. Future reviewers encountering the same flag must re-derive the "out of scope / prior ticket" ruling from CHECKPOINTS.md, which is not a task queue.
  impact: The NodePath export style issue remained unresolved across at least two tickets with no ownership. Each checkpoint recorded the same finding and the same resolution without advancing toward remediation.
  prevention: Any time a CRITICAL finding is deferred, a backlog entry or labeled CHECKPOINTS section must name the specific file, the required change, and which ticket or milestone should own it. A CRITICAL finding that generates no downstream work item is not properly triaged.
  severity: low

- category: testing
  insight: Two runtime ACs (seed log line on scene run; 5-room child count after _ready()) are inherently unautomatable headlessly because they depend on SceneTree entry and physics initialization. Strong code-inspection proxy evidence was accepted in lieu of automation, but no documented standard governs what constitutes an acceptable proxy. Each gatekeeper must re-derive sufficiency from ticket prose.
  impact: The gatekeeper accepted the proxies and escalated both items to the human. The outcome was correct, but the reasoning had to be reconstructed per-ticket rather than derived from a standard.
  prevention: When a spec is authored, any AC that requires SceneTree entry should be tagged `[INTG-ONLY]` and the spec must list the specific code evidence that constitutes a headless proxy (e.g., "unconditional print() call at code line X is sufficient code-inspection proxy for the log AC"). This eliminates per-ticket gatekeeper adjudication for a predictable class of cases.
  severity: low

### Anti-Patterns

- description: Writing geometry-absence assertions using full recursive subtree walks when the scene instances a packed sub-scene with known internal mesh nodes. The test becomes irreconcilable with a spec requirement that the sub-scene must not be modified.
  detection_signal: A geometry-absence test fails after the scene is correctly authored, and passing the test would require modifying a sub-scene that a separate NFR explicitly forbids modifying.
  prevention: Scope all geometry-absence assertions to direct children of the stated root node. Never use `find_nodes` or unconstrained recursive iteration for geometry checks. This failure pattern has now occurred three times across three tickets.

- description: Using `source_code.contains(forbidden_identifier)` to enforce a "no call to X" requirement without stripping comment lines first. A natural documentation comment that uses the literal forbidden identifier will produce a false failure with no code change.
  detection_signal: An absence assertion passes, but only because the implementation author paraphrased the forbidden identifier in comments. A reviewer adding a clarifying comment with the literal name breaks the test.
  prevention: Strip comment lines from source_code before applying contains() absence checks, or use the full call-site pattern (e.g., `some_object.forbidden_method(`) instead of the bare identifier to reduce comment-line collision risk.

- description: Deferred CRITICAL code-review findings recorded only in CHECKPOINTS.md with no downstream task or backlog entry. Each subsequent ticket must rediscover the finding and re-derive the same "out of scope" ruling.
  detection_signal: The same CRITICAL flag appears across multiple ticket CHECKPOINTS entries with identical "out of scope for this ticket" resolution and no reference to an open backlog item or a ticket that owns the fix.
  prevention: Every deferred CRITICAL finding must generate a named backlog entry or a labeled CHECKPOINTS note with a specific file, required change, and suggested owning ticket. The checkpoint entry alone is not sufficient.

### Prompt Patches

- agent: Test Design Agent
  change: "When writing any geometry-type absence assertion (no MeshInstance3D, no StaticBody3D, no CSGBox3D, etc.) for a scene that instances one or more packed sub-scenes, restrict the check to direct children of the stated root node using `root.get_child(i)` iteration. Do not use `find_nodes` or any recursive walk for geometry-absence assertions. Add a comment: '# Depth-limited to direct children only — packed-sub-scene internals are excluded.' If the spec text says 'anywhere in the subtree', flag this as a potential spec defect before writing the test and confirm with the spec author."
  reason: PRS-GEO-2 and RTS-ADV-16 both produced irreconcilable false failures because recursive geometry walks descended into packed-sub-scene internals. The scenes were correctly authored in both cases; only the tests were wrong. This pattern has now occurred three times.

- agent: Test Design Agent
  change: "When writing a source_code absence assertion (e.g., `not source_code.contains('some_identifier')`), strip comment lines from source_code before applying the check. Use: `var stripped = \"\\n\".join(source_code.split(\"\\n\").filter(func(l): return not l.strip_edges().begins_with(\"#\")))`. Then assert `not stripped.contains(forbidden_identifier)`. Add a comment: '# Comment lines stripped before check to prevent false positives from documentation references to the forbidden identifier.'"
  reason: ADV-PRS-09 passed only because the implementation author avoided writing the literal forbidden identifier in comments. A documentation edit using the literal name would produce a false failure with no implementation change.

- agent: Static QA Agent
  change: "When a CRITICAL finding is deferred as out of scope for the current ticket, you must append a labeled entry to CHECKPOINTS.md: 'DEFERRED CRITICAL — File: <path>, Finding: <one-line description>, Suggested owner: <ticket-id or milestone>'. This entry is required output. A CRITICAL finding that generates no downstream work item is not properly triaged."
  reason: The NodePath export CRITICAL flag was correctly deferred but left no trace in any task queue. Future agents encountering the same finding must re-derive a ruling that has already been made, wasting time and producing duplicate checkpoint entries.

### Workflow Improvements

- issue: The spec for PRS-GEO-2 wrote "anywhere in the subtree" for the geometry-absence requirement without noting that the player packed-scene instantiated as a direct child of root would expose internal mesh nodes to a recursive walk. The spec defect was only discovered at Engine Integration phase after full scene authoring.
  improvement: The Spec Agent must, before finalizing any absence assertion with recursive scope, enumerate the direct children of the target root node and identify which are packed-scene instances. For each packed-scene instance, the spec must state whether its internal nodes are in scope. If a packed-scene instance must remain unmodified per an NFR, the assertion scope must explicitly exclude it.
  expected_benefit: Catches the recursive-descent spec defect at authoring time, before any test is written or scene implemented. Prevents the escalation cycle that occurred here and in room_template_system.

- issue: INTEGRATION-class ACs requiring SceneTree entry have no standard proxy-evidence format. Each ticket requires the gatekeeper to adjudicate whether code-inspection evidence is sufficient for sign-off, producing per-ticket reasoning that is not reusable.
  improvement: The Spec Agent must tag any AC requiring SceneTree entry as `[INTG-ONLY]` and list the specific code evidence that constitutes an acceptable headless proxy (e.g., "unconditional print() at line X confirmed by code inspection"). The gatekeeper can then apply the proxy standard without re-deriving it from ticket prose.
  expected_benefit: Reduces ticket revision count and gatekeeper adjudication time for a predictable and recurring class of integration-only ACs.

### Keep / Reinforce

- practice: The Acceptance Criteria Gatekeeper's ruling on PRS-GEO-2 named both the root cause (spec over-specified "anywhere in the subtree") and the exact remediation (restrict walk to direct children or explicitly exclude packed-sub-scene-internal nodes). The ruling cited both the failing test and the conflicting NFR.
  reason: A gatekeeper ruling that identifies root cause and remediation prevents the same defect from being regenerated in a future ticket. This format is the correct standard for all defect rulings.

- practice: The ticket's Escalation Notes section explicitly surfaced omissions from the original input schema (SpawnPosition NodePath, infection_handler export) rather than silently absorbing them as assumptions. Each was stated with the required action.
  reason: Surfacing input-schema omissions explicitly in escalation notes prevents them from becoming silent implementation defects. Future agents reading the ticket can confirm that out-of-spec wiring decisions were intentional and traceable.

---

## [AP-CONTINUE-2026-03-27] — 7 tickets correctly held at INTEGRATION; zero false completions; playtest-result-capture path is missing from the workflow
*Completed: 2026-03-27*

### Learnings

- category: process
  insight: All 7 in-progress tickets (5 M4 + 2 M6) are structurally complete — automated test suites pass, scene wiring is done, and the AC Gatekeeper correctly identified the sole remaining blocker on each as a human-only visual or runtime observation. The AC Gatekeeper's hold behavior is correct and should be treated as expected steady state for tickets with subjective ACs.
  impact: Zero false completions occurred. The Gatekeeper's conservative stance prevents premature COMPLETE advancement. However, the pipeline has no affordance for a human to record evidence inline — the tickets contain a Manual QA Checklist section and a documented task, but there is no standard handoff mechanism that routes the human to those instructions or captures their response back into the ticket file.
  prevention: The workflow needs an explicit "human verification handoff" mechanism: a short summary document or notification that lists all INTEGRATION-blocked tickets, their scene to open, and the exact numbered checklist steps. Without this, playtest evidence accumulates nowhere and tickets remain at INTEGRATION indefinitely despite correct automated coverage.
  severity: high

- category: process
  insight: The "Manual QA Checklist" prompt patch for the Spec Agent has been documented in learnings entries for [containment_hall_01_layout], [fusion_opportunity_room], [light_skill_check], [procedural_room_chaining], and [FEAT-20260326-procedural-run-scene] — five consecutive mentions — and the checklists are now appearing in tickets (mini_boss_encounter, soft_death_and_restart, procedural_room_chaining all have explicit numbered playtest task blocks). However, none of these tickets have been completed because the human has not performed and recorded the playtests. The spec-side fix is working; the human-response side is the remaining gap.
  impact: Playtest checklists exist and are well-formed. The blocker is not spec quality — it is that playtest results have no path back into the ticket. The workflow has no actor responsible for consuming the checklist and writing evidence into Validation Status.
  prevention: Distinguish the two distinct sub-problems: (a) checklist creation at spec time — now solved; (b) evidence capture after playtest — still unsolved. Future workflow improvements should focus exclusively on (b).
  severity: high

- category: process
  insight: When an ap-continue run processes multiple tickets and all are held at INTEGRATION by the same class of blocker (human visual verification), the run produces zero new code and zero ticket state transitions. From a pipeline efficiency perspective, an ap-continue run in this state is a no-op — it confirms the correct hold state but advances nothing. This is not a failure; it is a structural signal that the pipeline is waiting for an out-of-band human input.
  impact: Autopilot runtime was consumed confirming already-correct state across 7 tickets. No rework occurred. The AC Gatekeeper behaved correctly on all 7. If this pattern recurs, the Orchestrator should recognize "all in-progress tickets at INTEGRATION with visual-only remaining blocker" as a condition to short-circuit the run and surface the playtest queue directly to the human rather than cycling through each ticket.
  prevention: When the Orchestrator begins an ap-continue run and finds that all in-progress tickets have Stage: INTEGRATION and all blocking issues are labeled "human playtest required," it should emit a single "Playtest Queue" summary rather than re-running the AC Gatekeeper per ticket.
  severity: medium

- category: process
  insight: The persistent 7 RSM-SIGNAL-* pre-existing test failures appear in every run log across multiple tickets (SDR, MMSP, PRS, PRC). Each integration agent spends time confirming they are pre-existing using the stash/restore method. The `known_failures.txt` improvement (identified in [soft_death_and_restart] learnings) was never implemented. Every subsequent agent rediscovers and re-confirms the same failures.
  impact: Compounding diagnostic overhead. The stash/restore confirmation method is fast, but the effort is entirely duplicated across each ticket's Integration Agent. Across 7 recent tickets, this diagnostic has been performed 7+ times for the identical failures.
  prevention: Create `tests/known_failures.txt` with the 7 RSM-SIGNAL-* test names and a one-line explanation. This file should be checked before declaring any test failure a regression. This improvement was identified in [soft_death_and_restart] and has not been actioned.
  severity: medium

### Anti-Patterns

- description: Logging a workflow improvement about creating `tests/known_failures.txt` across multiple learning entries without it ever being created. Logged once in [soft_death_and_restart] and still absent as of this run — it became a recurring anti-pattern where the insight is re-derived rather than actioned.
  detection_signal: A learning entry's "prevention" step refers to creating a specific file, but that file does not exist after two or more ticket cycles have passed since the entry was written.
  prevention: When an improvement requires creating a new project-level file, the Learning Agent must note it as an open directive for the next agent that touches the relevant directory, not only log it in LEARNINGS.md.

- description: An autopilot run that confirms correct hold state across all tickets but has no short-circuit path — each ticket is processed fully even when the outcome is deterministic (all are INTEGRATION, all have human-only remaining blockers).
  detection_signal: All in-progress tickets have Stage: INTEGRATION and all Blocking Issues contain the phrase "human" or "playtest required" at the start of the run.
  prevention: The Orchestrator should check the Stage and Blocking Issues fields of all in-progress tickets at the start of an ap-continue run. If all are INTEGRATION with human-only blockers, emit the playtest queue and halt rather than cycling each through the AC Gatekeeper.

### Prompt Patches

- agent: AC Gatekeeper Agent
  change: "At the start of any ap-continue run, before processing individual tickets, check the Stage and Blocking Issues of every in-progress ticket. If all tickets have Stage: INTEGRATION and all Blocking Issues contain only human-observation requirements (visual, runtime, playtest), emit a 'Playtest Queue' block listing: ticket name, scene to open, and the exact numbered checklist steps from each ticket's Manual QA task. Then halt without cycling through each ticket's gatekeeper logic individually."
  reason: The 2026-03-27 ap-continue run consumed runtime confirming correct hold state on 7 tickets with zero state transitions possible. Short-circuiting this case reduces cycle time and surfaces the actionable items (playtests) directly to the human.

- agent: Planner Agent
  change: "When creating or reviewing a ticket that will reach INTEGRATION with human-only remaining ACs, append the ticket name and its playtest task to `project_board/PLAYTEST_QUEUE.md` (create the file if absent). Each entry must include: ticket name, scene path, and the numbered Manual QA Checklist steps. This file is the human's input queue for in-editor verification."
  reason: Playtest checklists now exist in individual tickets but there is no consolidated view. The human must open each ticket to find what needs verification. A dedicated queue file surfaces all pending playtests at a glance.

- agent: Spec Agent
  change: "When authoring the Manual QA Checklist section for an INTEGRATION-class AC, append a 'Playtest Result Recording' subsection with these four verbatim steps: (1) Update the relevant Validation Status row from 'NOT EVIDENCED' to 'PASS — [your initials] [date]'; (2) Clear the Blocking Issues section; (3) Set Stage to COMPLETE; (4) Run `git mv project_board/<milestone>/in_progress/<ticket>.md project_board/<milestone>/done/<ticket>.md`."
  reason: All 7 INTEGRATION-held tickets have well-formed checklists but no instructions for how the human records evidence back into the ticket file. Without the result-recording steps, the human has no clear path to close the ticket after a successful playtest.

### Workflow Improvements

- issue: After a human performs a playtest, there is no documented mechanism for recording the result and closing the ticket. All 7 INTEGRATION tickets have playtest task blocks but none have result-recording steps. This is the structural gap that prevents closure.
  improvement: Every ticket that enters INTEGRATION with a human-only blocking AC must include a "Playtest Result Recording" subsection in its Manual QA task block (see Spec Agent prompt patch above). The subsection must appear in the ticket before it transitions to INTEGRATION — not as an afterthought.
  expected_benefit: Converts playtest completion from an open-ended task into a deterministic 4-step procedure. Eliminates the ambiguity about what the human does after verifying the playtest.

- issue: The `tests/known_failures.txt` file improvement has appeared in LEARNINGS.md since the [soft_death_and_restart] entry and has not been created. Improvements requiring a new artifact do not self-execute; they need an explicit owner.
  improvement: The next agent that processes `tests/` files (Test Design Agent, Engine Integration Agent, or Static QA Agent) should treat the creation of `tests/known_failures.txt` as a mandatory pre-step, listing at minimum: RSM-SIGNAL-1 through RSM-SIGNAL-6 and ADV-RSM-02, each with a one-line note identifying the root cause (lambda primitive capture in GDScript 4.6.1) and the ticket where it was diagnosed ([soft_death_and_restart]).
  expected_benefit: Ends the recurring stash/restore diagnostic for known-broken tests. Reduces noise that obscures real regressions.

### Keep / Reinforce

- practice: The AC Gatekeeper held all 7 tickets at INTEGRATION without advancing any prematurely, even across multiple ap-continue runs. All blocking issues were accurately identified as human-observation-only.
  reason: This is the correct behavior. The Gatekeeper's conservative stance is working. The remaining gap is human-side evidence capture, not gatekeeper logic. Reinforce this hold behavior as the correct default for all tickets where any AC requires runtime visual confirmation.

- practice: Every blocked ticket has a well-formed Manual QA Checklist with numbered steps specifying the exact scene path, trigger action, and expected observable outcome. The spec-side fix for the recurring "checklist missing" anti-pattern is working.
  reason: Tickets now contain executable verification procedures. The problem is no longer checklist quality — it is that the human has no consolidated entry point to discover and act on the queue, and no instructions for recording results. The spec practice is sound; the workflow gap is the aggregation and result-capture layer.

---

## [FEAT-MUTATION-COLOR] — StandardMaterial3D sub-resource sharing, per-frame material write guard, and is_instance_valid() for RefCounted references

*Completed: 2026-03-28*

### Learnings

- category: architecture
  insight: A `StandardMaterial3D` declared as a sub-resource (`[sub_resource ...]`) in a `.tscn` file is a shared singleton across all instances of that scene. Mutating `albedo_color` directly on `mesh.material_override` at runtime without first calling `.duplicate()` corrupts the shared definition, affects every instance simultaneously, and can dirty the `.tscn` on disk when Godot auto-serializes scene state.
  impact: If duplication had been omitted, a second player instance or a run-restart would inherit whatever `albedo_color` was set at mutation time rather than the baseline. The spec caught this in MAC-2 before any implementation occurred.
  prevention: Any script that writes to a material property at runtime must call `material_override.duplicate()` in `_ready()` before the first write. A dedicated `_material: StandardMaterial3D` member variable should hold the duplicated reference so it is never re-fetched from the mesh hierarchy.
  severity: high

- category: performance
  insight: Accessing `mesh.material_override.albedo_color` as a property chain per `_process()` frame traverses two property lookups and one cast per tick. Caching the duplicated `StandardMaterial3D` in a typed `_material: StandardMaterial3D` member variable reduces this to a single direct field write, which is measurably faster at high frame rates and consistent with the project's convention for cached node references.
  impact: The implementation introduced a fifth member variable (`_material`) not listed in the spec's MAC-7 inventory. This created a spec inventory discrepancy noted by the AC Gatekeeper, but the variable was architecturally required by the MAC-8 performance constraint. The spec's member inventory was incomplete relative to its own performance requirement.
  prevention: When a spec mandates that `_process()` must not perform per-frame property traversal (MAC-8), the spec's member variable inventory (MAC-7) must also include the cached material reference. Performance constraints and member variable tables must be co-authored and cross-checked before publication.
  severity: medium

- category: architecture
  insight: A `_current_tinted: bool` cache that gates material writes so `_process()` only writes on state transitions — not on every frame — is the correct pattern for any `_process()` hook that drives visual state from a polling query. Without it, the material property is re-assigned every frame regardless of whether the state changed, producing unnecessary GPU state changes and GDScript property overhead.
  impact: The `_current_tinted` cache was explicitly required by MAC-6 and correctly applied. No rework was needed here. The lesson is to recognize this as a generalizable pattern for any poll-driven visual state driver.
  prevention: Any `_process()` that reads a binary query (`any_filled()`, `is_active()`, etc.) and drives a visual property should cache the last-known boolean result and gate writes behind an inequality check. The pattern is: `if should_state == _current_state: return` before any property write.
  severity: low

- category: architecture
  insight: `is_instance_valid()` is the correct guard for `Object` references that may have been freed externally, while `!= null` is only reliable for objects the caller knows to still be alive. For `RefCounted` objects, `is_instance_valid()` is technically equivalent to `!= null` (RefCounted objects are not freed until all references drop), but using it consistently as the null guard is safer than relying on the caller to remember which class the reference is.
  impact: No bug was caused here — the spec explicitly required `is_instance_valid()` on both `_mesh` and `_mutation_slot_manager`. The learning is about establishing the guard as a consistent default for any externally-owned reference, regardless of whether the concrete type is Node or RefCounted.
  prevention: For any member variable that caches a reference obtained from an external source (parent node, autoload, scene tree query), use `is_instance_valid()` as the null guard in `_process()` regardless of the concrete class. Annotate the comment: `# is_instance_valid covers both null and freed-object cases`.
  severity: low

### Anti-Patterns

- description: Writing to `material_override.albedo_color` at runtime without first calling `.duplicate()` on the material. Because `.tscn` sub-resources are shared, the write affects all scene instances simultaneously and can corrupt the authored scene file on disk via Godot's auto-serialization.
  detection_signal: A `_process()` or `_ready()` that assigns to `mesh.material_override.albedo_color` or `mesh.get_active_material(0).albedo_color` without a `.duplicate()` call visible in the same script's `_ready()`.
  prevention: Add a mandatory `_ready()` guard: resolve `material_override`, call `.duplicate()`, store the result in a typed member. All subsequent writes go through the cached duplicated reference.

- description: A spec's member variable inventory that lists only the variables required for behavioral contracts but omits the performance-optimization variable that its own non-functional requirement necessitates. This produces a spec inventory discrepancy that the AC Gatekeeper must adjudicate as a non-blocking deviation.
  detection_signal: A spec has a "Non-Functional — Performance" section that requires caching a reference (to avoid per-frame traversal) but the member variable table does not include the cache field.
  prevention: The Spec Agent must read every non-functional constraint and derive any member variables that are implicitly required by it, then add them to the member variable table. Behavioral and performance members must both appear in the inventory.

- description: Resolving `get_parent()` or any scene-tree query inside `_process()` to obtain a reference that could have been cached in `_ready()`. This is a per-frame scene-graph walk with no semantic value when the parent-child relationship is stable for the node's lifetime.
  detection_signal: A `_process()` method body contains `get_parent()`, `get_node()`, or `find_child()`.
  prevention: All reference resolution that is stable for the node's lifetime must happen in `_ready()`. A `_process()` method that calls `get_parent()` or `get_node()` is always a defect; flag it in Static QA.

### Prompt Patches

- agent: Spec Agent
  change: "When writing a Non-Functional — Performance requirement that mandates caching a reference (e.g. 'material must not be accessed per frame via property traversal'), immediately update the member variable inventory table to include the cache field. The inventory table and the performance constraints must be co-authored. An inventory that is missing a cache variable required by a performance constraint is a spec defect."
  reason: The MAC-7 member variable inventory listed four variables but omitted `_material: StandardMaterial3D`, which was architecturally required by the MAC-8 performance constraint. The omission produced an AC Gatekeeper discrepancy note for a fifth variable that was entirely foreseeable at spec time.

- agent: Implementation Agent
  change: "Before writing any runtime material property assignment (`albedo_color`, `roughness`, `metallic`, etc.), check whether the material was obtained from a `.tscn` sub-resource (check for `[sub_resource ...]` in the scene file). If it was, call `.duplicate()` on the material in `_ready()` and store the result in a typed `StandardMaterial3D` member variable. Never write to `mesh.material_override.albedo_color` directly — always write to the cached duplicated material reference."
  reason: StandardMaterial3D sub-resources are shared across all scene instances. Direct mutation corrupts the shared definition and can dirty the .tscn on disk. This class of bug is silent — no runtime error fires, and the corruption only becomes visible when a second instance is created or the scene is resaved.

- agent: Static QA Agent
  change: "Flag any `_process()` method body that calls `get_parent()`, `get_node()`, `find_child()`, or any other scene-tree traversal method. These are per-frame scene-graph queries that should be cached in `_ready()`. Report each occurrence as a defect with severity MEDIUM and the recommended fix: cache the result in a typed member variable in `_ready()` and read the member in `_process()`."
  reason: Per-frame node resolution is one of the most common `_process()` performance anti-patterns in Godot. Catching it at Static QA phase prevents it from reaching implementation review.

### Workflow Improvements

- issue: The spec's MAC-7 member variable inventory was published before all non-functional constraints were fully derived. The Performance constraint (MAC-8) implicitly required a fifth member that the inventory did not list. The AC Gatekeeper had to adjudicate this as an "accepted non-blocking discrepancy" rather than verifying an exact inventory.
  improvement: The Spec Agent should perform a final cross-check pass before publishing: for each Non-Functional requirement, enumerate any member variables it implies and verify they appear in the member variable inventory. This check takes approximately one minute and closes the class of inventory incompleteness.
  expected_benefit: Eliminates gatekeeper inventory discrepancy notes that are predictable from the spec's own content. Keeps the gatekeeper's verdict clean.

### Keep / Reinforce

- practice: Resolving all stable references (`_mesh`, `_mutation_slot_manager`) in `_ready()`, caching them in typed member variables, and reading the members in `_process()` without re-resolution. This is the established convention for all `_process()` hot paths in this project.
  reason: Every `_process()` node in the codebase follows this pattern. Consistent application eliminates an entire class of per-frame overhead and keeps `_process()` bodies trivially reviewable — they should contain only guards, comparisons, and property writes, never node queries.

- practice: Using `has_method("get_mutation_slot_manager")` (duck-typing via method presence) rather than `is PlayerController3D` when resolving a reference from a parent node in `_ready()`. This makes the child node compatible with test stubs that are plain `Node` objects and do not extend `PlayerController3D`.
  reason: Strict type checks in child-to-parent reference resolution couple the child to a concrete parent class, making headless tests require a full `PlayerController3D` instantiation. Method-presence checks allow lightweight stubs and preserve testability without any behavioral compromise.

---

## [run_state_manager] — Lambda primitive capture bug produced 7 persistent signal-test failures; AC Gatekeeper accepted implementation via code inspection while tests were broken
*Completed: 2026-03-28*

### Learnings

- category: testing
  insight: GDScript 4.6.1 lambda closures capture primitive types (`bool`, `int`, `float`) by value at creation time. A lambda `func(): fired = true` writes to a copy of `fired`, not the original outer variable. The outer variable is never mutated. All signal-emission tests written with this pattern silently fail regardless of whether the signal actually fires.
  impact: RSM-SIGNAL-1 through RSM-SIGNAL-6 and ADV-RSM-02 were broken from the moment they were written. The failures persisted across 7 subsequent tickets (SDR, MMSP, PRC, PRS, GSV, AP-CONTINUE, scene_state_machine), requiring stash/restore diagnostic effort on every Integration Agent run. The fix — using an Array capture `var flags := [false]` — was made in a human cleanup commit outside the pipeline, not by any agent.
  prevention: Never use a bare `bool`, `int`, or `float` local variable as the mutation target inside a GDScript signal-detection lambda. Always use `var flags := [false]` (single-element Array) and `func(): flags[0] = true`. This rule was documented in [soft_death_and_restart] learnings but not applied when the RSM test suite was written, because the Test Design Agent authored the tests before the rule was logged. Apply this rule at test-write time, before running.
  severity: critical

- category: process
  insight: The AC Gatekeeper accepted the RSM ticket as COMPLETE by verifying the implementation via code inspection ("signal emits at lines 48–49, state updates at lines 49/53/57") rather than by running the automated test suite. The gatekeeper's evidence was correct — the implementation was right — but the 7 failing signal tests were not treated as a blocking condition. The ticket was marked COMPLETE while 7 of its own test IDs were failing.
  impact: A pattern was established where an implementation can be gatekeeper-accepted while its dedicated test suite is broken. The tests' purpose (automated regression detection) was nullified for those 7 cases. Any future regression in signal emission would pass the suite without detection.
  prevention: The AC Gatekeeper must run the test suite against the specific ticket's test files and treat failures in those files as blocking unless explicitly diagnosed as pre-existing (with a stash/restore comparison confirming they predated the ticket's implementation). Code inspection is a supplementary method, not a substitute for a passing test run.
  severity: high

- category: architecture
  insight: The `extends RefCounted` pattern for a pure-logic state machine with parameterless signals produced a completely headless-testable, SceneTree-free implementation. Signal connections, state transitions, and slot manager integration were all verifiable via `load().new()` with zero scene setup.
  impact: All structural and transition tests (RSM-STRUCT, RSM-TRANS, RSM-RESET, RSM-NOOP) passed first run. The architecture imposed no friction on test setup or teardown. This confirms that pure-logic state machines should always extend RefCounted when headless testability is a requirement.
  prevention: No prevention needed — reinforce this as default architecture for state machines in this project.
  severity: low

- category: testing
  insight: Signal emission timing (emit-before-state-change contract) is a subtle but load-bearing invariant that is invisible in transition tests. The implementation correctly emits signals before updating `_state`, but this contract can only be verified by a lambda that captures state at emit time (RSM-SIGNAL-6). If the emit-before-state test is written with the broken lambda pattern, the contract can silently regress with no test detection.
  impact: RSM-SIGNAL-6 was broken along with the other 6 signal tests, meaning the emit-first contract had zero automated coverage for the duration of the failures. A regression that emitted after state change would have been undetectable.
  prevention: The emit-before-state test is the highest-value single signal test for any state machine. It should be treated as a mandatory primary test (not adversarial), and its lambda capture must use the Array pattern to be valid.
  severity: medium

### Anti-Patterns

- description: Writing a signal-detection lambda with a bare primitive capture (`var fired: bool = false; rsm.connect("signal_name", func(): fired = true)`) when the intent is to detect whether the signal fired.
  detection_signal: A signal test with `assert(fired)` after an `apply_event()` call always fails even though the signal is confirmed by code inspection to be emitted.
  prevention: Replace `var fired: bool = false` with `var flags := [false]` and `func(): fired = true` with `func(): flags[0] = true`. This is a one-for-one substitution with no semantic change except correct GDScript 2.0 capture semantics.

- description: Accepting a ticket as COMPLETE when the ticket's own test suite has failing tests, based solely on implementation code inspection as evidence. Tests that fail are not providing coverage; they are silently passing regardless of implementation correctness.
  detection_signal: An AC Gatekeeper verdict that says "AC verified by code inspection at lines X–Y" for an AC that has a corresponding automated test ID that is failing.
  prevention: Failing tests for the current ticket's ACs are a blocking condition. The Gatekeeper must treat any failure in `test_[ticket_name].gd` or `test_[ticket_name]_adversarial.gd` as blocking unless a stash/restore comparison demonstrates the failure predates the ticket. Code inspection supplements; it does not substitute.

### Prompt Patches

- agent: Test Design Agent
  change: When writing any GDScript signal-detection lambda to assert that a signal was emitted, use Array-based capture exclusively. The pattern is: `var flags := [false]` and `func(): flags[0] = true`, then assert `flags[0]`. Never use `var fired: bool = false` with `func(): fired = true`. GDScript 4.6.1 captures `bool`, `int`, and `float` primitives by value in lambdas; mutations inside the lambda do not affect the outer variable. This applies to all signal tests, including emit-before-state-change tests.
  reason: RSM-SIGNAL-1 through RSM-SIGNAL-6 and ADV-RSM-02 were all written with the broken primitive-capture pattern and all failed silently. Seven tests provided zero coverage for 7+ ticket cycles. The Array capture pattern was already documented in [soft_death_and_restart] but was not applied at test-write time for this ticket.

- agent: Acceptance Criteria Gatekeeper Agent
  change: Before issuing a COMPLETE verdict, run the test suite and check specifically for failures in `tests/scripts/system/test_[ticket_id].gd` and `tests/scripts/system/test_[ticket_id]_adversarial.gd` (or the appropriate test path for the ticket). Failures in the ticket's own test files are blocking unless a stash/restore comparison confirms they predate the implementation. Code inspection of the implementation is supplementary evidence only — it does not substitute for a passing test run against the ticket's own suite.
  reason: The RSM gatekeeper accepted the ticket as COMPLETE while RSM-SIGNAL-1..6 and ADV-RSM-02 were failing. The implementation was correct but the tests were broken, eliminating regression detection for all signal behavior. A passing test run is the definitive AC evidence for headlessly-testable criteria.

### Workflow Improvements

- issue: A test design defect (broken lambda primitive capture) that was already documented in [soft_death_and_restart] learnings was not applied when the RSM test suite was authored in a later session. The learning was logged but not injected into the Test Design Agent's active behavior.
  improvement: When a Test Design Agent begins writing signal-emission tests for any new class, it should explicitly check the most recent LEARNINGS.md for GDScript signal-testing rules before writing the first test. The lambda primitive capture rule must be consulted, not rediscovered.
  expected_benefit: Prevents a documented failure pattern from recurring on the next ticket with signal tests. The [soft_death_and_restart] entry was available but not consulted.

- issue: The stale RSM-SIGNAL failures persisted for 7+ tickets and were diagnosed from scratch each time using stash/restore. The `tests/known_failures.txt` improvement has now been logged in three separate learning entries ([soft_death_and_restart], [AP-CONTINUE-2026-03-27], now here) without being created.
  improvement: The RSM-SIGNAL failures are now resolved (fixed in commit 55129da). If any new known failures emerge, `tests/known_failures.txt` should be created immediately with the test name, root cause, and diagnosing ticket. The file's absence is now the correct state (no known failures); it should be created only if a new pre-existing failure is confirmed.
  expected_benefit: Closes the loop on a three-entry recurring improvement suggestion. The underlying problem (RSM-SIGNAL failures) is resolved; the process improvement (known_failures.txt) is only needed if a new pre-existing failure is introduced.

### Keep / Reinforce

- practice: Implementing the state machine as `extends RefCounted` with `_slot_manager` initialized in `_init()` (not `_ready()`), using parameterless signals for all transitions, and placing all logic in `apply_event()` with a match block. No SceneTree API anywhere in the file.
  reason: This produced a file that is loadable headlessly, testable without a SceneTree, and trivially instantiable by consumers with no wiring overhead. The pattern also allowed `DeathRestartCoordinator._ready()` to wire signals without any scene path lookups. Reinforce this as the canonical design for all lifecycle state machines in this project.

- practice: The emit-before-state-change contract (signal fires before `_state` is updated) being verified by RSM-SIGNAL-6 using a lambda that captures `rsm.get_state()` at emit time. This test type is the only headless-safe way to verify ordering between two synchronous side effects.
  reason: Emit-before-state ordering is a contract that consumers depend on (e.g., a signal handler that reads state to branch behavior gets the pre-transition state). This test type should exist for any state machine that has an emit-first guarantee. Once the Array capture pattern is used, this test is reliable and provides real protection.

---

## [scene_state_machine] — Stale BLOCKED ticket, cross-domain handoff noise, and `_init()` vs `_ready()` for headless-tested nodes

*Completed: 2026-03-27*

### Learnings

- category: process
  insight: A ticket can be marked BLOCKED based on a test-failure report that was accurate at the time of writing but stale by the time it is re-read. The implementation was already correct; the block was a snapshot of an earlier incomplete state.
  impact: The autopilot restarted the ticket from BLOCKED, rediscovered the correct implementation, and had to reason through whether the failure report was current before making progress. No code changed — only the ticket state was wrong.
  prevention: When an agent marks a ticket BLOCKED due to test failures, it must record the exact test run hash, timestamp, or commit SHA alongside the failure report. Any agent resuming the ticket must re-run the suite before accepting the prior failure report as current. A stale failure report without a re-run is not valid blocking evidence.
  severity: high

- category: architecture
  insight: When the Core Simulation Agent authors both the pure-logic module and the Node controller/wiring as part of its scope, the Engine Integration Agent finds the handoff artifact already complete and must decide whether to re-verify, re-author, or simply validate. This ambiguity causes unnecessary deliberation and a checkpoint entry.
  impact: The Engine Integration Agent correctly determined the wiring was complete and moved on, but the decision cost a checkpoint and an explicit deliberation pass that would not have been needed with clearer scope boundaries.
  prevention: The ticket handoff between Core Simulation and Engine Integration must explicitly state which artifacts are pre-authored and which require the Engine Integration Agent's attention. A "pre-authored artifacts" list in the ticket's WORKFLOW STATE block eliminates the ambiguity without requiring the receiving agent to re-inspect.
  severity: medium

- category: testing
  insight: Constructing a Node-based controller's owned state in `_ready()` makes the controller untestable headlessly: integration tests that instantiate the node without inserting it into a SceneTree never trigger `_ready()`, and any property initialized there remains null.
  impact: The integration tests called `get_state_machine()` and received null because `_ready()` had not fired. The fix was to move construction to `_init()`, which fires at instantiation time regardless of scene tree membership.
  prevention: For any Node subclass that owns a pure-logic object (RefCounted or Object) that must be accessible in headless tests, initialize that owned object in `_init()`, not `_ready()`. Reserve `_ready()` only for initialization that genuinely requires a live SceneTree (node queries, signal connections to other tree nodes, etc.).
  severity: high

- category: architecture
  insight: When a pure-logic class acts as the sole source of truth for event string constants (e.g. `EVENT_SELECT_*`), those constants belong on that class rather than on the consuming controller, even if the controller is the only current consumer. Splitting string literals across two files creates divergence risk.
  impact: The GDScript review correctly placed `EVENT_SELECT_*` constants on `SceneStateMachine` rather than on the controller. This eliminated the only magic-string duplication risk in the event dispatch path.
  prevention: For any pure-logic class that defines a transition protocol (events, states, or config keys), co-locate all string/enum constants for that protocol on the pure-logic class. Controllers reference constants via class qualifier (`SceneStateMachine.EVENT_SELECT_*`), never via inline literals.
  severity: medium

### Anti-Patterns

- description: Marking a ticket BLOCKED based on a test-failure report without recording a run timestamp or commit reference. A resuming agent accepts the report as current and spends deliberation budget before re-running to discover the block is stale.
  detection_signal: A BLOCKED ticket whose failure report contains no timestamp, commit SHA, or test-run identifier alongside the listed failures.
  prevention: Blocking evidence must be time-stamped. Any agent that resumes a BLOCKED ticket must re-run the test suite as its first action, before reading the prior failure report.

- description: Implementing AC gating behavior (AC-4: "feature systems gated on state") via a method with no consumers. `get_config()` existed and was correct, but nothing called it — meaning the AC was technically present in code but zero-impact at runtime.
  detection_signal: An AC that requires "system X gated on state Y" but no test or code path calls the gating method to make a behavioral decision.
  prevention: For any AC that requires state-dependent gating, the Gatekeeper must verify that at least one consumer of the gating method exists (either a runtime consumer or a headless query helper called by integration tests). A method with no callers does not satisfy a gating AC.

- description: An untyped parameter on a dispatch method (e.g. `apply_event(event_id)` without annotation) that relies solely on a runtime `typeof()` guard for type safety. Static analysis tools flag this and the annotation adds zero runtime cost.
  detection_signal: A GDScript review pass that flags untyped parameters on public dispatch methods.
  prevention: All public method parameters on pure-logic modules must have explicit type annotations (use `Variant` when the type is intentionally polymorphic). Runtime guards are not a substitute for static type annotations.

### Prompt Patches

- agent: Engine Integration Agent
  change: At the start of any handoff, check the ticket's WORKFLOW STATE block for a "Pre-authored artifacts" list. If such a list exists, treat those artifacts as already complete and limit your scope to the items explicitly assigned to Engine Integration. If no such list exists, file a checkpoint naming each artifact you found pre-authored and your basis for accepting or rejecting it, before proceeding.
  reason: The SSM handoff caused deliberation overhead because the scope boundary was implicit. An explicit pre-authored artifact list in the ticket eliminates the re-inspection pass.

- agent: Acceptance Criteria Gatekeeper Agent
  change: For any AC of the form "X is gated on state Y" or "X is enabled/disabled based on Z", verify that at least one consumer of the gating method exists — either a runtime caller in scene code or a headless integration test that calls the query helper and asserts a behavioral outcome. A method that exists but has no callers does not satisfy a gating AC.
  reason: AC-4 on the SSM ticket had `get_config()` implemented but with zero consumers until the Engine Integration Agent added feature-gate query helpers. The gating AC was satisfied in letter (method exists) but not in spirit (nothing used it to make a decision).

- agent: Core Simulation Agent
  change: For any Node subclass that owns a pure-logic object (e.g. a RefCounted state machine, manager, or resolver) that will be accessed in headless integration tests, initialize the owned object in `_init()`, not `_ready()`. Add a comment: "# Constructed in _init() so headless tests that skip scene tree insertion can still access this object."
  reason: The SSM `SceneVariantController` initialized its state machine in `_ready()`, causing null returns in headless tests. Moving construction to `_init()` is a one-line fix with no behavior change in production but eliminates an entire class of headless null-dereference failures.

### Workflow Improvements

- issue: The ticket spent a full deliberation cycle on a stale BLOCKED state before the blocking condition was re-evaluated. No workflow step required re-running the test suite before acting on the block.
  improvement: Add a mandatory first step to the autopilot's BLOCKED ticket restart procedure: "Before reading the prior failure report, re-run the test suite. If the suite passes, update the ticket stage and proceed. Only act on prior failure descriptions if the re-run confirms them."
  expected_benefit: Eliminates the class of false-BLOCKED tickets where a prior agent's incomplete run left a stale failure report. Converts a deliberation cost into a single test-run step.

- issue: The two-agent split (Core Simulation → Engine Integration) produced overlapping scope: Core Simulation authored the controller and wiring that Engine Integration was expected to produce. The handoff had no artifact inventory, so Engine Integration could not distinguish "pre-built by prior agent" from "I missed something."
  improvement: The ticket's WORKFLOW STATE block should include a "Pre-authored artifacts" section populated by each agent before handoff, listing every file it created or modified. The receiving agent reads this section to scope its own work without re-inspecting the full codebase.
  expected_benefit: Reduces per-handoff checkpoint entries from "figure out what was already done" to a direct scope check against an explicit inventory.

### Keep / Reinforce

- practice: The GDScript review pass caught untyped parameters and magic strings before the Gatekeeper evaluated AC coverage. Fixing these before the AC audit prevented the Gatekeeper from seeing a noisy warning list alongside substantive AC gaps.
  reason: Separating static-analysis cleanup from AC coverage evaluation keeps the Gatekeeper's decision clean. Static QA is a prerequisite to Gatekeeper review, not concurrent with it.

- practice: Extending `RefCounted` (not `Node`) for the pure-logic `SceneStateMachine` allowed 15 headless tests with zero SceneTree setup and no teardown risk. The entire state-machine contract was verified without any scene or process context.
  reason: This is the established pattern for pure-logic modules in this project (reinforced in [procedural_room_chaining]). It continues to eliminate the largest category of headless test friction. Every new system that is computation-only should extend RefCounted, not Node.

---

## [first_4_families_in_level] — EditorScript cannot be run headlessly; infection call chain gaps survive static analysis; Variant-to-String coercion caught by GDScript reviewer; position mismatch caused by Engine Integration Agent not reading spec coordinates; AC-5 playability gate is structurally unautomatable

*Completed: 2026-03-30*

### Learnings

- category: architecture
  insight: An `@tool extends EditorScript` script cannot be driven headlessly. The only way to automate its logic is to replicate that logic in a new `extends SceneTree` script with `func _init()` as the entry point. The replication is a permanent maintenance fork — the two files diverge from the moment of creation.
  impact: `load_assets.gd` (EditorScript) had to be partially replicated as `generate_enemy_scenes.gd` (SceneTree). Any future change to the asset-generation algorithm must be applied in both files or the generated output diverges from the editor-driven output.
  prevention: When a ticket depends on an EditorScript as a prior deliverable, the Planner must immediately flag that EditorScript as a PENDING_MANUAL dependency. If automation is required, the Spec Agent must design the replacement as a headless SceneTree script from scratch — not as a modification to the EditorScript — and document the maintenance fork explicitly. This extends the [godot_scene_generator_validation] learning that EditorScript logic should be extracted to RefCounted utilities; the corollary is that the EditorScript shell itself can never be the headless entry point.
  severity: high

- category: architecture
  insight: A per-family mutation drop system (`mutation_drop` export var plus per-instance override in the level scene) can coexist silently with a hardcoded default resolver (`infection_absorb_resolver.gd` using `DEFAULT_MUTATION_ID` unconditionally). The spec's own call chain analysis treated the export var as sufficient evidence that AC-3 was satisfied, but the resolver never read the export var. The two mechanisms existed independently with no wire between them until a second AC Gatekeeper invocation caught it.
  impact: AC-3 ("correct mutation on absorption") was initially marked as satisfied by the Spec Agent and the first AC Gatekeeper invocation. The second Gatekeeper invocation correctly identified that the resolver hardcoded the default and the export var was never consulted. This required a full implementation pass to thread `mutation_drop` through the call chain.
  prevention: When a spec verifies a call chain for correctness, it must trace each link to actual code — not infer that because an export var exists and a resolver exists, they are connected. Any AC that asserts "correct value X is passed to system Y" must name the exact line in each file where the handoff occurs. If no such line can be named, the AC is not satisfied.
  severity: high

- category: architecture
  insight: `Object.get("property_name")` returns `Variant`, not the property's declared type. Assigning that result directly to a typed `String` field causes an implicit coercion that GDScript strict mode treats as a type warning or error. Replacing `.get()` with direct typed property access on a narrowed-type variable both eliminates the coercion and makes the call site statically verifiable.
  impact: The GDScript reviewer caught this after initial tests passed, requiring a fix iteration. The fix also revealed that the field type (`_target_enemy`) could be narrowed from `Node3D` to `EnemyInfection3D`, improving static guarantees across the call chain.
  prevention: When a script reads a property from a dynamically-typed variable via `.get()`, the Code Reviewer Agent must flag it and require either: (a) narrowing the variable type to the concrete class so direct property access is valid, or (b) casting the `.get()` result explicitly with `as TypeName`. Bare `.get()` returning Variant assigned to a typed field is always a Static QA finding.
  severity: medium

- category: testing
  insight: The Engine Integration Agent placed two enemies at positions derived from its own spatial reasoning ("spread positions on X axis") rather than reading the spec's coordinate table. The spec defined `(0,1,4)` and `(0,1,-4)` (Z-axis spread); the implementation chose `(-6,1,0)` and `(6,1,0)` (X-axis spread). The tests encoded the spec's canonical coordinates and failed against the level file.
  impact: A second AC Gatekeeper invocation was required to identify the mismatch. The level positions then had to be corrected in a separate fix pass. The Engine Integration Agent's test run had passed only because the tests were written to the spec — the agent did not cross-check its authored positions against the spec before declaring implementation complete.
  prevention: The Engine Integration Agent must read the spec's position table and quote the exact coordinate values before editing any .tscn. After authoring, it must grep the node's transform origin in the .tscn text and confirm it matches the spec value verbatim before running tests.
  severity: medium

- category: process
  insight: AC-5 ("playable without debug tools") is structurally unverifiable headlessly. All structural proxies passed (no `@tool`, no debug-only nodes, valid enemy positions, no debug prints), but none confirm that the game is actually playable from the player's perspective. This AC class recurs on every ticket involving placed interactive content and will always require a human play session.
  impact: The ticket was held at BLOCKED awaiting human verification after all 54 automated tests passed. The AC Gatekeeper correctly declined to accept structural-only evidence for a playability AC, consistent with prior tickets. The blocking is correct behavior, not a workflow failure.
  prevention: Tickets with an AC containing the word "playable" or requiring subjective runtime experience should have that AC labeled `[MANUAL-ONLY]` at spec time with the exact Manual QA Checklist and the Playtest Result Recording steps. No structural proxy can satisfy a playability AC — this boundary is absolute.
  severity: low

### Anti-Patterns

- description: Verifying a data-flow AC by confirming that both the source (export var) and the sink (resolver) exist, without tracing the actual code path connecting them. Two systems that exist in parallel with no wire between them satisfy "both exist" trivially but fail "correct value flows end-to-end."
  detection_signal: An AC Gatekeeper or Spec Agent describes the call chain in prose but cannot cite a specific line in each intermediate file where the value is read and forwarded.
  prevention: For any AC asserting that a value produced at source A reaches consumer B, the gatekeeper must name the line in A where the value is produced, the function signature through which it is passed, and the line in B where it is consumed. If any link cannot be named, the AC is not satisfied.

- description: The Engine Integration Agent placing scene nodes at positions derived from spatial intuition rather than the spec's coordinate table. "Spread positions" is ambiguous — X-axis and Z-axis spreads are both valid interpretations.
  detection_signal: A position test (asserting a specific spec coordinate) fails against the authored level file even though the implementation agent reported a passing test run.
  prevention: The Engine Integration Agent must read the spec's position table and quote exact coordinate values before editing the .tscn. After editing, it must grep the authored transform origin and confirm it matches the spec before running tests.

- description: A headless `extends SceneTree` script that replicates an `@tool extends EditorScript` without a cross-reference comment in either file documenting the maintenance fork.
  detection_signal: Two files with overlapping generation logic (e.g. `load_assets.gd` and `generate_enemy_scenes.gd`) with no comment indicating they must be kept in sync.
  prevention: When a headless replication of an EditorScript is committed, add a comment at the top of both files: "MAINTENANCE NOTE: This file's generation logic is replicated from [other_file]. Changes to the generation algorithm must be applied to both files."

### Prompt Patches

- agent: Spec Agent
  change: "When verifying an AC that asserts a value flows from source A to consumer B (e.g., 'correct mutation is granted on absorption'), you must name the exact file and line where each intermediate handoff occurs. A prose description of the call chain is insufficient. If any link cannot be named with a file and line reference, mark the AC as NOT SATISFIED and document the missing link explicitly."
  reason: The AC-3 call chain (mutation_drop export var to resolver) was accepted as satisfied in prose by the first Gatekeeper invocation, but the resolver never read the export var. Requiring named line references for each link prevents this class of false positive.

- agent: Engine Integration Agent
  change: "When placing nodes in a level .tscn, read the spec's coordinate table and quote the exact Vector3 position values for each node before editing the file. After authoring the .tscn, search the file text for each node's transform origin and confirm it matches the spec's value verbatim. Do not derive positions from spatial reasoning — always use the spec's explicit coordinates."
  reason: ClawCrawlerEnemy and CarapaceHuskEnemy were placed at X-axis spread positions instead of the spec's Z-axis positions. The tests failed because they encoded the spec's correct coordinates. A pre-edit spec read and post-edit text confirmation would have caught the mismatch before running the test suite.

- agent: Code Reviewer Agent
  change: "Flag any `Object.get('property_name')` call whose return value is assigned to a typed variable without an explicit cast. GDScript strict mode treats implicit Variant-to-typed-field coercion as a warning or error. Require the caller to either: (a) narrow the receiving variable's type to the concrete class that declares the property and use direct field access, or (b) cast the result explicitly (e.g., `as String`). Report bare `.get()` assigned to a typed field as a Static QA defect."
  reason: `_target_enemy.get("mutation_drop")` returning Variant assigned to a String-typed field was caught by the reviewer but required a fix iteration. The fix also enabled narrowing the field type from Node3D to EnemyInfection3D, improving static verifiability across the call chain.

### Workflow Improvements

- issue: The AC Gatekeeper's first invocation accepted AC-3 based on the existence of both the `mutation_drop` export var and the resolver, without tracing the actual call path. The second invocation caught the hardcoded default. Two Gatekeeper invocations were needed because the first did not apply the "name every link" standard.
  improvement: The AC Gatekeeper prompt should require that for any data-flow AC (value produced at A, consumed at B), the verdict block must include a line-by-line call chain in the Evidence Matrix, not a prose summary. If the chain cannot be traced to specific lines, the AC must be marked NOT SATISFIED with a "missing link" note.
  expected_benefit: Eliminates the class of false-positive AC verdicts where a data flow is assumed connected because both endpoints exist. Reduces Gatekeeper invocation count for tickets with integration-heavy ACs.

- issue: The `extends SceneTree` replication of `load_assets.gd` is a permanent maintenance fork with no tracking mechanism. If the generation algorithm changes in `load_assets.gd`, `generate_enemy_scenes.gd` will silently diverge.
  improvement: When a headless replication of an EditorScript is committed, the Planner Agent should append a note to `project_board/KNOWN_ISSUES.md` flagging the maintenance fork, the two files involved, and the condition under which they must be kept in sync.
  expected_benefit: Prevents silent divergence between the editor-driven and headless-driven asset generation paths. Makes the maintenance obligation explicit and discoverable by future agents.

### Keep / Reinforce

- practice: The AC Gatekeeper's second invocation independently re-read the level .tscn and the resolver source code rather than forwarding the prior Gatekeeper's analysis. This re-reading found both the position mismatch and the hardcoded resolver that the first invocation missed.
  reason: Gatekeeper invocations should always re-read primary evidence files rather than deferring to prior verdicts. The second invocation's independent read produced a materially more accurate result. Each Gatekeeper run is an independent audit.

- practice: Threading `mutation_drop` through the call chain using optional/default parameters (`mutation_id: String = ""`) preserved backwards compatibility with all existing call sites. Zero existing tests regressed.
  reason: When adding a new data-flow parameter to an established API, defaulting it to a sentinel value allows all existing callers to be unmodified while new callers pass the real value. This is the correct pattern for threading optional context through a settled call chain without a breaking change.

---

## [M7-ACS] — @export + RefCounted serialization conflict and stale generated scenes caused a full impl-fix iteration
*Completed: 2026-03-31*

### Learnings

- category: architecture
  insight: In Godot 4.6.1, `@export` annotations are enforced at runtime in headless mode. Assigning a plain Object stub to an `@export var field: AnimationPlayer` raises "Invalid assignment" and leaves the property null, silently breaking all tests that depend on stub injection.
  impact: All 39 tests failed silently (controller returned early on null) after the initial implementation used `@export var animation_player: AnimationPlayer`. A full impl-fix iteration was required to remove the `@export` and resolve via `find_child()` + direct assignment bypass.
  prevention: For any Node-type dependency that must be injected by tests (not the editor inspector), declare the var as a plain `var field: Object = null` with no `@export`. Document the rationale in the spec. The Spec Agent must flag this pattern explicitly when the tested node type cannot be subclassed by test stubs.
  severity: high

- category: architecture
  insight: `RefCounted`-derived objects cannot be serialized through an `@export` in `.tscn` files. A `Node`-typed export rejects `RefCounted` assignment at runtime. The only correct injection pattern for a `RefCounted` dependency in a scene-file–instantiated Node is a `setup()` method or a plain `var` with `Object` typing.
  impact: `EnemyStateMachine extends RefCounted` caused the initial `@export var state_machine: EnemyStateMachine` spec to be incorrect. The spec had to be retroactively corrected after implementation discovered the constraint.
  prevention: The Spec Agent must check the inheritance chain of any dependency type before specifying it as `@export`. If the type extends `RefCounted` (not `Node`), the spec must require a `setup()` injection method or plain `var`, never `@export`.
  severity: high

- category: infra
  insight: The scene generator (`generate_enemy_scenes.gd`) was updated to add `EnemyAnimationController` and `AnimationPlayer` nodes to generated enemy scenes, but the generator was not re-run. The committed `.tscn` files were stale — they did not contain the new nodes. The AC Gatekeeper caught this by directly reading a `.tscn` file and finding the node absent.
  impact: The Gatekeeper correctly blocked completion and required an explicit re-run of the generator (commit 3bae3ea). Without the Gatekeeper's structural verification, the stale scenes would have shipped.
  prevention: Whenever a generator script is modified, the Implementation Agent must re-run it and commit the regenerated output files in the same changeset. A post-implementation checklist item must read: "If any generator script was modified, regenerate all outputs and include them in the commit."
  severity: high

- category: testing
  insight: A test file that statically types a variable as `EnemyAnimationController` will fail to parse if the implementation file does not yet exist, crashing the entire test runner and preventing all other suites from running.
  impact: The Test Designer recognized this and used dynamic `load("res://...")` instead of static class references, allowing the test file to parse cleanly and emit per-test failures rather than a runner crash.
  prevention: All test files for new scripts must use dynamic loading (`load(...).new()`) and untyped local vars when the target class file may not exist at test-break time. The Test Designer prompt should include this as an explicit requirement.
  severity: medium

- category: process
  insight: The spec's test file path (`tests/unit/test_enemy_animation_controller.gd`) did not match the actual project convention (`tests/scripts/enemy/`). The Test Designer had to resolve this ambiguity, creating a low-priority but persistent discrepancy documented in the final Gatekeeper verdict.
  impact: No test execution impact (the runner auto-discovers all `test_*.gd` files). However, the spec path was never corrected, leaving a documented inconsistency between spec and reality.
  prevention: The Spec Agent must verify that any explicitly named test file path matches an existing directory in the project before writing the spec. If `tests/unit/` does not exist, the spec must use the actual convention.
  severity: low

### Anti-Patterns

- description: Specifying `@export var field: SomeConcreteType` for a dependency that will be injected by unit test stubs, without verifying whether the concrete type is subclassable by test stubs or whether Godot 4 enforces the annotation at runtime.
  detection_signal: The spec lists a typed `@export` for any field that the ACS-8 "stub contract" section says must be assignable from a plain `Object` or inner class.
  prevention: When a spec simultaneously requires `@export` on a field and test stub injection into that same field, treat that as a contradiction and resolve it in the spec before handing off to implementation. The resolution is always: remove `@export`, use plain `var` with `Object` typing.

- description: Writing a spec that requires running a generator script but does not include "re-run the generator" as an explicit implementation step, leaving it implicit and easily skipped under time pressure.
  detection_signal: A spec section modifies a generator script's behavior but contains no explicit "regenerate outputs" step in the acceptance criteria.
  prevention: Any AC that modifies a generator script must pair with an AC that verifies the generated output files were regenerated, committed, and match the new generator behavior.

- description: The Impl Agent's first attempt used `@export var animation_player: Node` (weakened to Node) rather than removing the `@export` entirely. This was a partially correct fix — it resolved the type-enforcement crash but retained the serialization side-effect. Only the impl-fix pass, which used a plain `var`, produced the fully correct design.
  detection_signal: An impl-fix iteration that changes `@export var T` to `@export var Node` to unblock tests, rather than questioning whether `@export` is needed at all.
  prevention: When removing a typed `@export` to fix test injection, ask: "Does this field need to appear in the editor inspector or be serialized into the `.tscn`?" If no, remove `@export` entirely rather than weakening the type.

### Prompt Patches

- agent: Spec Agent
  change: "Before specifying any `@export` variable for a dependency that will be unit-tested via stubs: (1) check the dependency type's inheritance chain — if it extends `RefCounted`, the field must never be `@export`; (2) verify whether test stubs can subclass the declared type; (3) if tests must inject a plain Object stub, the field must be declared as `var field: Object = null` with no `@export`, and a `setup()` injection method must be provided. Document the rationale in the spec under 'Constraints'."
  reason: The root cause of the impl-fix iteration was a spec that required `@export var animation_player: AnimationPlayer` and `@export var state_machine: EnemyStateMachine` without accounting for Godot 4.6.1 runtime type enforcement and RefCounted serialization limits. An earlier spec-phase check would have avoided the full rework.

- agent: Implementation Agent
  change: "After modifying any generator script (`generate_enemy_scenes.gd` or equivalent), re-run the generator immediately and verify that all generated output files (`.tscn`, `.tres`, etc.) reflect the changes. Include the regenerated files in the same commit as the generator change. Do not submit for AC Gatekeeper review until the generated outputs have been regenerated."
  reason: The stale `.tscn` files (generator updated but not re-run) caused the Gatekeeper to block completion and required an additional commit. The fix is purely procedural: re-run the generator before closing the implementation stage.

- agent: Test Designer Agent
  change: "All test files for scripts that do not yet exist (test-break stage) must use dynamic loading: `var ScriptClass = load('res://path/to/script.gd')` and untyped vars (`var controller = ScriptClass.new()`). Never use static class-name references in test files for scripts that may not exist at test-break time. A parse error in one test file crashes the entire test runner and prevents all other suites from executing."
  reason: The Test Designer for M7-ACS correctly applied this pattern, preventing a runner crash. Encoding it as an explicit rule prevents future Test Designers from using static class references in test-break files.

### Workflow Improvements

- issue: The initial spec specified `@export` for both `animation_player` and `state_machine` without noting the Godot 4 runtime type enforcement constraint for headless test injection. The constraint was only discovered by the Implementation Agent at test-run time, requiring a full impl-fix pass and a retroactive spec-fix pass.
  improvement: Add a mandatory spec-phase check: for every `@export` field listed in the spec, confirm the type is either a primitive (float, int, String, bool) or a Node-subclass that test stubs can be assigned to without a runtime type error. If neither condition holds, remove `@export` from the spec before handoff.
  expected_benefit: Eliminates the class of impl-fix iterations caused by `@export` type mismatches discovered only at test time. The spec-fix pass (a second Spec Agent run) would also be unnecessary.

- issue: The spec explicitly named `tests/unit/test_enemy_animation_controller.gd` as the test file path, but this directory does not exist in the project. The Test Designer silently resolved this by using the correct convention, leaving the spec incorrect.
  improvement: The Spec Agent must verify that any named file path (especially test paths) resolves to an existing directory structure before emitting the spec. If the directory does not exist, either create it in scope or use an existing path.
  expected_benefit: Prevents spec-vs-reality discrepancies that future agents must silently work around, reducing compounding divergence across tickets.

### Keep / Reinforce

- practice: The AC Gatekeeper directly read a generated `.tscn` file to verify node structure rather than trusting that the generator had been re-run. This structural verification caught the stale scene files that implementation had missed.
  reason: For any ticket that modifies a generator and requires the output to contain specific nodes, the Gatekeeper must read the actual output file, not infer from the generator source. Generator "was updated" does not mean "was run."

- practice: The Test Designer added `play_call_count: int` to the stub class as a pure test-infrastructure additive that does not appear in the production ACS-8 spec. This allowed idempotency and latch tests to assert "no play() call was made" without modifying the production contract.
  reason: Augmenting test stubs with call-counting fields beyond the minimum required interface is the correct pattern for negative-assertion tests ("not called"). It is additive, does not contaminate production code, and makes test intent explicit.

## [split_animated_acid_spitter] — Module split: assert `__module__` and registry identity, not only re-export import path

*Completed: 2026-04-05*

### Learnings

- category: testing
  insight: After moving a class to a dedicated module while keeping a barrel import (`from animated_enemies import X`), existing tests that only check "import works" stay green even if the class body was accidentally duplicated or shadowed in the barrel file.
  impact: Added `AnimatedAcidSpitter.__module__ == 'src.enemies.animated_acid_spitter'` and `assertIs(ENEMY_CLASSES['acid_spitter'], animated_acid_spitter.AnimatedAcidSpitter)` to lock the split contract.
  prevention: For any "extract to module" refactor, add one test for defining `__module__` and one for object identity against the canonical module.
  severity: medium

## [split_animated_adhesion_bug] — No significant learnings identified.

*Completed: 2026-04-05* (same extract-and-register pattern as `split_animated_acid_spitter`; tests and spec followed the established template.)

## [split_animated_carapace_husk] — No significant learnings identified.

*Completed: 2026-04-05* (same pattern: `__module__` + `BPG_ADV_SPLIT_03` registry identity; docs and spec mirrored prior split tickets.)

## [split_animated_claw_crawler] — No significant learnings identified.

*Completed: 2026-04-05* (same pattern as prior animated splits: `test_BPG_CLASS_17b` for `__module__`, `BPG_ADV_SPLIT_04` for registry `is` identity; removed unused `create_quadruped_armature` and top-level `EnemyBodyTypes` import from `animated_enemies.py` after extraction.)

## [split_animated_ember_imp] — No significant learnings identified.

*Completed: 2026-04-05* (same extract-and-register pattern; added `TestEmberImpClass` + `BPG_ADV_SPLIT_05`; removed unused `math` / `Euler` / `create_humanoid_armature` / `create_all_animations` from `animated_enemies.py` after extraction.)

## [split_animated_tar_slug] — No significant learnings identified.

*Completed: 2026-04-05* (same pattern: `TestTarSlugClass` + `BPG_ADV_SPLIT_06`; `animated_enemies.py` reduced to factory + imports after removing unused `BaseEnemy` and geometry/material imports that only served the inlined class.)

---

# Learning Output — [animated_enemy_registry_cleanup]

## Learnings
- category: process
  insight: A ticket marked BLOCKED on stale dependency state blocks progress even when CHECKPOINTS.md and `maintenance/done/` already prove all deps complete; resuming autopilot should verify the filesystem gate before returning to Human.
  impact: Would have stopped at BLOCKED without advancing the pipeline.
  prevention: On `/ap-continue`, list `maintenance/done/` for named dependency slugs and reconcile with the ticket Blocking Issues field.
  severity: medium

- category: architecture
  insight: Placing `AnimatedEnemyBuilder` in `animated/registry.py` while leaf modules stay as `animated_<slug>.py` siblings preserves a one-way import graph (registry → leaves only).
  impact: Avoids circular imports if per-enemy modules ever need shared registry constants.
  prevention: Keep `animated/__init__.py` as re-exports only; do not import registry from leaf enemy modules.
  severity: low

## Anti-Patterns
- description: Leaving a long-lived shim module after migration duplicates the “source of truth” for imports and confuses docs/tests.
  detection_signal: Two public paths (`animated_enemies` vs `animated`) both documented as canonical.
  prevention: After grep-clean migration, delete the old module in the same change set as test/doc updates.

*Completed: 2026-04-05*

---

# Learning Output — [base_models_split_by_archetype]

## Learnings
- category: process
  insight: A ticket can sit at IMPLEMENTATION_GENERALIST while the refactor already exists only on disk; `/ap-continue` should diff against `git status` before redoing work.
  impact: Avoids duplicate edits and speeds closure to AC Gatekeeper + commit.
  prevention: On resume, run `git status` on spec paths and pytest before invoking implementation agents.
  severity: low

- category: infra
  insight: Spec BMSBA-5.3 mandates ruff on touched files, but the package may not ship ruff — document Static QA as skipped with evidence rather than blocking COMPLETE.
  impact: Unblocks closure when lint tool is absent.
  prevention: Align spec templates with `pyproject.toml` optional dev deps or add ruff to dev extras.
  severity: low

## Anti-Patterns
- description: Leaving a deleted monolith (`base_models.py`) and new package untracked while the ticket advances through test stages.
  detection_signal: `git status` shows `D base_models.py` and `?? base_models/` with green pytest.
  prevention: Commit implementation in the same session as IMPLEMENTATION_GENERALIST handoff or immediately on resume.

*Completed: 2026-04-05*

---

## [MAINT-EAPD] — Headless tests must not use `ClassDB` for GDScript `class_name`; defer tickets need explicit pipeline waiver alignment

*Completed: 2026-04-05*

### Learnings

- category: testing
  insight: In headless Godot runs (`run_tests.gd`), GDScript global classes registered via `class_name` are not reliably visible on `ClassDB` the same way as engine types.
  impact: A naive `ClassDB.class_exists("EnemyAnimationController")`-style assertion would be flaky or false relative to editor expectations.
  prevention: Assert canonical script identity by loading the `GDScript` resource, checking `get_global_name()`, and matching `resource_path` to the expected `res://` path.
  severity: medium

- category: process
  insight: Default autopilot stage progression (e.g. advancing to `TEST_DESIGN` after Spec) can contradict an execution plan that explicitly waives implementation and test stages for “defer-only” closure.
  impact: Agents operated under medium-confidence assumptions about which instruction wins until reconciled via `NEXT ACTION` / Reason text.
  prevention: For defer placeholders, the handoff Reason must state AC-1-only scope (policy + tests, no prod edits) and that waived stages are not closure gates.
  severity: medium

- category: testing
  insight: Maintenance suites that guard shared state→clip semantics may intentionally couple tests to private resolvers via `call()` / `has_method()` so silent mapping drift fails loudly.
  impact: Accepts brittleness to internal refactors in exchange for catching the intended regression class; future policy-injection work stays explicitly out of scope for that suite.
  prevention: When adding such tests, document in-suite (`# CHECKPOINT` or file header) which future ticket owns the alternative (e.g. AC-2) coverage.
  severity: low

### Anti-Patterns

- description: Using `ClassDB.class_exists()` as the sole proof that a project `class_name` exists in headless CI.
  detection_signal: Tests or specs mandate ClassDB checks for GDScript globals; green locally in editor but ambiguous or wrong under headless runner.
  prevention: Prefer loaded-script identity checks (`GDScript` + path + global name) for project scripts.

### Prompt Patches

- agent: Test Designer Agent
  change: "For headless test suites, do not use `ClassDB.class_exists()` alone to assert a GDScript `class_name` global exists; load the script resource, assert `GDScript.get_global_name()` and `resource_path` match the canonical `res://` file."
  reason: Avoids false negatives and editor/headless divergence for global class registration.

- agent: Autopilot / Orchestrator (or Planner Agent)
  change: "When the execution plan marks TEST_DESIGN, TEST_BREAK, and IMPLEMENTATION as waived for closing a defer-only ticket, set `NEXT ACTION` Reason to state explicitly that downstream agents run AC-1-only (documentation and allowed policy tests) and must not treat waived stages as mandatory code-change gates."
  reason: Resolves conflict between default stage FSM and ticket-specific closure rules without ad hoc per-run interpretation.

### Workflow Improvements

- issue: Spec-complete tickets that defer implementation still enter the full stage names in order, which reads like a full pipeline despite waiver.
  improvement: Add a maintenance/defer template flag (or standard Reason boilerplate) that names the first in-scope agent after Spec and labels others N/A for closure in one place.
  expected_benefit: Reduces medium-confidence checkpoint churn on “which pipeline wins.”

### Keep / Reinforce

- practice: Satisfying AC-1 on architecture deferrals with a focused maintenance test file that encodes policy invariants (path, exports, shared behavior contracts) without editing production scripts.
  reason: Gives traceable, CI-enforced evidence for “no preemptive refactor” decisions.

---

## [MAINT-EMMU] — SSOT maps need subtree scans and consumer parity; gatekeeper-before-review needs a GDScript safety pass

*Completed: 2026-04-05*

### Learnings

- category: testing
  insight: Enforcing “exactly one literal under `scripts/asset_generation/`” is stronger with a **recursive directory scan** (e.g. walk the tree and flag `const MUTATION_BY_FAMILY := {` patterns) than relying on a single known file or repo-wide `rg` without a scoped subtree rule—duplicates can land in sibling files under the same folder.
  impact: Catches second definitions if the map or copy-paste spreads within the generation subtree; aligns with EMU-QA-1 intent beyond the canonical module path.
  prevention: For SSOT-by-path ACs, encode tests that enumerate `DirAccess` (or equivalent) under the declared root and assert count/location of forbidden patterns.
  severity: medium

- category: architecture
  insight: **`load_assets.gd` and `generate_enemy_scenes.gd` must stay in strict-mode parity** for shared helpers (e.g. AABB aggregation, capsule-related mesh typing): typed `Array[MeshInstance3D]`, explicit `AABB` / `Transform3D` / `Vector3`, and the same collision-shape assumptions. Touching one consumer for a shared preload can surface parse or type errors in the other when headless loads the `@tool` script.
  impact: Implementation aligned AABB helpers so `load()` of the editor script parsed under strict mode; without parity, green mutation-map tests could mask a broken editor pipeline.
  prevention: When editing either consumer, diff helper signatures and typing against the twin script before handoff; add or extend a minimal parse/load test if the project already loads these scripts headless.
  severity: medium

- category: process
  insight: If **Acceptance Criteria Gatekeeper runs before GDScript Reviewer** in a given run, treat that as mis-ordered closure: schedule **GDScript review immediately after gatekeeper** (or reorder the pipeline) so strict-mode, typing, and lifecycle issues on touched scripts are not skipped after “suite green.”
  impact: Reduces risk of marking COMPLETE while review-only findings remain.
  prevention: Document the corrective order in autopilot resume notes when stage FSM does not match agent charter order.
  severity: low

### Anti-Patterns

- description: Asserting SSOT only by checking the new module file exists, without scanning the **whole** subtree named in the AC for duplicate map literals.
  detection_signal: AC says “under `scripts/asset_generation/`” but tests only open one path; a second file could reintroduce `const MUTATION_BY_FAMILY := {`.
  prevention: Recursive scan + assert single literal location; keep `is_same()` / preload identity checks for runtime reference sharing.

- description: Changing imports or constants in `load_assets.gd` without reconciling **typed helper parity** with `generate_enemy_scenes.gd`.
  detection_signal: Headless parse errors or Variant warnings only when the editor script is loaded; asymmetric `Array` typing or missing explicit geometry types.
  prevention: Pair-edit both consumers when they share generation geometry helpers.

### Prompt Patches

- agent: Test Designer Agent
  change: "For tickets that require a single const map literal under a directory subtree (e.g. `scripts/asset_generation/`), add a test that **recursively walks that directory** (via `DirAccess` or project equivalent) and fails if more than one forbidden pattern (e.g. `const MUTATION_BY_FAMILY := {`) appears outside the canonical file; combine with preload/`is_same()` assertions so behavior and filesystem SSOT both hold."
  reason: Prevents duplicate literals in sibling files that a one-file test would miss.

- agent: Implementation Generalist Agent
  change: "When modifying `load_assets.gd` or `generate_enemy_scenes.gd` for shared asset-generation data, **diff AABB/capsule/mesh helper blocks** between the two scripts and align typed arrays and explicit `AABB`/`Transform3D`/`Vector3` usage so both parse under project strict mode and headless `load()` of the `@tool` script matches the SceneTree generator."
  reason: Avoids editor-only parse failures after consumer-only edits.

- agent: Autopilot / Orchestrator (or Planner Agent)
  change: "If the pipeline orders **Acceptance Criteria Gatekeeper before GDScript Reviewer**, insert a **mandatory GDScript Reviewer pass after gatekeeper** (or reschedule gatekeeper after review) so COMPLETE is not issued without script review on all touched `.gd` files."
  reason: Corrects weak closure when automated stage order inverts the intended review-then-signoff sequence.

### Workflow Improvements

- issue: Stage FSM may advance to gatekeeper while GDScript review is still pending or ordered later, weakening “review before ship” intent.
  improvement: Define a single canonical order (Spec → tests → implementation → **GDScript review** → **gatekeeper**) or an explicit post-gatekeeper review exception with a logged reason.
  expected_benefit: Fewer COMPLETE states with unreviewed script diffs.

### Keep / Reinforce

- practice: SSOT tests that preload the canonical module and use **`is_same()`** to prove consumers share **dictionary identity**, not just equal contents.
  reason: Catches duplicate literals that happen to match byte-for-byte.

- practice: Test Breaker hardening for **alternate dict declaration forms** and acyclic preload graph checks on the map module.
  reason: Reduces bypass via syntax variants or accidental consumer preload from the SSOT file.

---

## [MAINT-ESEG] — Shared enemy root script resolver, dual-consumer wiring, and unsafe stem hardening

*Completed: 2026-04-05*

### Learnings

- category: architecture
  insight: Choosing which gameplay script attaches to generated enemy roots is **shared policy**: a single resolver module must be the only place that encodes override directory + fallback base path; consumer scripts should not embed override-path literals so drift is caught by tests.
  impact: Ticket AC named `generate_enemy_scenes.gd` explicitly; correct behavior still required the same resolution in `load_assets.gd` and a shared API both call before `set_script`.
  prevention: Centralize path rules in one preloadable module; add tests that fail if either consumer hard-codes `res://scripts/enemies/generated/` (or equivalent) instead of calling the resolver.
  severity: medium

- category: testing
  insight: **`ResourceLoader.exists` on a formatted path is not sufficient** for adversarial `family_name` values: stems with path separators or `..` can escape the intended single-file layout unless the resolver rejects or normalizes them.
  impact: Test Breaker stage extended the suite with unsafe-stem cases; implementation added sanitization and empty-stem → base behavior.
  prevention: For any resolver that builds `res://.../<user-derived-segment>.gd`, encode tests for empty stem, `/`, `\`, and `..`; require the resolver to fall back to the safe default path when input is unsafe.
  severity: medium

- category: architecture
  insight: When some call sites already pass `EnemyNameUtils.extract_family_name` output and others might pass a raw GLB basename, the **resolver boundary** should normalize using the same utility when input matches basename-shaped patterns, instead of assuming a single caller convention.
  impact: Avoids subtle “works in CLI, wrong override in editor” or vice versa if one pipeline passes a different string shape.
  prevention: Document accepted input shapes on the resolver; implement normalization once inside the resolver before `exists` + `load`.
  severity: medium

- category: process
  insight: Spec that allows **implementer-chosen module filename** but leaves the **public method name** implicit can create medium-confidence mismatch risk between Test Designer fixtures and Implementation unless names are aligned in the same revision.
  impact: Checkpoint noted method naming as implementer-facing; unnecessary churn if tests and code disagree on `resolve_*` spelling.
  prevention: Either fix the resolver’s public method name in the spec handoff or have Test Designer quote the exact callable expected by tests in WORKFLOW STATE / ticket so Implementation matches in one pass.
  severity: low

### Anti-Patterns

- description: Duplicating “if override exists use X else base” conditionals in `generate_enemy_scenes.gd` and `load_assets.gd` instead of a shared resolver.
  detection_signal: Two files both mention override directory logic or both format the same `res://` pattern; tests cannot assert a single implementation.
  prevention: One module, two call sites, tests assert both consumers invoke it.

- description: Treating **`exists(formatted_path)`** as the only guard when the formatted path incorporates caller-controlled segments.
  detection_signal: Resolver concatenates `family_name` into a path without validating characters; security or layout bugs on malicious or mistaken stems.
  prevention: Reject or normalize unsafe stems; test adversarial inputs explicitly.

### Prompt Patches

- agent: Planner Agent
  change: "When ticket AC names only `generate_enemy_scenes.gd` for enemy asset output but `project_board/LEARNINGS.md` documents **editor vs headless parity** with `load_assets.gd`, add **`load_assets.gd` to blast radius and success criteria** in the execution plan and require the Spec Agent to state both consumers must call the same resolver."
  reason: Prevents shipping resolver logic in only one pipeline because the AC line was incomplete.

- agent: Test Breaker Agent
  change: "For resolvers that build `res://scripts/.../<stem>.gd` from a string parameter, add cases for **empty stem**, path separators, and `..`; assert the resolver returns the **safe base script path** and never a path that escapes the single-file layout under the override directory."
  reason: `ResourceLoader.exists` alone does not substitute for input validation on formatted paths.

- agent: Implementation Generalist Agent
  change: "When wiring `enemy_root_script_resolver` (or equivalent), if callers may pass either a **raw GLB basename** or **`EnemyNameUtils.extract_family_name` output**, normalize inside the resolver using `EnemyNameUtils.extract_family_name` when the input matches basename-shaped patterns before override lookup."
  reason: Keeps CLI and `@tool` pipelines aligned without requiring every call site to pre-normalize identically.

- agent: Spec Agent
  change: "When introducing a new shared module with a single required entrypoint, either **name the public method** in REQ text (e.g. `resolve_enemy_root_script_path`) or explicitly state ‘Test suite defines the callable name; implementation must match tests’ to avoid spec vs test-design drift."
  reason: Reduces revision churn when filename is flexible but API surface is not.

### Workflow Improvements

- issue: Acceptance criteria can list one generator file while repo precedent mandates two consumers stay in lockstep for the same behavior.
  improvement: Maintenance ticket template or planner checklist: for `scripts/asset_generation/*` behavior, grep for **`load_assets.gd` + `generate_enemy_scenes.gd`** and require dual-consumer language in spec AC when both attach scripts or metadata to generated enemies.
  expected_benefit: Fewer “AC satisfied in one file only” handoffs.

### Keep / Reinforce

- practice: Tests that **forbid embedding** the override directory literal in consumer sources while asserting both call the shared resolver.
  reason: Makes duplicate path logic mechanically detectable in CI.

- practice: A minimal **`extends EnemyBase`** fixture under `scripts/enemies/generated/` used only to prove “override exists” path selection, without mass-regenerating committed `.tscn` files.
  reason: Verifies AC for present-override behavior without churning all generated scenes when defaults stay on `enemy_base.gd`.

---

## [MAINT-ETRP] — Leaf slug registry + shared accessors prevent CLI vs `get_*()` drift

*Completed: 2026-04-05*

### Learnings

- category: process
  insight: If `main.py` list/help paths and library helpers like `EnemyTypes.get_animated()` are allowed to carry **independent copies** of the same slug enumeration, the copies will eventually diverge when one path is updated and the other is not; the fix is a **single authoritative sequence** (registry tuples consumed by `EnemyTypes` and by any CLI or generation entrypoint).
  impact: Ticket acceptance criteria explicitly required list commands and smart generation to stay aligned; parallel literals would violate that silently.
  prevention: Wire listing and smart pipelines through the same module or `get_*()` accessors; lock equality with frozen pytest expectations and, when AC demands it, a CLI smoke that compares visible output to those accessors.
  severity: medium

- category: architecture
  insight: Extracting immutable slug lists into a **leaf** `enemy_slug_registry`-style module with a documented import DAG—registry **never** imports `constants`, while `constants.EnemyTypes` may import the registry—turns “avoid circular imports” from a hope into a structural constraint enforceable by review and tests.
  impact: REQ-ETRP-002 and adversarial AST checks made violations machine-detectable rather than latent load-order bugs.
  prevention: For any growing aggregator module, peel stable string tuples to a leaf file; document one-way imports; add static or AST guards against upward imports from the leaf.
  severity: medium

- category: testing
  insight: In-package pytest often uses a `sys.path` layout that differs from running `main.py`; a **fresh subprocess** import-order smoke that mirrors the real entrypoint can surface import graphs that pass under pytest but fail at CLI launch.
  impact: Checkpoint called out isolating `utils.*` loading from pytest’s `src.utils` behavior; REQ-ETRP-004 encoded subprocess import order.
  prevention: For import-DAG tickets, include a minimal subprocess test sequence specified in the spec (e.g. import `utils.constants` then `utils.enemy_slug_registry` without `ImportError`).
  severity: medium

### Anti-Patterns

- description: Maintaining slug enumerations as duplicate literals in `main.py` (choices, help, or manual loops) while `EnemyTypes.get_animated()` / `get_static()` remains the “real” list elsewhere.
  detection_signal: Grep shows string slugs or tuples in CLI-only code but not routed through `EnemyTypes` or `enemy_slug_registry`; new enemy added in one place only.
  prevention: Single source: registry tuples or `get_*()`; CLI and smart generation both consume that surface.

- description: Creating a “registry” module that still imports `constants` (or anything that transitively loads `constants`) for convenience.
  detection_signal: New file appears to centralize data but pulls in the fat constants package; intermittent circular import errors depending on entrypoint.
  prevention: Keep registry as data-only leaf; compose in `constants` or other aggregators; AST or lint rule forbidding registry → `constants` imports.

### Prompt Patches

- agent: Spec Agent
  change: "When acceptance criteria require CLI list commands and generation code to **agree on type lists**, add an REQ that names the **single source of truth** (e.g. `enemy_slug_registry` tuples and `EnemyTypes.get_animated()` / `get_static()`) and explicitly forbids maintaining a **second parallel enumeration** in `main.py` or argparse-only code."
  reason: Prevents main.py list drift vs `get_*()` at specification time.

- agent: Implementation Generalist Agent
  change: "When extracting registries from `constants.py`, implement **one-way imports only**: the registry module must not import `constants` or modules that transitively import it; add tests that **AST-scan the registry** for forbidden imports and a **subprocess import-order smoke** aligned with how `main.py` resolves `utils`."
  reason: Makes the registry extraction pattern repeatable and catches pytest-only green states.

- agent: Acceptance Criteria Gatekeeper Agent
  change: "If the ticket AC requires CLI list behavior to match `EnemyTypes` / registry, treat **`main.py list` (or equivalent) exit 0 and output consistency** as blocking evidence before COMPLETE—not optional follow-up—unless an automated pytest harness is specified that exercises the same argparse path without Blender."
  reason: Autopilot deferred CLI smoke to gatekeeper; explicit blocking criteria avoids assuming someone will run the command later.

### Workflow Improvements

- issue: Multi-stage plans can mark “CLI list integration” as task 6 while an autopilot run stops at green pytest and assumes gatekeeper will run `main.py list`.
  improvement: Either fold a no-Blender CLI assertion into pytest (same wiring as `main.py list`) or require gatekeeper checklist item with logged output before marking COMPLETE.
  expected_benefit: AC “list commands still agree” is provably satisfied every time, not only when a human remembers the smoke.

### Keep / Reinforce

- practice: Immutable `ANIMATED_SLUGS` / `STATIC_SLUGS` tuples, `EnemyTypes` delegation, frozen snapshot contract tests, disjoint-set adversarial check, subprocess import-order smoke, and AST ban on registry importing `constants`.
  reason: Combines string freeze, DAG safety, and entrypoint-realistic imports in one maintainable bundle.

---

## [MAINT-EMSI] — Uniform model scale: preserve literal kwargs at multiplier 1.0; align mocks and fail-fast validation tests

*Completed: 2026-04-05*

### Learnings

- category: testing
  insight: A “no-op” uniform scale of `1.0` must not always flow through generic multiply helpers: multiplying tuple components by `1.0` can widen integer literals to floats and break strict backward-compatibility assertions on mocked primitive kwargs versus legacy code.
  impact: Implementation explicitly short-circuited scaling when `self.scale == 1.0` so call logs stay identical to pre-change behavior for mixed int/float geometry inputs.
  prevention: For default-multiplier APIs, add a fast path that returns inputs unchanged at `1.0` when tests or exporters assert byte- or tuple-level parity with legacy.
  severity: medium

- category: process
  insight: Early planning assumed a distinct instance field name (`geometry_scale` / `uniform_scale`) to avoid colliding with Blender object `scale`; the frozen spec chose `instance.scale` to match the ticket and EMSI-1, which is the right tradeoff but makes planning-only docs potentially misleading if read in isolation.
  impact: Low rework here (spec won), but it is an avoidable moment of ambiguity for implementers skimming checkpoints out of order.
  prevention: At spec freeze, add a one-line “resolution” when planning checkpoints assumed a different public name or shape than the REQ IDs.
  severity: low

- category: testing
  insight: Asserting an **empty** primitive call log for invalid scale catches validation that runs too late (after geometry calls), which a mere `ValueError` assertion might miss if order is wrong.
  impact: Test Breaker added fail-fast / mutation cases tied to EMSI-2.
  prevention: For validated builder/factory APIs backed by mocked side effects, pair domain errors with “no work performed” signals (empty logs, call counts) where the spec allows.
  severity: medium

- category: architecture
  insight: Observable contract for uniform scaling should pin whether parity is defined on **kwargs to primitives** vs a parent transform; an implementation that only applies a root empty still must satisfy the chosen observable or update tests with spec-backed equivalence.
  impact: Checkpoints flagged medium risk if implementation diverged from tuple-multiply reference without test updates.
  prevention: Spec should name the primary mock-observable (e.g. scaled `location` / primitive `scale` tuples) and treat alternate strategies as explicitly equivalent with adjusted tests.
  severity: low

### Anti-Patterns

- description: Implementing scale helpers as unconditional `component * scale` including when `scale == 1.0`, breaking int/float identity in asserted Blender primitive kwargs.
  detection_signal: Parity tests fail only on default scale with “expected (0, 0, z) got (0.0, 0.0, z)” or similar tuple drift.
  prevention: Short-circuit at `1.0` or preserve original tuple objects when the multiplier is exactly one and parity is required.

- description: Patching `create_sphere` / `create_cylinder` on a different import path than the archetype module under test, so mocks never fire and tests false-green or miss regressions.
  detection_signal: New test file passes but does not intercept calls; differs from sibling factory tests’ patch targets.
  prevention: Copy patch targets from the established factory test module for the same archetype package layout.

### Prompt Patches

- agent: Implementation Generalist Agent
  change: "When adding a default `scale` (or similar uniform multiplier) to geometry builders, if acceptance tests assert **kwargs parity with legacy at the default multiplier**, implement a **`scale == 1.0` short-circuit** that returns locations/extents unchanged so integer literals are not widened to floats by multiply-by-1.0."
  reason: Prevents spurious default-scale failures while keeping non-1.0 paths mathematically uniform.

- agent: Test Designer Agent
  change: "For Blender procedural tests that mock `create_sphere` / `create_cylinder`, state in the test module (or ticket notes) that patches must target the **same module attribute paths** as existing factory tests in `tests/enemies/` so mocks bind where archetypes invoke primitives."
  reason: Avoids silent non-intercepted mocks across package import boundaries.

- agent: Test Breaker Agent
  change: "For validated factory/builder APIs with mocked side effects, add at least one case where **invalid input yields both the specified exception and zero recorded primitive (or IO) calls**, to catch validation ordered after work."
  reason: Strengthens fail-fast guarantees beyond exception type alone.

### Workflow Improvements

- issue: Planning checkpoints can recommend API or field names that the spec later overrides without an explicit bridge note.
  improvement: Spec Agent adds a short “Planning resolution” bullet when REQ text contradicts the latest planning checkpoint assumption.
  expected_benefit: Implementers and reviewers do not treat stale planning confidence as authoritative.

### Keep / Reinforce

- practice: Adversarial additions—`math.nextafter` boundaries, large finite scale, fractional non-power-of-two scale, identical primitive **sequence** across scales for determinism, positional vs keyword `scale`, `int` vs `float` equivalence, unknown-type fallback with scale, and direct `HumanoidModel(..., invalid scale)` validation.
  reason: Small surface-area API changes still benefit from breadth without a full Blender render.

---

## [MAINT-HCSI] — Design-space vs global HUD tests; hybrid scaling when a single parent `scale` fails subtree uniformity

*Completed: 2026-04-05*

### Learnings

- category: testing
  insight: When a packaged HUD gains a scale transform or reparenting under `CanvasLayer`, tests that asserted raw scene `offset_*` on former direct children must distinguish **authoring/design space** from **`get_global_rect()` (transformed space)** so default-scale parity (HCSI-style ACs) stays meaningful without fighting the new root.
  impact: `test_player_hud_layout.gd` gained a design-space helper; `test_fusion_opportunity_room.gd` viewport bounds moved to global rects where the contract is on-screen geometry.
  prevention: For UI tickets that add scale or intermediate roots, plan coordinated updates: design-space helpers for scene-authored numbers, global rects for player-visible bounds and cross-widget ratios.
  severity: medium

- category: architecture
  insight: A single `Control.scale` on a container is not always enough for **uniform global-rect scale factors** across all descendants under `CanvasLayer` (e.g. a wide `Hints` strip with nested labels); a hybrid may be required—resize the container via scaled `offset_*` and apply `scale` to selected children so ratios match sibling HUD bars in tests.
  impact: Implementation checkpoint documents why parent-only scaling failed ratio checks for hints vs HPBar and how base pack dimensions must stay aligned with the scene at `hud_scale == 1.0`.
  prevention: Validate scale invariants using **multiple node roles** (top-level bar, nested label, container vs leaf) before locking a one-container approach; document any script constants that duplicate scene layout numbers.
  severity: medium

- category: testing
  insight: Adversarial cases for a float export—fractional scale, `1.0 → 2.0 → 1.0` idempotency, int-like `set()`, non-finite values, non-positive values, and a high stress ratio—surface clamp/validation gaps and “only tested at one multiplier” mutations quickly.
  impact: Test Breaker run reported expected pre-implementation failures; post-implementation suite green with explicit sanitization behavior.
  prevention: For designer-facing numeric exports on UI roots, mirror this breadth so setter semantics are pinned before reviewers assume a single happy-path multiplier is sufficient.
  severity: medium

- category: process
  insight: Early planning correctly flagged that `CanvasLayer` roots are not `Control`-scalable as-is, that reparenting risks `get_node` contracts in scripts, and that **non-`tests/ui/`** suites load the same packaged scene—those assumptions prevented silent breakage in fusion/start-flow tests.
  impact: Spec and test design explicitly extended level tests where viewport geometry mattered.
  prevention: For shared packaged scenes, keep a standing checklist: script path contracts, root type/name tests, and grep for `game_ui` (or equivalent) outside the primary UI test directory.
  severity: low

### Anti-Patterns

- description: Proving uniform HUD scale using only one widget class (e.g. a single progress bar) while `Hints`/labels live in a differently structured subtree.
  detection_signal: Global-rect width/height ratios diverge between bars and hint leaves at the same `hud_scale`.
  prevention: Add cross-role triangulation tests (implemented: `MutationIcon1` vs `HPBar`, `Hints` container vs `MoveHint`) before signing off on mechanism.

- description: Script constants for “base” layout sizes that can drift from the `.tscn` without a documented sync obligation.
  detection_signal: Scale `1.0` looks wrong only for one subtree after scene edits; tests pass on CI until someone opens the game.
  prevention: Comment or REQ that base width/height constants must match authoring offsets at default scale, or drive them from a single exported source.

### Prompt Patches

- agent: Implementation Frontend Agent
  change: "When implementing uniform HUD scale under `CanvasLayer`, verify **`get_global_rect()` scale ratios on representative leaves** (not only top-level bars). If parent-only `Control.scale` fails uniformity for a subtree (e.g. wide hint strips with nested labels), use a **documented hybrid** (e.g. scaled container `offset_*` plus per-child `scale`) and keep any script **base pack constants** aligned with the scene at default scale."
  reason: Avoids false confidence from a mechanism that looks uniform on one node type only.

- agent: Test Designer Agent
  change: "Before implementation lands, if layout tests assert scene `offset_*` on nodes that may be **reparented or scaled**, introduce or preserve helpers that read **design/authoring space** separately from **`get_global_rect()`**, and update **non-`tests/ui/`** consumers that assert viewport or HUD geometry to use the contract the spec defines for transformed space."
  reason: Preserves meaningful default-scale parity and prevents fusion/level tests from asserting the wrong coordinate space.

- agent: Planner Agent
  change: "When a ticket changes a **packaged UI scene** root or child structure, require an explicit inventory of **all test files** (not only `tests/ui/`) that instantiate or assert that scene, including **script `get_node` / path contracts**."
  reason: Catches level/integration tests that would otherwise break only after merge.

### Workflow Improvements

- issue: Adversarial tests for non-finite and non-positive float exports presuppose setter semantics (clamp vs reject) that the spec may only hint at.
  improvement: For UI scale REQ IDs, add one line in the spec: **expected behavior for non-finite and `≤ 0` writes** (even if defensive) so implementation and tests agree in one pass.
  expected_benefit: Fewer round-trips between Test Breaker expectations and implementer interpretation.

### Keep / Reinforce

- practice: Test Breaker’s fractional scale, order/idempotency, stress ratio, type coercion, and non-finite/non-positive cases on the same export.
  reason: Efficiently guards float UI knobs against narrow happy-path implementations.

- practice: Gatekeeper re-run of full `run_tests.sh` with AC matrix tied to named tests and script/scene evidence.
  reason: Clear closure traceability for maintenance HUD tickets.

---

## [MAINT-SLEEV] — Ticket `run/main_scene` prose vs repo; SLEEV-4.2 honest deferral; ADV ordering and source-scene guards

*Completed: 2026-04-05*

### Learnings

- category: process
  insight: Maintenance tickets can embed stale `project.godot` assumptions (e.g. `run/main_scene` target) that no longer match the repo; closure must not pretend the ticket prose is true.
  impact: Ticket Description/AC3 named `test_movement_3d.tscn` as main scene; repo had `procedural_run.tscn`. Spec **SLEEV-4.2** and Validation Status documented drift; tests enforced **SLEEV-4.1** only (main scene must not reference the new legacy duplicate).
  prevention: For any AC that pins `project.godot`, add a spec branch up front: exact equality, or documented actual value + narrowed automated contract + optional follow-up policy ticket.
  severity: medium

- category: testing
  insight: When a new scene is added by duplication, ordering ADV/source invariants before the “new file exists” gate keeps CI failing exactly once on the missing asset while still protecting the canonical scene and `run/main_scene` loadability.
  impact: Test Breaker ran source-sandbox GLB/`model_scene` guards and `project.godot` PackedScene checks before **SLEEV-1.1** so regressions surface alongside the single expected pre-implementation failure.
  prevention: For duplicate-scene maintenance, structure tests so source and global config assertions are not skipped behind a missing-file early return.
  severity: medium

- category: testing
  insight: Stricter file-text assertions than the normative spec bullets need an explicit trail so implementers do not treat failures as “spec bug.”
  impact: Tests forbade any `.glb` in `[ext_resource]` on the legacy level (stricter than four named paths); Test Designer documented this as intentional for devlog intent.
  prevention: When tests strengthen beyond REQ text, add a one-line comment or amend the spec so the contract is single-sourced.
  severity: low

### Anti-Patterns

- description: Validating a ticket by silently treating ticket `run/main_scene` prose as satisfied without reading `project.godot` or updating AC with traceability.
  detection_signal: Validation Status or docs claim parity with ticket Description while `grep`/`project.godot` shows a different path.
  prevention: Quote actual config in Validation Status and cite the spec clause that narrows or defers the assertion.

- description: Only asserting the new duplicate scene while dropping invariants on the original sandbox, allowing accidental removal of `model_scene` overrides on the live level.
  detection_signal: Legacy scene passes but `test_movement_3d.tscn` loses GLB `ext_resource` or `model_scene` lines.
  prevention: Keep **ADV-SLEEV-source_*** (or equivalent) checks on the canonical scene in the same test module.

### Prompt Patches

- agent: Planner Agent
  change: "Before finalizing a maintenance ticket plan, if Description or AC references `run/main_scene` or other `project.godot` keys as fixed, read `project.godot` (or require the Spec Agent to add an explicit sub-req: assert exact string **or** document actual value + deferred follow-up). Do not assume ticket prose matches repo."
  reason: Avoids planning and gatekeeping against a fictional baseline.

- agent: Spec Agent
  change: "Whenever requirements depend on `project.godot`, include a numbered escape hatch when ticket prose may disagree with repo (e.g. **X.Y**: closure allowed if actual value is documented, automated tests assert the minimal safe invariant such as ‘must not reference the new scene,’ and product intent is routed to a policy ticket)."
  reason: Preserves honest traceability without blocking shipping the scene work.

- agent: Acceptance Criteria Gatekeeper Agent
  change: "If tests defer a full AC clause (e.g. exact `run/main_scene` match), Validation Status must state the real `project.godot` value, cite the spec deferral ID, and forbid silently editing Description/AC to match repo unless that edit is an explicit human/product decision."
  reason: Prevents false closure and preserves audit trail.

- agent: Test Designer Agent
  change: "If file-text or scene assertions are stricter than the spec’s enumerated paths (e.g. ‘no `.glb` in any `[ext_resource]`’ vs four named GLBs), document that tightening in the test file header or update the spec so failure messages map to an agreed REQ."
  reason: Reduces implementer confusion and spec-vs-test arguments.

### Workflow Improvements

- issue: Tickets copied from older workflow docs can assert `run/main_scene` targets that M6 or later policy has moved.
  improvement: For sandbox-only maintenance, add a one-line planner checklist: confirm `run/main_scene` in `project.godot` vs ticket; if mismatch, spec owns SLEEV-4.2-style resolution before TEST_DESIGN.
  expected_benefit: Fewer mid-pipeline spec/test/gatekeeper reconciliations.

### Keep / Reinforce

- practice: **SLEEV-4.2** pattern—document drift, assert minimal safe invariant, escalate product intent separately.
  reason: Honest validation without blocking useful duplicate scenes.

- practice: Test Breaker’s ordering so ADV and source-scene checks run even when **SLEEV-1.1** fails first.
  reason: One clear missing-file failure while canonical scene and `project.godot` stay guarded.

---

## [MAINT-TSGR] — Combined runner fail-fast; DRY lefthook/CI; static bash contract + pytest mirrors

*Completed: 2026-04-05*

### Learnings

- category: infra
  insight: Shell steps that use `|| true` or discard stderr on prerequisites (e.g. headless `--import`) can report success while the tree or cache is broken, so later tests run on a false premise.
  impact: The pre-ticket runner could mask import/reimport failures and still proceed to Godot tests.
  prevention: Treat bounded `timeout` + visible stderr + `set -e` on import and test invocations as default; any bypass must be narrow, commented, logged, and spec-approved.
  severity: high

- category: process
  insight: “Full CI” and “pre-push” hooks must invoke the same resolver and phase order or teams get two different definitions of green.
  impact: Python pytest lived under lefthook only while `run_tests.sh` was Godot-only, so a canonical full run could miss Python failures.
  prevention: Extend the documented canonical script to call the shared Python entry (e.g. `.lefthook/scripts/py-tests.sh`) rather than duplicating resolver logic inline.
  severity: medium

- category: testing
  insight: Orchestration requirements (order, `set -e`, no masking, doc pointers) are expensive to prove with live engine-crash tests; a small executable bash verifier plus pytest that shells out from repo root encodes most of the contract cheaply.
  impact: TSGR-1..6 gained automated regression signal before and after implementation; adversarial tests added cwd independence and hollow-verifier guards.
  prevention: For runner/CI shell ACs, plan a static verifier + thin pytest wrapper as the default verification path when integration stubs are out of scope.
  severity: medium

- category: infra
  insight: Line-order and substring-based static checks on shell sources are brittle if comments or headers contain trigger tokens (e.g. `pytest`) above an earlier required line.
  impact: Implementers must keep comment placement compatible with naive ordering probes unless the verifier is upgraded in the same change.
  prevention: Document forbidden comment patterns next to the verifier, or replace line-order checks with structured markers or a single parsed block.
  severity: low

### Anti-Patterns

- description: Using `|| true` or redirecting stderr away from import/reimport or other prerequisite commands in the combined test runner.
  detection_signal: Script continues after import errors; CI logs lack stderr for the failed phase; exit code 0 with broken `.godot` cache.
  prevention: Fail-fast defaults; logged, spec-scoped bypasses only.

- description: Running Python tests only in git hooks and Godot tests only in CI (or duplicated resolver logic in two places).
  detection_signal: `run_tests.sh` and `.lefthook/scripts/py-tests.sh` disagree on `uv`/`.venv`/fallback behavior or one path omits a suite entirely.
  prevention: One callable script for the Python phase; CI and lefthook both delegate to it.

### Prompt Patches

- agent: Implementation Generalist Agent
  change: "When editing `ci/scripts/run_tests.sh` or `.lefthook/scripts/godot-tests.sh` guarded by MAINT-TSGR-style static contract tests, do not place comment lines containing `pytest` or `py-tests` above the Godot `run_tests.gd` invocation unless you update `verify_tsgr_runner_contract.sh` and the pytest mirrors in the same change; keep ordering probes green."
  reason: Naive line-order checks treat documentation comments as structure.

- agent: Test Designer Agent
  change: "For combined-runner specs, list which clauses are covered by static shell verification vs full integration (e.g. `timeout` SIGTERM exit aggregation). If static proof is impossible, name the gap in the spec and reserve gatekeeper or optional stub-based tests so it is not mistaken for proven."
  reason: Prevents false confidence on TSGR-4.3-style behaviors.

- agent: Planner Agent
  change: "For maintenance tickets whose AC requires non-zero exits on failure, grep the current canonical runner and hook scripts for `|| true`, `2>/dev/null`, or stderr discard on import/test lines and treat hits as explicit rework scope in the execution plan."
  reason: Surfaces the dominant false-green pattern before implementation starts.

### Workflow Improvements

- issue: Static contract cannot prove shell exit behavior when `timeout` kills a child (noted as TSGR-4.3 gap in test-design checkpoints).
  improvement: Either add a documented gatekeeper manual check, a stubbed `timeout`/fake `godot` integration test, or accept the gap explicitly in the spec with a follow-up ID.
  expected_benefit: Clear boundary between proven runner shape and unproven signal semantics.

### Keep / Reinforce

- practice: Python phase in `ci/scripts/run_tests.sh` delegates to `.lefthook/scripts/py-tests.sh` (TSGR-3 DRY) so pre-push and full suite stay aligned.
  reason: One resolver path for `.venv` / `uv run` / `python3` fallback.

- practice: Authoritative `verify_tsgr_runner_contract.sh` plus Test Breaker pytest mirrors (cwd independence, hollow verifier, key grep mirrors).
  reason: Defense-in-depth without requiring fragile full-Godot crash harnesses for every orchestration rule.

---

## [attack_telegraph_system] — Death must preempt telegraph state; asymmetric family tests need explicit AC wording

*Completed: 2026-04-06*

### Learnings

- category: architecture
  insight: Controllers that combine telegraph timers, animation completion, and a terminal lifecycle (e.g. Death) need explicit precedence: entering Death must clear telegraph flags and cancel hold/wall-clock paths so Death is never deferred behind telegraph logic, and one-shot timer callbacks must tolerate cancellation after telegraph fields are cleared.
  impact: GDScript review caught ordering where telegraph could still run alongside or after Death; fix was to reset `_ranged_telegraph_*` and related state when taking the Death branch before collision disable / play.
  prevention: When adding interruptible phases, add a checklist item: “terminal state clears all in-progress phase timers and flags.”
  severity: high

- category: testing
  insight: Headless adversarial tests that count live projectile spawns or rely on `get_class()` on instanced roots can be unreliable (SceneTree phase, node type vs script name); source-level guarantees (e.g. re-entry guards, `CONNECT_ONE_SHOT`, substring checks with `# CHECKPOINT`) can prove the same invariants without a flaky runtime harness.
  impact: Test Breaker chose structure over spawn counting for duplicate `_on_telegraph_finished` / double `_begin_attack_cycle` cases.
  prevention: Prefer source contracts when runtime identity or tree phase is ambiguous; reserve runtime stress only for paths where the harness is proven stable.
  severity: medium

- category: process
  insight: “Works for all N enemy families” without a normative test depth per family forces gatekeepers to assume asymmetric coverage (full behavioral tests for some families, contract/export/wiring for stubs) unless the spec states it.
  impact: AC gatekeeper logged medium confidence on whether carapace/claw required T-ATS-04-style SceneTree tests.
  prevention: Spec or ticket should state parity expectations (full vs contract) when families are at different maturity levels.
  severity: medium

### Anti-Patterns

- description: Letting Death or other terminal transitions run while telegraph timers and flags remain active, so completion ordering or collision disable is wrong.
  detection_signal: Death mid-attack; telegraph `emit` or hold timer fires after `queue_free`; review comments on “telegraph vs Death ordering.”
  prevention: Clear telegraph state on the same code path that latches Death and guard timer callbacks with `if not _ranged_telegraph_active`.

- description: Asserting spawn counts or class identity in headless tests without validating that the instanced node matches the expected `class_name` / script type.
  detection_signal: `get_class()` != expected type; tests pass/fail depending on `SceneTree._initialize` ordering.
  prevention: Use documented source checks or assert on node path + script resource path.

### Prompt Patches

- agent: GDScript Reviewer Agent
  change: "For `EnemyAnimationController`/`AnimationPlayer`-driven flows: if telegraph uses timers or hold flags, verify that Death (or any irreversible despawn) clears those flags and cancels any pending telegraph semantics before collision disable and `play('Death')`, and that timer callbacks exit early if telegraph was cleared."
  reason: Prevents death-vs-telegraph ordering bugs that static tests often miss.

- agent: Test Breaker Agent
  change: "For duplicate-emission or double-entry adversarial cases on spawned gameplay nodes: if headless spawn counting or `get_class()` is unreliable, prefer source-level guards (`# CHECKPOINT` comments) and document the constraint in the checkpoint; do not block on a flaky runtime harness."
  reason: Matches ADV-ATS pattern and avoids false reds from tree phase quirks.

- agent: Spec Agent
  change: "When acceptance criteria say 'works for all N families' and some families are stub or minimal implementations, add a normative line: either require behavioral parity tests per family or explicitly allow contract tests (exports, script presence, wiring) for families without full combat."
  reason: Removes AC gatekeeper ambiguity and avoids scope creep late in the pipeline.

### Workflow Improvements

- issue: Workflow stage enum has no `IMPLEMENTATION_GAMEPLAY`; Test Breaker advanced to `IMPLEMENTATION_GENERALIST` with handoff to Gameplay Systems.
  improvement: Document in `agent_context/agents/readme.md` (or planner routing) a single canonical mapping: “telegraph / enemy attack implementation → gameplay systems” when the stage is generalist.
  expected_benefit: Fewer wrong-agent handoffs and fewer medium-confidence routing assumptions.

### Keep / Reinforce

- practice: ATS-2 wall-clock floor (min 0.3 s) enforced when the Attack clip ends early via hold timer + `maxf`/`max` on fallback timers, with adversarial tests for clamps.
  reason: Readable wind-up without hardcoding a single duration in all attack scripts.

- practice: Primary suite stays deterministic (no `await`/wall-clock in NF1); adversarial suite carries timing and stress cases.
  reason: Stable CI while still covering edge cases.

---

## [ui_polish_and_start_sh] — Verification-first closure for malformed workflow stubs and explicit interactive-validation boundaries
*Completed: 2026-04-07*

### Learnings
- category: process
  insight: Tickets that skip required `WORKFLOW STATE` scaffolding should be treated as workflow defects first; closure can proceed only with an explicit verification-first contract instead of silently pretending normal stage progression occurred.
  impact: This ticket resumed from a malformed backlog stub and required assumption-based bootstrap before evidence collection, increasing ambiguity about expected sequencing.
  prevention: Add a mandatory bootstrap rule: if `WORKFLOW STATE` is missing, record a normalized resume block and enforce validation-only closure with explicit assumptions and confidence levels.
  severity: medium

- category: testing
  insight: UI tickets that combine process lifecycle checks and browser interactions need a split contract between automatable runtime evidence and manual interactive smoke, otherwise gatekeeping overstates confidence.
  impact: Non-interactive checks validated `start.sh` startup/shutdown and code-path mapping, but full editor-to-preview interaction remained manual follow-up.
  prevention: Require every mixed UI ticket to mark ACs as `automated`, `code-path`, or `manual-interactive` at planning/spec time and preserve that split in final validation.
  severity: medium

- category: infra
  insight: Startup wrappers that orchestrate multiple services should always be validated under bounded runtime with trap-driven teardown evidence, not only “server started” logs.
  impact: Bounded `start.sh` smoke with controlled shutdown provided stronger confidence that both services exit cleanly on interrupt.
  prevention: Standardize launcher AC verification to include bounded run + interrupt + teardown evidence for all multi-process scripts.
  severity: medium

### Anti-Patterns
- description: Closing malformed tickets as if they followed the normal staged pipeline without explicit bootstrap assumptions.
  detection_signal: Ticket is in `done/` but lacks a prior `WORKFLOW STATE` block or contains no resume normalization in checkpoint logs.
  prevention: Enforce a “malformed stub bootstrap” checkpoint template before any completion decision.

- description: Treating partial non-interactive smoke as equivalent to full UX verification for editor-driven workflows.
  detection_signal: Validation claims end-to-end success while checkpoints still list manual interactive follow-ups.
  prevention: Keep automated and manual evidence channels separate and require explicit manual checklist carry-forward.

### Prompt Patches
- agent: Acceptance Criteria Gatekeeper Agent
  change: "If a resumed ticket lacks a valid `WORKFLOW STATE` block, do not close it under normal-stage assumptions. First require a bootstrap note that states malformed input, normalization steps taken, and confidence level; then allow only verification-first closure."
  reason: Prevents false traceability when upstream workflow metadata is incomplete.

- agent: Spec Agent
  change: "For UI/editor tickets with both service orchestration and in-browser interaction, classify each AC as `automated runtime`, `code-path evidence`, or `manual interactive`; include the exact manual checklist in `NEXT ACTION` if any AC cannot be automated."
  reason: Reduces closure ambiguity and keeps confidence aligned with observable evidence.

- agent: Planner Agent
  change: "When a ticket includes a launcher script (`start.sh`-style), include bounded runtime + interrupt/teardown verification as a required execution-plan step, not an optional smoke check."
  reason: Makes process-lifecycle reliability a default acceptance dimension.

### Workflow Improvements
- issue: Malformed backlog stubs force ad-hoc assumptions during resume and weaken stage-level auditability.
  improvement: Add a pre-stage validator that blocks progression until `WORKFLOW STATE` and `NEXT ACTION` minimum schema are present or auto-normalized with logged provenance.
  expected_benefit: More consistent resumes and fewer medium-confidence closure decisions.

- issue: Interactive UI checks are often implied but not explicitly separated from automatable checks.
  improvement: Add an AC evidence matrix field (`automated`/`manual`) to ticket templates and require gatekeeper output to report both counts.
  expected_benefit: Clearer confidence signaling and less accidental over-claiming of end-to-end verification.

### Keep / Reinforce
- practice: Recording `Would have asked` / `Assumption made` / `Confidence` in scoped checkpoint logs for autonomy decisions.
  reason: Preserves decision provenance when human clarification is unavailable.

- practice: Bounded smoke execution for launcher scripts with visible startup and shutdown evidence.
  reason: Catches lifecycle regressions early without needing full interactive harness automation.

---

## [M9-MRVC] — Model registry spec path encoding vs ARGLB

*Completed: 2026-04-08*

### Learnings

- category: architecture
  insight: New registry specs that reference “repo-relative” paths must be checked against existing web/backend contracts (ARGLB) that already fix paths relative to `python_root`.
  impact: First MRVC draft used full repo prefixes; would have diverged from `animated_exports/...` strings in list/serve APIs.
  prevention: When adding manifest specs, grep for `python_root` / existing path literals and cite the same root in ADRs before freezing MRVC-3.
  severity: medium

- category: testing
  insight: Markdown spec contracts can be guarded with cheap pytest substring/heading tests so downstream tickets cannot silently drop ADRs or spawn/deletion sections.
  impact: 22 contract tests lock MRVC-1..12 and downstream ticket filenames without JSON-schema tooling yet.
  prevention: For specification-only tickets, default to `tests/specs/test_*_spec_contract.py` alongside the spec file path in `project_board/specs/`.
  severity: low

### Anti-Patterns

- description: Defining manifest path rules from first principles without reconciling to the assets router and Godot `res://` mapping in the same edit pass.
  detection_signal: Spec mentions different path prefixes than `GET /api/assets` and `config.py` `python_root`.
  prevention: Add an explicit “Consistency with ARGLB” requirement (MRVC-12 style) and one cross-reference test.

### Keep / Reinforce

- practice: ADR block for manifest location (single file vs sidecars) plus explicit deletion matrix D1–D5 for editor safety.
  reason: Unblocks umbrella blocked ticket’s “data contract” without implementation tickets reopening scope.

---

## [M9-EGMS] — Make API error precedence explicit and separate contract confidence from environment constraints
*Completed: 2026-04-09*

### Learnings
- category: architecture
  insight: APIs that validate multiple independent error classes (duplicate IDs, unknown IDs, draft/ineligible IDs) need an explicit precedence rule in the spec, not just "reject invalid input."
  impact: Mixed-invalid enemy-slot payloads created ambiguity (400 vs 404 ordering) and required conservative assumptions plus extra adversarial tests to stabilize behavior.
  prevention: Add a mandatory "validation precedence matrix" section to API specs that rank checks and status codes for mixed-invalid requests.
  severity: high

- category: process
  insight: Product behavior that affects UX trust (hot-reload vs restart-required and empty-pool fallback policy) must be declared before test design begins.
  impact: Planning/spec needed medium-confidence assumptions and checkpointed clarifications before tests could lock contracts.
  prevention: Planner/spec handoff should fail fast unless runtime-application semantics and fallback policy are explicitly declared.
  severity: medium

- category: testing
  insight: When one execution layer is environment-blocked, confidence can still be preserved by pairing deterministic lower-layer contract tests with API-boundary client tests and explicitly logging the remaining gap.
  impact: Router-suite execution was blocked by local `pydantic_core` architecture mismatch, but service tests plus frontend client validation tests provided acceptable AC evidence without silent risk.
  prevention: Require an "evidence substitution" pattern: (1) blocked layer noted, (2) compensating deterministic suites identified, (3) residual risk carried to gatekeeper.
  severity: medium

### Anti-Patterns
- description: Leaving mixed-invalid request semantics unspecified and expecting implementation order to become de-facto API contract.
  detection_signal: Tests or checkpoints debate whether 400 or 404 should win for one payload containing multiple violations.
  prevention: Define precedence in spec and encode one deterministic adversarial test for each mixed-invalid pair.

- description: Treating environment failures as either full blockers or as ignorable noise, with no formal substitute evidence model.
  detection_signal: Validation narratives jump from "cannot run X" directly to "complete" without compensating contract-level proof and residual-risk statement.
  prevention: Use a standard fallback evidence template and require gatekeeper acknowledgment of constrained confidence.

### Prompt Patches
- agent: Spec Agent
  change: "For every new mutation endpoint, include a `Validation Precedence` table that defines check order and exact status/code outcome for mixed-invalid payloads (e.g., duplicate + unknown + ineligible)."
  reason: Removes ambiguous failure semantics that otherwise surface late during test-break.

- agent: Test Breaker Agent
  change: "Always add at least one mixed-invalid payload test per mutation endpoint that asserts both atomic no-partial-write behavior and the declared precedence status code."
  reason: Prevents unstable contracts where only single-error cases are tested.

- agent: Acceptance Criteria Gatekeeper Agent
  change: "If any required suite is environment-blocked, require an explicit evidence-substitution triad in the ticket: blocked command/root cause, compensating deterministic suites, and residual-risk note before allowing COMPLETE."
  reason: Keeps completion decisions auditable without over- or under-blocking.

### Workflow Improvements
- issue: Runtime behavior decisions (restart-required player updates, zero-slot fallback) were clarified during planning/spec instead of being guaranteed up front.
  improvement: Add a planner exit criterion that blocks transition to SPECIFICATION unless runtime application timing and empty-state fallback are explicitly selected.
  expected_benefit: Fewer medium-confidence assumptions and less downstream contract churn.

- issue: Contract confidence depended on ad-hoc interpretation when router tests could not execute locally.
  improvement: Introduce a reusable "constrained environment evidence matrix" checklist in checkpoints for backend/API tickets.
  expected_benefit: Consistent, transparent AC closure under local environment constraints.

### Keep / Reinforce
- practice: Checkpointing `Would have asked` + `Assumption made` + `Confidence` at each uncertainty point.
  reason: Preserves decision provenance and prevents implicit assumptions from disappearing in final AC claims.

- practice: Pairing backend service-contract tests with frontend API-client contract tests for the same mutation semantics.
  reason: Provides cross-layer verification even when one infrastructure slice is temporarily unavailable.

---
## [M9-LEMA] — Freeze load-existing contract semantics early to avoid security and fixture rework
*Completed: 2026-04-09*

### Learnings
- category: architecture
  insight: Load/open endpoints that permit multiple selector forms (identity fields and optional path) require explicit ambiguity handling in the spec; mixed-selector payloads must be rejected, not silently precedence-resolved.
  impact: Test-break had to add and lock a conservative `400` rejection for identity+path payloads after contract ambiguity surfaced mid-pipeline.
  prevention: Require a selector-composition rule in spec for all open/load APIs: "single selector mode only; mixed modes rejected with deterministic status."
  severity: high

- category: testing
  insight: Security-path contracts need deterministic fixture coherence between "successful open" and "stale/missing file" cases for the same identity, otherwise tests encode contradictory expectations.
  impact: Backend implementation required rework to align fixture setup (`alpha_live_00.glb`) with missing-file `404` assertions while preserving positive-path coverage.
  prevention: Add a fixture sanity check in test-design: every identity used in both success and stale-file tests must be explicitly created, then deleted only within the stale-file test path.
  severity: medium

- category: process
  insight: Endpoint and payload-envelope assumptions deferred to test-design increase churn even when security intent is clear.
  impact: The stage had medium-confidence assumptions on exact route names and payload shape before tests could be authored.
  prevention: Planner-to-spec handoff should require explicit endpoint URI and request schema freeze before test-authoring starts.
  severity: medium

- category: testing
  insight: When environment architecture blocks one required command, confidence should come from an explicit substitution chain plus later architecture-correct rerun, not silent omission.
  impact: Test-break initially failed due to `pydantic_core` architecture mismatch; final evidence used architecture-pinned execution and preserved deterministic suite proof.
  prevention: Standardize a test-evidence fallback: record blocked command/root cause, run architecture-correct equivalent, and carry residual risk if no equivalent exists.
  severity: medium

### Anti-Patterns
- description: Allowing multi-selector request ambiguity (identity + raw path) and relying on implicit implementation order as contract.
  detection_signal: Checkpoints or tests debate whether identity or path "wins" for the same request payload.
  prevention: Treat mixed selector forms as invalid input and codify status/message in spec and adversarial tests.

- description: Building stale-file tests from identities that were never created in fixtures.
  detection_signal: Positive and missing-file tests reference the same identity but setup lacks explicit file creation before deletion.
  prevention: Require fixture lifecycle tables in backend router tests (created -> opened -> removed -> 404) for each shared identity.

- description: Freezing endpoint details at test-design instead of spec stage.
  detection_signal: Test-design checkpoint includes "would have asked" on route names or payload envelopes.
  prevention: Add a spec completeness gate that blocks test design until endpoint names, payload schema, and error layering are explicit.

### Prompt Patches
- agent: Spec Agent
  change: "For every new load/open workflow, include a `Selector Mode Contract` section that explicitly states allowed selector forms, mixed-selector rejection behavior, and exact status/message for ambiguity (`400`)."
  reason: Prevents late security-contract ambiguity and removes test-break precedence assumptions.

- agent: Test Designer Agent
  change: "When a registry identity appears in both success and stale-file tests, add a fixture lifecycle assertion proving the file exists before success-path assertions and is removed only inside stale-path cases."
  reason: Prevents contradictory expectations that force backend fixture rework.

- agent: Acceptance Criteria Gatekeeper Agent
  change: "If a required suite fails due to runtime architecture mismatch, require an evidence note with (1) failing command + mismatch detail, (2) architecture-correct equivalent command and output, and (3) residual-risk statement if equivalence is partial."
  reason: Keeps completion decisions deterministic under local runtime constraints.

### Workflow Improvements
- issue: Contract details (URI/payload ambiguity) were finalized too late, shifting design decisions into test-design/test-break.
  improvement: Add a spec exit checklist item: endpoint paths, request schema, selector-mode rules, and error precedence must be explicit before advancing to test design.
  expected_benefit: Less downstream churn and fewer medium-confidence assumptions.

- issue: Fixture consistency for stale-file flows was validated reactively during implementation.
  improvement: Add a pre-implementation "fixture coherence" review step for backend tests that pair success and not-found paths on shared identities.
  expected_benefit: Fewer rework loops caused by contradictory test scaffolding.

### Keep / Reinforce
- practice: Registry-backed candidate derivation with strict allowlist and deterministic sorting was validated across backend and frontend contract tests.
  reason: Security and UX behavior stayed aligned without introducing arbitrary filesystem exposure paths.

- practice: Scoped checkpointing of `Would have asked`/`Assumption made`/`Confidence` captured ambiguity at each stage.
  reason: High-value learning signals were recoverable for post-ticket process improvement.

---
## [M9-EMVDES] — Umbrella pipeline: verify child gates before SPECIFICATION; BLOCK when gating work remains
*Completed: 2026-04-09*

### Learnings
- category: process
  insight: An umbrella ticket that only coordinates numbered children and defers detailed work to those children should not advance to SPECIFICATION for net-new umbrella-level feature prose while a documented **gating** child remains in `backlog/`; the umbrella’s “spec” is the aggregation of child outcomes plus any explicit gap list, not a parallel spec track.
  impact: Advancing would risk duplicate or conflicting specification work and blur acceptance ownership across already-`done/` children and incomplete audit work.
  prevention: Before moving any umbrella to SPECIFICATION, enumerate required children and verify each is in `done/` or explicitly waived; if a named gate (e.g. audit/mesh ticket) is still backlog, set Stage `BLOCKED` and record the execution order instead.
  severity: medium

- category: process
  insight: Dependency verification for ticket sequencing should use **filesystem state** (presence in `backlog/` vs `done/`) as primary evidence, aligned with the umbrella’s own execution plan and blocking-issues list.
  impact: The planner could resolve “should we spec the umbrella?” deterministically from repo state without guessing scope completion.
  prevention: Make pre-SPECIFICATION checks mandatory: list expected child filenames and confirm their milestone folder; mismatch → BLOCKED or human routing, not stage advance.
  severity: high

- category: process
  insight: For **coordination-only** umbrellas, “complete” means all acceptance themes satisfied by children (or signed waiver)—a BLOCKED umbrella with a clear gate and `Next Responsible Agent: Human` is a valid terminal state for an autonomous planning pass when work is intentionally deferred.
  impact: Avoids falsely treating “not all children done” as a failure to close planning; it is correct to stop the pipeline at BLOCKED with documented unblock steps.
  prevention: Distinguish “ticket failed” from “pipeline correctly parked”; require checkpoint text that states the gate, the blocking child id, and the ordered unblock actions.
  severity: medium

### Anti-Patterns
- description: Advancing an umbrella to SPECIFICATION to “keep momentum” while a ticket it explicitly names as gating is still in `backlog/`.
  detection_signal: Umbrella references child `02` (or similar) as prerequisite but planner runs SPECIFICATION without verifying `done/` contains that child.
  prevention: Hard gate: no umbrella SPECIFICATION until all declared gating children are `done/` or waived in writing in the ticket.

- description: Treating umbrella and first child as interchangeable in sequencing when the umbrella text says children `01`–`09` carry the real spec and tests.
  detection_signal: Umbrella description says “detailed work is tracked in … `01` … `09`” but workflow tries to author a second top-level spec for the same themes.
  prevention: If children already absorbed spec/test/implementation, umbrella stages should be verification + coordination only unless a gap register lists missing themes.

### Prompt Patches
- agent: Planner Agent
  change: "When the ticket is labeled an umbrella and lists numbered child tickets as the source of detailed work, before setting Stage to SPECIFICATION or later: (1) verify each referenced child path exists and record whether it is in `backlog/`, `in_progress/`, or `done/`; (2) if any child explicitly listed under Blocking issues or execution plan as gating is not in `done/`, set Stage `BLOCKED`, increment Revision, set Next Responsible Agent to `Human`, and write an execution plan (complete gate → full test gate → verify umbrella AC vs named `done/` children). Do not open a parallel umbrella SPECIFICATION for net-new feature prose unless no such gating child remains."
  reason: Prevents duplicate spec tracks and aligns autonomous defaults with on-disk dependency truth.

- agent: Planner Agent
  change: "For coordination or umbrella tickets, if the correct autonomous outcome is to park work, prefer `BLOCKED` with documented unblock criteria over advancing to SPECIFICATION; include in the checkpoint: `Would have asked` (umbrella spec vs blocked), `Assumption made` (conservative block), `Confidence`, and filesystem evidence lines listing which children are `done/` vs backlog."
  reason: Makes BLOCKED vs advance decisions auditable and reproducible for future learning extraction.

### Workflow Improvements
- issue: Umbrella vs child responsibility can be ambiguous at stage transitions.
  improvement: Add a workflow rule: umbrellas with child ticket lists get a “dependency matrix” row in planning output (child id → folder → blocks umbrella? y/n) before any stage beyond PLANNING.
  expected_benefit: Fewer mistaken SPECIFICATION runs and clearer handoff to humans when gates exist.

- issue: SPECIFICATION stage semantics overload “write spec” vs “verify child specs cover AC.”
  improvement: Define two modes in workflow docs: **Umbrella-verify** (no new spec doc; checklist against `done/` children + tests) vs **Net-new-spec**; only the latter advances a spec-writing agent for the umbrella file itself.
  expected_benefit: Reduces redundant work and clarifies when BLOCKED is correct.

### Keep / Reinforce
- practice: Conservative autonomous default—BLOCKED + human routing when a gating child is incomplete rather than speculative umbrella SPECIFICATION.
  reason: Preserves single source of truth in child tickets and avoids conflicting narratives.

- practice: Checkpoint entries that pair a concrete question (umbrella advance vs BLOCKED) with filesystem evidence and explicit assumption.
  reason: Enables post-hoc learning and audit without re-deriving planner intent.

---

## [extras-shell-visible-spikes-on-top] — Base-distance protrusion tests and grep-verified multi-site literals
*Completed: 2026-04-11*

### Learnings
- category: testing
  insight: For cones placed along a surface normal, asserting only that the apex lies outside the body can still pass when the base circle is embedded; encode the real invariant (e.g. base at apex − depth × normal at or beyond the surface radius along that direction), not a weaker tip-only distance check.
  impact: An initial protrusion test keyed on tip distance would have stayed green with factor 0.55; the design was corrected before implementation to assert base-on-surface, producing a failing test that matched the AC.
  prevention: For “proud of surface” AC, Test Designer specifies apex vs base geometry and asserts non-embedded base (or equivalent exterior predicate) on a simple probe zone (e.g. unit sphere).
  severity: high

- category: process
  insight: Plans that state “change literal at N call sites” without a mechanical grep can miscount branches (this ticket: four vs five 0.55 sites); one path can retain the old factor until caught by path-specific tests.
  impact: Spec/plan text drifted until grep listed all sites; adversarial coverage explicitly targeted horns vs spikes paths.
  prevention: Before implementation, grep the target file for the literal and record count plus branch labels (body/head, uniform/random, horns) in the plan or spec.
  severity: medium

- category: testing
  insight: When the same primitive is invoked with mixed calling styles (positional tuple vs `location=` keyword), tests that assert only one form are brittle or can miss real calls.
  impact: TEST_DESIGN assumed shell tests should read location from both `args` and `kwargs`, consistent with existing bulb paths.
  prevention: Mirror the assertion style used by tests for sibling primitives in the same module, or accept both extraction paths in the mock capture.
  severity: low

- category: architecture
  insight: New zone float tunables should extend the existing `_zone_extra_scale` (or equivalent) path so attach-layer NaN/default/clamp behavior stays aligned with sanitize instead of ad hoc parsing per field.
  impact: `shell_scale` reused shared coercion with spike_size/bulb_size for defense in depth.
  prevention: Implementation agents add new keys to the shared helper and its tests rather than one-off float handling in attach-only code.
  severity: low

### Anti-Patterns
- description: “Protrusion” tests that only compare apex distance to the surface point while the cone base remains inside the mesh.
  detection_signal: Tests pass; art or manual preview still shows buried spikes; factor < 1.0 still green.
  prevention: Assert base center along normal at or outside the surface (or mesh-exterior equivalent) for the stated AC.

- description: Stating a call-site count for a repeated magic number from memory in the plan or spec.
  detection_signal: Narrative says “four sites” but the file has five code paths (e.g. extra random/uniform or horn branch).
  prevention: Enumerate matches from grep in the ticket/spec before merge.

### Prompt Patches
- agent: Test Designer Agent
  change: "For zone extras spikes, horns, or cones on an ellipsoid/sphere zone, if AC is spikes not buried or flush, do not rely on tip-only distance-from-center: assert the cone base (apex minus depth along the outward normal) is on or outside the surface (e.g. for a unit sphere probe, base distance from center ≥ 1.0). Explain in the test or spec why tip-only checks can pass while the base remains embedded."
  reason: Prevents false-green coverage that would have masked the 0.55 factor.

- agent: Planner Agent
  change: "When changing a repeated numeric literal or factor in one module, require a grep of that literal in the target file, record the exact number of matches, and list each logical branch (e.g. body uniform, body random, head horns, head spikes uniform, head spikes random). Do not use a hand-count in the execution plan."
  reason: Avoids missing the fifth call site and plan/spec miscounts.

- agent: Test Breaker Agent
  change: "After core protrusion tests exist, add path-specific or analytical cases so each distinct branch that could retain an old factor is exercised (e.g. horns expected tip at factor 1.0 vs captured `create_cone`, not only body spikes)."
  reason: Catches a horn call site left at 0.55 when other paths were updated.

### Workflow Improvements
- issue: Multi-branch numeric edits planned without mechanical enumeration.
  improvement: Insert a short gate between spec and implementation: grep literal → paste line roles → sign-off that all branches are in scope for the change.
  expected_benefit: Fewer partial factor updates across symmetric code paths.

### Keep / Reinforce
- practice: TEST_DESIGN checkpoint resolving positional vs keyword `location` for `create_sphere` by matching existing bulb call patterns in assertions.
  reason: Documents API ambiguity and keeps tests aligned with production call style.
- practice: Failing tests without `xfail` through TEST_BREAK when implementation follows immediately.
  reason: Preserves a clear red stage before green for the pipeline.

## [04_documentation_cursor_and_claude_mcp_setup] — MCP operator docs
*Completed: 2026-04-13*

### Learnings
- category: docs
  insight: Keep MCP JSON fragments in **one** canonical README (`asset_generation/mcp/README.md`) and a **single** `CLAUDE.md` pointer so Cursor/Claude config churn does not fork across web/python readmes.
  impact: Contributors merge fragments into local or project MCP config; `${workspaceFolder}` may need replacing with absolute `cwd` on some clients.
  prevention: Troubleshooting table documents `cwd` + `PYTHONPATH` mistakes explicitly.
  severity: low

## [03_mcp_stdio_server_wrapping_asset_editor_api] — FastMCP stdio MCP
*Completed: 2026-04-13*

### Learnings
- category: packaging
  insight: This repo’s pytest layout uses `from src.*` with `pythonpath = ["."]`; adding a second import root `"src"` enables a conventional package name (`blobert_asset_pipeline_mcp`) for the MCP entrypoint while keeping existing tests unchanged.
  impact: README and MCP `cwd`/`PYTHONPATH` must stay aligned (`PYTHONPATH=src`, cwd `asset_generation/python`).
  prevention: Ticket `04` copies the exact `uv run` + env from `src/blobert_asset_pipeline_mcp/README.md`.
  severity: low

### Keep / Reinforce
- practice: Thin `@mcp.tool` wrappers + shared `_request` / `format_http_response` instead of duplicating httpx per tool.
  reason: Keeps catalog drift visible in one module.

## [02_backend_blocking_or_polled_run_endpoint] — GET /api/run/complete
*Completed: 2026-04-13*

### Learnings
- category: asyncio
  insight: `asyncio.wait_for` on an `async for` over subprocess stdout must use `asyncio.shield` on the drain task when returning **504** early so the drain keeps running and avoids PIPE buffer deadlock; partial logs are returned from a shared `list` filled before timeout.
  impact: Without shield + background completion, a timed-out `/complete` could stall the child on a full stdout buffer.
  prevention: Document “background drain until exit” in the normative spec whenever max-wait is shorter than worst-case subprocess runtime.
  severity: medium
- category: testing
  insight: Backend router integration tests can avoid Blender by stubbing `routers.run.process_manager` with a tiny fake that implements `start` / `stream_output` / `is_running` / `exit_code` / `run_id`.
  impact: CI stays fast while still covering HTTP status codes and JSON bodies.
  prevention: Keep stubs in `test_run_complete_router.py` aligned with `ProcessManager` public surface.

### Keep / Reinforce
- practice: Share `_prepare_run_environment` between SSE and completion endpoints.
  reason: Prevents env/start_index drift between M21 UI and agents.

## [01_spec_asset_pipeline_mcp_and_agent_http_api] — APMCP normative spec + contract tests
*Completed: 2026-04-13*

### Learnings
- category: process
  insight: Spec-only milestone tickets still benefit from `spec_completeness_check.py --type api` plus markdown contract tests (pattern from MRVC) so AC for “frozen tool names” and security sections cannot drift silently.
  impact: Downstream MCP/backend tickets have executable guardrails without waiting for OpenAPI from ticket `02`.
  prevention: Reuse `tests/specs/test_*_spec_contract.py` for any normative `project_board/specs/*.md` that gates implementation.
  severity: low
- category: spec_authoring
  insight: Normative `GET /api/run/complete` URI may need revision if ticket `02` chooses POST; the spec already allows a documented one-line table update — keep that escape hatch explicit in APMCP-RUN handoffs.
  impact: Avoids false failures if implementation prefers POST for large `build_options`.
  prevention: Implementation ticket updates spec **Date** and endpoint freeze row in the same PR as the route.

### Keep / Reinforce
- practice: Frozen MCP tool names in a single catalog table referenced by skill ticket `06`.
  reason: Prevents string drift between MCP server and agent skill.

## [05_backlog_optional_glb_validation_or_preview_hooks] — Optional stretch (documented deferral)
*Completed: 2026-04-13*

### Learnings
- category: process
  insight: When a ticket’s acceptance criteria explicitly require **no implementation** for milestone closure, completing it with **operator-visible future-work text** plus a `COMPLETE` validation block (citing N/A tests) avoids leaving perpetual backlog noise while preserving scope for a later spike.
  impact: Reduces false “open work” in board scans without inventing MCP tools prematurely.
  prevention: Keep dependencies (e.g. tickets `01`–`04`, `06`, product direction) explicit in the deferred section and in the ticket body.
  severity: low

## [06_agent_skill_blobert_asset_pipeline_mcp] — Bundled skill + contract vs FastMCP registry
*Completed: 2026-04-13*

### Learnings
- category: testing
  insight: Asserting `SKILL.md` contains every name from `await mcp.list_tools()` ties procedural docs to the live FastMCP registration and catches catalog/skill drift without maintaining a second hard-coded tool list in tests (beyond the server as source of truth).
  impact: Adding a new `@mcp.tool` without updating the skill fails CI immediately.
  prevention: Keep a dedicated “Frozen MCP tool names” section in the skill with backtick-wrapped names matching `list_tools()`.
  severity: low
- category: tooling
  insight: `diff_cover_preflight.sh` measures coverage for the whole diff vs `origin/main`; a ticket that only adds markdown + thin tests can still fail the gate if other hunks on the branch leave MCP package lines under-covered — document in validation or fix coverage in a scoped chore.
  impact: Orchestrator should not assume a doc-only ticket will pass an aggregate diff-cover bar.
  prevention: Run preflight before merge; split PRs or add MCP integration tests when the gate blocks.
  severity: low

---

## [02_wire_generated_enemies_combat_rooms] — Resolve cross-ticket contract conflicts before implementation
*Completed: 2026-04-14*

### Learnings
- category: process
  insight: A ticket that depends on a prior ticket's behavioral contract must inherit the same authority model (authoritative spawn source vs embedded fixtures) before test design starts; otherwise downstream tests can encode mutually exclusive truths.
  impact: This ticket reached `BLOCKED` after implementation/tests because legacy `RTS-ENC-*` expectations (embedded enemies) and procedural `PESAL-T-05` expectations (no embedded enemies) were both treated as active acceptance evidence.
  prevention: Add a pre-test "contract inheritance check" that compares dependency tests and current ticket ACs for direct contradictions, and require planner arbitration before writing new tests if a conflict exists.
  severity: high

- category: testing
  insight: Cross-suite acceptance validation is fragile when old fixture-shape assertions remain normative after introducing runtime-driven generation contracts.
  impact: AC-R4.5 and AC-R5.5 could not be defensibly validated because passing one suite implied violating the other suite.
  prevention: When a runtime authority shift happens, explicitly mark legacy fixture assertions as deprecated, migrated, or scoped to non-authoritative compatibility tests.
  severity: high

- category: process
  insight: Medium/low-confidence assumptions about architecture boundaries (direct scene embedding vs runtime helper wiring) create avoidable rework when they are not resolved by ownership at planning time.
  impact: The implementation stage executed under a low-confidence assumption and then encountered gate failure that required planner-level arbitration anyway.
  prevention: Treat any assumption that changes canonical data authority as "must-resolve" in planning, not implementation.
  severity: medium

### Anti-Patterns
- description: Writing or keeping tests from two paradigms active at once without declaring which one is authoritative.
  detection_signal: Test names/fixtures assert opposite invariants for the same object lifecycle (for example "embedded child required" and "embedded child forbidden").
  prevention: Require a single "authority statement" in the ticket and test files before accepting new contract tests.

- description: Letting implementation proceed when checkpoints record low confidence on core contract assumptions.
  detection_signal: Checkpoint has `Confidence: Low` on an assumption that affects acceptance semantics (not just naming or formatting).
  prevention: Auto-escalate to planner/gatekeeper before implementation whenever low-confidence assumptions touch canonical behavior.

### Prompt Patches
- agent: Planner Agent
  change: "Before advancing a ticket with test dependencies to TEST_DESIGN, run a contradiction scan across referenced dependency tests and current acceptance criteria; if any pair asserts mutually exclusive behavior for the same runtime object, set Stage to `BLOCKED`, record both test IDs, and require an explicit canonical authority decision plus deprecation plan."
  reason: Prevents parallel test contracts from surviving long enough to block AC validation late in the pipeline.

- agent: Test Designer Agent
  change: "When introducing contract tests that replace a legacy fixture model, include a `Legacy Contract Disposition` note naming legacy test groups to deprecate, adapt, or keep as compatibility-only; do not leave both groups normative by default."
  reason: Forces explicit migration of old assertions instead of accidental dual-authority enforcement.

- agent: Acceptance Criteria Gatekeeper Agent
  change: "If acceptance evidence references two suites with opposite invariants, fail fast with `BLOCKED` and emit a required remediation checklist: canonical authority decision, specific tests to retire/update, and reassigned owners."
  reason: Moves contradiction discovery earlier and standardizes unblock steps.

### Workflow Improvements
- issue: Contract contradictions were discovered at AC gate after substantial downstream work.
  improvement: Insert a pre-implementation `Contract Consistency Gate` after TEST_BREAK for tickets that change runtime authority models.
  expected_benefit: Detects incompatible assertions before implementation churn and reduces blocked end states.

- issue: Checkpoint assumption metadata was informative but not enforceable.
  improvement: Add a workflow rule: low-confidence assumptions on canonical behavior automatically block stage progression until planner arbitration.
  expected_benefit: Converts passive checkpoint notes into active risk control.

### Keep / Reinforce
- practice: Scoped checkpoints captured `Would have asked` / `Assumption made` / `Confidence` at each stage.
  reason: The contradiction root cause and escalation boundary were reconstructable without re-running the full pipeline.

- practice: Acceptance gate refused to force closure under contradictory evidence.
  reason: Preserved integrity of completion criteria and prevented a false `COMPLETE` state.

---

## [03_procedural_enemy_attack_loop_runtime] — Headless PEAR pumps, CI diff-cover coupling, and acid attack off-tree semantics
*Completed: 2026-04-14*

### Learnings
- category: testing
  insight: Continuous attack-loop behavior under `tests/run_tests.gd` synchronous `run_all()` should be asserted with a deterministic bounded loop that calls `AcidSpitterRangedAttack._physics_process`, `AnimationPlayer.advance`, and `EnemyAnimationController._physics_process` together—not `SceneTree` idle/timer-driven advancement, which is unreliable in that harness.
  impact: Async assumptions would flake or never complete telegraphs; checkpoint TEST_DESIGN explicitly chose sync pumping aligned with existing attack telegraph integration tests.
  prevention: For headless “multi-cycle” contracts, default to the project’s established sync integration pattern and document the pump ordering in the test file header.
  severity: high

- category: testing
  insight: If production hosts defer wiring (`call_deferred` for animation/controller setup), contract tests must mirror that wiring synchronously in a helper (e.g. invoke the same post-ready hook the runtime would) so the SUT matches production state without requiring idle frames.
  impact: Without mirroring, pumps run against partially wired enemies and mis-attribute failures to attack logic.
  prevention: Test harness must list which deferred production paths are explicitly invoked for headless equivalence.
  severity: high

- category: architecture
  insight: Attack scripts that cast the parent to `EnemyInfection3D` in `_ready()` create a hard integration contract: “duck-typed” hosts are insufficient where M8 scripts assume that cast; tests should require the real host type when exercising those scripts.
  impact: Avoids false confidence from simplified test doubles that cannot satisfy runtime attack attachment semantics.
  prevention: When designing PEAR-style integration tests, align host type assertions with `_ready()` cast requirements in family attack scripts.
  severity: medium

- category: infra
  insight: Full `ci/scripts/run_tests.sh` runs Godot plus `asset_generation/python` pytest with diff-cover on changed lines; touches to pipeline/registry/Blender helpers in the same delivery as Godot runtime work can fail CI on Python coverage even when Godot is green.
  impact: Ticket closure evidence that cites only headless GDScript may miss a diff-cover failure from paired `.py` edits.
  prevention: Treat any commit touching `asset_generation/python/` as subject to diff-cover until `py-tests.sh` passes on the diff hunks; plan tests or refactors so changed Python lines execute under pytest coverage.
  severity: medium

- category: testing
  insight: Strict manual `_physics_process` pumps do not advance `SceneTree` timers or guarantee signal order with `AnimationPlayer` advance; ranged telegraph completion needs a production-side fallback (export timer and/or signal watchdog) when signals do not fire in the pumped order.
  impact: Headless tests could not complete telegraphs reliably without runtime support for non-timer completion paths and without relaxing `is_inside_tree()` gating on pumped attack nodes.
  prevention: When adding headless contract pumps, implement or extend attack scripts with explicit telegraph completion paths that do not depend solely on scene timers or tree membership.
  severity: high

### Anti-Patterns
- description: Gating attack progression on `is_inside_tree()` or only on `SceneTree` timer completion in code paths exercised by manual physics pumps.
  detection_signal: Headless PEAR tests hang under iteration cap or pass in-editor but fail headless with the same pump.
  prevention: Support pumped execution explicitly (documented in attack script) and use telegraph fallbacks/watchdogs where signals and timers diverge from gameplay.

- description: Treating “Godot suite green” as sufficient for ticket CI when the branch also modifies Python sources under diff-cover.
  detection_signal: `run_tests.sh` fails at diff-cover while `godot --headless -s tests/run_tests.gd` passed locally.
  prevention: Run full `ci/scripts/run_tests.sh` before closure when `asset_generation/python/` is in the diff.

### Prompt Patches
- agent: Test Designer Agent
  change: "For headless multi-frame combat contracts under `run_tests.gd`, specify a synchronous pump recipe (which nodes’ `_physics_process` run, `AnimationPlayer.advance` step, bounded `max_iters`) and require a harness helper that mirrors any production `call_deferred` wiring needed for equivalent ready-state; forbid relying on `await`/idle for timing-critical attack phases."
  reason: Makes PEAR-style tests deterministic and aligned with existing integration tests.

- agent: Engine Integration Agent (or Implementation Generalist for gameplay)
  change: "When family attacks are covered by headless pumps, ensure telegraph completion has a non-SceneTree-timer path (signal watchdog and/or export fallback) and avoid `is_inside_tree()` guards that block pumped `_physics_process` on valid hosts."
  reason: Matches strict manual pump semantics and prevents false-red headless contracts.

- agent: Acceptance Criteria Gatekeeper Agent
  change: "If Validation Status cites `ci/scripts/run_tests.sh` exit 0, confirm whether the diff touches `asset_generation/python/`; when yes, note diff-cover/pytest success explicitly alongside Godot evidence."
  reason: Full CI is not Godot-only; closure text should reflect both gates.

### Workflow Improvements
- issue: Dual-runtime CI (Godot + Python diff-cover) is easy to under-specify in Godot-heavy tickets.
  improvement: Add a gatekeeper checklist item: “Python diff touched → pytest+diff-cover evidence” whenever repo status includes `asset_generation/python/` changes.
  expected_benefit: Fewer surprise red CI runs after local Godot-only validation.

- issue: Deferred host wiring is invisible to tests unless explicitly mirrored.
  improvement: Require spec or TEST_DESIGN note listing deferred hooks that the PEAR harness must invoke for parity.
  expected_benefit: Less debugging of “works in play, fails in contract test” from ready-state skew.

### Keep / Reinforce
- practice: Map ticket ACs to trace IDs (`PEAR-T-08`/`PEAR-T-09` for multi-attack / cooldown separation) so “attacks more than once” has an objective headless substitute.
  reason: Bridges human play ACs with automated bounded simulation evidence.

- practice: Construct `RunSceneAssembler` via script instance + `_spawn_generated_enemies_for_room` without entering full run assembly, then free orphan instances.
  reason: Tests the production spawn path without duplicating spawn logic or dragging unrelated run lifecycle.

---

## [03_procedural_enemy_attack_loop_runtime] — Addendum (checkpoints: anti-burst, ESM closure)
*Completed: 2026-04-14*

*Supplements the entry above; avoids repeating headless pump + diff-cover themes already captured there.*

### Learnings
- category: testing
  insight: Aggregate “≥2 projectiles / ≥2 cycles” checks are not sufficient to define a clean attack loop; pairing them with per-cycle cardinality (e.g. PEAR-T-20: N completed cycles ⇒ exactly N projectiles for acid) catches burst-fire within one telegraph that inflates counts without real loop separation.
  impact: Without per-cycle bounds, headless pumps can mask spam or multi-spawn as “multi-attack.”
  prevention: For pumped ranged families, specify trace IDs for one-projectile-per-cycled-telegraph (or explicit salvo rules in spec) alongside multi-cycle engagement tests.
  severity: medium

- category: process
  insight: Planner-stage uncertainty about whether a stub ESM is sufficient must be resolved in specification before implementation whenever later tests assert stateful behavior (e.g. death suppressing further cycles); a single integration test requiring a real `EnemyStateMachine` forces that closure.
  impact: Medium-confidence planner assumptions on ESM fidelity risk rework when ACs imply statemachine-driven gating.
  prevention: Spec and TEST_DESIGN must list which ESM behaviors are in scope (idle-only stub vs death/lifecycle) and map each to a contract ID before coding.
  severity: medium

### Anti-Patterns
- description: Interpreting high projectile counts from a headless pump as proof of a disciplined attack loop without per-cycle separation.
  detection_signal: PEAR-T-08 passes marginally while fire patterns cluster in single-pump windows or violate cooldown spacing in gameplay.
  prevention: Add adversarial per-cycle assertions (anti-burst, cooldown delta) when TEST_BREAK reviews PEAR contracts.

### Prompt Patches
- agent: Test Breaker Agent
  change: "When adversarial review targets headless pumped attack-loop contracts, question aggregate-only multi-attack tests: require or recommend per-cycle projectile cardinality or explicit salvo exceptions in the spec."
  reason: Closes the burst loophole discussed in M10-03 TEST_BREAK (PEAR-T-20 rationale).

### Keep / Reinforce
- practice: `project_board/CHECKPOINTS.md` recorded PEAR landing RED until host/M8 wiring—contract-first integration failures were visible before closure.
  reason: Makes RED→green progression auditable for cross-layer procedural spawn work.

---

## [M25-ESPS] — Cross-ticket implementation bundling, stale test selectors, and RTL text-node fragmentation
*Completed: 2026-04-14*

### Learnings
- category: process
  insight: When an implementation agent hits a rate limit before doing any work, prior commits from adjacent tickets may already contain the required implementation. The agent must audit recent commits before treating the feature as "not yet done."
  impact: The Python eye-shape implementation (animated_build_options.py, blender_utils.py, spider/slug/claw_crawler builders) was delivered in commit e4b3f85 under a different ticket label. A naive agent would have re-implemented it, causing a duplicate or conflicting commit.
  prevention: At the start of every implementation run, scan `git log --oneline -10` and `git diff HEAD~5..HEAD -- <relevant paths>` to detect whether the spec's target functions already exist before writing a single line.
  severity: high

- category: testing
  insight: Frontend test selectors that use `getByText(/pattern/i)` on text split across inline child elements (e.g., `<code>` inside `<strong>` inside a paragraph) silently fail because RTL resolves `textContent` per node, not by joining siblings.
  impact: `ColorsPane.test.tsx` used `/animated.*player/i` against text rendered as two separate inline nodes; the test had been green on a previous DOM structure but broke without any component code change.
  prevention: When writing RTL selectors for text that spans multiple inline elements, use `getByRole` with `name` matcher, `getByTestId`, or `getAllByText` with exact match on the innermost text node. Never assume `getByText(/regex/)` will match across child-element boundaries.
  severity: medium

- category: testing
  insight: Test selectors tied to exact component copy text (e.g., `/pick an enemy/i`) become stale when UI copy changes and produce false negatives that are invisible until the suite is run against the updated component.
  impact: `ExtrasPane.test.tsx` used `/pick an enemy/i` but the component had been reworded to "geometry extras"; the test failed with no implementation change on this ticket.
  prevention: Empty-state and placeholder assertions should use `data-testid` attributes or role-based selectors rather than copy-dependent regexes. When a test must match visible text, prefer the shortest stable fragment (one or two unique words) and add a comment flagging the fragility.
  severity: low

- category: process
  insight: A missing agent slot in the routing table (no Python/frontend specialist registered) caused the orchestrator to fall through to "Engine Integration Agent" with a domain note, then correct itself to a generalist. The correction works but introduces an unnecessary routing indirection that appears in the workflow history.
  impact: Minor — no rework occurred, but the checkpoint record shows an indirection that could confuse future audits of which agent owns Python/frontend work.
  prevention: The routing table should include an explicit "Python/Frontend Implementation Agent" slot (or a "Generalist Implementation Agent" with explicit Python and frontend capability flags) so the orchestrator does not need to override with domain notes.
  severity: low

### Anti-Patterns
- description: Assuming implementation is absent without checking git history when the prior agent was interrupted by a rate limit.
  detection_signal: Workflow state shows a rate-limit interruption in the implementation stage; the next agent run begins writing files that the diff already contains.
  prevention: Every implementation agent run must begin with a git log + diff check against the spec's target files before writing any code.

- description: Binding RTL test assertions to user-visible copy text rendered across multiple inline DOM nodes.
  detection_signal: `getByText(/regex/i)` throws "Unable to find an element" even though the text is visually present; DevTools shows the text split across `<code>`, `<strong>`, or `<span>` siblings.
  prevention: Use `data-testid`, role matchers, or exact single-node text in RTL assertions for UI copy that may span elements.

- description: Accumulating stale test selectors over copy-editing cycles because no test ties the selector to a living component snapshot.
  detection_signal: A test fails only after a copy change, not after a code change; the selector worked for months.
  prevention: Treat copy-dependent test failures as a signal to migrate that assertion to a structural selector; add a comment at time of fix so the next editor knows the selector is fragile.

### Prompt Patches
- agent: Implementation Frontend Agent
  change: "Before writing any frontend implementation code, run `git log --oneline -10` and check whether the spec's target files already contain the required changes. If they do, skip implementation and proceed directly to running the test suite."
  reason: Prevents duplicate or conflicting implementation when a prior commit (from an adjacent ticket or an interrupted run) already contains the work.

- agent: Test Designer Agent
  change: "When writing RTL assertions for empty-state or placeholder text, do not use `getByText(/copy text/i)` if the text may span inline child elements. Prefer `getByTestId`, `getByRole`, or exact single-node text matchers. Add a comment in the test if you must use a copy-dependent regex."
  reason: Prevents the RTL text-node fragmentation failure pattern seen in ColorsPane.test.tsx and ExtrasPane.test.tsx.

### Workflow Improvements
- issue: The routing table has no dedicated Python/frontend agent slot, causing the orchestrator to emit a domain-note override and log an "Engine Integration Agent" step for work that is clearly Python/frontend.
  improvement: Add an explicit "Python / Frontend Implementation Agent" row to the routing table with capability flags covering Python asset pipeline, FastAPI, and TypeScript/React frontend work.
  expected_benefit: Cleaner workflow history; no override indirections; future auditors can immediately identify which agent was responsible for Python/frontend implementation steps.

- issue: Stale test selectors tied to copy text are not caught until the full test suite is run against the updated component, often by a different agent in a later stage.
  improvement: Add a pre-commit or CI lint rule (e.g., a custom eslint rule or grep gate) that flags `getByText(/[A-Za-z]{5,}/i)` patterns in test files as requiring a review comment justifying the copy dependency.
  expected_benefit: Forces authors to consciously document copy-dependent selectors at write time, reducing silent staleness.

### Keep / Reinforce
- practice: The test-break stage wrote adversarial suites covering `None`, whitespace-only strings, integer truthy/falsy coercion, and list-typed values for the new controls before implementation existed.
  reason: These adversarial edge cases (captured in test_eye_shape_pupil_controls_adversarial.py) exercised `_coerce_and_validate` paths that could silently corrupt serialized JSON. Writing them before implementation — and marking assumptions with `# CHECKPOINT` — keeps the contract honest.

- practice: The frontend fix commit (1cb8e23) was a single-line change to BuildControls.tsx, with two additional stale-test fixes isolated in the same commit and fully described in the message.
  reason: Minimal targeted fixes with explicit change descriptions make bisection and revert straightforward. This is the correct scope discipline for a "one missing rule" gap.

---

## [04_headless_tests_procedural_combat_enemies] — Headless contract scope clarity and fail-closed spawn semantics
*Completed: 2026-04-15*

### Learnings
- category: process
  insight: Ticket AC text that says "register in `tests/run_tests.gd`" can conflict with modern recursive runner discovery; the authoritative registration mechanism must be explicit in spec/test design to avoid unnecessary edits and false non-compliance.
  impact: This ticket required an assumption to reconcile legacy wording with current discovery behavior, creating avoidable ambiguity during TEST_DESIGN.
  prevention: Add a standing rule that test-registration ACs must declare whether explicit `run_tests.gd` entries are required or whether `tests/test_*.gd` discovery is sufficient.
  severity: medium

- category: architecture
  insight: Malformed generated-enemy declarations should fail closed at entry granularity (skip bad entry, continue processing room) rather than aborting entire room assembly.
  impact: The checkpoint captured medium-confidence uncertainty on invalid `res://` behavior; without explicit per-entry semantics, runtime behavior can diverge across agents.
  prevention: Specs for spawn pipelines must include a malformed-input matrix that names blast radius per failure type (entry-level, room-level, run-level) and required diagnostics.
  severity: high

- category: performance
  insight: Unknown `enemy_family` entries in repeated spawn evaluation loops should mark completion metadata after fail-closed handling to prevent deterministic retry storms.
  impact: TEST_BREAK had to checkpoint this behavior explicitly; absent done-meta, bad declarations can repeatedly re-trigger work each call.
  prevention: Include anti-retry assertions for malformed declarations in adversarial suites whenever spawn logic is frame- or call-driven.
  severity: high

- category: testing
  insight: Headless combat-room validation is most stable when it tests loader/scene-path contracts with bounded frame pumping, instead of requiring full-physics playthrough semantics.
  impact: The ticket achieved deterministic CI-safe coverage by asserting loadability and family/path contracts directly, avoiding harness limitations that can cause hangs.
  prevention: For room-content verification tickets, default to bounded contract assertions first and treat full-physics behavior as a separate runtime/integration scope.
  severity: medium

### Anti-Patterns
- description: Treating legacy AC phrasing as implementation-mandatory when project infrastructure has shifted (manual test registration vs auto-discovery).
  detection_signal: TEST_DESIGN checkpoint asks whether to edit `tests/run_tests.gd` despite passing discovery conventions in existing suites.
  prevention: Require spec stage to resolve registration authority and cite the current runner contract before test files are authored.

- description: Leaving malformed spawn behavior unspecified at the blast-radius level.
  detection_signal: Checkpoints ask whether invalid paths/unknown families should fail one entry or the entire room.
  prevention: Add explicit malformed-case outcome tables in spec (continue/abort, diagnostics required, metadata side effects).

### Prompt Patches
- agent: Spec Agent
  change: "When a ticket includes test-registration language, explicitly state the authoritative registration mechanism (manual `tests/run_tests.gd` entry vs recursive discovery) and map that decision to a requirement ID."
  reason: Prevents avoidable ambiguity and unnecessary file churn during TEST_DESIGN.

- agent: Test Breaker Agent
  change: "For spawn/declaration adversarial tests, require one anti-retry case: malformed entries must fail closed and set completion metadata (or equivalent) so repeated calls do not reprocess the same invalid declaration."
  reason: Catches retry-storm regressions that are not visible in single-call malformed tests.

- agent: Acceptance Criteria Gatekeeper Agent
  change: "If AC mentions test registration, verify closure evidence cites the active runner contract (discovery or manual list) rather than inferring from ticket wording alone."
  reason: Keeps acceptance decisions aligned with current infrastructure instead of stale phrasing.

### Workflow Improvements
- issue: Legacy AC wording and evolving runner infrastructure create repeated interpretation checkpoints.
  improvement: Add a reusable "test registration authority" checklist item to planning/spec templates for all test-only tickets.
  expected_benefit: Fewer assumption logs and faster progression from SPECIFICATION to TEST_DESIGN.

- issue: Malformed spawn semantics required medium-confidence assumptions in both SPECIFICATION and TEST_BREAK.
  improvement: Add a standard spawn-failure taxonomy section to procedural enemy specs (invalid path, unknown family, empty list, shape/type mismatch) with mandatory blast-radius outcomes.
  expected_benefit: Less agent drift and stronger cross-ticket consistency for fail-closed behavior.

### Keep / Reinforce
- practice: Enforcing bounded frame pumping with strict iteration caps for headless combat-room tests.
  reason: Preserves deterministic CI behavior while still validating runtime-relevant contracts.

---

## [M25-06] — Wrong method placement, None coercion, and file-size org violations cause implementation rework
*Completed: 2026-04-15*

### Learnings
- category: architecture
  insight: When a geometry feature is added to a class with separate `build_mesh_parts()` and `apply_themed_materials()` methods, new mesh-creation calls belong exclusively in `build_mesh_parts()`. Placing them in `apply_themed_materials()` breaks any test harness that patches at module import level and calls only `build_mesh_parts()`, because the test never exercises the patched path.
  impact: Four enemy files (spider, imp, claw_crawler, carapace_husk) had mouth/tail creation code in the wrong method; all four required rework after tests caught the mismatch.
  prevention: Implementation agent prompts for anatomy-style enemy classes must state: "All new mesh object creation must occur in `build_mesh_parts()`. `apply_themed_materials()` must not create mesh objects."
  severity: high

- category: testing
  insight: Using `str(dict.get(key))` to coerce an optional dict value to a string silently converts `None` to the literal string `"None"`, which is an unrecognized shape name. The correct guard is `str(dict.get(key) or default)`.
  impact: A `mouth_shape=None` input (e.g. from a UI reset that clears the key) would be forwarded to geometry builders as the string `"None"`, causing an unknown-shape fallback silently — or a crash if no fallback existed. The Test Breaker identified this as a high-risk mutation case and added an explicit test; the coerce bug was then found during implementation.
  prevention: Any string coercion of an optional dict key must use `or`-guarded default: `str(options.get(key) or fallback)`. Test designer prompts should include "test that `None` value for string-type options falls back to the default, not to the string 'None'."
  severity: high

- category: process
  insight: Pre-commit file-size org hooks create a hard stop after implementation if new code is appended to already-large modules without proactive extraction. A module at 850 lines that grows to 969 after a ticket triggers a hook violation requiring a second extraction commit.
  impact: `animated_build_options.py` exceeded the 900-line limit and `AnimatedSpider` exceeded the 350-line class limit; both required post-implementation extraction into new modules, adding a fixup commit cycle.
  prevention: Implementation agent must check current module line counts before writing new code to existing files. If adding to a module already within 100 lines of the org limit, extract first. Prompt patch: "Before appending to any existing Python module, count its current lines. If current_lines + estimated_additions > 900, extract a helper module first."
  severity: medium

- category: architecture
  insight: When a new float control (`tail_length`) is produced by the same helper that also produces non-float controls (`tail_enabled`, `tail_shape`), the caller's split-by-type assembly will only work correctly if the helper return list is filtered — not just appended whole — into the non-float and float blocks. Appending the entire helper output to `static_float` places the booleans in the wrong block; appending it to `static_non_float` places the float in the wrong block.
  impact: `tail_length` was initially placed after `static_float` rather than interleaved before mesh floats, violating the control ordering invariant. Caught by ordering tests; fixed in `animated_build_controls_for_api()`.
  prevention: Spec must explicitly state that mixed-type helpers (returning both float and non-float controls) must be split during assembly, not appended wholesale to either block. Spec Agent prompt patch: "If a new control helper returns controls of mixed types, the spec must specify how the caller filters and routes each type to the correct assembly block."
  severity: medium

- category: process
  insight: diff-cover can block merge even after all unit tests pass, if new geometry functions are added to `blender_utils.py` but test files only exercise those functions indirectly through enemy builder mocks. Direct function-level tests on the utility module are required to meet line-coverage gates.
  impact: `create_mouth_mesh` and `create_tail_mesh` in `blender_utils.py` had insufficient direct coverage; a separate `test_blender_utils_mouth_tail.py` file with 26 tests was required to bring diff-cover to 87%.
  prevention: When implementation adds new utility-layer functions that callers mock in tests, the Test Designer must also produce at least one test file that calls those utility functions directly (via the blender stub environment). Prompt patch for Test Designer: "For every new function added to a shared utility module (e.g. `blender_utils.py`), include at least one test file that imports and calls that function directly — do not rely solely on enemy-builder tests that mock the utility."
  severity: medium

### Anti-Patterns
- description: Placing mesh-creation logic in `apply_themed_materials()` instead of `build_mesh_parts()` in enemy builder classes.
  detection_signal: Tests that patch `create_*_mesh` at the enemy module level and call `build_mesh_parts()` pass unconditionally (mock never asserted called), while tests that run the full pipeline show unexpected part counts.
  prevention: Enforce a single-method rule in the implementation prompt: only `build_mesh_parts()` may create or attach new mesh objects.

- description: Using `str(dict.get(key))` without an `or`-guarded default for optional string options.
  detection_signal: Test Breaker adds a mutation case `key=None`; implementation passes it through to geometry builder as the string `"None"`.
  prevention: Standardize the coercion idiom to `str(options.get(key) or default)` and add it to the implementation agent's coercion instruction list.

- description: Adding substantial new code to a module already near the org line-count limit, deferring extraction until pre-commit blocks the commit.
  detection_signal: Pre-commit hook fails with "file exceeds N lines" after implementation — the extraction that should have been done first becomes a fixup step.
  prevention: Implementation agent checks module line count before starting; extraction is performed proactively if the estimate puts the module over the limit.

### Prompt Patches
- agent: Implementation Agent (Python)
  change: "Before appending new code to any existing Python module, count its current line total. If current_lines + estimated_additions would exceed 900 lines, extract a new helper module for the new code first, then import from it. Do not wait for pre-commit hooks to surface this."
  reason: Pre-commit org violations after implementation force a fixup extraction commit, adding unnecessary rework and delay.

- agent: Implementation Agent (Python)
  change: "In enemy builder classes that have both `build_mesh_parts()` and `apply_themed_materials()`, all new mesh object creation (calls to `create_*_mesh`, `bpy.ops.mesh.primitive_*`, or any function returning a `bpy.types.Object`) must be placed in `build_mesh_parts()`. The method `apply_themed_materials()` must not create mesh objects."
  reason: Tests patch utility functions at module import level and call `build_mesh_parts()`. Code placed in `apply_themed_materials()` is invisible to those tests, causing false passes and missed bugs.

- agent: Spec Agent
  change: "When a new control helper returns controls of mixed types (e.g., both `bool`/`select_str` and `float`), the spec must explicitly state how the caller splits that helper's output during control assembly — specifying which types route to the non-float block and which route to the float block. Do not leave this as an implementation detail."
  reason: Ambiguity about mixed-type helper assembly caused `tail_length` to be placed in the wrong block, requiring a fix after ordering tests failed.

- agent: Test Designer Agent
  change: "For every new function added to a shared utility module (e.g., `blender_utils.py`), include at least one test file that imports and calls that function directly using the blender stub environment. Do not rely solely on enemy-builder integration tests that mock the utility function — those tests cannot provide diff-cover for the utility module itself."
  reason: Mocked utility calls do not produce line coverage on the utility module; this creates a diff-cover gap that blocks merge even after all unit tests pass.

- agent: Test Breaker Agent
  change: "For any new string-type option that is read from a build_options dict, add a mutation test case where the option value is explicitly `None`. Verify the output is the string default (e.g., `'smile'`), not the literal string `'None'`. Flag any implementation that uses `str(dict.get(key))` without an `or`-guarded fallback."
  reason: `str(None)` produces `"None"`, a valid string but an unrecognized shape name, causing silent wrong-shape geometry that no standard option-validation test would catch.

### Workflow Improvements
- issue: Post-implementation org violations (file too long, class too long) forced a fixup extraction step after all tests passed, adding an extra commit and delaying ticket completion.
  improvement: Add a pre-implementation checklist item to the Implementation Agent: verify current line counts on all target modules before writing. If any module is within 100 lines of the org limit, plan and execute extraction first.
  expected_benefit: Eliminates the rework cycle of implement → pre-commit fail → extract → re-commit, which wastes a full round-trip and obscures the semantic commit boundary.

- issue: The Test Breaker's adversarial mutation for `shape=None` (producing the string `"None"`) correctly flagged a coercion risk, but that insight was not systematically encoded as a standard adversarial case for string options.
  improvement: Add "value=None mutation" as a standard adversarial test template for all `select_str` and `str`-typed options in the Test Breaker's procedure, not just when the agent happens to notice it.
  expected_benefit: Consistent coverage of the `str(None) == "None"` failure mode across all future option-handling tickets without relying on agent initiative.

### Keep / Reinforce
- practice: The Test Breaker logging placement sign tests (mouth location X > 0, tail location X < 0) as a high-severity gap and adding them before implementation.
  reason: Directional sign errors in geometry placement formulas (e.g., negating the head X offset) produce visually wrong but non-crashing output that no functional unit test would catch without explicit coordinate assertions.

- practice: Requiring all 6 geometry-wired slugs in baseline part-count regression tests (not just a representative subset).
  reason: Per-enemy implementation bugs (wrong method, missing import, off-by-one in part append) only appear on the affected enemy. Covering only a subset leaves regressions invisible until visual QA.

---

## [M25-PTP] — Defensive build-option coercion + preview overlay safety
*Completed: 2026-04-16*

### Learnings
- category: testing
  insight: When UI-controlled configs flow through a coercion/validation layer, adversarial tests must include non-finite floats (`NaN`, `±inf`), `None`, whitespace, and wrong-type inputs — not just out-of-range numbers and unknown enums.
  impact: Without these cases, option validators can silently emit non-JSON values, crash on `float()` conversion, or pass `"None"`/whitespace through as apparently-valid strings, producing hard-to-debug preview behavior.
  prevention: Make a standard mutation suite for every new control set: `None`, `""`, `"  value  "`, mixed case, list/dict types, `NaN`, `±inf`, plus min/max clamp checks for floats.
  severity: high

- category: architecture
  insight: Unknown enum values should collapse to the safest “disable everything / no-op” state, while still keeping the selector/control itself usable.
  impact: Treating unknown `mode` as partially-enabled can enable incompatible parameter rows and create confusing UI states; treating it as an error can lock users out of recovery.
  prevention: Define a consistent policy: invalid enum → canonical `"none"` (or equivalent), and in the UI: all mode-specific rows disabled, but the mode row always enabled.
  severity: medium

- category: architecture
  insight: Preview-only shader/material overlays must not assume UV availability; provide a deterministic coordinate fallback (object/world-space position) to keep procedural materials robust across generated meshes.
  impact: Procedural assets or primitive-derived GLBs may omit UVs, leading to broken shaders or uniform patterns that look “flat” and trigger false bug reports.
  prevention: In shader overlay patterns, explicitly support `uv` when present and fall back to position-derived coordinates when absent; treat this as a baseline requirement for procedural visualization features.
  severity: medium

### Anti-Patterns
- description: Only testing “happy path” values for new build options (valid enums, normal floats) and skipping `None`/NaN/∞/wrong-type mutations.
  detection_signal: Validators use `float(value)` / `str(value)` without guarding non-finite values and tests don’t mention `NaN` or `None`.
  prevention: Require a minimal adversarial matrix for every new option family and block completion until it exists.

- description: Letting unknown mode strings partially enable UI controls or disable the mode selector itself.
  detection_signal: A bad `mode` value causes inconsistent disabled/enabled rows or makes it impossible to switch back to “none”.
  prevention: Normalize invalid enums to `"none"` in validation and keep the mode selector always enabled in UI gating logic.

- description: Writing procedural shader overlays that assume UVs exist on all meshes.
  detection_signal: Shader code references `vUv` with no fallback path and preview regressions appear only on specific generated models.
  prevention: Require UV-optional shader patterns and a fallback coordinate strategy in spec and code review.

### Prompt Patches
- agent: Test Breaker Agent
  change: "For every new float option, add adversarial cases for `NaN`, `+inf`, `-inf`, and `None` and define the expected behavior (default vs clamp). For every new string/select option, include `None`, whitespace-padded, and mixed-case inputs; assert canonicalization."
  reason: Prevents validators from emitting non-JSON values or silently accepting garbage that causes UI/preview drift.

- agent: Spec Agent
  change: "For any new `mode`/enum control, explicitly specify the invalid-value policy (normalize to `'none'` or equivalent) and the UI recovery requirement (mode selector never disabled; invalid behaves like 'none' for gating)."
  reason: Avoids repeated assumption logs and prevents ambiguous UI states when configs contain unexpected values.

### Workflow Improvements
- issue: Adversarial mutation coverage for option coercion is often discovered late (during TEST_BREAK) instead of being a first-class part of test design.
  improvement: Add an “Option coercion adversarial matrix” checklist item to TEST_DESIGN for tickets that add controls (floats + enums + strings).
  expected_benefit: Earlier detection of coercion edge cases and fewer mid-implementation validator rewrites.

- issue: Shader-based preview features can pass all unit tests while still failing on models lacking specific attributes (e.g., UVs).
  improvement: Require the spec to declare required mesh attributes (uv/normals) and fallback behavior when absent for any preview-only material override feature.
  expected_benefit: Fewer model-specific preview regressions and less reliance on manual visual QA.

### Keep / Reinforce
- practice: Treating `options_for_enemy()` inputs as immutable and asserting idempotency/non-mutation.
  reason: UI stores frequently reuse config objects; mutation introduces state bleed and non-deterministic preview updates.

- practice: Keeping color controls as plain strings (hex) with explicit parsing/fallback rules rather than inventing new control types mid-ticket.
  reason: Prevents unnecessary frontend plumbing churn while still enabling consistent coercion and safe defaults.

---

## [M25-04] — AC/Execution Plan divergence, phantom test keys, and under-evidenced visual AC
*Completed: 2026-04-18*

### Learnings
- category: process
  insight: When the Planner descopes an AC item, the descoped AC text must be cross-struck or replaced in the ticket — not just noted in the Execution Plan. AC text and Execution Plan must be in agreement at the start of implementation, not resolved at the AC gate.
  impact: AC-4 ("A 'Reset Rotation' button restores the part to 0/0/0") was descoped in the Execution Plan but the AC text was left unchanged. This forced the AC Gatekeeper to resolve the conflict under uncertainty (Confidence: Medium), creating a checkpoint and delaying closure rather than catching the mismatch before the pipeline began.
  prevention: The Planner must annotate or overwrite any AC item it intends to descope at planning time; the Spec Agent should fail immediately if AC text conflicts with the Execution Plan on a non-trivial feature.
  severity: high

- category: process
  insight: Visual/runtime AC items that use the word "immediately" require an explicit evidence strategy defined in the spec, not resolved by assumption at the AC gate.
  impact: AC-5 ("Rotation changes reflect immediately in the 3D preview") required a checkpoint assumption that "immediately" means "upon next generate". This is defensible but not self-evident — it took a Medium-to-High confidence judgment call by the AC Gatekeeper rather than a deterministic check.
  prevention: Any AC item describing real-time or immediate visual feedback must specify in the spec or Execution Plan: the exact triggering action ("after clicking Regenerate" vs. "on slider release") and what automated evidence covers it (e.g., a unit test on the pipeline path, a screenshot, or explicit acceptance that manual smoke test is the gate).
  severity: medium

- category: testing
  insight: Test Breaker agents can introduce phantom keys — control keys that do not yet exist in the codebase — as "backward-compat" guard tests. When the Implementation Agent is not permitted to modify test files, it must add the phantom key to the implementation as dead/cosmetic code to pass the test, introducing scope creep silently.
  impact: The Test Breaker wrote a test for `RIG_HEAD_SCALE` which was not defined anywhere. The Implementation Agent added it to `allowed_non_mesh` and defaults without applying it in `build_mesh_parts`, creating a no-op key that appears in API responses. This is a scope mutation that bypassed review.
  prevention: Test Breaker agents must only add tests for keys/behaviors that are (a) explicitly described in the spec, or (b) logical variants of spec-described behavior. Any test that references a named constant, key, or symbol not present in the spec must be flagged in the checkpoint and escalated rather than silently causing the implementation to invent new surface area.
  severity: high

- category: process
  insight: When an Execution Plan task calls for verifying or documenting behavior in a test file ("add a code comment" or "extend existing test file"), but specifies no concrete assertion, it is frequently delivered as only a comment — not a test. This constitutes a coverage gap even when it is technically compliant with the task wording.
  impact: Task 6 ("Verify frontend Rig section renders RIG_HEAD_ROT_X") was delivered as a code comment in `BuildControls.meta_load.test.tsx` rather than an assertion. The Execution Plan wording permitted this ("if the existing filter already covers this by convention, document that no new test case is needed and add a code comment"), but the result is zero automated evidence that the Rig section filter works for rotation keys.
  prevention: Any Execution Plan task that touches a test file must produce either (a) a passing assertion or (b) an explicit human-acknowledged waiver. "Add a comment" should not be an acceptable substitute for test coverage when the test file is already open and a simple assertion is feasible.
  severity: medium

### Anti-Patterns
- description: Leaving AC text unchanged after the Planner descopes a feature in the Execution Plan, allowing the two sources of truth to diverge until the AC gate.
  detection_signal: Execution Plan contains "out of scope" or "not implemented" for something named in the AC checklist; no strikethrough or revision marker exists in the AC section.
  prevention: Require the Planner to annotate or replace any AC item it descopes; the Spec Agent validates consistency between AC and Execution Plan before proceeding.

- description: Test Breaker introducing keys/symbols not defined in the spec as phantom backward-compat tests, forcing the Implementation Agent to invent new surface area.
  detection_signal: An Implementation Agent checkpoint logs adding a key to `allowed_non_mesh`/defaults for a symbol not present in the Execution Plan or spec; Confidence is marked Low.
  prevention: Test Breaker must cross-reference every symbol it names in a test against the spec; phantom keys must be logged as a spec gap and escalated, not silently added.

- description: Treating a code comment in a test file as equivalent to a test assertion when verifying filtering/rendering behavior.
  detection_signal: A task's "Success Criteria" is met by a comment rather than a `expect`/`assert` call; `npm test` shows no new test cases for the touched file.
  prevention: Distinguish "document coverage" tasks (comment only acceptable) from "verify behavior" tasks (assertion required); Execution Plan language must be unambiguous about which category applies.

### Prompt Patches
- agent: Planner Agent
  change: "If an AC item is descoped or modified by the Execution Plan, you MUST annotate it directly in the AC section using a strikethrough or bracketed note such as `[DESCOPED: see Execution Plan Task N]`. The Execution Plan may not silently override AC text. The Spec Agent will fail if AC and Execution Plan are inconsistent on any non-trivial item."
  reason: Prevents the AC Gatekeeper from needing to resolve conflicts under uncertainty; eliminates Medium-confidence checkpoint assumptions on descoped features.

- agent: Test Breaker Agent
  change: "You may only write tests that reference keys, symbols, or behaviors explicitly described in the current ticket's spec or Execution Plan. If you believe a backward-compat guard is needed for a key not present in those documents, log it as a checkpoint with Confidence: Low and do NOT add a failing test for it — instead, flag it as a spec gap for human review."
  reason: Prevents phantom keys from forcing the Implementation Agent to invent new surface area (dead no-op controls) to pass tests that were never part of the ticket scope.

- agent: Spec Agent
  change: "For any AC item that uses the words 'immediately', 'real-time', or 'live', define the exact triggering action and the automated evidence strategy. State explicitly: (a) the user action that triggers the visual update, (b) whether this is covered by a unit test on the pipeline, a manual smoke test, or an explicit waiver, and (c) whether 'immediately' means on-input-change or on-generate. Leave nothing to be resolved at the AC gate."
  reason: Removes ambiguity that leads to Medium-confidence AC gate assumptions on visual/runtime acceptance criteria.

### Workflow Improvements
- issue: The AC Gatekeeper is the first agent to detect AC-vs-Execution-Plan divergence, but by that point the full implementation has already been delivered under the wrong scope. Resolving it requires a checkpoint and a judgment call rather than a deterministic pass/fail.
  improvement: Add an explicit "AC-vs-Execution-Plan consistency check" step to the Spec Agent's output gate: list each AC item and map it to the Execution Plan task that covers it; flag any AC item with no task and any task that reduces AC scope as an issue requiring resolution before the spec advances.
  expected_benefit: AC descopes are caught before implementation begins, eliminating end-of-pipeline scope-conflict checkpoints.

- issue: Task 6 pattern ("verify by convention, add comment if no change needed") consistently produces comment-only deliverables that provide no automated regression protection. The same risk recurred on M25-03 and M25-04.
  improvement: Replace "extend or comment" language in Execution Plan tasks with a binary: either a concrete `describe`/`it` block with one assertion that fails if the filter breaks, or a documented waiver signed off in the checkpoint log. The verification task success criterion must name the specific assertion.
  expected_benefit: Frontend filter and routing logic gains at least one regression test per ticket that touches it; "comment only" coverage gaps are eliminated.

### Keep / Reinforce
- practice: Parametrizing clamp/boundary tests across all affected slugs rather than the minimum required set.
  reason: A parametrized test over all 6 slugs catches slug-specific wiring omissions that a single-slug test would miss; the cost is near-zero and the signal is high.

- practice: Using dedicated module-level functions (`_rig_rotation_control_defs()`) for new control families rather than ClassVar promotion or ad-hoc dict literals.
  reason: ClassVar introspection with dynamic bounds breaks for default=0.0 (generates wrong range); explicit defs give exact step/min/max and are the established pattern for tail/mouth controls. Keeps control definitions co-located, testable independently, and easy to audit.

---

## [M901-01-import-standardization] — Import migration triggers org limits and diff-cover scope beyond “primary” files
*Completed: 2026-04-21*

### Learnings
- category: process
  insight: Repository organizational gates (for example line-count or module-size limits) treat import churn in large modules as structural change; a ticket scoped to imports can still force extraction or file splits before pre-commit passes.
  impact: `material_system.py` exceeded the enforced line threshold after import edits, requiring a new companion module and test patch location updates.
  prevention: Run org/size pre-commit or equivalent checks on the heaviest touched modules during implementation, not only at final handoff; plan extractions in the same deliverable when churn risks crossing thresholds.
  severity: medium

- category: testing
  insight: Coverage tools keyed to branch diff against `main` fail when any changed file has uncovered executable lines, even when those lines pre-existed or were not the semantic focus of the ticket.
  impact: Static QA initially reported diff-cover failure on `gradient_generator.py` despite the import ticket not targeting gradient behavior; closure required adding focused behavior tests until the diff hit the threshold.
  prevention: For any file that appears in the coverage diff, either add minimal behavior tests for uncovered branches or record an explicit, ticket-linked coverage waiver before gating—not an open escalation with no default resolution path.
  severity: medium

- category: architecture
  insight: Centralizing import bootstrap (`sys.path` / `PYTHONPATH` alignment) in the application entry layer keeps router and handler modules free of path-mutation patterns, which allows static AST checks to enforce the same contract as entrypoints.
  impact: Backend routers remained eligible for “no `sys.path` mutation” CI rules while subprocess and package layout stayed consistent with `pyproject` conventions.
  prevention: Prefer one sanctioned bootstrap point for path injection; avoid scattering compatibility hacks in modules that must stay lint-clean for static import contracts.
  severity: medium

### Anti-Patterns
- description: Treating import standardization as purely mechanical line edits while ignoring automated module-size or organization rules on high-churn files.
  detection_signal: Implementation checkpoint notes a pre-commit failure solely from line count or structure after import edits, without a corresponding extraction task in the plan.
  prevention: Include “verify org pre-commit on top-N touched modules” in implementation exit criteria for large refactor tickets.

- description: Raising diff-cover failures as ambiguous blockers when uncovered lines sit in ancillary files appearing only because of merge-base or tangential edits.
  detection_signal: Coverage report cites files the ticket did not name in its description, with no documented decision to test or waive.
  prevention: Gatekeeper or Static QA checklist: for each uncovered file in the diff, choose “add behavior tests” or “document waiver + owner” before rerunning the gate.

### Prompt Patches
- agent: Implementation Generalist Agent
  change: "For tickets that touch imports across large modules, run repository organization pre-commit (or equivalent line-count / structural checks) on those modules before declaring complete. If churn crosses a size threshold, extract submodules or split files in the same change set and update tests that patch symbols on moved objects."
  reason: Prevents a separate rework cycle solely to satisfy org gates after import migration.

- agent: Static QA Agent
  change: "When diff-cover or coverage-on-diff fails, enumerate each file with uncovered lines in the branch diff. For each file, either (1) add minimal behavior tests covering those lines or (2) write an explicit coverage waiver tied to a follow-on ticket—do not leave the failure as an unresolved 'pre-existing' note without one of these closures."
  reason: Makes coverage remediation deterministic and avoids indefinite gate retries.

- agent: Acceptance Criteria Gatekeeper Agent
  change: "If all ticket acceptance criteria have objective test evidence but Stage cannot advance to COMPLETE because the ticket file is still under `ready/` (milestone rule requires `done/`), set Stage to INTEGRATION (or the appropriate pre-complete stage), document the folder-move prerequisite in `NEXT ACTION`, and do not imply AC failure—distinguish 'AC satisfied' from 'workflow terminal state satisfied.'"
  reason: Prevents false signals that work failed when only a filesystem handoff remains.

### Workflow Improvements
- issue: Revision and workflow metadata were missing on the ticket at pipeline start, forcing a baseline `Revision: 1` assumption in the orchestrator checkpoint.
  improvement: Require new tickets to include initialized `WORKFLOW STATE` (Stage + Revision) or have the orchestrator seed them in a single first commit before spec work begins.
  expected_benefit: Fewer Medium-confidence assumptions about revision history and cleaner audit trails.

- issue: Terminal completion requires both AC evidence and physical move of the markdown file to `done/`, which can strand Learning/Blog agents that key off Stage `COMPLETE`.
  improvement: Automate or script the `ready/` → `done/` move when the AC gate passes, or add an explicit pipeline trigger on `INTEGRATION` + AC-validated instead of only `COMPLETE`.
  expected_benefit: Reduces human bottleneck and clarifies when downstream agents may run.

### Keep / Reinforce
- practice: Encoding the full import contract (entrypoints, backend routers, registry seams, package exports) in CI before the migration is finished, including subprocess and AST-based negative checks.
  reason: Makes partial migration states detectable early and aligns implementation with R1–R4 without relying on manual review alone.

- practice: Closing diff-cover gaps by adding behavior tests for the previously uncovered surfaces (`gradient_generator`, `get_enemy_materials` themes) rather than bypassing the gate.
  reason: Strengthens regression protection for code that entered the diff scope and satisfies coverage policy with durable tests.

---

## [M901-03-type-hints-and-documentation] — Scope ambiguity and strict-type gating noise drove assumption-heavy execution
*Completed: 2026-04-21*

### Learnings
- category: process
  insight: If ticket scope terms like "all refactored modules" are not frozen to an explicit file inventory before test design, multiple downstream stages will independently re-interpret scope and accumulate Medium-confidence assumptions.
  impact: Orchestrator, Test Designer, and Static QA each logged separate scope assumptions for AC enforcement and denominator boundaries, increasing coordination overhead and confidence risk despite eventual pass.
  prevention: Require the spec to include a canonical scoped-file manifest and AC-to-file mapping that all later agents must reuse without reinterpretation.
  severity: high

- category: testing
  insight: Type-gate acceptance criteria that require strict checking on scoped files need an explicit strategy for handling out-of-scope transitive imports.
  impact: Initial raw strict run surfaced transitive failures outside ticket scope, requiring a later scoped `mypy --strict --follow-imports=skip` contract to recover deterministic gating.
  prevention: Define the strict-type command contract in the spec (including import-follow policy) and make Test Designer/Static QA assert against that exact command from the start.
  severity: medium

- category: process
  insight: AC items that can be legitimately N/A due to scoped-no-diff conditions must include objective evidence rules, not ad hoc interpretation at integration time.
  impact: AC2 required a late explicit N/A proof path (`web/backend` no-diff evidence), which worked but consumed gatekeeper and static-QA decision bandwidth.
  prevention: For each cross-layer AC, predefine N/A criteria and required evidence artifact (for example, path-scoped diff proof) in the spec.
  severity: medium

### Anti-Patterns
- description: Repeated stage-by-stage scope interpretation instead of one frozen manifest reused across the pipeline.
  detection_signal: Multiple checkpoints in the same ticket contain "Would have asked" entries about module-set boundaries with Medium confidence.
  prevention: Block advancement from SPECIFICATION until a concrete file list and denominator policy are published.

- description: Running an unconstrained strict type check first, then retrofitting a scoped command after transitive failures appear.
  detection_signal: Checkpoints mention "initial raw strict run failed out-of-scope" followed by a different strict command used for final evidence.
  prevention: Require strict-command freeze (targets + flags) before implementation and treat deviations as a spec/test-design defect.

### Prompt Patches
- agent: Spec Agent
  change: "For any AC that uses scoped language (e.g., 'all refactored modules'), you MUST produce a canonical file manifest and AC-to-file matrix in the spec. Downstream agents must treat this manifest as the only valid scope source and may not redefine scope in checkpoints."
  reason: Eliminates repeated Medium-confidence scope assumptions and keeps evidence deterministic across stages.

- agent: Test Designer Agent
  change: "When a ticket includes a strict static-analysis AC (`mypy --strict`, lint gates, etc.), define and record the exact command (targets and flags) in tests/checkpoint notes. If transitive import behavior is excluded, explicitly encode that policy before implementation starts."
  reason: Prevents rework from late command changes and avoids ambiguous pass/fail criteria at integration.

- agent: Static QA Agent
  change: "If an AC is satisfied via scoped N/A (for example, no touched files in a required layer), you must attach objective evidence using a path-scoped diff command and cite the governing spec clause in the checkpoint."
  reason: Converts N/A decisions from subjective judgment into repeatable, auditable evidence.

### Workflow Improvements
- issue: Scope and denominator assumptions were rediscovered in three separate stages instead of resolved once upstream.
  improvement: Add a required "Scope Lock" artifact in SPECIFICATION (file manifest + denominator definition + cross-layer N/A rules) and fail TEST_DESIGN entry if missing.
  expected_benefit: Fewer checkpoint assumption loops, faster stage transitions, and higher-confidence AC validation.

- issue: Strict type-check strategy was stabilized only after an initial failure mode exposed transitive-noise risk.
  improvement: Introduce a pre-implementation static-gate dry-run in TEST_DESIGN that executes the exact strict command contract on the frozen scope.
  expected_benefit: Surfaces command/flag defects earlier and removes integration-stage gate churn.

### Keep / Reinforce
- practice: Logging assumption checkpoints with explicit confidence and "Would have asked" framing when ambiguity cannot be resolved immediately.
  reason: Preserves auditability and makes hidden uncertainty visible for future prompt/workflow hardening.

- practice: Pairing contract-only checks with behavior regression suites before declaring documentation/type-hardening complete.
  reason: Prevents non-functional tickets from masking runtime regressions while still enforcing strict typing/documentation outcomes.

---

## [M901-04-utility-file-consolidation] — Spec resolves AC literalism; contracts beat ticket filenames
*Completed: 2026-04-21*

### Learnings
- category: architecture
  insight: When a milestone ticket names a single file (e.g. `build_options.py`) but parallel work and collision avoidance favor a package facade, the approved spec must explicitly reconcile literal AC text with the chosen layout and record traceability to requirement IDs.
  impact: Without that bridge, reviewers can treat package layout as AC failure even when behavior and imports are correct.
  prevention: Freeze requirement IDs (e.g. R5) that define the canonical module shape and add a one-line AC mapping note in workflow validation, as done for `build_options/` vs. ticket wording.
  severity: medium

- category: process
  insight: Arbitrary per-module LOC caps in ticket prose often conflict with existing large domains; the planner should force the spec to either exempt, split, or replace the guideline before implementation—not assume implementers will silently compress code.
  impact: Medium-confidence planning assumptions arose for `build_options` size vs. "< 250 LOC" language; resolved only at spec time.
  prevention: For refactor tickets, replace vague LOC rules with “per spec §X decomposition” or drop the cap when a dependent ticket owns the bulk of the lines.
  severity: medium

- category: architecture
  insight: Path-validation helpers that mix “missing file” with “wrong shape” failures need an explicit exception taxonomy in the spec; choosing one catch-all type is a product decision for pipeline ergonomics.
  impact: Spec assumed `ValueError` for all `validate_glb_path` rejections (medium confidence); a different choice would change caller `except` clauses.
  prevention: Require a short “Exceptions” subsection for any new validation API: which errors use `FileNotFoundError` vs `ValueError` vs custom types.
  severity: medium

- category: testing
  insight: Legacy-import AST gates that include `tests/` will stay red until the migration lands; that is expected and should be documented so implementers do not treat the suite as accidentally broken.
  impact: Test design consciously scoped RED phase across src and tests; avoids false “tests are flaky” diagnosis.
  prevention: In test-design checkpoints, state explicitly: “contract tests intentionally fail until task N.”
  severity: low

### Anti-Patterns
- description: Deferring adversarial coverage for relative imports inside a package (`from .foo`) while only scanning absolute import forms in AST gates.
  detection_signal: Test-break log notes “deferred” relative-import coverage with medium confidence.
  prevention: Add one targeted negative test or lint rule for forbidden relative re-exports when a ticket removes duplicate local modules (e.g. `demo`).

- description: Stating optional APIs in the ticket (“export_manifest_entry”) without a spec decision to implement, omit, or stub—leaving scope ambiguous until spec explicitly defers.
  detection_signal: Spec checkpoint lists a function as optional/deferred because it does not exist in the codebase.
  prevention: Mark optional AC lines in the ticket as “if duplication exists” or remove them; spec must record omit vs implement with requirement ID.

### Prompt Patches
- agent: Planner Agent
  change: "When a ticket sets a per-file LOC target that conflicts with an existing or sibling-owned large module, do not proceed to SPECIFICATION until the ticket is amended or the spec template includes an explicit exemption or submodule decomposition table tied to requirement IDs."
  reason: Prevents medium-confidence assumptions and reviewer confusion when consolidated modules cannot meet arbitrary line counts.

- agent: Spec Agent
  change: "For every new validation function that inspects paths or files, add an 'Exception contract' bullet: list each failure mode and the exact exception type raised; do not leave 'ValueError vs FileNotFoundError' implicit."
  reason: Aligns pipeline exception handling with intentional semantics rather than implementer guesswork.

- agent: Test Breaker Agent
  change: "When R7-style 'no duplicate module name' rules apply, include at least one check for relative imports (`from .`) that could resurrect a shadow module without appearing in absolute-import AST scans, or document the gap as an accepted risk with owner sign-off."
  reason: Closes a class of regressions that absolute-only gates can miss.

### Workflow Improvements
- issue: Ticket acceptance criteria used literal filenames while the coordinated design required a package directory.
  improvement: Require milestone tickets that overlap another ticket’s namespace to include “canonical shape per spec §…” in ACs, not only filenames.
  expected_benefit: Fewer false AC failures and less validation narrative in workflow state.

- issue: Large mechanical import migrations can make RED contract tests look like environmental failure.
  improvement: Orchestrator or test-design stage adds a one-line banner in the ticket or checkpoint: “Import contract tests are expected RED until implementation stage completes.”
  expected_benefit: Reduces wasted triage on pre-implementation runs.

### Keep / Reinforce
- practice: Using a package `__init__.py` facade with `__all__` on the implementation module and star-import for stable public surface when replacing a flat module.
  reason: Preserves attribute parity for `import pkg as alias` patterns and keeps re-export intent explicit for reviewers.

- practice: Recording AC-to-spec traceability in validation status when ticket wording and spec shape diverge.
  reason: Gives auditors a single place to justify layout decisions without reopening scope debates.

---

## [M901-05-material-system-refactoring] — Freeze compatibility boundaries early when AC wording and legacy paths diverge
*Completed: 2026-04-22*

### Learnings
- category: process
  insight: Ticket wording that mixes conceptual module targets (for example `system.py`) with legacy import paths requires an explicit compatibility decision in the spec before test design.
  impact: The specification had to make a Medium-confidence assumption to keep `material_system.py` as the compatibility entrypoint while treating `system.py` as the orchestration target, which could have caused import-path churn or backend regressions if interpreted differently downstream.
  prevention: Add a mandatory "canonical runtime entrypoint vs conceptual module target" clause to refactor specs whenever acceptance criteria mention renamed or extracted modules.
  severity: high

- category: architecture
  insight: Registry-family lists in acceptance criteria should be treated as minimum required coverage unless the spec explicitly marks them as exhaustive.
  impact: Texture-handler scope required an explicit assumption to include existing modes beyond the listed families (`organic`, `gradient`, `stripes`, `spots`); without this, refactors can accidentally drop legacy behavior while still appearing AC-compliant.
  prevention: In spec freeze, annotate each capability list as "minimum set" or "exclusive set" and require tests for retained legacy modes when marked as minimum.
  severity: medium

- category: testing
  insight: For extraction refactors, encoding the target module contract as primary RED behavioral tests is a stronger anti-regression strategy than waiting for post-refactor parity checks.
  impact: Test design established extracted-module contracts up front, which created deterministic failure signals for missing modules and reduced ambiguity about what implementation had to preserve.
  prevention: Keep contract-first RED tests as the default pattern for decomposition tickets and explicitly prohibit prose-only or import-only assertions as the primary gate.
  severity: medium

### Anti-Patterns
- description: Deferring module-boundary decisions (compatibility facade vs physical rename) until implementation while AC text and existing imports point to different filenames.
  detection_signal: Specification checkpoints include "Would have asked" entries about whether to rename a core module path, with Medium confidence assumptions.
  prevention: Block advancement from SPECIFICATION unless module naming, compatibility shim policy, and consumer import guarantees are explicitly frozen.

- description: Treating listed feature families in AC text as an implicit exclusion set when legacy behavior already supports additional families.
  detection_signal: Spec or implementation checkpoints ask whether non-listed legacy modes should be retained.
  prevention: Require explicit "scope set semantics" (minimum vs exclusive) for every enumerated capability list.

### Prompt Patches
- agent: Spec Agent
  change: "When acceptance criteria reference new module names but legacy import paths still exist, include a required Compatibility Boundary subsection that states: (1) canonical runtime entrypoint for this ticket, (2) whether a facade/shim is required, and (3) whether any caller import-path changes are allowed."
  reason: Prevents Medium-confidence naming assumptions and keeps refactor behavior stable for downstream consumers.

- agent: Test Designer Agent
  change: "For decomposition/extraction tickets, write contract-first RED tests against the target extracted modules and orchestration surface before implementation; do not rely on import-presence checks as primary evidence."
  reason: Produces deterministic failure signals and reduces late-stage ambiguity about extraction completeness.

- agent: Acceptance Criteria Gatekeeper Agent
  change: "If a ticket is intentionally routed through the generic spec gate while touching compatibility-sensitive layers, require one explicit checkpoint line that justifies gate type selection and names the residual risk review method."
  reason: Makes gate classification auditable and prevents silent under-scoping of validation rigor.

### Workflow Improvements
- issue: The ticket started without explicit `WORKFLOW STATE` / `NEXT ACTION`, forcing orchestrator assumptions at run start.
  improvement: Add a pre-stage normalization step that seeds missing workflow metadata (Stage, Revision, Next Responsible Agent) before PLANNING for all ready tickets.
  expected_benefit: Reduces assumption logging and improves audit continuity across stages.

- issue: Spec gate-type selection can remain implicit when tickets are "mostly generic" but still include backend compatibility constraints.
  improvement: Add a lightweight gate-classification checklist to orchestrator output that records why generic/API/destructive/randomness/load-open was selected.
  expected_benefit: Improves traceability and prevents downstream disagreement on whether validation depth matched risk.

### Keep / Reinforce
- practice: Recording "Would have asked" assumptions with confidence levels in checkpoints.
  reason: Surfaces uncertainty early and creates concrete input for prompt/workflow hardening rather than burying ambiguity in silent decisions.

- practice: Verifying cross-layer non-modification claims with path-scoped diff evidence (for example backend router scope checks).
  reason: Converts compatibility claims into objective evidence and lowers regression risk for non-target layers.

---

## [M901-06-animated-build-options-consolidation] — Preserve package-level helper compatibility during file retirement
*Completed: 2026-04-22*

### Learnings
- category: architecture
  insight: Deleting legacy modules in a consolidation ticket can still break consumers when package-level helper re-exports are treated as "internal" and dropped.
  impact: A post-implementation regression fix was required to restore helper exports (`_mouth_control_defs`, `_tail_control_defs`, `_eye_shape_pupil_control_defs`) after adversarial contract tests failed.
  prevention: Treat package `__init__` exports as part of the compatibility surface unless the spec explicitly deprecates them; require test coverage for symbol-level parity before legacy-file deletion is considered complete.
  severity: high

- category: testing
  insight: Adversarial checks for mutable-default isolation and malformed envelope handling are high-leverage guards in schema/validation consolidations.
  impact: Test-break contracts detected subtle behavior risks that import-only checks would miss, and provided deterministic regression signals during refactor churn.
  prevention: For consolidation tickets, require at least one idempotence/mutable-default test and one malformed-input fail-closed test in the mandatory suite.
  severity: medium

- category: process
  insight: Acceptance criteria that mix structural refactor goals with maintainability targets need objective proof artifacts, not narrative claims.
  impact: Gate closure depended on scripted import-order/cycle evidence and deterministic `<150 LOC` touchpoint measurement rather than subjective "looks simpler" assertions.
  prevention: Standardize evidence bundles for refactors: import graph proof, targeted behavioral suite, diff-cover preflight, and scripted maintainability metric when LOC-style ACs exist.
  severity: medium

### Anti-Patterns
- description: Assuming named public APIs are the full compatibility contract while silently dropping package helper exports used by active tests/imports.
  detection_signal: Consolidation passes core API tests but fails late with missing-symbol import errors from package boundaries.
  prevention: Add an explicit "package export parity" checklist item and contract test set before deleting legacy modules.

- description: Declaring maintainability ACs as satisfied without deterministic measurement criteria.
  detection_signal: Checkpoints justify LOC/complexity targets with prose but no reproducible command output.
  prevention: Require one scripted metric command per maintainability AC and store its output in validation status.

### Prompt Patches
- agent: Implementation Generalist Agent
  change: "Before deleting legacy modules in a compatibility-sensitive refactor, enumerate and preserve package-level exports (including helper symbols used by tests/runtime imports). If any symbol is intentionally removed, require an explicit deprecation decision in the spec and matching test updates."
  reason: Prevents late regression cycles caused by hidden import-surface dependencies.

- agent: Test Breaker Agent
  change: "For schema/validation consolidations, always add adversarial tests for (1) mutable-default isolation across repeated calls and (2) malformed envelope payloads that must fail closed without exceptions."
  reason: Captures high-risk behavioral regressions that basic parity tests often miss.

- agent: Acceptance Criteria Gatekeeper Agent
  change: "When maintainability ACs use numeric targets (for example '<150 LOC for new enemy onboarding'), require deterministic command-based evidence in Validation Status; reject narrative-only justification."
  reason: Makes non-functional AC validation objective and reproducible.

### Workflow Improvements
- issue: Compatibility regressions were discovered after the initial implementation handoff, requiring a dedicated regression-fix iteration.
  improvement: Add a mandatory pre-handoff "export compatibility smoke" step in IMPLEMENTATION for consolidation tickets that delete legacy modules.
  expected_benefit: Reduces gatekeeper bounce-backs and shortens time-to-complete for refactor tickets.

- issue: Maintainability acceptance evidence required an extra integration pass to formalize scripted proof.
  improvement: Require maintainability evidence commands to be prepared during IMPLEMENTATION, not deferred to final integration evidence updates.
  expected_benefit: Eliminates late-stage evidence churn and increases first-pass gate success.

### Keep / Reinforce
- practice: Recording assumption checkpoints with confidence levels and converting medium-confidence assumptions into explicit evidence reruns.
  reason: Maintains auditability while preventing assumption drift from becoming silent acceptance-criteria debt.

- practice: Re-running both targeted behavioral suites and diff-cover preflight after regression fixes.
  reason: Confirms that compatibility patches close the immediate failure without weakening quality gates elsewhere.

---

## [M901-10-backend-python-import-adapter] — Contract freezing prevented import-boundary drift during backend adapter migration
*Completed: 2026-04-22*

### Learnings
- category: process
  insight: Infrastructure/refactor tickets that enter the pipeline without initialized workflow metadata (stage/revision) create avoidable assumption debt at PLANNING.
  impact: The run required a Medium-confidence workflow-state initialization assumption before normal execution, adding non-functional ambiguity at ticket start.
  prevention: Add a pre-planning normalization step that auto-seeds missing workflow metadata for all `ready/` tickets before agent execution begins.
  severity: medium

- category: architecture
  insight: For import-boundary migrations, freezing adapter location and root-precedence policy in SPECIFICATION is necessary to keep downstream behavior deterministic.
  impact: Explicitly locking a service-layer adapter seam and deterministic root-selection precedence prevented router-level divergence while preserving endpoint behavior.
  prevention: Require spec-time "adapter boundary + precedence contract" for any migration that centralizes runtime import/bootstrap logic.
  severity: high

- category: testing
  insight: Locking a minimal runtime adapter API surface during TEST_DESIGN yields stronger migration safety than abstract seam assertions.
  impact: Fixing concrete adapter symbols enabled deterministic router-migration tests without fragile source-inspection gates.
  prevention: For boundary-extraction tickets, require test design to declare the minimal callable API contract (symbol names + responsibilities) before implementation.
  severity: medium

### Anti-Patterns
- description: Starting implementation pipelines from tickets with incomplete workflow-state scaffolding.
  detection_signal: Early checkpoints include "Would have asked" entries about missing revision/stage initialization rather than technical behavior.
  prevention: Block PLANNING entry when `WORKFLOW STATE` fields are absent or malformed; auto-repair first.

- description: Deferring import-boundary policy decisions (adapter path, precedence, API names) until implementation.
  detection_signal: Spec/test checkpoints contain medium-confidence assumptions about where the boundary lives or which symbols must exist.
  prevention: Require SPECIFICATION and TEST_DESIGN gates to fail closed unless boundary location, precedence, and minimal API contract are explicitly frozen.

### Prompt Patches
- agent: Orchestrator Agent
  change: "Before PLANNING, validate that the ticket contains a complete WORKFLOW STATE block (Stage, Revision, Last Updated By, NEXT ACTION). If missing, normalize these fields explicitly and record the normalization in the checkpoint before any stage advancement."
  reason: Eliminates startup ambiguity and reduces repeated metadata assumptions across downstream agents.

- agent: Spec Agent
  change: "For any ticket that centralizes Python import/bootstrap behavior, you MUST include an 'Import Boundary Contract' subsection that freezes adapter module location, root-selection precedence, and failure-surface ownership (adapter vs caller) before handoff."
  reason: Prevents implementation-time drift in infrastructure seams that can silently reintroduce duplication or non-determinism.

- agent: Test Designer Agent
  change: "When testing boundary-extraction refactors, define and lock a minimal runtime API surface (exact symbol names and responsibilities) for the new boundary module; do not rely on abstract seam language alone."
  reason: Produces deterministic, behavior-first migration tests and reduces interpretation gaps during implementation.

### Workflow Improvements
- issue: Workflow-state incompleteness was handled as an ad hoc assumption instead of a standardized precondition check.
  improvement: Introduce a mandatory ticket-normalization gate before PLANNING that seeds/validates workflow metadata.
  expected_benefit: Cleaner audit trail and fewer non-technical assumption checkpoints.

- issue: Generic gate selection can mask risk in compatibility-sensitive backend migrations unless contract details are explicitly frozen.
  improvement: Add a gate-classification note requiring explicit residual-risk controls (boundary contract and deterministic failure taxonomy) when using generic routing for backend import refactors.
  expected_benefit: Preserves lightweight workflow while keeping validation rigor proportional to integration risk.

### Keep / Reinforce
- practice: Defining deterministic root resolution and adapter-owned failure taxonomy before implementation.
  reason: Keeps import behavior stable across routers and enables reproducible error-path testing.

- practice: Using adapter-focused behavioral tests plus router regression suites as joint closure evidence.
  reason: Validates both the extracted seam and unchanged public route behavior in one coherent gate package.

---
## [M901-11-registry-path-policy-unification] — Freeze security-path contract details early to avoid medium-confidence assumptions
*Completed: 2026-04-22*

### Learnings
- category: process
  insight: Security-sensitive backend tickets that start without fully initialized workflow metadata force avoidable non-technical assumptions before real planning begins.
  impact: PLANNING had to make a medium-confidence initialization decision for revision/state scaffolding, adding audit noise and early ambiguity.
  prevention: Require a pre-planning metadata normalization check that seeds missing workflow fields before stage advancement.
  severity: medium

- category: testing
  insight: Path-policy contract tests are most stable when the service API symbol and rejection taxonomy are frozen explicitly before RED tests are authored.
  impact: TEST_DESIGN needed a medium-confidence assumption to bind to one function signature and `ValueError` fail-closed behavior; this could have caused churn if implementation chose a different exception surface.
  prevention: In spec freeze, mandate an explicit "API symbol + exception taxonomy" contract for all validation/canonicalization boundaries.
  severity: high

- category: architecture
  insight: Generic spec-gate routing can still be appropriate for backend-integrated refactors if residual risk controls are explicitly documented.
  impact: The run skipped API-type gate checks by assumption; correctness stayed intact only because the downstream contract remained behavior-focused and fail-closed.
  prevention: When selecting generic gate for backend-touching security work, require a checkpoint note that names compensating controls (behavioral contract coverage plus deterministic rejection policy).
  severity: medium

### Anti-Patterns
- description: Treating workflow-state initialization as an ad hoc planning assumption rather than a standardized prerequisite.
  detection_signal: Early checkpoint logs contain "Would have asked" entries about revision/stage defaults instead of technical design tradeoffs.
  prevention: Block PLANNING until workflow metadata is validated or auto-normalized.

- description: Writing validation tests before freezing concrete error-contract semantics.
  detection_signal: Test-design checkpoints include medium-confidence assumptions about exception types or callable symbols.
  prevention: Add mandatory exception-taxonomy and API-surface bullets to spec templates for security/path policy tickets.

### Prompt Patches
- agent: Orchestrator Agent
  change: "Before PLANNING on any ticket, validate that WORKFLOW STATE fields are present and coherent (Stage, Revision, Last Updated By, NEXT ACTION); if missing, normalize them first and record the normalization as a non-technical precondition step."
  reason: Removes repeated initialization ambiguity and keeps checkpoint evidence focused on engineering risk.

- agent: Spec Agent
  change: "For path-validation or canonicalization requirements, add an explicit 'Error Contract' subsection that freezes function symbol(s), return shape, and exact exception taxonomy for invalid/malformed/forbidden classes."
  reason: Prevents test and implementation drift on fail-closed behavior semantics.

- agent: Test Designer Agent
  change: "Do not author final RED contract assertions for security validation boundaries until the spec explicitly declares callable API symbol names and exception taxonomy; otherwise emit a blocking clarification checkpoint."
  reason: Avoids brittle or assumption-driven tests that can mis-specify the intended boundary contract.

### Workflow Improvements
- issue: Gate-type choice (generic vs API) for backend-adjacent security tickets was justified only implicitly.
  improvement: Add a required gate-classification line in orchestrator checkpoints that states chosen gate type plus compensating controls.
  expected_benefit: Improves auditability and keeps validation rigor proportional to integration risk.

- issue: Contract-critical details (symbol and exception semantics) were left to test-design assumptions.
  improvement: Extend specification checklist with a required "runtime boundary contract" block for validation-heavy tickets.
  expected_benefit: Reduces rework risk and keeps RED tests deterministic across agent handoffs.

### Keep / Reinforce
- practice: Freezing behavior-level policy outcomes independent of transitional module placement.
  reason: Preserves migration flexibility without sacrificing deterministic security behavior.

- practice: Requiring cross-layer command evidence (service contract suite plus router delegation/regression suites) for closure.
  reason: Validates both centralized policy correctness and unchanged endpoint behavior in one acceptance pass.

---

## [M901-13-backend-registry-service-extraction-and-router-thinning]

### Learnings
- **FastAPI router modules bind imported function names as local attributes** (`from services.registry_query import safe_is_file_under_python_root`). Tests that patch `services.registry_query.safe_is_file_under_python_root` may not affect the router if the router calls the *local* binding. For transport-level behavioral tests, patch `routers.registry.<symbol>` (or re-import patterns) when exercising route bodies.
- **“Thin router” refactors should separate policy (`src.model_registry.service`) from composition** (`services/registry_query.py` scanning `model_registry.json` and assembling candidate rows).

### Anti-Patterns
- **String-substring guard tests on router source** after introducing imports (false positives). Prefer AST-based checks for forbidden top-level function definitions.

### Prompt Patches
- **agent: Test Designer Agent** — "When a router uses `from package import fn`, require tests to state whether they are patching the defining module or the router’s bound name; default to patching the router for route-level behavior."
- **agent: Implementation Backend Agent** — "When extracting helpers from routers, add a small AST contract test to prevent reintroducing extracted `def` names into the router module."

### Workflow Improvements
- Add a standard checklist item for FastAPI re-exports: "identify all `from import` names used in route functions and list their patch targets for tests."

### Keep / Reinforce
- **Mechanical module-boundary tests** (AST) for “router stays transport-only” without tying tests to milestone prose.

---

## [M8-01-enemy-floating-health-bar] — Guard-clause correctness requires dedicated adversarial test coverage in GDScript features with disabled modes

*Completed: 2026-05-16*

### Learnings
- category: testing
  insight: GDScript guard-clause logic (if !enabled { return }) can appear correct in unit tests of individual methods but fail under integration load if the test suite does not explicitly verify that disabled guards prevent observable state changes across all mutation paths. Behavioral-only assertions (method returns successfully) are insufficient—tests must capture side effects before and after.
  impact: AC 6 required a dedicated test file (test_enemy_health_bar_3d_debug_toggle.gd) with 9 focused tests verifying that enabled=false prevents fill updates, visibility changes, and position updates. Without explicit guard-coverage tests, implementation could have soft-disabled some paths (e.g., visibility changes) while leaving others active (e.g., position updates), creating partial-disable bugs only visible in full-scene integration.
  prevention: For any GDScript feature with an enabled/disabled flag, require an explicit adversarial test suite that asserts absence of state mutations when disabled, not just presence when enabled. Capture before/after state (visibility, progress_bar.value, node.position) rather than relying on return-value assertions.
  severity: high

- category: process
  insight: World-space UI features (health bars, floating damage text) introduce positional-binding assumptions that are easy to defer to implementation but riskier when implementation must discover camera-facing projection logic and offset values without spec-level examples or baseline test cases.
  impact: The planning checkpoint captured 10 clarifying questions with medium-to-medium-high confidence on positioning (offset value, billboard implementation choice, camera focus under rotation). Test Designer and Implementation agents had to re-derive these behaviors through test iteration. A spec-level example screenshot or pseudocode for position-update logic would have reduced assumption churn.
  prevention: For world-space UI specs, include pseudocode or concrete calculation examples for position-to-screen-space projection. Document baseline offset values or ranges (e.g., "1.0–1.5m above enemy root center") and specify fallback behavior if camera is in unusual orientations (behind enemy, orthogonal).
  severity: medium

- category: testing
  insight: Multi-test-file strategies (primary, adversarial-1, adversarial-2, debug-toggle, integration) are high-leverage for incremental-feature discovery but create maintenance burden if the test suite does not explicitly separate concerns. Behavioral test files should map cleanly to either "core AC behavior" or "risk category" (null-safety, boundary values, edge cases, feature flag).
  impact: The ticket produced 71 tests across 5 files with clear separation: primary (core methods), adversarial-1 (null-safety/boundaries), adversarial-2 (determinism/concurrency), debug-toggle (AC 6 flag), integration (signal wiring/scene lifecycle). This separation made it easy to add the 9 debug-toggle tests late without reshuffling existing test organization. Tighter specs upfront would have allowed all 71 tests to be designed together in TEST_DESIGN rather than iteratively during implementation.
  prevention: In TEST_DESIGN, explicitly list risk categories and map each test file to one category or a tightly-scoped combination (e.g., "integration handles signal + lifecycle" is one file; "null-safety + boundary values" is another). Avoid letting test files drift into multiple concerns without explicit mapping.
  severity: low

- category: architecture
  insight: Health-bar-style world-space UI components that depend on enemy properties (current_hp, max_hp) should declare their dependency contract explicitly in both spec and test. If the enemy health component is not yet implemented, spec-level pseudocode or a mock/stub contract is necessary to unblock Test Designer and Implementation.
  impact: Spec and checkpoint both captured a MEDIUM confidence assumption that "health is managed by a health component (not yet implemented) or exposed via EnemyBase properties." This deferral meant implementation had to stub/mock the health component in tests before testing the bar logic. Spec could have included a minimal HealthComponent interface (mock-friendly method signatures) as a non-blocking reference.
  prevention: For UI features that depend on unimplemented gameplay components, define a minimal interface contract (method names, return types) in the spec, even as a "reference mock" section. This unblocks parallel test + implementation work without waiting for the dependency to be coded first.
  severity: medium

### Anti-Patterns
- description: Treating "feature has an enabled flag" as sufficiently specified for testing without explicitly mapping guard-clause locations and verifying all side-effect paths respond to the flag.
  detection_signal: Implementation includes guard clauses at entry points (e.g., `if !enabled: return` in `_process`), but test suite only asserts method-return correctness, not state isolation.
  prevention: Create a mandatory checklist for enabled/disabled features: list all methods with state mutations, identify guard-clause entry points, then require state-before/after assertions for each mutation path when disabled.

- description: Deferring world-space positioning logic (offset calculation, camera projection, billboard update) to implementation without spec-level examples or baseline test pseudocode.
  detection_signal: Spec uses abstract language like "camera-facing" and "positioned above enemy" but includes no calculation example or concrete baseline values (e.g., offset = 1.2m).
  prevention: For positional UI specs, include pseudocode or worked example for projection logic, baseline offset ranges, and fallback behavior for edge cases (camera behind object, extreme angles).

- description: Accumulating test files without explicit concern mapping, allowing tests to drift into multiple risk categories per file.
  detection_signal: A single test file verifies both null-safety and integration wiring, making it hard to understand which tests apply to which concern or to add feature-flag coverage late without reshuffling.
  prevention: In TEST_DESIGN, declare test-file-to-concern mapping explicitly and update it when new risk categories emerge (e.g., "adding debug-toggle tests → new file test_*_debug_toggle.gd").

### Prompt Patches
- agent: Test Designer Agent
  change: "For any GDScript feature with an enabled/disabled or feature-flag contract, create a dedicated test file with explicit before/after state assertions for all methods that should respect the flag. Do not rely on method-return assertions alone; capture observable mutations (visibility state, numeric property values, node position/rotation) before and after disabled-flag execution, and assert no changes occurred."
  reason: Prevents partial-disable bugs where some code paths respond to the flag and others silently execute, only discoverable in full-scene integration.

- agent: Spec Agent
  change: "When specifying world-space UI (health bars, floating labels, damage text) that positions relative to 3D world objects, include a 'Positioning and Projection' subsection with pseudocode or worked examples for screen-space calculation, baseline offset values or ranges, and fallback behavior for camera edge cases. Reference unimplemented dependencies via interface contracts (mock-style method signatures) to unblock Test Designer and Implementation parallelization."
  reason: Reduces positioning-assumption churn and allows parallel test/implementation work even when gameplay dependencies are not yet coded.

- agent: Test Designer Agent
  change: "Explicitly map each test file to a concern category (core AC behavior, null-safety, boundary values, performance/determinism, feature flags, integration/signals) at the start of TEST_DESIGN. When new concerns emerge during implementation, add them to the mapping and create corresponding test files. Document the mapping in a comment at the top of each test file or in the test checkpoint."
  reason: Improves traceability and makes late-stage feature additions (e.g., AC 6 debug-toggle tests) easier to slot in without re-organizing existing test structure.

### Workflow Improvements
- issue: Test-suite expansion (from 4 planned test files to 5 actual files with 71 total tests) happened during implementation without early coordination, causing some rework in test organization.
  improvement: In TEST_DESIGN, require an explicit per-AC test-mapping (which tests cover which ACs) and per-AC risk breakdown (what edge cases / adversarial paths apply). This unblocks Test Breaker and Implementation from independently identifying additional test files without rework.
  expected_benefit: Reduces late-stage test-organization churn and allows all test files to be authored in parallel rather than sequentially during implementation.

- issue: Positioning logic for world-space UI was uncertain until implementation, requiring test iteration to validate camera projection and offset behavior.
  improvement: In SPEC, require a positioning-behavior worked example (pseudocode or screenshot) for world-space UI features. In TEST_DESIGN, use this example to author baseline integration tests before implementation, allowing implementation to match expected behavior rather than discover it.
  expected_benefit: Reduces positional-UI rework cycles and shortens implementation-to-passing-tests time.

- issue: AC 6 (debug flag toggle) was fully specified but lacked dedicated test-suite planning until implementation, causing a delayed test-file addition.
  improvement: In TEST_DESIGN, treat enabled/disabled or feature-flag ACs as requiring dedicated adversarial test files, not as an afterthought in the primary suite. Call out guard-clause coverage explicitly.
  expected_benefit: Ensures flag-based features are tested comprehensively upfront and reduces late-stage rework or partial-disable bugs.

### Keep / Reinforce
- practice: Multi-file test organization by risk category (primary, adversarial, feature-specific, integration) with clear separation of concerns.
  reason: Makes test suite maintainable and allows risk-specific test files to be added or expanded without disrupting the overall structure.

- practice: Writing adversarial and integration tests in parallel with primary tests rather than sequentially, to catch state-isolation and wiring issues early.
  reason: Reduces implementation-stage surprises and ensures edge cases are covered from the start.

- practice: Explicit before/after state assertions in guard-clause tests to catch partial-disable bugs.
  reason: Prevents subtle bugs where some code paths respect a disabled flag and others do not, only visible under integration load.

---

## [M8-SEFI] — GDScript API differences and test generation create cascading rework in generated test files

*Completed: 2026-05-17*

### Learnings
- category: testing
  insight: Generated GDScript test files that embed fixture setup code (mock enemy builders, indicator instance creation) create maintenance burden and compliance issues. When test generation produces ~5 test files with duplicated helper methods, later edits to fix compilation errors must be applied to each file independently, multiplying rework cycles. Generated test code should minimize or eliminate duplication at the point of generation, not defer it to manual cleanup.
  impact: Test Breaker created 42 additional tests across 2 files (mutation and concurrency suites). These files contained duplicated helper methods (_create_mock_enemy_with_effects, _create_indicators_instance). When implementation revealed compilation errors, fixing all copies required iterating through multiple files and manually reconciling changes. The fix commit had to update both mutation and concurrency test files with signature corrections and null parameter handling. Future test generation should template these helpers into a shared base class or mixin, not inline them.
  prevention: When generating multiple test files with shared fixtures, refactor duplicated helper methods into a parent class or mixin module at generation time. Require test generation to validate generated code compiles before committing. Include a post-generation deduplication pass that extracts common fixtures into a shared module (e.g., tests/ui/enemy_status_effect_indicators_fixtures.gd).
  severity: medium

- category: architecture
  insight: Godot 4 method availability differs from GDScript 3 and common assumptions (e.g., HBoxContainer.clear() does not exist). Implementation agents must verify API contracts against the actual Godot 4 runtime. Code review and linting can catch syntax errors but not missing methods on built-in classes.
  impact: Initial implementation used `_icon_container.clear()` to reset TextureRect children. This method does not exist in Godot 4; the correct pattern is manual iteration and queue_free(). The error was caught during integration but would have been a runtime crash. Static review cannot detect this (linter has no visibility into Godot class hierarchies). Future implementation agents need a Godot 4 API reference or examples from existing codebase.
  prevention: Add a Godot 4 API reference section to CLAUDE.md (or project_board/GODOT_API_NOTES.md) documenting commonly-used node patterns in this project: Container clearing, signal connection, scene instantiation, and dynamic child management. Include contrasts with GDScript 3 for agents familiar with older versions. Require implementation agents to validate API usage against a curated list before handoff to testing.
  severity: high

- category: testing
  insight: Test helper methods that instantiate components should prefer loading actual scene files (when possible) over programmatic inline instantiation. Scene-based instantiation exposes integration mismatches between scene structure (@export defaults, node hierarchies) and test expectations. Inline instantiation can pass tests but fail in scene context.
  impact: Early test helpers used inline _ready() logic to create EnemyStatusEffectIndicators instances without loading the scene file. Later, when integration revealed that max_visible_count changes after instantiation weren't triggering UI updates, it became clear that the scene file had no dynamic-resize logic. Adding _ensure_icon_rects() to the implementation required corresponding test helper updates to load the actual scene (which now calls _ensure_icon_rects()). Test helpers should load scenes from disk by default.
  prevention: For GDScript UI components, define a standard test-helper pattern: load scene file via ResourceLoader or preload, then modify @export properties programmatically if needed. Document this in test templates. Avoid inline instantiation of Control/Node trees; inline instantiation should only be used for pure-data fixtures (mock enemies) or utility helpers (color checks).
  severity: medium

- category: process
  insight: Dynamic @export property changes in Godot (e.g., max_visible_count changed at runtime) require coordinated re-initialization logic in both implementation and tests. If the implementation does not explicitly handle live updates to @export vars, tests that verify "change max_visible_count at runtime" will fail. Spec language like "live-tunable" must trigger implementation of property change handlers (_notification or explicit setters).
  impact: Mutation tests included `test_max_visible_dynamic_change_reduces_visible`, which changed max_visible_count after scene initialization and expected immediate re-render. Implementation initially did not handle this; the test would fail because TextureRects were pre-allocated at _ready time. Adding _ensure_icon_rects() to _render_indicators() fixed it by dynamically adjusting the icon rect pool whenever max_visible_count differed from current count.
  prevention: When spec mentions "@export properties" or "live-tunable" configuration, Test Designer must create explicit test cases for runtime property changes and Implementation must include a property-change handler (_notification with NOTIFICATION_PROPERTY_LIST_CHANGED or explicit setters) that re-initializes affected UI state.
  severity: medium

- category: testing
  insight: Mutation test coverage of edge cases like "max_visible_count changed to negative value" exposes boundary validation bugs that happy-path tests never exercise. Defensive clamping logic (max_visible_count = max(1, max_visible_count)) prevents crashes but may be missing if implementation assumes spec-valid input. Adversarial tests should include boundary-value mutations for all numeric @export properties.
  impact: Mutation tests included `test_max_visible_negative_becomes_one`, which verified that negative max_visible_count values were handled gracefully (clamped to 1, not crashed). This is a defensive pattern that should be standard for any numeric tuning parameters.
  prevention: For numeric @export properties in UI/gameplay, include boundary mutation tests (zero, negative, huge values). Implementation should clamp or reject invalid values explicitly (not assume editor prevents invalid input). Document clamping behavior in spec or code comments.
  severity: low

### Anti-Patterns
- description: Generating multiple test files with duplicated fixture code (helper methods that create mocks, instantiate components). This defers deduplication work and makes fixes apply in multiple places.
  detection_signal: Test generation produces 2+ files with identical method signatures (_create_mock_enemy_with_effects, _create_indicators_instance) that differ only in minor details or parameter order.
  prevention: At generation time, refactor duplicated helpers into a shared parent class or mixin module (tests/ui/*_fixtures.gd). Validate generated code compiles before returning.

- description: Assuming Godot 4 method availability based on GDScript 3 patterns or general knowledge. Methods like HBoxContainer.clear() do not exist in Godot 4, causing runtime failures.
  detection_signal: Implementation uses a method on a built-in class that was not validated against Godot 4 API docs or existing codebase usage.
  prevention: Require agents to check existing codebase usage of a node type before using unfamiliar methods. Add Godot 4 API pitfalls section to CLAUDE.md with common corrections (e.g., "use manual loop + queue_free() instead of .clear()").

- description: Test helpers that instantiate components inline without loading scene files. This hides integration mismatches between scene structure and test expectations.
  detection_signal: Test helper creates a Control/Node tree programmatically; later, scene-based integration reveals missing initialization or property handling.
  prevention: Require test helpers to load scene files when available. Reserve inline instantiation for data mocks only (e.g., mock enemies). Document this pattern in test templates.

- description: Spec language like "live-tunable" or "@export property" without corresponding implementation of property-change handlers. Changes to @export vars at runtime do not trigger UI updates.
  detection_signal: Mutation/adversarial tests change an @export property after initialization and expect immediate effect; implementation does not detect the change.
  prevention: When spec mentions "@export" or "live-tunable", include explicit test cases for runtime changes. Implementation must include _notification handler or property setter to re-initialize affected state.

### Prompt Patches
- agent: Test Breaker Agent
  change: "When generating multiple test files with shared setup fixtures, extract duplicated helper methods into a shared parent class (e.g., tests/<module>/<feature>_fixtures.gd) at generation time. Validate that all generated test files compile without parse errors before finalizing. Include a merge-deduplication step in the generation template to ensure helpers are defined once and imported by all test files."
  reason: Reduces rework cycles when fixing compilation errors across multiple test files and improves maintainability by centralizing fixture logic.

- agent: Implementation Agent (GDScript)
  change: "Before implementing methods or properties that reference built-in Godot classes (HBoxContainer, Control, etc.), verify method availability in the Godot 4 codebase by: (1) searching existing blobert files for similar usage (git grep 'HBoxContainer'), (2) consulting CLAUDE.md Godot API pitfalls section if present, (3) checking Godot 4 docs if uncertain. Document non-obvious API contracts (e.g., 'use manual child loop instead of .clear()') in code comments near the usage."
  reason: Prevents runtime failures from unavailable methods and builds team knowledge of Godot 4 API differences from earlier versions.

- agent: Spec Agent
  change: "When specifying dynamic or 'live-tunable' configuration (@export properties that can change at runtime), explicitly list which properties require immediate re-render or re-initialization (e.g., 'max_visible_count: changes must immediately adjust visible indicator count'). Include a 'Dynamic Property Changes' subsection in the spec that maps each mutable @export property to its expected behavior on change."
  reason: Ensures Test Designer and Implementation both understand that @export property changes require active handlers, not passive reflection.

- agent: Test Designer Agent
  change: "For UI components with @export numeric properties, create explicit boundary-value mutation tests (zero, negative, huge values) that verify graceful handling (clamping, error messages, or rejection) rather than crashes. Include these in adversarial/mutation test files alongside happy-path variants."
  reason: Exposes missing validation logic and ensures UI stability under invalid configuration.

### Workflow Improvements
- issue: Generated test files with duplicated fixture code require multiple coordinated fixes when compilation errors are discovered, multiplying rework cycles.
  improvement: Implement a deduplication pass in test generation that extracts common helper methods into a shared fixtures module and requires all generated test files to import from it. Validate generated code compiles as part of the generation output step.
  expected_benefit: Reduces fix-propagation burden and ensures generated test files are immediately compile-ready.

- issue: Implementation agents may not be familiar with Godot 4 API differences (e.g., missing .clear() method), leading to runtime failures only discovered during integration testing.
  improvement: Add a Godot 4 API reference section to CLAUDE.md or create a project_board/GODOT_4_API_NOTES.md with common pitfalls and correct patterns (Container clearing, signal connection, dynamic child management, etc.). Require static review to validate API usage against this reference.
  expected_benefit: Catches API mismatches during code review rather than integration testing.

- issue: Mutation tests that change @export properties at runtime revealed that implementation did not handle live updates, requiring addition of _ensure_icon_rects() logic.
  improvement: In SPEC, explicitly document @export properties that are "live-tunable" and their expected behavior on change. In TEST_DESIGN, create explicit test cases for each live property. In Implementation, use _notification(NOTIFICATION_PROPERTY_LIST_CHANGED) or explicit property setters to handle changes.
  expected_benefit: Ensures dynamic property handling is designed and tested upfront rather than discovered as a gap during mutation testing.

### Keep / Reinforce
- practice: Mutation test suites that exercise dynamic property changes (e.g., changing numeric config at runtime) to expose implementation gaps early.
  reason: These tests caught the max_visible_count live-update gap, preventing a subtle runtime bug where UI layout would not adjust to config changes.

- practice: Defensive clamping of numeric @export properties (max(1, max_visible_count)) to prevent crashes under invalid input.
  reason: Protects against editor misconfiguration or accidental negative values and makes UI stable under all numeric inputs.

- practice: Loading actual scene files in test helpers rather than inline instantiation, to expose scene-structure mismatches early.
  reason: Avoids integration surprises where tests pass but scene-based usage fails due to missing initialization.

---

## [M902-18] — Tool categorization system: ambiguity-first specification resolved SDK uncertainty and deferred framework integration

*Completed: 2026-05-18*

### Learnings
- category: process
  insight: When a feature depends on uncertain SDK or framework capabilities (e.g., "agent SDK supports tool filtering"), the Spec Agent should explicitly document the assumption, define a contract that assumes the capability exists, and defer implementation/framework-integration tasks to downstream agents who can verify and adapt. Spec does not validate SDK internals; it freezes the contract that implementation must satisfy.
  impact: Planner identified SDK tool filtering as MEDIUM-confidence assumption. Spec Agent did not investigate SDK availability; instead, it documented the assumption clearly and defined the interface contract (`get_tools_for_category()`) that implementation must deliver regardless of SDK mechanism. This deferred the framework integration details to Integration Agent (Task 5) but unblocked backend implementation (Task 4) immediately. All 180 backend tests passed without waiting for SDK coordination.
  prevention: When Spec encounters an uncertain external dependency (SDK feature, framework capability), capture the assumption in Spec Clarifying Questions section with explicit confidence levels. Define the feature contract (function signature, error handling, measurement protocol) independent of the SDK mechanism. Document what downstream agent (Integration Agent, Framework Integration) must verify and decide. This separates specification (what the feature does) from integration (how it hooks into frameworks).
  severity: high

- category: architecture
  insight: Backend implementation and framework integration can be decoupled via clear function contracts. Tool categorization has two phases: (1) Backend—build the filtering logic and measurement functions, fully testable in isolation; (2) Framework Integration—wire the framework to accept tool_category parameter and call backend functions. Separating these avoids blocking backend work on uncertain framework internals.
  impact: Execution plan explicitly anticipated deferred framework integration (Task 5 separate from Task 4 backend). This allowed Implementation Agent to complete all 180 tests and deliver tool_category_manager.py without waiting for agent framework code access or modification. Framework integration blocked by unknown framework architecture but has a clear contract to implement (accept tool_category param, extract category from prompt using regex, call get_tools_for_category()). Backward compatibility is guaranteed (agents without category param get all tools).
  prevention: For features that span backend logic + framework wiring, define a clear handoff contract: (1) Backend phase: define function interface, build against specs only, test in isolation with mocks. (2) Framework phase: accept handoff, verify framework can satisfy the contract, integrate cleanly. Document both phases in execution plan with separate tasks.
  severity: high

- category: testing
  insight: Adversarial and mutation test suites can detect spec gaps (unstated assumptions, missing constraints) early. Test Breaker discovered 7 significant gaps (version field requirement, tool naming constraints, config parsing strictness, file change detection, floating-point precision, schema immutability, bash categorization). These gaps do not block implementation but require explicit documentation and design decisions by implementer.
  impact: Test Breaker created spec-gap test class that exposed assumptions unstated in spec. Examples: (1) version field—spec doesn't say if required; (2) tool naming—no constraints on spaces/special chars; (3) bash in parse—implicit constraint not enforced. These gaps were flagged to Implementation Agent in recommendations. Implementation made reasonable decisions (strict parsing, accept all tool names, etc.) but the gaps should have been frozen in spec beforehand.
  prevention: Spec Agent should include a "Implicit Constraints" review pass before finalizing spec. For each config field, enum value, and function behavior, ask: "What am I assuming about this that is not explicitly stated?" Test Designer should then create spec-gap tests for each assumption. This moves assumption documentation from implementation time to spec time.
  severity: medium

- category: process
  insight: Acceptance Criteria Gatekeeper must recognize when partial satisfaction (AC-1 through AC-6 complete, AC-7 and AC-8 deferred to later tasks) is correct per the execution plan, not a blocker condition. In M902-18, 6 of 8 ACs were satisfied in backend phase; 2 ACs (live agent integration, runbook documentation) were correctly sequenced to Integration Agent tasks. Gatekeeper validated this was intentional per spec design, not an escalation issue.
  impact: Gatekeeper initially noted AC-4 and AC-5 (framework integration) not complete in this ticket, and AC-7 and AC-8 (live agent testing, runbook) not complete. But gatekeeper correctly recognized that execution plan explicitly anticipated these deferrals as downstream tasks, and confirmed with spec that this was the intended workflow. No escalation was needed; the ticket was correctly partitioned.
  prevention: Gatekeeper should cross-reference ticket WORKFLOW STATE against execution plan task breakdown before escalating incomplete ACs. If a task deliberately defers work to a later task, mark as "Deferred (intended)" with task reference rather than "Incomplete (blocker)". This requires gatekeeper to understand not just spec, but execution plan and task sequencing.
  severity: medium

- category: testing
  insight: Mutation tests can catch subtle bugs in deterministic functions (e.g., JSON serialization without sort_keys loses determinism, regex group indexing off-by-one returns wrong substring). For infrastructure features like tool categorization, mutation test coverage validates that the implementation is not just correct, but stable under code changes.
  impact: Test Breaker created 30 mutation tests covering: inverted conditions (category validation), off-by-one errors (regex group indexing), exception handling (ValueError vs. TypeError), and JSON serialization (sort_keys=True vs. omitted). Each mutation directly targets a code pattern likely to regress. This gave Implementation high confidence that the delivered functions are correct and stable.
  prevention: For deterministic or cryptographic-style functions (parsing, serialization, filtering), require mutation test coverage of: (1) boolean inversion (if cond: → if not cond:), (2) off-by-one in indexing, (3) exception type changes, (4) JSON/serialization parameter omission, (5) operator swaps (AND ↔ OR). This is especially valuable for infrastructure code that will be reused by many agents.
  severity: medium

- category: performance
  insight: Stress tests with large schemas (1000+ tools, 10MB+) and concurrent access patterns validated that tool categorization overhead is acceptable (<10ms per call, <100ms per measurement). These tests should be run before declaring a feature "complete" to avoid discovering performance issues in production agent runs.
  impact: Stress test suite (20 tests) verified: 1000-tool schema filtering in <50ms, deterministic measurements across 100 iterations, no race conditions under parallel access (10 threads), floating-point precision stability. This gave Implementation and Gatekeeper confidence that the feature won't become a bottleneck in agent workflows.
  prevention: For any feature that processes collections, filters data, or does serialization, require stress test suite with: (1) large dataset (10x or 100x typical size), (2) repeated operations (determinism check), (3) concurrent access (thread safety), (4) performance assertions (<X ms per AC/NFR). Include stress tests in the Test Designer baseline, not deferred to late stages.
  severity: low

### Anti-Patterns
- description: SDK/framework dependencies stated as assumptions without explicit escalation or fallback mechanism. "Use agent SDK's tool filtering mechanism" assumes SDK has the feature, but doesn't define what happens if SDK doesn't expose it.
  detection_signal: Spec mentions an external dependency (SDK, framework) without defining what the contract is if that dependency doesn't exist. No fallback or mitigation documented.
  prevention: When specifying a feature that depends on external capability, state the assumption with confidence level. Define what the feature must do (contract), separate from how the SDK might enable it (mechanism). Document fallback: if SDK doesn't support filtering, can we filter at a different layer (middleware, framework wrapper)?

- description: Acceptance Criteria Gatekeeper escalates incomplete ACs without cross-referencing execution plan. If execution plan explicitly defers work to later tasks, escalation is unnecessary.
  detection_signal: Gatekeeper marks ACs incomplete; on review, execution plan clearly shows these ACs in downstream task scope with documented reasoning.
  prevention: Gatekeeper should always check execution plan and spec design decisions before escalating. "This AC is incomplete in this ticket" only escalates if it blocks this ticket's success criteria. "This AC is deferred per plan to task X" is not an escalation—it's the intended workflow.

- description: Spec finalizes without explicitly documenting implicit constraints and assumptions. Config field names, enum values, and function behaviors often have unstated requirements (field optionality, tool naming rules, parsing strictness).
  detection_signal: Test suite creates "spec gap" test class and identifies 5+ assumptions not in spec prose. Implementation must make design decisions about these gaps (strict vs. lenient parsing, etc.).
  prevention: Add Implicit Constraints review to Spec completion checklist. For each config field, function parameter, and enum, explicitly document: is this required? what values are allowed? what happens on invalid input? Gaps should be resolved in spec, not deferred to implementation.

### Prompt Patches
- agent: Spec Agent
  change: "For features with external dependencies (SDK capabilities, framework internals), document assumptions with confidence levels in Clarifying Questions section. Define the feature contract (function signature, error handling) independent of SDK mechanism. Explicitly defer framework-integration tasks to downstream agents (Integration Agent) with a clear handoff contract."
  reason: Separates specification from implementation concerns and prevents speculation about SDK internals from blocking backend work. Allows backend to complete and be testable while framework integration is coordinated separately.

- agent: Spec Agent
  change: "Before finalizing spec, create an Implicit Constraints section. For each config field, function parameter, and behavior, explicitly state: required/optional, allowed values, handling of invalid input. Identify gaps that don't have clear answers and call them out for Test Designer to verify via spec-gap tests."
  reason: Moves unstated assumptions into explicit documentation and ensures implementation doesn't have to guess about constraints. Test Designer can then verify these constraints are enforced.

- agent: Acceptance Criteria Gatekeeper Agent
  change: "Before escalating incomplete ACs, cross-reference the execution plan to confirm whether deferral is intentional and documented. Mark as 'Deferred (intentional, Task X)' rather than 'Incomplete (blocker)' when execution plan explicitly scopes that AC to a downstream task. Only escalate if the deferral blocks this ticket's primary success criteria."
  reason: Prevents unnecessary escalations when partial AC satisfaction is correct per design. Distinguishes between "incomplete by accident" (escalate) and "incomplete by design" (proceed).

- agent: Test Designer Agent
  change: "Create a spec-gap test class dedicated to documenting unstated assumptions and implicit constraints in the spec. For each assumption found, create a test that would fail if the assumption is violated (e.g., if version field is assumed required, test fails when it's missing). Document each gap with a recommendation for spec clarification."
  reason: Surfaces spec ambiguities early and ensures implementation decisions about these gaps are made consciously rather than by accident.

### Workflow Improvements
- issue: Features with uncertain SDK/framework dependencies block backend implementation waiting for framework coordination. "Can the SDK filter tools?" is a yes/no question but blocks work while it's being clarified.
  improvement: In SPEC, document the assumption and define the contract. Defer framework integration to a separate task with clear handoff criteria. Allow backend implementation to proceed on schedule with full test coverage and mocks for the framework layer.
  expected_benefit: Backend work is unblocked; framework integration is a parallel or sequential task with a clear contract rather than a blocker.

- issue: Execution plan task breakdown and sequencing is not visible to Gatekeeper, leading to false escalations of incomplete ACs.
  improvement: Require Gatekeeper to review execution plan before escalating. Include explicit deferral language in execution plan (e.g., "Task 4: Backend only; Task 5: Framework integration; Task 7: Live agent testing and runbook"). Gatekeeper should verify ticket success criteria are met in this phase before escalating.
  expected_benefit: Reduces noise in escalations and clarifies which ACs belong to which task.

- issue: Spec gaps (implicit constraints, unstated requirements) are discovered late by test suites and must be resolved by implementation via trial-and-error.
  improvement: Move spec-gap discovery to test design phase. Test Designer creates spec-gap tests for each assumption. Spec Agent reviews and documents findings. Spec is finalized with explicit coverage of implicit constraints.
  expected_benefit: Implementation has clear spec requirements and doesn't need to make assumption-based design decisions.

### Keep / Reinforce
- practice: Explicit assumption documentation in Spec Clarifying Questions, with confidence levels for each assumption. This allows downstream agents to understand what's certain vs. uncertain.
  reason: M902-18 Spec clearly documented that SDK tool filtering was an assumption and would be verified/adapted in framework integration task. This prevented over-specification and allowed backend to proceed.

- practice: Decoupled backend implementation (Tool Category Manager) from framework integration (agent framework modification). Clear function contracts and isolated test suites allowed backend to complete independently.
  reason: 180 tests passing and backend complete on schedule, even though framework integration was uncertain. This is an efficient workflow: build what you can, defer what you can't.

- practice: Comprehensive mutation and stress test suites for infrastructure features like tool categorization. These tests validated determinism, performance, and stability under edge cases.
  reason: Gave high confidence that the delivered tool_category_manager.py is correct, efficient, and thread-safe. Implementation teams can depend on this module without worrying about subtle bugs under load.

---

## [M902-09] — Bare Exception Handlers Must Be Replaced with Explicit Types; Timing-Sensitive Tests Require System Load Tolerance
*Completed: 2026-05-18*

### Learnings

- **category: architecture**
  **insight:** Bare `except Exception` clauses in critical paths mask the root cause of errors and prevent meaningful error propagation. In subprocess-based infrastructure, expected exceptions must be caught explicitly so unexpected exceptions propagate correctly.
  **impact:** Implementation had 2 bare `except Exception` blocks in `_is_formatting_only_file` (line 205) and `_get_staged_files` (line 262). Security review required replacing with explicit `(OSError, subprocess.CalledProcessError, ValueError)`. This pattern was correct but went undetected initially, meaning code review didn't flag it as a finding during initial implementation—only during security-focused review.
  **prevention:** Infrastructure agents and code reviewers must audit subprocess/shell-integration modules specifically for bare exception handlers. Add to pre-commit hook: flag any `except Exception` in `ci/scripts/gates/*.py` and `ci/scripts/*.py` as a finding. Document the policy: "infrastructure modules must catch specific exception types only."
  **severity:** high

- **category: testing**
  **insight:** Performance timing thresholds in tests must account for system load variance. A 500ms threshold is ambiguous on shared/CI systems where CPU contention can cause legitimate variance.
  **impact:** Test `test_nfr_performance_completes_in_under_500ms` failed intermittently when system load was high (500–600ms executions vs. 500ms threshold). This was not a code bug but a timing assumption that was too strict. Fix: raised threshold to 1000ms and renamed test to clarify intent.
  **prevention:** Timing-sensitive tests should document their environment assumptions (expected system load, CPU availability). For CI environments, use percentile thresholds (e.g., "p95 latency < 1000ms") rather than hard limits. Alternatively, measure on current system and add a margin (e.g., 2x baseline). Test name should reflect whether threshold is advisory or hard requirement.
  **severity:** medium

- **category: process**
  **insight:** Test infrastructure bugs (mkdir on existing directories, missing parent paths) can coexist with implementation bugs and should be caught early by running tests in a clean environment before marking implementation COMPLETE.
  **impact:** 5 of 105 tests failed on first integration run: 2 mkdir idempotence issues in adversarial tests, 3 logic bugs in behavioral tests. These were caught by Test Breaker (who adds adversarial coverage), but marked as "pre-existing test infrastructure bugs" rather than being escalated immediately. However, marking implementation COMPLETE with 5 failing tests triggered AC Gatekeeper escalation and held ticket in INTEGRATION, requiring a second fix cycle.
  **prevention:** Implementation Agent should run full test suite (behavioral + adversarial) in a clean shell environment before marking COMPLETE. If any tests fail, categorize them: is this a code bug or test bug? Do not claim COMPLETE if unresolved test failures exist. If test bugs are discovered, fix them in the implementation checkpoint and re-run before updating ticket status.
  **severity:** high

### Anti-Patterns

1. **Bare exception handlers in infrastructure modules:** `except Exception` in subprocess/git integration paths allows errors to be silently swallowed. Root cause is obscured.

2. **Timing thresholds without margin:** Hard timing limits (e.g., "< 500ms") in performance tests without accounting for system variance. Should use "< X ms on typical CI environment" with documented assumptions or percentile targets.

3. **Test failures marked as "infrastructure bugs" without immediate escalation:** When a test fails, determine root cause immediately. Don't defer categorization to later. If test bugs exist, fix them before marking ticket COMPLETE.

4. **Isolated test runs:** Running only behavioral tests or only adversarial tests in isolation. Full suite (behavioral + adversarial) should be run together to catch interaction bugs.

### Prompt Patches

- **agent: Implementation Agent (M902 gates and infrastructure)**
  **change:** "After implementation is complete, run the full test suite (both behavioral and adversarial tests) in a clean environment. If any tests fail, immediately investigate: is this a code bug or a test infrastructure bug? Do not mark Stage COMPLETE with failing tests. If test bugs are found, fix them and re-run. Failing tests = unresolved issues that will be escalated by AC Gatekeeper."
  **reason:** Prevents discovering test failures during AC Gatekeeper review. Ensures all issues are resolved before claiming completion. Reduces rework cycles.

- **agent: Code Reviewer (GDScript / Python security review)**
  **change:** "For modules under `ci/scripts/gates/` and `ci/scripts/`, specifically audit subprocess and shell-integration functions for bare `except Exception` blocks. Require explicit exception types `(OSError, subprocess.CalledProcessError, ValueError, TimeoutError, FileNotFoundError)` or similar. Bare exceptions in infrastructure are HIGH-priority findings."
  **reason:** Subprocess error handling is a common source of silent failures. Explicit types ensure meaningful error propagation. Infrastructure modules must be reliable.

- **agent: Test Designer (Performance tests)**
  **change:** "For timing-sensitive tests (performance, latency, responsiveness), document the measurement conditions: expected system load, CPU availability, warm/cold caches. Set thresholds with margin: measured baseline + 50% = threshold, or use percentile language ('p95 < 1000ms'). Test name should reflect whether threshold is hard requirement or advisory (e.g., test_perf_completes_in_reasonable_time_1000ms or test_perf_sla_required_under_500ms)."
  **reason:** Timing tests are often flaky on shared systems. Margin prevents false failures. Clear naming prevents misinterpretation of thresholds.

### Workflow Improvements

- **issue:** Test failures discovered during AC Gatekeeper review create a second rework cycle (Gatekeeper escalates, Implementation/Test Breaker fixes, Gatekeeper re-reviews). This delays completion.
  **improvement:** Require Implementation Agent to run full test suite before marking COMPLETE. If failures exist, fix them immediately. Only mark COMPLETE when all tests pass. Document test execution results in implementation checkpoint.
  **expected_benefit:** Eliminates second rework cycle. AC Gatekeeper can focus on spec compliance rather than test execution validation.

- **issue:** Bare exception handlers in infrastructure are a recurring pattern (this ticket, others). Code review doesn't always catch them without specific focus.
  **improvement:** Add linting rule or pre-commit hook: `grep -r "except Exception:" ci/scripts/gates/ ci/scripts/` and fail the hook if found. Require explicit exception types in these modules.
  **expected_benefit:** Prevents silent failures and improves observability of infrastructure module errors.

### Keep / Reinforce

- **practice:** Comprehensive adversarial test suite (mutation, boundary, stress, concurrency, determinism, error handling, assumption validation, type/schema validation) for infrastructure modules. Test Breaker adds 50+ adversarial tests that catch subtle implementation bugs.
  **reason:** M902-09's adversarial suite caught concurrency race conditions and file descriptor leaks that basic tests missed. This is a high-value investment for infrastructure.

- **practice:** Clear test naming conventions (behavior-driven, no ticket IDs) and organized test classes (one per requirement). Makes tests discoverable and maintainable.
  **reason:** 105 tests across 2 files, all organized and named clearly, making it easy to locate specific coverage and understand what each test validates.

- **practice:** Real git fixtures (not mocks) for diff classification testing. Tests use actual git repos and subprocess calls to validate real behavior.
  **reason:** Caught actual git integration bugs (path normalization, subprocess output parsing) that mocks would have missed.

---

## M902-10 — Error handling distinction in graceful degradation vs. hard failures

*Completed: 2026-05-19*

### Learnings

1. **Error category distinction is critical in gate implementation:** The spec defined three error categories (formatter unavailable = WARN/skip, formatter failed = FAIL, git failed = FAIL), but the implementation must distinguish between them at the subprocess level. The test suite (adversarial tests) revealed that simply checking `if "not found" in error_msg.lower()` is insufficient for reliable detection. Formatters may output error messages in different formats (FileNotFoundError exception vs. OSError vs. returncode != 0 with stderr). The implementation uses exception type matching (`OSError, FileNotFoundError` in try/except) to reliably distinguish unavailable formatters from failures.
   **impact:** Without clear error category boundaries, the gate could misclassify a missing formatter (graceful degrade) as a formatter error (hard fail), blocking users unnecessarily. Mutation tests specifically checked that inverted error checks would cause this bug.
   **severity:** high

2. **Git diff parsing must handle two formats: name-only and unified diff:** Initial assumption was that `git diff --name-only` returns only filenames. However, when testing with output parsing, the implementation discovered that if `--name-only` is omitted, git returns unified diff format (lines starting with `---` and `+++`). The implementation's `_detect_formatting_changes()` function includes fallback parsing logic to handle both formats (e.g., extracting filenames from `--- a/path` and `+++ b/path` prefixes). Adversarial tests with malformed git output caught this edge case.
   **impact:** Without dual-format parsing, the change detection logic would fail on unexpected git output formats, causing false negatives (missing detection of formatting changes) or exceptions.
   **severity:** medium

3. **Duration tracking must use max(1, ...):** Initial implementation calculated `duration_ms = int((time.time() - start_time) * 1000)`, which can produce 0 on very fast runs. The spec and adversarial tests require `duration_ms > 0` (timestamp milliseconds must always have a value). Boundary tests caught this: fast operations completed in <1ms. Fixed by using `max(1, int(...))` to ensure minimum 1ms.
   **impact:** Zero-duration gates confuse downstream consumers and violate the schema contract. Boundary and schema validation tests caught this.
   **severity:** low

4. **Message formatting for mixed formatter scenarios requires consistent delimiters:** The `_format_message()` function handles cases where some formatters apply and others are unavailable. Test vectors (TV-15, TV-18) required different message templates: "Re-staged for review" when changes detected, vs. separate formatting for applied/unavailable formatters. Initial implementation used inconsistent delimiters (comma vs. semicolon). Spec-driven tests validated exact message text for determinism. This matters because downstream tools may parse these messages.
   **impact:** Inconsistent message formatting makes parsing unreliable for automation. Tests that checked exact message text caught this.
   **severity:** low

5. **Graceful degradation: WARN violations should still result in PASS status when no formatters fail:** The spec clearly stated "non-blocking errors must record WARN violations but return PASS." Initial assumption was that if any formatter is unavailable, return FAIL. Mutation tests specifically inverted this: `if all_formatters_unavailable: return FAIL` was the bug caught. The correct behavior is: unavailable formatters produce WARN violations, but gate still returns PASS. The implementation now correctly checks `if not success and "not found" in error: skip and warn; otherwise fail`.
   **impact:** Misclassifying "formatter unavailable" as a blocker (FAIL) would break legitimate workflows where users have only some formatters installed. Mutation tests caught this inversion bug.
   **severity:** high

### Anti-Patterns

1. **String-based error classification (e.g., `"not found" in error_msg.lower()`) is fragile:** Formatters output errors in different locales and formats. Exception type matching (OSError, FileNotFoundError) is more reliable. String-based error detection relies on exact message content, which varies by OS and formatter version.

2. **Assuming git diff output format is static:** Different git options (--name-only, unified, stat) produce different formats. Code that parses git output should handle multiple formats or explicitly validate the format.

3. **Skipping minimum value validation in timing calculations:** Times that can be zero (fast operations) require explicit `max(1, ...)` guards. This is easy to miss in code review but catches boundary conditions.

4. **Message templates without version/format control:** If downstream tools parse gate output messages, format changes can break parsing. Better to have structured fields (violations array, flags) than to rely on message text.

### Prompt Patches

- **agent: Implementation Agent (infrastructure gates)**
  **change:** "When implementing error handling in subprocess-based gates, distinguish errors by exception type (OSError, FileNotFoundError, subprocess.TimeoutExpired, etc.) rather than string matching on error messages. Errors messages vary by OS, locale, and tool version. Document the three categories: (1) tool unavailable = graceful skip + WARN, (2) tool failed = hard FAIL, (3) git/env error = hard FAIL. Implement each with explicit exception matching and separate code paths."
  **reason:** Exception type is deterministic; error messages are fragile. Prevents misclassification of missing tools as failures, avoiding false blocking of users.

- **agent: Test Designer (formatting/linting gates)**
  **change:** "For gates that parse tool output (git diff, formatter stderr), include adversarial tests that feed multiple output formats: well-formed, malformed whitespace, alternate formats (git unified vs. name-only), locale-specific error messages, non-UTF8 characters. Verify the parser handles format variation gracefully or fails explicitly (not crash)."
  **reason:** Tool output varies. Parsers must be robust to variation or fail fast with clear errors. Malformed output tests reveal fragility.

- **agent: Test Designer (timing/performance tests)**
  **change:** "For any duration or timing metric calculated from elapsed time, explicitly test the boundary case: very fast operations (< 1ms). Verify minimum thresholds (duration_ms >= 1, latency > 0, etc.) are enforced. Use assertions like `assert result['duration_ms'] >= 1` to catch zero-value bugs."
  **reason:** Fast operations complete in microseconds; rounding to milliseconds can produce zero. Schema contracts often require positive values. Boundary tests catch this.

### Workflow Improvements

- **issue:** The gap between what the spec says ("error category") and what the implementation does (try/except or string matching) isn't validated until test execution. String-based error detection is a common pitfall.
  **improvement:** In Spec Agent output, add an "Implementation Checkpoints" section that defines how each error category will be detected at code level: "Category 1 (unavailable) will be caught by `except FileNotFoundError` and `except OSError`; Category 2 (failed) will be caught by `returncode != 0`; etc." Implementation Agent must follow this and code reviewer validates alignment.
  **expected_benefit:** Bridges the spec-to-code gap. Reduces surprises when tests run. Makes error handling explicit and reviewable.

- **issue:** Mutation tests caught the "inverted graceful degradation" bug (if unavailable: fail instead of skip), but this is easy to introduce in future gates.
  **improvement:** Add a mutation test template to the Test Breaker toolkit: "For each graceful degradation path in spec, include a mutation test that inverts the condition and verifies the test suite catches it." Document this as a standard pattern for infrastructure gates.
  **expected_benefit:** Ensures graceful degradation logic is tested consistently across M902-11, M902-12, etc.

### Keep / Reinforce

- **practice:** Three-category error handling framework (unavailable, failed, env-failed) with distinct code paths and WARN/FAIL outcomes. Clear, auditable, testable. Prevents logic bugs where categories bleed into one another.
  **reason:** This structure, combined with mutation tests that invert each category, creates high confidence in error path correctness.

- **practice:** Comprehensive adversarial test suite with 100+ test cases including mutation tests specifically designed to catch inverted conditions, omitted operations, and wrong return values. The mutation tests in M902-10 caught real bugs (graceful degradation, git diff parsing, duration rounding).
  **reason:** Mutation testing is not just a validation technique; it's a design tool. It forces implementation to be explicit about decision points.

- **practice:** Separation of concerns in helper functions (`_run_formatter()`, `_detect_formatting_changes()`, `_git_add_files()`) with clear return contracts (`(success, error_msg) -> tuple`). Makes error handling testable in isolation.
  **reason:** Each helper is tested independently (unit) and integrated (integration). Errors in helpers are caught by both levels.

---

## M902-11 — Architecture Enforcement Gate: Mock Stubs vs. Real Invocation

*Completed: 2026-05-19*

### Major Rework Event

**Initial state:** Implementation provided mock stubs for all five tool functions, returning empty lists. Tests passed (51 behavioral + 29 adversarial), but AC-1 through AC-7 (tool invocation and violation detection) were not satisfied.

**Trigger:** AC Gatekeeper review flagged tool invocation as "not implemented" after implementation claimed Stage `IMPLEMENTATION_BACKEND_COMPLETE`.

**Root cause:** Implementation intentionally provided mocks "for test isolation" (per initial code comments), believing test coverage was sufficient. However, the spec (Requirement 03) explicitly listed tool invocation as in-scope ("Tool orchestration and invocation only"). The implementation interpreted "test isolation" as "defer tool invocation," but acceptance criteria required real invocation.

**Rework:** Replaced mock stubs with real subprocess calls, including:
- Created `_invoke_tool()` helper (lines 45–84) for standard subprocess handling
- All five tool functions now invoke subprocess with proper timeouts, error handling, and output parsing
- Added exception handling: TimeoutExpired → TOOL_TIMEOUT, FileNotFoundError → TOOL_UNAVAILABLE, ValueError → TOOL_ERROR
- Fixed hardcoded `cwd="/"` to use `codebase_root` parameter throughout
- Added structured logging and error transparency (JSON parse failures now raise ValueError, not silent return)

**Impact:** 2 full development iterations required: design → initial implementation with mocks → AC review rejection → redesign and real implementation → acceptance.

### Engineering Insights

1. **Mock stubs for "test isolation" are insufficient for infrastructure gates:** The implementation assumed "we'll mock the tools to isolate the test suite from external dependencies." However, isolation ≠ completion. If the spec says tool invocation is required, then tool invocation code must be present even if mocked by the test suite. The correct pattern is: (1) implement real tool invocation, (2) provide mocks in test setup (`unittest.mock.patch` at test time), not in the implementation code itself. Placing mocks in the implementation creates ambiguity: is the mock temporary or intentional? This led to AC-1 being marked "not implemented" despite 80 passing tests.
   **severity:** high
   **prevention:** Implementation agent must distinguish between (a) deferred scope (AC explicitly deferred to M903) vs. (b) test isolation (mock in tests, not in code). Provide real implementations even if tests override them. Review must check for "# Mocked for testing" comments in submitted code.

2. **Hardcoded `cwd="/"` breaks real deployments:** Initial implementation called all tools with `cwd="/"`, which fails when tools need to find configuration files relative to the codebase root (e.g., `.import-linter`, `.semgrep.yml`). This was caught by code review, not tests, because the mocked functions never actually invoked subprocess. The fix: accept `codebase_root` parameter and pass to all tool functions.
   **severity:** high
   **prevention:** Code review checklist: "If code invokes subprocess, verify cwd is configurable (not hardcoded). Tools often need to find config/source files relative to project root." Pre-commit hook could validate this: `grep -n 'cwd="/"' ci/scripts/gates/*.py`.

3. **Code duplication in tool invocation requires a helper function early:** Initial implementation (after rework) had five separate try/except blocks with identical TimeoutExpired/FileNotFoundError handling, creating duplication and maintenance burden. This was a "fix Issue #3" during gatekeeper feedback. The correct pattern: extract `_invoke_tool(tool_name, args, timeout, cwd)` helper immediately when multiple tool invocations are planned. Tests should mock this helper, not individual tool functions.
   **severity:** medium
   **prevention:** When spec requires orchestrating multiple subprocess calls, implement helper function first. Avoid writing tool function with try/except, then realizing it needs to be duplicated five times.

4. **Silent JSON parse failures make debugging impossible:** Initial implementation called `json.loads()` but had no exception handling. If a tool returned malformed JSON (due to tool failure, version mismatch, or environment issue), the gate would crash or silently return empty list. Code review required explicit ValueError raising with output preview: `logger.error(..., result.stdout[:500])`. This preserves observability.
   **severity:** high
   **prevention:** For any external tool invocation that parses structured output (JSON, XML, etc.), wrap the parse call in try/except, raise ValueError with the first N bytes of output in the error message. This allows downstream debugging without rerunning the gate.

5. **Bare except Exception clauses require explicit justification per code_governance.md:** The `_collect_violations()` function has a catch-all exception handler to record tool errors as violations (preventing cascading failures). Code review flagged this as a bare except violation. Fix: add detailed comment explaining why broad catch is necessary: tool functions are plugin-like; unexpected exceptions must be recorded, not crash the gate. All exceptions logged with traceback (`exc_info=True`).
   **severity:** medium
   **prevention:** Whenever a broad exception catch is necessary (plugin interface, infrastructure resilience), document the specific exception types handled and the reason for broad catch scope. This satisfies code_governance.md "No bare except clauses" rule.

### Anti-Patterns

1. **"Mock for test isolation" in implementation code:** Placing `# Mocked for testing; real implementation would invoke subprocess` in the implementation itself creates false signal about completion. Tests should use `unittest.mock.patch` to override real implementations, not rely on placeholder code. Signals: comments saying "mocked," functions returning hardcoded test data, `TODO`/`FIXME` for real implementation.

2. **Hardcoding infrastructure constants (cwd, paths, timeouts):** Subprocess invocations often hardcode `cwd="."` or `cwd="/"` without parameterization. This breaks when tools need different working directories. Parameterize from the start: `cwd: str` function parameter, passed from caller.

3. **Skipping exception handling for "simple" subprocess calls:** Subprocess calls can fail in multiple ways (tool not found, timeout, output parsing, permissions). Assuming "it won't fail" or "tests will catch it" leads to missing error paths in real deployments. Comprehensive exception handling is infrastructure code, not optional.

4. **JSON/XML parsing without error context:** When tool output is malformed, logging just the exception type is insufficient. Include the first N bytes of the output (e.g., `result.stdout[:500]`) in the error message for debugging.

### Prompt Patches

- **agent: Implementation Agent (infrastructure / gate modules)**
  **change:** "When implementing tool orchestration (multiple subprocess calls to external tools), follow this checklist: (1) Create a `_invoke_tool()` helper with standard error handling (TimeoutExpired, FileNotFoundError, CalledProcessError). (2) All tool functions accept `codebase_root` parameter and pass to _invoke_tool. (3) For structured output (JSON, XML), wrap parse in try/except, raise ValueError with first 500 bytes of output. (4) Broad exception catch in orchestrator (e.g., _collect_violations) requires explicit comment explaining plugin interface resilience. (5) Do NOT place 'mocked for testing' comments in implementation code; move mocks to test setup (unittest.mock.patch). Mocks in the implementation signal incomplete work to reviewers."
  **reason:** Tool orchestration has recurring pitfalls (hardcoded paths, missing error handling, duplicate code). Checklist prevents oversight and clarifies that test isolation happens in test code, not implementation code.

- **agent: Code Review Agent**
  **change:** "For infrastructure modules invoking subprocess or external tools, verify: (1) Working directory is configurable (not hardcoded). (2) All exception types are explicit (no bare except Exception without comment). (3) For JSON/XML parsing, confirm ValueError is raised with output preview. (4) Implementation code has no comments like 'mocked for testing'; those belong in tests. (5) Exception comments justify broad catches per code_governance.md. If any check fails, request changes before approval."
  **reason:** Subprocess and parsing errors are common in infrastructure code and easy to miss in initial review. Explicit checklist reduces rework cycles.

- **agent: Test Designer (infrastructure gates)**
  **change:** "When designing tests for tool orchestration gates, mock individual tool functions via unittest.mock.patch, not by accepting placeholder implementations. Use assertions like `assert mock_tool.called_with(...)` to verify invocation happened with correct arguments. This validates the orchestrator logic without depending on the tool functions being mocked in the implementation code itself. Test naming should be behavior-driven (e.g., `test_collect_violations_retries_on_timeout`, not `test_mock_functions`)."
  **reason:** Mocks in test code are explicit; mocks in implementation code signal incomplete work. Separating these concerns clarifies what's done vs. what's deferred."

### Workflow Improvements

- **issue:** AC Gatekeeper review discovered tool invocation was not implemented (despite 80 passing tests), leading to a full rework cycle. This was caught at AC review stage, late in the workflow.
  **improvement:** **Precursor check before IMPLEMENTATION_BACKEND_COMPLETE:** Implementation agent runs a "presence check" that verifies required functions/modules actually do their work (not just mocks). For tool orchestration: verify _invoke_tool is called from each tool function, not just present in the file. Use a simple grep/regex check: `grep -n "_invoke_tool\|subprocess\|popen" ci/scripts/gates/architecture_enforcement_check.py` and require at least 5 matches for 5 tools. Checkpoint this as "tool invocation presence: VERIFIED."
  **expected_benefit:** Catches "mocked for testing" implementations before AC review, moving feedback earlier to implementation stage instead of AC stage.

- **issue:** Multiple rework cycles (initial implementation with mocks → AC gatekeeper feedback → rework with real invocation → code review with 4 blocking issues → fixes). Each cycle added 2-4 hours.
  **improvement:** Create a "Tool Orchestration Gate Checklist" that Implementation Agent must complete and sign off on before marking IMPLEMENTATION_BACKEND_COMPLETE. Checklist includes: (1) _invoke_tool helper exists, (2) all tool functions call it with codebase_root parameter, (3) exception handling covers TimeoutExpired, FileNotFoundError, ValueError, and broad catch, (4) output parsing includes error context, (5) cwd is not hardcoded. This can be automated as a pre-submission linting check.
  **expected_benefit:** Reduces rework cycles by catching infrastructure issues at implementation stage, before tests are finalized.

### Keep / Reinforce

- **practice:** Comprehensive exception handling with structured logging (tool name, error type, output preview) in infrastructure modules. This makes production failures debuggable.
  **reason:** When a gate fails in CI, having clear logs (tool name, timeout value, stderr/stdout preview) allows diagnosis without re-running the gate. M902-11's final implementation logs all this.

- **practice:** Parameterization of infrastructure constants (cwd, timeouts, config paths) instead of hardcoding. All tool functions accept codebase_root and pass to subprocess invocation.
  **reason:** Enables real-world use in CI/CD pipelines where project root may not be the process cwd.

- **practice:** Multi-stage tool orchestration with deduplication and scoring across tools. M902-11 aggregates violations from five tools, deduplicates by (file, line, rule_id), and computes risk/architecture scores. This is more maintainable than merging results ad-hoc.
  **reason:** Consistent aggregation logic across gates (M902-09, M902-10, M902-11) reduces duplication and improves reliability.

---

## [M902-13] — Adversarial Test Design Catches Boundary Conditions Before Implementation
*Completed: 2026-05-19*

### Critical Learning

**Adversarial testing (boundary conditions, edge cases, stress scenarios) designed and executed *before* implementation successfully identified potential off-by-one bugs, infinite-loop risks, and schema robustness issues that would have surfaced in real deployments.** M902-13's adversarial suite (37 tests across 10 dimensions) caught 9 distinct vulnerability categories, all of which were prevented by the test-first discipline.

### Learnings

- **category: testing**
  **insight:** Boundary condition tests encode assumption clarity. Tests like "99KB passes, 100KB fails" force the specification to commit to exact semantics (< 100000 bytes, not <= 100000). Ambiguous specs become obvious when writing boundary tests.
  **impact:** Test Breaker's adversarial suite caught that the spec used strict <100000 (not <=100000) by encoding 99KB as PASS and 100KB as requiring truncation. This ensured implementation enforced the exact boundary, preventing silent off-by-one bugs that would fail in production with bundles right at the limit.
  **prevention:** For any infrastructure gate with hard limits (size, depth, line count, timeout), write boundary tests *before* implementation. Example: "test_exactly_at_boundary (should pass)" and "test_one_byte_over_boundary (should truncate)". This forces the spec and implementation into explicit agreement.
  **severity:** high

- **category: architecture**
  **insight:** Cycle detection (graph traversal with visited set) requires test validation for specific failure patterns (simple A→B→A, deep cycles A→B→C→D→A). Absence of visited set in traversal does not fail obvious cases; it fails specific topologies that exceed depth limits or have large cycle lengths.
  **impact:** Adversarial tests included `test_circular_import_loop_ab_ba_no_infinite_loop` and `test_circular_import_deep_loop_abcda_cycle_at_depth_3` with 5s timeout. These caught the specific risk that naive DFS without visited set would loop infinitely on A→B→A (simple cycle) or exhaust the 2-hop depth limit if the cycle was longer. Implementation correctly used visited set from the start because tests defined the expected behavior.
  **prevention:** When implementing graph traversal with cycles, write adversarial tests for: (1) simple back-edge (A→B→A), (2) deep cycle (chain of 4+ nodes looping), (3) depth limit enforcement (A→B→C→D should truncate at depth 2). These tests clarify whether cycle detection is done via visited set, depth counter, or both.
  **severity:** high

- **category: testing**
  **insight:** Fallback strategies (e.g., CODEOWNERS missing → use directory heuristic) require exhaustive edge case testing: missing file, malformed syntax, empty content. A single "test CODEOWNERS missing" test is insufficient; each failure mode may trigger different code paths.
  **impact:** Adversarial tests included three separate CODEOWNERS tests: missing file, malformed syntax, empty file. This ensured the fallback was triggered by all three conditions. Implementation correctly checked for all three (file doesn't exist, parse error, content empty) and fell back accordingly. Without these granular tests, a single missing file test might pass while malformed syntax was silently accepted or ignored.
  **prevention:** For any fallback strategy: enumerate all failure modes of the primary strategy (missing, malformed, empty, wrong permission, timeout), write separate tests for each, and validate that fallback is triggered for all modes. Do not consolidate into a single "primary fails" test.
  **severity:** medium

- **category: performance**
  **insight:** Stress tests with realistic data (100 files, 1000 import edges, 1000 violations) executed *before* implementation establish a performance baseline and catch potential timeout risks. A <5s SLA requires testing at scale, not on toy examples.
  **impact:** Adversarial tests included `test_performance_100_files_1000_import_edges_under_5s` and `test_performance_1000_violations_under_5s`. These forced the implementation to optimize import graph extraction (lazy traversal, visited set for cycle detection, early termination) and violation processing (streaming, not materializing all violations). Implementation passed these tests, confirming <5s execution on large changes.
  **prevention:** For gates with performance SLAs, write stress tests using realistic data volumes *before* implementation. Use these tests to establish a baseline and detect regressions during code review. Include tests with 10x, 100x, 1000x nominal case sizes.
  **severity:** medium

- **category: process**
  **insight:** Checkpoint markers in adversarial tests (e.g., "Would have asked: Is 50-line limit max (<=50) or exclusive (>50)?") force specification boundary semantics into explicit assumption statements. This clarity prevents late disagreements between implementation and acceptance testing.
  **impact:** Test Breaker's checkpoint for code hunk boundaries explicitly stated: "50-line limit is max (<=50), so 51+ must truncate." Implementation matched this assumption from the start. Acceptance Criteria Gatekeeper validated the assumption was met. Without the checkpoint, ambiguity could have led to different implementations (some allowing 51 lines, some truncating).
  **prevention:** Use CHECKPOINT protocol in all adversarial test files. Mark each major assumption with: "Would have asked: [question] → Assumption made: [decision] → Confidence: [level]". This creates a validated assumption log that implementation and acceptance testing can reference.
  **severity:** low

### Anti-Patterns

1. **"Skip boundary tests because implementation is simple":** Common pitfall: "size limits are straightforward, so no need for 99KB/100KB/101KB tests." In practice, off-by-one boundaries are the *most* common source of production failures in infrastructure gates. Boundary tests are the minimum.

2. **"Single fallback test covers all modes":** Testing CODEOWNERS fallback with only "test_codeowners_missing" risks missing parsing errors or empty file scenarios. Each failure mode needs a separate test.

3. **"Stress tests run after implementation":** Performance tests written post-implementation cannot inform design decisions. Write <5s tests *before* implementation to prevent inefficient graph traversal or streaming violations.

4. **"Assumptions documented only in text":** Spec prose saying "code hunk max 50 lines" is ambiguous. Adversarial tests with explicit boundary checks (exactly_50_lines_pass, 51_lines_truncate) make the assumption unambiguous.

### Prompt Patches

- **agent: Test Breaker Agent**
  **change:** "For any infrastructure gate with hard limits (size, depth, line count, timeout), always write boundary condition tests covering: (1) exactly at limit (should pass), (2) one unit over limit (should enforce limit), (3) far over limit (stress case). Use explicit test names like `test_size_boundary_exactly_100kb_pass` and `test_size_boundary_101kb_truncate`. Include CHECKPOINT markers documenting the boundary semantic (e.g., `< 100000 bytes` not `<= 100000`)."
  **reason:** Boundary conditions are subtle but critical. Test-driven clarity prevents off-by-one bugs that surface in production. Explicit test names and checkpoint assumptions make agreement between spec, tests, and implementation unambiguous.

- **agent: Implementation Agent**
  **change:** "When implementing fallback strategies (e.g., CODEOWNERS → directory heuristic), ensure tests exist for each failure mode of the primary strategy (missing, malformed, empty, permission denied, timeout). Do not assume 'one test covers all modes'; each mode may trigger different code paths. Reference adversarial test patterns in M902-13 for fallback test structure."
  **reason:** Fallback strategies are common in infrastructure gates. Each failure mode is a separate edge case requiring separate test coverage. Omitting a failure mode mode may allow a bug to persist in production.

### Keep / Reinforce

- **practice:** Adversarial test design *before* implementation establishes behavioral contracts for boundary conditions, fallback strategies, and performance SLAs. This discipline prevents late discoveries during acceptance testing.
  **reason:** M902-13's adversarial suite (37 tests, 10 dimensions) executed cleanly against implementation, with 0 failures or rework cycles. This contrasts with M902-12 (late spec contradictions discovered during implementation). Test-first design caught all edge cases upfront.

- **practice:** Checkpoint markers in adversarial tests document assumptions that would otherwise be ambiguous in spec prose. "Code hunk max 50 lines" is ambiguous; "exactly_50_lines_no_truncation, 51_lines_truncate" is unambiguous.
  **reason:** Reduces interpretation disagreements between spec, tests, and implementation. All parties reference the same test expectations.

- **practice:** Schema validation tests (required fields, field types, JSON serializability) are lightweight but high-value. M902-13's TV-29–32 tests prevented silent schema violations by asserting presence/type of 20+ bundle fields.
  **reason:** Infrastructure gates often have schema contracts with downstream consumers. Early schema validation prevents runtime failures in consumer code.

---

## [M902-14] — Specification Scope Deferral Resolves Architectural Constraints Cleanly

*Completed: 2026-05-19*

### Critical Learning

**When a specification anticipates ambiguity and explicitly defers resolution to post-implementation analysis, structured constraint documentation during implementation prevents false blockers and clarifies architectural reality.** M902-14's AC-5 location requirement appeared to conflict with git version control constraints, but the specification's explicit deferral language ("if directory structure differs, clarified post-implementation") enabled a clean resolution that satisfied intent while respecting technical constraints.

### Learnings

- **category: architecture**
  **insight:** Symbolic links to external directories (like CloudDocs) create a git security boundary that version control systems enforce automatically. Files placed beyond this boundary cannot be tracked, committed, or reviewed in CI/CD pipelines, regardless of implementation intent.
  **impact:** AC-5 requirement stated "agent implementation at `agent_context/agents/`", but `agent_context/` is a symlink to an external cloud directory. Git refuses to track files beyond symlinks for security reasons. Implementation at this location would be untraceable, untestable in CI, and unreviable. Resolution: move implementation to `ci/scripts/agents/semantic_reviewer.py` (git-trackable), which mirrors the gate wrapper pattern and satisfies the architectural intent.
  **prevention:** When specifying file locations, validate that the target directory is within the git repository boundary. Avoid symlink targets in specification requirements. Document architectural constraints (like "this directory is external" or "this is a symlink to cloud storage") in requirements that reference them.
  **severity:** high

- **category: process**
  **insight:** Specification language that anticipates ambiguity and explicitly defers resolution ("if X differs from expected, clarified post-implementation") is a legitimate design pattern, not a spec deficiency. This pattern works well when: (1) the specification documents the anticipated ambiguity, (2) implementation is checked against constraints, (3) constraint analysis is documented as a checkpoint.
  **impact:** M902-14 specification included explicit deferral language ("Agent instruction sets in `agent_context/agents/` (if directory structure differs) clarified post-implementation"). This anticipation of location ambiguity meant the post-implementation constraint analysis (symlink boundary documentation in AC5_location_constraint.md) was expected and legitimate. No spec revision was needed; only post-implementation clarification.
  **prevention:** When writing specifications for infrastructure components with potential environmental variation, use deferral language explicitly: "if [constraint differs], [decision] clarified post-implementation during [agent stage]". Document which constraint is expected to vary and which agent will resolve it. This prevents false alarms at AC Gatekeeper when the anticipated deferral occurs.
  **severity:** medium

- **category: testing**
  **insight:** Comprehensive test coverage (235 tests covering all 8 signals, decision outcomes, edge cases, determinism, performance) provides confidence that implementation logic is correct even when the implementation location differs from specification requirements. Tests validate intent, not location.
  **impact:** AC-5 location mismatch did not trigger a full rework because tests validated that the agent correctly evaluates bundles, makes decisions, and integrates with gates. Whether the module is at `agent_context/agents/semantic_reviewer.py` or `ci/scripts/agents/semantic_reviewer.py`, the behavioral contract is the same. Tests ensured intent satisfaction regardless of location.
  **prevention:** Separate acceptance criteria into: (1) behavioral AC (what the agent does), (2) structural AC (where it is located or how it is packaged). Behavioral ACs should be validated by tests; structural ACs by constraints analysis. This allows structural requirements to be reinterpreted post-implementation if constraints change, while behavioral intent remains testable.
  **severity:** medium

- **category: process**
  **insight:** AC Gatekeeper review that systematically documents architectural constraints and deferred decisions (like the symlink boundary analysis) prevents future confusion about why implementation locations differ from initial requirements.
  **impact:** AC Gatekeeper's decision checkpoint (Decision 1, page 127 of checkpoint) explicitly documents: (1) specification language anticipated the deferral, (2) git symlink boundary is a hard constraint, (3) alternate location is architecturally sound, (4) all 235 tests pass, (5) AC intent is satisfied. This documentation will inform future agents reading the AC record that the location choice was deliberate and justified, not a deviation.
  **prevention:** When accepting AC deviations due to constraints, always document in AC Gatekeeper checkpoint: (1) what constraint forced the deviation, (2) what specification language anticipated it, (3) how intent is still satisfied, (4) what evidence validates the choice. Avoid logging "AC-5 accepted as SATISFIED despite location difference" without explanation; always explain the constraint and rationale.
  **severity:** low

### Anti-Patterns

1. **"Specification requirement doesn't match reality" → immediate redesign:** When a spec requirement conflicts with technical constraints (like git version control boundaries), the impulse is to revise the spec. Better approach: check if spec anticipated the ambiguity. If it did (via explicit deferral language), constraint analysis is sufficient; no revision needed.

2. **"Move requirements to post-implementation deferral without anticipating constraints":** Adding deferral language to spec *after* discovering a conflict (vs. *before* during spec writing) signals incomplete spec review. Deferral should be intentional, not reactive.

3. **"Accept structural deviation without documenting rationale":** If AC-5 location differs, failing to document why (git boundary, symlink constraint) makes the deviation appear arbitrary to future readers. Documentation prevents the same conflict from arising in similar tickets.

### Prompt Patches

- **agent: Specification Agent**
  **change:** "When specifying file locations or directory structures for code artifacts, validate that the target is within the git repository boundary. If a directory is external (symlink, mounted, cloud-based), include explicit deferral language: 'Agent implementation in [directory] (if directory structure differs from expected, location clarified post-implementation per [stage] constraints analysis).' Document the constraint in the requirements section."
  **reason:** Prevents specification requirements from conflicting with version control constraints. Anticipatory deferral language provides legitimate scope for post-implementation clarification without requiring spec revision.

- **agent: AC Gatekeeper Agent**
  **change:** "When accepting AC deviations due to technical constraints: (1) Document the constraint in checkpoint (what external system enforces it—git, OS, CI pipeline), (2) Cite specification language that anticipated the deviation (if present), (3) Validate that implementation intent is satisfied via tests or other evidence, (4) Recommend future specifications include explicit deferral language if the constraint is environmental or system-dependent."
  **reason:** Provides traceability for why structural requirements were reinterpreted. Prevents false reports of 'spec violations' when constraints are documented and anticipated.

### Keep / Reinforce

- **practice:** Specification deferral language ("if X differs, clarified post-implementation") for anticipated ambiguities is legitimate and reduces revision cycles. Use it intentionally in specifications with environmental or system-dependent requirements.
  **reason:** M902-14's anticipatory deferral allowed clean resolution of the AC-5 location constraint without spec revision. Specification intent (agent implementation, tested, integrated) was satisfied, and constraint analysis was documented.

- **practice:** Test-driven AC validation decouples behavioral intent from structural implementation. Tests can validate "agent correctly evaluates bundles" regardless of whether the module is at `agent_context/` or `ci/scripts/`.
  **reason:** M902-14's 235 tests ensured behavioral correctness independent of location. AC Gatekeeper could confidently accept the alternate location because intent was tested and validated.

- **practice:** Comprehensive checkpoint documentation in AC Gatekeeper review (including constraint analysis, rationale, evidence) provides future traceability for why structural requirements were reinterpreted.
  **reason:** The AC5_location_constraint.md and AC Gatekeeper checkpoint decision logs explain the symlink boundary, architectural intent, and evidence. Future agents can understand why the location choice was correct without repeating the analysis.

---

## [M902-15] — Adversarial Test-Driven Specification Prevents Implementation Rework

*Completed: 2026-05-19*

### Critical Learning

**When Test Breaker systematically identifies vulnerability categories and encodes them as boundary/null-handling/type-safety tests before implementation, implementation agents encounter 0 test failures. This discipline eliminates rework cycles and accelerates delivery. M902-15 delivered 487-LOC gate implementation with 189 tests passing on first run — zero rework.**

### Learnings

- **category: testing**
  **insight:** Adversarial test design that systematically maps vulnerability categories to concrete boundary conditions (exactly_10_chars, 11_chars, 9_chars for reason length) makes implicit assumptions explicit and testable. Implementation cannot deviate from tested boundaries without test failure.
  **impact:** Test Breaker's 18 boundary mutation tests (M902-15 adversarial suite) defined exact limits: reason 10–200 chars, ticket 3–20 chars, repeated suppression threshold 3+, expiration "today" is valid. Implementation matched every boundary perfectly on first run. Zero off-by-one bugs.
  **prevention:** In all future Test Breaker runs, explicitly enumerate vulnerability categories (boundaries, null handling, type mismatches, logic consistency, scope edge cases, timestamp edge cases, concurrency/order, regex safety, file handling, schema compliance, stress) and write minimum 1 test per category per feature gate. Use explicit test names like `test_boundary_reason_exactly_10_chars_pass` and `test_boundary_reason_9_chars_fail`.
  **severity:** high

- **category: process**
  **insight:** Specification language that defers detail to "implementation clarifies" works only when Test Designer and Test Breaker encode the deferred detail as explicit test expectations. Spec said "50-line window (clarified in implementation)" → Test Breaker wrote `test_repeated_suppression_exactly_50_line_window_pass` and `test_repeated_suppression_51_lines_separate_count`. Implementation could not deviate.
  **impact:** AC-5 (repeated suppression detection) contained ambiguous scope definition in spec ("same code area = same file + 50-line window or function scope, TBD"). Test Breaker resolved the ambiguity by encoding both expectations in tests. Implementation was forced to choose and justify. Zero ambiguity at implementation time.
  **prevention:** When a specification defers a detail to "implementation clarifies", Test Breaker **must** write tests covering all plausible interpretations (both 50-line window and function scope, for example). At least one interpretation will pass; others will fail and guide implementation. This transforms ambiguous specs into test-driven clarity.
  **severity:** high

- **category: architecture**
  **insight:** Gate result schemas (JSON output contracts) should be frozen in specification and validated by tests before implementation. When audit log schema is defined in spec and validated by 8+ audit log output tests, implementation cannot produce schema violations.
  **impact:** AC-8 (audit log JSON artifact) froze schema in specification (version, timestamp, total_suppressions, total_escalations, suppressions array with file/line/rule_id/reason/ticket/expiration/first_seen/repeat_count/escalation_reasons/validation_errors fields). 8 TestAuditLogOutput tests validated schema presence, field types, ISO 8601 timestamps, determinism. Implementation generated audit logs that passed all schema tests on first run. Zero schema violations.
  **prevention:** For any gate that produces structured output (JSON, protobuf, schema-validated data), freeze the schema in specification and write at least 3 tests: (1) schema validation (required fields present, correct types), (2) determinism (same input → identical JSON), (3) field semantics (timestamps are ISO 8601, arrays are sorted, counts are accurate). These 3 tests prevent silent schema violations.
  **severity:** high

- **category: process**
  **insight:** Checkpoint protocol (recording assumptions with "Would have asked? → Assumption made? → Confidence?") creates an artifact that AC Gatekeeper can validate systematically. No ambiguity survives a checkpoint-equipped workflow.
  **impact:** M902-15 workflow included 5 checkpoint files (Planning, Specification, Test Design, Test Break, AC Gatekeeper). Each checkpoint logged decisions and confidence levels. AC Gatekeeper could validate the entire chain: (1) Planning froze 7 design decisions (all HIGH confidence), (2) Spec froze 8 assumptions and 8 risks (all mitigated), (3) Tests captured assumptions as executable conditions. Zero AC ambiguity. All 9 ACs evidenced through test coverage.
  **prevention:** All tickets should use checkpoint protocol in Planning, Specification, Test Design, and Test Break phases. Checkpoints create a validated decision trail that AC Gatekeeper can audit. Absence of checkpoints correlates with ambiguous ACs and rework.
  **severity:** medium

- **category: testing**
  **insight:** Test categories encoding frozen assumptions (TestAssumptionEncodingCheckpoints class with 6 dedicated tests) provide a validation mechanism for assumptions that would otherwise remain implicit. If implementation deviates from assumed limits, tests catch it.
  **impact:** Test Breaker created TestAssumptionEncodingCheckpoints with 6 tests encoding frozen assumptions from spec: "expiration boundary today is valid (not expired)", "threshold is 3 (not 2)", "prefixes AR-, SE-, AS-, EXH- only", "format ISO 8601 YYYY-MM-DD only", "exit code always 0", "syntax single-line comment only". These 6 tests guardrail implementation against assumption deviations.
  **prevention:** Create explicit TestAssumptionEncodingCheckpoints class in all Test Breaker test files. Mark each test with CHECKPOINT comment. For each frozen assumption in spec, write 1 test. This enforces that implementation respects all spec-frozen assumptions without debate.
  **severity:** medium

### Anti-Patterns

1. **"Spec is ambiguous about repeated suppression scope; we'll clarify during implementation":** This often leads to implementation that clarifies one interpretation, tests fail, rework needed. Better: Test Breaker writes tests for both plausible interpretations. One passes, one fails; implementation is guided by test results.

2. **"Audit log is optional; we can skip schema validation tests":** Schema violations in gates propagate silently downstream (consumer code crashes on missing field or wrong type). Schema validation tests are low cost, high value. Always include them.

3. **"Boundary testing is pedantic; we tested with valid inputs":** Off-by-one errors are the #1 source of production bugs in infrastructure gates. Boundary tests (9 vs 10 vs 11 chars) are not optional.

4. **"We'll validate assumptions during AC review":** Assumptions embedded in spec prose are harder to validate than assumptions encoded as executable tests. Encode early (Test Breaker phase), validate late (implementation phase). If assumption is wrong, test fails before implementation completes.

### Prompt Patches

- **agent: Test Breaker Agent**
  **change:** "For every infrastructure gate ticket: (1) Enumerate vulnerability categories: boundaries, null/empty handling, type mismatches, logic consistency, scope edge cases, timestamps, concurrency, regex safety, file handling, schema compliance, stress. (2) Write minimum 1 test per category per acceptance criterion. (3) Use explicit test method names like `test_[category]_[scenario]_[expected_outcome]`. (4) Create TestAssumptionEncodingCheckpoints class with 1 test per frozen spec assumption, marked with CHECKPOINT comment. (5) Document all tests in checkpoint with vulnerability_id, test_method, and expected_implementation_behavior."
  **reason:** Systematic vulnerability enumeration ensures comprehensive adversarial coverage. Explicit test names and assumption checkpoint create a traceability matrix that guides implementation and validates spec-frozen decisions."

- **agent: Specification Agent**
  **change:** "When writing specifications for infrastructure gates: (1) Freeze all output schemas (JSON, protobuf, structured logs) with exact field names, types, presence requirements. (2) For ambiguous requirements (like 'repeated suppression scope'), add note: 'Test Breaker will write tests for [interpretation A] and [interpretation B]. Implementation will be guided by test results.' (3) For all deferred details ('clarified in implementation'), note in parentheses: '(Test Breaker will encode expected behavior as executable tests; implementation must pass all tests).' This makes deferral legitimate and test-driven."
  **reason:** Schema freezing + explicit deferral language + test-driven ambiguity resolution transforms vague specifications into test-constrained specifications. Implementation cannot deviate from tested boundaries without test failure."

- **agent: AC Gatekeeper Agent**
  **change:** "When validating acceptance criteria, check for: (1) All ACs mapped to test classes in Test Designer checkpoint. (2) All frozen assumptions in spec mapped to CHECKPOINT tests in Test Breaker checkpoint. (3) All output schemas validated by schema compliance tests (required fields, field types, JSON serializability). (4) Test execution results showing 0 test failures at implementation (if failures exist, rework needed before AC validation). (5) Checkpoint files present for Planning, Specification, Test Design, Test Break phases (absence signals incomplete workflow). If any check fails, escalate to responsible agent; do not validate ACs."
  **reason:** Comprehensive AC validation requires verifying the entire workflow chain (spec → tests → implementation → validation). Checkpoint files and test results provide evidence for each link."

### Keep / Reinforce

- **practice:** Test Breaker's vulnerability category enumeration (boundaries, null/empty, type mismatch, logic consistency, scope, timestamp, concurrency, regex, file handling, schema, stress) provides a quality checklist that guides comprehensive test coverage. 97 adversarial tests covering 10 dimensions achieved 0 rework.
  **reason:** Systematic enumeration beats intuitive "write good tests". M902-15's Test Breaker explicitly categorized vulnerabilities; implementation passed all 189 tests on first run. Contrast with tickets lacking systematic categorization, which often encounter implementation surprises.

- **practice:** Explicit test method names that encode scenario + expected outcome (test_boundary_reason_9_chars_fail) create self-documenting test suites. Implementation teams reading test names understand exactly what boundary is being tested and what outcome is expected.
  **reason:** M902-15 implementation team could read `test_boundary_reason_9_chars_fail` and immediately understand: "reason with 9 characters should fail validation". No guessing about intent or expected behavior.

- **practice:** Checkpoint protocol (Would have asked? → Assumption made? → Confidence?) creates decision artifacts that survive ticket completion. Future agents reading M902-15 checkpoints can understand why 50-line window was chosen, what risks were mitigated, and what confidence level each decision achieved.
  **reason:** M902-15 completed with 5 checkpoint files documenting 7 planning decisions, 8 spec assumptions, 8 risks, and 6 assumption-encoding checkpoint tests. This artifact enables AC Gatekeeper to validate with confidence and future agents to avoid repeating analysis.

---

## [M902-16] — Frozen Planning + Detailed Specification Enables Zero-Rework Gate Implementation
*Completed: 2026-05-19*

### Critical Learning

**Comprehensive planning that freezes all ambiguities in checkpoints, paired with a detailed specification document (834 lines, 8 requirements), enabled the Implementation Agent to build a 804-line security gate with 118 tests all passing on the first implementation attempt (zero rework, zero test failures). No contradictions emerged. Planning decisions froze 8 major design choices with HIGH confidence; only 1 item (Tool Timeout Strategy) had MEDIUM confidence, and integration tests validated it.**

### Learnings

- **category: process**
  **insight:** Planning agents that produce checkpoint decisions (frozen tool selections, severity thresholds, fixture strategy, determinism requirements) reduce downstream ambiguity and rework. Planning checkpoint for M902-16 documented 8 frozen decisions with confidence levels. When Implementation Agent encountered a technical choice, the decision was already made (not re-evaluated).
  **impact:** No specification contradictions discovered during implementation (zero revision cycles). No test vector mismatches (contrast with M902-12 which required spec v1.0 → v1.1 revision after test failures). All 118 tests passed on first implementation, suggesting spec-to-test alignment was correct.
  **prevention:** Require Planning Agent to document: (1) 5+ key design decisions with explicit "Would have asked / Assumption made / Confidence", (2) Risk assessment for each medium/low-confidence item, (3) Checkpoint file saved before handoff to Spec Agent. Template in checkpoint protocol: "Decision: X, Rationale: Y, Confidence: HIGH|MEDIUM|LOW, Mitigation: Z".
  **severity:** medium

- **category: architecture**
  **insight:** Detailed specification documents (8 requirements, 834 lines, including tool configurations, severity mappings, schema examples, fixture strategy, and false-positive risk mitigation) guide implementation without ambiguity. M902-16 spec froze all tool-specific behaviors (gitleaks JSON structure, bandit severity mapping, semgrep result format, CVSS thresholds, timeout values).
  **impact:** Implementation Agent did not need to make architectural decisions; all decisions were spec-driven. Gate implementation was straightforward subprocess orchestration + JSON parsing + decision matrix, no novel patterns. Zero "what did the spec really mean?" discussions.
  **prevention:** Specification freeze gate (e.g., spec-exit-gate skill) should verify: (1) All numeric thresholds documented with units and rationale. (2) All tool configurations include example JSON input/output. (3) All schema definitions are complete (field names, types, presence). (4) Severity mappings are explicit (tool_rule_name → severity_enum with examples). (5) Failure modes documented (timeout handling, missing tool, malformed JSON, network failure if applicable).
  **severity:** medium

- **category: testing**
  **insight:** Test Designer producing 59 behavioral tests with comprehensive coverage (gitleaks, bandit, semgrep, pip-audit, npm audit, decision matrix, schema compliance, determinism, scope, error handling, edge cases) provided clear contracts. Test Breaker producing 59 adversarial tests covering 14 dimensions (timeout, subprocess failure, malformed JSON, boundary thresholds, determinism, mixed violations, mutation, extreme payloads, tool state, encoding, empty/null, concurrency, exit codes, checkpoint assumptions) left no implementation blind spots.
  **impact:** 118 tests all passing on first implementation suggests test coverage was correct and implementation understood all edge cases. No test-then-fix cycle. Contrast with tickets where tests fail during implementation (indication of spec-test misalignment).
  **prevention:** Before handoff from Test Breaker to Implementation, verify: (1) All acceptance criteria have ≥2 behavioral tests. (2) All boundary conditions have adversarial tests. (3) All error paths have tests (timeout, subprocess failure, malformed output). (4) Mutation testing covers critical operators (>= vs >, any() vs all()). (5) Determinism tests verify repeated runs → identical output. (6) Checkpoint document lists all 14 vulnerability dimensions covered with test count per dimension.
  **severity:** low

- **category: process**
  **insight:** AC Gatekeeper validation report (273 lines) that maps all 9 ACs to implementation code paths, test coverage, and objective evidence (line numbers, tool invocation examples, severity mapping examples) provides confidence that implementation is complete and correct. Evidence-driven validation (not assertion-based).
  **impact:** AC Gatekeeper concluded "All 9 ACs satisfied with explicit, objective evidence" without escalation or rework. Ticket transitioned cleanly from IMPLEMENTATION_COMPLETE → COMPLETE. No gates blocked.
  **prevention:** AC Gatekeeper template should require: (1) For each AC, cite implementation code path (file + line range). (2) For each AC, cite test evidence (≥2 tests with class + method names). (3) For each AC, verify M902-01 schema compliance if gate-related. (4) For critical ACs, cite objective measurements (e.g., "AC-9 Determinism: 4 tests run gate 5x each on same fixtures → identical output all runs"). (5) If any AC cannot be evidenced, escalate to responsible agent; do not advance stage.
  **severity:** low

### Anti-Patterns

1. **Planning without decision checkpoints:** Planning phase analyzes design space but does not document frozen decisions. Spec Agent re-evaluates same decisions (waste), or assumes prior decisions are outdated (risk). Solution: Planning Agent must produce checkpoint file with ≥5 explicit decisions.

2. **Specification without schema examples:** Spec describes tool JSON outputs in narrative form ("gitleaks returns an array of matches with severity, rule, and file"). Implementation must reverse-engineer the exact schema from tool documentation or trial runs, risking mismatches. Solution: Spec freeze gate requires tool JSON input/output examples.

3. **Test suite without dimension enumeration:** Test Breaker writes 50 tests covering "edge cases" without systematic categorization. Implementation encounters untested scenarios (missing field, timeout, extremely large payload, encoding edge case). Solution: Test Breaker checkpoint lists vulnerability dimension categories and test count per category.

4. **AC Gatekeeper validation without evidence:** AC Gatekeeper states "AC-1 is satisfied" without citing code path or test. If rework is needed, there's no traceability to guide it. Solution: Evidence-driven validation with code citations.

### Prompt Patches

- **agent: Planning Agent**
  **change:** "In the planning checkpoint, document (1) Tool selection: which security scanning tools are required? Why? Per spec/code_governance or ticket? (2) Severity thresholds: what are HARD_FAIL, WARN, PASS conditions? (3) Fixture strategy: mock-only or real? How to prevent accidental real secrets/vulns? (4) Determinism requirement: identical output guarantee or best-effort? (5) Shadow vs blocking mode: which applies in this milestone? (6) Framework integration: which gate runner version? (7) Timeout strategy: per-tool or aggregate? (8) Exclusion policy: which files/directories skip scanning? For each decision, state: Assumption, Rationale, Confidence (HIGH|MEDIUM|LOW), Mitigation (if MEDIUM/LOW)."
  **reason:** Explicit planning checkpoints freeze design space before Spec Agent writes. Eliminates spec re-evaluation and reduces ambiguity-driven rework downstream."

- **agent: Specification Agent**
  **change:** "When freezing a specification for gates or infrastructure, include: (1) Tool version pinning (pyproject.toml, package.json references). (2) Complete tool JSON input/output examples (gitleaks, bandit, semgrep, etc.). (3) Severity mapping table (tool_rule_name → ERROR/WARN/INFO enum). (4) Numeric threshold definitions with units (CVSS 7.0 = critical, <7.0 = warn, <4.0 = info). (5) Timeout values per tool and aggregate limit. (6) Error handling strategy (tool not found, subprocess timeout, malformed JSON). (7) Determinism validation approach (no timestamps in logic, sorted output, no randomness). (8) M902-01 schema compliance checklist (required fields, field types, examples). Freeze spec only when all 8 items are complete."
  **reason:** Detailed specifications guide implementation without ambiguity. Spec completeness checklist prevents 'clarified in implementation' deferrals that delay or derisk testing."

- **agent: Test Breaker Agent**
  **change:** "When producing adversarial tests, enumerate vulnerability dimensions upfront: (1) Boundary conditions (threshold edge cases, min/max values). (2) Null/empty/missing fields (subprocess returns empty array, malformed JSON, missing field). (3) Type mismatches (field is string when int expected). (4) Logic consistency (operators, cascading conditions, priority order). (5) Scope (tool applies to right files? ignores exclusions?). (6) Timestamps and ordering (non-determinism risks). (7) Concurrency (subprocess interleaved output). (8) Regex/pattern matching (false positives/negatives). (9) File I/O (permissions, path encoding, large file names). (10) Schema compliance (JSON serialization, required fields). (11) Stress (extreme payloads, deep nesting). (12) Mutation (operator flips, condition negation). (13) Exit code semantics (per-tool exit code meanings). (14) Checkpoint assumptions (protocol-level invariants). List target test count per dimension. Implement dimensions in order until target reached. Log test count per dimension in checkpoint."
  **reason:** Systematic dimension enumeration prevents cognitive overload and ensures comprehensive coverage. Checkpoint documentation enables AC Gatekeeper to verify coverage is complete."

### Workflow Improvements

1. **Planning-Spec-Test triple-checkpoint validation:** After Planning Agent produces checkpoint, require Spec Agent to review planning decisions and document agreement or escalation. After Spec freeze, require Test Designer and Test Breaker to review spec decision sections and verify test coverage maps to decisions. Creates explicit traceability: Decision → Spec Section → Test(s).

2. **Specification freeze gate (spec-exit-gate skill):** Automatically validate spec completeness before advancing to Test Design. Checklist: (1) All tool versions pinned. (2) JSON input/output examples present. (3) Severity mappings complete. (4) Numeric thresholds defined. (5) Error handling documented. (6) Schema examples provided. (7) Determinism approach explained. (8) M902-01 compliance (if gate). If checklist fails, route back to Spec Agent; do not advance.

3. **Test dimension coverage matrix:** After Test Breaker completes, automatically generate a matrix (dimensions × test count) and compare to target. Alert if coverage is low (<20% of expected dimension tests). This prevents "looks comprehensive" gates that miss edge cases.

### Keep / Reinforce

1. **practice:** Planning Agent freeze + checkpoint produces reusable design decisions. M902-16 Planning froze 8 decisions with rationale; Spec Agent did not re-debate them. Future gates (security scanning, linting, performance testing) can reuse tool selection decisions from M902-16 checkpoint.
  **reason:** Decisions frozen in checkpoints become team norms. M902-16's "gitleaks + bandit + semgrep + pip-audit + npm audit" became the reference for future security gates, eliminating re-evaluation."

2. **practice:** Detailed specification (834 lines with 8 requirements, examples, severity tables, error handling) creates clear contracts for Implementation and Test Breaker agents. M902-16 spec was frozen v1.0 without revision, suggesting contracts were clear enough.
  **reason:** Contrast with M902-12 spec that required v1.0 → v1.1 revision after test contradictions. M902-16's detailed spec prevented contradictions. Invest time in spec detail to save rework downstream."

3. **practice:** AC Gatekeeper evidence-driven validation (code path citations + test citations + objective measurements) creates confidence in completion. M902-16 AC Gatekeeper's detailed evidence report (273 lines) enabled clean COMPLETE transition.
  **reason:** Evidence-driven validation is trustworthy. Narrative validation ("AC-1 looks satisfied") is not. Require citations."

---

## [M902-17] — Zero-Rework Integration Validation via Explicit Scope Boundary Enforcement

*Completed: 2026-05-19*

### Executive Summary

M902-17 (Final Validation & Stage Integration) completed from planning through AC gatekeeper sign-off with zero rework loops, zero test failures during implementation, and zero AC ambiguities. This ticket validates 16 completed child tickets (M902-01 through M902-16) and an 8-stage governance pipeline. All 27 ACs passed on first validation attempt (64/64 tests PASS, 13/13 gates compliant, 16/16 child tickets verified). The success pattern is replicable and reveals critical disciplines for integration validation tickets.

### Key Learnings

1. **Explicit Scope Boundary Enforcement at Planning Stage Prevents Rework (Critical)**
   
   - **Insight:** M902-17 planning checkpoint explicitly defined validation scope as "M902-01 through M902-16 only; M902-18 through M902-27 remain in backlog." This single decision prevented scope creep and ambiguity. No part of the execution phase attempted to validate out-of-scope tickets. Planning agent read ticket AC structure (lines 17-93), confirmed all references were to M902-01-M902-16, and documented assumption with HIGH confidence.
   
   - **Impact:** Without this boundary, spec might have included validation of tool categorization (M902-18), context budgeting (M902-21), or API contracts (M902-24-27). Each would have added 2-4 weeks of validation work, 50+ additional tests, and multiple rework cycles as implementation discovered missing fixtures or integration gaps. Explicit scope boundary eliminated this entire risk class.
   
   - **Prevention:** For integration/umbrella tickets: (1) At planning stage, explicitly list which child tickets are in scope vs. backlog. (2) Document the decision rule (e.g., "only tickets in 02_complete/ folder are in scope"). (3) If scope is ambiguous, ask clarifying question: "Does this ticket validate 27 features or 16?" (4) Freeze scope decision before spec is written. Do not allow scope expansion during specification.
   
   - **Severity:** CRITICAL

2. **Triple-Layer Verification Strategy Eliminates Single-Domain Gaps (High)**
   
   - **Insight:** Specification defined three independent verification layers: (1) Structural (read all 16 specs, verify files exist at expected paths), (2) Integration (run gate_runner.py with sample diffs, verify all 8 stages execute in order), (3) Audit (cross-reference all 27 ACs against evidence artifacts, build traceability matrix). All three had to pass independently. This redundancy caught issues that single-layer verification would miss.
   
   - **Impact:** Structural validation alone would miss gate registry gaps (missing entries, invalid modes). Integration validation alone would miss schema violations in gate outputs. Audit validation alone would miss module path inconsistencies. The three layers combined ensured no artifact inconsistency survived to implementation. Result: AC Gatekeeper found zero blockers.
   
   - **Prevention:** For large integration tickets (>10 child dependencies, >8 ACs): Always specify three verification layers in specification. Make each layer independent. Do not allow implementation to skip any layer. Document in spec what each layer checks and what class of bugs it catches.
   
   - **Severity:** HIGH

3. **Traceability Matrix as Executable Specification Prevents AC Ambiguity (High)**
   
   - **Insight:** Specification created AC traceability matrix mapping all 27 ACs to specific test cases and evidence artifact paths BEFORE test design began. This artifact became the source of truth: when Implementation Agent and AC Gatekeeper executed tests, they followed the matrix exactly. Zero ACs had ambiguous acceptance criteria.
   
   - **Impact:** Without the matrix, ACs would be validated ad-hoc as different agents encountered them. AC-17 (code governance linked) might be validated by reading CLAUDE.md; AC-13 (gate registry) validated by counting entries in JSON; AC-22 (test matrix coverage) validated by counting test files. Each approach would be different, subjective, and could produce different results on re-validation. With the matrix: every AC has one canonical test case and one evidence artifact path. Reproducible, objective, auditable.
   
   - **Prevention:** Always create traceability matrix at spec freeze for validation tickets. Format: AC # | AC name | test case(s) | evidence artifact path | status. Update status after implementation. Use matrix as input to AC Gatekeeper; require AC Gatekeeper to validate every AC listed in matrix.
   
   - **Severity:** HIGH

4. **Evidence Artifact Catalog Enables Instant AC Sign-Off (Medium)**
   
   - **Insight:** Implementation Agent did not just run tests; it systematically collected evidence artifacts (gate outputs, test reports, schema validations, registry audits) into a catalog under `project_board/checkpoints/M902-17/evidence/`. AC Gatekeeper received 8 machine-readable evidence files: test_execution_report.txt, gate_registry_validation.txt, schema_audit.txt, etc. AC Gatekeeper validated each AC by reading the corresponding evidence artifact, not by re-running tests or re-reading source code.
   
   - **Impact:** AC Gatekeeper sign-off took ~2 hours (reading artifacts, cross-checking against ACs). If evidence had not been systematized, AC Gatekeeper would have needed to: (1) run gate_runner.py independently to verify gates, (2) re-check test logs for specific test names, (3) read source files to verify gates are registered. Estimated time: 8-12 hours. Systemized evidence shortened validation by 75%.
   
   - **Prevention:** For integration validation tickets: require Implementation Agent to produce evidence artifact catalog. Each artifact should be: (1) machine-readable (JSON, CSV, or plaintext with structured headers), (2) self-documenting (include headers, legends, methodology), (3) indexed (provide evidence catalog/index document). Provide catalog path in implementation checkpoint.
   
   - **Severity:** MEDIUM

5. **Test Suite as Integration Contract Prevents Implementation Interpretation Drift (Medium)**
   
   - **Insight:** Test Designer created 38 behavioral + 26 adversarial tests before implementation began. Tests were deterministic, mocked (no real gate execution), and encoded exact expectations: Stage 0 must output `classification: "docs-only"` and `routing_decision: "skip"` for docs-only changes. When Implementation Agent ran gates, it compared actual outputs to test expectations. Test suite was the spec, not the code.
   
   - **Impact:** If tests had not been written until after implementation, Implementation Agent could have made subjective choices (e.g., "routing_decision is advisory; gates can ignore it if confidence is low"). Test-first approach locked in the contract before code was written. Result: Implementation produced outputs that matched tests exactly. Zero discrepancies.
   
   - **Prevention:** For integration validation tickets with multiple child subsystems (gates in this case): write behavioral test suite BEFORE implementation. Tests should use realistic mock outputs (schema-compliant, realistic fields) and encode exact expectations. Tests become the integration contract. Implementation must match tests, not vice versa.
   
   - **Severity:** MEDIUM

### Anti-Patterns

1. **Scope Creep During Implementation:** Ticket says "validate 16 tickets" but implementation discovers "actually, I should also check if M902-18 will work." Result: scope expands, new tests are added, evidence artifacts multiply, AC Gatekeeper finds new ambiguities. Prevention: Freeze scope at planning stage; document out-of-scope items explicitly in spec. If out-of-scope work is discovered during implementation, log it as a separate finding, don't add it to validation scope.

2. **Ad-Hoc Evidence Collection:** Implementation Agent runs tests, produces a summary ("all tests pass"), but doesn't systematize evidence artifacts. AC Gatekeeper receives summary + asks for clarification on specific ACs. Result: back-and-forth discovery. Prevention: Require Implementation Agent to produce evidence catalog during execution, not after AC Gatekeeper asks for it. Make artifact location explicit in spec.

3. **Test Suite as Afterthought:** Specification written, Implementation Agent discovers gaps during coding, asks Test Designer to add tests retroactively. Test Designer adds tests that fit the implementation, not the spec. Result: tests validate the code, not the contract. Prevention: Test Designer phase must complete before Implementation Agent starts. Tests are immutable during implementation (except for bug fixes, which are tracked separately).

4. **Validation Assumed vs. Explicitly Verified:** Planning checkpoint says "assume gate_registry.json is authoritative" without actually reading it. Implementation discovers the registry is missing an entry for Stage 5. Prevention: Planning should include spot-checks (read 2-3 files to verify assumptions). Specification should make these assumptions explicit ("Assumption A1: gate_registry.json is authoritative; verified by reading file on 2026-05-19").

### Prompt Patches

**Planning Agent (Integration Validation Tickets):**
- Add: "For integration/umbrella tickets: (1) Explicitly define scope boundaries (e.g., 'Validates M902-01 through M902-16; M902-18+ deferred'). (2) Document the decision rule in planning checkpoint with HIGH confidence. (3) Identify all child tickets and confirm their status. (4) List what is explicitly out of scope to prevent scope creep during spec/implementation."

**Specification Agent (Integration Validation Tickets):**
- Add: "Create AC traceability matrix mapping every AC to one or more test case(s) and one evidence artifact path. Matrix format: AC # | AC name | test case(s) | evidence path | status. This matrix becomes the source of truth for test design and AC gatekeeper validation. Do not proceed to Test Designer without this matrix."
- Add: "For multi-layer verification (structural, integration, audit): specify what each layer checks, what class of bugs it catches, and what evidence artifacts each layer produces. Do not allow layers to be skipped or reordered during implementation."

**Implementation Agent (Integration Validation Tickets):**
- Add: "After all tests pass: (1) Create evidence artifact catalog. (2) For each major validation activity (test execution, gate registry validation, schema audit, etc.), produce a machine-readable artifact and index it. (3) Provide catalog path in implementation checkpoint. (4) Do not assume AC Gatekeeper can re-run tests; provide evidence artifacts instead."

**AC Gatekeeper Agent (Integration Validation Tickets):**
- Add: "Accept evidence artifacts from Implementation Agent as source of truth for AC validation. Do not re-run tests or re-read source code unless artifact is ambiguous. Validate each AC by reading corresponding evidence artifact. If evidence is missing or ambiguous, route back to Implementation Agent for artifact clarification, not code review."

### Workflow Improvements

1. **Scope Freeze Gate (Planning → Specification):**
   - Add: "For integration/umbrella tickets, require explicit scope boundary document at end of planning. Document: (1) In-scope child tickets (list by ID), (2) Out-of-scope tickets (list by ID), (3) Decision rule (e.g., 'all tickets in 02_complete/ folder'), (4) Confidence level. Specification phase cannot begin until scope boundary is approved."

2. **Evidence Artifact Checklist (Implementation → AC Gatekeeper):**
   - Add: "Implementation phase must produce evidence artifact checklist listing all artifacts created, their paths, and what they validate. Checklist becomes the index for AC Gatekeeper. Example: 'gate_registry_validation.txt validates AC-13, AC-14, AC-15 (gate registry completeness and CLI interface)'."

3. **Traceability Matrix as Handoff Document (Specification → Test Design → Implementation):**
   - Add: "AC traceability matrix (created in Specification phase) becomes the handoff document to Test Designer and Implementation Agent. Matrix includes: AC #, test case name, evidence path. Test Designer implements exactly the tests listed in matrix. Implementation Agent collects evidence at paths listed in matrix. AC Gatekeeper validates exactly the ACs listed in matrix."

### Keep / Reinforce

1. **Planning Checkpoint Protocol Strength:** M902-17 planning agent used explicit checkpoint format ("Would have asked / Assumption made / Confidence"). This discipline surfaced the scope boundary question clearly. The assumption "M902-18+ are backlog" was documented with HIGH confidence, making it traceable and reviewable. Reinforce this checkpoint format for all integration tickets.

2. **Test Suite Determinism:** Both behavioral (38 tests) and adversarial (26 tests) test suites executed in <0.1 seconds with zero flakes. This was enabled by mocking all external dependencies (no real gate invocation, no filesystem I/O, no network). Reinforce mock-first test design for infrastructure/pipeline validation tickets.

3. **Schema-First Implementation:** M902-01 schema was the contract (status, violations, remediation_hints, metadata). Every gate output was validated against this schema. Tests verified schema compliance. No gate was allowed to return custom JSON. Reinforce schema-first design: define schema before implementation, test against schema, validate outputs in tests.

4. **Evidence-Driven AC Gatekeeper:** AC Gatekeeper did not read source code or run tests independently; it read systematic evidence artifacts. This made AC Gatekeeper's review objective, auditable, and efficient. Reinforce evidence-artifact-first approach for all validation tickets.

---

## [M902-20] — Todo Gate: Artifact Contract, Runbook AC, and Attribution-Scoped Handoff Validation

*Completed: 2026-05-20*

### Learnings

- **category: process**
  **insight:** Ticket AC that names a standalone deliverable (e.g. runbook file) cannot be satisfied by equivalent prose in the spec alone; AC Gatekeeper must verify the file exists at the documented path.
  **impact:** First AC Gatekeeper pass routed to INTEGRATION with 8/9 ACs PASS because `TODO_VALIDATION_RUNBOOK.md` was missing despite Req 10 text in `902_20_todo_validation_spec.md`. Required a follow-up commit before COMPLETE.
  **prevention:** Implementation Agent checklist: for every AC bullet that names a path, create that file before requesting AC review. AC Gatekeeper: FAIL the AC if the path is absent even when spec duplicates the content.
  **severity:** high

- **category: architecture**
  **insight:** Handoff gates that read agent-written checkpoints need a frozen primary artifact (`todos-latest.json`), explicit fail-closed on invalid primary data (no silent fallback), and secondary fallbacks only when primary is absent—not corrupt.
  **impact:** Spec/checkpoints resolved A1/A5: invalid `todos-latest.json` → `FAIL` with `todo_artifact_invalid`; vacuous PASS only when no artifacts or empty `todos[]`. Adversarial suite (28+ tests) encoded merge/mtime/fenced-JSON precedence so implementation could not “helpfully” pass on stale or wrong snapshots.
  **prevention:** Spec Agent: document discovery order and “no fallback on corrupt primary” in requirements table. Test Breaker: add tests for corrupt primary + valid older `todos-*.json` (must still FAIL).
  **severity:** high

- **category: architecture**
  **insight:** Multi-agent todo validation must scope FAIL to todos attributed to the finishing `expected_agent`; prior-agent `in_progress` rows are noise, not blockers.
  **impact:** Without attribution filtering, every handoff would fail on leftover todos from earlier stages. Spec A6 + tests (`prior-agent ignore`) made the contract executable.
  **prevention:** Any gate validating per-agent work lists must define attribution rules (envelope `agent`, per-todo `agent`, normalization table) and test cross-agent `in_progress` rows do not appear in `incomplete_tasks[]`.
  **severity:** high

- **category: testing**
  **insight:** Checkpoint-reading gates need path-traversal and repo-root anchoring tests in the adversarial suite, not only happy-path fixture layout.
  **impact:** Test design/break phases added 6+ path-security cases; ticket closure notes NFR-3 repo/cwd anchor and path confinement fix after review—security behavior was test-driven, not discovered at AC time.
  **prevention:** Test Breaker: for every gate that resolves `project_board/checkpoints/<ticket_id>/`, include `..`, absolute-outside-repo, and symlink/override injection cases. Implementation: anchor paths to detected repo root, never trust raw `ticket_id` segments.
  **severity:** medium

- **category: process**
  **insight:** Deliver gate module + registry + runbook in the ticket; defer autopilot invocation to a follow-on ticket (M902-23) with explicit out-of-scope language in planning/spec.
  **impact:** Avoided expanding M902-20 into full orchestrator wiring while still shipping a testable `todo_validation_check` in shadow mode. Runbook documents shadow exit-code behavior so agents remediate on FAIL even when CI exits 0.
  **prevention:** Planning checkpoint: state “module-only vs wired” with Medium confidence; Spec: repeat in Executive Summary out-of-scope. Do not block M902-20 COMPLETE on M902-23 unless ticket AC explicitly requires wiring.
  **severity:** medium

### Anti-Patterns

1. **Spec-as-runbook:** Writing runbook content only in the spec and skipping `project_board/checkpoints/<ticket_id>/TODO_VALIDATION_RUNBOOK.md` when the ticket AC requires a runbook file.
   **detection_signal:** AC Gatekeeper marks runbook AC FAIL while implementation and registry tests pass.
   **prevention:** Copy or generate the standalone runbook from spec Req 10 before AC review; link path in implementation checkpoint.

2. **Fallback on corrupt primary:** When `todos-latest.json` is invalid JSON, falling back to an older `todos-*.json` or fenced markdown block to obtain PASS.
   **detection_signal:** Adversarial test `invalid latest + valid older snapshot` expects FAIL; gate returns PASS.
   **prevention:** Fail-closed on primary parse/schema errors; fallbacks only when primary file is missing.

3. **Global in_progress sweep:** Failing handoff if *any* todo in the snapshot is `in_progress`, regardless of `expected_agent`.
   **detection_signal:** FAIL payloads list todos attributed to Spec Agent when validating Implementation Agent handoff.
   **prevention:** Filter by normalized agent attribution before building `incomplete_tasks[]`.

4. **Shadow-mode complacency:** Treating shadow registry mode (exit 0 on FAIL) as permission to hand off with open todos.
   **detection_signal:** Orchestrator advances stage while `incomplete_tasks[]` non-empty; agents never write `todos-latest.json`.
   **prevention:** Runbook + agent prompts: remediate FAIL before handoff regardless of exit code until M903 blocking mode.

### Prompt Patches

- **agent: Implementation Agent (Generalist)**
  **change:** "Before AC Gatekeeper: (1) For each ticket AC that names a file path (runbook, registry entry, gate module), verify the file exists at that path. (2) Write TodoWrite snapshots to `project_board/checkpoints/<ticket_id>/todos-latest.json` with `schema_version` `1.0` before handoff. (3) On gate FAIL, read `incomplete_tasks[]` and `remediation_hints[]`; update snapshot and re-run gate with same `expected_agent`."
  **reason:** Prevents INTEGRATION hold for missing runbook and vacuous PASS from missing snapshots.

- **agent: AC Gatekeeper Agent**
  **change:** "For deliverable ACs that specify a path (e.g. `TODO_VALIDATION_RUNBOOK.md`): require `test -f <path>` or equivalent; do not accept spec section duplication as evidence. For gate tickets in shadow mode: still require runbook and PASS/FAIL contract tests; note shadow exit-code behavior in escalation notes only."
  **reason:** Caught missing runbook on first pass; keeps shadow rollout from skipping agent-facing docs.

- **agent: Test Breaker Agent**
  **change:** "For checkpoint-reading gates: add adversarial matrix rows—corrupt primary + valid backup (must FAIL), path traversal on `ticket_id`, fenced JSON precedence in `.md` logs, attribution bypass (prior-agent `in_progress` must not fail current agent), empty/vacuous PASS cases. Emit handoff checklist in checkpoint for Implementation."
  **reason:** 66/66 first-close tests including path and fallback cases reduced implementation rework.

- **agent: Spec Agent**
  **change:** "Freeze TodoWrite on-disk contract in Assumptions table: primary file name, schema_version, discovery order, fail-closed rules, attribution rules, and dual payload (`incomplete_tasks[]` + `violations[]` with `rule`). State orchestrator wiring explicitly out-of-scope with ticket id (e.g. M902-23) if deferred."
  **reason:** Planning ambiguities (A1 format, A4 wiring) were resolved once in spec and not re-debated in implementation.

### Workflow Improvements

1. **Runbook path in AC traceability**
   - **issue:** Runbook AC treated as documentation satisfied by spec prose.
   - **improvement:** Map runbook AC to exact path `project_board/checkpoints/<ticket_id>/TODO_VALIDATION_RUNBOOK.md` in spec traceability; Implementation checkpoint must cite path.
   - **expected_benefit:** Eliminates INTEGRATION rework for “invisible” deliverables.

2. **INTEGRATION stage for missing operational artifacts**
   - **issue:** 8/9 ACs pass but ticket cannot close.
   - **improvement:** AC Gatekeeper → INTEGRATION (not COMPLETE) when only operational/docs ACs fail; Implementation fixes artifacts without re-running full test suite unless code changed.
   - **expected_benefit:** Clear separation between code-complete and workflow-complete.

3. **Todo snapshot write before stage transition**
   - **issue:** Vacuous PASS when agents never persist TodoWrite.
   - **improvement:** Document in M902-23 orchestrator: refresh `todos-latest.json` immediately before `todo_validation_check`; until then, agents must write snapshot in implementation checkpoint step.
   - **expected_benefit:** Gate validates real handoff state, not empty directories.

### Keep / Reinforce

1. **Dual FAIL payload (`incomplete_tasks[]` + `violations[]`)** — Agent-readable rows plus M902-01 audit rules; planning checkpoint A2 carried through spec and tests.
2. **Planning assumption table → spec A1–A7** — Medium-confidence format questions (snapshot format, wiring scope) frozen before test design; no spec revision cycle reported.
3. **66-test red-green handoff** — Behavioral + adversarial suites collected red with `ModuleNotFoundError` until gate module landed; single implementation pass to green.
4. **Vacuous PASS semantics** — No artifacts and empty `todos[]` PASS with explicit messages; prevents false blocks on tickets that do not use TodoWrite yet.

---

## [M902-28] — Lefthook Parallel Hooks: Safety Matrix, Scope Boundaries, and Config-Contract Tests

*Completed: 2026-05-20*

### Learnings

- **category: infra**
  **insight:** Enabling hook parallelism requires a frozen shared-resource matrix (write paths, git index, ports) per command pair—not a single `parallel: true` flip. Pairs marked UNKNOWN must stay UNSAFE until Integration evidence upgrades them.
  **impact:** Spec Appendix B classified `godot-tests` ∥ `py-tests` as **SAFE** only after documenting disjoint writes (`.godot/` vs `asset_generation/python/coverage.xml`). Static tests (T4/T5) and an adversarial concurrent-`coverage.xml` case prevent accidental cross-writes before parallel pre-push ships.
  **prevention:** Spec Agent: deliver normative safety matrix before Implementation. Test Breaker: add mutation tests for script write paths and same-file races when matrix claims SAFE.
  **severity:** high

- **category: process**
  **insight:** Developer-hook scheduling (Lefthook) and canonical CI ordering (`ci/scripts/run_tests.sh`) are separate contracts; parallelizing hooks must not imply parallelizing the full suite without an explicit ticket.
  **impact:** Planning checkpoint and spec A4 kept MAINT-TSGR sequential Godot→Python in CI while only flipping `pre-push.parallel` in `lefthook.yml`. Avoided scope creep into pytest-xdist, parallel Ruff, or `run_tests.sh` reordering.
  **prevention:** Planner/Spec: state “Lefthook only” vs “CI canonical” in assumptions table; Test Designer: assert `run_tests.sh` order unchanged (T6). Defer inner-script parallelism (Ruff→pytest→diff-cover) unless profiled and ticket-scoped.
  **severity:** medium

- **category: infra**
  **insight:** Lefthook 1.x parallel scheduling is config-only (`parallel:` in `lefthook.yml`); upstream does not document `LEFTHOOK_PARALLEL` or project-specific env kill-switches. Opt-out is `LEFTHOOK=0`, `LEFTHOOK_EXCLUDE`, or temporary `parallel: false`.
  **impact:** Planner medium-confidence question on `LEFTHOOK_PARALLEL` was resolved in spec Requirement 05—no invented `BLOBERT_HOOKS_PARALLEL`. Documented real opt-outs in `CLAUDE.md` and `lefthook.yml` header instead of non-functional env vars.
  **prevention:** Spec Agent: verify parallel/opt-out against the repo’s Lefthook version docs before freezing Requirement 05; adversarial tests assert no phantom env vars in the implementation tree.
  **severity:** medium

- **category: testing**
  **insight:** Hook-scheduling tickets can close on YAML + shell **config-contract** tests in CI; full dual-suite wall-clock overlap belongs in Integration/Human follow-up, not pytest-in-CI.
  **impact:** 30/30 PASS (11 behavioral + 19 adversarial) with one expected red on `pre-push.parallel: false` before Implementation. T7 overlap timing stub deferred; AC Gatekeeper noted Human may confirm with `LEFTHOOK_VERBOSE=1 git push` on mixed `.gd` + Python changes.
  **prevention:** Test Designer: parse `lefthook.yml` and `.lefthook/scripts/*` only—no markdown golden-output assertions. Spec: separate “contract tests” (Req 10) from “baseline wall-clock” (Req 02) with explicit owner (Integration checkpoint vs Human).
  **severity:** medium

- **category: infra**
  **insight:** `parallel: true` in YAML does not prove effective concurrency; pre-commit already had `parallel: true` while pre-push was the real bottleneck at `parallel: false`. Verification needs `LEFTHOOK_VERBOSE=1` log overlap or ≥25% wall-clock reduction vs sequential single-hook runs on the same staged set.
  **impact:** Ticket’s largest win was flipping pre-push, not re-litigating pre-commit. Spec Requirement 06 defines evidence bar so agents do not mark “parallelism verified” from config alone.
  **prevention:** Integration/AC Gatekeeper: when AC says “confirm parallelism,” require verbose logs or timed before/after table in checkpoint—not YAML inspection only.
  **severity:** medium

### Anti-Patterns

1. **Inventing parallel kill-switch env vars** — Documenting `LEFTHOOK_PARALLEL` or `BLOBERT_HOOKS_PARALLEL` without upstream Lefthook support.
   **detection_signal:** Docs mention env override but `lefthook.yml` is the only lever; adversarial test finds env var in tree without Lefthook reference.
   **prevention:** Spec negative finding + `LEFTHOOK=0` / `LEFTHOOK_EXCLUDE` / config `parallel: false` only.

2. **CI suite parallelism by analogy** — Changing `ci/scripts/run_tests.sh` to overlap Godot and Python because pre-push hooks were parallelized.
   **detection_signal:** `run_tests.sh` order tests fail; MAINT-TSGR contract drift.
   **prevention:** Explicit ticket for CI scheduling; keep hook ticket scope to `lefthook.yml` and hook scripts.

3. **YAML-as-proof of concurrency** — Treating `pre-commit.parallel: true` as sufficient without overlap evidence when AC requires “true concurrency.”
   **detection_signal:** No baseline table; no `LEFTHOOK_VERBOSE` excerpt in checkpoint.
   **prevention:** Requirement 06 evidence protocol in spec; Human/Integration timing follow-up for dual-suite pre-push.

4. **Inner-script parallelism scope creep** — Parallelizing Ruff, pytest, and diff-cover inside `py-tests.sh` in the same ticket as cross-command Godot∥Python.
   **detection_signal:** Implementation edits `py-tests.sh` flow without safety matrix row; single `coverage.xml` writer races.
   **prevention:** Spec marks P15/P16 as N/A; deferrals point to M902-07/M903 for lint caching and xdist.

### Prompt Patches

- **agent: Spec Agent**
  **change:** "For Lefthook/scheduling tickets: (1) Verify parallel and opt-out mechanisms against the repo’s Lefthook version—document negative findings (e.g. no `LEFTHOOK_PARALLEL`). (2) Freeze Appendix safety matrix: every concurrent command pair → shared writes, git index, ports → SAFE/UNSAFE/N/A. (3) State explicitly: `ci/scripts/run_tests.sh` order unchanged unless ticket AC requires CI changes."
  **reason:** Resolved A1 env-var myth and A4 CI boundary before test design; prevented invented kill-switches.

- **agent: Planner Agent**
  **change:** "When ticket mentions ‘parallel hooks,’ decompose: cross-command (Lefthook `parallel:`) vs inner-script (shell pipeline) vs canonical CI (`run_tests.sh`). Default scope to Lefthook only; flag inner/CI parallelism as out-of-scope or follow-on unless trivial and matrix-approved."
  **reason:** Planning checkpoints kept py-tests internal steps and MAINT-TSGR sequential out of M902-28.

- **agent: Test Designer Agent**
  **change:** "Hook config tickets: assert `lefthook.yml` keys, glob delegation, and hook script write paths (no cross-suite artifacts). Do not assert markdown spec/ticket bodies as golden output. Leave full Godot+Python wall-clock overlap to Integration checkpoint or Human; one expected-red test on the flag Implementation will flip."
  **reason:** 30-test suite closed without Godot-in-CI timing; clean red→green on `pre-push.parallel`.

- **agent: Test Breaker Agent**
  **change:** "For parallel hook specs: adversarial matrix must include—missing/duplicate `parallel` YAML keys, string `'false'` vs bool, concurrent write to shared `coverage.xml`, `run_tests.sh` ordering regression, and governance that `lefthook.yml` stays monitored. If matrix row is SAFE, add at least one test that would fail if scripts converged write paths."
  **reason:** 19 adversarial tests caught YAML drift and coverage races without live hook runs in CI.

- **agent: AC Gatekeeper Agent**
  **change:** "For parallelism ACs: accept config-contract pytest PASS + implementation checkpoint baseline table template. If dual-suite pre-push wall-clock was not measured (no mixed `.gd`+Python push), note in escalation as Human follow-up—do not FAIL solely for missing local timing when Req 10 tests pass."
  **reason:** Ticket completed with contract evidence; timing explicitly deferred per spec/checkpoint.

### Workflow Improvements

1. **Safety matrix before Implementation flip**
   - **issue:** Flipping `parallel: true` without documented pair-level resource analysis risks flaky hooks or corrupt artifacts.
   - **improvement:** Spec Requirement 01 + Appendix B complete before Test Design; Implementation changes only pairs marked SAFE.
   - **expected_benefit:** Rollback criterion (Requirement 05) is evidence-based, not reactive guesswork.

2. **Contract tests vs Integration timing split**
   - **issue:** Agents block COMPLETE waiting for full Godot+pytest overlap in CI, or skip timing entirely with only YAML edits.
   - **improvement:** Req 10 → pytest contract; Req 02 → checkpoint baseline table; Human optional `LEFTHOOK_VERBOSE=1` confirmation on mixed changes.
   - **expected_benefit:** Predictable closure in agent CI; real wall-clock proof where machines have Godot.

3. **Expected-red handoff for single-config tickets**
   - **issue:** Unclear whether failing `pre-push.parallel` test means broken tests or correct pre-implementation state.
   - **improvement:** Test Design checkpoint documents verbatim failure (`assert False is True`); Test Break reports “1 expected red”; Implementation flips one key → 30/30.
   - **expected_benefit:** No false rework cycles on intentional red.

### Keep / Reinforce

1. **Planning assumption table → spec A1–A6** — `LEFTHOOK_PARALLEL`, inner py-tests, CI sequential, and `.godot/` contention resolved before test design; no spec revision cycle.
2. **30-test red-green on one YAML flag** — Behavioral + adversarial suites; Implementation changed `pre-push.parallel` + docs only; `verify_tsgr_runner_contract.sh` OK.
3. **Disjoint-write static contracts** — Godot hook must not touch `coverage.xml`; Python hook writes only under `PY_ROOT`; enforced in T4/T5 and adversarial race test.
4. **No markdown prose as test oracle** — `TestNoMarkdownProseContract` + YAML/script parsing only; stable CI without reading ticket bodies.

---

## [M902-22] — Early-Stop: Fixture Signal Isolation, Scoped JSONL Dedupe, Fail-Closed Evaluate
*Completed: 2026-05-20*

### Learnings

- **category: testing**
  **insight:** Streak-detection tests must vary each signal dimension independently; reusing the same `diff_hash` across iterations while varying only `error` still satisfies `repeated_diff` (3× identical hash) and produces false positives unrelated to the scenario under test.
  **impact:** Primary behavioral suite (`test_early_stop_detection.py`) initially triggered `repeated_diff` in tests aimed at error repetition or alternation; implementation rework required unique per-iteration `diff_hash` fixtures (e.g. `f"{i:064x}"[:64]`) except in tests that explicitly assert `repeated_diff`.
  **prevention:** Test Designer: for each heuristic (error / diff / no-op / max-iter), document which fields are held constant vs varied per iteration. Test Breaker: add a matrix row “varying error only — diff_hash must differ each iteration unless testing diff stall.”
  **severity:** high

- **category: architecture**
  **insight:** Module-level idempotency caches keyed only by event content (e.g. escalation reason + iteration) leak across logical tenants when pytest uses multiple `tmp_path` checkpoint roots in one process.
  **impact:** Process-global `_last_jsonl_event_key` suppressed JSONL writes under a second checkpoints root; adversarial `test_jsonl_lines_are_valid_json_objects` failed with `FileNotFoundError` for `early_stop_events.jsonl`. Fix: include `checkpoints_root` (resolved path) in the dedupe key; autouse fixture clears cache between tests.
  **prevention:** Any append-only side-effect log with in-process dedupe must scope the key by `(checkpoints_root, ticket_id, …)` not global content hash alone. Test Breaker: require `test_escalate_writes_jsonl_under_each_checkpoints_root` when dedupe exists.
  **severity:** high

- **category: architecture**
  **insight:** Evaluators that walk persisted iteration lists must validate element types before streak logic; corrupt on-disk `iterations` (e.g. JSON array of strings) must fail closed per spec (`incomplete_iterations: true`, `should_escalate: false`), not raise through internal helpers.
  **impact:** `evaluate_early_stop` crashed in `_tail_streak` with `AttributeError: 'str' object has no attribute 'get'` on adversarial `test_iterations_wrong_type_on_disk_blocks_evaluate`; violated AC-07.4 until implementation guarded schema before streak comparison.
  **prevention:** Implementation: treat load/parse + per-element dict contract as a single gate before heuristics. Test Breaker: always pair “corrupt/mistyped artifact” with assert on `incomplete_iterations` and no unhandled exception.
  **severity:** high

- **category: testing**
  **insight:** Adversarial CI modules for checkpoint-backed trackers should run collection independently of implementation (skip/gate on missing module) while still executing type/corruption tests once the module exists—catches evaluate crashes and global-state bugs behavioral happy paths miss.
  **impact:** Test Break run: 2 failed / 13 passed / 2 skipped before implementation fixes; failures were real contract gaps (JSONL path isolation, evaluate crash), not flaky env. Post-fix: 45 passed behavioral + adversarial.
  **prevention:** Keep separate `*_adversarial.py` for persistence gates; include rows: wrong `iterations` element type, concurrent append, JSONL idempotency per root, process-global state reset fixture.
  **severity:** medium

- **category: process**
  **insight:** Multi-signal loop detectors (error + diff + no-op + max-iter) need explicit spec severity per signal (e.g. no-op flag-only vs error/diff escalate); planning ambiguities on `diff_hash` source and no-op break behavior should freeze in spec assumptions before test vectors encode wrong expectations.
  **impact:** Planning checkpoint A1/A2 (diff source, no-op ≠ solo escalate) carried to spec A1–A3; reduced spec revision during implementation. Remaining test bugs were fixture isolation, not spec contradiction.
  **prevention:** Planner + Spec: assumption table entries for each detection dimension’s escalate vs flag-only behavior and hash contract before Test Designer authors T1–T10.
  **severity:** medium

### Anti-Patterns

1. **Shared diff_hash in non–diff-stall tests:** Using one constant `_DIFF_HASH_A` for every `record_iteration` in tests about error repetition, alternation, or max-iter.
   **detection_signal:** Unexpected `reason == "repeated_diff"` or escalation before the third identical error; evidence shows matching `diff_hashes` across iterations the test narrative claims differ.
   **prevention:** Vary `diff_hash` per iteration by default; only hold hash constant in `TestRepeatedDiffEscalation` (or equivalent).

2. **Global dedupe without tenant scope:** Idempotency key omits checkpoints root / ticket path; second test root never receives side-effect files.
   **detection_signal:** Adversarial JSONL test passes in isolation, fails in full suite order; `FileNotFoundError` on `early_stop_events.jsonl` under `tmp_path` B after escalation under `tmp_path` A.
   **prevention:** Scope dedupe keys to resolved checkpoints directory; reset module globals in pytest autouse fixture.

3. **Streak logic on unvalidated JSON:** Assuming `iterations[]` elements are dicts because schema_version is present.
   **detection_signal:** `AttributeError` on `.get` during evaluate; AC expects `incomplete_iterations` but process raises.
   **prevention:** Validate list element types after `json.load`; return incomplete payload without running `_tail_streak`.

4. **Behavioral-only coverage for persistence modules:** Happy-path append + escalate tests without corrupt-type and multi-root JSONL cases.
   **detection_signal:** 100% green behavioral suite while adversarial fails on first implementation pass.
   **prevention:** Test Breaker adversarial matrix mandatory for `ci/scripts/*_tracker.py` pattern (mirror M902-20/M902-21).

### Prompt Patches

- **agent: Test Designer Agent**
  **change:** "For loop-detection tests (repeated error, diff, no-op, max-iter): unless the test name explicitly targets that signal, use a distinct `diff_hash` per iteration (e.g. indexed 64-char hex). Document in the test class docstring which dimensions are intentionally held constant. Do not reuse a single fixture hash across T2/T5/T7 scenarios."
  **reason:** Prevents false `repeated_diff` triggers that force implementation rework.

- **agent: Test Breaker Agent**
  **change:** "For checkpoint append + JSONL escalation trackers: (1) add `test_escalate_writes_jsonl_under_each_checkpoints_root` when module uses in-process dedupe; (2) add corrupt `iterations` wrong element type → `evaluate_early_stop` returns `incomplete_iterations: true`, no exception; (3) autouse-clear any module-level `_last_*` caches between tests."
  **reason:** Caught JSONL path leak and evaluate crash before AC gate.

- **agent: Implementation Agent (Generalist)**
  **change:** "Before streak/heuristic logic in `evaluate_*`: validate loaded artifact schema (iterations list elements are dicts with required keys). On violation return spec-defined incomplete payload (`incomplete_iterations: true`, `should_escalate: false`). For idempotent JSONL writes, include resolved `checkpoints_root` in dedupe key, not event body alone."
  **reason:** Satisfies AC-07.4 fail-closed and multi-root test isolation.

- **agent: Spec Agent**
  **change:** "For multi-heuristic detectors, table each signal: detection rule, consecutive count, escalate vs flag-only, and evidence fields. Freeze `diff_hash` contract (injected vs git-computed, empty sentinel) in Assumptions before Requirement test contract (T1–T10)."
  **reason:** Aligns test vectors with severity split (no-op flag vs error/diff escalate).

### Workflow Improvements

1. **Fixture signal checklist at TEST_DESIGN handoff**
   - **issue:** Behavioral tests encoded accidental cross-signal correlation (same hash everywhere).
   - **improvement:** Test Design checkpoint lists, per test class, which of `{error, diff_hash, modified_files, tools_invoked}` vary across the N iterations.
   - **expected_benefit:** Fewer false-red cycles during implementation.

2. **Adversarial gate before IMPLEMENTATION complete**
   - **issue:** Evaluate crash and JSONL isolation found only when adversarial module ran against first implementation.
   - **improvement:** Require Test Break checkpoint to cite failing adversarial test names + expected contract before Implementation marks tracker done.
   - **expected_benefit:** Implementation lands fail-closed evaluate and scoped dedupe in one pass.

3. **Process-global state inventory for new CI modules**
   - **issue:** Hidden module globals break pytest isolation.
   - **improvement:** Planning task for persistence modules: list module-level caches/locks; Test Breaker adds autouse reset or per-tenant keys.
   - **expected_benefit:** Full-suite green matches isolated-module green.

### Keep / Reinforce

1. **Planning assumption table → spec A1–A6** — `diff_hash` two-tier contract, no-op flag-only vs escalate, orchestrator-direct evaluate, `loop_mode` gating resolved before test design.
2. **45-test behavioral + adversarial closure** — Red collection until `early_stop_tracker.py` exists; adversarial skips when module missing; 2 expected failures documented in test-break checkpoint drove targeted fixes.
3. **Sibling middleware hook pattern** — `_maybe_record_early_stop_iteration` mirrors context budget hook; exceptions swallowed so tracking never breaks invocations.
4. **Standalone runbook at checkpoint path** — `EARLY_STOP_RUNBOOK.md` maps `repeated_error` / `repeated_diff` / no-op to Human-first escalation; satisfies agent-facing AC without spec-only prose.

---

## [M902-23] — Atomic Handoff Checkpoint

### Root causes

1. **YAML `schema_version` parsed as float** — Fixture dumps `1.0` without quotes; PyYAML loads `1.0` float; strict string compare failed. **Fix:** accept `"1.0"`, `"1"`, and float forms in structure validation.
2. **Empty `checklist:` key → `None`** — Test fixture serializer emitted `checklist:` with no items; PyYAML sets `checklist: null`. **Fix:** treat `None` as `handoff_artifact_invalid`, not only empty list.
3. **Discover helper returned `"yaml"` as payload** — Second tuple element was mistaken for inline YAML; parser read literal `"yaml"`. **Fix:** empty string payload when loading from file path.
4. **Symlink `handoff-latest.yaml`** — `Path.resolve()` followed symlink and validated external target as PASS. **Fix:** reject any symlink on primary artifact (`path_traversal`).

### Keep / reinforce

- Mirror `todo_validation_check` for path confinement, `GateResult` shape, and registry wiring.
- Quote evidence in test YAML fixtures when whitespace/tabs present (adversarial `_yaml_dump`).
- Seven frozen pair catalogs in code (`PAIR_CATALOGS`) — single source for tests and gate.

---

## [M902-25] — Dual validation: live API beats stale TS unions; minimal drift fixtures miss production variants
*Completed: 2026-05-21*

### Learnings

- **category: testing**
  **insight:** Shared JSON drift fixtures prove Pydantic/Zod parity on synthetic shapes, but empty or minimal nested payloads do not exercise discriminated unions the live route actually emits.
  **impact:** `meta.ok.minimal.json` used `animated_build_controls: {}`; 18 drift cases passed while `test_meta_router` (live stub pipeline) still returned `fill_picker` and `select_str.hint` controls that failed strict unions until Static QA expanded the schema.
  **prevention:** For meta/build-control endpoints, require at least one valid drift fixture with a real control per `type` literal from the Python producer (`animated_build_options`) or a checkpoint attestation that route-level integration tests cover every union arm.
  **severity:** high

- **category: architecture**
  **insight:** When mirroring backend unions to Zod/Pydantic, the producer module and one live GET snapshot outrank hand-maintained frontend types that may lag the wire format.
  **impact:** Spec Req 04 cited `src/types/index.ts` `AnimatedBuildControlDef`, which omitted `fill_picker` even though the API and zone-texture integration tests already depended on it; implementation initially matched the stale list.
  **prevention:** Spec and implementation should enumerate `type` literals from `animated_build_options` (or OpenAPI components post–M902-24), then diff against TS types; treat index.ts mismatch as a spec defect, not “frontend-only.”
  **severity:** high

- **category: process**
  **insight:** Ambitious ticket prose (“100% runtime coverage”, “all API response types”) must be collapsed to a pilot table before TEST_DESIGN so gatekeepers do not block on out-of-scope `JSONResponse` routes.
  **impact:** Spec run logged pilot = 3 GET endpoints + Req 12 backlog table (~28 remaining routes); AC Gatekeeper completed without forcing full-router conversion.
  **prevention:** At spec freeze, add explicit “pilot vs deferred” mapping (ticket AC row → spec requirement → verification command); reference Req 12-style tables for all partial-coverage API tickets.
  **severity:** medium

- **category: testing**
  **insight:** Dual-layer validation needs both fixture drift (offline) and route contracts (mocked or stubbed live pipeline) on the same endpoints.
  **impact:** Red phase showed registry invalid manifest returning 200 instead of 500 and missing `models` package; green drift suite alone would not have caught manifest validation ordering without TestClient cases in `test_response_models_pilot.py`.
  **prevention:** Test Designer checklist per pilot route: (1) ≥1 valid + invalid shared fixture, (2) ≥1 TestClient assertion on HTTP status/body shape, (3) for meta, reuse or extend `test_meta_router.py` when controls are discriminated unions.
  **severity:** medium

- **category: infra**
  **insight:** Manual Pydantic↔Zod sync is viable for a pilot when `extra="forbid"` / Zod `.strict()` and a documented README checklist exist; OpenAPI regen (M902-24) is a compile-time backstop, not a substitute for runtime Zod on fetch boundaries.
  **impact:** Delivered `validatedFetch`, `ApiValidationError` user-safe messaging, `scripts/fixtures/dual_validation/`, and sync checklist in frontend README; remaining routes listed in spec Req 12 for a follow-up ticket.
  **prevention:** Follow-up tickets should extend the fixture directory and client wrapper per route cluster, not re-litigate pilot patterns; run `sync-api-types.sh` whenever `response_model` changes.
  **severity:** low

### Anti-Patterns

- **description:** Treating minimal drift fixtures as proof that production meta controls validate end-to-end.
  **detection_signal:** Valid meta fixture has empty `animated_build_controls` while `test_meta_router` asserts non-empty spider/slug/player control lists.
  **prevention:** Add fixture `meta.ok.controls_sample.json` sliced from a recorded GET or built from canonical defs with one arm per `type`.

- **description:** Using stale `AnimatedBuildControlDef` in `types/index.ts` as the union source of truth for backend/Zod mirrors.
  **detection_signal:** Python API or integration tests reference control `type` values absent from Pydantic `Literal` unions.
  **prevention:** Spec lists literals from Python producer first; file follow-up to align OpenAPI/TS types when drift is intentional.

- **description:** Deferring “valid nested control” coverage called out in test-design checkpoint until Static QA or AC gatekeeper.
  **detection_signal:** Test Designer “Spec gaps” section lists missing AnimatedBuildControlDef valid arms; drift suite only tests `{}` or missing `type`.
  **prevention:** Test Breaker or Implementation first PR must close the gap or document explicit waiver with route-test substitute.

### Prompt Patches

- **agent: Spec Agent**
  **change:** "For `AnimatedBuildControlDef`-style unions, list every `type` literal from the Python control producer (`animated_build_options` / router assembly), not only `src/types/index.ts`. If TS types omit a live wire variant, note it as a defect and include that variant in Pydantic/Zod requirements."
  **reason:** Prevents spec-approved schemas that reject real API responses.

- **agent: Test Designer Agent**
  **change:** "For dual-validation pilots: (1) parametrize shared fixtures under `scripts/fixtures/dual_validation/` for both pytest and Vitest; (2) per discriminated-union endpoint, require either a valid fixture with one object per union arm or an existing route test (`test_meta_router`) cited in the handoff; (3) do not rely solely on empty nested objects for valid cases."
  **reason:** Catches fill_picker/hint gaps before Static QA.

- **agent: Implementation Agent (Generalist)**
  **change:** "Before STATIC_QA on web validation tickets: run `pytest tests/test_meta_router.py` and pilot drift tests when `/api/meta/enemies` is in scope; fix union literals before handoff. After adding `response_model`, run M902-24 `sync-api-types.sh` and note output in checkpoint."
  **reason:** Surfaces live-wire union gaps during implementation, not review.

- **agent: Static QA Agent**
  **change:** "When reviewing discriminated unions on live GET routes, diff Pydantic/Zod `type` literals against one successful TestClient GET (stubbed python_root). Flag any control `type` present in JSON but missing from unions as CRITICAL."
  **reason:** Formalizes the fill_picker fix pattern for future pilots.

- **agent: AC Gatekeeper Agent**
  **change:** "If ticket AC claims full API coverage but spec defines a pilot + Req 12 backlog, PASS only when backlog table is cited and pilot trio has fixture + route + frontend client evidence; do not fail on non-pilot `JSONResponse` routes."
  **reason:** Aligns gate with spec-scoped interpretation used at COMPLETE.

### Workflow Improvements

- **issue:** Union completeness was discovered in Static QA via `meta_router` failure, after drift tests were already green.
  **improvement:** Add IMPLEMENTATION → STATIC_QA gate item: “meta pilot: `test_meta_router.py` + drift valid fixture with ≥1 non-empty control map” with checkpoint path evidence.
  **expected_benefit:** Eliminates rework on discriminated unions before review.

- **issue:** Test Designer documented missing valid nested control fixtures but no stage owner closed them before QA.
  **improvement:** Test Break checkpoint must either add the fixture or explicitly assign to Implementation with test name; Implementation handoff cannot cite “deferred to QA.”
  **expected_benefit:** Reduces spec-gap carryover on schema-heavy tickets.

- **issue:** Manual Pydantic/Zod sync without codegen risks recurring literal drift.
  **improvement:** Follow-up ticket should extend Req 12 route table incrementally (registry cluster, then files/assets), each tranche adding drift files + `validatedFetch` wrapper—same checklist as pilot README.
  **expected_benefit:** Predictable expansion without renegotiating pilot scope.

### Keep / Reinforce

- **practice:** Shared `scripts/fixtures/dual_validation/*.json` parametrized in pytest and Vitest—single source for cross-runtime pass/fail.
  **reason:** Proved backend and frontend validators agree on invalid keys, wrong literals, and extra fields.

- **practice:** `ConfigDict(extra="forbid")` on Pydantic response models paired with Zod `.strict()` on mirrored objects.
  **reason:** Catches wire drift at both boundaries with the same failure semantics as fixtures.

- **practice:** Pilot trio + Req 12 explicit backlog table in spec before implementation.
  **reason:** Prevented scope explosion on ~28 remaining `JSONResponse` routes while delivering measurable dual validation.

- **practice:** `client.ts` delegating registry/meta fetch to `validatedFetch` while keeping pre-parse shims out of Zod.
  **reason:** Preserves legacy wire handling without weakening runtime validation on pilot paths.

---

## [M902-26] — OpenAPI contract suite: path ambiguity, hybrid transports, cache symmetry
*Completed: 2026-05-22*

### Learnings

- **category: process**
  **insight:** Ticket AC paths like `tests/api/test_registry_contract.py` must be resolved to the directory `pytest tests/` actually collects before TEST_DESIGN, not at implementation.
  **impact:** Planning assumed `asset_generation/python/tests/api/` so `py-tests.sh` / `run_tests.sh` picked up the suite without a new runner or glob.
  **prevention:** Planner checkpoint records AC path → CI discovery path mapping; spec cites the resolved tree in Req 10/CI evidence.
  **severity:** medium

- **category: architecture**
  **insight:** Not every public route is a JSON document contract—SSE and binary responses need a hybrid policy (jsonschema on event JSON / Tier rules; status + Content-Type + headers only for GLB).
  **impact:** Spec froze SSE happy via `done` event shape + `_run_stream` generator; binary routes skip full body schema validation.
  **prevention:** API contract specs label each endpoint transport class (JSON Tier A/B, SSE, binary) and forbid applying JSON harness helpers to non-JSON bodies.
  **severity:** high

- **category: testing**
  **insight:** OpenAPI-derived jsonschema validation requires inlining nested `$ref` before validate; live `components` alone fail on deeply nested registry/meta responses.
  **impact:** Test Designer added `_inline_all_refs` in harness after MetaEnemiesResponse / ModelRegistryResponse refs blocked validation.
  **prevention:** Contract harness checklist: “refs inlined or bundled schema” as a red-phase gate before per-router modules.
  **severity:** medium

- **category: testing**
  **insight:** Strict bidirectional OpenAPI path-set checks (live ⊆ cache and cache-only paths fail) catch snapshot drift earlier than one-direction subset tests.
  **impact:** Test Breaker added cache symmetry adversarial cases; medium-confidence planning assumption became enforced CI behavior.
  **prevention:** When M902-24 cached OpenAPI is authority, adversarial suite must assert symmetric path keys unless spec documents intentional cache lag.
  **severity:** medium

- **category: testing**
  **insight:** httpx SSE client tests against `sse-starlette` are order-dependent and can bleed event-loop state across the session; generator-based `_run_stream` stays stable.
  **impact:** `test_run_stream_invalid_cmd_error_contract` failed when httpx SSE ran earlier; adversarial SSE coverage moved to `_run_stream` with httpx marked fragile in gaps table.
  **prevention:** Prefer ASGI/generator SSE contract tests; if httpx SSE is kept, isolate session/fixture or document as optional hardening, not baseline CI.
  **severity:** medium

### Anti-Patterns

- **description:** Placing contract tests at repo-root `tests/api/` because ticket AC says so, without verifying `asset_generation/python` pytest roots.
  **detection_signal:** New `tests/api/` at repo root while `py-tests.sh` only runs `cd asset_generation/python && pytest tests/`.
  **prevention:** Planning assumption table maps every AC file path to discovered pytest path; implementation handoff cites `py-tests.sh` line evidence.

- **description:** Running full jsonschema validation on SSE streams or GLB bodies like JSON Tier A routes.
  **detection_signal:** Contract test calls `validate_response` on `text/event-stream` or `model/gltf-binary` without transport branch.
  **prevention:** Spec endpoint freeze table includes transport column; Test Designer splits `test_run_contract` (SSE) vs `test_assets_contract` (binary header-only).

- **description:** Relying on default registry fixtures with empty `player.versions` for DELETE/PATCH player contract cases.
  **detection_signal:** Happy-path registry tests pass but player mutation tests 404/422 on “need ≥2 slotted versions.”
  **prevention:** Document required fixtures in test-design checkpoint (`registry_with_player_version`, confirm text for enemy draft delete).

- **description:** Using httpx SSE integration as the only SSE contract signal in a large shared pytest session.
  **detection_signal:** Single SSE failure after unrelated tests pass; reordering tests changes outcome.
  **prevention:** Generator `_run_stream` for contract + adversarial; httpx SSE only in isolated module or marked experimental.

### Prompt Patches

- **agent: Planner Agent**
  **change:** "For API contract tickets, map each AC test path to the pytest root CI uses (`asset_generation/python/tests/` via `py-tests.sh`). Record the resolved directory in the execution plan before Spec; flag repo-root `tests/` AC lines as WARN."
  **reason:** Prevents suites that never run in canonical CI.

- **agent: Spec Agent**
  **change:** "Endpoint freeze table must include Transport: `json-tier-a`, `json-tier-b`, `sse`, or `binary`. For SSE, specify per-event JSON schema or parser test; for binary, specify status + Content-Type + header assertions only—no full-body jsonschema."
  **reason:** Keeps contract scope aligned with wire reality.

- **agent: Test Designer Agent**
  **change:** "OpenAPI contract harness: require `$ref` inlining (or bundled schema) before jsonschema.validate; list registry/meta fixtures that need non-default manifests (`registry_with_player_version`, enemy draft delete confirm string). Do not use httpx SSE for baseline contract tests—use `_run_stream` or ASGI generator."
  **reason:** Avoids red churn on nested refs, player routes, and flaky SSE ordering.

- **agent: Test Breaker Agent**
  **change:** "Add adversarial OpenAPI cache symmetry (live paths ⊆ cache AND no cache-only paths). For SSE, test malformed/empty/done/log via generator; document httpx SSE fragility if any httpx cases remain."
  **reason:** Catches M902-24 snapshot drift and transport flakiness before implementation handoff.

- **agent: Implementation Agent (Backend)**
  **change:** "Req 11 runbook in `asset_generation/web/backend/AGENTS.md` must state schema authority order (live `app.openapi()`, committed cache, optional live server URL), `pytest tests/api/ -q`, and steps when routes change (regen cache per M902-24). Confirm suite is under `asset_generation/python/tests/api/` collected by `pytest tests/`—no separate CI glob."
  **reason:** Closes runbook gap Test Break flagged; documents CI discovery for future endpoint edits.

### Workflow Improvements

- **issue:** Ticket AC implied a single `test_registry_contract.py` at an ambiguous path while CI collects all of `asset_generation/python/tests/`.
  **improvement:** PLANNING → SPEC gate item: "contract test root path + pytest collect evidence" in checkpoint before test design files land.
  **expected_benefit:** Zero misplaced suites and no duplicate runners.

- **issue:** SSE contract strategy was medium-confidence at planning but httpx fragility surfaced only at TEST_BREAK.
  **improvement:** TEST_DESIGN handoff lists transport per module; TEST_BREAK checkpoint must cite generator vs httpx decision before IMPLEMENTATION marks SSE complete.
  **expected_benefit:** Stable 87-test baseline without order-dependent flakes.

- **issue:** Req 11 runbook was pending while contract code was green—operators could change routes without cache regen steps.
  **improvement:** Block IMPLEMENTATION → STATIC_QA until `AGENTS.md` contract section exists with schema-authority order and links to M902-24/25/26 specs.
  **expected_benefit:** Human and agent edits stay paired with OpenAPI cache updates.

### Keep / Reinforce

- **practice:** Contract layer additive to `tests/web/test_registry_api.py` and backend service tests—no mass deletion of behavioral/delegation coverage.
  **reason:** OpenAPI shape enforcement complements, not replaces, registry delegation and process mocks.

- **practice:** Live OpenAPI + committed cache as dual authority with symmetric path adversarial tests.
  **reason:** Catches both stale cache and undocumented new routes before merge.

- **practice:** Tier A full jsonschema on M902-25 pilot GETs; Tier B anchor `type: object` until `response_model` backlog—explicit deferred boundary in spec and checkpoint.
  **reason:** Delivers full contract CI without blocking on ~28 remaining JSONResponse routes.

- **practice:** 65 → 87 tests after Test Break adversarial module; single `pytest tests/api/ -q` evidence in implementation and static QA checkpoints.
  **reason:** One command proves harness + routers + adversarial closure for gatekeepers.

---

## [M902-27] — Pre-commit hook: delegate sync, glob scope, shell-test mock traps
*Completed: 2026-05-22*

### Learnings

- **category: architecture**
  **insight:** Pre-commit Step 1 must call the existing M902-24 `sync-api-types.sh` pipeline, not duplicate ticket AC `npx openapi-typescript http://localhost:8000/...` — cache fallback, exit codes, and pinned tooling live in one script.
  **impact:** Planning assumed delegation; spec froze it; hook reuses validated behavior instead of a second OpenAPI fetch path.
  **prevention:** For hook tickets that regenerate artifacts, Planner maps each AC bash block to an existing script in `execution_plans/` before Spec; Spec cites script path + exit-code contract, not illustrative curl/npx one-liners.
  **severity:** high

- **category: process**
  **insight:** Lefthook `glob` in ticket AC (`routers/**/*.py`) often under-triggers; OpenAPI surface changes also land in `main.py`, `core/`, and shared response models outside `routers/`.
  **impact:** Planning flagged medium-confidence tradeoff; Spec froze `asset_generation/web/backend/**/*.py`; adversarial **A11** locks glob against routers-only drift.
  **prevention:** PLANNING checkpoint documents “ticket glob vs recommended glob”; Spec exit gate records frozen glob + one-line rationale; Test Break adds YAML glob regression test.
  **severity:** medium

- **category: testing**
  **insight:** CI tests for multi-step bash hooks need PATH stubs that delegate `npx` to the real binary for non-`tsc` invocations — a stub that exits 127 for everything except `tsc` breaks Step 1 `openapi-typescript` while still mocking type-check.
  **impact:** Test Break G2: 12 baseline tests red until stub uses `exec "$(command -v npx)" "$@"`; **A13** guards regression.
  **prevention:** Test Designer documents per-step binaries mocked vs real; Test Break adds adversarial “Step 1 uses real openapi-typescript under PATH stub” before implementation handoff.
  **severity:** high

- **category: testing**
  **insight:** Frozen stderr banners and cache-warning strings are executable contracts — static tests grep the hook script; naive substring rules false-fail on intentional `echo` lines or `#` comments.
  **impact:** G1: H7 failed on `task editor` in Fix echo; G4: A6 failed on `openapi-typescript` in comments; fixes scoped grep to non-comment lines and echo exceptions.
  **prevention:** Spec lists exact stderr literals; Test Break adversarial suite covers “forbidden substring only in echo/comment” and “no backend auto-start” separately from success-path output.
  **severity:** medium

- **category: testing**
  **insight:** Assert warning ordering on `proc.stderr` and script source order, not `stdout + stderr` concat — buffers are not temporal.
  **impact:** H5 cache-fallback test failed until stderr-only check preceded `[2/3]` banner in script text (G3).
  **prevention:** Shell-hook tests document which stream carries each contract line; avoid combined-stream ordering unless the hook explicitly merges streams.
  **severity:** medium

- **category: testing**
  **insight:** Fail-fast between hook steps must be proven in tests (Step 1 failure must not invoke `uv run pytest`) via side-effect markers, not only exit code.
  **impact:** **A9** `uv.marker` file pattern; **A3** blocks before `[1/3]` when `uv` missing (G5, G6).
  **prevention:** Multi-step hook test matrix includes per-step isolation cases in TEST_BREAK before IMPLEMENTATION marks Req 03 complete.
  **severity:** medium

- **category: process**
  **insight:** Manual dry-run matrix (spec Req 07 D1–D5) was deferred past Static QA with only automated 26+87 pytest evidence — operator workflow validation remains unlogged.
  **impact:** Implementation checkpoint notes deferred dry-run; ticket escalation still lists Req 07 for follow-up; merge-ready attestation relied on CI mocks, not live `git commit` rehearsal.
  **prevention:** STATIC_QA handoff requires either `*-dry-run.md` checkpoint with D1–D5 evidence or explicit BLOCKED item on ticket until human/agent dry-run completes.
  **severity:** medium

### Anti-Patterns

- **description:** Implementing ticket AC `npx openapi-typescript` URL fetch inside the hook instead of M902-24 `sync-api-types.sh`.
  **detection_signal:** Hook script contains duplicate curl/OpenAPI URL logic or divergent cache-warning text from sync script.
  **prevention:** Execution plan “Type sync” row points to single script; Spec Req 02 references script path only.

- **description:** Narrow Lefthook glob copied from ticket example (`routers/**`) when schemas/OpenAPI change outside routers.
  **detection_signal:** Backend commit under `core/` or `main.py` does not trigger `api-contract-check`; contract drift merges without pre-commit failure.
  **prevention:** Spec-frozen glob + adversarial YAML parse test (A11).

- **description:** PATH `npx` mock that only succeeds for `tsc`, breaking Step 1 under test.
  **detection_signal:** `openapi-typescript exited non-zero` / exit 127 in H1/H5 while tsc tests pass.
  **prevention:** Delegate non-`tsc` args to real `npx`; add A13-style regression test.

- **description:** Grep-based “no backend start” / “no openapi-typescript in hook” checks without echo/comment exemptions.
  **detection_signal:** Implementation fails H7/A6 despite compliant script with Fix echo or documented comments.
  **prevention:** Test Break documents grep rules in gaps table (G1, G4) before implementation.

- **description:** Marking hook tickets COMPLETE with pytest-only evidence while Req 07 manual dry-run checklist is empty.
  **detection_signal:** No `*-dry-run.md` under ticket checkpoint; escalation notes “deferred to Static QA” with no follow-up artifact.
  **prevention:** AC Gatekeeper requires dry-run checkpoint or open BLOCKED for Req 07.

### Prompt Patches

- **agent: Planner Agent**
  **change:** "For Lefthook/pre-commit tickets: map each AC command to an existing repo script (e.g. M902-24 `sync-api-types.sh`). Record ticket glob vs recommended glob (`routers/**` vs `backend/**`) with confidence. Record pytest cwd for Step 3 (`cd asset_generation/python && uv run pytest tests/api/test_*_contract.py`)."
  **reason:** Prevents duplicate OpenAPI logic and wrong test discovery path in the hook subprocess.

- **agent: Spec Agent**
  **change:** "Freeze: lefthook glob path, `stage: commit`, exact cache-warning stderr (`Backend not reachable; using cached OpenAPI spec`), Step 1 = sync script only (no backend auto-start), Step 3 cwd under `asset_generation/python`. Reference Req 07 dry-run protocol with D1–D5 IDs."
  **reason:** Gives Test Designer/Breaker literal contracts and closes glob ambiguity.

- **agent: Test Designer Agent**
  **change:** "Shell hook tests live under `tests/ci/`; mock PATH per step: real `npx` delegation for `openapi-typescript`, stub `tsc`/`uv`; use `BLOBERT_SYNC_SKIP_FETCH` or cache fixture — no live :8000. Assert stderr for warnings, not stdout+stderr concat."
  **reason:** Avoids red churn from mock traps and flaky live server dependency.

- **agent: Test Breaker Agent**
  **change:** "Adversarial: lefthook YAML glob/run/stage:commit; Step-1 failure must not create pytest side effects (marker file); missing `uv` fails before `[1/3]`; grep rules exempt `#` comments and Fix `echo` lines; PATH npx stub must pass A13 (delegate non-tsc to real npx)."
  **reason:** Captures G1–G7 traps before implementation rework.

- **agent: Implementation Agent (Generalist)**
  **change:** "Hook script: call `sync-api-types.sh`, emit frozen Req 03 banners, never start backend. Lefthook `api-contract-check` on spec glob with `stage: commit`. Runbook in `AGENTS.md` + `CLAUDE.md`. If Req 07 dry-run not run, leave escalation note — do not claim manual workflow validated."
  **reason:** Aligns deliverables with adversarial suite and honest handoff.

### Workflow Improvements

- **issue:** Ticket AC bash blocks are illustrative while canonical behavior lives in prior-milestone scripts.
  **improvement:** PLANNING → SPEC gate: "AC command → existing script path" table mandatory for hook/integration tickets.
  **expected_benefit:** Zero duplicate fetch/cache logic across M902-24 and M902-27.

- **issue:** Test Break grep/mock fixes (G1–G7) indicate Test Designer shell-hook patterns were underspecified.
  **improvement:** TEST_DESIGN handoff includes mock matrix (which steps real vs stub, which stream holds warnings); TEST_BREAK must land adversarial class before IMPLEMENTATION when hook script absent.
  **expected_benefit:** Implementation lands green on first pass (26/26) without grep rework loops.

- **issue:** Req 07 manual dry-run deferred with merge-ready attestation.
  **improvement:** STATIC_QA → LEARNING requires `*-dry-run.md` or ticket BLOCKED line for Req 07; AC Gatekeeper cannot clear workflow validation AC without it.
  **expected_benefit:** Pre-commit hook validated on real `git commit` path, not only mocked subprocess tests.

### Keep / Reinforce

- **practice:** Reuse M902-24 sync + M902-26 contract suite as hook Steps 1 and 3 — no new dependencies.
  **reason:** One pre-commit command enforces the full API contract stack already built in prior tickets.

- **practice:** `tests/ci/test_api_contract_precommit_hook.py` for lefthook + bash (13 → 26 with adversarial); contract tests stay in `asset_generation/python/tests/api/`.
  **reason:** Separates hook orchestration tests from OpenAPI jsonschema suite; 26+87 pytest is dual evidence in implementation/Static QA checkpoints.

- **practice:** Exact stderr templates and “no backend auto-start” as frozen spec requirements tested before script exists (12 RED → green).
  **reason:** TDD caught banner drift and auto-start regressions without live backend.

- **practice:** `pre-commit.parallel: true` guard test (Req 04) alongside new `api-contract-check` command.
  **reason:** M902-28 parallel hooks remain intact when adding another pre-commit command.

---

## [BUG-model-load-ui-settings] — Decouple preview GLB load from sidecar UI import
*Completed: 2026-05-22*

### Learnings

- **category: architecture**
  **insight:** Navigation actions (change preview `activeGlbUrl`) must not implicitly import persisted settings from disk. Coupling preview selection with `hydrateBuildOptionsFromPreviewGlbPath` made every registry/build sync overwrite in-session `animatedBuildOptionValues` and command export fields.
  **impact:** Registry version preview and BuildControls enemy sync reset the editor to the sidecar snapshot (`eye_count` 7 → 2 in regression test) even when the user was only browsing GLBs.
  **prevention:** Store APIs that change preview URL accept an explicit opt-in (`importBuildOptions: true`); default preview path updates URL, clips, and animation reset only. Document preview-only vs open-with-settings call sites in the ticket spec selector table.
  **severity:** high

- **category: architecture**
  **insight:** React component local state that only pushes defaults into a global store on mount/render creates a second source of truth that races async store hydration. CommandPanel `finish`/`hexColor` initialized to `"glossy"`/`""` and effects that wrote local → store could overwrite sidecar-derived `commandExport*` before or after import completed.
  **impact:** Even when import was intentional, users saw glossy/empty command bar while the store briefly held imported values; ColorsPane then copied stale export fields into `feat_*` via `queueMicrotask`.
  **prevention:** For fields owned by the store: initialize local state from `useAppStore.getState()`, subscribe with an effect that syncs store → local when store keys change, and push store updates only from explicit user edits (not mount). Treat import completion as a store event CommandPanel must reflect.
  **severity:** high

- **category: testing**
  **insight:** Regression tests for “preview must not import” should assert the sidecar fetch boundary is never invoked (`fetchBuildOptionsSidecarForGlbPath` not called), not only final store equality — final state can pass while still doing wasteful or racy fetches.
  **impact:** TDD test `BUG-model-load-ui-settings-preview-select-does-not-import-sidecar` failed on `eye_count` before fix and passes with `not.toHaveBeenCalled()` after; gives a stable contract for REQ-1.
  **prevention:** Bugfix frontend tests name the ticket ID, mock the sidecar module, and pair state preservation assertions with “fetch not called” (or dedicated import tests with `importBuildOptions: true` when REQ-2 coverage is in scope).
  **severity:** medium

- **category: process**
  **insight:** One-line bug reports that use “current” without naming the domain (in-session editor state vs on-disk export settings) hide product intent and drive wrong fixes (disable all hydration vs fix CommandPanel only).
  **impact:** Spec Agent logged medium-confidence assumptions: preview = no import; open-existing and post-run auto-select = import. Wrong assumption would have broken post-generation UX.
  **prevention:** Bugfix Spec stage must publish a selector-mode table (preview-only / open+import / post-run import) and one checkpoint resolving “current settings” before Test Designer authors AC tests.
  **severity:** medium

- **category: testing**
  **insight:** Async sidecar import plus ColorsPane `queueMicrotask` hydration is order-sensitive; preview-only fix (REQ-1) does not remove REQ-4 risk on import paths without `act` + awaited import in tests.
  **impact:** REQ-4 and REQ-2 import-path Vitest were deferred; gatekeeper validated REQ-1 + non-regression suites only (10 tests), not full `npm test`.
  **prevention:** When a ticket splits preview vs import, Test Designer lists deferred REQ IDs on the ticket; Implementation or follow-up adds import-path test before claiming REQ-2 AC complete.
  **severity:** medium

### Anti-Patterns

- **description:** Single `selectAssetByPath(path)` that always hydrates from `*.build_options.json` because hydration utility exists.
  **detection_signal:** Any registry preview or enemy-sync call mutates `animatedBuildOptionValues`, `commandExport*`, or `commandContext.cmd` when only the canvas GLB should change.
  **prevention:** Gate hydration behind explicit options; keep `hydrateBuildOptionsFromPreviewGlbPath` as a dedicated import API.

- **description:** Command bar local state with hardcoded defaults and a one-way effect to the store on every render/mount.
  **detection_signal:** After store import sets `commandExportFinish: "metallic"`, UI still shows `"glossy"` until user touches the control; grep for `useState("glossy")` without store subscription.
  **prevention:** Store → local sync effect keyed on `commandExportFinish` / `commandExportHexColor`; push to store only from handlers.

- **description:** Inferring import intent from hidden global state (e.g. “we are in registry preview mode”) instead of the call signature.
  **detection_signal:** Same function behaves differently based on flags set elsewhere; hard to test and easy to regress when adding a new caller.
  **prevention:** Call-site passes `{ importBuildOptions: true }` for open-existing and `refreshAssetsAndAutoSelect` only.

- **description:** Closing a bugfix ticket on targeted Vitest green while implementation remains uncommitted.
  **detection_signal:** WORKFLOW STATE BLOCKED with “commit + push before COMPLETE”; learnings still valid for process.
  **prevention:** AC Gatekeeper re-run after commit; do not move ticket to `done/` until workflow_enforcement commit gate passes.

### Prompt Patches

- **agent: Bugfix / Spec Agent**
  **change:** "For editor UI bugs involving load/preview/open: define three modes in the spec — (1) preview-only URL, (2) explicit import from sidecar, (3) user edit — with a call-site table. Resolve ambiguous words like ‘current’ in one checkpoint (in-session vs on-disk). Do not freeze spec until preview vs import boundaries are explicit."
  **reason:** Prevents shipping the wrong interpretation of vague bug reports.

- **agent: Implementation Frontend Agent**
  **change:** "When fixing store+React dual state: list every consumer that reads/writes the same fields (store, CommandPanel, ColorsPane). Preview navigation must not call sidecar fetch unless `importBuildOptions: true`. CommandPanel: initialize from store, sync store→local on `commandExport*` change, write store only on user input."
  **reason:** Addresses the actual failure chain (hydrate + one-way local state + Colors microtask).

- **agent: Test Designer Agent**
  **change:** "For ‘must not import on preview’ AC: mock `fetchBuildOptionsSidecarForGlbPath` and assert `not.toHaveBeenCalled()` in addition to preserved `animatedBuildOptionValues` and `commandExport*`. Name test id `BUG-<ticket>-preview-select-does-not-import-sidecar`. Run failing test before implementation handoff."
  **reason:** Encodes REQ-1 at the IO boundary, not only post-hoc state.

- **agent: Acceptance Criteria Gatekeeper**
  **change:** "For split preview/import requirements: verify explicit flag at call sites (grep `importBuildOptions`) and that deferred REQ ACs are listed as open items — do not mark REQ-2 complete without import-path tests if ticket claims full REQ-2 coverage."
  **reason:** This ticket passed REQ-1 with wiring-only evidence for REQ-2.

### Workflow Improvements

- **issue:** Bugfix pipeline advanced Test Designer → Implementation Frontend without `test_design_to_test_break` handoff validation (orchestrator override).
  **improvement:** For frontend store contract bugs, still run Test Breaker on the new regression file or document waiver in checkpoint; minimum: adversarial case “preview call with mocked sidecar must not invoke fetch.”
  **expected_benefit:** Catches weak assertions (state-only) before implementation.

- **issue:** Full `npm test` failures (16 across unrelated files) noted at test-design time but not gated on ticket closure.
  **improvement:** Ticket WORKFLOW STATE records “targeted suite” vs “full frontend suite” scope; gatekeeper uses the frozen list from spec REQ-5.
  **expected_benefit:** Avoids false confidence from unrelated red suites while keeping REQ-5.3 explicit.

- **issue:** COMPLETE blocked on uncommitted implementation despite behavioral AC met.
  **improvement:** Learning extraction can run at gatekeeper BLOCKED; append learnings with status note; Implementation agent commits before ticket moves to `bugfix/done/`.
  **expected_benefit:** Insights captured without skipping commit discipline.

### Keep / Reinforce

- **practice:** Explicit `selectAssetByPath(path, { importBuildOptions: true })` at post-run auto-select and load-existing open only; registry preview stays preview-only.
  **reason:** Makes intent visible in code review and grepable for gatekeeper.

- **practice:** RED regression test with ticket-prefixed id and verbatim fail output in checkpoint before implementation.
  **reason:** Proved `eye_count` 7→2 failure; implementation fix was narrowly scoped.

- **practice:** Mermaid sequence diagram in bugfix diagnosis linking store, sidecar fetch, CommandPanel, and ColorsPane.
  **reason:** Surfaced race ordering for implementers without re-auditing every call site.

- **practice:** Targeted Vitest bundle for gatekeeper (`previewOnly` + `BuildControls.previewSync` + `ColorsPane`) when full suite has unrelated debt.
  **reason:** 10/10 passed on fix; scoped evidence documented in WORKFLOW STATE.

---

## [STUDIO-01] — Studio shell scoped green; full-suite AC and git closure blocked COMPLETE
*Status: INTEGRATION (2026-05-23) — AC-1..AC-6 met; AC-7 full `npm test -- --run` red (14 failures, 3 files); implementation uncommitted on dirty branch*

### Learnings

- **category: process**
  **insight:** Frontend tickets that list both ticket-scoped Vitest files and AC-7 “full `npm test -- --run`” need an explicit validation split in WORKFLOW STATE: scoped evidence vs full-suite gate. Scoped green (e.g. 34/34 `StudioLayout` + 4/4 `ThreePanelLayout`) does not satisfy AC-7 when parallel branch work leaves unrelated files red.
  **impact:** AC Gatekeeper held at INTEGRATION despite complete Phase 1 shell; 14 failures in `BuildControlRow.concurrency`, `BuildControls.texture`, and `ImageMode` (e.g. `onFileChange` arity mismatch) were outside STUDIO-01 paths.
  **prevention:** At SPEC or TEST_DESIGN freeze, record a “full-suite baseline” command output on the branch (pass/fail file list). Gatekeeper marks AC-7 Met only after full suite green or Human waiver with pre-existing-failure inventory dated before implementation started.
  **severity:** high

- **category: process**
  **insight:** Implementation → Static QA handoff checklists must not attest “all tests passing” when evidence is only a scoped `npm test <paths>` run. Overstated handoff (`impl_tests_passing` / AC-7 green) delays discovery until AC Gatekeeper re-runs the full suite.
  **impact:** `handoff-latest.yaml` claimed AC-7 green while checkpoint showed scoped runs only; gatekeeper re-run exposed the gap.
  **prevention:** Handoff evidence_type must name exact commands; Static QA rejects attestation unless checkpoint includes verbatim `npm test -- --run` summary or ticket AC explicitly allows scoped-only closure.
  **severity:** medium

- **category: testing**
  **insight:** Feature-flag layout tickets benefit from an adversarial env matrix: only exact `VITE_* === "1"` enables the new shell; trim, booleans, padded strings, and `vi.resetModules` toggle tests prevent accidental loose parsing.
  **impact:** Test Breaker added 24+ invalid-flag cases; implementation used strict `isStudioLayoutEnabled()` and stayed aligned with spec §11 without product debate at implementation time.
  **prevention:** Spec §11 should freeze strict equality; Test Designer includes `it.each` invalid values + module reset; Implementation must not add trim/coerce unless spec changes.
  **severity:** medium

- **category: architecture**
  **insight:** Parallel layout introductions (legacy + feature-flagged shell) need paired positive/negative mount tests: new subtree mounts preview stack; explicitly omits deferred UI (CommandPanel, Terminal) with dedicated testids absent under `studio-layout`.
  **impact:** Spec freeze added T-6 after planner ambiguity; prevented Phase 1 scope creep into command/terminal wiring deferred to STUDIO-02+.
  **prevention:** When legacy layout includes widgets the new shell defers, add FR + Vitest “absence under flag on” before implementation, not only “presence” tests for new components.
  **severity:** medium

- **category: testing**
  **insight:** New layout code on branches with preview/hydration invariants should assert IO boundaries (no `selectAssetByPath({ importBuildOptions: true })`, no sidecar fetch on mount/tab cycle), not only final store shape — same pattern as preview-only bugfixes but applied to greenfield mount trees.
  **impact:** STUDIO-01 T-5/T-5 adversarial cases passed; scoped suite proved Studio subtree does not reintroduce implicit import on navigation.
  **prevention:** Test Designer lists hydration spies for every new layout entry point; Test Breaker adds tab-cycle and App-integration cases.
  **severity:** medium

### Anti-Patterns

- **description:** Treating scoped Vitest green as proof of AC-7 when the ticket AC names full `npm test -- --run`.
  **detection_signal:** WORKFLOW STATE cites only `StudioLayout.test.tsx` paths; gatekeeper full run shows failures in unrelated `src/components/**` files.
  **prevention:** Split AC-7 evidence lines in Validation Status; gatekeeper runs full suite before COMPLETE.

- **description:** Handoff checklist attestation without matching checkpoint command output.
  **detection_signal:** `impl_tests_passing: complete` but no `Test Files X passed (Y)` block from `npm test -- --run`.
  **prevention:** Handoff validator compares attestation strings to checkpoint verbatim blocks.

- **description:** Shipping or closing a ticket on a dirty branch with unrelated frontend WIP when workflow requires commit + push of implementation paths.
  **detection_signal:** `git status` shows STUDIO-01 files mixed with other modified frontend tests; gatekeeper notes uncommitted shell paths.
  **prevention:** Human triage: fix unrelated reds, stash/cherry-pick, or split commits; re-run gatekeeper after isolated STUDIO-01 commit.

- **description:** Locking visual token shape in tests (`#RRGGBB` hex) when spec only requires non-empty color strings.
  **detection_signal:** Test Breaker `# CHECKPOINT` comments on `soft` blend math; spec silent on rgba vs hex.
  **prevention:** Spec Agent freezes token representation in one checkpoint before Test Breaker hardens assertions.

### Prompt Patches

- **agent: Spec Agent**
  **change:** "For frontend layout tickets with AC-7 full-suite requirement: add Validation Scope table — (1) scoped test file list for implementation sign-off, (2) full `npm test -- --run` for gatekeeper COMPLETE. If branch may carry unrelated WIP, require Human to record pre-existing failure file list in ticket Blocking Issues before IMPLEMENTATION."
  **reason:** Prevents false confidence from scoped-only green and clarifies INTEGRATION vs COMPLETE.

- **agent: Implementation Frontend Agent**
  **change:** "Checkpoint test evidence must list exact commands. If AC-7 requires full suite, run `npm test -- --run` before Static QA handoff; if red, document failing file paths and do not attest AC-7 complete. For `VITE_*` flags use strict `=== '1'` unless spec says otherwise."
  **reason:** Fixes handoff overstatement and matches §11 adversarial contract.

- **agent: Test Designer Agent**
  **change:** "Greenfield layout tickets: T-1 legacy testid when flag off; T-2 grid/preview when flag on; T-6 absence tests for widgets deferred to later phases; T-5 hydration — spy `selectAssetByPath` and sidecar fetch, assert no `importBuildOptions: true` on Studio mount and tab interactions."
  **reason:** STUDIO-01 traceability map (T-1..T-6) caught scope and hydration regressions early.

- **agent: Acceptance Criteria Gatekeeper**
  **change:** "When scoped tests pass but full `npm test -- --run` fails: set Stage INTEGRATION (not COMPLETE), list failing files verbatim, state whether failures touch ticket change surface. Do not move to `done/` until AC-7 green AND commit/push per workflow_enforcement. Extract learnings allowed at INTEGRATION."
  **reason:** Matches STUDIO-01 outcome; separates deliverable quality from branch hygiene.

### Workflow Improvements

- **issue:** Single AC-7 line conflates implementation confidence (scoped) with release gate (full suite).
  **improvement:** Split into AC-7a (scoped files from spec §8) and AC-7b (full frontend suite), or reference NFR with explicit gatekeeper-only full run.
  **expected_benefit:** Implementation and Static QA can complete with scoped evidence; gatekeeper failure mode is predictable.

- **issue:** Learning stage scheduled only after COMPLETE though insights are available when gatekeeper blocks on unrelated suite debt.
  **improvement:** Allow Learning Agent at INTEGRATION with status note; Human fixes suite/commit; gatekeeper re-run for COMPLETE without re-running full pipeline.
  **expected_benefit:** Captures process lessons (handoff, suite scope) without skipping commit discipline.

- **issue:** Milestone pre-authored spec + greenfield components — planner assumed CommandPanel in studio center until spec freeze.
  **improvement:** PLANNING checkpoint must resolve “legacy-only vs new-shell” widget parity in one table; Spec Agent confirms before TEST_DESIGN.
  **expected_benefit:** Avoids mid-pipeline T-6 addition and rework on center-column scope.

### Keep / Reinforce

- **practice:** Validate existing `project_board/specs/studio_editor_redesign_spec.md` (§6–§9) instead of duplicating a new spec file when milestone spec is pre-authored.
  **reason:** Spec exit gate PASS with FR/NFR/T traceability; Spec Agent focused on freeze decisions (CommandPanel omission, strict flag).

- **practice:** `bot_vault/.../studio.jsx` and `shared.jsx` as design-time IA/color reference only — production code follows `RegistryTagChips` / `ThreePanelLayout` patterns (`CSSProperties`, Zustand, Vitest).
  **reason:** Avoided 1:1 port of prototype globals and kept preview stack parity via reused components.

- **practice:** Adversarial Test Breaker matrix (invalid flags, hydration, lowercase inspector tab ids, single visible panel) before implementation.
  **reason:** 34-case `StudioLayout.test.tsx` stayed green through implementation without flag-parsing rework.

- **practice:** `data-testid="legacy-layout"` on `ThreePanelLayout` plus `studio-layout` when flag on — explicit regression hooks for dual-layout era.
  **reason:** AC-1 regression guard stayed green alongside new shell tests.

---

## [M11-01] — Player FSM scoped green; full `run_tests.sh` and push block COMPLETE
*Status: INTEGRATION (2026-05-23) — 7/8 AC met; FSM 40+229 PASS; `run_tests.sh` exit 1 (18 unrelated Godot failures); push pending*

### Learnings

- **category: process**
  **insight:** Refactor tickets that add a scoped Godot contract suite (`test_player_state_machine*.gd`) still list global AC `run_tests.sh` exits 0. Scoped green (269/269 FSM) does not satisfy branch closure when unrelated suites (UI indicators, test harness smoke) are red.
  **impact:** AC Gatekeeper held INTEGRATION despite committed FSM deliverable; 18 failures in `test_enemy_status_effect_indicators*.gd` (15) and `test_utils_*` (3) had zero references to player paths.
  **prevention:** At SPEC freeze, add Validation Scope: (1) ticket-scoped Godot paths + command for implementation sign-off, (2) full `ci/scripts/run_tests.sh` for gatekeeper COMPLETE. Record pre-existing failure file list in Blocking Issues before IMPLEMENTATION when branch carries WIP.
  **severity:** high

- **category: architecture**
  **insight:** Kinematic state (`MovementSimulation.MovementState`) and gameplay state (`PlayerStateMachine.PlayerState`) must stay in separate types/modules with explicit derivation priority (DEAD > HURT > ABSORB > … > kinematic). Conflating names or enums causes silent wrong gating for M11 attacks.
  **impact:** Planner flagged MovementState trap; spec froze dual layer; Test Breaker `ADV-001` asserts `MovementSimulation` does not define `PlayerState`; implementation kept derivation in `PlayerStateDerivationContext` DTO.
  **prevention:** Spec Agent documents both layers in one table; Test Breaker adds naming-isolation test before implementation; Gameplay Systems Agent never aliases enums across layers.
  **severity:** high

- **category: testing**
  **insight:** Isolation tests for guarded states (e.g. FLOAT, HURT) must reach the state via spec-legal entry paths (JUMP + `MIN_FLOAT_FROM_JUMP_SEC`, `notify_damage_taken`), not shortcuts that bypass guards — otherwise implementation “fixes” violate G-FLOAT/G-HURT.
  **impact:** Implementation adjusted `test_ec6_same_state_noop_all_states` to enter FLOAT via JUMP + timer after initial adversarial RED assumptions.
  **prevention:** Test Designer links each guarded-state test to spec transition row; Implementation Agent rejects test changes that weaken guards unless spec checkpoint resolves ambiguity.
  **severity:** medium

- **category: testing**
  **insight:** Adversarial EC-1..EC-10 matrix before implementation (229 tests) plus primary PSM-1..PSM-9 (40 tests) gave high confidence for behavior-preserving refactor; controller wiring (PSM-10) relied on static QA + full suite, not duplicate FSM unit coverage.
  **impact:** No player-controller failures in full Godot run; large adversarial suite caught HURT re-entry, DEAD terminal, epsilon boundaries, and `can_transition_to` ↔ `transition` consistency without manual playtest.
  **prevention:** For explicit FSM extractions: unit + adversarial EC table in TEST_BREAK; defer integration tests unless spec mandates observable controller wiring beyond FSM API.
  **severity:** medium

- **category: infra**
  **insight:** Godot runner counts every `FAIL:` line in `test_utils_*` adversarial/smoke files as suite failures. Intentional failure probes in harness tests block `run_tests.sh` even when product code under test is correct.
  **impact:** 3 of 18 gatekeeper failures were harness self-tests, not gameplay regressions — same class of debt as unrelated UI indicator tests.
  **prevention:** AC Gatekeeper buckets failures by path prefix; Bugfix/harness tickets exclude intentional-fail files from `run_tests.gd` discovery or gate them behind env flag. Do not attribute harness red to feature tickets in Escalation Notes.
  **severity:** medium

### Anti-Patterns

- **description:** Closing or attesting “all tests passing” from scoped FSM runs when ticket AC names full `run_tests.sh`.
  **detection_signal:** WORKFLOW STATE cites 40/40 + 229/229 only; gatekeeper full run shows reds in `tests/ui/` or `tests/scripts/test_utils_*`.
  **prevention:** Split Validation Status into scoped PASS vs full-suite gate; gatekeeper runs `timeout 300 ci/scripts/run_tests.sh` before COMPLETE.

- **description:** Routing FSM implementation rework when full suite fails on unrelated UI indicator tests.
  **detection_signal:** Failure messages reference `EnemyStatusEffectIndicators`, not `player_state_machine` or `player_controller_3d`.
  **prevention:** Gatekeeper supplies `failure_buckets` JSON (as M11-01 NEXT ACTION); Bugfix Agent owns branch health, Gameplay Systems owns scoped regression only.

- **description:** Entering FLOAT/HURT in tests via illegal transitions to make isolation tests shorter.
  **detection_signal:** Test expects `transition(FLOAT)` from IDLE without JUMP/timer; or `HURT→HURT` without re-entry guard.
  **prevention:** Map each test to spec guard ID (G-FLOAT, G-HURT); Test Breaker encodes conservative denial per EC table.

### Prompt Patches

- **agent: Spec Agent**
  **change:** "For gameplay FSM refactors: freeze (1) enum separate from any kinematic/movement enum, (2) derivation priority table, (3) which states are explicit-only vs derived (e.g. FLOAT not from `compute_derived_state`), (4) Validation Scope — scoped test paths vs full `run_tests.sh`. Reference `enemy_state_machine.gd` patterns but do not merge enums."
  **reason:** M11-01 dual-layer and FLOAT explicit-only decisions prevented M1 behavior drift and naming traps.

- **agent: Test Breaker Agent**
  **change:** "FSM tickets: implement spec Edge Cases EC-1..EC-n as named `test_ecN_*` before implementation; add ADV naming test ensuring movement/kinematic module does not export gameplay enum; for MIN_*_SEC gates use epsilon `MIN - 1e-6` adversarial cases."
  **reason:** 229-test adversarial suite was the regression contract while branch suite was red.

- **agent: Gameplay Systems Agent**
  **change:** "Evaluate `can_transition_to` guards before same-state no-op; document hurt latch (`_hurt_pending`, `_hurt_reentry_blocked`) in checkpoint when EC-2 tests exist. Wire controller: single `update(delta)` per physics frame, `sync_from_context` after `move_and_slide`. Do not attest full-suite green without `run_tests.sh` log excerpt."
  **reason:** Implementation ordering matched adversarial HURT/EC-6 findings; handoff honesty avoids false COMPLETE.

- **agent: Acceptance Criteria Gatekeeper**
  **change:** "When scoped ticket tests pass but `run_tests.sh` fails: Stage INTEGRATION; list failing files verbatim; confirm zero failures touch ticket change surface; route Bugfix with `failure_buckets`; note push-ahead-of-origin separately. Allow Learning at INTEGRATION."
  **reason:** M11-01 outcome — deliverable complete, branch hygiene separate.

### Workflow Improvements

- **issue:** Single AC line `run_tests.sh` exits 0 conflates feature contract (FSM suites) with branch health (UI + harness).
  **improvement:** Split AC into scoped Godot paths (from spec §Test Strategy) and full-suite gatekeeper-only row; optional `m11_01_regression_command` in NEXT ACTION schema for re-verify after bugfix.
  **expected_benefit:** Implementation/Static QA can finish with 269/269 evidence; gatekeeper failure mode is predictable.

- **issue:** Learning scheduled only after COMPLETE though gatekeeper already documented failure buckets and dual validation split.
  **improvement:** Run Learning at INTEGRATION when scoped evidence is complete; append LEARNINGS; Bugfix clears branch suite; gatekeeper re-run for COMPLETE without re-spec/implement.
  **expected_benefit:** Captures FSM/dual-layer lessons while suite debt is fresh (same pattern as STUDIO-01).

- **issue:** `test_utils` adversarial files pollute global failure count.
  **improvement:** Track harness intentional-fail policy in milestone hygiene ticket; gatekeeper excludes known harness paths from 'blocks feature AC' unless ticket touches `tests/utils/`.
  **expected_benefit:** Reduces false routing of gameplay agents to fix runner semantics.

### Keep / Reinforce

- **practice:** RefCounted FSM + `PlayerStateDerivationContext` snapshot DTO — no Node/Input in machine module; controller owns sync after physics.
  **reason:** Static QA PASS; clear PSM-10 wiring boundary for M11-02 frame order.

- **practice:** Spec path `project_board/specs/player_state_machine_spec.md` with generic spec exit; planner path superseded by repo convention.
  **reason:** Spec completeness PASS; 110+ spec corpus consistency.

- **practice:** Behavior-preserving constants frozen in spec (`MIN_FLOAT_FROM_JUMP_SEC = 0.05`, `MIN_HURT_SEC = 0.0`, `VERTICAL_JUMP_EPSILON`) with matching PSM-6/ADV epsilon tests.
  **reason:** Adversarial boundaries caught vy threshold without changing M1 feel.

- **practice:** AC Gatekeeper failure bucketing and NEXT ACTION JSON (`failure_buckets`, `verify_command`, scoped regression command).
  **reason:** Unblocks Bugfix Agent without reopening FSM implementation.

---

## [M11-02] — Physics frame order: buffer landing, coyote ownership, one-way mask pipeline
*Completed: 2026-05-23*

### Learnings

- **category: architecture**
  **insight:** Jump buffer and coyote time are orthogonal timers with different consume sites: buffer arms in controller Step 2 and consumes on first grounded frame; coyote decrements inside `MovementSimulation.simulate()`. `jump_pressed` (hold) stays raw for jump-cut; only `jump_just_pressed` is augmented by buffer (PFO-5).
  **impact:** Conflating both timers in controller Step 2 would duplicate M1 coyote math and break sim test authority; mixing hold into buffer would break jump-cut (SPEC-20).
  **prevention:** Spec must freeze timer ownership table (controller vs sim) before implementation; buffer tests that need pure buffer behavior must expire coyote first (`_arm_jump_buffer_after_coyote`).
  **severity:** high

- **category: architecture**
  **insight:** Landing buffer consume cannot run entirely in pre-slide dispatch: `is_on_floor()` for a mid-air→ground transition is unknowable until after `move_and_slide()`. Post-slide Step 8 must re-dispatch with `effective_jump_just_pressed` when `landed_this_frame && _jump_buffer_pending_at_frame_start`.
  **impact:** Step-4-only buffer consume misses EC-1 (press in air, land within 0.1s → jump on landing); TB-PFO-002 fails if Step 2 decrement clears timer before post-slide can read pending state.
  **prevention:** Snapshot `_jump_buffer_pending_at_frame_start` at Step 0 (before Step 2 decrement); document dual consume paths (pre-slide grounded vs post-slide landing) in spec PFO-5/EC-1.
  **severity:** high

- **category: testing**
  **insight:** CharacterBody3D integration tests stay deterministic by calling `player._physics_process(PHYSICS_STEP)` directly, syncing both `player.velocity` and `_current_state.velocity` (2D sim mirror), and splitting input helpers: `_step_player` releases jump after tick; `_step_player_preserve_jump` keeps jump held for ascent/jump-cut/one-way pass-through tests.
  **impact:** Without dual velocity sync, landing/buffer setup drifts; releasing jump in `_release_all_input()` breaks buffer arm tests; auto jump-cut during ascent causes false one-way stall failures.
  **prevention:** PFO harness checklist: settle 90 frames → `_set_controller_velocity` for both layers → coyote-expire N frames before buffer arm → preserve-jump variant for ascending scenarios.
  **severity:** medium

- **category: architecture**
  **insight:** One-way collision mask must use post-dispatch `velocity.y` and apply every frame after simulate, strictly before `move_and_slide()`. Ascending (`vy > 0`) or airborne apex (`vy == 0` and not on floor) excludes one-way bit; grounded or falling includes it.
  **impact:** Mask-after-slide causes upward stall at platform lip (TB-PFO-012); mask-only-on-jump-frame leaves one-way enabled mid-ascent (TB-PFO-009); strict `vy > 0` alone fails apex pass-through.
  **prevention:** Freeze Step 5→7 ordering in spec; adversarial tests assert mask every ascending frame and stall detection below one-way lip; expose `get_one_way_collision_mask()` for behavioral asserts only.
  **severity:** high

- **category: testing**
  **insight:** Coyote + buffer combinatorial cases (EC-11) require sim `jump_consumed` as the single-jump gate: coyote jump in air must not re-fire via buffer on landing (TB-PFO-006); double air-press must not reset buffer into multiple landing jumps (TB-PFO-007).
  **impact:** Without explicit EC-11 adversarial tests, buffer landing polish reintroduces double-jump on walk-off + late press sequences.
  **prevention:** Test Breaker must add coyote+buffer and double-press landing cases whenever buffer is added to a sim that already owns coyote.
  **severity:** medium

### Anti-Patterns

- **description:** Buffer consume only in pre-slide `_dispatch_movement` using `is_on_floor()` from prior frame — misses first landing frame where floor contact resolves in Step 7.
  **detection_signal:** EC-1/TB-PFO-002 fail; player lands without upward impulse despite pending buffer; timer hits zero on landing frame before consume.
  **prevention:** Dual-path consume: pre-slide for already-grounded; post-slide re-simulate on `landed_this_frame` with Step-0 pending snapshot.

- **description:** Coyote and jump buffer both decremented or armed in controller Step 2.
  **detection_signal:** M1 sim coyote tests diverge; controller tests pass but `test_jump_simulation*.gd` regress; duplicate timer logic in two modules.
  **prevention:** Spec ownership table: coyote in sim only; controller mirrors export and passes `prior_state.is_on_floor` at frame start.

- **description:** One-way mask updated after `move_and_slide()` or only on the jump initiation frame.
  **detection_signal:** TB-PFO-009/TB-PFO-012 stall or fail pass-through; player hangs below one-way lip with positive vy.
  **prevention:** Step 5 mask from post-dispatch velocity; assert mask each ascending tick in adversarial suite.

- **description:** Test harness releases jump in generic input cleanup, breaking buffer arm and jump-cut scenarios.
  **detection_signal:** Buffer tests flaky or never arm; ascending one-way tests show premature velocity clamp.
  **prevention:** Separate `_step_player` (release jump) vs `_step_player_preserve_jump` (hold through tick); `_release_all_input` omits jump release.

### Prompt Patches

- **agent: Spec Agent**
  **change:** "For controller physics-frame tickets: freeze (1) numbered step pipeline with pre/post-slide boundaries, (2) timer ownership table (controller vs sim), (3) effective-input contract (`jump_just_pressed` buffered, `jump_pressed` raw for jump-cut), (4) post-slide unknowable state list (landing, `is_on_floor`), (5) collision-mask step relative to dispatch and `move_and_slide`. Include EC table for buffer+coyote interaction (EC-11)."
  **reason:** M11-02 rework risk was frame-boundary ambiguity, not missing features.

- **agent: Test Designer Agent**
  **change:** "CharacterBody3D harness: load `test_movement_3d.tscn` sandbox; call `_physics_process` directly; sync `velocity` AND `_current_state.velocity`; `_settle_on_floor` before behavioral asserts; `_arm_jump_buffer_after_coyote` before buffer-landing tests; `_step_player_preserve_jump` for ascent/jump-cut. Assert runtime behavior only (position, vy, mask, `is_on_floor`) — no call-order logging."
  **reason:** Primary PFO suite patterns were the implementation contract; settle failures in RED phase resolved post-refactor.

- **agent: Test Breaker Agent**
  **change:** "Physics-frame tickets: add boundary tests for timer expiry one frame before/after 0.1s (frame-count at 60 Hz); mask flip at vy==0 apex; reorder regression (mask before slide); coyote+buffer single-jump (EC-11); double air-press buffer reset. Mark frame-count vs wall-clock assumptions with `# CHECKPOINT`."
  **reason:** 28 adversarial tests caught landing-frame boundary and mask-order bugs pre-merge.

- **agent: Gameplay Systems Agent**
  **change:** "When buffer must fire on landing: snapshot pending at frame start; post-slide consume via re-dispatch if `landed_this_frame`. Do not move coyote decrement to controller. One-way mask: post-dispatch velocity, before slide; treat airborne vy==0 as ascending. Do not claim COMPLETE without scoped PFO suite log; route INTEGRATION if branch `run_tests.sh` has unrelated failures."
  **reason:** Implementation checkpoint documented Step-0 snapshot decision that fixed TB-PFO-002.

### Workflow Improvements

- **issue:** Spec PFO-5 initially described buffer consume only in Step 4; landing frame requires post-slide path discovered during implementation.
  **improvement:** Spec exit gate for physics-frame specs: require explicit 'unknowable until post-slide' state list and dual consume paths for any input buffer tied to collision resolution.
  **expected_benefit:** Test Designer writes EC-1 landing tests against frozen contract; fewer implementation checkpoints on frame boundaries.

- **issue:** One-way layer bits were greenfield (`project.godot` had no layer names); tests needed fixture scene + runtime box spawn.
  **improvement:** Planner/spec checklist for collision features: declare bit map, baseline player mask, headless fixture path, and test accessor policy in same spec section (PFO-6 + PFO-7 + PFO-11).
  **expected_benefit:** Avoids split deliverables across implementation Tasks 4–5.

- **issue:** Learning ran at INTEGRATION (scoped 43/43 green, branch 4 unrelated failures) — same pattern as M11-01.
  **improvement:** Reinforce INTEGRATION-stage Learning when scoped spec paths pass; gatekeeper re-run for COMPLETE after branch hygiene.
  **expected_benefit:** Frame-order lessons captured while buffer/mask decisions are fresh.

### Keep / Reinforce

- **practice:** 10-step PFO-2 pipeline with in-code step comments matching spec numbers; private methods `_tick_controller_timers`, `_dispatch_movement`, `_update_one_way_collision_mask`, `_sync_renderer_from_state`.
  **reason:** Behavioral tests (PFO-10) enforce structure without fragile call-order mocks.

- **practice:** Coyote remains sim-authoritative; controller adds net-new buffer only — M1 `test_jump_simulation*.gd` unchanged.
  **reason:** Preserves movement feel while adding controller-boundary polish.

- **practice:** Adversarial matrix TB-PFO-001..012 covering expiry boundaries, EC-10 suppression, mask sustained ascending, reorder stall detection.
  **reason:** 43/43 scoped pass was regression contract while branch suite had unrelated debt.

- **practice:** `get_one_way_collision_mask()` test-only accessor for deterministic mask asserts separate from gameplay API surface.
  **reason:** Enables PFO-7 tests without exposing mask internals to production callers.

---

## [M11-06] — Fill-order semantics, handoff schema drift, and controller line-budget exhaustion
*Completed: 2026-05-25*

### Learnings

- **category: testing**
  **insight:** Tests that manipulate ordered-slot systems (like `MutationSlotManager.fill_next_available`) must account for deterministic fill order. Clearing "slot 0" after a single fill empties the only occupied slot, not "the other slot." Test authors who intend to test slot-B-only states must fill both slots first, then clear the one they want empty.
  **impact:** EC-20 adversarial test (`slot_b_fires_base_attack`) filled one slot and cleared index 0 — both slots ended up empty. The implementation agent correctly diagnosed this as a test setup bug (not an implementation bug), but didn't fix it, causing a 156/157 pass rate that required orchestrator intervention.
  **prevention:** Test Breaker Agent should include a "slot state assertion" immediately after setup for any test that targets a specific slot configuration. For multi-slot systems, always assert the intended pre-condition (e.g., `assert_true(msm.is_slot_filled(1))`) before exercising the behavior under test.
  **severity:** medium

- **category: process**
  **insight:** Handoff gate artifacts (`handoff-latest.yaml`, `todos-latest.json`) are consistently produced with incorrect schemas by subagents. Across M11-04, M11-05, and M11-06, every subagent wrote artifacts with missing `schema_version`, wrong field names (`description` instead of `content`, `complete` instead of `completed`), missing `captured_at`, missing root `handoff:` key, or wrong checklist item keys. The orchestrator manually fixed every one.
  **impact:** Cumulative orchestrator tax: 3+ tickets × 5+ agents per ticket = 15+ manual artifact fixes. This is a recurring time sink that compounds as tickets increase.
  **prevention:** Provide a validated YAML/JSON template in the agent prompt (not just a schema reference). Alternatively, implement a deterministic script that generates these artifacts from structured input (ticket_id, stage, checklist items) so agents never handwrite them.
  **severity:** high

- **category: architecture**
  **insight:** Godot 4.6 prevents `class_name X` on scripts registered as autoload `X` — the parser raises `Class "X" hides an autoload singleton`. When the gd-organization hook requires `class_name`, the only workaround is a suffix pattern like `class_name XNode`.
  **impact:** Implementation agent had to discover and resolve this at implementation time. The spec and planner did not anticipate the `class_name` vs autoload naming conflict.
  **prevention:** Planner Agent should flag any new autoload deliverable and include a note: "Godot 4.6 autoload naming: use `class_name <Name>Node` to avoid parser collision with autoload singleton `<Name>`."
  **severity:** low

- **category: architecture**
  **insight:** `PlayerController3D` reached exactly 900 lines (the `gd-organization` limit) after M11-06 wiring. Any future additions will trigger the lint gate and require an extraction refactor.
  **impact:** No immediate failure, but the next ticket touching `PlayerController3D` (M11 attack states, charge-up, etc.) will be blocked by line-count enforcement unless the file is refactored first.
  **prevention:** When a core file is within 10% of the organization line limit after implementation, create a follow-up refactor ticket immediately. For `PlayerController3D`, extract attack pipeline methods (`_try_attack`, cooldown management, attack input handling) into a dedicated helper class or child node before the next M11 ticket begins.
  **severity:** medium

### Anti-Patterns

- **description:** Test Breaker writes a slot-manipulation test without asserting the slot state after setup, relying on implicit understanding of fill order.
  **detection_signal:** Any adversarial test that calls `fill_next_available` followed by `clear_slot(index)` without an assertion between them confirming the intended slot configuration.
  **prevention:** Require a "state assertion barrier" pattern in slot tests: `fill → assert intended state → act → assert behavior`. Add this as a Test Breaker prompt instruction for ordered-collection test setup.

- **description:** Subagents hand-write structured handoff artifacts (YAML/JSON) with field names from memory, producing schema-invalid files every time.
  **detection_signal:** Orchestrator finds `handoff-latest.yaml` or `todos-latest.json` needs manual correction after any subagent handoff.
  **prevention:** Replace hand-written artifacts with a deterministic generation script, or embed exact copy-paste templates with populated examples in each agent prompt.

- **description:** Implementation agent correctly identifies a test setup bug but routes it to "next agent" instead of fixing it, leaving a known-failing test in the suite.
  **detection_signal:** Agent reports N-1 of N tests passing with an explanation of why the failure is not an implementation bug but does not apply the fix.
  **prevention:** Implementation agent prompt patch: "If a test failure is diagnosed as a test setup bug (not an implementation bug), fix the test setup in the same run. Do not defer test fixes to downstream agents."

### Prompt Patches

- **agent: Test Breaker Agent**
  **change:** "For any test that manipulates ordered-collection state (slot managers, queues, stacks): after setup calls, add an explicit assertion confirming the pre-condition matches intent (e.g., `assert_true(msm.is_slot_filled(1), 'Slot B should be filled before testing slot-B-only behavior')`). This prevents fill-order assumptions from producing vacuous tests."
  **reason:** EC-20 test setup bug went undetected through the entire Test Breaker run because there was no assertion verifying the intended slot-B-only state was achieved.

- **agent: Gameplay Systems Agent (Implementation)**
  **change:** "If a test failure is diagnosed as a test setup bug (not an implementation defect), fix the test in the same implementation run. Do not route test-setup fixes to downstream agents. A known-failing test must never be left in the suite when the fix is understood."
  **reason:** Implementation agent identified the EC-20 root cause with high confidence but deferred the fix, requiring orchestrator intervention and an extra round-trip.

- **agent: Planner Agent**
  **change:** "When a deliverable includes a new Godot autoload: note in the plan that Godot 4.6 prevents `class_name X` on an autoload registered as `X`. Recommend `class_name XNode` suffix in the implementation task notes. Also: if the target controller file is within 10% of the gd-organization line limit, add a follow-up refactor task to the plan."
  **reason:** Both the autoload naming conflict and the 900-line ceiling were discovered at implementation time rather than planning time, causing avoidable checkpoint entries.

- **agent: All subagents (handoff writers)**
  **change:** "When writing `handoff-latest.yaml`: root key must be `handoff:`, required fields are `schema_version: '1.0'`, `ticket_id`, `ticket_path`, `from_agent`, `to_agent`, `stage`, `revision`, `validated_at`, `required_items_met`, `total_required_items`, `checklist` (array of objects with keys: `item_key`, `item`, `status`, `evidence`), `blocking_issues`. When writing `todos-latest.json`: required fields are `schema_version: '1.0'`, `ticket_id`, `captured_at`, `stage`, `todos` (array with `id`, `content`, `status`, `agent`)."
  **reason:** Every subagent across M11-04, M11-05, M11-06 produced schema-invalid handoff artifacts, creating cumulative orchestrator overhead.

### Workflow Improvements

- **issue:** Implementation agent deferred a known test-setup fix to the next agent, creating an unnecessary round-trip and orchestrator intervention.
  **improvement:** Add a "test-setup fix" step to the implementation agent workflow: after all tests run, if any failure is attributed to test setup (not implementation), fix the test and re-run before handoff.
  **expected_benefit:** Eliminates round-trips for test-setup bugs; implementation agent delivers a clean 100% pass rate.

- **issue:** `PlayerController3D` hit the 900-line organization limit with no follow-up refactor planned, creating a latent blocker for downstream tickets.
  **improvement:** Planner Agent should run a pre-flight line-count check on files that will be modified. If a file is within 50 lines of the limit, add a refactor extraction task (or a prerequisite refactor ticket) to the plan.
  **expected_benefit:** Prevents surprise lint gate failures on the next ticket that touches a near-limit file.

- **issue:** Handoff artifact schema drift has been documented as a learning in M902-23 and recurs in M11-04/05/06 — the learning alone did not prevent recurrence.
  **improvement:** Escalate from "learning" to "tooling": create a deterministic `ci/scripts/write_handoff.sh` script that takes structured arguments and emits valid YAML/JSON. Agents call the script instead of hand-writing artifacts. Until the script exists, embed the full validated template (not a schema reference) directly in each agent's prompt.
  **expected_benefit:** Eliminates handoff schema errors entirely by removing hand-authoring from the critical path.

### Keep / Reinforce

- **practice:** Spec Agent resolved mutation_id type (int → String) by tracing the existing codebase (`MutationSlot._active_mutation_id: String`, `EnemyInfection3D.mutation_drop: String`) rather than following the ticket's illustrative pseudocode.
  **reason:** Prevented a type mismatch bug at the system boundary that would have required a late refactor across slot manager, controller, and database.

- **practice:** Order-independent fused attack lookup with alphabetically sorted canonical key (`"acid_claw"` regardless of input order).
  **reason:** Eliminates a class of caller-order bugs and simplifies downstream fused attack registration.

- **practice:** 98 total tests (48 primary + 50 adversarial) with dedicated controller integration tests separate from unit-level database tests.
  **reason:** Clean separation caught the EC-20 slot setup bug at the integration boundary, not buried in unit tests.

---

## [M11-12] — Verification tickets benefit from automated test conversion; line-limit pressure needs upstream mitigation
*Completed: 2026-05-25*

### Learnings

- **category:** testing
  **insight:** "Manual verification" tickets can and should be converted to automated behavioral tests by the pipeline. When all AC items describe observable state transitions, they map directly to assertions.
  **impact:** 83 automated tests (46 primary + 37 adversarial) now permanently guard cooldown cross-state behavior, replacing ephemeral manual checks that would need repeating on every future change.
  **prevention:** Planner Agent should flag "manual test" AC items as candidates for automated conversion during planning. Default to automated unless the AC truly requires human perception (visual, audio, feel).
  **severity:** medium

- **category:** testing
  **insight:** Adversarial testing against engine-contract boundaries (negative delta, zero delta, massive delta) catches defensive-programming gaps that spec-driven tests miss by design.
  **impact:** GAP-1 (negative delta increasing cooldown) would have been undetectable by spec tests since the spec assumes non-negative engine delta. The `maxf(0.0, delta)` guard was added only because of adversarial probing.
  **prevention:** Test Breaker Agent should always include "engine boundary" adversarial cases for any code that consumes `delta`, `time`, or other engine-provided values.
  **severity:** medium

- **category:** architecture
  **insight:** When a file is within 10 lines of the organization line limit, even a 2-line fix creates a blocking side-quest (inlining variables, removing blank lines) that consumes review cycles.
  **impact:** Adding 2 lines to `player_controller_3d.gd` pushed it to 902 lines (over the 900 limit), requiring a separate Static QA task to inline a variable and remove a trailing blank line to get to 899.
  **prevention:** Already captured as a workflow improvement in M11-04/05/06. Reinforced here: the planner's pre-flight line-count check MUST be implemented, not just documented.
  **severity:** medium

- **category:** process
  **insight:** Handoff schema non-compliance has now recurred across M902-23, M11-04, M11-05, M11-06, and M11-12 despite being documented as a learning each time. Learnings alone do not fix structural deficiencies — tooling does.
  **impact:** Orchestrator manually repaired subagent handoff artifacts every run. Cumulative overhead is now measurable across 5+ tickets.
  **prevention:** Escalate from repeated learning to mandatory action: build `ci/scripts/write_handoff.sh` (deterministic artifact writer) or embed the complete validated template in each agent prompt. Stop re-documenting; start enforcing.
  **severity:** high

### Anti-Patterns

- **description:** Re-documenting a known recurring problem as a "learning" without implementing the fix, creating a false sense of resolution.
  **detection_signal:** The same learning appears in 3+ consecutive ticket entries with identical or near-identical prevention text.
  **prevention:** After the second recurrence, escalate from "learning" to "tooling ticket" — create a backlog item to build the automation that eliminates the problem. Tag it as a blocker for the next milestone.

- **description:** Implementation agent adds minimal lines to a near-limit file without checking the line count, causing a lint gate failure that requires a separate review pass to fix.
  **detection_signal:** Implementation checkpoint shows file grew past a known organization limit (e.g., 900 lines for GDScript).
  **prevention:** Implementation agent should run `wc -l` on the target file before and after changes. If the file will exceed the limit, apply an inline refactor in the same commit (don't defer to Static QA).

### Prompt Patches

- **agent: Planner Agent**
  **change:** "When a ticket has 'manual test' or 'manual verification' in its AC items, evaluate whether each AC can be expressed as an automated assertion (state transition, value check, timing constraint). If yes, rewrite the AC as automated test requirements and note that the original manual scope has been superseded. Only keep AC items as manual if they require human sensory judgment (visual appearance, audio quality, game feel)."
  **reason:** M11-12's five "manual test" AC items were all state-transition checks that mapped directly to automated tests. The pipeline discovered this at spec time rather than planning time, which is less efficient.

- **agent: Test Breaker Agent**
  **change:** "For any function that consumes `delta` (physics frame time), `Time.get_ticks_*`, or other engine-provided temporal values: always include adversarial tests for negative values, zero, epsilon (1e-10), and very large values (1e6). These engine-boundary cases are outside the spec's domain but are reachable in edge scenarios (paused physics, frame spikes, mocked tests)."
  **reason:** GAP-1 (negative delta) was only caught because the Test Breaker happened to include it. Making this a standing instruction ensures consistent coverage of engine-contract boundaries.

- **agent: All subagents (handoff writers)**
  **change:** "ESCALATION: Handoff schema compliance has been a recurring learning for 5+ tickets. Until `ci/scripts/write_handoff.sh` exists, copy-paste the EXACT template below when writing `handoff-latest.yaml` — do not reconstruct from memory. [Template already provided in M11-04/05/06 prompt patch — reuse verbatim.]"
  **reason:** Repeating the prompt patch with an escalation marker increases salience. The real fix is the script, but until it ships, maximum-salience prompting is the stopgap.

### Workflow Improvements

- **issue:** "Learnings" about recurring problems are documented but never converted to actionable work items, creating a documentation graveyard.
  **improvement:** Add a "Recurrence Check" step to the Learning Agent: before appending a new learning, search LEARNINGS.md for the same root cause. If found 2+ times, emit a `TOOLING_TICKET_REQUIRED` flag with a one-line description. The orchestrator must create the ticket before proceeding to the next milestone.
  **expected_benefit:** Breaks the cycle of re-documenting known problems. Converts chronic learnings into one-time fixes.

- **issue:** Verification tickets that specify "manual tests" still go through the full 7-stage pipeline (plan → spec → test-design → test-break → implement → review → gate), which is correct for automated conversion but the planner should recognize the conversion opportunity upfront.
  **improvement:** Planner Agent should classify verification tickets into "automatable" vs "requires-human-judgment" at planning time. Automatable tickets proceed through the standard pipeline with a note that the original manual scope is superseded. Human-judgment tickets should be routed to a simplified gate-only workflow.
  **expected_benefit:** Eliminates spec-time discovery of the automation opportunity; the planner makes the call, and downstream agents execute with clarity.

### Keep / Reinforce

- **practice:** Pipeline correctly elevated a "manual verification" ticket into 83 automated tests, permanently encoding the verification as regression coverage rather than a one-time check.
  **reason:** This is the ideal outcome for any verification ticket — convert ephemeral checks into durable automated guards. The pipeline's TDD structure naturally drives this conversion.

- **practice:** Planner Agent identified the single implementation gap (`_mutation_cooldowns.clear()` missing from `reset_hp()`) during code analysis at planning time, allowing the entire downstream pipeline to focus narrowly.
  **reason:** Early gap identification prevented spec/test agents from discovering the issue independently, saving at least one round-trip.

- **practice:** Test Breaker's adversarial testing found a real defensive-programming gap (GAP-1: negative delta) that no other stage would have caught.
  **reason:** Validates the Test Breaker stage as high-value even when the implementation is "almost complete." Engine-boundary adversarial testing should be a standing practice.

---

## [M11-13] — Test Breaker output must respect file limits; verification pipelines can skip implementation stage
*Completed: 2026-05-25*

### Learnings

- **category:** process
  **insight:** Test Breaker Agent generates adversarial test files without checking output size against the project's 900-line organization limit, causing a post-generation split that wastes a review cycle.
  **impact:** The adversarial test file for M11-13 reached 971 lines, requiring a split into two files (`_adversarial.gd` at 578 lines and `_adversarial_b.gd` at 487 lines). The split itself was clean, but it was an avoidable rework step.
  **prevention:** Test Breaker Agent must track cumulative line count while generating adversarial tests. When the running total approaches 800 lines, start a new file with a `_b` / `_c` suffix proactively instead of requiring a reactive split.
  **severity:** medium

- **category:** process
  **insight:** Verification-only tickets require zero implementation changes by definition, yet the pipeline still schedules an implementation stage. When all tests pass on first run, the implementation stage is a no-op that adds orchestration overhead and checkpoint noise.
  **impact:** M11-13 (and M11-12 before it) ran through a full 7-stage pipeline when the implementation stage contributed nothing. The planner correctly predicted "no implementation expected" but the pipeline did not act on that signal.
  **prevention:** When the Planner classifies a ticket as "verification-only" and the Test Designer's tests all pass on first run, the pipeline should skip the implementation stage and proceed directly to static QA / AC gatekeeper.
  **severity:** low

- **category:** process
  **insight:** Handoff schema non-compliance has now recurred across M902-23, M11-04, M11-05, M11-06, M11-12, and M11-13 (6+ occurrences). **`TOOLING_TICKET_REQUIRED`**: build `ci/scripts/write_handoff.sh` — a deterministic artifact writer that takes structured arguments and emits valid YAML/JSON. Documenting this as a learning no longer has preventive value.
  **impact:** Every ticket run requires manual correction of handoff artifacts by the orchestrator. Cumulative cost is now significant across 6+ tickets.
  **prevention:** Stop documenting. Build the script. Block next milestone on its completion.
  **severity:** high

### Anti-Patterns

- **description:** Test-generation agents produce output that exceeds file organization limits, then a separate agent must retroactively split and re-validate the output.
  **detection_signal:** Adversarial test file exceeds 800 lines during generation, or the Static QA pass fails on a freshly generated test file.
  **prevention:** All code-writing agents (Implementation, Test Designer, Test Breaker) must track output line count. When approaching the limit, proactively split into multiple files within the same generation pass.

- **description:** Pipeline stages run unconditionally even when upstream signals indicate they will be no-ops (e.g., "verification-only" classification + all tests passing).
  **detection_signal:** Implementation checkpoint shows "no changes made" or "all tests already pass."
  **prevention:** Add a conditional gate after test execution: if all tests pass and the planner flagged "no implementation expected," skip the implementation stage and emit a checkpoint noting the skip reason.

### Prompt Patches

- **agent: Test Breaker Agent**
  **change:** "Track cumulative line count while generating adversarial tests. When the output file approaches 800 lines, close the current file and start a new one with a `_b` (then `_c`, etc.) suffix. Each split file must have its own class_name, docstring with spec traceability, and independent pass/fail counters. Never generate a single test file exceeding 850 lines."
  **reason:** M11-13's adversarial file hit 971 lines, requiring a reactive split. Pre-emptive splitting during generation eliminates this rework.

- **agent: Orchestrator / Autopilot**
  **change:** "After running tests for a verification-only ticket: if all tests pass with 0 failures and the Planner flagged 'no implementation expected,' skip the Implementation stage. Record a checkpoint entry: 'Implementation stage skipped — verification-only ticket, all N tests pass.' Proceed directly to Static QA."
  **reason:** Two consecutive verification tickets (M11-12, M11-13) ran a no-op implementation stage. Skipping it saves one agent invocation and reduces checkpoint noise.

### Workflow Improvements

- **issue:** `TOOLING_TICKET_REQUIRED` — Handoff schema non-compliance (6th recurrence). Learning-based prevention has failed to resolve this issue.
  **improvement:** Create backlog ticket: "Build `ci/scripts/write_handoff.sh` — deterministic handoff artifact writer." Block M12 milestone start on its completion. The script accepts `ticket_id`, `from_agent`, `to_agent`, and a checklist array as arguments and emits a valid `handoff-latest.yaml`.
  **expected_benefit:** Eliminates handoff schema errors permanently. Removes the need for manual artifact correction on every ticket.

- **issue:** Test Breaker has no line-budget awareness, creating a mismatch between its output and the project's GDScript organization rules.
  **improvement:** Add a `MAX_TEST_FILE_LINES = 850` constant to the Test Breaker's generation loop. When the threshold is reached mid-generation, the agent splits output into a new file and continues. The split is transparent to downstream agents because each file is independently runnable.
  **expected_benefit:** Prevents reactive file splits and the associated re-validation overhead. Aligns test generation with the same limits that apply to implementation code.

### Keep / Reinforce

- **practice:** Planner Agent's pre-flight code analysis identified all 5 coverage gaps (cross-mutation integration, VFX position, projectile on-hit, e2e knockback direction, projectile velocity) with high confidence, and all 5 mapped 1:1 to spec requirements VDK-1 through VDK-5.
  **reason:** Accurate gap analysis at planning time eliminates rework in the spec and test-design stages. The planner's pattern of reading existing test files and comparing against ticket AC is highly effective.

- **practice:** Spec Agent's discrepancy resolutions (VDK-DR-1 for unhandled effect_types, VDK-DR-2 for missing EnemyBase methods) preemptively clarified scope boundaries, preventing test designers from attempting to test unimplemented handlers.
  **reason:** Explicit discrepancy resolution in the spec prevents downstream agents from making incorrect assumptions about what is testable. This pattern should be standard for any ticket where the implementation boundary is partial.

- **practice:** 69 tests (31 primary + 38 adversarial) with 206 assertions, all passing on existing code with zero implementation changes, permanently guard the attack system's damage/knockback contracts.
  **reason:** This is the second consecutive ticket (after M11-12's 83 tests) demonstrating that verification tickets are high-ROI — they convert undocumented behavioral assumptions into durable regression coverage.

---

## [M11-14] — AC Gatekeeper rework caused by unit-only test suite; handoff schema 7th recurrence; helper extraction kept EnemyBase lean
*Completed: 2026-05-26*

### Learnings

- **category:** testing
  **insight:** When an acceptance criterion explicitly names two interacting systems ("EnemyBase receives damage from AttackExecutor and PlayerProjectile3D"), unit tests that verify each system in isolation do not satisfy that criterion — integration tests bridging the two systems are required, even if the unit count is high (190 tests).
  **impact:** AC Gatekeeper correctly routed back from INTEGRATION stage because AC-11 had zero integration test coverage despite 190 passing unit/behavioral tests. A second implementation pass was required to produce `test_enemy_attack_integration.gd` (31 tests). This added a full rework cycle.
  **prevention:** Test Designer Agent must parse each AC for cross-system interaction keywords ("receives from", "delivers to", "triggers on", "bridges"). When detected, at least one integration test file must be planned in the test design pass, not deferred to a later stage.
  **severity:** high

- **category:** process
  **insight:** Handoff schema non-compliance is now on its 7th consecutive occurrence (M902-23, M11-04, M11-05, M11-06, M11-12, M11-13, M11-14). All 5 subagents in M11-14 produced incorrect YAML schema (wrong keys, missing required fields). The orchestrator corrected all 5 manually. This is no longer a learning — it is a tooling gap that documentation cannot fix.
  **impact:** Cumulative orchestrator time spent on handoff corrections across 7 tickets is now a significant drag on pipeline throughput. The per-ticket cost is small but the pattern is permanent without tooling intervention.
  **prevention:** `TOOLING_TICKET_REQUIRED` (escalated from M11-13). Build `ci/scripts/write_handoff.sh`. Do not log this learning again — build the script.
  **severity:** critical

- **category:** architecture
  **insight:** Extracting DoT/slowness tracking into a dedicated helper Node (`EnemyEffectTracker`, 85 lines) kept EnemyBase at 138 lines (under 200 limit) while implementing 6 new methods, 3 signals, death state, knockback physics, and WEAKENED threshold. The helper owns its own `_process()` for tick timing, decoupling effect lifecycle from the host entity.
  **impact:** Clean implementation with no line-budget violations. The helper pattern is composable — future effect types (burn, freeze, etc.) can be added to EnemyEffectTracker without touching EnemyBase.
  **prevention:** For any Node class approaching a line budget, identify "lifecycle-owning" concerns (timers, ticking effects, state machines) and extract them into child Node helpers early — during spec, not during implementation rework.
  **severity:** low

- **category:** testing
  **insight:** Test Breaker produced 838 lines (42 test functions) for M11-14, staying under the 850-line threshold. This is a measurable improvement from M11-13's 971-line overshoot, indicating that the line-budget prompt patch from M11-13's learnings may have taken effect, or the agent self-corrected.
  **impact:** No reactive file split was needed, saving one rework cycle compared to M11-13.
  **prevention:** Continue reinforcing the 850-line budget in the Test Breaker prompt. Monitor for regression.
  **severity:** low

### Anti-Patterns

- **description:** Implementation agent produces a complete unit test suite (190 tests) and declares coverage sufficient, without checking whether any AC explicitly requires cross-system integration tests. The AC Gatekeeper catches the gap, triggering a full rework cycle.
  **detection_signal:** AC text contains cross-system verbs ("receives from", "delivers to", "verifies X from Y") but the test inventory has zero files importing both system names.
  **prevention:** Before declaring test coverage complete, the Implementation Agent must grep the AC list for cross-system interaction language and verify at least one test file references both named systems. If none exists, write integration tests before advancing.

- **description:** Every subagent in a pipeline run produces handoff artifacts with incorrect schema, and the orchestrator silently fixes them rather than failing the stage. This normalizes non-compliance and ensures the pattern recurs.
  **detection_signal:** Orchestrator checkpoint notes mention "fixed handoff schema" or "corrected YAML."
  **prevention:** Make handoff validation a hard gate: if the artifact does not validate against the schema, reject the handoff and return to the subagent with a specific error message. (Interim: build `ci/scripts/write_handoff.sh` to eliminate the error source.)

### Prompt Patches

- **agent: Test Designer Agent**
  **change:** "Before finalizing the test plan, scan each acceptance criterion for cross-system interaction language: phrases like 'receives from', 'delivers to', 'verifies X from Y', 'triggers on'. For each such AC, plan at least one integration test file that instantiates both named systems and verifies the interaction end-to-end. Do not defer integration tests to a later pipeline stage."
  **reason:** M11-14's AC-11 explicitly required integration tests ("EnemyBase receives damage from AttackExecutor and PlayerProjectile3D"), but the Test Designer produced only unit tests. The AC Gatekeeper caught this, adding a full rework cycle.

- **agent: Orchestrator / Autopilot**
  **change:** "After each subagent writes handoff-latest.yaml, validate the artifact against the schema before proceeding. Required root key: `handoff`. Required fields: `schema_version`, `ticket_id`, `from_agent`, `to_agent`, `validated_at`, `required_items_met`, `total_required_items`, `checklist` (array of objects with `item_key`, `item`, `status`, `evidence`). If validation fails, return the artifact to the subagent with the specific schema violations listed. Do not silently correct handoff artifacts."
  **reason:** 7 consecutive tickets with handoff schema errors, all silently corrected by the orchestrator, have normalized non-compliance. Hard validation forces the subagent to learn the schema or fail fast.

### Workflow Improvements

- **issue:** `TOOLING_TICKET_CRITICAL` — Handoff schema non-compliance (7th recurrence). Previous M11-13 learning escalated to `TOOLING_TICKET_REQUIRED`. This ticket confirms the pattern is permanent. The `ci/scripts/write_handoff.sh` script has not been built.
  **improvement:** Create and prioritize a blocking ticket at the top of the next milestone backlog: "Build `ci/scripts/write_handoff.sh` — deterministic handoff artifact writer." The script accepts `ticket_id`, `from_agent`, `to_agent`, `validated_at`, and a checklist array as CLI arguments, emits a schema-valid `handoff-latest.yaml`, and exits non-zero on invalid input. Block M12 milestone kickoff on completion.
  **expected_benefit:** Eliminates the error class permanently. Removes manual orchestrator correction overhead. Makes handoff validation automatable as a pre-stage gate.

- **issue:** AC Gatekeeper catches missing integration tests late in the pipeline (after 190 unit tests pass), causing a full rework cycle back to the Implementation Agent.
  **improvement:** Add an integration-test checkpoint between Test Design and Implementation: after Test Designer outputs the test plan, the AC Gatekeeper (or a lightweight validator) checks whether ACs with cross-system language have corresponding integration test files planned. If not, route back to Test Designer before implementation begins — catching the gap at plan time instead of post-implementation.
  **expected_benefit:** Eliminates the most expensive rework pattern (post-implementation AC failure). The M11-14 rework cycle required writing 31 new integration tests after 190 unit tests already passed.

### Keep / Reinforce

- **practice:** Planner Agent's helper extraction recommendation (EnemyEffectTracker as child Node) was adopted by the Spec Agent, implemented exactly as planned, and kept EnemyBase at 138 lines (under 200 limit). The pattern of identifying lifecycle-owning concerns during planning prevents line-budget violations during implementation.
  **reason:** Early architectural decisions at planning time avoid reactive refactoring during implementation. This is the first M11 ticket where the planner's architectural recommendation was adopted unchanged through all stages.

- **practice:** AC Gatekeeper's evidence matrix format (AC-by-AC mapping to test references and code locations) correctly identified the one AC without coverage (AC-11) despite 190 passing tests. The systematic AC-to-evidence mapping is the most reliable quality gate in the pipeline.
  **reason:** The AC Gatekeeper's thoroughness prevented a false COMPLETE. Without this gate, the ticket would have shipped with a documented acceptance criterion (integration tests) unsatisfied. This reinforces that high unit test counts do not substitute for AC-level coverage verification.

- **practice:** Implementation Agent committed its own code (commits d279a6c, ec9eb70), reducing orchestrator overhead. This is the first M11 ticket where the implementation agent managed its own git workflow.
  **reason:** Self-committing implementation agents reduce handoff friction and make the commit history more traceable (commit author matches the agent that wrote the code).

---

## [M11-08] — Modifier-based extension pattern enables zero-new-file mutation implementation
*Completed: 2026-05-26*

### Learnings

- **category:** architecture
  **insight:** Mutation-specific attack behavior (WEAKENED→INFECTED transition) was implemented entirely through a modifier key (`infect_weakened`) in the existing `AttackResource.modifiers` dict and a new branch in `_apply_modifiers()`. Zero new script files were created. This validates the M11-04/05 attack pipeline architecture as properly extensible via data-driven modifiers.
  **impact:** Claw was the first concrete mutation to exercise the full attack pipeline end-to-end. The modifier pattern held without architectural changes, confirming that acid, adhesion, and carapace can follow the same pattern.
  **prevention:** Future mutation attacks should default to adding a modifier key + handler branch before considering new script files. If a modifier cannot express the behavior, that signals an architecture gap worth escalating.
  **severity:** medium

- **category:** architecture
  **insight:** The Spec Agent's decision to add a `pre_damage_state` parameter to `_apply_modifiers()` resolved the same-hit weaken+infect ambiguity at design time, preventing what would have been a subtle runtime bug. The two-hit invariant (first hit weakens, second infects) was enforced structurally rather than relying on execution order.
  **impact:** Without pre-damage state capture, a single claw hit could both weaken and infect an enemy in the same frame, violating the "aggressive two-hit play" design intent. 10+ tests validated this invariant.
  **prevention:** When a modifier interacts with state transitions caused by the same hit's damage, always capture the relevant state before damage application and pass it explicitly. Do not rely on post-damage state checks.
  **severity:** high

- **category:** process
  **insight:** Test Designer self-corrected from 1114 lines to 763 lines within the same agent turn. The initial generation still overshoots the 850-line budget, but the review step catches and corrects it before handoff. This indicates the line-budget prompt patch from M11-13 operates as a review-time constraint rather than a generation-time constraint.
  **impact:** No reactive file-split rework cycle was needed (saved one full rework cycle compared to M11-13). However, the initial overshoot wastes tokens regenerating the file.
  **prevention:** The self-correction mechanism is working — reinforce the 850-line budget. To reduce wasted tokens, add front-loading guidance: "Before writing tests, estimate the line count from your test plan. If the estimate exceeds 700 lines, split into primary and edge-case files proactively."
  **severity:** low

- **category:** process
  **insight:** Pipeline efficiency improved measurably: planner gate passed first try (vs. M11-14's 5 consecutive fixes), AC Gatekeeper approved on first pass (vs. M11-14's integration test rework), and both Test Breaker and Implementation gates required only one handoff fix each (label/evidence format). Total pipeline throughput: 7 revisions to COMPLETE, with no rework cycles returning to earlier stages.
  **impact:** The accumulated prompt patches from M11-13 and M11-14 learnings are producing measurable pipeline throughput gains. First-pass AC approval eliminates the most expensive rework pattern in the pipeline.
  **prevention:** Continue applying learnings from each ticket to refine agent prompts. The diminishing-returns signal will be consecutive tickets with zero handoff fixes and zero rework cycles.
  **severity:** medium

### Anti-Patterns

- **description:** Handoff YAML schema non-compliance persists (8th ticket in a row). Both Test Breaker and Implementation gates needed one fix each for label/evidence formatting. The `ci/scripts/write_handoff.sh` script recommended in M11-13 and escalated to `TOOLING_TICKET_CRITICAL` in M11-14 has still not been built.
  **detection_signal:** Orchestrator checkpoint notes mention handoff fix, corrected YAML, or label format adjustment for any subagent.
  **prevention:** This is the 8th consecutive recurrence. The only permanent fix is the deterministic `write_handoff.sh` script. Escalation status: `TOOLING_TICKET_OVERDUE`.

- **description:** Test Designer's initial generation ignores the 850-line budget and relies on the review step to catch the overshoot. This wastes tokens regenerating the file and indicates the budget constraint is not internalized during planning.
  **detection_signal:** Test Designer produces an initial file exceeding 850 lines and then immediately rewrites it in the same turn.
  **prevention:** Front-load the budget check: require the Test Designer to produce a line-count estimate from the test plan before writing code. If the estimate exceeds 700 lines, mandate a two-file split at plan time.

### Prompt Patches

- **agent: Test Designer Agent**
  **change:** "Before writing test code, estimate the total line count from your test plan (count planned test functions × ~20 lines each + setup/teardown overhead). If the estimate exceeds 700 lines, split into two files at the plan stage: `test_<feature>.gd` for primary behavioral tests and `test_<feature>_edge.gd` for edge cases. Do not generate a single file and then split reactively."
  **reason:** M11-08's Test Designer generated 1114 lines and self-corrected to 763 in the same turn. The budget is enforced at review time but ignored during generation, wasting tokens on a full regeneration cycle.

- **agent: Spec Agent**
  **change:** "When specifying a modifier that interacts with state transitions caused by the same hit's damage (e.g. infect-on-weakened), always require a pre-damage state capture parameter. Specify the parameter name, default value, and which call sites must pass it. Do not leave execution-order-dependent behavior implicit."
  **reason:** M11-08's `pre_damage_state` parameter prevented the same-hit weaken+infect bug. This pattern will recur for acid (corrode-on-weakened) and adhesion (slow-on-weakened). Making it a spec-level requirement prevents the bug class from reaching implementation.

### Workflow Improvements

- **issue:** `TOOLING_TICKET_OVERDUE` — Handoff schema non-compliance (8th recurrence). The `ci/scripts/write_handoff.sh` script has been recommended since M11-13 and escalated to `TOOLING_TICKET_CRITICAL` in M11-14. Still unbuilt.
  **improvement:** No new recommendation — the existing `write_handoff.sh` ticket is the correct fix. Escalation status upgraded to `OVERDUE`. If not built before M11-09, the Learning Agent will recommend hard-blocking the next milestone.
  **expected_benefit:** Eliminates the single most persistent error class in the pipeline (8 consecutive tickets).

- **issue:** First-pass AC approval on M11-08 suggests the M11-14 integration-test prompt patch to the Test Designer is working, but sample size is 1. Need confirmation on M11-09 (acid) to validate.
  **improvement:** Track first-pass AC approval rate across M11-09 through M11-11. If 3/3 pass first try, mark the M11-14 Test Designer prompt patch as validated and reinforce. If any fail, analyze whether the integration-test scanning heuristic missed a case.
  **expected_benefit:** Evidence-based prompt patch validation prevents cargo-culting prompt changes that may not actually improve outcomes.

### Keep / Reinforce

- **practice:** Planner Agent's risk register identified the "same-hit weaken+infect ambiguity" and the "first concrete mutation registration pattern" risks. Both were resolved cleanly by the Spec Agent. The risk-to-spec pipeline is working as designed.
  **reason:** Planner risk identification at plan time prevents spec ambiguities from becoming implementation bugs. M11-08 is the second consecutive ticket (after M11-14) where planner risks were fully resolved before implementation.

- **practice:** Modifier-based extension via `AttackResource.modifiers` dict + `_apply_modifiers()` branch pattern. Zero new files for mutation-specific behavior. Pattern is clean and reusable for remaining 3 mutations (acid, adhesion, carapace).
  **reason:** Data-driven extension through modifiers keeps the codebase compact and avoids the script-proliferation anti-pattern. Each new mutation is one dict entry + one handler branch, not a new script file.

- **practice:** AC Gatekeeper's linter-fix-in-place for mechanical changes (extracting numeric literals to named constants) during autonomous mode. The AC agent correctly classified this as a non-behavioral change that did not require routing back to the implementation agent.
  **reason:** Autonomous-mode efficiency: mechanical linter fixes that don't change behavior should be handled in-place by the current agent, not routed back through the pipeline. This saved one full agent round-trip.

---

## [M11-09] — AC Gatekeeper git-state gate validates; gd-organization DRY enforcement catches test duplication
*Completed: 2026-05-26*

### Learnings

- **category:** process
  **insight:** AC Gatekeeper correctly blocked COMPLETE transition when implementation files were uncommitted/unpushed. All 7 ACs were evidenced but git state was dirty (3 modified + 2 untracked files). The INTEGRATION hold forced the implementation agent to commit before closure, proving the "Commit and Push BEFORE COMPLETE Closure" gate is effective at preventing drift between validated state and repository state.
  **impact:** Without this gate, the ticket would have been marked COMPLETE with code only in the working tree — invisible to other agents, CI, or deployment. The hold added one routing cycle but guaranteed reproducibility.
  **prevention:** Implementation agents should self-commit before requesting AC Gatekeeper review. Add a pre-AC self-check: "Is `git status` clean for all files I touched?"
  **severity:** medium

- **category:** testing
  **insight:** The `gd-organization` hook detected `_build_scene()` duplication across `test_acid_attack.gd` and `test_acid_attack_adversarial.gd`. Both test files independently defined nearly identical scene-building helpers. The fix was extracting a shared `AttackExecutorHarness` utility, which DRYs the pattern for all future attack test files.
  **impact:** Without the hook catch, each new mutation test file would copy-paste the scene builder, accumulating divergent variants. The harness extraction prevents N-way drift as adhesion and carapace tests are added.
  **prevention:** When test files share scene-building or mock-setup logic, extract to a shared harness/fixture immediately during Test Design — do not defer to the organization hook. Test Designer should check for existing harness patterns before writing new setup code.
  **severity:** medium

- **category:** process
  **insight:** Zero implementation rework cycles — all 187 tests (83 behavioral + 104 adversarial) passed on the first implementation run. This is the second consecutive ticket (after M11-08) where implementation required no rework. The combination of precise specs, pre-implementation Test Breaker adversarial hardening, and the modifier-based extension pattern produces implementation that works correctly on first attempt.
  **impact:** Zero rework eliminates the most expensive pipeline operation (implementation → test failure → re-route → re-implementation). Pipeline completed in 8 revisions with no stage regression.
  **prevention:** Reinforce the current pipeline sequencing. The "spec precision + adversarial pre-hardening + data-driven architecture" combination is the proven recipe for first-pass implementation success.
  **severity:** low

### Anti-Patterns

- **description:** Handoff YAML schema non-compliance continues (9th consecutive ticket). The `agent_alias_map` in handoff validation does not include "Gameplay Systems Agent" as a recognized alias, despite being the agent that performs implementation for attack tickets. This causes routing confusion when the AC Gatekeeper routes back to "Gameplay Systems Agent" for commit — the alias must be manually resolved.
  **detection_signal:** Handoff `to_agent` or `from_agent` field contains an agent name not present in the canonical agent alias registry, requiring orchestrator interpretation.
  **prevention:** `TOOLING_TICKET_BLOCKED` — The `write_handoff.sh` script (recommended since M11-13, critical since M11-14, overdue since M11-08) must include a validated agent alias enum. Until built, add "Gameplay Systems Agent" to the alias map in `workflow_enforcement_v1.md`. Escalation: hard-block M11-12 if `write_handoff.sh` is not merged.

- **description:** Implementation agent did not self-commit before requesting AC review. The code was fully working (187/187 tests pass) but existed only in the working tree, triggering a preventable routing cycle back to the implementation agent.
  **detection_signal:** AC Gatekeeper checkpoint mentions "git state dirty" or "uncommitted files" as the sole blocker with all ACs evidenced.
  **prevention:** Add to Implementation Agent prompt: "After all tests pass, run `git add` and `git commit` for all files you created or modified before updating the ticket to request AC review."

### Prompt Patches

- **agent: Gameplay Systems Agent (Implementation)**
  **change:** "After confirming all tests pass (`run_tests.sh` exits 0), immediately commit your changes with `git add <files> && git commit -m 'feat(attacks): <description>'` BEFORE updating the ticket stage or requesting AC Gatekeeper review. A dirty git state will always block COMPLETE transition."
  **reason:** M11-09's AC Gatekeeper correctly held the ticket at INTEGRATION because implementation files were uncommitted. This added one unnecessary routing cycle. Self-committing eliminates the round-trip.

- **agent: Test Designer Agent**
  **change:** "Before writing scene-building helper functions (`_build_scene`, `_build_*`), check if a shared test harness exists under `tests/scripts/attacks/` (e.g. `AttackExecutorHarness`). If one exists, import and use it. If one doesn't exist but your test plan requires scene setup that future test files will also need, create the harness as a separate file and import it from the start."
  **reason:** M11-09's `gd-organization` hook caught duplicate `_build_scene()` across two test files. Extracting `AttackExecutorHarness` post-hoc is less efficient than designing for reuse upfront. Adhesion and carapace tests will need the same harness.

### Workflow Improvements

- **issue:** `TOOLING_TICKET_BLOCKED` — Handoff schema non-compliance (9th recurrence). `write_handoff.sh` still unbuilt. Per M11-08 learning: "If not built before M11-09, recommend hard-blocking the next milestone." Condition met.
  **improvement:** Hard-block recommendation: do not begin M11-12 until `ci/scripts/write_handoff.sh` is merged. The script must validate agent names against a canonical enum, enforce YAML schema, and be called by all subagents at handoff time. This is the only permanent fix for the single most persistent pipeline error.
  **expected_benefit:** Eliminates 9-ticket-recurring handoff format errors. Saves 1-2 routing cycles per ticket (estimated 18+ wasted cycles across M11).

- **issue:** M11-08 learning requested tracking first-pass AC approval rate across M11-09 through M11-11. M11-09 result: AC Gatekeeper **did not** approve on first pass (blocked on git state), but all behavioral ACs were evidenced on first pass. The block was procedural (git state), not substantive (missing evidence).
  **improvement:** Refine the tracking metric: separate "AC evidence completeness on first pass" (M11-09: YES) from "AC COMPLETE on first pass" (M11-09: NO, procedural block). The M11-14 Test Designer integration-test prompt patch appears validated for evidence completeness (2/2 tickets pass). The git-state block is a separate issue addressed by the implementation self-commit patch above.
  **expected_benefit:** Prevents conflating procedural blocks with substantive AC failures when evaluating prompt patch effectiveness.

### Keep / Reinforce

- **practice:** Modifier-based extension pattern (`acid_on_hit` modifier key + `_apply_modifiers()` branch) produced a second successful zero-new-file mutation implementation. Acid follows the identical structural pattern as claw (`infect_weakened`). The pattern is now validated across 2 mutations with 2 remaining (adhesion, carapace).
  **reason:** Consistent architectural pattern reduces implementation cognitive load and enables first-pass success. Each mutation is predictable: one modifier key, one handler branch, one `AttackResource` registration.

- **practice:** Test Breaker Agent's "gaps discovered" section provided precise, actionable implementation notes (exact line numbers, exact code patterns, exact test names that will fail). The Implementation Agent cited these notes as sufficient to complete the work with zero ambiguity.
  **reason:** When Test Breaker provides implementation-ready gap analysis, the Implementation Agent can work without consulting the spec directly. This eliminates one source of misinterpretation and explains the zero-rework outcome.

- **practice:** Planner's estimated effort (~1 hour) closely matched actual throughput. All pipeline stages completed within expected bounds with no unexpected scope expansion.
  **reason:** Accurate effort estimation enables better resource allocation and sets correct expectations for pipeline monitoring. When estimates match reality, it signals the task decomposition was correct.

---

## [M11-10] — Test Breaker line-count overrun and decorative separators trigger lint false positives
*Completed: 2026-05-26*

### Learnings

- **category:** process
  **insight:** Test Breaker Agent produced a 1132-line adversarial test file, exceeding the 900-line `gd-organization` limit. The orchestrator had to split it into two files (`adversarial.gd` + `adversarial_b.gd`). This mirrors the M11-08 Test Designer overrun (1114 lines → split). The M11-08 prompt patch targeted Test Designer only — Test Breaker has the identical blind spot.
  **impact:** Orchestrator spent a full correction cycle splitting the file, renaming references, and re-running lint. The split is mechanical work that the agent should have prevented at generation time.
  **prevention:** Apply the same line-budget pre-check to Test Breaker that was patched into Test Designer after M11-08: estimate line count before writing, split at the plan stage if estimate exceeds 700 lines.
  **severity:** medium

- **category:** tooling
  **insight:** Test Breaker used `# ===========================================================================` decorative section headers in generated test files. The `gd-review` hook's merge-conflict marker detector treats any line containing seven or more consecutive `=` characters as a git conflict marker (`=======`), producing false-positive lint failures. The orchestrator replaced all `=` separators with `-` separators.
  **impact:** Every decorative `=` header line became a lint failure, requiring a bulk find-and-replace cycle. The root cause is that agents default to `=` for visual emphasis, which collides with a legitimate safety check.
  **prevention:** All code-generating agents must avoid `=` character sequences of 4+ in comments or string literals. Use `-` or `#` for section separators.
  **severity:** medium

- **category:** process
  **insight:** AC Gatekeeper blocked COMPLETE transition for the third consecutive ticket (M11-08, M11-09, M11-10) on "commits not pushed to remote." In a local-only development workflow without a remote, this gate is always a false positive. The orchestrator overrode to COMPLETE each time, establishing a de facto workaround.
  **impact:** Each occurrence adds one unnecessary routing cycle (AC Gatekeeper → orchestrator override → COMPLETE). Three consecutive overrides indicate a systematic mismatch between the gate and the operating environment.
  **prevention:** AC Gatekeeper needs a workflow mode flag (`local_only: true`) that skips the git-push gate when no remote is configured or when the orchestrator explicitly declares local-only operation. The commit gate (files committed) should remain; only the push gate should be conditional.
  **severity:** medium

- **category:** architecture
  **insight:** Carapace's SLAM_AOE used a dedicated `_handle_slam_aoe()` handler function rather than the modifier-based approach used for claw (`infect_weakened` modifier) and acid (`acid_on_hit` modifier). The handler pattern was cleaner for SLAM_AOE because the attack has qualitatively different dispatch semantics (radial area, async wind-up, airborne deferral) that don't map to the "apply modifier after standard hit" model.
  **impact:** Zero implementation rework and cleaner code. The handler owns its entire lifecycle (`_is_active` management, async wind-up, landing poll), while modifiers are post-hit decorators. Using modifiers for SLAM_AOE would have forced an awkward async modifier that fights the synchronous modifier pipeline.
  **prevention:** Future mutations should evaluate whether the attack is a "standard hit + post-hit effect" (→ modifier) or a "qualitatively different dispatch pattern" (→ dedicated handler). Adhesion's slow-on-hit is likely a modifier; any future area/channeled/combo attack is likely a handler.
  **severity:** low

### Anti-Patterns

- **description:** Test Breaker generates decorative comment separators using `=` character sequences that trigger `gd-review`'s merge-conflict marker detector. This is the same class of "agent output contains sequences that collide with tooling safety checks" seen when agents generate long `---` sequences near YAML frontmatter or `<<<`/`>>>` in string literals.
  **detection_signal:** `gd-review` reports "possible merge conflict marker" on lines that are clearly decorative comments, not conflict artifacts.
  **prevention:** Add to all code-generating agent prompts: "Never use 4+ consecutive `=` characters in comments or decorative headers. Use `-` or `#` for visual separators."

- **description:** Handoff YAML schema non-compliance continues (10th consecutive ticket). Fields use `id` instead of `item_key`, `met: true` instead of `status: complete`, and agent names outside the canonical alias registry. Every handoff requires manual correction by the orchestrator.
  **detection_signal:** Orchestrator correction cycle on every handoff artifact. Presence of `id:` or `met:` keys in handoff YAML instead of `item_key:` and `status:`.
  **prevention:** `TOOLING_TICKET_CRITICAL_OVERDUE` — `write_handoff.sh` has been recommended for 10 consecutive tickets (since M11-13). Escalation: hard-block next milestone if not merged. This is the single highest-recurrence error in the pipeline.

### Prompt Patches

- **agent: Test Breaker Agent**
  **change:** "Before writing adversarial test code, estimate total output line count (planned test functions × ~25 lines each + setup/mock overhead). If the estimate exceeds 700 lines, split into two adversarial files at the plan stage: `test_<feature>_adversarial.gd` (first half of categories) and `test_<feature>_adversarial_b.gd` (second half). Do not generate a single file exceeding 900 lines."
  **reason:** M11-10's Test Breaker generated 1132 lines, requiring orchestrator-initiated file splitting. This is the same issue fixed in Test Designer after M11-08, but the patch was never applied to Test Breaker.

- **agent: Test Breaker Agent**
  **change:** "Never use 4 or more consecutive `=` characters in comments, section headers, or decorative separators. Use `# ---------------------------------------------------------------------------` for section breaks. Sequences of `=` trigger the gd-review merge-conflict marker detector."
  **reason:** M11-10's Test Breaker used `# ===========================================================================` headers that produced false-positive merge-conflict lint failures on every decorated line.

- **agent: AC Gatekeeper Agent**
  **change:** "When the orchestrator declares `workflow_mode: local` or when `git remote` returns no configured remotes, skip the 'commits pushed to remote' gate. Still enforce the 'all changes committed' gate. Do not block COMPLETE solely because commits are unpushed in a local-only workflow."
  **reason:** M11-08, M11-09, and M11-10 were all blocked by the push gate in a local-only environment. Three consecutive orchestrator overrides demonstrate this gate is systematically inapplicable in the current operating mode.

### Workflow Improvements

- **issue:** `TOOLING_TICKET_CRITICAL_OVERDUE` (10th recurrence) — `ci/scripts/write_handoff.sh` remains unbuilt. Every handoff artifact requires manual field correction (item_key vs id, status vs met, agent alias validation). The learning recommendation to hard-block the next milestone (issued at M11-08, condition was "if not built before M11-09") has been deferred twice.
  **improvement:** Reclassify as `PIPELINE_BLOCKER`. The `write_handoff.sh` script must be the first ticket in the next milestone or the next planning session. No new feature tickets should be planned until this debt is retired. Script requirements: YAML schema validation, canonical agent alias enum, `item_key`/`status` field enforcement, called by all agents at handoff time.
  **expected_benefit:** Eliminates the single most persistent pipeline error (10 consecutive tickets, estimated 20+ wasted correction cycles across M11).

- **issue:** AC Gatekeeper git-push gate has no local-only bypass. Three consecutive orchestrator overrides (M11-08, M11-09, M11-10) demonstrate the gate is inapplicable for local development. The override is undocumented and ad hoc.
  **improvement:** Add a `workflow_mode` field to `workflow_enforcement_v1.md` with values `local` (skip push gate) and `remote` (enforce push gate). Default to `local` when `git remote` returns empty. AC Gatekeeper reads this field before evaluating the push gate.
  **expected_benefit:** Eliminates one routing cycle per ticket in local-only development. Removes the need for undocumented orchestrator overrides.

### Keep / Reinforce

- **practice:** Third consecutive ticket (M11-08, M11-09, M11-10) with zero implementation rework. All tests passed on first implementation run (M11-10: 167 tests across 3 files). The "precise spec → adversarial pre-hardening → implementation" pipeline is consistently producing first-pass success.
  **reason:** The pipeline's value proposition is validated over 3 tickets: spec precision prevents ambiguity, Test Breaker hardens expectations before implementation, and the implementation agent has unambiguous targets. This pattern should be the baseline for all future milestones.

- **practice:** Carapace's dedicated handler pattern (`_handle_slam_aoe()`) vs claw/acid's modifier pattern demonstrates that the attack system has two clean extension points for different complexity tiers. The architecture supports both without forcing all mutations through one abstraction.
  **reason:** Dual extension points (modifier for post-hit decorators, handler for qualitatively different dispatches) prevent the "everything is a modifier" anti-pattern that would require increasingly complex modifier pipelines for non-standard attack behaviors.

- **practice:** Planner's risk register correctly identified the airborne deferral mechanism as the highest-risk item (medium confidence in checkpoint). The Spec Agent resolved it with a concrete polling loop + timeout design (CCA-DR-3). The risk→resolution pipeline worked exactly as designed.
  **reason:** Planner-identified risks that are resolved at spec time never become implementation bugs. Three consecutive tickets with clean risk→resolution flow validates the checkpoint system's value.

---

