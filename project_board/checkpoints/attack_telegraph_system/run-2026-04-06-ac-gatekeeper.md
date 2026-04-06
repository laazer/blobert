### [attack_telegraph_system] STATIC_QA → COMPLETE — AC gatekeeper

**Would have asked:** Whether “Works for all 4 enemy families” requires T-ATS-04-style SceneTree tests for carapace/claw or is satisfied by script existence, `@export` telegraph fields, NF2 wiring (ADV-ATS-07/08), and `EnemyInfection3D` attack node wiring.

**Assumption made:** Ticket spec and test suite intentionally give acid/adhesion full behavioral telegraph tests (T-ATS-04, T-ATS-07) and carapace/claw contract/minimal-path coverage (T-ATS-08, ADV-ATS-07/08) plus family slug extraction (T-ATS-06); that combination satisfies AC for this milestone.

**Confidence:** Medium

---

**Evidence recorded (2026-04-06):**

- `timeout 300 ci/scripts/run_tests.sh` → exit **0**; log includes `=== ALL TESTS PASSED ===` and Python `419 passed`.
- Primary: `tests/scripts/enemy/test_attack_telegraph_system.gd` — maps to ≥0.3 s defaults (T-ATS-05), no damage path during telegraph for acid/adhesion (T-ATS-04), Attack clip / telegraph signal (T-ATS-07), four-family slugs + carapace/claw script presence (T-ATS-06/08), exports (T-ATS-05c).
- Adversarial: `tests/scripts/enemy/test_attack_telegraph_system_adversarial.gd` — ATS-2 floor clamps (ADV-ATS-02/03), NF2 and carapace/claw exports when present (ADV-ATS-07/08), re-entry guards (ADV-ATS-04, 09, 10).
- Normative spec: `project_board/specs/attack_telegraph_system_spec.md` (ticket cross-reference unchanged).

**Outcome:** Stage set to `COMPLETE`; ticket moved to `project_board/8_milestone_8_enemy_attacks/done/attack_telegraph_system.md`.
