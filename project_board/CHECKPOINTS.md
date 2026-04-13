# Checkpoint Index

## Run: 2026-04-11-pipeline-18-19-complete
- Tickets: `project_board/9_milestone_9_enemy_player_model_visual_polish/done/18_registry_subtabs_by_pipeline_cmd.md`, `.../done/19_model_viewer_fullscreen_button.md`
- Stage: STATIC_QA → COMPLETE (AC Gatekeeper)
- Outcome: Vitest adversarial tests + `npm run build`; tickets moved to milestone `done/`.

## Resume: 2026-04-11T21-00-00Z-ap-continue
- Ticket: `project_board/inbox/in_progress/extras-shell-visible-spikes-on-top.md` (from spec `@enemy_body_part_extras_spec.md`)
- Resuming at Stage: `TEST_BREAK`
- Next Agent: Test Breaker Agent
- Log: `project_board/checkpoints/extras-shell-visible-spikes-on-top/run-2026-04-11-autopilot.md`

### [extras-shell-visible-spikes-on-top] — OUTCOME: COMPLETE
Visible shell via `create_sphere` + `shell_scale`; spike tip factor 1.0; 55 focused pytest + full `run_tests.sh` green; spec updated for shell/spike semantics.
Log: `project_board/checkpoints/extras-shell-visible-spikes-on-top/run-2026-04-11-autopilot.md`

This file is intentionally small and acts as an index only.
Full checkpoint bodies live under `project_board/checkpoints/`.

## Index-only rules (agents must follow)

- **Do not** append checkpoint decision bodies here: no `**Would have asked:**`, no `**Assumption made:**`, no multi-paragraph assumptions.
- **Do** write those only under `project_board/checkpoints/<ticket-id>/<run-id>.md`.
- **Do** keep entries here short: run/resume headers, ticket path, stage, `Log:` path, and optional one-line outcome summaries.

## Migration

- Monolithic log frozen on 2026-03-30:
  - `project_board/checkpoints/frozen/CHECKPOINTS-2026-03-30-frozen.md`
- New write target for checkpoint details:
  - `project_board/checkpoints/<ticket-id>/<run-id>.md`
- Backward compatibility:
  - If a consumer cannot find a scoped log yet, it may read the frozen file.

---

## Run: 2026-04-11-ac-gatekeeper-registry-fix
- Ticket: `project_board/inbox/done/registry-fix-versions-slots-load.md`
- Stage: STATIC_QA → COMPLETE
- Next Agent: Human
- Log: `project_board/checkpoints/registry-fix-versions-slots-load/run-2026-04-11-ac-gatekeeper-complete.md`
- Outcome: AC gatekeeper; targeted registry pytest/Vitest green; full CI red only in unrelated shell tests; ticket moved to inbox `done/`.

## Run: 2026-04-11-test-break-registry-fix
- Ticket: `project_board/inbox/in_progress/registry-fix-versions-slots-load.md`
- Stage: TEST_BREAK → IMPLEMENTATION_BACKEND
- Next Agent: Implementation Backend Agent
- Log: `project_board/checkpoints/registry-fix-versions-slots-load/run-2026-04-11-autopilot.md`
- Outcome: Adversarial tests added (Python service, FastAPI registry routers, `registryLoadExisting` Vitest); all new tests green; handoff to backend implementation.

## Run: 2026-04-11-test-design-registry-fix
- Ticket: `project_board/inbox/in_progress/registry-fix-versions-slots-load.md`
- Stage: TEST_DESIGN → TEST_BREAK
- Next Agent: Test Breaker Agent
- Log: `project_board/checkpoints/registry-fix-versions-slots-load/run-2026-04-11-autopilot.md`
- Outcome: Spec-trace tests added; Vitest red on `canAddEnemySlot`/Add slot until R3 implementation; Python + new backend PUT test green.

## Run: 2026-04-11-spec-registry-fix
- Ticket: `project_board/inbox/in_progress/registry-fix-versions-slots-load.md`
- Stage: SPECIFICATION → TEST_DESIGN
- Next Agent: Test Designer Agent
- Log: `project_board/checkpoints/registry-fix-versions-slots-load/run-2026-04-11-autopilot.md`
- Outcome: Spec written to `project_board/specs/registry-fix-versions-slots-load.md`; assumptions appended to scoped checkpoint.

## Run: 2026-04-11T23-59-00Z-planner-decomposition
- Ticket: `project_board/inbox/in_progress/registry-fix-versions-slots-load.md`
- Stage: PLANNING → SPECIFICATION
- Next Agent: Spec Agent
- Log: `project_board/checkpoints/registry-fix-versions-slots-load/run-2026-04-11-autopilot.md`
- Outcome: Execution plan appended to ticket; assumptions logged in scoped checkpoint.

## Run: 2026-04-11T22-15-00Z-autopilot-description
- Queue mode: single ticket (created from description)
- Queue scope: registry: multiple versions, empty slots, load existing models
- Lean: no
- Log root: project_board/checkpoints/registry-fix-versions-slots-load/
- Created ticket from description: project_board/inbox/in_progress/registry-fix-versions-slots-load.md

