Basic UI feedback (infection loop) — Specification
=================================================

Ticket: `project_board/2_milestone_2_infection_loop/backlog/basic_ui_feedback_infection.md`  
Milestone: 2 — Infection Loop  
Scope: Presentation/UI layer only (no changes to infection simulation or controller logic)


### Requirement INF-UI-1 — Infection UI container and scene integration

#### 1. Spec Summary
- **Description:**  
  - The infection loop has a dedicated HUD container that owns all infection-related UI elements for this ticket.  
  - This container is present and active whenever the infection loop is playable in-editor.
- **Constraints:**  
  - Infection UI must not be parented under moving physics bodies (e.g. `Player`, `Floor`, `Chunk`) to avoid camera-relative jitter and overlap with world geometry.  
  - Infection UI must be discoverable by tests and other agents via a **stable node name and type**.  
  - Infection UI must respect the Milestone 1 “human-playable” conventions for readability and non-blocking layout (reused from `human_playable_core_prototype`).
- **Assumptions:**  
  - The infection loop is exercised in at least one playable scene that can be instantiated headlessly for tests (similar to `test_movement.tscn`).  
  - Human-playable core helpers (e.g. central play area computation) continue to exist and may be reused by Test Designer agents.  
  - A dedicated infection HUD container is preferable to overloading the existing control-hints UI.
- **Scope:**  
  - Defines the structural contract for infection UI nodes (container, anchoring, and parenting).  
  - Does **not** define art style, colors, or fonts beyond legibility constraints.

#### 2. Acceptance Criteria
- **INF-UI-1.A — Dedicated infection HUD container exists:**  
  - In every playable scene used to exercise the infection loop for Milestone 2, the scene root has a child `CanvasLayer` named exactly `InfectionUI`.  
  - `InfectionUI` is part of the active scene tree while the player can interact with infection mechanics.
- **INF-UI-1.B — Container hierarchy and parenting:**  
  - `InfectionUI` is a direct or near-direct child of the scene root (it may be nested under another non-moving UI/root node, but **not** under any physics body such as `CharacterBody2D`, `StaticBody2D`, or `RigidBody2D`).  
  - All infection-loop UI elements defined in this spec (at minimum, the absorb prompt) are parented somewhere under `InfectionUI`.
- **INF-UI-1.C — Non-overlap with dynamic world nodes:**  
  - No infection UI node (including the absorb prompt) has a dynamic-world ancestor (e.g. `Player`, `Floor`, `Chunk`, or their physics-body descendants), matching the pattern enforced for move/jump/detach hints in `test_human_playable_core_adversarial.gd`.  
  - Tests can check this using a helper analogous to `_has_dynamic_world_ancestor`.
- **INF-UI-1.D — Central play area non-overlap baseline reused:**  
  - Long-lived infection UI (anything visible for more than 0.5 seconds at a time) is placed fully **outside** the “central play area” bounding box used by existing human-playable tests (i.e. the same rectangle used for move/jump/detach hint placement).  
  - Short-lived prompts may appear closer to screen edges but must still not overlap the central play area.

#### 3. Risk & Ambiguity Analysis
- **Risks:**  
  - If the scene structure changes (e.g. new root node or different naming), tests that assume `InfectionUI` under the root may break.  
  - Over-constraining hierarchy could conflict with future HUD work if a more complex UI system is introduced.
- **Edge cases:**  
  - Scenes that do not expose infection mechanics (e.g. menus, non-infection levels) are not required to have `InfectionUI`.  
  - If multiple infection-playable scenes exist, each must satisfy INF-UI-1.A–D independently.
- **Unclear aspects / conflicts:**  
  - Exact scene names and counts for infection content are not defined in this ticket; this spec intentionally stays scene-agnostic and focuses on node structure.

#### 4. Clarifying Questions
1. Which specific scene(s) should be treated as the canonical infection-loop testbed for UI verification (e.g. a dedicated `test_infection_loop.tscn` vs. augmenting the existing `test_movement.tscn`)?  
2. Should `InfectionUI` also own other non-infection HUD elements (health, generic prompts), or should those remain in a separate HUD container?


