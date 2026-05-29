# SPEC: Fused Attack Resources

**Ticket:** M12-02 (`project_board/12_milestone_12_fused_mutation_attacks/backlog/02_fused_attack_resources.md`)
**Spec ID:** FAR
**Status:** Frozen
**Revision:** 1
**Author:** Spec Agent
**Spec Exit Type:** generic
**Date:** 2026-05-29

---

## 1. Overview

This spec defines the 6 canonical fused `AttackResource` instances for the M12 fused mutation attack system. All 6 resources are registered in `AttackDatabaseNode._register_defaults()` via `register_fused_attack()` calls, using the exact same named-constant + `AttackResource.new()` + property-assignment pattern established by the 4 base attacks.

No `.tres` files are created. No new directory is introduced. There is no `res://attacks/fused/` path in this project.

The spec freezes: (1) the registration pattern (DR-1), (2) all stat values at magnitudes consistent with base attacks (DR-2), (3) the attack ID scheme 101–106 (DR-3), and (4) the named-constant requirement for every numeric literal (DR-4).

**Scope:** `scripts/attacks/attack_database.gd` — additions to `_register_defaults()` and the named-constant block at the top of `AttackDatabaseNode`. Tests in `tests/scripts/attacks/` validating the 6 registrations and their content values.

**Out of scope:** Enemy reactions to fused damage types, HUD changes, new effect-type handlers, new modifier handler implementations, `.tres` file creation.

---

## 2. Evidence Sources

| Source | Path |
|--------|------|
| Ticket | `project_board/12_milestone_12_fused_mutation_attacks/backlog/02_fused_attack_resources.md` |
| AttackResource class | `scripts/attacks/attack_resource.gd` |
| AttackDatabase implementation | `scripts/attacks/attack_database.gd` |
| FADI spec (FADI-DD-4: 6-combo matrix) | `project_board/specs/fused_attack_database_integration_spec.md` |
| Planning checkpoint | `project_board/checkpoints/M12-02/2026-05-29T-plan-run.md` |
| Spec checkpoint | `project_board/checkpoints/M12-02/2026-05-29T-spec-run.md` |

---

## 3. Frozen Design Decisions

All four decisions are normative. No implementation agent may deviate without a plan revision.

### DR-1: Code Registration — No .tres Files

**Decision:** All 6 fused attacks are registered in `AttackDatabaseNode._register_defaults()` via `register_fused_attack(slot_a_id, slot_b_id, resource)` calls appended after the 4 base attack registrations. The ticket title references `.tres` files, but the entire existing attack system uses code registration only. There is no `attacks/` directory in the project root. Code registration is the authoritative pattern.

**Rationale:** Consistency with all 4 base attacks. No Godot resource file parsing infrastructure needed. The ticket explicitly allows programmatic creation ("Can be created as .tres files manually or programmatically after initial data is defined"). Code registration is strictly simpler and matches existing conventions.

**Observable contract:** After `_ready()`, `get_fused_attack_count() == 6`. All 6 fused resources are accessible via `get_fused_attack(a, b)` using the canonical mutation ID strings `"claw"`, `"acid"`, `"carapace"`, `"adhesion"`.

### DR-2: Stat Range Conventions

**Decision:** All numeric stat values for fused attacks must be within or modestly above the magnitude range established by base attacks. The ticket example values (`knockback_magnitude: 120.0`, `projectile_speed: 200.0`) are out-of-range and must not be used.

**Authoritative ranges:**
- `damage`: 1.5–5.5 (base range 1.0–4.0; fused may be up to ~40% above max base)
- `cooldown`: 1.0–4.0 (base range 0.8–3.5; fused combos typically longer than either component)
- `knockback_magnitude`: 0.0–8.0 (base range 0.0–5.0; max fused knockback is 8.0)
- `projectile_speed`: 8.0–14.0 (base value 8.0; fused may be modestly faster)
- `projectile_lifetime`: 1.0–2.5 (base range 1.25–2.0)
- `attack_range`: 0.0 for PROJECTILE_SPIT; 1.5–3.5 for MELEE_SWIPE and SLAM_AOE
- `vfx_scale`: 1.0–1.8

### DR-3: Attack IDs 101–106

**Decision:** The 6 canonical fused attacks use `attack_id` values 101 through 106, mapped to sorted combo keys as follows:

| attack_id | Sorted Key | Combo |
|-----------|------------|-------|
| 101 | `acid_claw` | claw + acid |
| 102 | `adhesion_claw` | claw + adhesion |
| 103 | `carapace_claw` | claw + carapace |
| 104 | `acid_adhesion` | acid + adhesion |
| 105 | `acid_carapace` | acid + carapace |
| 106 | `adhesion_carapace` | carapace + adhesion |

IDs 1–4 are reserved for base attacks. IDs 600+ are reserved for synthetic test resources. IDs 101–106 provide clear, non-colliding identity for the canonical fused set.

### DR-4: Named Constants Required for Every Numeric Value

**Decision:** Every numeric literal assigned to a fused attack property must be a named constant declared at the top of `AttackDatabaseNode`. This is required for `gd-review` (`task hooks:gd-review`) to pass without findings.

Named constant naming convention: `<COMBO_KEY_UPPER>_<PROPERTY_UPPER>` where combo key is the sorted key in upper snake case (e.g., `ACID_CLAW` for the `acid_claw` combo).

String values (attack_name, description, knockback_direction) and Color values do not require named constants (they are not flagged as tuning literals by `gd-review`). However, the spec defines them as string literals in the registration block for clarity.

---

## 4. Fused Attack Stat Blocks

The following 6 subsections define the complete property values for each fused attack. All numeric values appear first as their named constant and then their frozen value. These are the authoritative values that implementation must use verbatim.

### 4.1 acid_claw (attack_id 101) — "Toxic Slash"

A fast melee swipe charged with acid. Combines Claw's close-range speed with Acid's damage-over-time coating. Meaningfully stronger than Claw (damage) and adds acid modifier absent from Claw alone.

| Named Constant | Value | Property |
|----------------|-------|----------|
| `ACID_CLAW_ATTACK_ID` | `101` | `attack_id` |
| `ACID_CLAW_DAMAGE` | `4.0` | `damage` |
| `ACID_CLAW_COOLDOWN` | `1.5` | `cooldown` |
| `ACID_CLAW_RANGE` | `1.5` | `attack_range` |
| `ACID_CLAW_KNOCKBACK` | `3.0` | `knockback_magnitude` |
| `ACID_CLAW_VFX_SCALE` | `1.3` | `vfx_scale` |

