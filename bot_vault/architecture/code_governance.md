# Blobert Engineering Governance System — Full Implementation Prompt
Design and implement a complete layered engineering governance system for a polyglot repository containing:
- Python backend (FastAPI)
- React/TypeScript frontend
- Godot game systems
The system must be production-grade, enforceable, and layered across deterministic → semantic → agent reasoning.
It must prioritize:
| Principle | Goal |
|---|---|
| OOP 📦 | Clear ownership, hierarchy, SRP |
| TDD 📋 | Behavioral correctness and confidence |
| DRY ☔️ | Prevent duplication and entropy |
| KISS 💋 | Minimize cognitive complexity |
| Security 🔒 | Prevent unsafe and silent failure modes |
---
# 🧠 Core System Philosophy
The system is structured as a **strict layered pipeline with early exits**:

Formatting
→ Micro-quality enforcement (wemake)
→ Structural architecture enforcement
→ Semantic risk scoring
→ Semantic extraction
→ Agent review
→ Override / escalation system
→ Final security gate

Agents are NOT always-on.
Agents ONLY operate on ambiguous or high-risk changes.

⸻

# 🟢 Stage 0 — Diff Classification (HARD EARLY EXIT)

Classify staged changes:

Exit immediately if:

* docs-only changes
* formatting-only changes
* lockfile-only changes
* empty semantic impact changes

Route selectively:

* tests-only → reduced pipeline
* migration-only → migration rules only
* runtime code → full pipeline

⸻

# 🟢 Stage 1 — Formatting Layer

Run:

* black / ruff format
* isort / ruff import sorting
* prettier (TS/React)
* gdformat (Godot)

Rules:

* auto-fix only
* if changes occur → re-stage and EXIT

⸻

# 🟡 Stage 2 — Micro-Code Quality (WEMAKE CORE LAYER)

Run:

* wemake-python-styleguide
* ruff
* eslint
* eslint-sonarjs
* typescript-eslint
* react-hooks rules
* gdlint

⸻

Enforces:

Complexity

* cognitive load limits
* nesting depth restrictions
* function/class size constraints

Micro-DRY

* local duplication avoidance
* readability consistency

Anti-patterns

* over-engineered constructs
* unclear control flow

Type safety

* mypy / TS correctness

⸻

❗ Exception Handling Rules 

The system MUST strictly enforce no exception swallowing.

Forbidden patterns:

* except: pass
* except Exception: pass
* silent failure returns (return None, return False) without context
* logging-only exception handlers without propagation or transformation

⸻

Required behaviors:

All exceptions MUST follow at least ONE:

1. Propagate
    * re-raise original exception
2. Transform
    * convert into domain-specific exception
3. Observe + propagate
    * structured logging + re-raise
4. Explicit recovery
    * documented fallback with clear semantics

⸻

Enforcement:

* wemake → detects unsafe patterns (soft)
* semgrep → hard fail
* agent → semantic validation (intent correctness)
* observability layer → trace integrity enforcement

⸻

Exit rules:

* syntax errors → hard fail
* type errors → hard fail
* async safety violations → hard fail
* complexity violations → hard fail
* hook violations → hard fail

⸻

# 🟠 Stage 3 — Structural Architecture Enforcement

Run:

* import-linter (Python dependency graph)
* eslint-plugin-boundaries (frontend architecture)
* semgrep (custom architecture rules)
* jscpd (duplication)
* lizard/radon (complexity deltas)

⸻

Enforced Architecture Rules

SRP (Single Responsibility Principle)

* controllers: HTTP only
* services: workflows only
* repositories: persistence only
* domain: business rules only
* infrastructure: external systems only

⸻

Communication Boundaries

* no cross-layer leakage
* no forbidden imports
* feature isolation enforced
* dependency direction enforced

⸻

Object Hierarchy Rules

* no unnecessary inheritance depth
* composition preferred over inheritance
* no empty wrapper classes
* no fake abstraction layers
* abstraction must reduce complexity, not increase it

⸻

Data Ownership & Lifecycle (CRITICAL)

* DTO ownership must be explicit
* persistence writes owned by repositories only
* mutation boundaries enforced
* cache ownership must be defined
* no implicit cross-layer state mutation

⸻

Observability Enforcement (NEW)

* structured logging required
* correlation/request IDs required
* no raw logger usage
* audit events required for critical flows
* traces must propagate across services

⸻

Async & Concurrency Safety

* no blocking calls in async context
* no unbounded task spawning
* proper cancellation handling required
* React async cleanup required
* Godot signal lifecycle correctness enforced