### Requirement INF-UI-2 — Absorb prompt text, visibility, and layout

#### 1. Spec Summary
- **Description:**  
  - The player sees a clear, readable on-screen prompt when an infection-related **absorb** (or equivalent interaction) is available, and no such prompt when it is not.  
  - This absorb prompt is the **only mandatory infection UI element** for this ticket.
- **Constraints:**  
  - Prompt must be implemented as a `Label` (or subclass of `Label`) named `AbsorbPromptLabel` under `InfectionUI`.  
  - Prompt text must explicitly contain the word “absorb” (case-insensitive) so that tests can identify it by content.  
  - Prompt must not overlap the central play area and must remain readable at the project’s default window size.
- **Assumptions:**  
  - Infection / interaction logic exposes a single boolean concept “absorb available to the player right now” that this UI can observe or be signaled with.  
  - The absorb action is bound to the existing `detach` input (E key) or another clearly-documented action; this spec does not introduce new input actions.
- **Scope:**  
  - Defines the presence, naming, visual constraints, and high-level behavior of the absorb prompt.  
  - Does **not** define the underlying infection mechanics or exact conditions under which absorb becomes available; it only consumes the “absorb available” boolean.

#### 2. Acceptance Criteria
- **INF-UI-2.A — Node presence and naming:**  
  - Under `InfectionUI`, there exists a node `AbsorbPromptLabel` whose runtime type is `Label` (or a subclass of `Label`).  
  - Tests can obtain it via `InfectionUI.get_node("AbsorbPromptLabel") as Label` without null.
- **INF-UI-2.B — Text content contract:**  
  - `AbsorbPromptLabel.text` contains the substring `"absorb"` ignoring case (e.g. `"Press E to Absorb"`).  
  - The text may also include the relevant input binding (e.g. `"E"` or localized equivalent), but this is optional.
- **INF-UI-2.C — Readability and legibility:**  
  - At runtime with default project resolution:  
    - `AbsorbPromptLabel`’s `CanvasItem.modulate.a` is **strictly greater than 0.0** whenever the prompt is visible (not fully transparent).  
    - `AbsorbPromptLabel.scale.x` and `.scale.y` have absolute values **≥ 0.5** (reusing the “not tiny” threshold from `test_ui_hints_not_fully_transparent_and_not_tiny`).  
    - Font size and style may vary, but text must be fully visible and not clipped within its control bounds.
- **INF-UI-2.D — Layout and non-blocking behavior:**  
  - When visible, the prompt’s screen-space bounding box lies entirely outside the central play area rectangle used for core UI hints (same definition as human-playable core tests) and within a reasonable distance of the viewport center (e.g. center-to-center distance ≤ 2000px).  
  - The prompt never covers the player character or primary infection targets while the camera framing matches the canonical test scene setup.
- **INF-UI-2.E — Default-state visibility:**  
  - Immediately after the infection-loop scene loads and before any infection interaction is available, `AbsorbPromptLabel.visible` is `false` (or equivalent: it does not render or affect layout).

#### 3. Risk & Ambiguity Analysis
- **Risks:**  
  - Overly strict layout constraints could conflict with localized text (longer strings may require more space).  
  - If absorb is bound to a non-keyboard input (e.g. controller button), hard-coding key glyphs in the text may become inaccurate.
- **Edge cases:**  
  - Rapid toggling of absorb availability (e.g. leaving and re-entering an infection radius every frame) must not cause flickering that breaks readability; see INF-UI-3.  
  - If the infection loop allows absorb in multiple contexts (enemy, environment, projectiles), the same prompt may be reused, but this spec only requires that **some** absorb-available state is surfaced.
- **Unclear aspects / conflicts:**  
  - Whether to include explicit key names (e.g. “E”) or generic action names (e.g. “Absorb”) is not fixed here; the only hard requirement is that `"absorb"` appears in the text.

