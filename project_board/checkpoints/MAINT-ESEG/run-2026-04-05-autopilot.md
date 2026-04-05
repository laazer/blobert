# MAINT-ESEG — enemy_script_extension_and_scene_generator

Run: 2026-04-05 autopilot (maintenance backlog)

### [MAINT-ESEG] PLANNING — Resolver key and path convention
**Would have asked:** Should optional enemy scripts be keyed by `EnemyNameUtils.extract_family_name` (per GLB slug stem) or by mutation bucket / a separate registry dict?
**Assumption made:** Primary lookup uses the same `family_name` string already computed in both generators (`extract_family_name` on GLB basename), mapped to `res://scripts/enemies/generated/<family_name>.gd` with fallback to `res://scripts/enemies/enemy_base.gd`, unless the Spec Agent documents a different contract.
**Confidence:** Medium (slug-level vs shared mutation-level script is product preference; planning defaults to slug-level to match ticket example `adhesion_bug.gd`.)

### [MAINT-ESEG] PLANNING — Editor vs headless parity
**Would have asked:** Is updating `load_assets.gd` in scope when AC only names `generate_enemy_scenes.gd`?
**Assumption made:** Yes — `LEARNINGS.md` and EMU precedent require strict parity between `load_assets.gd` and `generate_enemy_scenes.gd`; Spec Agent must include both in the blast radius and acceptance narrative.
**Confidence:** High

### [MAINT-ESEG] PLANNING — Regenerated scene churn
**Would have asked:** Must the generator be re-run and all `.tscn` committed on every resolver change?
**Assumption made:** When no override `.gd` files exist, resolver output should still select `enemy_base.gd`, so committed scenes should remain byte-stable; Implementation Agent re-runs generator once to confirm and commits only if diffs appear (per LEARNINGS: generator change + verify output).
**Confidence:** High

### [MAINT-ESEG] PLANNING — Execution plan recorded
**Would have asked:** None; ticket AC and target files are explicit.
**Assumption made:** Pipeline order Spec → Test Designer → Test Breaker → Implementation Generalist → `run_tests.sh` verification.
**Confidence:** High

**Deliverable:** `project_board/maintenance/in_progress/enemy_script_extension_and_scene_generator.md` — **Execution Plan** table (5 tasks); WORKFLOW STATE Stage `SPECIFICATION`, Revision 2, Next `Spec Agent`, Status `Proceed`.

### [MAINT-ESEG] SPECIFICATION — Resolver module and override contract

**Would have asked:** Exact filename for the new resolver under `scripts/asset_generation/`.

**Assumption made:** Spec allows implementer-chosen filename (example `enemy_root_script_resolver.gd`) but mandates a single module and no duplicated logic in the two generators.

**Confidence:** High

### [MAINT-ESEG] SPECIFICATION — Lookup key

**Would have asked:** Per full GLB basename vs `extract_family_name` stem.

**Assumption made:** Stem-only (`EnemyNameUtils.extract_family_name` output) as `family_stem`; multiple GLBs can share one override file.

**Confidence:** High

**Deliverable (spec handoff):** Ticket **Specification** filled with REQ-ESEG-1–3 and ESEG-DOC; WORKFLOW STATE Stage `TEST_DESIGN`, Revision 3, Last Updated By `Spec Agent`, Next `Test Designer Agent`, Status `Proceed`.
