# Procedural material / color pipeline (asset_generation)

**Prefix:** PMCP-1 … PMCP-8  
**Scope:** `asset_generation/python` Blender export materials — `materials/material_system.py` and shared palette (`utils/materials.py`) only; no new per-enemy shaders unless promoted to shared helpers.

## PMCP-1 — Principled defaults survive procedural layers

For materials created via `create_material` with `add_texture=True`, **category handlers must not replace** the caller’s intended **Roughness** and **Metallic** with a full 0–1 noise drive when `force_surface` is false (default enemy finish). Organic and metallic texture handlers must keep exported PBR values **consistent** with the roughness/metallic computed in `setup_materials` / `_material_for_finish_hex` before the handler runs.

## PMCP-2 — Organic base color detail

Organic procedural variation must **preserve palette identity**: base-color modulation strength is bounded by a named constant (subtle multiply / mix), not an unexplained tuning literal embedded only in node setup.

## PMCP-3 — Finish presets

`ENEMY_FINISH_PRESETS` remains the single source for finish overrides (`glossy`, `matte`, `metallic`, `gel`, `default`). When `force_surface` is true, existing `_force_principled_value` behavior remains authoritative after handlers run.

## PMCP-4 — Hex / feature overrides

No behavior change required for `_sanitize_hex_input`, `apply_feature_slot_overrides`, or `material_for_zone_part` beyond what existing tests already specify; regressions are forbidden.

## PMCP-5 — Audit traceability

Until ticket `02_mesh_and_material_audit_enemy_families_and_player` publishes a fix-required table, ticket `03` **Validation Status** must cite either:

- explicit wont-fix/defer lines per missing audit row, or  
- this spec + code changes as the conservative stand-in for “README / code-review identified” material issues.

## PMCP-6 — Regeneration evidence

At least one **documented** regen command (in ticket `NEXT ACTION` or `Validation Status`) for an animated enemy family whose theme is materially affected (e.g. slug: tar/slime/dirt mix). Command must match repo docs (`python main.py animated <enemy>` from `asset_generation/python`).

## PMCP-7 — Testing

Automated tests must cover PMCP-1/PMCP-2 **without** a live Blender binary where possible (mocks of `bpy` data API and node graph), and must not regress existing `tests/materials/test_feature_zone_materials.py`.

## PMCP-8 — Full suite

`uv run pytest tests/` for `asset_generation/python` and `timeout 300 ci/scripts/run_tests.sh` must exit successfully before Stage `COMPLETE`.
