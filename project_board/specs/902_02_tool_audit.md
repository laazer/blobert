# M902-02 Tool Audit Document

**Date:** 2026-05-14  
**Agent:** Implementation Generalist  
**Purpose:** Comprehensive audit of all static analysis tools, their CLI invocations, config file locations, target directories, exclusion patterns, and version constraints.

---

## Tool Inventory & Configuration Map

### Python Tools (asset_generation/python)

#### 1. ruff
- **Status:** EXISTING (in pyproject.toml)
- **Version constraint:** >=0.8
- **Config location:** `asset_generation/python/pyproject.toml` ([tool.ruff] section)
- **CLI invocation:** `ruff check {target_dir}`
- **Target directories:** `asset_generation/python/src`, `asset_generation/python/tests`, `asset_generation/web/backend`
- **Exclusions:** `.venv`, `examples`, generated files (*.glb, *.png from exports)
- **Rules enabled:** E9 (runtime errors), F (Pyflakes), I (isort)
- **Output format:** Text (parseable via line regex)
- **Notes:** Existing config must be preserved. Per-file ignores in place for `__init__.py`.

#### 2. mypy (NEW)
- **Status:** TO INSTALL
- **Recommended version:** >=1.8,<2.0
- **Config location:** `asset_generation/python/pyproject.toml` ([tool.mypy] section)
- **CLI invocation:** `mypy {target_dir} --json`
- **Target directories:** `asset_generation/python/src`, `asset_generation/web/backend`
- **Exclusions:** `.venv`, `tests` (optional; can run separately)
- **Output format:** JSON
- **Notes:** Type checking tool. Will be new addition to pyproject.toml.

#### 3. bandit (NEW)
- **Status:** TO INSTALL
- **Recommended version:** >=1.7.5,<2.0
- **Config location:** `asset_generation/python/pyproject.toml` ([tool.bandit] section)
- **CLI invocation:** `bandit -r {target_dir} --format json`
- **Target directories:** `asset_generation/python/src`, `asset_generation/web/backend`
- **Exclusions:** `.venv`, test files (`tests/`), fixtures
- **Output format:** JSON
- **Notes:** Security linter. Strict but advisory in M902.

#### 4. vulture (NEW)
- **Status:** TO INSTALL
- **Recommended version:** >=2.10,<3.0
- **Config location:** `asset_generation/python/pyproject.toml` ([tool.vulture] section)
- **CLI invocation:** `vulture {target_dir} --json`
- **Target directories:** `asset_generation/python/src`
- **Exclusions:** `.venv`, `tests`, `__pycache__`
- **Output format:** JSON
- **Notes:** Dead code detector. Will skip tests.

#### 5. import-linter (NEW)
- **Status:** TO INSTALL
- **Recommended version:** >=2.13,<3.0
- **Config location:** `.import-linter` (TOML file at repo root or in asset_generation/python)
- **CLI invocation:** `lint-imports`
- **Target directories:** `asset_generation/python/src`
- **Exclusions:** Test packages, `.venv`
- **Output format:** Text (parseable via line regex)
- **Notes:** Validates import boundaries. Configuration is minimal; used to enforce layering.

#### 6. semgrep (NEW)
- **Status:** TO INSTALL
- **Recommended version:** >=1.80,<2.0
- **Config location:** `asset_generation/python/.semgrep.yml` (local rules only, no remote registry)
- **CLI invocation:** `semgrep --config {config_file} {target_dir} --json`
- **Target directories:** `asset_generation/python/src`, `asset_generation/web/backend`
- **Exclusions:** `.venv`, generated files, test fixtures
- **Output format:** JSON
- **Notes:** Static analysis engine. Uses LOCAL rules only (no remote registry in M902). Remote registry deferred to M903.

#### 7. wemake-python-styleguide (NEW)
- **Status:** TO INSTALL
- **Recommended version:** >=1.36,<2.0
- **Config location:** `asset_generation/python/pyproject.toml` ([tool.flake8] section, wemake plugin)
- **CLI invocation:** `flake8 {target_dir} --format=json`
- **Target directories:** `asset_generation/python/src`
- **Exclusions:** `.venv`, tests, migrations, generated code
- **Output format:** JSON (via flake8-json plugin)
- **Notes:** Style guide enforcement (strict). Runs on top of flake8. May overlap with ruff; both run independently. Advised: minimal enforcement in M902, grandfathering in M903.

---

### TypeScript/React Tools (asset_generation/web/frontend)

#### 8. eslint
- **Status:** EXISTING in package.json (verify/update versions)
- **Recommended version:** >=8.0,<9.0
- **Config location:** `asset_generation/web/frontend/eslint.config.js` (flat config, ES2020+)
- **CLI invocation:** `eslint {target_dir} --format json`
- **Target directories:** `asset_generation/web/frontend/src`, `asset_generation/web/frontend/tests`
- **Exclusions:** `node_modules`, `.venv`, build artifacts (`dist/`, `build/`)
- **Output format:** JSON
- **Notes:** Main linter. Config file location depends on ESLint major version (8.x uses eslint.config.js, 9.x requires it).

