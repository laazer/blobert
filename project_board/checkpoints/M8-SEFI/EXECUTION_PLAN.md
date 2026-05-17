# Execution Plan: Enemy Status Effect Indicators (M8-SEFI)

**Ticket:** project_board/8_milestone_8_enemy_attacks/in_progress/02_enemy_status_effect_indicators.md
**Status:** PLANNING COMPLETE → SPECIFICATION
**Date:** 2026-05-17
**Next Responsible Agent:** Spec Agent

---

## Project: Enemy Floating Status Effect Indicators

**Description:** Extend the world-space enemy UI with compact status effect indicator badges above the health bar. Indicators display active combat states (poison, slow, stun, weaken, infection) so players can make tactical decisions at a glance.

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|---|---|---|---|---|---|---|
| 1 | Write detailed acceptance criteria specification | Spec Agent | Ticket acceptance criteria; enemy_base.gd; health bar implementation (enemy_health_bar_3d.gd, scenes/ui/enemy_health_bar_3d.tscn); any existing status effect gameplay code | `project_board/specs/enemy_status_effect_indicators_spec.md` with 6–10 detailed AC (each measurable and testable); confirmed status effect contract (signals, polling interface, expected shape); icon asset paths or fallback strategy; sort order normative definition; overflow badge spec; risk mitigation strategies; traceability matrix (AC × test columns) | None (PLANNING complete) | Spec document complete; all checkpoint ambiguities resolved (or deferred with rationale); status effect interface contract confirmed or escalated; no TBD sections blocking Test Designer | **Gating risk:** Status effect gameplay system may not exist or may not expose state to display layer. **Mitigation:** Spec Agent escalates if blocking; Test Designer writes test scaffolds with mocked status effect interface. **Asset risk:** Icon assets not available. **Mitigation:** Spec Agent identifies fallback strategy (placeholder PNGs or Godot primitives). |
| 2 | Design and write primary test suite | Test Designer Agent | Specification from Task 1; ticket acceptance criteria; health bar test patterns (tests/ui/test_enemy_health_bar_3d*.gd); test file naming conventions | Primary test suite (15–20 tests) covering: icon container creation/lifecycle, multi-effect render order (stun > weaken > poison > slow > infection), overflow badge behavior (+N count), fallback icon for unknown IDs, real-time updates (add/remove/refresh), max visible count enforcement, integration with health bar, edge cases (null enemy, empty effects, rapid cycles, large lists). Tests executable but expected to fail. Test file naming follows behavior-descriptive pattern (not ticket IDs). | Task 1 (SPECIFICATION complete) | Primary tests written; organized by concern (lifecycle, ordering, overflow, fallback, integration); test file compiles and loads (but tests fail, which is expected); all test methods call actual methods (not scene assertions); 15–20 test count | **Assumption:** Status effect interface accessible via mocked enemy node. If actual interface differs, update fixtures. **Confidence:** MEDIUM |
| 3 | Write adversarial test suite | Test Breaker Agent | Primary test suite from Task 2; specification; ticket acceptance criteria | Adversarial test suite (20–30 tests) covering: null/invalid enemy references, malformed status data (missing ID, invalid type, duplicates), extreme cases (100+ effects, rapid cycles), invalid icon paths, asset load failures, sort order stability, performance/memory under stress, boundary values (max_visible = 0, 1, 100), overflow edge cases, determinism, state machine transitions. All tests fail (not yet implemented). | Task 2 (primary tests complete) | Adversarial tests written; high coverage of boundary/negative cases; tests fail as expected; combined primary + adversarial = 35–50 tests total | **Assumption:** Adversarial tests may assume status effect interface that differs from actual implementation. **Confidence:** MEDIUM |
| 4 | Implement status effect indicators (scene + script) | Implementation Agent (Generalist) | Specification from Task 1; primary + adversarial test suites; health bar scene/script as reference (enemy_health_bar_3d.tscn, scripts/ui/enemy_health_bar_3d.gd) | **Scene:** `scenes/ui/enemy_status_effect_indicators.tscn` (Control root with HBoxContainer child, placeholder Label nodes for icons, Label for overflow badge). **Script:** `scripts/ui/enemy_status_effect_indicators.gd` with public methods (update_from_enemy(), set_active_effects(), on_effect_added(), on_effect_removed()) and private methods (_render_indicators(), _sort_effects(), _load_icon(), _update_overflow_badge()). **@export vars:** enabled, max_visible_count, fallback_icon_path, icon_size. **Integration:** Status indicator added as child/sibling to health bar in enemy_health_bar_3d.gd or as part of EnemyHealthBar3D Control. **Tests:** All primary + adversarial tests passing (exit code 0). | Task 3 (test suites complete); Spec finalized (Task 1) | All primary + adversarial tests pass; no GDScript linter issues (task hooks:gd-review passes); implementation matches specification; no orphan UI nodes; lifecycle cleanup verified | **Risk:** Actual status effect interface differs from spec assumption. **Mitigation:** Implementation adapts to actual interface; tests updated accordingly. **Confidence:** MEDIUM-HIGH |
| 5 | Perform static GDScript review | GDScript Reviewer (via task hooks:gd-review) | Implementation scripts + scenes from Task 4 | Review report covering: naming convention compliance (match health bar patterns); code organization and clarity; resource path safety; signal/callback patterns (match health bar); documented tuning constants; null/empty reference safety; GDScript linter compliance report | Task 4 (implementation complete, tests passing) | No GDScript linter issues; naming and patterns consistent with project conventions (match health bar); resource safety verified; review report filed (can be comment in ticket or checkpoint) | **Risk:** Linter detects style issues. **Mitigation:** Route back to Implementation Agent for fixes. **Confidence:** MEDIUM (depends on implementation quality) |
| 6 | Verify integration and all tests passing | Integration Tester (or Implementation Agent) | Implementation from Task 4; primary + adversarial test suites; existing enemy_health_bar_3d integration | Run full test suite: `timeout 300 godot --headless -s tests/run_tests.gd`. Verify: status indicator integrates with health bar (both rendered, no conflicts), status effects update in real time, all tests pass (exit code 0), no orphan UI nodes, lifecycle cleanup verified, debug flag (if AC 6 defined) toggles feature correctly. Godot import may require: `timeout 120 godot --headless --import` | Task 5 (STATIC_QA passes) | All tests passing (exit code 0); integration test suite confirms feature works with health bar; debug toggle works (if applicable); no test failures or errors; status indicator visible above health bar during gameplay or test scenarios | **Risk:** Godot import hangs or timeout. **Mitigation:** Use explicit timeout (120s); fail-fast on non-zero exit. **Assumption:** Godot environment stable and imports correctly. **Confidence:** MEDIUM-HIGH |

