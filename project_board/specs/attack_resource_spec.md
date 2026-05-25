# SPEC: AttackResource Data Model

**Ticket:** M11-04 (`project_board/11_milestone_11_base_mutation_attacks/in_progress/04_attack_resource.md`)  
**Spec ID:** ATK  
**Status:** Frozen  
**Revision:** 1  
**Author:** Spec Agent  
**Spec Exit Type:** generic  
**Date:** 2026-05-25

---

## 1. Overview

AttackResource is a Godot `Resource` subclass that serves as the canonical data model for all mutation attacks (base M11 and fused M12). It defines identity, combat parameters, visual feedback, and an extensible modifier system. This is a **data-only** class — no runtime dispatch, no hitbox logic, no scene-tree coupling. Runtime execution is deferred to M11-05 (AttackExecutor).

**File location:** `scripts/attacks/attack_resource.gd`  
**Class name:** `AttackResource`  
**Extends:** `Resource`

---

## 2. Evidence Sources

| Source | Path | Role |
|--------|------|------|
| Ticket | `project_board/11_milestone_11_base_mutation_attacks/in_progress/04_attack_resource.md` | Acceptance criteria |
| Design spec | `project_board/specs/mutation_attack_system_design_spec.md` | Canonical schema draft |
| Adhesion lunge | `scripts/enemy/adhesion_bug_lunge_attack.gd` | Existing parameter patterns (`attack_range`, `cooldown_seconds`, `lunge_speed`) |
| Acid spitter | `scripts/enemy/acid_spitter_ranged_attack.gd` | Existing parameter patterns (`attack_range`, `cooldown_seconds`, `projectile_speed`) |
| Claw crawler | `scripts/enemy/claw_crawler_attack.gd` | Existing parameter patterns (`attack_range`, `cooldown_seconds`, `damage_per_hit`, `knockback_per_hit`) |
| Carapace husk | `scripts/enemy/carapace_husk_attack.gd` | Existing parameter patterns (`attack_range`, `cooldown_seconds`, `charge_speed`, `damage_amount`, `knockback_strength`) |

---

## 3. Discrepancy Resolutions

### ATK-DR-1: `range` → `attack_range`

**Problem:** The ticket and design spec use `range: float`. GDScript has a built-in `range()` function. Naming a property `range` shadows the built-in and prevents calling `range()` in any method body on the class.

**Evidence:** All four existing enemy attack scripts (`adhesion_bug_lunge_attack.gd`, `acid_spitter_ranged_attack.gd`, `claw_crawler_attack.gd`, `carapace_husk_attack.gd`) already use `attack_range: float`.

**Resolution:** Use `attack_range: float` to avoid shadowing, consistent with established codebase convention. The ticket examples that reference `range:` are interpreted as `attack_range:` throughout this spec.

### ATK-DR-2: `knockback_direction` placement

**Problem:** The ticket AC lists `knockback_direction: String` as a top-level export. The design spec places it inside the `modifiers` dictionary as `"knockback_direction": "away"`.

**Resolution:** Keep `knockback_direction` as a **top-level export** per ticket AC. The ticket acceptance criteria are authoritative for this ticket's scope. Having it top-level is correct because knockback direction is a core combat parameter used by every attack that applies knockback, not an optional modifier.

### ATK-DR-3: `description: String` addition

**Problem:** The ticket AC omits `description`. The design spec includes it as `@export var description: String`.

**Resolution:** **Include** `description: String` with default `""`. It is a low-cost addition useful for HUD/UI display of attack names in the player's ability panel. Omitting it would require a breaking schema change later.

### ATK-DR-4: `projectile_lifetime: float` addition

**Problem:** The ticket AC omits `projectile_lifetime`. The design spec includes it with default `2.0`.

**Resolution:** **Include** `projectile_lifetime: float` with default `2.0`. Projectile attacks need a lifetime to auto-despawn; without it, the executor (M11-05) would need a hardcoded fallback. Including it keeps the resource self-describing.

---

## 4. Requirements

### ATK-01: Class Declaration

**Description:** The file `scripts/attacks/attack_resource.gd` declares `class_name AttackResource` extending `Resource`.

