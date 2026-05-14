# Plan: Adopt Blobert Engineering Governance — Pre-commit & Repo Best Practices

**Source:** `bot_vault/architecture/code_governance.md` (792-line governance spec)  
**Scope:** Phase 1 = pre-commit hook updates + repo best-practice alignment  
**Approach:** Incremental, non-breaking, staged rollout

---

## Current State Assessment

### What exists today

| Layer | Current Tooling | Coverage |
|-------|----------------|----------|
| **Diff classification** | None | Missing |
| **Formatting** | None in hooks | Missing |
| **Python lint** | Ruff (E9, F, I only) + Pylint (too-many-statements only) | Partial |
| **Python org** | Custom `py_organization_check.py` (line counts, private imports, DRY, getattr/setattr) | Custom |
| **Python tests** | pytest + coverage + diff-cover (85% threshold) | Present |
| **GDScript lint** | Custom `gd_review_check.py` + `gd_magic_number_check.py` + `gd_organization_check.py` | Custom |
| **Frontend lint/format** | **None** (no ESLint, no Prettier) | Missing |
| **Backend lint** | **None** (bare `requirements.txt`, no pyproject.toml) | Missing |
| **Architecture** | None | Missing |
| **Security** | None | Missing |
| **Commit-msg** | Advisory conventional commit check | Present |

### Key gaps vs governance doc

1. **No diff classification** — hooks run on all staged files indiscriminately
2. **No formatting layer** — no auto-formatting or check in pre-commit
3. **Ruff is under-configured** — only E9/F/I; missing B, SIM, UP, FURB, exception handling rules
4. **No exception handling enforcement** — governance doc's CRITICAL exception rules are unenforced
5. **No structural architecture checks** — no import-linter, no semgrep, no architecture boundaries
6. **No frontend tooling** — TypeScript/React has zero lint/format
7. **No backend Python tooling** — FastAPI backend has no linting
8. **No security scanning** — no gitleaks, bandit, or dependency audit
9. **No semantic risk scoring** — governance's Stage 4 is conceptual only

---

## Phase 1: Pre-commit Hook Updates

### 1.1 Add Diff Classification (Stage 0)

**Goal:** Early exit for trivial changes; route selectively.

**Changes:**
- Create `.lefthook/scripts/classify-diff.sh`
  - Analyzes staged files to classify: docs-only, formatting-only, lockfile-only, tests-only, migration-only, runtime code
  - Exits 0 for trivial (skip remaining hooks)
  - Exits 1 for runtime code (proceed to full pipeline)
  - Exits 2 for tests-only (proceed to reduced pipeline)
- Update `lefthook.yml` to run `classify-diff` first in pre-commit; use `needs` or `skip` conditions

**Files to modify:**
- `.lefthook/scripts/classify-diff.sh` (new)
- `lefthook.yml` (modify pre-commit section)

**Risk:** Low. Pure shell script, well-scoped.

---

### 1.2 Add Formatting Layer (Stage 1)

**Goal:** Deterministic formatting before quality checks.

**Changes:**

#### Python (ruff format)
- Add `ruff format --check` to pre-commit
- Already in dev dependencies; no new installs needed

#### Frontend (Prettier)
- Install Prettier + TypeScript/React config in `asset_generation/web/frontend/`
- Add `prettier --check` to pre-commit for `**/*.{ts,tsx,js,jsx,json,css}`
- Configure for React/TypeScript conventions

#### GDScript (gdformat)
- Check if `gdformat` (from `gdtooling` package) is available
- If not, add `pip install gdtooling` to dev deps
- Add `gdformat --check` to pre-commit for `**/*.gd`

**Files to modify:**
- `lefthook.yml` (add formatting commands)
- `asset_generation/web/frontend/package.json` (add prettier devDep)
- `asset_generation/web/frontend/.prettierrc` or `prettier.config.mjs` (new)
- `asset_generation/python/pyproject.toml` (add `[tool.ruff.format]` section)

**Risk:** Medium — Prettier config may need tuning for existing code.

---

### 1.3 Enhance Python Micro-Quality (Stage 2)