| Property | Value | Notes |
|----------|-------|-------|
| `attack_name` | `"Toxic Slash"` | String literal |
| `description` | `"Acid-coated melee swipe. Applies acid on hit."` | String literal |
| `effect_type` | `"MELEE_SWIPE"` | Claw-dominant |
| `startup_frames` | `0` | Identity literal; exempt from named-constant rule |
| `knockback_direction` | `"away"` | String literal |
| `projectile_speed` | `0.0` | Identity literal |
| `projectile_lifetime` | `0.0` | Identity literal |
| `color` | `Color(0.6, 0.85, 0.0)` | Yellow-green: acid tint on claw orange |
| `modifiers` | `{"acid_on_hit": true, "acid_duration": 2.0, "acid_dps": 0.8}` | Combined from Acid base |

Modifier value notes: `acid_duration` 2.0 (shorter than base Acid's 3.0 — melee DoT window is shorter range), `acid_dps` 0.8 (lower than base Acid's 1.0 — direct melee damage compensates).

### 4.2 adhesion_claw (attack_id 102) — "Sticky Slash"

A melee swipe that coats the target in adhesive on contact. Combines Claw's fast direct damage with Adhesion's root/slow effect applied at melee range. Distinctly different from Adhesion's ranged projectile root.

| Named Constant | Value | Property |
|----------------|-------|----------|
| `ADHESION_CLAW_ATTACK_ID` | `102` | `attack_id` |
| `ADHESION_CLAW_DAMAGE` | `3.5` | `damage` |
| `ADHESION_CLAW_COOLDOWN` | `2.0` | `cooldown` |
| `ADHESION_CLAW_RANGE` | `1.5` | `attack_range` |
| `ADHESION_CLAW_KNOCKBACK` | `1.0` | `knockback_magnitude` |
| `ADHESION_CLAW_VFX_SCALE` | `1.2` | `vfx_scale` |
| `ADHESION_CLAW_SLOW_DURATION` | `2.0` | Used in `modifiers` |

| Property | Value | Notes |
|----------|-------|-------|
| `attack_name` | `"Sticky Slash"` | String literal |
| `description` | `"Melee swipe that roots the target on contact."` | String literal |
| `effect_type` | `"MELEE_SWIPE"` | Claw-dominant |
| `startup_frames` | `0` | Identity literal |
| `knockback_direction` | `"away"` | String literal |
| `projectile_speed` | `0.0` | Identity literal |
| `projectile_lifetime` | `0.0` | Identity literal |
| `color` | `Color(0.85, 0.65, 0.0)` | Amber: claw orange + adhesion gold |
| `modifiers` | `{"slow": 0.0, "slow_duration": ADHESION_CLAW_SLOW_DURATION}` | Root via slow=0.0 (Adhesion pattern) |

Design note: `knockback_magnitude` is reduced (1.0 vs Claw's 2.0) because adhesion rooting an enemy is already a strong positioning effect; high knockback would work against the root's purpose.

### 4.3 carapace_claw (attack_id 103) — "Armored Slam"

A leaping melee strike delivered from a carapace-enhanced body. Combines Claw's direct damage with Carapace's AoE radius and knockback. Bridges single-target melee and multi-target AoE, with a shorter wind-up than full Carapace.

| Named Constant | Value | Property |
|----------------|-------|----------|
| `CARAPACE_CLAW_ATTACK_ID` | `103` | `attack_id` |
| `CARAPACE_CLAW_DAMAGE` | `5.0` | `damage` |
| `CARAPACE_CLAW_COOLDOWN` | `3.0` | `cooldown` |
| `CARAPACE_CLAW_RANGE` | `2.5` | `attack_range` |
| `CARAPACE_CLAW_KNOCKBACK` | `6.0` | `knockback_magnitude` |
| `CARAPACE_CLAW_STARTUP_FRAMES` | `8` | `startup_frames` |
| `CARAPACE_CLAW_VFX_SCALE` | `1.5` | `vfx_scale` |

| Property | Value | Notes |
|----------|-------|-------|
| `attack_name` | `"Armored Slam"` | String literal |
| `description` | `"Powerful melee slam in a wider arc. Infects weakened enemies."` | String literal |
| `effect_type` | `"SLAM_AOE"` | Carapace-dominant; AoE matches the hardened body slam |
| `knockback_direction` | `"away"` | String literal |
| `projectile_speed` | `0.0` | Identity literal |
| `projectile_lifetime` | `0.0` | Identity literal |
| `color` | `Color(0.65, 0.35, 0.05)` | Dark orange-brown: carapace brown + claw orange |
| `modifiers` | `{"infect_weakened": true}` | Claw's infect modifier carried forward |

Design note: `startup_frames` 8 is shorter than Carapace's 12 (Claw's speed contribution), `attack_range` 2.5 is between Claw's 1.5 and Carapace's 3.0, `knockback_magnitude` 6.0 exceeds Carapace's 5.0 (Claw's momentum adds to the slam).

### 4.4 acid_adhesion (attack_id 104) — "Venom Web"

A sticky acid projectile that roots the first enemy hit and applies acid damage-over-time. Combines both ranged projectile mutations. The root traps the enemy in acid, amplifying the DoT window. This is the most crowd-control-oriented combo.

| Named Constant | Value | Property |
|----------------|-------|----------|
| `ACID_ADHESION_ATTACK_ID` | `104` | `attack_id` |
| `ACID_ADHESION_DAMAGE` | `2.0` | `damage` |
| `ACID_ADHESION_COOLDOWN` | `3.0` | `cooldown` |
| `ACID_ADHESION_PROJECTILE_SPEED` | `10.0` | `projectile_speed` |
| `ACID_ADHESION_PROJECTILE_LIFETIME` | `1.75` | `projectile_lifetime` |
| `ACID_ADHESION_VFX_SCALE` | `1.2` | `vfx_scale` |
| `ACID_ADHESION_SLOW_DURATION` | `2.5` | Used in `modifiers` |
| `ACID_ADHESION_ACID_DURATION` | `3.0` | Used in `modifiers` |
| `ACID_ADHESION_ACID_DPS` | `1.2` | Used in `modifiers` |

| Property | Value | Notes |
|----------|-------|-------|
| `attack_name` | `"Venom Web"` | String literal |
| `description` | `"Sticky acid projectile. Roots first target and applies acid."` | String literal |
| `effect_type` | `"PROJECTILE_SPIT"` | Both components are PROJECTILE_SPIT |
| `startup_frames` | `0` | Identity literal |
| `attack_range` | `0.0` | Identity literal; range implicit in lifetime * speed |
| `knockback_magnitude` | `0.0` | Identity literal; root replaces knockback |
| `knockback_direction` | `"none"` | String literal |
| `color` | `Color(0.3, 0.75, 0.1)` | Acid green with adhesion gold tint |
| `modifiers` | `{"acid_on_hit": true, "acid_duration": ACID_ADHESION_ACID_DURATION, "acid_dps": ACID_ADHESION_ACID_DPS, "slow": 0.0, "slow_duration": ACID_ADHESION_SLOW_DURATION}` | Full combination of both base modifiers |

