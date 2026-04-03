# M7-ACS Planning Checkpoints — run-2026-04-01

---

### [M7-ACS] Planning — state system to drive animation controller

**Would have asked:** The ticket description mixes two state enums.
`EnemyStateMachine` uses string constants (`idle`, `active`, `weakened`,
`infected`, `dead`) while `EnemyBase` exposes a separate integer enum
(`NORMAL=0`, `WEAKENED=1`, `INFECTED=2`, no DEAD). Which is the canonical
source of truth for the animation controller? Should the controller read
`EnemyStateMachine.get_state()` (strings), `EnemyBase.get_base_state()` (enum
int), or both?

**Assumption made:** `EnemyStateMachine` is the canonical source. It is the
pure lifecycle machine that tracks all five states including `active` and
`dead`. `EnemyBase.State` is an older, narrower representation used for
external coordination. The animation controller will call
`EnemyStateMachine.get_state()` and map its string values to animation clips.
The `NORMAL` label in the ticket is treated as equivalent to `idle`/`active`
in `EnemyStateMachine` terms.

**Confidence:** Medium

---

### [M7-ACS] Planning — how the controller receives its EnemyStateMachine reference

**Would have asked:** `EnemyStateMachine` is a `RefCounted` pure-logic object,
not a Node child. How does the animation controller get its reference — via
`get_parent()` cast to `EnemyBase` and a method call, via an `@export` var set
at scene construction, or via a signal/bus?

**Assumption made:** The controller will accept the `EnemyStateMachine`
reference through an `@export` var (or a `setup(esm: EnemyStateMachine)` init
method). This is the most testable pattern (mock-friendly, no Node dependency
required in tests). The Spec Agent will choose the exact API surface; both
options are documented in the spec as acceptable.

**Confidence:** Medium

---

### [M7-ACS] Planning — movement detection for Walk vs Idle within NORMAL/active state

**Would have asked:** The ticket says "NORMAL + moving → Walk". The animation
controller is a child Node, not the movement controller. How does it determine
that the enemy is currently moving? `EnemyStateMachine` has no velocity
concept. Options: (a) check `owner.velocity.length() > threshold` where owner
is `EnemyBase` (CharacterBody3D), (b) require the caller to push a move event,
(c) receive a `is_moving` boolean via a setter each physics frame.

**Assumption made:** The controller will read `owner.velocity` (casting owner
as `CharacterBody3D`) each `_process` frame. A configurable threshold
(`@export var move_threshold: float = 0.1`) distinguishes idle from walking.
This keeps the contract simple and avoids adding a new API to `EnemyStateMachine`.

**Confidence:** Medium

---

### [M7-ACS] Planning — "on hit received" signal source

**Would have asked:** The `Hit` animation is triggered "on damage received".
There is no `hit_received` signal visible in the existing scripts. What emits
this event — a signal on `EnemyBase`, a call from a combat resolver, or a
dedicated `AnimationController.play_hit()` method called externally?

**Assumption made:** The controller will expose a public method
`trigger_hit_animation()` that callers invoke. This is the most decoupled
approach and is trivially testable without a real combat system. The Spec Agent
should document which caller is responsible for invoking it.

**Confidence:** High

---

### [M7-ACS] Planning — AnimationPlayer node path in generated scenes

**Would have asked:** The current `generate_enemy_scenes.gd` does not add an
`AnimationPlayer` to generated scenes. Should the scene generator be updated
as part of this ticket, or will the AnimationPlayer be added later by the
`blender_animation_export` ticket when GLBs are imported?

**Assumption made:** The animation controller must be defensively coded to
handle a missing or null `AnimationPlayer` without crashing (guard at `_ready`
with an early return and a warning). The `generate_enemy_scenes.gd` update
(adding the AnimationPlayer node) is a separate sub-task scoped to the
Implementation Agent for this ticket. This way the controller + scene generator
changes ship as one unit, and the exported clips simply appear later.

**Confidence:** Medium

---

### [M7-ACS] Planning — test strategy for headless AnimationPlayer

**Would have asked:** `AnimationPlayer` requires a scene tree to function.
Tests must run headlessly via `run_tests.sh`. Should tests use a real
`AnimationPlayer` added to a minimal scene, or a mock/stub class?

**Assumption made:** Tests will use a lightweight stub class defined inline in
the test file (a plain `RefCounted` or inner class that implements just the
`play(name, blend)`, `stop()`, `is_playing()`, `current_animation` surface).
The controller will be designed to accept its `AnimationPlayer` reference
through a `@export` var (or `setup()`) so a stub can be injected. No real
`AnimationPlayer` Node is required for the unit tests.

**Confidence:** High

---

### [M7-ACS] Planning — blender_animation_export dependency

**Would have asked:** The `blender_animation_export` ticket has not run.
Should this controller ticket be blocked until clips exist, or proceed with
stub-based tests that verify behavior against named clip strings?

**Assumption made:** Proceed. The controller is written against the documented
clip name strings (`Idle`, `Walk`, `Hit`, `Death`) as string constants. Tests
verify the controller passes those exact strings to the AnimationPlayer stub.
When real GLB clips land, no code changes are needed — only integration
validation.

**Confidence:** High
