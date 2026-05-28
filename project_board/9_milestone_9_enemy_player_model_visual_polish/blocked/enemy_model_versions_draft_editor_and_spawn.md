Title:
Enemy model versions, draft lifecycle, editor load rules, and spawn-time randomization
---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | BLOCKED |
| Status | Blocked |
| Revision | 4 |
| Last Updated By | Human |
| Next Responsible Agent | Human |

---

Description:
**Umbrella ticket (M9).** Detailed implementation work is tracked in `project_board/9_milestone_9_enemy_player_model_visual_polish/` as **`01_spec_model_registry_draft_versions_and_editor_contract.md`** through **`09_automated_tests_registry_allowlist_delete.md`**. Close this ticket when those acceptance themes are satisfied end-to-end **and** default-run/player wiring in M10 (`project_board/done/10_milestone_10_procedural_enemies_in_level/backlog/integrate_new_models_into_game.md`) is complete (or explicitly waived with owner sign-off).

Original scope summary:

End-to-end pipeline so each **enemy type/family** can have **multiple visual versions** (same gameplay hooks, different mesh/silhouette), the **3D model quick editor** and game-facing UI can manage **draft vs in-use** assets, and **spawning** picks a random authorized version per type.

Scope bundles:

1. **Spawn-time random version (enemies)**  
   When an enemy of a given type is instantiated (procedural rooms, sandbox, or shared spawn helper), select **uniformly (or weighted)** among registered **active versions** for that type. All versions share the same scripts, collision contract, animation set name, and infection metadata; only the visual asset differs.

2. **UI: draft flag**  
   Asset editor (or companion UI) can mark exports as **draft** so they are excluded from default game loads until promoted.

3. **UI: which models the game uses**  
   - **Player:** exactly one **active** model path (full replacement of the current player visual).  
   - **Enemies:** **slot** additional versions per type (add/remove from the pool the spawner uses). Draft entries never enter the pool until promoted.

4. **Model editor: load from local assets**  
   Open/browse existing exports under the project’s **canonical enemy/player export roots** only. Allow picking **draft** models and **models currently slotted for the game**; **do not** expose arbitrary paths or miscellaneous GLBs outside those contracts (no loading random files from disk).

5. **Deletion**  
   Support **delete draft** (remove from draft store + files or registry per spec). Support **delete model in use** with explicit rules: either block when sole version, reassign spawner pool, or require confirmation — behavior must be specified in the spec and covered by tests.

Acceptance Criteria:
- Spawning two instances of the same enemy type can yield different GLB/version choices when multiple versions are registered; with one version, behavior matches today.
- Draft-tagged assets never appear in the default run spawn pool or default player visual until promoted via UI.
- Player “active model” UI replaces the in-game player visual; enemy UI adds/removes **version slots** without duplicating gameplay identity.
- Editor file picker (or list) only offers **draft + in-use** models from allowed asset roots; attempts to load outside the allowlist are rejected with a clear error.
- Draft deletion and in-use deletion flows are implemented per the written safety rules; automated tests cover allowlist and at least one deletion path.
- `timeout 300 ci/scripts/run_tests.sh` passes (Godot + Python suites as applicable).

## Execution plan
1. Complete `in_progress/02_mesh_and_material_audit_enemy_families_and_player.md`.
2. Complete M10 follow-up `integrate_new_models_into_game.md` (default run + player wiring).
3. Re-run full `timeout 300 ci/scripts/run_tests.sh`.
4. Verify umbrella acceptance criteria against `done/` tickets `01`, `03`–`09`, completed **02**, and **integrate_new_models_into_game.md**.

---

Blocking issues:
- **Ticket 02 (gating)** — `02_mesh_and_material_audit_enemy_families_and_player.md` is `in_progress/`; complete before this umbrella leaves BLOCKED. Child tickets `01` and `03`–`09` are in `done/`.
- **M10 integration** — `integrate_new_models_into_game.md` must land default-run/player paths before umbrella close.
- **M21** — 3D Model Quick Editor surfaces must exist or be extended for load/browse/delete; coordinate to avoid duplicate file browsers.

Unblock when ticket **02**, **integrate_new_models_into_game.md**, and remaining blocking issues are resolved; then verify acceptance against `done/` tickets `01`, `03`–`09` plus completed **02**.

## NEXT ACTION
- Finish `02_mesh_and_material_audit_enemy_families_and_player.md`, complete M10 `integrate_new_models_into_game.md`, run `timeout 300 ci/scripts/run_tests.sh`, and verify umbrella acceptance when both are done.
