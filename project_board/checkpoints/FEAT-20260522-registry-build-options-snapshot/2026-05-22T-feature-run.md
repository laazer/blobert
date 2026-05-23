# FEAT-20260522-registry-build-options-snapshot — feature run

Started: 2026-05-22  
Planner handoff: 2026-05-23

Ticket: `project_board/inbox/00_backlog/FEAT-20260522-registry-build-options-snapshot.md`

---

## Checkpoint — Planner (2026-05-23)

### Would have asked
Should player version rows use the same `build_options` key and `*.build_options.json` validation as enemies, or a separate key sourced from `*.player.json`?

### Assumption made
Spec Agent will define a player snapshot field (default assumption: same `build_options` object shape where applicable, validated against player export JSON schema; enemy rows use `parse_build_options_json` / sanitize path). Sidecars remain on disk for both; registry is canonical for API/UI reads.

### Confidence
Medium

---

### Would have asked
Should `schema_version` increment when adding `versions[].build_options`, or is an optional key on `schema_version: 1` sufficient?

### Assumption made
Keep `SCHEMA_VERSION = 1` with optional `build_options` on version rows unless spec documents a migration bump; backfill is idempotent merge from on-disk sidecars, not a destructive manifest rewrite.

### Confidence
High

---

### Would have asked
Where should post-run persistence attach the snapshot — inside `sync_discovered_animated_glb_versions`, a new service helper called from `run.py`, or a dedicated `POST` backfill endpoint only?

### Assumption made
Primary write on successful animated run: extend post-run sync path (`_sync_registry_for_family` + service) to attach snapshot from the run’s resolved `build_options` JSON or freshly written sidecar for the new `output_file` stem. Backfill for legacy rows runs in discover-sync or a spec-defined one-shot helper (idempotent).

### Confidence
Medium

---

### Dependency note (non-blocking)
`project_board/bugfix/in_progress/model-load-ui-settings.md` is **in_progress**, not `done/`. Not an umbrella child ticket. Execution plan requires preserving preview-only semantics from working-tree fix; Spec must cross-reference REQ-1/REQ-2 in that bug doc.

---

## Checkpoint — Spec Agent (2026-05-23)

### Would have asked
Should PATCH endpoints accept client-supplied `build_options` for manual correction?

### Assumption made
**No.** PATCH bodies remain `draft` / `in_use` / `name` / `tags` only; snapshots are written by export, post-run attach, and idempotent `sync_discovered_*` backfill. PATCH must preserve existing snapshots.

### Confidence
High

---

### Would have asked
For legacy player exports with only `*.player.json`, should backfill synthesize a minimal snapshot from filename color?

### Assumption made
**No synthesis.** Player backfill reads `*.build_options.json` only (new sidecar after R6). Legacy rows stay without registry snapshot until re-export or sidecar appears.

### Confidence
High

---

### Would have asked
When registry snapshot and sidecar disagree, which wins on explicit import?

### Assumption made
**Registry canonical** when `build_options` present on row; sidecar used only when registry field absent (R2).

### Confidence
High

---

### Spec output
`project_board/specs/FEAT-20260522_registry_build_options_snapshot_spec.md` — `schema_version` stays **1**; player field name **`build_options`**; player validation via **`coerce_validate_enemy_build_options("player_slime", …)`**; new player **`*.build_options.json`** export sidecar for backfill/portability.
