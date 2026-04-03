# M7-ACS TestBreak Checkpoints — run-2026-04-01-testbreak

---

### [M7-ACS] TestBreak — empty string from get_state()

**Would have asked:** Should the controller treat `get_state()` returning `""` (empty string) as an unknown/fallback state (play "Idle", speed 1.0) or is an empty state string a programming error that should produce a distinct behavior? The primary suite never tests `""` as a state value.

**Assumption made:** Empty string is not a canonical state. The resolution table's final row covers "any other state string (future/unknown)" which includes `""`. The controller must not crash; it falls through to the `"Idle"` fallback at speed 1.0. This is the conservative interpretation consistent with AC-4.8.

**Confidence:** High

---

### [M7-ACS] TestBreak — blend_time mutated after _ready()

**Would have asked:** The spec says `blend_time` is an `@export` variable read at transition time. An implementation that caches `blend_time` into a local copy in `_ready()` would not reflect post-ready changes. Should changes to `blend_time` after `_ready()` take effect on the next transition?

**Assumption made:** Yes. `blend_time` is an export with no caching semantics described in the spec. `_physics_process` must read the live `blend_time` value each time it calls `play()`. A test that changes `blend_time` from 0.15 to 0.0 after `_ready()` and then triggers a new transition must see 0.0 passed to `play()`.

**Confidence:** High

---

### [M7-ACS] TestBreak — negative blend_time passed to play()

**Would have asked:** If `blend_time` is set to a negative value (e.g., `-1.0`), should the controller pass that negative value to `animation_player.play()` verbatim, or should it clamp to 0.0? In Godot 4, passing `-1.0` as blend_time to AnimationPlayer.play() uses the default blend from the AnimationPlayer settings. The spec says "the blend_time export value is used" — does that mean verbatim pass-through?

**Assumption made:** Verbatim pass-through. The spec does not define clamping behavior for negative blend_time. The controller passes whatever `blend_time` contains to `play()`. This is a potential gotcha for the implementation agent: if they clamp internally, this test catches the divergence. If they pass through, the test documents the behavior.

**Confidence:** Medium

---

### [M7-ACS] TestBreak — trigger_hit_animation() before first tick

**Would have asked:** The primary suite always calls one `_tick()` before `trigger_hit_animation()` to establish `_current_clip`. If `trigger_hit_animation()` is called immediately after `_ready()` with no prior tick, `_current_clip` is `""` and `_prior_clip` will be set to `""`. Is this safe? Will the controller crash, or will it handle the uninitialized `_current_clip` gracefully?

**Assumption made:** No crash. The hit path unconditionally calls `animation_player.play("Hit", 0.0)` regardless of `_current_clip`. `_prior_clip` being `""` is valid state. On Hit completion, the controller re-evaluates live state (AC-6.6), so `_prior_clip = ""` is never used for resume. The test confirms no crash and that Hit is played correctly.

**Confidence:** High

---

### [M7-ACS] TestBreak — _physics_process called before _ready()

**Would have asked:** The spec defines `_ready_ok: bool = false` as the default. If `_physics_process` runs before `_ready()` (the direct-call test pattern makes this possible), the controller must be dormant because `_ready_ok` defaults to false. This is an invariant of the flag-based approach.

**Assumption made:** The default value of `_ready_ok` is `false` per spec AC-3.5. `_physics_process` called before `_ready()` must be a no-op. The test confirms zero `play()` calls when `_ready()` has never been called.

**Confidence:** High

---

### [M7-ACS] TestBreak — death latch does not suppress speed_scale changes

**Would have asked:** After `_death_latched = true`, the spec (AC-7.3) says no `play()`, `stop()`, or `speed_scale` call is made. An implementation that checks the latch for `play()` calls but forgets to guard `speed_scale` mutations (e.g., in a subsequent tick that resolves "weakened" before checking the latch) would pass the `play_call_count` assertion but silently mutate `speed_scale`. Should the adversarial suite explicitly verify `speed_scale` is not changed after latching?

**Assumption made:** Yes. AC-7.3 explicitly includes `speed_scale`. After death latch, a tick that would otherwise resolve "weakened" must not set `speed_scale = 0.5`. The test transitions through weakened→dead, latches, then verifies `speed_scale` remains 1.0 on subsequent ticks.

**Confidence:** High

---

### [M7-ACS] TestBreak — current_animation == "" triggers premature hit exit

**Would have asked:** The spec (ACS-6) says hit completion is detected when `is_playing() == false OR current_animation != "Hit"`. If the stub's `current_animation` starts as `""` (before any play call), then after `trigger_hit_animation()` correctly sets `current_animation = "Hit"`, does the completion check use `current_animation` reliably? Conversely, what if an implementation reads `current_animation` before the stub updates it and gets `""`? This tests that the controller's completion check is not fooled by empty animation name.

**Assumption made:** The implementation must read `current_animation` from the stub, which sets it to `"Hit"` on `play("Hit", 0.0)`. The test probes the specific scenario where stub `current_animation` is manually reset to `""` while `_is_playing` remains true — simulating an AnimationPlayer that has had its `current_animation` cleared externally. This should be treated as "Hit is no longer playing" and exit the hit state.

**Confidence:** Medium

---

