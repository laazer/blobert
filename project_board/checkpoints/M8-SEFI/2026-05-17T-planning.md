# Checkpoint Log: M8-SEFI (Enemy Status Effect Indicators) — PLANNING Stage

**Ticket:** project_board/8_milestone_8_enemy_attacks/in_progress/02_enemy_status_effect_indicators.md
**Stage:** PLANNING → SPECIFICATION
**Date:** 2026-05-17
**Agent:** Planner Agent

---

## Summary

Execution plan frozen for ticket 02_enemy_status_effect_indicators. Feature extends the world-space enemy UI (ticket 01_enemy_floating_health_bar, COMPLETE) with compact status effect indicator badges above the health bar.

---

## Scope Analysis

**Scope:** Display-layer only. Extends enemy_health_bar_3d.gd with new visual component for active status effects.

**Out of scope:**
- Status effect gameplay logic (add/remove/refresh happens elsewhere)
- Tooltip/hover text
- Per-effect duration countdown
- Icon art polish (placeholders acceptable)

**In scope:**
- Status icon container (new scene component)
- Subscriber pattern to enemy status-effect state
- Stable sort policy for icon ordering (stun > weaken > poison > slow > infection)
- Fallback resource for unknown effect IDs
- Multi-effect render with overflow `+N` badge
- Max visible count enforcement
- Real-time add/remove/refresh visuals

---

## Design Decisions Frozen

| Decision | Choice | Rationale | Confidence |
|----------|--------|-----------|------------|
| **Icon container type** | HBoxContainer child of EnemyHealthBar3D Control | Leverages existing Control node architecture; maintains 2D UI layer isolation | HIGH |
| **Status effect reference model** | Consumed from enemy node (meta fields or properties); display layer reads, does not manage lifecycle | Matches health bar pattern; decouples display from gameplay | HIGH |
| **Sort order** | Static enum-backed policy (stun=0, weaken=1, poison=2, slow=3, infection=4) | Deterministic, testable, matches ticket language | HIGH |
| **Overflow badge** | Label "+N" where N = (active_count - max_visible) | Simple, clear, testable | MEDIUM |
| **Fallback icon path** | `res://assets/ui/status_effects/unknown_effect.png` (configurable @export) | Prevents resource errors; test fallback with placeholder SVG or PNG | MEDIUM |
| **Max visible count** | @export tuning constant, default 5 | Matches ticket scope; allows scene-level override | MEDIUM |
| **Signal/callback pattern** | Assume enemy emits signals (status_added, status_removed, status_refreshed) OR display layer polls enemy meta each frame | Checkpoint ambiguity: gameplay system not yet defined. Assume conservative polling if no signal contract | MEDIUM |

---

## Checkpoint Ambiguities & Assumptions

### Q1: Status effect structure and lifecycle contract
**Would have asked:** How does the enemy manage active status effects? Are effects stored as:
- Array of effect IDs (strings)?
- Array of effect objects with ID and metadata?
- Enum-based flags (e.g., `has_poison: bool`)?

**Assumption made:** Assume conservative polling. Display layer reads enemy.get_meta("active_status_effects") or enemy.active_status_effects (array of strings or objects with `id` property). Spec Agent will confirm with enemy_base.gd and any status effect gameplay spec. If no array exists at implementation time, handler falls back to a state property or signals, determined by Spec Agent.

**Confidence:** MEDIUM

---

### Q2: Signal vs polling for real-time updates
**Would have asked:** Should the status indicator subscribe to enemy signals (status_added, status_removed) or poll each frame?

**Assumption made:** Assume Spec Agent will review enemy gameplay system and design the most appropriate pattern. If signals exist, use them. If no signals, poll in _process(). Initial implementation will support both (signal subscriptions with fallback polling).

**Confidence:** MEDIUM

---

### Q3: Icon asset paths and format
**Would have asked:** What is the canonical path and naming scheme for status effect icons?

**Assumption made:** Assume icons live under `res://assets/ui/status_effects/` with filenames matching effect IDs (e.g., `poison.png`, `stun.png`, `slow.png`, `weaken.png`, `infection.png`). Fallback to a shared `unknown_effect.png`. Spec Agent will confirm paths and provide or reference icon assets. If assets not available, use simple colored squares (via Godot primitives or placeholder PNGs).

**Confidence:** MEDIUM

---

### Q4: Deterministic sort order vs dynamic priority
**Would have asked:** Should status effect indicator order be static (stun always first) or dynamic (based on severity or remaining duration)?

