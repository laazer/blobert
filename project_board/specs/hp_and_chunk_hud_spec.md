# HP & Chunk HUD — Specification

## Requirement HUD-1 — Data source and update cadence

### 1. Spec Summary
- **Description:** The HP and chunk HUD in both `test_movement.tscn` and `test_infection_loop.tscn` reads from the authoritative player simulation state (`current_hp`, `max_hp`, `has_chunk`) via `PlayerController` accessors and updates every frame while the player exists in the scene.
- **Constraints:** No changes to movement or HP simulation code (`movement_simulation.gd`); HUD may only read from existing accessors on `PlayerController`. HUD logic must live in UI scripts / scenes (e.g., a `CanvasLayer` with `infection_ui.gd` or equivalent) and must not introduce new singletons or simulation-layer state.
- **Assumptions:** A single player instance exists in each scene and is placed in the `"player"` group so the HUD can resolve it via `get_first_node_in_group("player")`. The existing `PlayerController` methods `get_current_hp()`, `has_chunk()`, and `is_wall_clinging_state()` remain the only APIs used to query state.
- **Scope:** Applies to `scenes/test_movement.tscn` and `scenes/test_infection_loop.tscn` only; other scenes may remain without this HUD until explicitly ticketed.

### 2. Acceptance Criteria
- **AC-HUD-1.1:** In both scenes, a HUD `CanvasLayer` exists in the root of the scene tree and successfully resolves a `PlayerController` instance each time `_process()` runs, as long as the player node exists.
- **AC-HUD-1.2:** The HUD reads `current_hp` exclusively via `PlayerController.get_current_hp()` and never touches `_current_state` or simulation objects directly.
- **AC-HUD-1.3:** The HUD reads chunk state exclusively via `PlayerController.has_chunk()` and does not infer chunk state from the presence/absence of chunk nodes or other side channels.
- **AC-HUD-1.4:** The HUD runs its update logic every rendered frame (e.g., Godot `_process`) while the scene is active; tests can observe HP and chunk text/bar values changing within one frame after the underlying simulation values change.
- **AC-HUD-1.5:** No HUD code writes back to simulation or controller state; there are zero assignments to `_current_state`, `_simulation`, or new public setters on `PlayerController` from HUD scripts.

### 3. Risk & Ambiguity Analysis
- **Risk:** Multiple players in future scenes could make `get_first_node_in_group("player")` ambiguous.  
  **Impact:** HUD might attach to an unintended player instance. For this ticket, both target scenes have exactly one player, so risk is acceptable.
- **Risk:** If `Player` is removed from the `"player"` group in one scene, HUD will fail silently.  
  **Impact:** HP/chunk HUD would stop updating; tests should catch this via AC-HUD-1.1.
- **Ambiguity:** Whether HUD should survive player deletion or scene transitions.  
  **Resolution:** Out of scope; HUD only needs to function for the lifetime of the player node in these prototype scenes.

### 4. Clarifying Questions
- **CQ-HUD-1.A:** Should the HUD support scenes with multiple players (e.g., split-screen) or only the single-player prototype?  
  **Assumption:** Single-player only for this ticket; multi-player is future scope.
- **CQ-HUD-1.B:** Should the HUD ever pause updates (e.g., during pause menus)?  
  **Assumption:** HUD updates continuously whenever the scene tree is active; pause/menus are out of scope.

---

## Requirement HUD-2 — HP bar widget behavior

### 1. Spec Summary
- **Description:** A non-debug HP bar is present and visible in both `test_movement.tscn` and `test_infection_loop.tscn`, driven continuously from the player’s `current_hp` and `max_hp`. It is implemented as a proper UI widget (not debug text) with clear fill proportion.
- **Constraints:** The HP bar must be part of a HUD `CanvasLayer` (screen-space UI) and must not be drawn using debug shapes or world-space polygons. Implementation uses a single `TextureProgressBar` (or semantically equivalent progress bar node) named `HPBar`.
- **Assumptions:** `max_hp` is the upper bound used for the bar’s `max_value`. `current_hp` is always within a reasonable numeric range for visualizing as a progress bar; if it temporarily falls outside \[0, max_hp\], the bar is clamped as specified below.
- **Scope:** Applies to both prototype scenes; the same bar behavior and appearance is reused, not re-implemented differently per scene.

