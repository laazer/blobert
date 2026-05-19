# M902-13: Stage 5 — Semantic Extraction & Bundling

**Status:** PENDING  
**Target:** 2026-07-06

## Overview

Implement Stage 5 of the 8-stage governance pipeline: **Semantic Extraction Layer**. Build focused review bundles from high-risk changes for agent semantic review (Stage 6).

## Acceptance Criteria

- [ ] Extracts: changed code, dependency neighborhood, ownership graph, related abstractions, tests, duplication clusters, architecture violations, async boundaries, observability gaps, suppression history
- [ ] Generates `.semantic_reviews/<issue_id>.json` bundle (< 100KB, focused context)
- [ ] Includes: file diffs, related test code, affected modules, ownership assignments, violation summaries
- [ ] Does NOT include: full repo context, unrelated files, generated artifacts
- [ ] Implemented as `ci/scripts/gates/semantic_extraction_check.py`
- [ ] Outputs JSON schema documented
- [ ] Tested with complex multi-file changes

## Implementation Notes

- Parse git diff to extract changed code hunks
- Use import graph to find dependency neighbors (1–2 hops)
- Grep for related tests (by module name)
- Extract ownership from CODEOWNERS or team assignments
- Build compressed bundle suitable for agent context window

## Spec Reference

See: `project_board/specs/902_13_semantic_extraction_spec.md`

## Dependencies

- M902-01 (Validation Gate Framework)
- M902-12 (Risk Scoring System)
- `code_governance.md` Stage 5 architecture