**Assumption made:** Assume static, enum-backed sort order per ticket wording: "stun > weaken > poison > slow > infection". This is testable and deterministic. Dynamic priority (if needed later) is a follow-up ticket.

**Confidence:** HIGH

---

### Q5: Overflow badge threshold
**Would have asked:** Should the overflow badge include the count of effects beyond max visible (e.g., "+2" for 7 active effects with max 5)?

**Assumption made:** Yes. Ticket says "overflow is represented with a `+N` badge" where N = number of hidden effects. Simple and clear.

**Confidence:** HIGH

---

## Risks & Mitigation

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Status effect gameplay system (enemy state management) not yet implemented or not accessible to display layer | HIGH | **Gating:** Spec Agent will review enemy_base.gd, any existing status effect gameplay, and confirm contract. If not available, implement display-layer-only stub that reads mock data for testing. TEST_DESIGN will encode assumed contract as a fixture. |
| Icon assets not available; fallback needed | MEDIUM | Fallback resource path with guard clauses. Spec Agent confirms asset paths and sources placeholders if needed. Tests mock asset loading. |
| Performance impact of frequent status effect list scanning | MEDIUM | Implement efficient _process() check (cache last seen state, only update on change). Tests verify idempotency and re-render only when needed. |
| Scene tree structure changes (e.g., enemy prefab refactor) break health bar attachment | MEDIUM | Health bar already handles parent-child lifecycle (ticket 01). Status indicator inherits same pattern. Integration tests verify attachment. |
| Unknown effect IDs render broken textures | LOW | Fallback icon path prevents this. Tests verify fallback behavior. |

---

## Execution Plan (6 Tasks)

### Task 1: SPECIFICATION
- **Agent:** Spec Agent
- **Input:** Current ticket, enemy_base.gd, health bar implementation, any existing status effect gameplay code
- **Output:** `project_board/specs/enemy_status_effect_indicators_spec.md` with:
  - 6–10 detailed acceptance criteria (each with measurable, testable condition)
  - Status effect contract from enemy node (signals, polling interface, expected shape)
  - Icon asset paths and fallback strategy
  - Sort order normative definition
  - Max visible count guidance
  - Overflow badge behavior spec
  - Risk mitigation strategies
  - Traceability matrix (AC × test plan columns)
- **Dependencies:** None (PLANNING complete)
- **Success Criteria:** Spec document complete, all ambiguities resolved (or deferred to Test Designer with checkpoint record), no TBD sections
- **Risks/Assumptions:** Spec Agent may find status effect gameplay system incomplete; escalate if blocking (does not prevent Test Designer from writing test scaffolds)

---

### Task 2: TEST_DESIGN
- **Agent:** Test Designer Agent
- **Input:** Specification, ticket acceptance criteria, health bar test patterns
- **Output:** Test design document + primary test suite covering:
  - Icon container creation and lifecycle (initialization, add to scene tree, cleanup)
  - Multi-effect render order (stun first, then weaken, poison, slow, infection)
  - Overflow badge behavior (hidden effects count, `+N` label update)
  - Fallback icon for unknown effect IDs (no missing-resource errors)
  - Real-time update on effect add/remove/refresh (icon appears/disappears, order stable)
  - Max visible count enforcement (5 visible, overflow badge if > 5 active)
  - Integration with health bar (both health and status indicators visible, no z-order issues)
  - Edge cases: null enemy, empty effect list, rapid add/remove cycles, very large effect lists
- **Dependencies:** Task 1 (SPECIFICATION complete)
- **Success Criteria:** Primary test suite (15–20 tests) written, organized by concern (lifecycle, ordering, overflow, fallback, integration), tests are executable but expected to fail (not yet implemented)
- **Risks/Assumptions:** Tests assume status effect array accessible via mocked enemy node; if actual interface differs, update fixtures accordingly

---

### Task 3: TEST_BREAK
- **Agent:** Test Breaker Agent
- **Input:** Primary test suite, specification, ticket acceptance criteria
- **Output:** Adversarial test suite (20–30 tests) covering:
  - Null enemy, invalid enemy reference, enemy despawned mid-update
  - Malformed status effect data (missing ID, invalid type, duplicate effects)
  - Extreme cases: 100+ active effects, very rapid add/remove cycles, concurrent scene manipulations
  - Invalid icon paths, missing asset files, asset load failures
  - Sort order stability under rapid mutations
  - Memory/performance: many concurrent status indicators, rapid updates
  - Boundary values: max_visible = 0, max_visible = 1, max_visible >= 100
  - Edge cases in overflow badge (hidden count = 0, 1, 1000)
  - Determinism: identical effect sequences produce identical UI state
  - State machine: transitions from empty → 1 effect → many → empty