---

## Design Decisions Frozen

| Decision | Choice | Rationale | Confidence |
|----------|--------|-----------|------------|
| **Icon container type** | HBoxContainer child of EnemyHealthBar3D Control | Leverages existing Control node architecture (from ticket 01); maintains 2D UI layer isolation; horizontal layout for badges | HIGH |
| **Status effect reference model** | Display layer reads from enemy node (meta/properties); does not manage lifecycle | Matches health bar pattern; decouples display from gameplay | HIGH |
| **Sort order** | Static enum-backed policy (stun=0 > weaken=1 > poison=2 > slow=3 > infection=4) | Deterministic, testable, matches ticket language | HIGH |
| **Overflow badge** | Label "+N" where N = (active_count - max_visible) | Simple, clear, testable | MEDIUM |
| **Fallback icon path** | `res://assets/ui/status_effects/unknown_effect.png` (@export configurable) | Prevents resource errors; test fallback with placeholder | MEDIUM |
| **Max visible count** | @export tuning constant, default 5 | Matches ticket scope; allows scene-level override | MEDIUM |
| **Signal/callback pattern** | Assume conservative polling (read enemy status each frame) OR use signals if defined; Spec Agent confirms contract | Flexible approach; accommodates both signal-driven and polling-based systems | MEDIUM |