**Acceptance Criteria:**
- AC-01a: File exists at `scripts/attacks/attack_resource.gd`.
- AC-01b: First non-comment line contains `class_name AttackResource`.
- AC-01c: Script extends `Resource` (verified via `extends Resource`).
- AC-01d: Instantiation via `AttackResource.new()` succeeds and returns a valid `Resource` instance.
- AC-01e: `is_instance_of(instance, Resource)` returns `true`.

---

### ATK-02: Identity Properties

**Description:** Identity properties uniquely identify an attack and provide human-readable metadata.

| Property | Type | Default | Export | Notes |
|----------|------|---------|--------|-------|
| `attack_id` | `int` | `0` | `@export` | Unique numeric ID. Convention: 100-series for base (101–104), 200-series for fused (M12). |
| `attack_name` | `String` | `""` | `@export` | Human-readable name (e.g., "Claw Swipe", "Acid Spit"). |
| `description` | `String` | `""` | `@export` | Brief description for HUD/UI tooltip. Optional; empty string is valid. |

**Acceptance Criteria:**
- AC-02a: All three properties are exported and typed.
- AC-02b: Default values match the table above when instantiated via `.new()`.
- AC-02c: Properties are assignable and readable at runtime.

---

### ATK-03: Effect Type

**Description:** The `effect_type` property is a `String` that acts as the dispatch key for the AttackExecutor (M11-05). It uses string enum convention (uppercase constants) rather than a GDScript `enum` to allow extensibility without recompilation.

| Property | Type | Default | Export | Notes |
|----------|------|---------|--------|-------|
| `effect_type` | `String` | `""` | `@export` | One of the known values below, or a future extension. |

**Known effect_type values (initial set):**

| Value | Behavior | M11 Example |
|-------|----------|-------------|
| `"MELEE_SWIPE"` | Close-range hitbox in front of attacker | Claw Swipe |
| `"PROJECTILE_SPIT"` | Spawns a projectile that travels and hits on contact | Acid Spit |
| `"SLAM_AOE"` | Area-of-effect ground impact (charge + slam) | Carapace Slam |
| `"LUNGE"` | Short dash forward with melee hit on contact | Adhesion Lunge |

**Extensibility:** New effect_type strings can be added without modifying AttackResource. The executor (M11-05) adds a handler for each new effect_type via a `match` statement. Unknown values are not validated at the Resource level — the executor logs an error for unrecognized types.

**Acceptance Criteria:**
- AC-03a: `effect_type` is exported and typed as `String`.
- AC-03b: Default is `""` (empty string).
- AC-03c: Can be set to any of the four known values and read back.
- AC-03d: Can be set to an arbitrary string (extensibility); no validation in the Resource.

---

### ATK-04: Core Combat Parameters

**Description:** Numeric parameters that govern damage, timing, and spatial behavior.

| Property | Type | Default | Export | Notes |
|----------|------|---------|--------|-------|
| `damage` | `float` | `1.0` | `@export` | Base damage per hit. Zero is valid (utility attacks). Negative values are allowed by the Resource but semantically nonsensical (edge case for tests). |
| `cooldown` | `float` | `0.8` | `@export` | Seconds until attack can be used again. |
| `attack_range` | `float` | `1.5` | `@export` | Melee range OR projectile spread radius. Named `attack_range` to avoid shadowing GDScript built-in `range()`. See ATK-DR-1. |
| `startup_frames` | `int` | `0` | `@export` | Frames before hitbox activates (animation lead). 0 = instant. |
| `knockback_magnitude` | `float` | `0.0` | `@export` | Force applied on hit. 0.0 = no knockback. |
| `knockback_direction` | `String` | `"away"` | `@export` | Direction of knockback: `"away"` (push target away from attacker), `"toward"` (pull target toward attacker), `"none"` (no directional component). See ATK-DR-2. |

**Acceptance Criteria:**
- AC-04a: All six properties are exported and typed per the table.
- AC-04b: Default values match the table when instantiated via `.new()`.
- AC-04c: All properties are independently assignable and readable.
- AC-04d: `knockback_direction` accepts arbitrary strings (no Resource-level validation); known values are `"away"`, `"toward"`, `"none"`.

---

### ATK-05: Projectile-Specific Parameters

**Description:** Parameters relevant only to projectile-type attacks. These are still present on all AttackResource instances (simplifies the data model), but only consumed by projectile-related effect_type handlers.