Design note: `projectile_speed` 10.0 (faster than both base projectiles at 8.0 — fused momentum). `acid_dps` 1.2 exceeds base Acid's 1.0 because the root guarantees the full DoT lands. `slow_duration` 2.5 is shorter than Adhesion's 3.0 root to balance against the added acid DoT.

### 4.5 acid_carapace (attack_id 105) — "Corrosive Slam"

A ground slam that sprays acid across the AoE impact zone. Combines Carapace's heavy AoE with Acid's DoT. Enemies caught in the slam radius receive both knockback and acid coating. The most area-denial-oriented combo.

| Named Constant | Value | Property |
|----------------|-------|----------|
| `ACID_CARAPACE_ATTACK_ID` | `105` | `acid_id` |
| `ACID_CARAPACE_DAMAGE` | `4.5` | `damage` |
| `ACID_CARAPACE_COOLDOWN` | `4.0` | `cooldown` |
| `ACID_CARAPACE_RANGE` | `3.5` | `attack_range` |
| `ACID_CARAPACE_KNOCKBACK` | `4.0` | `knockback_magnitude` |
| `ACID_CARAPACE_STARTUP_FRAMES` | `12` | `startup_frames` |
| `ACID_CARAPACE_VFX_SCALE` | `1.8` | `vfx_scale` |
| `ACID_CARAPACE_ACID_DURATION` | `2.5` | Used in `modifiers` |
| `ACID_CARAPACE_ACID_DPS` | `0.6` | Used in `modifiers` |

| Property | Value | Notes |
|----------|-------|-------|
| `attack_name` | `"Corrosive Slam"` | String literal |
| `description` | `"Ground slam that coats the impact zone with acid."` | String literal |
| `effect_type` | `"SLAM_AOE"` | Carapace-dominant; AoE is the delivery mechanism |
| `knockback_direction` | `"away"` | String literal |
| `projectile_speed` | `0.0` | Identity literal |
| `projectile_lifetime` | `0.0` | Identity literal |
| `color` | `Color(0.4, 0.65, 0.05)` | Olive-green: carapace earth + acid green |
| `modifiers` | `{"acid_on_hit": true, "acid_duration": ACID_CARAPACE_ACID_DURATION, "acid_dps": ACID_CARAPACE_ACID_DPS}` | Acid DoT applied to all AoE targets on hit |

Design note: `cooldown` 4.0 is the highest in the game (slower than Carapace's 3.5) to offset the AoE + DoT combination. `attack_range` 3.5 exceeds Carapace's 3.0 (acid spray extends the effective splash). `knockback_magnitude` 4.0 is less than Carapace's 5.0 (the slam is less concussive; the acid coating is the primary threat). `acid_dps` 0.6 is below base Acid's 1.0 because it is applied to multiple targets simultaneously.

### 4.6 adhesion_carapace (attack_id 106) — "Web Slam"

A ground slam that covers the impact zone in sticky webbing, rooting multiple enemies in place. Combines Carapace's AoE coverage with Adhesion's root effect. Highly disruptive crowd control.

| Named Constant | Value | Property |
|----------------|-------|----------|
| `ADHESION_CARAPACE_ATTACK_ID` | `106` | `attack_id` |
| `ADHESION_CARAPACE_DAMAGE` | `3.5` | `damage` |
| `ADHESION_CARAPACE_COOLDOWN` | `3.5` | `cooldown` |
| `ADHESION_CARAPACE_RANGE` | `3.0` | `attack_range` |
| `ADHESION_CARAPACE_KNOCKBACK` | `2.0` | `knockback_magnitude` |
| `ADHESION_CARAPACE_STARTUP_FRAMES` | `12` | `startup_frames` |
| `ADHESION_CARAPACE_VFX_SCALE` | `1.6` | `vfx_scale` |
| `ADHESION_CARAPACE_SLOW_DURATION` | `2.0` | Used in `modifiers` |

| Property | Value | Notes |
|----------|-------|-------|
| `attack_name` | `"Web Slam"` | String literal |
| `description` | `"Ground slam that roots all enemies in the impact zone."` | String literal |
| `effect_type` | `"SLAM_AOE"` | Carapace-dominant; AoE delivery |
| `knockback_direction` | `"away"` | String literal |
| `projectile_speed` | `0.0` | Identity literal |
| `projectile_lifetime` | `0.0` | Identity literal |
| `color` | `Color(0.55, 0.45, 0.1)` | Dark gold-brown: carapace brown + adhesion gold |
| `modifiers` | `{"slow": 0.0, "slow_duration": ADHESION_CARAPACE_SLOW_DURATION}` | Root via slow=0.0 applied AoE |

Design note: `knockback_magnitude` 2.0 is intentionally low compared to Carapace's 5.0. The adhesion root is the primary crowd-control effect; high knockback would scatter enemies out of the sticky zone before they are rooted. `slow_duration` 2.0 (shorter than Adhesion's 3.0 single-target root; multi-target AoE root is balanced by shorter duration).

---

## 5. Requirements

---

### Requirement FAR-1: Named Constants for All Fused Attack Numeric Properties

#### 1. Spec Summary

- **Description:** Every numeric value used in a fused attack registration block must be a named constant declared in `AttackDatabaseNode` at the class level, following the pattern `const <COMBO_KEY_UPPER>_<PROPERTY_UPPER> := <value>`. This applies to `attack_id`, `damage`, `cooldown`, `attack_range` (when non-zero), `knockback_magnitude` (when non-zero), `projectile_speed` (when non-zero), `projectile_lifetime` (when non-zero), `vfx_scale`, `startup_frames` (when non-zero), and any numeric modifier dictionary values.
- **Constraints:** Identity literals (`0`, `0.0`) assigned to properties are exempt from the named-constant rule (they are not tuning literals). The `attack_id` integer is not exempt — each fused attack's ID must be a named constant (e.g., `ACID_CLAW_ATTACK_ID := 101`). Named constants use `:=` (type-inferred) consistent with the base attack constants in `attack_database.gd`. `const` declarations must be at class scope (not inside functions).
- **Assumptions:** `gd-review` (`task hooks:gd-review`) will flag unexplained numeric literals in `_register_defaults()`. All 6 stat blocks defined in Section 4 satisfy this constraint when their named constants are declared.
- **Scope:** `scripts/attacks/attack_database.gd` — the named-constant block and `_register_defaults()` function.

#### 2. Acceptance Criteria