- **Dependencies:** Task 2 (primary tests complete)
- **Success Criteria:** Adversarial test suite complete, all tests fail (implementation not yet done), high coverage of boundary/negative cases
- **Risks/Assumptions:** Tests may assume status effect interface that differs from actual; checkpoint assumptions logged

---

### Task 4: IMPLEMENTATION_GENERALIST
- **Agent:** Implementation Agent (Generalist: GDScript + scene layout)
- **Input:** Specification, test suites (primary + adversarial), health bar scene/script (reference)
- **Output:**
  - **Scene:** `scenes/ui/enemy_status_effect_indicators.tscn` (Control root with HBoxContainer child, placeholder Label for each icon, Label for overflow badge)
  - **Script:** `scripts/ui/enemy_status_effect_indicators.gd` with:
    - Public methods: `update_from_enemy()`, `set_active_effects()`, `on_effect_added()`, `on_effect_removed()`
    - Private methods: `_render_indicators()`, `_sort_effects()`, `_load_icon()`, `_update_overflow_badge()`
    - @export vars: `enabled`, `max_visible_count`, `fallback_icon_path`, `icon_size`
    - Lifecycle: creation, parent-child management, cleanup on enemy death
  - **Integration:** Status indicator added as sibling to progress bar in `enemy_health_bar_3d.gd` or as child of existing EnemyHealthBar3D Control node
  - **Tests:** All primary + adversarial tests passing
- **Dependencies:** Task 3 (test suites complete), Spec finalized
- **Success Criteria:** Implementation complete, all primary + adversarial tests passing, no GDScript linter issues (task hooks:gd-review passes)
- **Risks/Assumptions:** If actual status effect interface differs from spec, implementation adapts and tests updated accordingly

---

### Task 5: STATIC_QA
- **Agent:** GDScript Reviewer (via task hooks or manual review)
- **Input:** Implementation (scripts + scene)
- **Output:** Review report covering:
  - Naming conventions (match existing codebase)
  - Code organization and clarity
  - Resource paths and fallback safety
  - Signal/callback patterns (match health bar patterns)
  - No unexplained tuning constants (or documented with rationale)
  - Null/empty reference safety
  - GDScript linter compliance (run `task hooks:gd-review`)
- **Dependencies:** Task 4 (implementation complete, tests passing)
- **Success Criteria:** No GDScript issues, naming and patterns consistent with project conventions, resource safety verified
- **Risks/Assumptions:** Linter passes; if issues found, route back to Implementation Agent

---

### Task 6: INTEGRATION
- **Agent:** Integration Tester (or Implementation Agent)
- **Input:** Implementation, primary + adversarial test suites
- **Output:**
  - Verify status indicator integrates with enemy_health_bar_3d.gd (both rendered together, no conflicts)
  - Verify status indicator updates when enemy status effects change (real-time responsiveness)
  - Verify all tests pass in Godot test suite (run `timeout 300 godot --headless -s tests/run_tests.gd`)
  - Verify no orphan UI nodes or memory leaks (lifecycle cleanup verified)
  - Verify debug flag (if AC 6 defined) toggles feature correctly
- **Dependencies:** Task 5 (STATIC_QA passes)
- **Success Criteria:** All tests passing (exit code 0), integration test suite confirms feature works with health bar, debug toggle works if defined, no test failures or errors
- **Risks/Assumptions:** Godot import may require refresh if scene structure changed; handled with `timeout 120 godot --headless --import`

---

## Gating Dependencies

No gating dependencies. Ticket 01_enemy_floating_health_bar is COMPLETE and provides the base UI infrastructure.

---

## Next Steps

1. **Spec Agent** reads this plan and begins Task 1 (SPECIFICATION).
2. Upon completion, update ticket Stage to `SPECIFICATION`, increment Revision, set Last Updated By: "Planner Agent", Next Responsible Agent: "Spec Agent".
3. **Test Designer** begins Task 2 once Spec is complete.
4. Pipeline continues through Tasks 3–6 sequentially.

---

## Confidence Summary

- **Scope clarity:** HIGH (ticket well-defined, out-of-scope clear)
- **Design decisions:** HIGH (most choices are deterministic and testable)
- **Ambiguity risk:** MEDIUM (status effect interface TBD, resolved via Spec Agent review)
- **Overall execution readiness:** HIGH (plan is actionable, dependencies clear, fallback strategies documented)

---

**Plan Status:** FROZEN. Ready for Spec Agent handoff.
