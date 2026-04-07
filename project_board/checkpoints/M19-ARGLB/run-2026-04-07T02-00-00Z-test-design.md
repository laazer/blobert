# Checkpoint Log — M19-ARGLB Test Design Run

**Run ID:** run-2026-04-07T02-00-00Z-test-design
**Agent:** Test Designer Agent
**Stage:** TEST_DESIGN
**Ticket:** project_board/19_milestone_19_3d_model_quick_editor/in_progress/assets_router_and_glb_viewer.md

---

### [M19-ARGLB] TEST_DESIGN — settings.python_root override strategy
**Would have asked:** How should tests override `settings.python_root` to point at a temporary directory with controlled fixture files, without modifying global state or requiring a real on-disk export tree?
**Assumption made:** Use `pytest` `tmp_path` fixtures + `monkeypatch` to patch `core.config.settings.python_root` before each test. The app is imported fresh via `ASGITransport(app=app)` so settings patching via monkeypatch on the module attribute is sufficient. Each test creates its own tmp directory structure for deterministic behavior.
**Confidence:** High

### [M19-ARGLB] TEST_DESIGN — ARGLB-3.5 directory-as-path behavior
**Would have asked:** ARGLB-3.5 says "preferred behavior is HTTP 404" for a path that resolves to a directory. Should the test assert 404 firmly or leave it as a soft assertion?
**Assumption made:** Write the strictest defensible test: assert the response is 4xx (either 404 or 500). Do not assert exactly 404 since the spec says "preferred" not "required". Mark the test with a comment referencing ARGLB-3.5.
**Confidence:** Medium

### [M19-ARGLB] TEST_DESIGN — app import path for ASGITransport
**Would have asked:** The `main.py` is under `asset_generation/web/backend/`. Running pytest from that directory vs the repo root affects import resolution. Which is canonical?
**Assumption made:** Tests will be run from `asset_generation/web/backend/` (matching the ticket's `cd asset_generation/web/backend && python -m pytest` command). conftest.py adds the backend dir to `sys.path` if needed so `from main import app` resolves correctly.
**Confidence:** High

### [M19-ARGLB] TEST_DESIGN — httpx normalizes .. in URLs before sending
**Would have asked:** Tests for ARGLB-3.1/3.2/3.7 use literal `..` in URLs. httpx normalizes these before the request reaches the server (e.g., `/api/assets/../../main.py` becomes `/main.py`). Should these tests be kept as-is (they will fail because 404 from route miss, not 400 from guard) or should they use URL-encoded dots?
**Assumption made:** Keep the literal-dot tests but document the normalization. Add separate tests using URL-encoded `%2e%2e` variants (which httpx does NOT normalize) to test the actual server-side path guard. The literal `..` tests document the httpx normalization behavior and correctly fail until implementation changes routing to handle normalized paths — or they become documentation tests. The URL-encoded variants are the security-relevant tests.
**Confidence:** High

### [M19-ARGLB] TEST_DESIGN — directory path returns 500 not 404
**Would have asked:** ARGLB-3.5 says "preferred HTTP 404" for directory paths. Current scaffold raises RuntimeError(500) from FileResponse when path is a directory. Should test assert 404 strictly?
**Assumption made:** Assert `!= 200` (i.e., not 200) to capture both 404 and 500 as non-200. The Implementation agent must fix FileResponse to explicitly check `is_file()` and return 404. Tests document the current broken behavior.
**Confidence:** High

### [M19-ARGLB] TEST_DESIGN — list endpoint filter: subdirectories excluded
**Would have asked:** ARGLB-1 says only files at the top level are included and subdirectories are excluded. The implementation uses `f.suffix in _MIME` which for a directory `d` would have `d.suffix == ""` (not in _MIME). This means subdirectories are implicitly excluded by the MIME filter rather than by an explicit `f.is_file()` check. Should the test verify this behavior?
**Assumption made:** Yes, test this as an observable behavior: a subdirectory inside an export dir must not appear in the assets list. This is lockable from spec ARGLB-1 constraint "Subdirectories within an export directory are excluded."
**Confidence:** High