#### 9. @typescript-eslint/eslint-plugin (NEW/UPDATE)
- **Status:** TO INSTALL/UPDATE
- **Recommended version:** >=7.0,<8.0
- **Config location:** `asset_generation/web/frontend/eslint.config.js`
- **CLI invocation:** (via eslint)
- **Target directories:** `asset_generation/web/frontend/src`
- **Exclusions:** Non-TS files, node_modules
- **Output format:** (JSON via eslint)
- **Notes:** TypeScript-specific rules. Requires `@typescript-eslint/parser`.

#### 10. @typescript-eslint/parser (NEW/UPDATE)
- **Status:** TO INSTALL/UPDATE
- **Recommended version:** >=7.0,<8.0
- **Target:** TypeScript parsing (required by @typescript-eslint/eslint-plugin)
- **Notes:** Must match eslint-plugin version.

#### 11. eslint-plugin-react-hooks (NEW)
- **Status:** TO INSTALL
- **Recommended version:** >=4.6,<5.0
- **Config location:** `asset_generation/web/frontend/eslint.config.js`
- **Output format:** (JSON via eslint)
- **Notes:** Validates React hooks usage.

#### 12. eslint-plugin-sonarjs (NEW)
- **Status:** TO INSTALL
- **Recommended version:** >=0.25,<1.0
- **Config location:** `asset_generation/web/frontend/eslint.config.js`
- **Notes:** Quality/maintainability rules inspired by SonarQube.

#### 13. eslint-plugin-boundaries (NEW)
- **Status:** TO INSTALL
- **Recommended version:** >=4.0,<5.0
- **Config location:** `asset_generation/web/frontend/eslint.config.js`
- **Notes:** Enforces module boundaries (similar to import-linter for Python).

---

### Godot Tools (scripts/, scenes/, tests/)

#### 14. gdformat (NEW, OPTIONAL)
- **Status:** TO INSTALL (external, optional if Godot CLI unavailable)
- **Recommended version:** Latest stable
- **CLI invocation:** `gdformat {target_dir}`
- **Target directories:** `scripts/`, `scenes/`, `tests/`
- **Exclusions:** `.godot/`, `import_cache`, generated scenes
- **Output format:** Text (pass/fail, can output violations with --check)
- **Notes:** GDScript code formatter. Optional; skip if gdformat not available.

#### 15. gdlint (NEW, OPTIONAL)
- **Status:** TO INSTALL (external, optional)
- **Recommended version:** Latest stable
- **CLI invocation:** `gdlint {target_dir}`
- **Target directories:** `scripts/`, `scenes/`, `tests/`
- **Exclusions:** `.godot/`, generated code
- **Output format:** Text (parseable via line regex)
- **Notes:** GDScript linter. Optional; skip if gdlint not available.

---

### Cross-Repo Duplication Detection

#### 16. jscpd (NEW)
- **Status:** TO INSTALL (npm global or local)
- **Recommended version:** >=4.0,<5.0
- **Config location:** `jscpd.json` (at repo root)
- **CLI invocation:** `jscpd --config {config_file} {target_dir}`
- **Target directories:** Repo root (all source code)
- **Exclusions:** `*.glb`, large generated exports, `node_modules/`, `.venv/`, `reference_projects/`
- **Output format:** JSON or text
- **Notes:** Cross-language duplication detector. Threshold: 10+ lines/tokens.

---

## Scope Map: Tool → Target Directories

| Tool | Python | Backend | Frontend | GDScript | Cross-Repo |
|------|--------|---------|----------|----------|------------|
| ruff | ✓ | ✓ | - | - | - |
| mypy | ✓ | ✓ | - | - | - |
| bandit | ✓ | ✓ | - | - | - |
| vulture | ✓ | (optional) | - | - | - |
| import-linter | ✓ | - | - | - | - |
| semgrep | ✓ | ✓ | - | - | - |
| wemake | ✓ | - | - | - | - |
| eslint | - | - | ✓ | - | - |
| @typescript-eslint | - | - | ✓ | - | - |
| eslint-plugin-react-hooks | - | - | ✓ | - | - |
| eslint-plugin-sonarjs | - | - | ✓ | - | - |
| eslint-plugin-boundaries | - | - | ✓ | - | - |
| gdformat | - | - | - | ✓ | - |
| gdlint | - | - | - | ✓ | - |
| jscpd | - | - | - | - | ✓ |

---

## Exclusion Patterns (Per CLAUDE.md Guardrails)