### [registry-fix-versions-slots-load] — OUTCOME: COMPLETE
Registry: player slot GET/PUT API; frontend `in_use`/draft alignment, placeholder duplicate fix, Vitest + model_registry + router tests green. Full `run_tests.sh` still red from unrelated shell_scale failing-first tests on main.
Log: project_board/checkpoints/registry-fix-versions-slots-load/run-2026-04-11-ac-gatekeeper-complete.md

## Run: 2026-04-11T19-59-11Z-autopilot-description
- Queue mode: single ticket (created from description)
- Queue scope: "fix the extras so that the shell is actually visible and spikes properly appear on top too"
- Lean: no
- Log root: project_board/checkpoints/extras-shell-visible-spikes-on-top/
- Created ticket from description: project_board/inbox/in_progress/extras-shell-visible-spikes-on-top.md

## Run: 2026-04-11T00-00-00Z-autopilot-single
- Queue mode: single ticket
- Queue scope: `project_board/9_milestone_9_enemy_player_model_visual_polish/backlog/17_zone_extras_offset_xyz_controls.md` → `in_progress/17_zone_extras_offset_xyz_controls.md`
- Lean: no
- Log root: project_board/checkpoints/17_zone_extras_offset_xyz_controls/

## Resume: 2026-04-11T15-05-00Z-ap-continue
- Ticket: `project_board/9_milestone_9_enemy_player_model_visual_polish/done/17_zone_extras_offset_xyz_controls.md`
- Resuming at Stage: `TEST_BREAK` → implementation → `COMPLETE`
- Next Agent: (completed in-session) Engine Integration + frontend + AC closure
- Log: `project_board/checkpoints/17_zone_extras_offset_xyz_controls/run-2026-04-11-test-break.md`

### [17_zone_extras_offset_xyz_controls] — OUTCOME: COMPLETE
Per-zone offset X/Y/Z in `animated_build_options` + `zone_geometry_extras_attach`; Extras UI `SUFFIX_ORDER` / `suffixRank` / `rowDisabled`; tests + `timeout 300 ci/scripts/run_tests.sh` exit 0.
Log: `project_board/checkpoints/17_zone_extras_offset_xyz_controls/run-2026-04-11-test-break.md`

## Run: 2026-04-11T20-30-00Z-planner-decomposition
- Ticket: `project_board/inbox/in_progress/extras-shell-visible-spikes-on-top.md`
- Stage: PLANNING → SPECIFICATION
- Next Agent: Spec Agent
- Log: `project_board/checkpoints/extras-shell-visible-spikes-on-top/run-2026-04-11-autopilot.md`

## Run: 2026-04-11T-spec-agent
- Ticket: `project_board/inbox/in_progress/extras-shell-visible-spikes-on-top.md`
- Stage: SPECIFICATION → TEST_DESIGN
- Next Agent: Test Designer Agent
- Log: `project_board/checkpoints/extras-shell-visible-spikes-on-top/run-2026-04-11-autopilot.md`
- Outcome: Spec updated — shell kind promoted from v1 stub to ellipsoid overlay; shell_scale field documented; 5 spike tip call sites identified and documented; capability matrix updated.

## Run: 2026-04-11-test-break-shell-spike
- Ticket: `project_board/inbox/in_progress/extras-shell-visible-spikes-on-top.md`
- Stage: TEST_BREAK → IMPLEMENTATION_GENERALIST
- Next Agent: Engine Integration Agent
- Log: `project_board/checkpoints/extras-shell-visible-spikes-on-top/run-2026-04-11-autopilot.md`
- Outcome: Adversarial tests added (incl. `test_shell_and_spike_protrusion_adversarial.py`); 55 tests 51 fail / 4 pass pre-impl; py-review + py-organization clean; handoff to implementation.

## Run: 2026-04-11T00-00-00Z-test-design-shell-spike
- Ticket: `project_board/inbox/in_progress/extras-shell-visible-spikes-on-top.md`
- Stage: TEST_DESIGN → TEST_BREAK
- Next Agent: Test Breaker Agent
- Log: `project_board/checkpoints/extras-shell-visible-spikes-on-top/2026-04-11T00-00-00Z-test-design.md`
- Outcome: 11 attach tests (9 red / 2 green pre-implementation) + 27 options tests (25 red / 2 green pre-implementation) written; blender stub check clean; all failures confirmed against current code.

## Run: 2026-04-13T00-00-00Z-autopilot-single-m23-01
- Queue mode: single ticket
- Queue scope: `project_board/23_milestone_23_asset_editor_pipeline_mcp/backlog/01_spec_asset_pipeline_mcp_and_agent_http_api.md`
- Lean: no
- Log root: `project_board/checkpoints/01-spec-asset-pipeline-mcp/`

### [01_spec_asset_pipeline_mcp_and_agent_http_api] — OUTCOME: COMPLETE
APMCP normative spec at `project_board/specs/asset_pipeline_mcp_spec.md`, API spec completeness PASS, 26 pytest contract tests green; ticket in milestone `done/`.
Log: `project_board/checkpoints/01-spec-asset-pipeline-mcp/run-2026-04-13-autopilot.md`