⸻

Migration Safety (DB + API separated)

* DB migrations must be isolated
* API migrations must be versioned
* migration PRs must contain minimal unrelated runtime changes
* schema changes must be paired with controlled service updates

⸻

Static Performance Budgets (RELAXED STATIC ONLY)

* max component size thresholds
* max nesting depth thresholds
* query complexity heuristics
* scene complexity heuristics (Godot)
* bundle growth warnings

(Do NOT enforce runtime profiling yet)

⸻

Exit rules:

* architecture violation → HARD FAIL
* SRP violation → HARD FAIL
* dependency violation → HARD FAIL
* unsafe migration → HARD FAIL
* observability violation → WARN or FAIL (configurable)

⸻

# 🟠 Stage 4 — Semantic Risk Scoring

Compute weighted risk score:

Signals:

* SRP ambiguity
* architecture drift
* duplication clusters
* async complexity
* migration complexity
* suppression usage
* observability gaps
* ownership ambiguity
* abstraction introduction

⸻

Early exits:

* score 0–2 → EXIT
* score 3–5 → WARN only
* score 6+ → semantic extraction

⸻

# 🟣 Stage 5 — Semantic Extraction Layer

Generate focused review bundles.

Extract:

* changed code
* dependency neighborhood
* ownership graph
* related abstractions
* tests
* duplication clusters
* architecture violations
* async boundaries
* observability gaps
* historical suppressions

Output:

.semantic_reviews/<issue>.json

DO NOT send full repo context.

⸻

# 🟣 Stage 6 — Agent Review Layer

Agents evaluate ONLY extracted bundles.

Responsibilities:

* SRP correctness
* abstraction justification
* hierarchy correctness
* ownership clarity
* observability completeness
* migration safety
* async correctness
* exception handling intent
* suppression justification

⸻

Output:
```json
{
  "decision": "approve | warn | reject",
  "confidence": 0.0-1.0,
  "reasoning": "...",
  "violations": []
}
```
⸻

# 🔴 Stage 7 — Override & Escalation System

Allow controlled bypasses:
```text
# blobert-ignore-next-line
# Reason: temporary migration coupling
# Ticket: BLB-142
```
⸻

Rules:

* must include justification
* optionally include expiration
* must link to issue/ticket

⸻

Escalation triggers:

* repeated suppressions
* architecture bypasses
* security bypass attempts
* exception handling bypasses
* observability suppression

⸻

# 🔴 Stage 8 — Final Security Gate

Run:

* gitleaks
* bandit
* dependency vulnerability scans
* critical semgrep security rules

⸻

Hard fail conditions:

* secrets detected
* unsafe deserialization
* auth bypass
* critical vulnerability patterns

⸻

# 🧠 Full Pipeline Flow
```text
STAGED FILES
  ↓
[0] Diff Classification
  → trivial changes EXIT
  ↓
[1] Formatting
  → modified files → re-stage EXIT
  ↓
[2] Micro Quality (Wemake)
  → fail → EXIT
  ↓
[3] Architecture Enforcement
  → fail → EXIT
  ↓
[4] Risk Scoring
  → low → EXIT
  → medium → WARN
  → high → semantic extraction
  ↓
[5] Semantic Extraction
  ↓
[6] Agent Review
  ↓
[7] Override System
  ↓
[8] Security Gate
  ↓
COMMIT
```
⸻

# 🧠 Final System Goal

This system ensures:

* deterministic correctness first
* architecture correctness second
* semantic reasoning only when needed
* agents only see ambiguous or high-risk changes
* exceptions are never silently lost
* observability is guaranteed structurally
* SRP is enforced across layers
* system evolution is controlled and safe

⸻

Mermaid diagram:

```mermaid
flowchart TD

%% =========================
%% ENTRY
%% =========================
A[Staged Files] --> B0[Stage 0: Diff Classification]

%% =========================
%% STAGE 0
%% =========================
B0 -->|Docs only| X0[EXIT: Skip Pipeline]
B0 -->|Formatting only| B1
B0 -->|Lockfile only| B2[Dependency Check Only]
B0 -->|Runtime code| B1
B0 -->|Migration only| B3[Migration Safety Only]
B0 -->|Tests only| B2

%% =========================
%% STAGE 1
%% =========================
B1[Stage 1: Formatting Layer] --> B1R{Formatting changed files?}
B1R -->|Yes| X1[Re-stage and exit]
B1R -->|No| C

%% =========================
%% STAGE 2
%% =========================
C[Stage 2: Micro-Quality Layer]

C -->|Fail (lint/type/async)| X2[HARD EXIT]
C -->|Pass| D

%% =========================
%% STAGE 3
%% =========================
D[Stage 3: Architecture Enforcement]

D -->|Violation| X3[HARD EXIT]
D -->|Pass| E

%% =========================
%% STAGE 4
%% =========================
E[Stage 4: Risk Scoring]

E -->|0-2| X4[EXIT: No AI]
E -->|3-5| W1[WARN]
E -->|6+| F

%% =========================
%% STAGE 5
%% =========================
F[Stage 5: Semantic Extraction] --> G[Stage 6: Agent Review]

%% =========================
%% STAGE 6
%% =========================
G -->|Reject| X5[HARD EXIT]
G -->|Warn| W2[ALLOW + COMMENT]
G -->|Approve| H[Stage 7: Override System]

%% =========================
%% STAGE 7
%% =========================
H -->|Invalid override| X6[HARD EXIT]
H -->|Valid| I[Stage 8: Security Gate]

%% =========================
%% STAGE 8
%% =========================
I -->|Security issue| X7[HARD EXIT]
I -->|Clean| J[COMMIT]
```

 Good — this is the point where your system stops being a “design” and becomes something you can actually implement.

Below is a consolidated enforcement table: libraries + exactly what they enforce in your Blobert system, mapped to your layers and rules.

⸻

# 🧱 Blobert Governance Stack — Tools + Enforced Rules

# 🟢 1. Formatting & Canonicalization Layer

Tool	Language	Enforced Rules
black	Python	Canonical formatting, line length consistency, no style debates
ruff format	Python	Unified formatting + import normalization (optional replacement for black/isort combo)
isort	Python	Import ordering: stdlib → third-party → first-party
prettier	TS/React	Consistent formatting, JSX normalization
gdformat	Godot	GDScript formatting consistency

Rules enforced:

* No manual formatting changes in PRs
* Formatting-only commits auto-exit pipeline
* Deterministic diffs only

⸻

🟡 2. Micro-Code Quality Layer (WEMAKE CORE)

Tool	Purpose	Rules Enforced
wemake-python-styleguide	Python style + cognitive discipline	SRP pressure, complexity limits, anti-pattern detection, readability constraints
ruff	Python lint engine	Syntax correctness, unused imports, unsafe patterns
eslint	TS/React linting	Code correctness + style consistency
eslint-sonarjs	TS complexity analysis	Cognitive complexity, deep nesting, long functions
typescript-eslint	Type safety	Strict typing, unsafe any usage
react-hooks	React correctness	Hook rules, dependency correctness

Rules enforced:

* Function/class complexity limits
* Nesting depth limits
* Micro-DRY enforcement (local duplication signals)
* Early detection of anti-patterns
* Hook correctness enforcement
* Type safety enforcement

⸻

❗ Exception Handling Rules (CRITICAL SYSTEM RULE)

Enforced via:

* wemake
* ruff
* semgrep
* agent review

Rules:

Rule	Description
No bare except	except: forbidden
No silent failures	except Exception: pass forbidden
No hidden returns	return None without explicit semantics forbidden
No logging-only handling	logging must not replace propagation
No swallowed exceptions	all exceptions must be handled or re-raised

Allowed patterns:

* propagate (raise)
* transform (domain exception)
* observe + propagate (log + raise)
* explicit recovery (documented fallback)

⸻

# 🟠 3. Structural Architecture Layer

Tool	Purpose	Rules Enforced
import-linter	Python dependency graph enforcement	SRP, layering, module boundaries
eslint-plugin-boundaries	Frontend architecture boundaries	Feature isolation, import restrictions
semgrep	Custom architecture rules	SRP violations, forbidden coupling, data leaks
jscpd	Duplication detection	Cross-file duplication clusters
radon/lizard	Complexity deltas	Structural complexity changes

⸻

🧱 SRP Rules (STRICT)

* Controller = HTTP only
* Service = workflow orchestration only
* Repository = persistence only
* Domain = business logic only
* Infrastructure = external systems only

Forbidden:

* controller → repository access
* domain → infrastructure imports
* service → HTTP logic
* repository → orchestration logic

⸻

🧭 Communication Boundary Rules

* no cross-feature coupling
* no reverse dependency edges
* no shared mutable domain state across layers
* strict dependency direction enforcement

⸻

🧩 Object Hierarchy Rules

* no unnecessary inheritance depth
* composition preferred over inheritance
* no empty wrapper abstractions
* abstraction must reduce complexity, not add it

