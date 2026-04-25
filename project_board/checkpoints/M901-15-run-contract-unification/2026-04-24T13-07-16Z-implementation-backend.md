### [M901-15] IMPLEMENTATION_BACKEND — run-contract module boundary
**Would have asked:** Should backend keep local command/env/output helpers or fully delegate to a shared Python module despite mixed legacy test imports?
**Assumption made:** Fully delegate to `src.utils.run_contract` and update run-router tests to assert delegation seams while preserving endpoint semantics.
**Confidence:** High

### [M901-15] IMPLEMENTATION_BACKEND — backend pytest invocation ambiguity
**Would have asked:** Which canonical invocation should be used when backend tests that import `from main import app` collide with `asset_generation/python/main.py` under mixed root execution?
**Assumption made:** Validate required suites with explicit targeted invocations through `ci/scripts/asset_python.sh` and absolute test paths, plus run existing run-router regression files individually for deterministic evidence.
**Confidence:** Medium