- **FAR-1a:** Every non-identity numeric literal assigned to a fused attack property inside `_register_defaults()` resolves to a named `const` declared at class level in `AttackDatabaseNode`.
- **FAR-1b:** No unexplained numeric literal (e.g., `2.0`, `101`, `3.0`) appears inline in the fused registration blocks; `gd-review` produces zero findings for the fused registration section.
- **FAR-1c:** All 40 named constants defined in Section 4 (6 combos × ~6-7 numeric properties each) are present in `attack_database.gd` with values matching Section 4 exactly.
- **FAR-1d:** The `attack_id` constant for each fused attack is declared (e.g., `const ACID_CLAW_ATTACK_ID := 101`) and used in the registration block.
- **FAR-1e:** Modifier numeric values (e.g., `acid_duration`, `acid_dps`, `slow_duration`) that are non-identity are also named constants rather than inline literals.

#### 3. Risk & Ambiguity Analysis

- **Identity literals in modifiers:** `{"slow": 0.0}` — the value `0.0` for the `slow` key is an identity/falsy-zero value that encodes the root mechanic (per the M11-11 adhesion spec: `slow=0.0` means full stop). This is an identity literal by convention and is exempt from the named-constant rule. Implementation must not introduce a named constant for it (it would be misleading).
- **`true` boolean literals:** `{"acid_on_hit": true}` — boolean `true` is not a tuning literal and is exempt.
- **Reviewer disagreement risk:** If `gd-review` flags vfx_scale or startup_frames defaults as findings, implementation agent must extract them to named constants regardless. This spec pre-emptively includes constants for all non-identity numeric values to avoid any reviewer findings.

#### 4. Clarifying Questions

None.

---

### Requirement FAR-2: Registration Pattern — register_fused_attack() Calls in _register_defaults()

#### 1. Spec Summary

- **Description:** Six `register_fused_attack(slot_a_id, slot_b_id, resource)` calls are appended to `_register_defaults()` after the 4 existing `register_base_attack()` calls. Each call uses the two canonical mutation ID string literals as `slot_a_id` and `slot_b_id` arguments. The order of the two arguments does not affect the stored key (alphabetical sort is applied internally by `_make_fused_key()`), but for readability the arguments should be provided in alphabetical order (matching the sorted key).
- **Constraints:** The registration calls must appear inside `_register_defaults()`, not in `_ready()` or any other function. The `AttackResource.new()` + property assignment + `register_fused_attack()` block for each fused attack follows the identical structure as the base attack blocks. No `.tres` file loading. No `load()` or `preload()` calls.
- **Assumptions:** The 4 canonical mutation ID strings are `"claw"`, `"acid"`, `"carapace"`, `"adhesion"`. These must be used verbatim in the `register_fused_attack()` arguments.
- **Scope:** `scripts/attacks/attack_database.gd`, `_register_defaults()` function.

#### 2. Acceptance Criteria

- **FAR-2a:** `_register_defaults()` contains exactly 6 `register_fused_attack()` calls after the completion of all 4 `register_base_attack()` calls.
- **FAR-2b:** Each of the 6 calls uses the correct canonical mutation ID string pair matching the combo it registers, using the sorted (alphabetical) order as the first and second arguments.
- **FAR-2c:** For each call, the `resource` argument is an `AttackResource` created inline (via `AttackResource.new()`) in the same block, with all properties assigned before the `register_fused_attack()` call.
- **FAR-2d:** No `.tres` file loading (`load()`, `preload()`, `ResourceLoader.load()`) appears in `_register_defaults()` or `_ready()` for fused attacks.
- **FAR-2e:** The 6 registration calls are ordered by sorted key alphabetically: `acid_claw`, `adhesion_claw`, `carapace_claw`, `acid_adhesion`, `acid_carapace`, `adhesion_carapace`. (Note: alphabetical order of sorted keys is: `acid_adhesion`, `acid_carapace`, `acid_claw`, `adhesion_carapace`, `adhesion_claw`, `carapace_claw`. Either declaration order is acceptable as long as all 6 are present; the observable contract is registration completeness, not order.)

#### 3. Risk & Ambiguity Analysis

- **Order of declarations vs order of arguments:** The declaration order inside `_register_defaults()` has no observable effect. The important constraint is that `slot_a_id` and `slot_b_id` are the correct canonical strings for the combo. Tests must verify the registered resource is retrievable via `get_fused_attack("claw", "acid")` and `get_fused_attack("acid", "claw")`, not that the registration call used a specific argument order.
- **Base attack registration must come first:** The 4 base attack registrations must remain in place and unchanged. The fused registrations are purely additive at the end.

#### 4. Clarifying Questions

None.

---

### Requirement FAR-3: Fused Attack IDs Are Unique and In Range 101–106

#### 1. Spec Summary

- **Description:** The `attack_id` for each fused attack is assigned from the range 101–106, one per combo, as defined in DR-3. No two fused attacks share an `attack_id`. These IDs do not overlap with base attack IDs (1–4) or test synthetic IDs (600+).
- **Constraints:** The specific ID-to-combo mapping is frozen: `acid_claw`=101, `adhesion_claw`=102, `carapace_claw`=103, `acid_adhesion`=104, `acid_carapace`=105, `adhesion_carapace`=106.
- **Assumptions:** No other system currently uses attack IDs in the 101–106 range. No assumption is made about how `attack_id` is consumed by external systems (it is stored as a plain integer property and not validated by `AttackDatabaseNode`).
- **Scope:** `attack_id` property assignments in `_register_defaults()` and named constants `ACID_CLAW_ATTACK_ID` through `ADHESION_CARAPACE_ATTACK_ID`.

#### 2. Acceptance Criteria

- **FAR-3a:** `get_fused_attack("acid", "claw").attack_id == 101`
- **FAR-3b:** `get_fused_attack("adhesion", "claw").attack_id == 102`
- **FAR-3c:** `get_fused_attack("carapace", "claw").attack_id == 103`
- **FAR-3d:** `get_fused_attack("acid", "adhesion").attack_id == 104`
- **FAR-3e:** `get_fused_attack("acid", "carapace").attack_id == 105`
- **FAR-3f:** `get_fused_attack("adhesion", "carapace").attack_id == 106`
- **FAR-3g:** No two fused attacks return the same `attack_id` value (the 6 IDs are distinct). A test collecting all 6 `attack_id` values into an array and asserting `array.size() == array.duplicate().size()` (or equivalent uniqueness check) passes.
- **FAR-3h:** No base attack (`get_base_attack("claw")`, `get_base_attack("acid")`, etc.) has an `attack_id` in the range 101–106.

#### 3. Risk & Ambiguity Analysis

- **ID validation not enforced by database:** `AttackDatabaseNode` does not validate `attack_id` uniqueness at registration time. A test must explicitly verify the IDs rather than relying on runtime enforcement. This is by design (the same as base attacks, which are not ID-validated either).
- **Future ID expansion:** If M13 or later milestones introduce new mutations beyond the 4 canonical ones, their fused combos would need IDs beyond 106. The 101–106 range should be treated as reserved for these 6 canonical combos only.

#### 4. Clarifying Questions

None.

---

### Requirement FAR-4: Fused Attack Stat Values Match Section 4 Spec Blocks

#### 1. Spec Summary