#### 4. Clarifying Questions
1. Should the absorb prompt explicitly include the current physical key or gamepad button binding (e.g. `"Press E to Absorb"` vs. `"Press [Absorb] to interact"`), and if so, should this be read dynamically from the InputMap?  
2. Is the absorb prompt expected to be localized in later milestones, requiring any specific structure (e.g. key glyph placeholder tokens) to support translation?


### Requirement INF-UI-3 — Absorb prompt behavior over time

#### 1. Spec Summary
- **Description:**  
  - The absorb prompt appears only while an absorb action is actually available and disappears promptly when it is not, with predictable timing and without animation glitches.  
  - Behavior is defined solely in terms of a single boolean **absorb-available** concept supplied by the infection/interaction layer.
- **Constraints:**  
  - UI may lag the underlying absorb-available boolean by at most one physics frame (e.g. one `_process`/`_physics_process` tick).  
  - The prompt’s visibility behavior must be deterministic for a given sequence of absorb-available values.  
  - The UI layer may not change or infer infection mechanics; it only reflects the boolean state it is given.
- **Assumptions:**  
  - Infection or interaction code exposes a stable, repeatable way for UI to observe when absorb is available (property, signal, or controller callback).  
  - Frame rate is within a normal range (e.g. ~60 FPS); this spec does not attempt to define per-millisecond timing beyond “frame-level” granularity.
- **Scope:**  
  - Defines the mapping from absorb-available boolean to `AbsorbPromptLabel.visible` and related properties.  
  - Does **not** specify who owns the boolean or how it is computed.

#### 2. Acceptance Criteria
- **INF-UI-3.A — Visibility follows absorb-available boolean:**  
  - For any frame where absorb-available is `true`, the absorb prompt is visible on that frame or the immediately following frame.  
  - For any frame where absorb-available is `false`, the prompt is hidden on that frame or the immediately following frame.  
  - Tests can model this as: `visible(t) ∈ {available(t), available(t-1)}` where `visible(t)` is the prompt’s visibility for frame `t`.
- **INF-UI-3.B — No “always-on” or “always-off” behavior:**  
  - It is possible (via test harness or gameplay sequence) to reach a state where absorb-available is `true` and the prompt is visible, and another state where absorb-available is `false` and the prompt is hidden.  
  - There is no configuration in which, during normal infection-loop gameplay, the absorb prompt remains permanently visible regardless of availability.
- **INF-UI-3.C — No flickering under stable input:**  
  - When absorb-available stays `true` for N ≥ 5 consecutive frames, the prompt must remain visible for all of those frames (no on/off flicker).  
  - When absorb-available stays `false` for N ≥ 5 consecutive frames, the prompt must remain hidden for all of those frames.
- **INF-UI-3.D — Re-entrancy behavior:**  
  - If absorb-available toggles `false → true → false` within a short window (e.g. a few frames as the player moves in and out of range), the prompt mirrors that toggle without accumulating stale state (i.e. it does not remain visible accidentally after availability returns to `false`).  
  - Multiple toggles in one session are handled consistently and deterministically.

#### 3. Risk & Ambiguity Analysis
- **Risks:**  
  - If the infection controller emits absorb-available changes on a different tick than the UI listens on, edge cases at transition boundaries could cause off-by-one-frame inconsistencies.  
  - Overly strict timing requirements could make tests brittle across different delta values or platforms.
- **Edge cases:**  
  - Very short pulses of availability (e.g. one-frame windows) may cause the prompt to appear only for a single frame; while this is technically compliant, it may not be human-readable. For Milestone 2, this is accepted as long as longer-availability windows look good.  
  - Paused or slow-motion gameplay may stretch frame intervals but still obey frame-based rules.
- **Unclear aspects / conflicts:**  
  - Whether the prompt should fade/animate in/out is left unspecified; animations are permitted as long as `visible` semantics above hold and alpha/scale constraints remain satisfied.