| Property | Type | Default | Export | Notes |
|----------|------|---------|--------|-------|
| `projectile_speed` | `float` | `0.0` | `@export` | Speed in units/sec. 0.0 = not a projectile attack. |
| `projectile_lifetime` | `float` | `2.0` | `@export` | Seconds before projectile auto-despawns. See ATK-DR-4. |

**Acceptance Criteria:**
- AC-05a: Both properties are exported and typed per the table.
- AC-05b: Default values match the table when instantiated via `.new()`.
- AC-05c: Both are present on non-projectile attacks (just unused at 0.0/2.0).

---

### ATK-06: Visual Feedback Properties

**Description:** Properties controlling visual appearance of the attack effect.

| Property | Type | Default | Export | Notes |
|----------|------|---------|--------|-------|
| `color` | `Color` | `Color.WHITE` | `@export` | VFX/ability badge color. |
| `vfx_scale` | `float` | `1.0` | `@export` | Magnitude of visual feedback (particle size, flash intensity). |

**Acceptance Criteria:**
- AC-06a: Both properties are exported and typed per the table.
- AC-06b: `color` defaults to `Color.WHITE` (1, 1, 1, 1).
- AC-06c: `vfx_scale` defaults to `1.0`.
- AC-06d: Color components (r, g, b, a) are individually readable after assignment.

---

### ATK-07: Modifiers Dictionary Contract

**Description:** The `modifiers` property is a schemaless `Dictionary` for extensible key-value pairs. Any string key is allowed. No validation is performed at the Resource level — validation (if any) is the executor's responsibility.

| Property | Type | Default | Export | Notes |
|----------|------|---------|--------|-------|
| `modifiers` | `Dictionary` | `{}` | `@export` | Extensible key-value pairs. |

**Known modifier keys (documented, not enforced):**

| Key | Type | Description | Example |
|-----|------|-------------|---------|
| `acid_on_hit` | `bool` | Enable acid damage-over-time on hit | `true` |
| `acid_duration` | `float` | Duration of acid DOT in seconds | `2.0` |
| `acid_dps` | `float` | Acid damage per second | `0.3` |
| `poison` | `bool` | Enable poison DOT on hit | `true` |
| `poison_duration` | `float` | Duration of poison in seconds | `3.0` |
| `poison_dps` | `float` | Poison damage per second | `0.5` |
| `slow` | `float` | Movement speed multiplier during effect (0.0–1.0) | `0.7` |
| `slow_duration` | `float` | Duration of slow effect in seconds | `2.0` |
| `followup_melee` | `bool` | Enable melee follow-up after projectile | `true` |
| `followup_range` | `float` | Range of melee follow-up | `2.0` |
| `followup_damage` | `float` | Damage of melee follow-up | `1.0` |
| `weaken` | `bool` | Enable weakness debuff | `true` |
| `weaken_duration` | `float` | Duration of weakness debuff | `2.0` |

**Contract:**
- The dictionary is **schemaless**: any `String` key maps to any `Variant` value.
- Empty dictionary (`{}`) is the default and is valid (attack has no special modifiers).
- The executor (M11-05) reads modifier keys via `modifiers.get("key", default)` with explicit fallback defaults.
- Adding a new modifier key does **not** require changes to AttackResource.
- Nested dictionaries are **not recommended** but not prohibited by the Resource. Executor handlers are responsible for their own depth limits.

**Acceptance Criteria:**
- AC-07a: `modifiers` is exported and typed as `Dictionary`.
- AC-07b: Default is an empty dictionary `{}`.
- AC-07c: Key-value pairs can be set and read back correctly (string keys, mixed value types).
- AC-07d: Multiple modifiers can coexist in the same dictionary.
- AC-07e: `modifiers.get("nonexistent_key", default)` returns the default.

---

### ATK-08: Serialization Contract

**Description:** AttackResource is a Godot `Resource` and must be serializable via Godot's built-in resource system.

**Requirements:**
- ATK-08a: Can be saved as a `.tres` file via `ResourceSaver.save()`.
- ATK-08b: Can be loaded from a `.tres` file via `ResourceLoader.load()` (or `load()`/`preload()`).
- ATK-08c: Round-trip serialization preserves all property values (identity, combat, projectile, visual, modifiers).
- ATK-08d: `Resource.duplicate()` creates a deep copy with all properties intact.
- ATK-08e: Two resources with identical property values are value-equal (property-by-property comparison); they are not reference-equal.

