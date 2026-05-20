# M902-28 Test Break Run

**Date:** 2026-05-20  
**Agent:** Test Breaker Agent  
**Stage:** TEST_BREAK → IMPLEMENTATION_GENERALIST

## Summary

Authored behavioral module `tests/ci/test_parallel_hook_execution.py` (11 tests, helpers for YAML/script contracts) and adversarial suite `tests/ci/test_parallel_hook_execution_adversarial.py` (19 tests). **29 passed, 1 expected red** (`test_pre_push_parallel_enabled` — `lefthook.yml` still has `pre-push.parallel: false` until Implementation Generalist Task 4).

## Adversarial coverage matrix

| Dimension | Tests |
|-----------|-------|
| Null & empty | `test_missing_pre_push_parallel_key_fails_contract` |
| Boundary / type | `test_parallel_false_string_is_not_enabled`, `test_duplicate_parallel_key_last_value_wins` |
| Invalid / corrupt | YAML mutations via `tmp_path` copies |
| Concurrency | `test_concurrent_writes_same_coverage_xml_corrupt_or_race`, stub overlap in behavioral T7 |
| Order dependency | `test_run_tests_python_before_godot_fails_ordering` |
| Combinatorial | parallel false + missing key + delegation drift |
| Mutation | godot/py script isolation, run_tests `&`, glob narrow, bash vs task |
| Assumption checks | governance `lefthook.yml` monitored, no `BLOBERT_HOOKS_PARALLEL` in impl tree |
| Determinism | 4× `--collect-only` → 30 tests each run |

## Pytest evidence

```text
$ uv run --project asset_generation/python pytest tests/ci/test_parallel_hook_execution.py tests/ci/test_parallel_hook_execution_adversarial.py -q --tb=line

F.............................                                           [100%]
=========================== short test summary info ============================
FAILED tests/ci/test_parallel_hook_execution.py::TestRequirement03LefthookParallelContract::test_pre_push_parallel_enabled
1 failed, 29 passed in 2.79s
```

```text
$ for i in 1 2 3 4; do uv run --project asset_generation/python pytest tests/ci/test_parallel_hook_execution.py tests/ci/test_parallel_hook_execution_adversarial.py --collect-only -q 2>&1 | tail -1; done

30 tests collected in 0.06s
30 tests collected in 0.04s
30 tests collected in 0.04s
30 tests collected in 0.04s
```

## Handoff

Implementation Generalist: set `pre-push.parallel: true` in `lefthook.yml`; keep delegation and TSGR scripts unchanged; re-run both test modules until **30/30 PASS**.
