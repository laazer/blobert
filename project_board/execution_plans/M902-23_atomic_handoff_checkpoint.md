# Execution Plan: M902-23 Atomic Handoff Checkpoint

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/23_atomic_handoff_checkpoint.md`

**Status:** PLANNING COMPLETE  
**Revision:** 1  
**Date:** 2026-05-20  
**Next Agent:** Spec Agent (Task 1)  
**Checkpoint:** `project_board/checkpoints/M902-23/2026-05-20T-planning-run.md`

---

## Executive Summary

**Objective:** Formalize per-agent handoff contracts so each finishing agent must emit a structured YAML checklist in checkpoint logs before the next agent starts. Deliver `validate_handoff_checklist(ticket_id, from_agent, to_agent) -> GateResult`, a `handoff_validation_check` gate module registered in `gate_registry.json`, orchestrator invocation at stage transitions, agent runbook, and good/bad checkpoint examples.

**Scope:**
- Seven handoff pairs from ticket AC (Planner→Spec through Learning→Complete), each with required/optional items, status enum (`complete` | `incomplete` | `deferred` | `blocked`), and evidence strings
- Canonical artifact under `project_board/checkpoints/<ticket_id>/` (primary + optional per-run history)
- Gate module `ci/scripts/gates/handoff_validation_check.py` mirroring `todo_validation_check.py` patterns (path safety, agent alias map, M902-01 `violations[]` + supplementary `gaps[]` / `missing_items[]`)
- Composable with M902-20 `todo_validation_check` (both may run; distinct concerns)
- Autopilot / `.claude/skills/autopilot/SKILL.md` wiring: call gate after each stage with correct `from_agent` / `to_agent`
- Documentation: runbook + ≥3 end-to-end validated handoff pairs with pytest evidence

**Prerequisites:** M902-01 COMPLETE (`ci/scripts/gate_runner.py`, `gate_registry.json`, gate schemas). M902-20 COMPLETE (`todo_validation_check.py`, `902_20_todo_validation_spec.md`). Checkpoint protocol and `project_board/checkpoints/<ticket_id>/` layout established.

**Estimated Effort:** 9–12 agent runs (spec → tests → gate + templates → writer/orchestrator → examples/runbook → integration → static QA → AC gatekeeper)

---

## Repo Discovery (Planning Evidence)

| Asset | Path | Relevance |
|-------|------|-----------|
| Todo validation gate (pattern) | `ci/scripts/gates/todo_validation_check.py` | `validate_*` API, `GateResult`, agent normalization, checkpoint discovery, FAIL remediation |
| Gate runner | `ci/scripts/gate_runner.py` | CLI envelope, shadow/blocking modes, artifact write |
| Gate registry | `ci/scripts/gate_registry.json` | Register `handoff_validation_check` |
| M902-01 spec | `project_board/specs/902_01_gate_runner_spec.md` | Result schema, shadow semantics |
| M902-20 spec | `project_board/specs/902_20_todo_validation_spec.md` | Defers orchestrator + snapshot writer to M902-23 |
| M902-04 handoff metadata | `project_board/specs/902_04_handoff_metadata_spec.md` | Gate-risk metadata (orthogonal to YAML checklist content) |
| Spec placeholder | `project_board/specs/902_23_atomic_handoff_spec.md` | Referenced by ticket; **does not exist** — Spec Agent creates Task 1 |
| Ticket example YAML | `23_atomic_handoff_checkpoint.md` | Informative schema; spec must normative-freeze |

**Gap:** No `validate_handoff_checklist`, no handoff YAML writer contract, no registry entry, no runbook for checklist items.

---

## Task Breakdown

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| **1** | **Specification: YAML schema, per-pair catalogs, discovery, FAIL contract, orchestrator hooks** | Spec Agent | Ticket AC + example YAML; `todo_validation_check.py`; `902_20_todo_validation_spec.md` § M902-23; `workflow_enforcement_v1.md`; `checkpoint_protocol_v1.md`; stage enum mapping | `project_board/specs/902_23_atomic_handoff_spec.md` with: (a) normative `handoff` YAML root (`from_agent`, `to_agent`, `checklist[]`, `required_items_met`, `total_required_items`, `validated_at`), (b) per-item fields (`item`, `required`, `status`, `evidence`, optional `defer_reason` / `block_reason`), (c) **seven frozen catalogs** (Planner→Spec, Spec→Test Designer, Test Designer→Test Breaker, Test Breaker→Implementation, Implementation→Review, Review→Learning, Learning→Complete) mapping ticket bullets to machine-checkable evidence rules, (d) status semantics: `blocked` on any **required** item → FAIL; `deferred` allowed only when `required: false` or catalog marks deferrable with `defer_reason`; (e) artifact discovery (`handoff-latest.yaml` primary; optional `handoff-<run-id>.yaml`; fenced YAML in scoped `.md` fallback), (f) `validate_handoff_checklist(ticket_id, from_agent, to_agent)` signature and `GateResult` fields (`gaps[]`/`missing_items[]` + `violations[]` with `rule: handoff_item_missing` \| `handoff_blocked` \| `handoff_artifact_invalid`), (g) `gate_runner` contract (`handoff_validation_check`, required inputs, shadow default), (h) **composition** with `todo_validation_check` (order: todos then handoff, or spec-defined), (i) **coverage > 80%** rule for Test Designer→Test Breaker: freeze measurable definition (e.g. diff-cover on `asset_generation/python` when applicable, else “all planned test modules exist and `pytest`/`godot` collection succeeds” — no prose-only proof), (j) snapshot **writer** contract for finishing agents (when to refresh `handoff-latest.yaml`), (k) runbook section + good/bad checkpoint examples (embedded or paths), (l) autopilot invocation table: workflow Stage → `(from_agent, to_agent)` pairs. Run `python ci/scripts/spec_completeness_check.py project_board/specs/902_23_atomic_handoff_spec.md --type generic` before TEST_DESIGN. | None | Spec exit gate PASS; every ticket AC bullet mapped; blocked/deferred rules unambiguous; 3+ pair test vectors in spec. | **A1:** “Timeline estimated” (Planner AC) is subjective — spec defines minimum evidence (execution plan path + Revision bump). **A2:** Review agent may be Static QA / code-reviewer — spec aliases align with `AGENT_ALIAS_MAP`. **A3:** Learning→Complete may invoke AC Gatekeeper — spec names downstream `ac_gatekeeper`. |
| **2** | **Test design: gate behavior (3+ handoff pairs + core rules)** | Test Designer | Spec (Task 1); `tests/ci/test_todo_validation_gate.py` patterns | `tests/ci/test_handoff_validation_gate.py`: minimum cases — (1) Planner→Spec all required `complete` → PASS, (2) one required `incomplete` → FAIL lists gap, (3) required `blocked` → FAIL, (4) optional `deferred` with reason → PASS, (5) wrong `from_agent`/`to_agent` file → FAIL `handoff_pair_mismatch`, (6) missing artifact → FAIL fail-closed (not vacuous PASS unless spec allows), (7) malformed YAML → FAIL, (8) **three distinct pairs** from spec catalogs (e.g. Spec→Test Designer, Test Breaker→Implementation, Implementation→Review) with pair-specific required items, (9) `run()` + `gate_runner` smoke. `unittest.mock` + `tmp_path` fixtures only. Module docstring traces M902-23 / spec. | Task 1 | Tests red before Task 4; no markdown/ticket prose assertions. | Fixture catalogs must match spec exactly. |
| **3** | **Test break: adversarial handoff cases** | Test Breaker | Tests (Task 2), spec | +10 cases: inflated `required_items_met`, missing `evidence` on `complete`, deferred without reason on required item, duplicate checklist keys, YAML alias tricks, path traversal `ticket_id`, stale handoff file vs wrong pair, concurrent writes, empty checklist, mixed case agent names, fence-in-markdown vs `.yaml`. Four consecutive pytest runs zero flakes. | Task 2 | Bypass attempts fail closed; determinism documented. | |
| **4** | **Implementation: `validate_handoff_checklist` + gate module** | Implementation Agent (Generalist) | Spec; tests (Tasks 2–3) | `ci/scripts/gates/handoff_validation_check.py`: `validate_handoff_checklist(...)`, `run(inputs)`; PyYAML safe_load (stdlib-only preference: if PyYAML required, document in spec and `pyproject` dev dep — **spec decides**); path guards like M902-20; pair catalog lookup; FAIL payloads per spec. All Task 3 tests PASS. | Tasks 1–3 | Public API name matches ticket AC; blocked required items never PASS. | **R1:** YAML dep vs custom parser — spec Task 1 must decide. **R2:** Subjective items validated only for presence of evidence string, not truth (per test realism guardrail). |
| **5** | **Frozen checklist templates + agent writer helpers** | Implementation Agent (Generalist) | Spec catalogs | Versioned templates under `agent_context/agents/common_assets/handoff_catalogs/` (or spec path): one YAML fragment per pair for agents to copy/fill; optional `ci/scripts/handoff_snapshot.py` CLI to validate/write `handoff-latest.yaml` (if spec mandates). | Task 1 | Templates match spec item-for-item; linked from runbook. | Keep templates DRY — single source in spec/catalog files. |
| **6** | **Registry + gate_runner + doc enumeration updates** | Implementation Agent | Task 4; `gate_registry.json`; `tests/ci/test_gate_registry.py`; doc gate lists | Registry entry `handoff_validation_check` (`required_inputs`: `ticket_id`, `from_agent`, `to_agent`; optional `checkpoints_dir`; `default_mode`: `shadow`). CLI smoke documented in spec. Registry/doc tests updated. | Task 4 | Gate discoverable; shadow exit 0 on FAIL. | |
| **7** | **Orchestrator integration: stage transitions invoke gates** | Implementation Agent (Generalist) | Spec § autopilot; `.claude/skills/autopilot/SKILL.md`; `feature/SKILL.md` | Autopilot/feature skills: after each stage handoff, run `todo_validation_check` (upstream finishing agent) then `handoff_validation_check` with mapped pair; on blocking FAIL set Stage `BLOCKED` with remediation in NEXT ACTION; document commands in runbook. Checkpoint index notes wiring. | Tasks 4, 6 | Table Stage→gate commands in skill; no silent skip. | **R3:** Blocking mode may stay shadow until M903 — document. |
| **8** | **Documentation: good/bad checkpoint examples** | Integration / Spec appendix | Spec examples §; real checkpoint dirs | `project_board/checkpoints/M902-23/examples/` (or spec path): ≥1 good + ≥1 bad example per **three** handoff stages (ticket AC “examples at each stage” interpreted as ≥3 stages); README index; linked from spec and runbook. | Task 1 | Examples validate against schema (pytest or `handoff_snapshot --validate`). | |
| **9** | **Runbook: per-handoff expected items** | Integration / Documenter | Spec runbook; templates (Task 5) | `project_board/checkpoints/M902-23/HANDOFF_RUNBOOK.md` (or extend M902-08 canonical runbook if spec directs): per-pair checklist, evidence types, FAIL remediation, composition with todo gate, shadow vs blocking. | Tasks 1, 5 | Actionable without reading Python. | |
| **10** | **Integration validation: 3+ pairs end-to-end** | Integration / Autopilot Orchestrator | Tasks 4–9 | Scoped log `project_board/checkpoints/M902-23/2026-05-20T-integration-run.md` with pytest output for pair suite + three fixture pipelines producing `handoff-latest.yaml` → gate PASS/FAIL as expected. | Tasks 4–9 | Ticket AC “3+ agent pairs” evidenced with commands. | Failures logged verbatim per workflow. |
| **11** | **Static QA** | python-reviewer / Code Reviewer | Tasks 4–7 Python | Ruff-clean; typed public APIs; safe YAML; no bare `except` except documented tracking guard. | Tasks 4–7 | No blocking findings. | |
| **12** | **AC gatekeeper** | AC Gatekeeper | All outputs; ticket AC | Per-AC evidence matrix; targeted pytest + gate_runner smoke; git clean + push before COMPLETE; `git mv` ticket to `02_complete/`. | Tasks 1–11 | All AC checkboxes evidenced; runbook + examples linked. | COMPLETE blocked without push. |

---

## Dependency Matrix

| Dependency | Folder / State | Blocks M902-23? | Notes |
|------------|----------------|-----------------|----------------|
| M902-01 Validation Gate Framework | `02_complete/` | No (satisfied) | Gate runner + schemas |
| M902-20 TODO Validation Gates | `02_complete/` | No (satisfied) | Composable; writer/orchestrator scope moves here |
| M902-04 Handoff Metadata | `02_complete/` or active | No | Risk metadata ≠ YAML checklist |
| M902-08 Workflow / Runbook | `02_complete/` | No | May host links; M902-23 adds handoff section |
| Checkpoint protocol | `agent_context/.../checkpoint_protocol_v1.md` | No | Ambiguity logs separate from handoff YAML |
| M902-22 Early Stop | `01_in_progress/` / near complete | No | Shares checkpoint dir only |

**Umbrella:** No.

---

## Handoff Pair → Workflow Stage Map (Planning Default)

| Finishing agent (upstream) | Next agent (downstream) | Typical Stage transition |
|----------------------------|-------------------------|---------------------------|
| Planner | Spec | PLANNING → SPECIFICATION |
| Spec | Test Designer | SPECIFICATION → TEST_DESIGN |
| Test Designer | Test Breaker | TEST_DESIGN → TEST_BREAK |
| Test Breaker | Implementation (Generalist) | TEST_BREAK → IMPLEMENTATION_* |
| Implementation | Review (Static QA) | IMPLEMENTATION_* → STATIC_QA |
| Review | Learning | STATIC_QA → INTEGRATION (or dedicated learning stage per orchestrator) |
| Learning | AC Gatekeeper / Complete | INTEGRATION → COMPLETE |

Spec Agent may adjust stage names to match `workflow_enforcement_v1.md` enum exactly.

---

## Notes

- **M902-01 alignment:** `run()` returns `status`, `gate`, `violations`, `remediation_hints`, `message`; ticket “list of gaps” maps to `gaps[]` or `missing_items[]` plus parallel `violations[]`.
- **Test realism:** Gate checks artifact structure and required-item status; it does **not** execute pytest/ruff to verify evidence prose — evidence is attestations unless spec defines machine-verifiable hooks (e.g. path must exist).
- **Shadow mode:** Register `default_mode: "shadow"` until M903; agents still must remediate before handoff.
- **TodoWrite snapshots:** M902-23 owns refreshing `todos-latest.json` guidance in runbook if not already orchestrator-automated.
- **Spec reference path:** Ticket cites `902_23_atomic_handoff_spec.md` — Task 1 creates it (placeholder absent today).

---

## Acceptance Criteria Traceability (Planning)

| AC | Task owner |
|----|------------|
| Per-agent handoff checklists (7 pairs) | 1, 5 |
| YAML in checkpoint, structured validation | 1, 4 |
| `validate_handoff_checklist(...)` | 1, 4 |
| FAIL + gap list | 1, 4 |
| 3+ pairs tested e2e | 2, 3, 10 |
| Agent runbook | 1, 9 |
| Good/bad checkpoint examples | 1, 8 |

---

## Next Steps

**Immediate:** Spec Agent — freeze YAML schema, seven catalogs, discovery rules, and FAIL contract in `902_23_atomic_handoff_spec.md`.

**Unblocks:** Deterministic multi-agent pipeline exits; complements M902-20 todo gate at every transition.
