# Blog context — M902-25

- **Ticket:** M902-25 — Pydantic + Zod dual validation (pilot)
- **Goal:** Runtime validate three GET APIs on backend (Pydantic) and frontend (Zod)
- **Outcome:** COMPLETE (pilot scope)
- **Commit:** 15c1395 `feat(web): dual Pydantic/Zod validation on three pilot GET APIs`
- **Checkpoint log:** project_board/checkpoints/M902-25/2026-05-21T-implementation-run.md
- **Surprises:** Live meta controls include `fill_picker` and `select_str.hint` not in initial unions — caught by `test_meta_router`, not minimal drift fixtures
- **Handoff:** Gate required path evidence for ruff (`gate-results-ruff-pilot.txt`); spec handoff paths must be repo-relative
- **Scope:** Spec Req 12 defers full-router coverage; ticket AC “100%” applies to health/registry/meta only
- **Tests:** 25 pytest + 22 Vitest pilot + 12 adversarial sync