**Acceptance Criteria:**
- AC-08a: `resource.duplicate()` returns a new instance with matching property values.
- AC-08b: Modifying the duplicate does not affect the original.
- AC-08c: `.tres` serialization round-trip is deferred to integration testing (requires Godot file I/O) but the Resource class must not override or break `_get_property_list()`.

---

### ATK-09: Example Attack Configurations

**Description:** The following four attack configurations are the M11 baseline. They must be representable as AttackResource instances and serve as concrete test fixtures.

**Claw Swipe (base, melee):**

| Property | Value |
|----------|-------|
| `attack_id` | `101` |
| `attack_name` | `"Claw Swipe"` |
| `description` | `"Quick melee swipe at close range"` |
| `effect_type` | `"MELEE_SWIPE"` |
| `damage` | `2.0` |
| `cooldown` | `0.8` |
| `attack_range` | `1.5` |
| `startup_frames` | `2` |
| `knockback_magnitude` | `100.0` |
| `knockback_direction` | `"away"` |
| `projectile_speed` | `0.0` |
| `projectile_lifetime` | `2.0` |
| `color` | `Color(0.8, 0.2, 0.1)` |
| `vfx_scale` | `1.0` |
| `modifiers` | `{}` |

**Acid Spit (base, projectile):**

| Property | Value |
|----------|-------|
| `attack_id` | `102` |
| `attack_name` | `"Acid Spit"` |
| `description` | `"Ranged acid projectile with DOT"` |
| `effect_type` | `"PROJECTILE_SPIT"` |
| `damage` | `1.5` |
| `cooldown` | `1.2` |
| `attack_range` | `15.0` |
| `startup_frames` | `0` |
| `knockback_magnitude` | `50.0` |
| `knockback_direction` | `"away"` |
| `projectile_speed` | `250.0` |
| `projectile_lifetime` | `2.0` |
| `color` | `Color(0.2, 0.8, 0.1)` |
| `vfx_scale` | `1.0` |
| `modifiers` | `{"acid_on_hit": true, "acid_duration": 2.0, "acid_dps": 0.3}` |

**Carapace Slam (base, area-of-effect):**

| Property | Value |
|----------|-------|
| `attack_id` | `103` |
| `attack_name` | `"Carapace Slam"` |
| `description` | `"Heavy charge into ground slam"` |
| `effect_type` | `"SLAM_AOE"` |
| `damage` | `35.0` |
| `cooldown` | `4.0` |
| `attack_range` | `6.0` |
| `startup_frames` | `6` |
| `knockback_magnitude` | `22.0` |
| `knockback_direction` | `"away"` |
| `projectile_speed` | `0.0` |
| `projectile_lifetime` | `2.0` |
| `color` | `Color(0.6, 0.4, 0.2)` |
| `vfx_scale` | `1.5` |
| `modifiers` | `{}` |

**Adhesion Lunge (base, lunge):**

| Property | Value |
|----------|-------|
| `attack_id` | `104` |
| `attack_name` | `"Adhesion Lunge"` |
| `description` | `"Short dash forward with root on hit"` |
| `effect_type` | `"LUNGE"` |
| `damage` | `0.0` |
| `cooldown` | `2.0` |
| `attack_range` | `3.0` |
| `startup_frames` | `0` |
| `knockback_magnitude` | `0.0` |
| `knockback_direction` | `"none"` |
| `projectile_speed` | `0.0` |
| `projectile_lifetime` | `2.0` |
| `color` | `Color(0.9, 0.7, 0.2)` |
| `vfx_scale` | `1.0` |
| `modifiers` | `{"root_duration": 0.5}` |

**Acceptance Criteria:**
- AC-09a: Each of the four configurations can be instantiated and all properties set without error.
- AC-09b: Property values match the tables above when read back.
- AC-09c: Modifier dictionaries are correctly populated and queryable via `.get()`.

---

## 5. Frozen Property List (Summary)