⸻

🧬 Data Ownership Rules

* DTOs have single owner
* persistence writes only in repository layer
* mutation boundaries must be explicit
* no cross-layer state mutation
* cache ownership explicitly defined

⸻

🔍 Observability Rules

* structured logging required
* correlation/request ID required
* no raw logger usage
* audit events required for critical flows
* trace propagation required across services

⸻

⚡ Async Safety Rules

* no blocking calls in async context
* no unbounded task spawning
* proper cancellation handling required
* React async cleanup required
* Godot signal lifecycle correctness enforced

⸻

🚚 Migration Safety Rules

* DB migrations isolated from runtime logic changes
* API migrations must be versioned
* migration PRs must not include unrelated runtime changes
* schema changes must be paired with service updates

⸻

📊 Static Performance Budgets (RELAXED)

* max function size (soft threshold)
* max nesting depth
* React component size heuristics
* query complexity heuristics
* Godot scene complexity heuristics
* bundle growth warnings

⸻
# Dynamic Introspection Rules (CRITICAL)

The following Python dynamic reflection patterns are restricted:

## Forbidden (in application logic layers):
- getattr(obj, ...)
- setattr(obj, ...)
- hasattr(obj, ...)
- __dict__ mutation access
- direct use of __getattribute__ overrides (outside metaprogramming layer)

## Allowed ONLY in:
- serialization/deserialization layer
- framework adapters
- explicit reflection utilities module
- testing utilities

## Enforcement:
- Semgrep: HARD FAIL in domain/service/controller layers
- Wemake: soft warning (cognitive complexity signal)
- Agent layer: semantic justification required if used

## Required justification:
If used, must explicitly declare:
- why static dispatch is insufficient
- what abstraction boundary is being preserved
- why polymorphism cannot solve the issue

⸻

# 🔵 4. Duplication & Entropy Layer

Tool	Rules
jscpd	Cross-file duplication detection
eslint unused code rules	Dead code detection
vulture	Python dead code detection

Rules:

* duplication allowed locally only if abstraction cost is higher
* duplication clusters across modules must be flagged
* repeated logic across services must trigger refactor consideration

⸻

# 🟣 5. Semantic Risk Scoring Layer

(No direct tool — computed layer)

Inputs:

* wemake violations
* complexity spikes
* SRP violations
* architecture drift
* duplication clusters
* async risk
* migration risk
* observability gaps
* override usage

Output:

* 0–2 → exit
* 3–5 → warn
* 6+ → agent review

⸻

# 🤖 6. Semantic Extraction Layer

(No tool — pipeline stage)

Builds:

* dependency graph snapshot
* ownership graph
* code diff context
* related tests
* duplication clusters
* architecture violations
* async + observability context
* suppression history

⸻

# 🧠 7. Agent Review Layer

(No tool — reasoning layer)

Evaluates:

* SRP correctness
* abstraction quality
* hierarchy correctness
* ownership correctness
* observability integrity
* async safety
* migration safety
* exception handling correctness
* suppression justification

⸻

# 🔴 8. Security Layer

Tool	Rules
gitleaks	secrets detection
bandit	Python security patterns
semgrep security rules	auth, injection, deserialization
npm audit / pip-audit	dependency vulnerabilities

Hard fail rules:

* secrets detected
* unsafe deserialization
* auth bypass patterns
* critical CVEs

⸻

# 🧠 Final System Summary

This stack enforces:

📦 OOP

* SRP via architecture + semgrep + agent validation

📋 TDD

* tests + behavioral validation + contract enforcement

☔ DRY

* jscpd + duplication clustering + semantic review

💋 KISS

* wemake + complexity + cognitive load constraints

🔒 Security

* static security scanning + observability + exception safety rules

# Agent PreToolUse Governance Hook

Implement a PreToolUse hook for all agent shell/tool execution.

The hook must inspect commands BEFORE execution.

---

## Forbidden operations

Block:
- git commit --no-verify
- hook disabling
- governance config bypass
- governance script deletion
- blanket lint suppressions
- CI bypass attempts

---

## Detection requirements

The hook must:
- parse argv safely
- normalize shell commands
- detect nested shell execution
- detect multiline command bypass attempts

String matching alone is insufficient.

---

## Governance-sensitive files

Modifications to:
- .pre-commit-config.yaml
- semgrep.yml
- .github/workflows/*
- governance scripts

must:
- elevate semantic risk score
- require agent justification
- optionally require human review

---

## Escalation behavior

If governance bypass is attempted:
- block execution
- emit audit event
- require escalation