#### 4. Clarifying Questions
1. Should the absorb prompt enforce a minimum “on-screen duration” (e.g. stay visible for at least 0.25s once shown) to guarantee human readability, even if absorb-available drops to `false` earlier?  
2. Should the infection controller be required to expose absorb-available as a property polled each frame, or is a signal/event-based API acceptable as long as the functional behavior is equivalent?


### Requirement INF-UI-4 — Non-functional constraints (performance, decoupling, and safety)

#### 1. Spec Summary
- **Description:**  
  - Infection UI must be cheap to update, decoupled from the infection simulation, and safe to run in headless automated tests.  
  - UI code must not introduce new game-logic side effects; it is purely presentational.
- **Constraints:**  
  - Infection UI must not allocate significant per-frame resources (no frequent scene instantiation, texture loads, or uncontrolled string allocations).  
  - Infection UI may read, but must not mutate, core infection/simulation state.  
  - Infection UI must function correctly in headless runs where scenes are instantiated directly by test code.
- **Assumptions:**  
  - Existing tests and controllers already enforce separation between simulation (`movement_simulation.gd`, infection logic) and engine integration.  
  - Additional UI nodes have negligible impact on frame time at the scales used in this prototype.
- **Scope:**  
  - Applies to all code and scenes introduced or modified to satisfy INF-UI-1 through INF-UI-3.

#### 2. Acceptance Criteria
- **INF-UI-4.A — Read-only dependency on infection state:**  
  - Infection UI scripts (nodes under `InfectionUI`) never write to core infection or movement state objects (e.g. no direct mutation of simulation structs, HP values, or has-chunk / infection flags).  
  - Any interaction with infection systems is via read-only properties, signals, or controller APIs that are designed to be observed by presentation code.
- **INF-UI-4.B — Headless test compatibility:**  
  - Instantiating the infection-loop scene and its `InfectionUI` in a headless test (without a running editor) does not throw errors, assert failures, or rely on editor-only APIs.  
  - Tests can freely create and free scenes with `InfectionUI` without leaks or double-free issues.
- **INF-UI-4.C — Performance baseline:**  
  - The infection UI update cost is O(1) per frame with respect to the number of active infection entities in the scene (i.e. no per-entity dynamic node creation/destruction loops tied directly to frame updates).  
  - Typical operations are limited to property updates (e.g. label text/visibility) and do not materially change frame time compared to a no-infection-UI baseline for the current prototype scenes.
- **INF-UI-4.D — Failure modes:**  
  - If infection systems fail to provide a valid absorb-available signal (e.g. null reference), the infection UI fails **gracefully**: it may hide the absorb prompt or log an error, but must not crash the game or test run.  
  - Misconfiguration of infection UI (e.g. missing `AbsorbPromptLabel`) should be detectable by tests via clear assertion failures rather than silent no-op behavior.

#### 3. Risk & Ambiguity Analysis
- **Risks:**  
  - Future expansion of infection UI (e.g. multiple mutation slots, timers) may require richer data than the single absorb-available boolean; that is intentionally deferred.  
  - If implementers violate read-only assumptions, infection bugs may be harder to diagnose because they originate in the UI layer.
- **Edge cases:**  
  - Extremely low-end hardware or pathological scenes with many UI elements could reveal performance issues; for Milestone 2 prototype scope, this is considered unlikely.  
  - Some platforms may render fonts differently; legibility must still be checked manually via the existing human-playable checklist pattern.
- **Unclear aspects / conflicts:**  
  - Whether logging from infection UI (e.g. `print()` on state changes) is permitted in production builds is not defined here; for tests, minimal logging is acceptable but should not be spammy.

#### 4. Clarifying Questions
1. Should infection UI be explicitly prohibited from performing any file I/O, network requests, or other non-rendering side effects, or is the existing “no non-presentation logic” guidance sufficient?  
2. Are there any platform-specific performance targets (e.g. minimum FPS on a reference machine) that infection UI should be measured against, or is qualitative “no noticeable slowdown” sufficient for Milestone 2?