### [M7-ACS] TestBreak — velocity exactly at move_threshold

**Would have asked:** The resolution table says `velocity.length() >= move_threshold` → Walk. Is the boundary condition (exactly equal) intended to be Walk (>=) or Idle (<)? The primary suite does not test the exact threshold value.

**Assumption made:** Strictly follows the spec: `>= move_threshold` → Walk. `velocity.length() == move_threshold` must resolve to Walk, not Idle. The test uses `Vector3(0.1, 0.0, 0.0)` with default `move_threshold = 0.1` (length == 0.1 == threshold).

**Confidence:** High

---

### [M7-ACS] TestBreak — weakened-to-active speed_scale restoration

**Would have asked:** When transitioning from `weakened` (which sets `speed_scale = 0.5`) to `active` with non-zero velocity (which should set `speed_scale = 1.0`), does the controller correctly restore `speed_scale`? Primary suite only tests initial state from default `speed_scale = 1.0`; it never tests a state that previously had a different speed.

**Assumption made:** The controller sets `speed_scale` on every transition where the resolved (clip, speed) tuple changes. Weakened→active means the tuple changes from ("Idle", 0.5) to ("Walk" or "Idle", 1.0). The controller must call `play()` and set `speed_scale = 1.0`. The test confirms `speed_scale` is 1.0 after the transition.

**Confidence:** High

---

### [M7-ACS] TestBreak — both exports null simultaneously

**Would have asked:** The spec edge case (ACS-3 section 3) says "Both exports null simultaneously — both warnings must fire, not just the first." The primary suite tests each null independently. Does the implementation short-circuit on the first null (only one `push_warning` call) or check both independently?

**Assumption made:** Both must fire. The test verifies `_ready_ok = false` regardless — the observable side effect of interest — since intercepting `push_warning()` calls in GDScript headless tests is impractical. The test does confirm both-null produces `_ready_ok = false` and that subsequent `_physics_process` calls don't crash with either reference.

**Confidence:** High

---

### [M7-ACS] TestBreak — multiple controller instances are isolated

**Would have asked:** If two EnemyAnimationController instances exist simultaneously (two enemies in one scene), do they share any static/class-level state? An implementation using a `static var` for any internal flag would cause cross-instance contamination.

**Assumption made:** No shared state. Two controllers driven independently — one to death, one remaining in idle — must not affect each other's `_death_latched` or `_hit_active` flags. This matches the isolation pattern from ESM TB-006.

**Confidence:** High

---

### [M7-ACS] TestBreak — trigger_hit_animation() when _ready_ok == false

**Would have asked:** The primary suite tests that `trigger_hit_animation()` is suppressed by `_death_latched`. But what about `_ready_ok == false`? If the null guard fires and the controller is dormant, should `trigger_hit_animation()` also be a no-op? The spec's AC-3.3 says `_physics_process` makes zero calls on `animation_player` after null guard, but it says nothing about `trigger_hit_animation()` in this case.

**Assumption made:** Conservative: `trigger_hit_animation()` must guard `_ready_ok` before acting. Calling `trigger_hit_animation()` when `animation_player` is null would crash. The method must check `_ready_ok` (or null-check `animation_player`) before calling `animation_player.play()`. The test confirms zero `play()` calls and no crash when `trigger_hit_animation()` is called with `_ready_ok = false`.

**Confidence:** Medium

---

### [M7-ACS] TestBreak — dead state detected during hit active window (pre-clip-end)

**Would have asked:** EAC-16 tests that after Hit COMPLETES (clip ends), if state is dead, Death plays. But what about the tick DURING which the enemy dies while `_hit_active` is true and `is_playing()` is still true? The controller should suppress state resolution (AC-6.4), so Death should NOT be triggered mid-hit. The test confirms Death is not triggered until the Hit clip finishes.

**Assumption made:** While `_hit_active` is true and `is_playing()` is true, even if state becomes "dead", the controller must not call `play("Death", ...)`. Death must wait until Hit completes. This is the correct priority order per AC-6.4.

**Confidence:** High

---

### [M7-ACS] TestBreak — wrong casing state string (case sensitivity)

**Would have asked:** The spec says "casing is significant" for clip name strings. Does this also apply to state strings from `get_state()`? If `get_state()` returns `"IDLE"` or `"Active"`, these are not canonical states. Should they fall through to the unknown/fallback branch (play "Idle", speed 1.0)?

**Assumption made:** Yes. The resolution table uses exact lowercase string matching. `"IDLE"` does not match `"idle"`. It falls through to the unknown-state fallback. The test confirms `"ACTIVE"` (all caps) resolves to `"Idle"`, speed 1.0, not `"Walk"` even with non-zero velocity.

**Confidence:** High

---

### [M7-ACS] TestBreak — large velocity value (stress/boundary)

**Would have asked:** Is there any numerical instability or branch logic that could break at very large velocity magnitudes? The `velocity.length()` computation involves a square root. For velocity `Vector3(1000.0, 1000.0, 1000.0)`, the length is ~1732. This should trivially exceed any reasonable `move_threshold`.

**Assumption made:** No crash; resolves to Walk. The test confirms the controller handles extreme velocity without error, guarding against any hypothetical integer overflow or unexpected branch behavior at large magnitudes.

**Confidence:** High