- **Description:** The observable property values of each registered fused `AttackResource` must match the frozen stat blocks defined in Section 4 of this spec. Tests must verify each property of each fused attack by asserting the returned resource's fields against the specified values.
- **Constraints:** All values must match exactly (no float approximation tolerance beyond normal float equality in GDScript for exact decimal values like `4.0`, `1.5`, etc.). Color values must match the specified `Color(r, g, b)` constructor values. Modifier dictionaries must have the exact keys defined in Section 4 with the exact values.
- **Assumptions:** GDScript float literals like `4.0`, `1.5`, `2.5` represent exact IEEE 754 values with no rounding ambiguity at these magnitudes.
- **Scope:** Tests in `tests/scripts/attacks/` asserting fused attack property values.

#### 2. Acceptance Criteria

The following per-combo AC groups define which properties must be verified. Tests must cover every row marked (Required).

**FAR-4-101 (acid_claw / Toxic Slash):**
- **FAR-4-101a (Required):** `damage == 4.0`
- **FAR-4-101b (Required):** `cooldown == 1.5`
- **FAR-4-101c (Required):** `attack_range == 1.5`
- **FAR-4-101d (Required):** `knockback_magnitude == 3.0`
- **FAR-4-101e (Required):** `effect_type == "MELEE_SWIPE"`
- **FAR-4-101f (Required):** `modifiers.has("acid_on_hit")` and `modifiers["acid_on_hit"] == true`
- **FAR-4-101g (Required):** `modifiers["acid_duration"] == 2.0`
- **FAR-4-101h (Required):** `modifiers["acid_dps"] == 0.8`
- **FAR-4-101i (Required):** `attack_name == "Toxic Slash"`

**FAR-4-102 (adhesion_claw / Sticky Slash):**
- **FAR-4-102a (Required):** `damage == 3.5`
- **FAR-4-102b (Required):** `cooldown == 2.0`
- **FAR-4-102c (Required):** `attack_range == 1.5`
- **FAR-4-102d (Required):** `knockback_magnitude == 1.0`
- **FAR-4-102e (Required):** `effect_type == "MELEE_SWIPE"`
- **FAR-4-102f (Required):** `modifiers.has("slow")` and `modifiers["slow"] == 0.0`
- **FAR-4-102g (Required):** `modifiers["slow_duration"] == 2.0`
- **FAR-4-102h (Required):** `attack_name == "Sticky Slash"`

**FAR-4-103 (carapace_claw / Armored Slam):**
- **FAR-4-103a (Required):** `damage == 5.0`
- **FAR-4-103b (Required):** `cooldown == 3.0`
- **FAR-4-103c (Required):** `attack_range == 2.5`
- **FAR-4-103d (Required):** `knockback_magnitude == 6.0`
- **FAR-4-103e (Required):** `startup_frames == 8`
- **FAR-4-103f (Required):** `effect_type == "SLAM_AOE"`
- **FAR-4-103g (Required):** `modifiers.has("infect_weakened")` and `modifiers["infect_weakened"] == true`
- **FAR-4-103h (Required):** `attack_name == "Armored Slam"`

**FAR-4-104 (acid_adhesion / Venom Web):**
- **FAR-4-104a (Required):** `damage == 2.0`
- **FAR-4-104b (Required):** `cooldown == 3.0`
- **FAR-4-104c (Required):** `projectile_speed == 10.0`
- **FAR-4-104d (Required):** `projectile_lifetime == 1.75`
- **FAR-4-104e (Required):** `effect_type == "PROJECTILE_SPIT"`
- **FAR-4-104f (Required):** `modifiers.has("acid_on_hit")` and `modifiers["acid_on_hit"] == true`
- **FAR-4-104g (Required):** `modifiers["acid_duration"] == 3.0`
- **FAR-4-104h (Required):** `modifiers["acid_dps"] == 1.2`
- **FAR-4-104i (Required):** `modifiers.has("slow")` and `modifiers["slow"] == 0.0`
- **FAR-4-104j (Required):** `modifiers["slow_duration"] == 2.5`
- **FAR-4-104k (Required):** `attack_name == "Venom Web"`

**FAR-4-105 (acid_carapace / Corrosive Slam):**
- **FAR-4-105a (Required):** `damage == 4.5`
- **FAR-4-105b (Required):** `cooldown == 4.0`
- **FAR-4-105c (Required):** `attack_range == 3.5`
- **FAR-4-105d (Required):** `knockback_magnitude == 4.0`
- **FAR-4-105e (Required):** `startup_frames == 12`
- **FAR-4-105f (Required):** `effect_type == "SLAM_AOE"`
- **FAR-4-105g (Required):** `modifiers.has("acid_on_hit")` and `modifiers["acid_on_hit"] == true`
- **FAR-4-105h (Required):** `modifiers["acid_duration"] == 2.5`
- **FAR-4-105i (Required):** `modifiers["acid_dps"] == 0.6`
- **FAR-4-105j (Required):** `attack_name == "Corrosive Slam"`

**FAR-4-106 (adhesion_carapace / Web Slam):**
- **FAR-4-106a (Required):** `damage == 3.5`
- **FAR-4-106b (Required):** `cooldown == 3.5`
- **FAR-4-106c (Required):** `attack_range == 3.0`
- **FAR-4-106d (Required):** `knockback_magnitude == 2.0`
- **FAR-4-106e (Required):** `startup_frames == 12`
- **FAR-4-106f (Required):** `effect_type == "SLAM_AOE"`
- **FAR-4-106g (Required):** `modifiers.has("slow")` and `modifiers["slow"] == 0.0`
- **FAR-4-106h (Required):** `modifiers["slow_duration"] == 2.0`
- **FAR-4-106i (Required):** `attack_name == "Web Slam"`

#### 3. Risk & Ambiguity Analysis

- **Modifier dictionary equality:** Testing `modifiers["slow"] == 0.0` is problematic in GDScript because `0.0` is falsy. Tests must use `modifiers.has("slow")` combined with a type check or explicit `== 0.0` assertion to verify the key exists AND has the correct value. Using only `if modifiers["slow"]` would incorrectly report `0.0` as missing. This matches the M11-11 adhesion bug pattern (the `slow=0.0` falsy bug). Tests must use the null-safe pattern: `assert(modifiers.has("slow") and typeof(modifiers["slow"]) == TYPE_FLOAT and modifiers["slow"] == 0.0)`.
- **Color value equality:** GDScript `Color(r, g, b)` comparison is floating-point. Tests may use `color.is_equal_approx(Color(r, g, b))` or exact equality — both are acceptable since the values are small decimals representable exactly in float32.
- **Modifier dictionary completeness:** Tests should also verify that modifier dictionaries do not contain unexpected extra keys. For example, `acid_claw` modifiers should have exactly 3 keys (`acid_on_hit`, `acid_duration`, `acid_dps`) and no others.

