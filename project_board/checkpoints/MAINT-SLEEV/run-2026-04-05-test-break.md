# MAINT-SLEEV — Test Breaker — 2026-04-05

**Ticket:** `project_board/maintenance/in_progress/sandbox_scene_legacy_external_enemy_visuals.md`  
**Spec:** `project_board/specs/sandbox_scene_legacy_external_enemy_visuals_spec.md`  
**Tests:** `tests/scenes/levels/test_legacy_enemy_visual_sandbox_scene.gd`

## Outcome

Adversarial extensions added (ADV-SLEEV-*). Source-sandbox and `project.godot` invariants run **before** the legacy file gate so CI still fails exactly once on `SLEEV-1.1_file_exists` until the duplicate `.tscn` exists, with extra guardrails on the live `test_movement_3d.tscn` and loadable `run/main_scene`.

## Matrix coverage (new / reinforced)

| Dimension | Tests |
|-----------|--------|
| Assumption / regression | `ADV-SLEEV-source_*` — main sandbox must keep four GLB refs + four `model_scene = ExtResource` lines |
| Invalid / corrupt config | `ADV-SLEEV-proj_*` — `run/main_scene` non-empty, `ResourceLoader.exists`, loads as `PackedScene` |
| Structural parity gaps | `ADV-SLEEV-spawn_*` — `RespawnZone.spawn_point` matches main vs legacy at runtime |
| Silent .tscn edits | `ADV-SLEEV-respawn_signal_connection` — exact `[connection]` line preserved |
| Type/structure / omission | `ADV-SLEEV-enemy_*` — per-enemy `[node]` block must include interp + mutation + transform tail; must not contain `model_scene` substring |
| Invalid resource strip | `ADV-SLEEV-enemy_base_ext` — legacy file must still reference `enemy_infection_3d.tscn` |
| Combinatorial / confusion | `ADV-SLEEV-one_legacy_filename` — exactly one `*legacy_enemy_visual*.tscn` under sandbox with normative basename |

## Evidence

```text
timeout 300 godot -s tests/run_tests.gd
# test_legacy_enemy_visual_sandbox_scene.gd: ADV-SLEEV-* PASS; SLEEV-1.1 FAIL until duplicate scene exists; === FAILURES: 1 ===
```

## Would have asked

- None — spec already defers SLEEV-4.2 exact `main_scene` string vs repo policy (`procedural_run.tscn`).

## Assumption made

- Implementation will name the duplicate exactly `test_movement_3d_legacy_enemy_visual.tscn` (spec normative path); `ADV-SLEEV-one_legacy_filename` enforces a single such file under `res://scenes/levels/sandbox/`.

## Confidence

High — assertions are file-text or deterministic property reads; no timing or physics dependence.

## Next

Implementation Generalist: add `test_movement_3d_legacy_enemy_visual.tscn` per SLEEV-1..3; full suite should reach `=== ALL TESTS PASSED ===`.