**Goal:** Expand Ruff rule set to cover governance's micro-quality requirements.

**Changes:**

#### Expand Ruff rules in `asset_generation/python/pyproject.toml`
```toml
[tool.ruff.lint]
select = [
    "E9",    # Error
    "F",     # Pyflakes
    "I",     # isort
    "B",     # flake8-bugbear (exception handling, unsafe defaults)
    "SIM",   # flake8-simplify
    "UP",    # pyupgrade
    "FURB",  # flake8-duplicate-view-fields
    "C90",   # mccabe (complexity)
    "W",     # pycodestyle warnings
]
```

#### Add exception handling rules (CRITICAL from governance doc)
- Ruff `B017` (catching `Exception` without logging)
- Ruff `B012` (return in except/finally)
- Ruff `B024` (abstract base class without abstract methods)
- Custom semgrep rules for:
  - `except: pass` → forbidden
  - `except Exception: pass` → forbidden
  - `logging only` without re-raise → forbidden

#### Add complexity limits
- McCabe max-complexity = 10 (per governance's cognitive load limits)
- Already partially covered by Pylint's too-many-statements

**Files to modify:**
- `asset_generation/python/pyproject.toml` (expand Ruff select, add complexity config)
- `.lefthook/scripts/` or `ci/scripts/` (new semgrep config + hook)
- `pyproject.toml` (add `semgrep` to dev deps)

**Risk:** Medium — expanding Ruff rules may flag existing violations; need to audit first.

---

### 1.4 Add Structural Architecture Enforcement (Stage 3)

**Goal:** Enforce SRP, communication boundaries, data ownership.

**Changes:**

#### Python: import-linter
- Add `import-linter` to dev deps
- Create `.importlint` config enforcing:
  - Layer boundaries: controllers → services → repositories (no cross-layer)
  - No forbidden imports (e.g., domain → infrastructure)
  - Feature isolation

#### Python: semgrep architecture rules
- Create `.semgrep/rules/` with custom rules for:
  - SRP violations (controller accessing repository directly)
  - Forbidden import patterns
  - Data ownership violations

#### Frontend: ESLint + TypeScript ESLint
- Add ESLint with `@typescript-eslint/parser` + `@typescript-eslint/recommended`
- Add `eslint-plugin-react-hooks` for React correctness
- Add `eslint-plugin-boundaries` for architecture boundaries
- Create `asset_generation/web/frontend/eslint.config.mjs`

#### Frontend: TypeScript strictness
- Update `tsconfig.json`: enable `noUnusedLocals`, `noUnusedParameters`, `verbatimModuleSyntax`
- These are already partially enabled

**Files to modify:**
- `asset_generation/python/pyproject.toml` (add import-linter, semgrep)
- `.importlint` (new)
- `.semgrep/rules/` (new directory with rule YAML files)
- `lefthook.yml` (add import-linter, semgrep, eslint commands)
- `asset_generation/web/frontend/package.json` (add eslint deps)
- `asset_generation/web/frontend/eslint.config.mjs` (new)
- `asset_generation/web/frontend/tsconfig.json` (update strictness)

**Risk:** High — import-linter and ESLint configs need careful tuning to avoid blocking development.

---

### 1.5 Add Security Gate (Stage 8)

**Goal:** Pre-push security scanning.

**Changes:**

#### Add to pre-push hooks:
- `gitleaks` — secret detection (pre-commit or pre-push)
- `bandit` — Python security patterns (in `py-tests.sh` or separate hook)
- `npm audit` or `npm audit --production` — frontend dependency audit

**Files to modify:**
- `lefthook.yml` (add security commands to pre-push)
- `.lefthook/scripts/py-tests.sh` (add bandit step)
- `asset_generation/python/pyproject.toml` (add bandit to dev deps)
- New: `.gitleaks.toml` (gitleaks config)

**Risk:** Low — these are standard tools with minimal config.

---

### 1.6 Add Backend Python Linting

**Goal:** Bring the FastAPI backend into the governance framework.

**Changes:**
- Create `asset_generation/web/backend/pyproject.toml` with:
  - Ruff config (same rule set as asset_generation/python)
  - pytest config
  - Package metadata
- Add backend to pre-commit hooks (ruff check on `asset_generation/web/backend/**/*.py`)
- Add backend to pre-push (pytest)

**Files to modify:**
- `asset_generation/web/backend/pyproject.toml` (new)
- `lefthook.yml` (add backend path globs)
- `Taskfile.yml` (add `hooks:backend-review` task)

**Risk:** Low — straightforward configuration.

---

### 1.7 Add Frontend Testing

**Goal:** Ensure frontend tests run in CI and pre-push.

**Changes:**
- Already has Vitest configured in `package.json`
- Add `task hooks:web` to Taskfile.yml
- Add `web-tests` to pre-push in `lefthook.yml` (run when `asset_generation/web/**/*.{ts,tsx}` changes)

**Files to modify:**
- `lefthook.yml` (add web-tests pre-push hook)
- `Taskfile.yml` (add hooks:web task)

**Risk:** Low — already partially set up.

---

## Phase 2: Repo Best-Practice Alignment

### 2.1 Exception Handling Cleanup

**Goal:** Align existing code with governance's exception handling rules.

**Approach:**
1. Run semgrep to find violations of:
   - `except: pass`
   - `except Exception: pass`
   - logging-only handlers without re-raise
2. Fix violations systematically
3. Add to `.gitleaks.toml` or semgrep config as hard-fail rules

**Files likely affected:**
- `asset_generation/python/src/` (Blender pipeline — most likely)
- `asset_generation/web/backend/` (FastAPI — possible)
- `ci/scripts/` (shell scripts — N/A)

**Risk:** Medium — may require touching many files.

---

### 2.2 Code Size Reduction

**Goal:** Address governance's complexity limits on existing files.

**Current violations (from governance doc + analysis):**
| File | Lines | Governance Limit | Action |
|------|-------|------------------|--------|
| `schema.py` | 1,888 | 1,500 | Split into submodules |
| `material_system.py` | 1,483 | 1,500 | Near limit; monitor |
| `service.py` (model_registry) | 1,223 | 1,500 | Near limit; monitor |
| `attachment.py` | 1,217 | 1,500 | Near limit; monitor |
| `player_controller_3d.gd` | 687 | 900 | Near limit; monitor |
| `movement_simulation.gd` | 507 | 900 | OK |

**Action:** Schedule as separate tickets. Not part of Phase 1.

---

### 2.3 Backend Requirements → pyproject.toml Migration

**Goal:** Standardize Python project metadata.

**Changes:**
- Migrate `asset_generation/web/backend/requirements.txt` to `pyproject.toml`
- Add proper package metadata, dependencies, dev dependencies
- Align with `asset_generation/python/pyproject.toml` conventions

**Files to modify:**
- `asset_generation/web/backend/pyproject.toml` (new, created in 1.6)
- `asset_generation/web/backend/requirements.txt` (delete or mark as legacy)

**Risk:** Low.

---

### 2.4 Add .semgrep/config.yaml

**Goal:** Centralize semgrep rules for the project.

**Contents:**
- Exception handling rules (hard fail)
- SRP architecture rules (hard fail)
- Forbidden import patterns (hard fail)
- Security rules (bandit-compatible)
- Custom blobert-specific rules

**Files to modify:**
- `.semgrep/config.yaml` (new)
- `.semgrep/rules/` (new directory)

**Risk:** Medium — needs careful rule tuning.

---

## Execution Order & Dependencies

```
Phase 1 (Pre-commit Hooks):
  1.1 Diff classification ──────────────→ low effort, no dependencies
  1.6 Backend pyproject.toml ───────────→ low effort, no dependencies
  1.3 Expand Ruff rules ────────────────→ medium effort, audit first
  1.2 Formatting layer ─────────────────→ medium effort, needs prettier install
  1.4 Architecture enforcement ─────────→ high effort, needs import-linter + eslint
  1.5 Security gate ────────────────────→ low effort, standard tools
  1.7 Frontend testing ─────────────────→ low effort, already configured

Phase 2 (Repo Best-Practices):
  2.1 Exception handling cleanup ───────→ medium effort, needs semgrep scan
  2.2 Code size reduction ──────────────→ separate tickets
  2.3 Backend requirements migration ───→ low effort
  2.4 Semgrep config ───────────────────→ medium effort
```

---

## Rollout Strategy

### Step 1: Audit (no breaking changes)
- Run expanded Ruff rules on current codebase → identify violations
- Run semgrep on current codebase → identify violations
- Run Prettier --check on frontend → identify violations
- Document violations by severity (must-fix vs can-allow)

### Step 2: Add tooling (non-blocking)
- Add diff classification as advisory-only first
- Add formatting as --check (non-blocking) in pre-commit
- Add backend pyproject.toml
- Add frontend ESLint config (non-blocking)

### Step 3: Gradual enforcement
- Enable Ruff expanded rules one group at a time (B → SIM → UP → FURB)
- Enable ESLint rules incrementally
- Enable architecture enforcement after audit
- Enable security gate on pre-push only (not pre-commit)

### Step 4: Final state
- All hooks enforcing their respective rules
- Coverage: Python lint, frontend lint, formatting, security, architecture
- Governance doc's Stages 0-3 and Stage 8 implemented; Stages 4-7 deferred

---

## Deferred / Out of Scope for Phase 1

| Governance Stage | Why Deferred | When to Implement |
|-----------------|--------------|-------------------|
| Stage 4: Risk scoring | Requires custom infrastructure | After hooks are stable |
| Stage 5: Semantic extraction | Requires custom infrastructure | After hooks are stable |
| Stage 6: Agent review | Requires agent integration | After hooks are stable |
| Stage 7: Override system | Requires convention + tooling | After hooks are stable |
| Code size reduction | Separate refactoring effort | Scheduled as individual tickets |

---

## Files Summary

### New files to create
1. `.lefthook/scripts/classify-diff.sh` — diff classifier
2. `asset_generation/web/frontend/.prettierrc` — Prettier config
3. `asset_generation/web/frontend/eslint.config.mjs` — ESLint config
4. `asset_generation/web/backend/pyproject.toml` — backend project config
5. `.semgrep/config.yaml` — semgrep rules
6. `.semgrep/rules/` — semgrep rule directory
7. `.importlint` — import-linter config
8. `.gitleaks.toml` — gitleaks config

### Existing files to modify
1. `lefthook.yml` — add all new hooks
2. `asset_generation/python/pyproject.toml` — expand Ruff rules, add dev deps
3. `asset_generation/web/frontend/package.json` — add Prettier + ESLint deps
4. `asset_generation/web/frontend/tsconfig.json` — tighten strictness
5. `Taskfile.yml` — add new hook tasks
6. `.lefthook/scripts/py-tests.sh` — add bandit step
7. `.lefthook/scripts/py-review.sh` — expand to cover backend paths

### Files to audit before implementation
1. `asset_generation/python/src/` — Ruff violations
2. `asset_generation/web/frontend/src/` — Prettier/ESLint violations
3. `asset_generation/web/backend/` — Ruff violations
4. `scripts/` — GDScript organization violations

---

## Success Criteria

- [ ] Pre-commit: diff classification runs first, exits early for trivial changes
- [ ] Pre-commit: Python formatting check (ruff format --check)
- [ ] Pre-commit: Frontend formatting check (prettier --check)
- [ ] Pre-commit: Ruff expanded rules (B, SIM, UP, FURB)
- [ ] Pre-commit: Frontend ESLint (TypeScript + React)
- [ ] Pre-commit: Backend Ruff lint
- [ ] Pre-commit: GDScript organization + magic number checks (existing, unchanged)
- [ ] Pre-push: gitleaks security scan
- [ ] Pre-push: bandit Python security scan
- [ ] Pre-push: frontend npm audit
- [ ] Pre-push: Python tests + coverage + diff-cover (existing, unchanged)
- [ ] Pre-push: Godot tests (existing, unchanged)
- [ ] Pre-push: frontend Vitest tests
- [ ] Commit-msg: advisory conventional commit (existing, unchanged)
- [ ] All existing hooks preserved and functional
- [ ] No breaking changes to developer workflow