**Universal exclusions (apply to all tools):**
- `*.glb` (3D model files)
- Large generated exports: `*_export.png`, `*_bake.png`, `*.jpg` (from asset pipeline)
- `.venv/` and `venv/` (virtual environments)
- `node_modules/` (npm packages)
- `.godot/` (Godot cache)
- `__pycache__/` (Python cache)
- `reference_projects/` (read-only reference material, per CLAUDE.md)
- `dist/`, `build/`, `.next/`, `out/` (build artifacts)

**Tool-specific exclusions:**
- **ruff, mypy, bandit, vulture, semgrep, wemake:** Tests are included (unit tests are in scope for linting); fixtures may be excluded.
- **import-linter:** Test packages excluded (no import boundaries in tests).
- **eslint, plugins:** Non-JS/TS files, vendored code.
- **gdformat, gdlint:** `.godot/` cache, import cache, generated scenes.
- **jscpd:** All of the above, plus very large binary/generated files.

---

## Version Constraints & Compatibility

### Python Ecosystem
- **Target Python:** 3.11+
- **Tool compatibility matrix:**
  - mypy >=1.8,<2.0 (supports Python 3.11)
  - bandit >=1.7.5,<2.0 (supports Python 3.11)
  - vulture >=2.10,<3.0 (supports Python 3.11)
  - import-linter >=2.13,<3.0 (supports Python 3.11)
  - semgrep >=1.80,<2.0 (supports Python 3.11)
  - wemake-python-styleguide >=1.36,<2.0 (depends on flake8, which supports Python 3.11)
  - ruff >=0.8 (Rust-based; supports Python 3.11)

### Node.js Ecosystem
- **Target Node:** 18+ (from project.json or package.json)
- **Tool compatibility matrix:**
  - eslint >=8.0,<9.0 (supports Node 18+)
  - @typescript-eslint/eslint-plugin >=7.0,<8.0 (supports Node 18+)
  - @typescript-eslint/parser >=7.0,<8.0 (supports Node 18+)
  - eslint-plugin-react-hooks >=4.6,<5.0 (supports Node 18+)
  - eslint-plugin-sonarjs >=0.25,<1.0 (supports Node 18+)
  - eslint-plugin-boundaries >=4.0,<5.0 (supports Node 18+)
  - jscpd >=4.0,<5.0 (supports Node 18+)

### Godot Ecosystem
- **Target Godot:** 4.x
- **Tools:**
  - gdformat: External tool; must be installed separately (not via pip/npm).
  - gdlint: External tool; must be installed separately.

---

## CLI Invocation Reference

### Python Tools

```bash
# ruff
ruff check asset_generation/python/src asset_generation/web/backend

# mypy
mypy asset_generation/python/src asset_generation/web/backend --json

# bandit
bandit -r asset_generation/python/src asset_generation/web/backend --format json

# vulture
vulture asset_generation/python/src --json

# import-linter
lint-imports  # (uses .import-linter config)

# semgrep
semgrep --config asset_generation/python/.semgrep.yml asset_generation/python/src asset_generation/web/backend --json

# wemake (via flake8)
flake8 asset_generation/python/src --format=json
```

### TypeScript/React Tools

```bash
# eslint
eslint asset_generation/web/frontend/src --format json

# (plugins run via eslint, no separate invocation)
```

### Godot Tools

```bash
# gdformat
gdformat scripts/ scenes/ tests/

# gdlint
gdlint scripts/ scenes/ tests/
```

### Cross-Repo Tools

```bash
# jscpd
jscpd --config jscpd.json .
```

---

## Assumptions & Decision Log

| ID | Assumption | Confidence | Fallback |
|----|-----------|-----------|----------|
| A1 | All Python tools available on PyPI | High | Skip missing tools with log |
| A2 | All npm tools available on npm registry | High | Skip missing tools with log |
| A3 | Godot CLI optional; gdformat/gdlint may not be available | High | Skip if not found |
| A4 | Web backend uses same Python tooling as asset_generation/python | High | Config paths can differ if needed |
| A5 | semgrep uses local rules only in M902; remote registry deferred to M903 | Medium | Checkpoint if remote rules required |
| A6 | jscpd threshold default 10+ lines (minTokens or minLines) | Medium | Config will document and lock this value |
| A7 | Lock files (uv.lock, package-lock.json) will be deterministic | High | Verify with determinism tests |
| A8 | Tool output is JSON or text parseable via regex | High | Fallback to text if JSON malformed |

---

## Audit Completion Status

✓ All 16 tools inventoried  
✓ Config locations mapped  
✓ Target directories specified  
✓ Exclusion patterns documented  
✓ Version constraints assigned  
✓ CLI invocations catalogued  
✓ Compatibility matrix completed  
✓ Assumptions logged  

**Next steps:** Tasks 3-5 (install dependencies, create config files, run baseline validation).
