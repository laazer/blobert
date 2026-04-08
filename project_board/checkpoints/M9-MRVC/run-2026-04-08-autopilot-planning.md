# M9-MRVC — Planning (autopilot 2026-04-08)

**Ticket:** `project_board/9_milestone_9_enemy_player_model_visual_polish/backlog/01_spec_model_registry_draft_versions_and_editor_contract.md`

## Outcome

Decomposed into: (1) author `project_board/specs/model_registry_draft_versions_spec.md` with numbered requirements + ADRs + deletion matrix + spawn interface; (2) pytest contract tests locking required headings and traceability to backlog `04`–`09`; (3) gatekeeper evidence via pytest + spec path.

### [M9-MRVC] Planning — manifest location

**Would have asked:** Should the registry live at repo root, under `asset_generation/python/`, or beside each GLB?

**Assumption made:** Single JSON manifest under `asset_generation/python/model_registry.json` (documented in ADR-001); paths inside it are relative to that directory as repo-root-relative segments matching existing export layout (`animated_exports/...`, etc.).

**Confidence:** Medium

### [M9-MRVC] Planning — Godot vs Python as source of truth

**Would have asked:** Does Godot runtime read the JSON directly or copy into a Resource?

**Assumption made:** Spec defines an abstract **registry reader contract**; first implementation may live in Python (editor backend) and Godot (spawn) with the same file as source of truth—details left to tickets `05`/`08`/`09`.

**Confidence:** Medium