#### 4. Clarifying Questions

None.

---

### Requirement FAR-5: _register_defaults() Fused Attack Count

#### 1. Spec Summary

- **Description:** After `_ready()` completes on a fresh `AttackDatabaseNode` instance, `get_fused_attack_count()` returns exactly `6`. This verifies all 6 fused attacks are registered by `_register_defaults()` without gaps or duplicates.
- **Constraints:** Tests must use a fresh database instance (not the autoload singleton) to avoid cross-test state contamination. The autoload state depends on singleton lifecycle; unit tests must use `AttackDatabaseNode.new()` and call `_register_defaults()` manually, or use the scene tree test harness pattern used in existing ADB tests.
- **Assumptions:** No fused attacks are registered outside of `_register_defaults()`. The count is stable after a single `_register_defaults()` call.
- **Scope:** `AttackDatabaseNode.get_fused_attack_count()` return value.

#### 2. Acceptance Criteria

- **FAR-5a:** On a fresh `AttackDatabaseNode` after `_register_defaults()`, `get_fused_attack_count() == 6`.
- **FAR-5b:** On a fresh `AttackDatabaseNode` before `_register_defaults()` (i.e., after `clear()`), `get_fused_attack_count() == 0`.
- **FAR-5c:** `get_base_attack_count() == 4` is unchanged after the 6 fused registrations are added (additive, no interference).
- **FAR-5d:** Calling `_register_defaults()` a second time on the same instance without a `clear()` in between results in `get_fused_attack_count() == 6` (last-write-wins semantics, not double-registration). This verifies the 6 combo keys are distinct so no accidental self-overwrite doubles a single key.

#### 3. Risk & Ambiguity Analysis

- **FAR-5d risk:** If two fused registration blocks used the same sorted key (e.g., two blocks both register `acid_claw`), the second call would silently overwrite the first. The count would still be 6, but one combo would be wrong. FAR-5d combined with FAR-3g (ID uniqueness) catches this scenario.
- **Autoload singleton state:** The project uses `AttackDatabaseNode` as an autoload. Tests that use `AttackDatabase` (the autoload node name) may see a state that differs from a freshly constructed instance if prior tests registered synthetic resources. Tests must use isolated instances per the pattern in existing ADB test files.

#### 4. Clarifying Questions

None.

---

### Requirement FAR-6: All 6 Fused Attacks Retrievable by Both Lookup Orderings

#### 1. Spec Summary

- **Description:** After `_register_defaults()`, every fused attack can be retrieved in both argument orderings via `get_fused_attack()`. This is guaranteed by `_make_fused_key()` alphabetical sort (FADI-DD-3), but must be explicitly tested for all 6 combos using the real registered resources.
- **Constraints:** Tests for this requirement must use the real registered resources (from a `_register_defaults()` call) rather than synthetic registration. This distinguishes FAR-6 from the FADI-6 combo matrix tests, which use synthetic resources to test the API contract.
- **Assumptions:** FADI-DD-3 (order-independence via alphabetical sort) is already proven correct by FADI-6 tests. FAR-6 adds the integration-level check that the real resources pass through the same mechanism correctly.
- **Scope:** `AttackDatabaseNode.get_fused_attack()` called on a `_register_defaults()`-initialized instance.

#### 2. Acceptance Criteria

For each of the 6 combos, both orderings must return a non-null resource with matching `attack_id`:

- **FAR-6a:** `get_fused_attack("acid", "claw")` returns resource with `attack_id == 101` AND `get_fused_attack("claw", "acid")` returns same resource.
- **FAR-6b:** `get_fused_attack("adhesion", "claw")` returns resource with `attack_id == 102` AND `get_fused_attack("claw", "adhesion")` returns same resource.
- **FAR-6c:** `get_fused_attack("carapace", "claw")` returns resource with `attack_id == 103` AND `get_fused_attack("claw", "carapace")` returns same resource.
- **FAR-6d:** `get_fused_attack("acid", "adhesion")` returns resource with `attack_id == 104` AND `get_fused_attack("adhesion", "acid")` returns same resource.
- **FAR-6e:** `get_fused_attack("acid", "carapace")` returns resource with `attack_id == 105` AND `get_fused_attack("carapace", "acid")` returns same resource.
- **FAR-6f:** `get_fused_attack("adhesion", "carapace")` returns resource with `attack_id == 106` AND `get_fused_attack("carapace", "adhesion")` returns same resource.
- **FAR-6g:** None of the 6 lookups return `null` (all are registered).

#### 3. Risk & Ambiguity Analysis

- **"Same resource" identity:** In GDScript, `get_fused_attack("acid", "claw") === get_fused_attack("claw", "acid")` (identity check) confirms both calls return the exact same object reference stored in `_fused_attacks`. Tests may use `===` or verify the `attack_id` field matches; either is acceptable.
- **No cross-combo contamination:** `get_fused_attack("acid", "claw")` must not return the `acid_adhesion` resource. Tests for FAR-6 should verify `attack_id` to catch any key-collision bugs.

#### 4. Clarifying Questions

None.

---

### Requirement FAR-7: Fused Attacks Are Meaningfully Distinct from Their Base Components

#### 1. Spec Summary

- **Description:** Each fused attack must differ from both of its base component attacks in at least two of: `damage`, `cooldown`, `effect_type`, `modifiers`, `knockback_magnitude`. This requirement ensures fusion produces a new capability, not a reskin of an existing base attack.
- **Constraints:** "Meaningfully different" is formalized below as concrete property differences, not a subjective design judgment. The spec does not require that fused stats always exceed base stats — only that the combination is distinct.
- **Assumptions:** The base attack properties are those registered by `_register_defaults()` at time of writing (M12 release state). Changes to base attacks after M12-02 is complete are out of scope.
- **Scope:** Property comparison between fused resource and its two component base resources.

#### 2. Acceptance Criteria