| # | Property | Type | Default | Category |
|---|----------|------|---------|----------|
| 1 | `attack_id` | `int` | `0` | Identity |
| 2 | `attack_name` | `String` | `""` | Identity |
| 3 | `description` | `String` | `""` | Identity |
| 4 | `effect_type` | `String` | `""` | Dispatch |
| 5 | `damage` | `float` | `1.0` | Combat |
| 6 | `cooldown` | `float` | `0.8` | Combat |
| 7 | `attack_range` | `float` | `1.5` | Combat |
| 8 | `startup_frames` | `int` | `0` | Combat |
| 9 | `knockback_magnitude` | `float` | `0.0` | Combat |
| 10 | `knockback_direction` | `String` | `"away"` | Combat |
| 11 | `projectile_speed` | `float` | `0.0` | Projectile |
| 12 | `projectile_lifetime` | `float` | `2.0` | Projectile |
| 13 | `color` | `Color` | `Color.WHITE` | Visual |
| 14 | `vfx_scale` | `float` | `1.0` | Visual |
| 15 | `modifiers` | `Dictionary` | `{}` | Extensible |

All 15 properties are `@export`-annotated and typed.

---

## 6. Deferred Boundary

The following are **explicitly out of scope** for M11-04:

| Item | Owner | Notes |
|------|-------|-------|
| `AttackExecutor` class | M11-05 | Runtime dispatch (`match effect_type`) |
| `AttackDatabase` / resource file storage | M11-05+ | How resources are registered/looked up |
| Hitbox creation / collision | M11-05 | Scene-tree wiring |
| Cooldown tracking at player level | M11-05 | PlayerController integration |
| Fused attack definitions | M12 | 200-series attack_ids |
| Effect_type validation | M11-05 | Executor logs unknown types |
| Charge scaling (`is_chargeable`, `max_charge_mult`) | M13+ | Future extension |

AttackResource is a **pure data container**. It has no `_ready()`, no `_process()`, no `_physics_process()`, no signals, and no methods beyond those inherited from `Resource`.

---

## 7. Test Strategy

### Test scope

Data-only Resource tests — property contracts, defaults, serialization, and example configurations. No runtime behavior testing (no scene tree, no physics, no input).

### Test file

`tests/scripts/attacks/test_attack_resource.gd`

### Test categories

| Category | What to test | ATK Requirement |
|----------|-------------|-----------------|
| Instantiation | `AttackResource.new()` succeeds, `is_instance_of(Resource)` | ATK-01 |
| Defaults | Every property has correct default after `.new()` | ATK-02 through ATK-07 |
| Typed access | Set and read each property; verify type preservation | ATK-02 through ATK-07 |
| Effect type values | Set each of the four known effect_type strings | ATK-03 |
| Knockback direction values | Set `"away"`, `"toward"`, `"none"` and read back | ATK-04 |
| Modifier operations | Set/get/has_key on modifiers; mixed value types; `.get()` with defaults | ATK-07 |
| Serialization | `duplicate()` round-trip; independence of copy from original | ATK-08 |
| Example configs | Instantiate all four M11 attacks; verify all property values | ATK-09 |

### Adversarial test categories (Test Breaker)