### 2. Acceptance Criteria
- **AC-HUD-2.1:** In both scenes, the HUD contains a node named `HPBar` of type `TextureProgressBar` (or subclass of `Range` configured as a horizontal progress bar) within the UI `CanvasLayer`.
- **AC-HUD-2.2:** `HPBar.min_value` is set to `0.0`, and `HPBar.max_value` is set to the player’s `max_hp` value as exposed from simulation (either by copying once on ready or reading on each update); `max_value` is strictly positive.
- **AC-HUD-2.3:** On each frame, `HPBar.value` is updated from `current_hp`, with its on-screen fill proportion equal to `clamp(current_hp, 0.0, max_hp) / max_hp`.
- **AC-HUD-2.4:** When the player’s `current_hp` is at full health (equal to `max_hp`), the bar appears fully filled; when at zero, the bar appears empty; intermediate values appear proportionally filled.
- **AC-HUD-2.5:** In both scenes, triggering a detach event that reduces HP causes the bar’s fill amount to visually decrease within one frame; triggering a recall that restores HP causes the bar to increase correspondingly within one frame.
- **AC-HUD-2.6:** The HP bar is rendered using a non-debug theme (standard Godot progress bar skin or a simple custom style); no debug overlays or built-in physics debug drawing are used.

### 3. Risk & Ambiguity Analysis
- **Risk:** If `max_hp` is ever configured to zero or a negative value, division-by-zero or inverted bar behavior could occur.  
  **Mitigation:** Tests should configure a strictly positive `max_hp` for this ticket; handling pathological `max_hp` values is out of scope but can be guarded against defensively in implementation.
- **Ambiguity:** Exact art/style of the bar (colors, textures) is not crisply defined.  
  **Mitigation:** For this ticket, tests assert only structure, numeric wiring, and relative fill, not specific textures.

### 4. Clarifying Questions
- **CQ-HUD-2.A:** Should the bar ever exceed full fill (e.g., overheal) or visually cap at full?  
  **Assumption:** The bar clamps visually at full; values above `max_hp` render as full bar.
- **CQ-HUD-2.B:** Should there be any animation (lerp) between values or instantaneous jumps?  
  **Assumption:** Instant updates are acceptable for this prototype; no interpolation is required.

---

## Requirement HUD-3 — Numeric HP display

### 1. Spec Summary
- **Description:** A numeric HP value is displayed alongside the HP bar in both target scenes, showing the player’s current HP and maximum HP in a compact, readable format.
- **Constraints:** Numeric HP must be text-based (e.g., `Label`) placed near the HP bar. It must be driven from the same `current_hp` and `max_hp` values as the bar and updated every frame. Floats are rendered as rounded integers for readability.
- **Assumptions:** HP is non-negative in normal gameplay; rounding with `round()` is an acceptable lossy representation of the float value.
- **Scope:** Applies only to HP (not to other stats); appears in both `test_movement.tscn` and `test_infection_loop.tscn`.

### 2. Acceptance Criteria
- **AC-HUD-3.1:** In both scenes, the HUD contains a `Label` node named `HPLabel` logically grouped with `HPBar` (e.g., as siblings or parent/child) within the HUD `CanvasLayer`.
- **AC-HUD-3.2:** On each frame, `HPLabel.text` is updated to the format `HP: <current> / <max>`, where `<current>` is the rounded integer form of `current_hp` and `<max>` is the rounded integer form of `max_hp`.
- **AC-HUD-3.3:** When HP changes due to detach, the numeric `<current>` value decreases to match the new HP within one frame, and when HP increases due to recall, `<current>` increases accordingly.
- **AC-HUD-3.4:** While HP remains constant across frames, both the bar and the numeric label remain stable (no flicker or oscillation in text).
- **AC-HUD-3.5:** If `current_hp` falls below `0.0` or above `max_hp` due to future tickets, the numeric label still displays the raw rounded value; this ticket does not impose additional clamping on text.

