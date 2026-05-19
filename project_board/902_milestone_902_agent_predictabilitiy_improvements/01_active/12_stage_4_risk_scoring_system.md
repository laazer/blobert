# M902-12: Stage 4 — Semantic Risk Scoring System

**Status:** PENDING  
**Target:** 2026-06-29

## Overview

Implement Stage 4 of the 8-stage governance pipeline: **Semantic Risk Scoring**. Compute weighted risk score from gate violations and signals to determine if high-risk changes need semantic extraction and agent review.

## Acceptance Criteria

- [ ] Risk scoring function: weighted inputs from stages 1–3
- [ ] Signals: SRP ambiguity, architecture drift, duplication clusters, async complexity, migration complexity, suppression usage, observability gaps, ownership ambiguity
- [ ] Scoring bands:
  - 0–2: EXIT (no agent review needed)
  - 3–5: WARN (non-blocking advisory)
  - 6+: ESCALATE to Stage 5 (semantic extraction)
- [ ] Scoring matrix documented with weights per signal
- [ ] Implemented as `ci/scripts/gates/risk_scoring_check.py`
- [ ] Returns JSON with: risk_score, reasoning, next_stage_recommendation
- [ ] Tested with known high/medium/low risk change patterns

## Implementation Notes

- Ingest violation data from previous gates
- Weight signals by impact (e.g., SRP violation = +3, duplication = +1)
- Recommend escalation threshold based on project risk tolerance (default: 6+)
- Non-blocking (advisory); guides routing but doesn't fail

## Spec Reference

See: `project_board/specs/902_12_risk_scoring_spec.md`

## Dependencies

- M902-01 (Validation Gate Framework)
- Stages 0–3 gate outputs (diff classification, formatting, micro-quality, architecture)
- `code_governance.md` Stage 4 architecture