| Category | Edge case |
|----------|-----------|
| Negative damage | `damage = -5.0` — Resource accepts it (no validation) |
| Zero cooldown | `cooldown = 0.0` — valid (no artificial floor) |
| Empty attack_name | `attack_name = ""` — valid |
| Unknown effect_type | `effect_type = "UNKNOWN_TYPE"` — Resource accepts any string |
| Large modifiers | Dictionary with 100+ keys — no crash |
| Nested modifier values | Modifier value is a Dictionary — allowed but not recommended |
| Color boundary values | `Color(0, 0, 0, 0)` transparent, `Color(1, 1, 1, 1)` white |
| Duplicate attack_ids | Two resources with same `attack_id` — no uniqueness enforcement at Resource level |
| Zero attack_range | `attack_range = 0.0` — valid |
| Negative knockback | `knockback_magnitude = -10.0` — Resource accepts (semantics are executor's concern) |
| Very large startup_frames | `startup_frames = 99999` — valid |
| Empty modifiers after population | Set modifiers, then clear to `{}` — should work |

---

## 8. Edge Cases Table

| # | Scenario | Expected Behavior | Rationale |
|---|----------|-------------------|-----------|
| EC-1 | `damage = -5.0` | Resource stores the value; no error | Data container has no validation. Executor handles semantics. |
| EC-2 | `cooldown = 0.0` | Resource stores `0.0` | No artificial minimum. Zero-cooldown attacks are valid (spam attacks). |
| EC-3 | `attack_name = ""` | Resource stores `""` | Empty name is the default. UI layer can handle display. |
| EC-4 | `effect_type = "UNKNOWN_TYPE"` | Resource stores the string | No enum validation. Executor logs error for unknown types (M11-05). |
| EC-5 | `modifiers = {}` (empty) | Default state; `modifiers.get("any_key", default)` returns default | Most base attacks have no modifiers. |
| EC-6 | `modifiers` with 100+ keys | Dictionary stores all; no performance degradation expected | GDScript dictionaries handle large key sets. |
| EC-7 | Nested modifier value (e.g., `"combo": {"hits": 2, "delay": 0.1}`) | Resource stores it. Executor reads at its own depth. | Not recommended but not prohibited. |
| EC-8 | Two resources with `attack_id = 101` | Both valid; no uniqueness enforcement | Uniqueness is AttackDatabase's concern (M11-05+). |
| EC-9 | `knockback_direction = "diagonal"` (unknown value) | Resource stores it | String enum is convention, not enforced. |
| EC-10 | `color = Color(2.0, -1.0, 0.5)` | Resource stores it (Godot Color allows HDR/out-of-range values) | No clamping at Resource level. |
| EC-11 | `attack_range = 0.0` | Resource stores `0.0` | Zero range is meaningful (self-only attacks). |
| EC-12 | `projectile_speed = 0.0` on a PROJECTILE_SPIT | Resource stores it | Data inconsistency is executor's problem, not the Resource's. |
| EC-13 | `startup_frames = -1` | Resource stores it (GDScript `int` allows negative) | No validation. |
| EC-14 | `duplicate()` then modify copy | Original unchanged; copy has new values | Standard Resource.duplicate() behavior. |

---

## 9. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| `attack_range` rename breaks ticket examples | Low | Ticket examples use `range:`; this spec normalizes to `attack_range`. Test Designer must use `attack_range` in all tests. |
| SLAM_AOE vs CHARGE naming for carapace-style attacks | Medium | This spec uses `SLAM_AOE` per task directive. The existing `carapace_husk_attack.gd` implements a linear charge, which could map to either. The executor (M11-05) defines the handler semantics. If both behaviors are needed, `CHARGE` can be added as a new effect_type later without changing AttackResource. |
| Modifiers dictionary type safety | Low | Schemaless by design. The risk of misspelled keys (e.g., `"acid_duraton"` vs `"acid_duration"`) is accepted for flexibility. Executor should use `.get()` with explicit defaults. |
| First `scripts/attacks/` directory | Low | Implementation agent must create the directory. No existing files to conflict with. |
| First custom Resource in project | Low | Godot Resources are well-documented. No project-specific Resource conventions to follow (this sets the convention). |

---

## 10. Clarifying Questions

All questions from the planning phase have been resolved:

| Question | Resolution | Confidence |
|----------|------------|------------|
| Use `range` or `attack_range`? | `attack_range` — avoids GDScript built-in shadowing; matches all 4 existing enemy scripts (ATK-DR-1) | High |
| `knockback_direction` top-level or in modifiers? | Top-level export per ticket AC (ATK-DR-2) | High |
| Include `description` and `projectile_lifetime`? | Yes — low-cost additions from design spec (ATK-DR-3, ATK-DR-4) | High |
| Effect_type values for M11? | MELEE_SWIPE, PROJECTILE_SPIT, SLAM_AOE, LUNGE (extensible via new strings) | High |
| Test scope for data-only Resource? | Property contracts, defaults, serialization, example configs. No runtime behavior (ATK-01 through ATK-09). | High |

No unresolved ambiguities remain.

---

## 11. Traceability Matrix

| Ticket AC | Spec Requirement | Test Category |
|-----------|-----------------|---------------|
| `AttackResource` class created | ATK-01 | Instantiation |
| All properties exported and typed | ATK-02 through ATK-07 | Defaults, Typed access |
| Class documented with examples | ATK-09 | Example configs |
| Modifiers system documented | ATK-07 | Modifier operations |
| Tests validate property access and serialization | ATK-02–ATK-08 | All categories |
| `run_tests.sh` exits 0 | (integration) | Full suite run |