### 3. Risk & Ambiguity Analysis
- **Risk:** Rounding may occasionally show HP as unchanged when very small float differences occur (e.g., 99.4 vs 99.6).  
  **Mitigation:** For this prototype, HP changes are expected to be in coarse discrete steps; tiny deltas are unlikely and acceptable.
- **Ambiguity:** Whether to localize or format with thousands separators is unspecified.  
  **Mitigation:** For this ticket, plain integer formatting via `str(round(value))` is sufficient.

### 4. Clarifying Questions
- **CQ-HUD-3.A:** Should the numeric HP ever be hidden (e.g., diegetic-only bar)?  
  **Assumption:** Numeric HP is always visible in these prototype scenes when the HUD is visible.

---

## Requirement HUD-4 — Chunk state indicator

### 1. Spec Summary
- **Description:** A chunk state indicator is visible in both target scenes, clearly showing whether the player’s chunk is attached or detached, driven exclusively by `has_chunk`.
- **Constraints:** The indicator is implemented as a simple text label (no iconography is required), using exact, consistent wording tied to boolean chunk state. It must be part of the HUD `CanvasLayer` and updated every frame.
- **Assumptions:** `PlayerController.has_chunk()` is the single source of truth for chunk state; there is no partial or transitioning state for this ticket.
- **Scope:** Applies to `test_movement.tscn` and `test_infection_loop.tscn`; other scenes may omit this indicator.

### 2. Acceptance Criteria
- **AC-HUD-4.1:** The HUD contains a `Label` node named `ChunkStatusLabel` in both target scenes.
- **AC-HUD-4.2:** On each frame, `ChunkStatusLabel.text` is updated based solely on `PlayerController.has_chunk()`:  
  - `"Chunk: Attached"` when `has_chunk()` returns `true`.  
  - `"Chunk: Detached"` when `has_chunk()` returns `false`.
- **AC-HUD-4.3:** Pressing the detach input when detach is eligible causes `ChunkStatusLabel.text` to change from `"Chunk: Attached"` to `"Chunk: Detached"` within one frame in both scenes.
- **AC-HUD-4.4:** Completing a successful recall that reattaches the chunk causes the label to change back to `"Chunk: Attached"` within one frame in both scenes.
- **AC-HUD-4.5:** While chunk state remains constant, `ChunkStatusLabel.text` remains stable (no transient alternate text values).

### 3. Risk & Ambiguity Analysis
- **Risk:** If future tickets introduce intermediate chunk states (e.g., “in-flight” during recall), a binary attached/detached label may become misleading.  
  **Mitigation:** For this ticket, tests assume binary state only; nuanced visualizations are future scope.
- **Ambiguity:** Whether color-coding (e.g., green for attached, red for detached) is required.  
  **Mitigation:** Color differences are optional for this ticket; tests focus on text content.

### 4. Clarifying Questions
- **CQ-HUD-4.A:** Should the chunk indicator ever be hidden (e.g., when no chunk mechanic is available)?  
  **Assumption:** In these prototype scenes, chunk mechanics are always relevant; the label remains visible at all times.

---

## Requirement HUD-5 — Layout, readability, and scene coverage

### 1. Spec Summary
- **Description:** The HP bar, numeric HP, and chunk indicator form a compact HUD cluster that remains readable at the project’s default resolution and camera framing, and does not overlap the primary play space where the player and floor reside.
- **Constraints:** HUD elements must be anchored to the viewport (screen space) rather than world space and placed away from the center of the screen. Their positions must be consistent between `test_movement.tscn` and `test_infection_loop.tscn` to the extent possible.
- **Assumptions:** The project uses a fixed default resolution and the existing camera setup from the prototype scenes; future resolution scaling is out of scope.
- **Scope:** Applies to both specified scenes; does not constrain UI layout in future menus or levels.

