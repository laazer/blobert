# M902-11: Stage 3 — Architecture Enforcement Gate

**Status:** PENDING  
**Target:** 2026-06-22

## Overview

Implement Stage 3 of the 8-stage governance pipeline: **Structural Architecture Enforcement**. Enforce SRP, layer boundaries, dependency direction, duplication, and complexity limits.

## Acceptance Criteria

- [ ] Gate runs: import-linter (Python), eslint-plugin-boundaries (TypeScript), semgrep (custom rules), jscpd (duplication), radon/lizard (complexity)
- [ ] Detects SRP violations: controller→repository, domain→infrastructure, service→HTTP logic
- [ ] Detects dependency direction violations (reverse edges, circular imports)
- [ ] Detects cross-layer state mutation and ownership boundary violations
- [ ] Detects duplication clusters (8+ lines, cross-file)
- [ ] Detects complexity spikes (function/class size, nesting depth)
- [ ] Flags async safety violations (blocking I/O in async, unbounded spawning)
- [ ] Implemented as `ci/scripts/gates/architecture_enforcement_check.py`
- [ ] Integrated into gate registry
- [ ] Tested with architecture violation vectors

## Implementation Notes

- Tool configs: `asset_generation/python/.import-linter.ini`, `asset_generation/web/frontend/eslint.config.js`, `.semgrep.yml`
- Aggregates violations from all tools into single report
- Return FAIL if SRP violations, WARN if complexity warnings, PASS if clean
- Hard exit on architecture violations in blocking mode

## Spec Reference

See: `project_board/specs/902_11_architecture_enforcement_spec.md`

## Dependencies

- M902-01 (Validation Gate Framework)
- M902-02 (Static Analysis tools baseline)
- `code_governance.md` Stage 3 architecture