- **FAR-7a (acid_claw vs claw):** `acid_claw.damage != claw.damage` OR `acid_claw.modifiers != claw.modifiers`. Concretely: `acid_claw.damage (4.0) > claw.damage (3.0)` AND `acid_claw.modifiers` contains `"acid_on_hit"` which `claw.modifiers` does not.
- **FAR-7b (acid_claw vs acid):** `acid_claw.effect_type != acid.effect_type` (MELEE_SWIPE vs PROJECTILE_SPIT). AND `acid_claw.knockback_magnitude (3.0) > acid.knockback_magnitude (0.0)`.
- **FAR-7c (adhesion_claw vs claw):** `adhesion_claw.cooldown (2.0) > claw.cooldown (0.8)` AND `adhesion_claw.modifiers` contains `"slow"` which `claw.modifiers` does not.
- **FAR-7d (adhesion_claw vs adhesion):** `adhesion_claw.effect_type (MELEE_SWIPE) != adhesion.effect_type (PROJECTILE_SPIT)` AND `adhesion_claw.damage (3.5) > adhesion.damage (1.0)`.
- **FAR-7e (carapace_claw vs claw):** `carapace_claw.effect_type (SLAM_AOE) != claw.effect_type (MELEE_SWIPE)` AND `carapace_claw.attack_range (2.5) > claw.attack_range (1.5)`.
- **FAR-7f (carapace_claw vs carapace):** `carapace_claw.damage (5.0) > carapace.damage (4.0)` AND `carapace_claw.modifiers` contains `"infect_weakened"` which `carapace.modifiers` does not.
- **FAR-7g (acid_adhesion vs acid):** `acid_adhesion.projectile_speed (10.0) > acid.projectile_speed (8.0)` AND `acid_adhesion.modifiers` contains `"slow"` which `acid.modifiers` does not.
- **FAR-7h (acid_adhesion vs adhesion):** `acid_adhesion.modifiers` contains `"acid_on_hit"` which `adhesion.modifiers` does not AND `acid_adhesion.cooldown (3.0) > adhesion.cooldown (2.5)`.
- **FAR-7i (acid_carapace vs acid):** `acid_carapace.effect_type (SLAM_AOE) != acid.effect_type (PROJECTILE_SPIT)` AND `acid_carapace.knockback_magnitude (4.0) > acid.knockback_magnitude (0.0)`.
- **FAR-7j (acid_carapace vs carapace):** `acid_carapace.modifiers` contains `"acid_on_hit"` which `carapace.modifiers` does not AND `acid_carapace.damage (4.5) > acid.damage (1.0)`.
- **FAR-7k (adhesion_carapace vs carapace):** `adhesion_carapace.modifiers` contains `"slow"` which `carapace.modifiers` does not AND `adhesion_carapace.knockback_magnitude (2.0) < carapace.knockback_magnitude (5.0)` (root is the primary effect; knockback is deliberately reduced).
- **FAR-7l (adhesion_carapace vs adhesion):** `adhesion_carapace.effect_type (SLAM_AOE) != adhesion.effect_type (PROJECTILE_SPIT)` AND `adhesion_carapace.damage (3.5) > adhesion.damage (1.0)`.

#### 3. Risk & Ambiguity Analysis

- **Subjectivity risk:** This requirement could be interpreted as "is the attack fun" rather than "do the properties differ". The AC table above converts the design intent into concrete numerical and key-presence assertions that are fully mechanically testable.
- **Base attack changes:** If a base attack's modifiers are changed after this spec is written, FAR-7 assertions that compare modifier keys could fail. This is a maintenance risk, not a spec gap. The assertions are correct at M12-02 freeze date.

#### 4. Clarifying Questions

None.

---

## 6. Non-Functional Requirements

### FAR-NF-1: run_tests.sh Must Exit 0

All tests for M12-02 must pass. `bash ci/scripts/run_tests.sh` (or `timeout 300 godot --headless -s tests/run_tests.gd`) must exit 0 before the ticket can advance to COMPLETE. All pre-existing tests must remain green.

### FAR-NF-2: gd-review Must Pass Clean

`task hooks:gd-review -- scripts/attacks/attack_database.gd` must produce zero findings on the modified file. This is satisfied by FAR-1 (all numeric tuning literals extracted to named constants).

### FAR-NF-3: No New Script Files

All implementation work is confined to `scripts/attacks/attack_database.gd`. No new `.gd`, `.tres`, or `.res` files are created for this ticket. Tests are created in `tests/scripts/attacks/` as new `.gd` test files.

### FAR-NF-4: No Modification to Base Attack Registrations

The 4 existing base attack registration blocks (`claw`, `acid`, `carapace`, `adhesion`) in `_register_defaults()` must be unchanged. No base attack constants, property values, or modifier dictionaries may be altered by the M12-02 implementation.

### FAR-NF-5: Effect Types and Modifier Keys Must Be Existing Handlers

Only effect types with existing handlers in `AttackExecutor` may be used: `"MELEE_SWIPE"`, `"PROJECTILE_SPIT"`, `"SLAM_AOE"`. Only modifier keys with existing processing in the codebase may be used: `"acid_on_hit"`, `"acid_duration"`, `"acid_dps"`, `"infect_weakened"`, `"slow"`, `"slow_duration"`. No new modifier keys or effect types are introduced by this ticket.

### FAR-NF-6: Attack Names Are Unique

All 6 fused `attack_name` values are distinct from each other and from all 4 base attack names. No two attacks share a name string.

---

## 7. Edge Cases and Risks

| ID | Edge Case | Behavior | Risk Level |
|----|-----------|----------|-----------|
| FAR-EC-1 | `slow: 0.0` modifier key — falsy zero bug | Tests must verify `modifiers.has("slow")` AND `modifiers["slow"] == 0.0` using explicit `== 0.0` comparison, not truthiness. Matches M11-11 known bug pattern. | High — silently wrong if tested with `if modifiers["slow"]` |
| FAR-EC-2 | Modifier dictionary extra keys | Each fused attack's modifier dictionary should have exactly the keys defined in Section 4. No undocumented keys. Tests should verify `modifiers.size() == N` for each combo's expected key count. | Medium — extra keys could indicate a copy-paste error in implementation |
| FAR-EC-3 | `_register_defaults()` called twice without `clear()` | Last-write-wins: second registration overwrites first. `get_fused_attack_count() == 6` (not 12). This is correct behavior verified by FAR-5d. | Low — covered by spec |
| FAR-EC-4 | `get_fused_attack()` called before `_ready()` | Database is empty; all lookups return null. This is existing behavior. M12-02 does not change when registration occurs (still in `_ready()` → `_register_defaults()`). | Low — existing behavior unchanged |
| FAR-EC-5 | `acid_adhesion` modifiers contain both `"slow"` and `"acid_on_hit"` keys simultaneously | Both modifiers must coexist in the same dictionary. Test must verify both are present. The `AttackExecutor._apply_modifiers()` iterates the dictionary and applies each modifier independently. | Medium — copy-paste risk: implementing this block last may copy acid-only or adhesion-only block and miss one set of keys |
| FAR-EC-6 | `carapace_claw` uses `SLAM_AOE` effect_type | `SLAM_AOE` handler applies to all enemies in `attack_range` radius (not just a single target). Combined with `infect_weakened` modifier: the modifier applies to each enemy hit by the AoE. This is the correct interpretation and requires no new handler code. | Low — existing SLAM_AOE handler already supports arbitrary modifiers per M11-10 spec |
| FAR-EC-7 | `acid_carapace` `ACID_CARAPACE_ATTACK_ID` constant name typo (uses `acid_id` label in spec table) | Section 4.5 table header says `acid_id` — this is a spec typo; the correct constant name is `ACID_CARAPACE_ATTACK_ID` and the property is `attack_id`. Implementation must use `attack_id`. | Low — implementation agent must use `attack_id` property name, not the table label |
| FAR-EC-8 | Float equality for `acid_dps: 0.8` and `acid_dps: 0.6` | These values (0.8, 0.6) are not exactly representable in IEEE 754 binary float. GDScript `==` comparison may fail. Tests should use `absf(val - 0.8) < 0.001` or `is_equal_approx(val, 0.8)`. | Medium — test implementation detail; apply consistently |

