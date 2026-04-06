# attack_telegraph_system — Test design (2026-04-06)

## Summary

Primary behavioral suite: `tests/scripts/enemy/test_attack_telegraph_system.gd` (AttackTelegraphSystemTests). Maps test IDs T-ATS-* to spec ATS-* / ATS-NF*.

## Spec ↔ test traceability

| Spec | Tests | Notes |
|------|-------|--------|
| ATS-1 | T-ATS-01 | `_begin_attack_cycle` / `_on_telegraph_finished` present on acid + adhesion scripts |
| ATS-2 | T-ATS-05a/b | Default `telegraph_fallback_seconds` ≥ 0.3 (export floor); wall-clock 0.3s integration deferred (SceneTree timing + run_tests invocation context) |
| ATS-3 | T-ATS-07a (partial) | `Attack` clip current after telegraph begin when controller path succeeds |
| ATS-4 | T-ATS-04a, T-ATS-04b | No projectile / no lunge velocity gate before telegraph completion path |
| ATS-5 | T-ATS-05c | `@export` + `telegraph_fallback_seconds` in acid + adhesion sources |
| ATS-6 | T-ATS-06 | `EnemyNameUtils.extract_family_name` for four slugs |
| ATS-7 | T-ATS-07a | `ranged_attack_telegraph_finished` connected after begin; Attack clip — full auto-completion via AnimationPlayer deferred to implementation / adversarial suite |
| ATS-8 | T-ATS-08 | **Fails until implementation:** `res://scripts/enemy/carapace_husk_attack.gd`, `res://scripts/enemy/claw_crawler_attack.gd` must exist |
| ATS-NF1 | (throughout) | No `await`/wall-clock; deterministic script/property checks |
| ATS-NF2 | T-ATS-NF2 | Source contains `CONNECT_ONE_SHOT` + `ranged_attack_telegraph_finished` on acid + adhesion |

## Checkpoint entries

### [attack_telegraph_system] TEST_DESIGN — Carapace/claw script paths

**Would have asked:** Exact filenames for carapace and claw attack entry scripts (spec ATS-8 allows “new files or clear branches”).

**Assumption made:** Require `carapace_husk_attack.gd` and `claw_crawler_attack.gd` under `scripts/enemy/` as stable contract paths; implementation creates or re-exports and updates tests if names differ.

**Confidence:** Medium

---

### [attack_telegraph_system] TEST_DESIGN — SceneTree during run_tests.gd

**Would have asked:** Should integration tests add nodes under `Engine.get_main_loop().root` during `SceneTree._initialize()` while `run_all()` runs?

**Assumption made:** `Node.get_tree()` was observed null for nodes added in that phase; dropped full spawn integration from T-07 and documented limitation. Ordering/no-projectile-before-cycle remains in T-04; spawn-after-signal is implementation + Test Breaker.

**Confidence:** High

---

### [attack_telegraph_system] TEST_DESIGN — ATS-2 wall-clock

**Would have asked:** How to assert 0.3s wall-clock without flaky sleeps or async `run_all`.

**Assumption made:** Encode minimum via default export ≥ 0.3; full wall-clock verification left to implementation (`max` with animation) and adversarial tests.

**Confidence:** Medium

## Spec gaps / questions for Spec Agent

1. **ATS-8 script paths:** Spec does not mandate filenames; tests fix two paths for CI. Align spec or ticket with chosen names when implementation lands.
2. **ATS-2 wall-clock:** Primary suite uses export default; confirm whether an additional named export (e.g. unified `telegraph_duration_seconds`) replaces `telegraph_fallback_seconds` — tests use current property name.

## Outcome

- Suite added; **2 tests intentionally red** (T-ATS-08) until carapace/claw attack scripts exist.
- `timeout 300 ci/scripts/run_tests.sh` will fail until T-08 passes or implementation adjusts paths + updates tests.
