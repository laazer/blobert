# MAINT-HCSI — Acceptance Criteria Gatekeeper (2026-04-05)

**Ticket:** `project_board/maintenance/done/hud_components_scale_input.md`  
**Run:** `run-2026-04-05-ac-gatekeeper`

## Evidence executed

- `timeout 300 ci/scripts/run_tests.sh` → exit 0, `=== ALL TESTS PASSED ===` (2026-04-05 gatekeeper re-run; RID leak warnings unchanged)

## AC matrix

| AC | Evidence |
|----|----------|
| Single documented scale parameter; default `1.0` preserves layout | `test_hcsi1_hud_scale_exists_and_defaults_to_one` in `tests/ui/test_hud_components_scale_input.gd`; `@export var hud_scale` + scene/script notes in `scripts/ui/infection_ui.gd` |
| All interactive/readout HUD in `game_ui.tscn` scale together (incl. input hints) | HCSI-5/HCSI-6 + adversarial tests in same file (HPBar, MoveHint, MutationIcon1, Hints subtree); `test_player_hud_layout.gd` HCSI-2 at scale 1.0 |
| `run_tests.sh` exit 0; `tests/ui` meaningful under default scale | Full suite green; dedicated HUD scale suite + layout helpers |

## Actions

- WORKFLOW STATE: Stage `COMPLETE`, Revision 7, Validation Status AC summary + re-verify command
- NEXT ACTION: Human, Proceed
- `git mv` `in_progress/hud_components_scale_input.md` → `maintenance/done/hud_components_scale_input.md`
- `CHECKPOINTS.md` entry + this log

## Outcome

COMPLETE