---

## Ambiguities & Checkpoint Assumptions

| # | Question | Assumption | Confidence |
|---|----------|-----------|------------|
| 1 | **Status effect structure & lifecycle** How does enemy manage active effects? Array of IDs? Array of objects? Enum flags? | Assume conservative polling. Display layer reads enemy.get_meta("active_status_effects") or enemy.active_status_effects (array of strings or objects with `id` property). Spec Agent confirms with enemy_base.gd and any status effect gameplay spec. | MEDIUM |
| 2 | **Signal vs polling for real-time updates** Should status indicator subscribe to enemy signals or poll each frame? | Assume Spec Agent reviews and designs most appropriate pattern. If signals exist, use them. If not, poll in _process(). Implementation supports both. | MEDIUM |
| 3 | **Icon asset paths & format** Where do status effect icons live? Naming scheme? | Assume icons under `res://assets/ui/status_effects/` with filenames matching effect IDs (poison.png, stun.png, etc.). Fallback: unknown_effect.png. Spec Agent confirms paths and provides/references assets. If not available, use Godot primitives or placeholder PNGs. | MEDIUM |
| 4 | **Deterministic sort order vs dynamic priority** Static ordering (stun always first) or dynamic (based on severity/duration)? | Assume static, enum-backed order per ticket: stun > weaken > poison > slow > infection. Deterministic and testable. Dynamic priority is a follow-up ticket. | HIGH |
| 5 | **Overflow badge threshold & count** Should overflow badge show hidden effect count (e.g., "+2" for 7 effects with max 5)? | Yes. Ticket says "overflow is represented with a `+N` badge" where N = hidden effects. Simple and clear. | HIGH |

---

## Gating Dependencies

**None.** Ticket 01_enemy_floating_health_bar is COMPLETE (Stage: COMPLETE, Revision 9) and provides the base world-space UI infrastructure.

---

## Risk Register

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Status effect gameplay system not implemented or not accessible to display layer** | HIGH | Gating: Spec Agent reviews enemy_base.gd and any status effect gameplay. If not available, implement display-layer-only stub with mock data for testing. TEST_DESIGN encodes assumed contract as fixture. Escalate if blocking. |
| **Icon assets not available; fallback needed** | MEDIUM | Implement fallback resource path with guard clauses. Spec Agent confirms asset paths and sources placeholders if needed. Tests mock asset loading. |
| **Performance impact of frequent status effect list scanning** | MEDIUM | Implement efficient _process() check (cache last state, only re-render on change). Tests verify idempotency and conditional re-render. |
| **Scene tree structure changes break health bar attachment** | MEDIUM | Health bar already handles parent-child lifecycle (ticket 01). Status indicator inherits same pattern. Integration tests verify attachment. |
| **Unknown effect IDs render broken textures** | LOW | Fallback icon path prevents this. Tests verify fallback behavior. |

---

## Next Steps

1. **Spec Agent** reads this plan and begins Task 1 (SPECIFICATION).
2. Upon completion, Spec Agent updates ticket Stage to `SPECIFICATION` (already done), increments Revision, sets Last Updated By: "Spec Agent", sets Next Responsible Agent: "Test Designer Agent", updates Validation Status, and sets Status to `Proceed`.
3. **Test Designer Agent** begins Task 2 once Spec is complete and reviewed.
4. Pipeline continues through Tasks 3–6 sequentially per workflow enforcement module.
5. **After Task 6 (INTEGRATION):** Ticket moves to COMPLETE or routes to Learning Agent (if Stage 7 enabled in autonomous pipeline).

---

## Execution Readiness

- **Scope clarity:** HIGH (ticket well-defined; out-of-scope clear)
- **Design decisions:** HIGH (most choices deterministic and testable)
- **Ambiguity risk:** MEDIUM (status effect interface TBD; resolved via Spec Agent)
- **Overall readiness:** HIGH (plan actionable; dependencies clear; fallback strategies documented)

---

**Status:** FROZEN. Ready for Spec Agent handoff.