### 2. Acceptance Criteria
- **AC-HUD-5.1:** In both scenes, the HUD `CanvasLayer` is configured to render in screen space (standard Godot `CanvasLayer` behavior) and is not parented under the `Player` node or other moving world-space nodes.
- **AC-HUD-5.2:** `HPBar`, `HPLabel`, and `ChunkStatusLabel` are positioned in the top-left quadrant of the viewport with at least 16px padding from the top and left edges.
- **AC-HUD-5.3:** At the project’s default window size and camera zoom, no part of `HPBar`, `HPLabel`, or `ChunkStatusLabel` appears within the central 50% of the viewport width or the central 60% of the viewport height.
- **AC-HUD-5.4:** Text in `HPLabel` and `ChunkStatusLabel` uses a readable font size (e.g., default Godot label font size) such that characters are clearly legible from a normal viewing distance during human playtests.
- **AC-HUD-5.5:** The HUD cluster appears in both `test_movement.tscn` and `test_infection_loop.tscn` with the same relative ordering: bar on top, numeric HP label adjacent or directly beneath it, and chunk label beneath or beside the HP label.

### 3. Risk & Ambiguity Analysis
- **Risk:** Different monitors and resolutions may slightly change perceived overlap with play space.  
  **Mitigation:** Tests rely on viewport-relative percentage criteria (central 50%/60%) rather than pixel-perfect assumptions.
- **Ambiguity:** Exact font size and margin values are not numerically specified.  
  **Mitigation:** For this ticket, “readable” is enforced via human playtesting and visual inspection rather than automated pixel checks; automated tests can still assert node presence and approximate positions.

### 4. Clarifying Questions
- **CQ-HUD-5.A:** Should the HUD support multiple UI scaling factors (accessibility)?  
  **Assumption:** Single scale targeting default resolution is sufficient for this milestone.

---

## Requirement HUD-6 — Non-functional constraints

### 1. Spec Summary
- **Description:** The HUD implementation must be simple, maintainable, and performant, adding negligible overhead to the prototype scenes and introducing no coupling from UI back into simulation.
- **Constraints:** HUD scripts must be short, focused on presentation, and avoid complex logic or heavy per-frame allocations. No new global singletons (autoloads) may be introduced for this HUD.
- **Assumptions:** Per-frame updates for a small number of labels and a single progress bar are effectively free in the context of these prototype scenes.
- **Scope:** Applies to any scripts and scene changes introduced to satisfy Requirements HUD-1 through HUD-5.

### 2. Acceptance Criteria
- **AC-HUD-6.1:** HUD scripts do not allocate new nodes inside `_process()` or per-frame; all required nodes are created and wired in the scene or `_ready()`, and `_process()` only reads state and updates properties.
- **AC-HUD-6.2:** No new autoloads or global singletons are added; HUD is instantiated as a regular scene node.
- **AC-HUD-6.3:** There are no circular dependencies between HUD scripts and simulation or controller scripts (e.g., HUD does not require `movement_simulation.gd` directly).
- **AC-HUD-6.4:** Running the game in headless mode with the HUD scenes loaded introduces no new errors or warnings related to missing nodes or invalid type casts from the HUD code.
- **AC-HUD-6.5:** All new or modified HUD scripts pass Godot’s `--headless --check-only` validation without errors.

### 3. Risk & Ambiguity Analysis
- **Risk:** Future expansion of HUD (e.g., adding more labels or animations) could increase per-frame cost.  
  **Mitigation:** This ticket keeps the HUD minimal (one bar + two labels); future complexity should be gate-kept by additional tickets.
- **Ambiguity:** Whether to log or gracefully handle missing player references.  
  **Mitigation:** For this ticket, HUD scripts may early-return from `_process()` when the player reference is `null` without logging; stability is prioritized over verbose error reporting.

### 4. Clarifying Questions
- **CQ-HUD-6.A:** Should HUD scripts emit metrics or logs for analytics?  
  **Assumption:** No metrics/logging are required for this prototype; silence is acceptable when functioning correctly.

---