---

## 8. Test Strategy (for Test Designer Agent)

### Test File

New test file: `tests/scripts/attacks/test_fused_attack_resources.gd`

Traceability docstring: `# M12-02, FAR-1 through FAR-7`

The existing `test_fused_combo_matrix.gd` covers FADI-6 (API contract with synthetic resources). The new file covers FAR (real registered resources, content values, ID scheme).

Do NOT add tests to `test_fused_combo_matrix.gd` — that file tests the API contract, not the registered content.

### Test Setup Pattern

Use a fresh `AttackDatabaseNode` instance with `_register_defaults()` called manually (not the autoload singleton) to ensure isolation. Reference the setup pattern from `tests/scripts/attacks/test_attack_database.gd`.

```gdscript
# Example setup (not code — illustrative)
var db: AttackDatabaseNode
func before_each():
    db = AttackDatabaseNode.new()
    add_child(db)  # triggers _ready() -> _register_defaults()
```

### Minimum Required Test Cases

**Registration completeness (FAR-5):**
1. `get_fused_attack_count() == 6` after `_ready()`
2. `get_base_attack_count() == 4` unchanged
3. No fused attack returns null (6 assertions)

**ID verification (FAR-3):**
4. All 6 attack_ids match DR-3 mapping (6 assertions)
5. IDs are unique across all 6 fused attacks

**Bidirectional lookup (FAR-6):**
6. Each of 6 combos: forward lookup returns non-null (6 assertions)
7. Each of 6 combos: reverse lookup returns same resource (6 assertions via `===` or ID check)

**Stat value verification (FAR-4) — minimum one test per combo:**
8. acid_claw: damage, cooldown, effect_type, modifier keys (4+ assertions)
9. adhesion_claw: damage, cooldown, effect_type, slow+slow_duration modifiers (4+ assertions)
10. carapace_claw: damage, effect_type, startup_frames, knockback_magnitude, infect_weakened (5+ assertions)
11. acid_adhesion: both acid and adhesion modifiers present (5+ assertions including slow==0.0 pattern)
12. acid_carapace: damage, cooldown, effect_type, attack_range, acid modifiers (5+ assertions)
13. adhesion_carapace: effect_type, knockback_magnitude, slow+slow_duration modifiers (4+ assertions)

**Modifier dictionary size verification (FAR-EC-2):**
14. `acid_claw.modifiers.size() == 3`
15. `adhesion_claw.modifiers.size() == 2`
16. `carapace_claw.modifiers.size() == 1`
17. `acid_adhesion.modifiers.size() == 5`
18. `acid_carapace.modifiers.size() == 3`
19. `adhesion_carapace.modifiers.size() == 2`

**Meaningful distinction (FAR-7):**
20. acid_claw differs from claw base (damage higher, acid_on_hit not in claw)
21. adhesion_claw effect_type differs from adhesion base
22. carapace_claw effect_type is SLAM_AOE (not MELEE_SWIPE like claw)
23. acid_adhesion modifiers contain both acid and slow keys
24. acid_carapace effect_type is SLAM_AOE (not PROJECTILE_SPIT like acid)
25. adhesion_carapace knockback is less than carapace base knockback

**Attack names (FAR-4 name assertions):**
26. All 6 attack_name values are non-empty and match Section 4 names exactly

**Named constant values indirectly tested:** The above tests verify the values as they appear on the registered resource. Named constant correctness is tested by the matching implementation producing correct property values.

**Total minimum test functions: 26.** Additional adversarial tests covering FAR-EC-1 (`slow==0.0` falsy), FAR-EC-7 (property name correctness), FAR-EC-8 (float approx) are expected from the Test Breaker Agent.

---

## 9. Implementation Guidance (for Implementation Agent)

This section is informative, not normative. It translates spec decisions into direct implementation steps.

**Step 1:** Add named constants for all 6 fused combos at the top of `AttackDatabaseNode`, after the existing 4 base attack constant blocks. Group by combo, one block per combo.

**Step 2:** In `_register_defaults()`, after the `register_base_attack("adhesion", adhesion)` call, add 6 fused attack blocks in this structure (one block per combo):

```
var <combo_var> := AttackResource.new()
<combo_var>.attack_id = <COMBO>_ATTACK_ID
<combo_var>.attack_name = "<Name>"
<combo_var>.description = "<description>"
<combo_var>.effect_type = "<EFFECT_TYPE>"
<combo_var>.damage = <COMBO>_DAMAGE
<combo_var>.cooldown = <COMBO>_COOLDOWN
<combo_var>.attack_range = <COMBO>_RANGE  # or 0.0 literal for projectile combos
<combo_var>.startup_frames = <COMBO>_STARTUP_FRAMES  # or 0 literal if none
<combo_var>.knockback_magnitude = <COMBO>_KNOCKBACK  # or 0.0 literal if none
<combo_var>.knockback_direction = "<direction>"
<combo_var>.projectile_speed = <COMBO>_PROJECTILE_SPEED  # or 0.0 literal if none
<combo_var>.projectile_lifetime = <COMBO>_PROJECTILE_LIFETIME  # or 0.0 literal if none
<combo_var>.color = Color(r, g, b)
<combo_var>.vfx_scale = <COMBO>_VFX_SCALE
<combo_var>.modifiers = { ... }
register_fused_attack("<id_a_sorted>", "<id_b_sorted>", <combo_var>)
```

**Variable names for combo blocks:** `acid_claw_attack`, `adhesion_claw_attack`, `carapace_claw_attack`, `acid_adhesion_attack`, `acid_carapace_attack`, `adhesion_carapace_attack`.

**Step 3:** Run `task hooks:gd-review -- scripts/attacks/attack_database.gd` and verify zero findings. Run `timeout 300 godot --headless -s tests/run_tests.gd` and verify exit 0.

**Note on FAR-EC-7:** In Section 4.5, the named constant table header contains a typo (`acid_id` instead of `attack_id`). The correct GDScript property is `attack_id`. Use `<combo_var>.attack_id = ACID_CARAPACE_ATTACK_ID`.

---

## 10. Checkpoint Log Reference

Assumptions made during this spec run are logged at:
`project_board/checkpoints/M12-02/2026-05-29T-spec-run.md`

---

## 11. Revision History

| Revision | Date | Agent | Change |
|----------|------|-------|--------|
| 1 | 2026-05-29 | Spec Agent | Initial frozen spec |
