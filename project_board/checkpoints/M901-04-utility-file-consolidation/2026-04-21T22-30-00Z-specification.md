# [M901-04-utility-file-consolidation] Spec Agent — specification checkpoint

- Ticket: `project_board/901_milestone_901_asset_generation_refactoring/ready/04_utility_file_consolidation.md`
- Run: `2026-04-21T22-30-00Z`
- Spec artifact: `project_board/specs/m901_04_utility_file_consolidation_spec.md`

### [M901-04] SPECIFICATION — validate_glb_path error type
**Would have asked:** Should `validate_glb_path` raise `FileNotFoundError` for missing files or a single `ValueError` for all rejections?
**Assumption made:** Use **`ValueError`** with clear messages for all rejections (missing file, wrong suffix, empty file) so call sites have one exception type to catch in pipeline code unless implementation discovers an existing project convention to match.
**Confidence:** Medium

### [M901-04] SPECIFICATION — export_manifest_entry
**Would have asked:** Is `export_manifest_entry()` required in this milestone?
**Assumption made:** **Optional / deferred** — not present in codebase; add only if it removes real duplication without changing registry JSON shapes; otherwise omit (documented in R3).
**Confidence:** High

### [M901-04] SPECIFICATION — build_options as package vs single file
**Would have asked:** Literal `build_options.py` at `utils/` root vs package?
**Assumption made:** Implement **`utils/build_options/` package** with `__init__.py` as the public facade; aligns with M901-06 and avoids name collision with a sibling file.
**Confidence:** High
