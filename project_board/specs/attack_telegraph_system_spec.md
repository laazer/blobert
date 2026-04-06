# Attack Telegraph System Specification

**Ticket:** `project_board/8_milestone_8_enemy_attacks/in_progress/attack_telegraph_system.md`  
**Spec IDs:** ATS-1 … ATS-9, ATS-NF1, ATS-NF2  
**Spec Version:** 1  
**Spec Author:** Spec Agent  
**Date:** 2026-04-06  
**Stage:** TEST_DESIGN (downstream)

---

## Executive Summary

Enemy attacks are split into a **telegraph phase** (wind-up) and an **active phase** (when damage-dealing behavior is allowed). This specification defines minimum timing (≥ 0.3 s wind-up), visible feedback during wind-up, exported tuning per family, integration with `EnemyAnimationController`, and the boundary with the backlog `hitbox_and_damage_system` ticket. It applies to the four prototype families: **acid_spitter**, **adhesion_bug**, **carapace_husk**, and **claw_crawler** (canonical slugs aligned with `EnemyNameUtils.extract_family_name` and `enemy_mutation_map`).

---

## Requirement ATS-1: Definitions — Telegraph Phase vs Active Phase

#### 1. Spec Summary
- **Description:** For every enemy attack covered by this ticket, the implementation must distinguish two sequential phases. **Telegraph phase:** from the moment the attack cycle starts until the moment the **active phase** begins. **Active phase:** the interval during which the attack may apply damage, spawn damage-dealing projectiles, register melee hits (including radius/overlap checks), or enable `Area3D` attack hitboxes. No overlap: telegraph ends immediately before active begins.
- **Constraints:** Telegraph is mandatory for each attack cycle; skipping straight to active phase is invalid. Death or despawn may abort an in-progress attack; behavior when aborted is implementation-defined but must not apply active-phase damage after the enemy is dead.
- **Assumptions:** “Attack cycle” is one logical attempt (cooldown boundaries apply between cycles). Multiple simultaneous attack cycles per enemy are out of scope unless explicitly added later.
- **Scope:** All four prototype families’ primary attack behaviors for this milestone.

#### 2. Acceptance Criteria
- **AC-ATS-1.1:** Documentation or code structure makes it possible to identify where telegraph starts and where active phase starts for each family’s attack path.
- **AC-ATS-1.2:** Active-phase side effects (projectile spawn, melee hit registration, player damage/root, `Area3D.monitoring` for attack hitbox) occur only after telegraph completion for that cycle.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Ambiguous “start” if attack is triggered from multiple code paths — mitigated by requiring a single entry point per attack script (or documented coordinator).
- **Edge case:** Enemy dies during telegraph — active phase must not run or must no-op damage.

#### 4. Clarifying Questions
- None for this definition; family-specific wiring is covered in ATS-6 and ATS-8.

---

## Requirement ATS-2: Minimum Wind-Up Duration

#### 1. Spec Summary
- **Description:** The telegraph phase must last **at least 0.3 seconds** of **wall-clock** time from telegraph start to active phase start, for every family.
- **Constraints:** The minimum applies regardless of animation length: if the `"Attack"` animation ends sooner than 0.3 s, the implementation must **hold** the end of telegraph (e.g. timer or controller state) until 0.3 s elapsed before entering active phase. If animation is longer than 0.3 s, active phase begins when telegraph completion is signaled per ATS-7 (not before 0.3 s).
- **Assumptions:** Measured in real time (`delta` accumulation or `SceneTree` timers), not scaled by `AnimationPlayer.speed_scale` unless the spec is explicitly extended — default is **unscaled wall-clock** for the 0.3 s floor.
- **Scope:** All four families.

#### 2. Acceptance Criteria
- **AC-ATS-2.1:** For each family, the interval from telegraph start to first active-phase effect is **≥ 0.3 s** under default exported tuning.
- **AC-ATS-2.2:** Tests can observe the timing boundary without flaky frame-one-off failures (e.g. via signals, exported timers, or deterministic test doubles).

#### 3. Risk & Ambiguity Analysis
- **Risk:** Animation-based end before 0.3 s — implementation must pad time (planning checkpoint assumed conservative compliance).
- **Edge case:** Very low FPS — wall-clock still applies; tests should use controlled time steps where possible.

#### 4. Clarifying Questions
- None.

---

## Requirement ATS-3: Visual Change During Telegraph

#### 1. Spec Summary
- **Description:** During the telegraph phase, a **player-visible** change must occur: either the `"Attack"` animation plays via `EnemyAnimationController`, **or** if `"Attack"` is unavailable or not used, an alternative visual (e.g. material color flash, shader parameter, or a dedicated indicator `Node3D` / `MeshInstance3D`) must be active for the duration of telegraph.
- **Constraints:** Idle/Walk alone without any distinct cue is insufficient. The cue must be distinguishable from normal locomotion idle at a typical gameplay camera distance.
- **Assumptions:** Generated enemy scenes include `AnimationPlayer` with `"Attack"` where M7 wiring succeeded; fallback path is required for tests or assets missing `"Attack"`.
- **Scope:** All four families.

#### 2. Acceptance Criteria
- **AC-ATS-3.1:** When an attack enters telegraph, either `AnimationPlayer` plays a clip whose base name resolves to `Attack` (per existing controller base-name rules) **or** a documented fallback visual path runs for the telegraph duration.
- **AC-ATS-3.2:** No family relies solely on invisible timing with no visual or animation change.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Headless tests cannot “see” pixels — tests may assert on animation state, material property, or visibility flags on indicator nodes.

#### 4. Clarifying Questions
- None.

---

## Requirement ATS-4: No Active Damage During Telegraph

#### 1. Spec Summary
- **Description:** While the telegraph phase is in progress, the attack must **not** deal damage, spawn `AcidProjectile3D` (or other damaging projectiles), apply movement root from the attack, nor enable monitoring on an attack `Area3D` hitbox.
- **Constraints:** This ticket does not require implementing `enemy_attack_hitbox.gd` (backlog `hitbox_and_damage_system`). Until that exists, “hitbox” includes **any** damage registration path: projectile `Area3D`, melee radius checks (`AdhesionBugLungeAttack._try_register_hit`), and future dedicated attack `Area3D`.
- **Assumptions:** `hitbox_and_damage_system` will activate `Area3D` only **after** telegraph when integrated; this spec does not duplicate that ticket’s HP/knockback API.
- **Scope:** All attack implementations for the four families.

#### 2. Acceptance Criteria
- **AC-ATS-4.1:** For acid: no projectile instantiation before telegraph completion for that cycle.
- **AC-ATS-4.2:** For adhesion: no lunge motion and no `_try_register_hit` success before telegraph completion.
- **AC-ATS-4.3:** For carapace and claw: no active-phase damage or hit registration before telegraph completion once attack scripts exist.
- **AC-ATS-4.4:** Any future `EnemyAttackHitbox` (or equivalent) is **disabled** during telegraph and enabled only for the active phase.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Race between animation end and timer — ATS-7 defines completion semantics to serialize telegraph end.

#### 4. Clarifying Questions
- None.

---

## Requirement ATS-5: Exported, Non-Hardcoded Telegraph Duration

#### 1. Spec Summary
- **Description:** Each family’s attack logic must expose telegraph duration (or the **floor** duration used when animation is absent) as an **`@export`** variable on the attack script (or a single shared attack coordinator **per enemy instance** with `@export`), not as a magic literal buried only inside private logic with no inspector access.
- **Constraints:** Default export values must satisfy ATS-2 (≥ 0.3 s) **after** any `max(export, 0.3)` (or equivalent clamp) policy the implementation applies. Document the policy in code comment ≤ 2 lines or in the ticket validation notes.
- **Assumptions:** Existing `telegraph_fallback_seconds` on `AcidSpitterRangedAttack` and `AdhesionBugLungeAttack` may be renamed or supplemented by a unified name (e.g. `telegraph_duration_seconds`); renaming is allowed if tests and scenes are updated consistently.
- **Scope:** Attack scripts for all four families.

#### 2. Acceptance Criteria
- **AC-ATS-5.1:** Acid and adhesion attack scripts expose an `@export` that controls minimum telegraph/wall-clock fallback behavior per ATS-2.
- **AC-ATS-5.2:** Carapace and claw attack scripts (when added) expose the same class of export.
- **AC-ATS-5.3:** No attack family relies solely on a hardcoded `0.3` literal with no export controlling the tunable part (constants used only as **documented** floor alongside exports are acceptable).

#### 3. Risk & Ambiguity Analysis
- **Risk:** Two exports (`telegraph_fallback_seconds` + animation) — spec allows both if effective duration still honors ATS-2 and inspector tuning.

#### 4. Clarifying Questions
- None.

---

## Requirement ATS-6: Four Prototype Families

#### 1. Spec Summary
- **Description:** The acceptance criteria of this ticket apply to enemies whose canonical family identifiers are **acid_spitter**, **adhesion_bug**, **carapace_husk**, and **claw_crawler** (matching milestone “four families” and `EnemyNameUtils` / spawn naming).
- **Constraints:** Other archetypes (e.g. tar_slug, ember_imp) are out of scope unless a follow-up ticket extends scope.
- **Assumptions:** `enemy_family` on `EnemyBase` / `EnemyInfection3D` instances matches these slugs when placed in levels or tests.
- **Scope:** Level and test fixtures that claim coverage for “all four families.”

#### 2. Acceptance Criteria
- **AC-ATS-6.1:** Each of the four slugs has an attack path that satisfies ATS-1 through ATS-5 and ATS-7.
- **AC-ATS-6.2:** Verification references concrete scene/script targets listed in ATS-8.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Carapace/claw may lack dedicated attack scripts at spec time — ATS-8 requires implementation to add them; spec is not complete until all four are covered in implementation (may be stubbed minimal attack that still telegraphs).

#### 4. Clarifying Questions
- None.

---

## Requirement ATS-7: EnemyAnimationController Integration

#### 1. Spec Summary
- **Description:** When `AnimationPlayer` has an `"Attack"` clip, telegraph should begin via `EnemyAnimationController.begin_ranged_attack_telegraph()` (or a **renamed** API if refactored, provided behavior is equivalent: plays `Attack`, tracks completion, emits completion signal). Telegraph completion is signaled by `ranged_attack_telegraph_finished` (or renamed signal with identical semantics) after the `Attack` clip finishes per the controller’s existing completion detection.
- **Constraints:** Controller must remain compatible with hit reaction (`Hit` clip) and death (`Death` clip) per existing ACS rules; telegraph must not start during `_hit_active` or after death latch.
- **Assumptions:** `begin_ranged_attack_telegraph` name is historical (“ranged”); melee may reuse the same telegraph entry until a unified `begin_attack_telegraph()` is introduced — either name is acceptable if documented on the controller.
- **Scope:** `scripts/enemies/enemy_animation_controller.gd` and callers.

#### 2. Acceptance Criteria
- **AC-ATS-7.1:** If `begin_*_telegraph()` returns `true`, active phase must not begin until the paired completion signal fires (or telegraph is aborted by death — then no active phase).
- **AC-ATS-7.2:** If `begin_*_telegraph()` returns `false`, attack scripts use the **fallback** wall-clock path using exported duration (≥ 0.3 s per ATS-2).
- **AC-ATS-7.3:** Completion signal emits at most once per successful telegraph start.

#### 3. Risk & Ambiguity Analysis
- **Edge case:** Attack clip loops — generated assets should not loop during telegraph; if they do, controller must still reach “finished” per existing non-looping assumptions or implementation must force one-shot.

#### 4. Clarifying Questions
- None.

---

## Requirement ATS-8: Concrete Integration Points and Script Map

#### 1. Spec Summary
- **Description:** Normative wiring targets for implementation and tests:
  - **acid_spitter:** `scripts/enemy/acid_spitter_ranged_attack.gd` — spawns `AcidProjectile3D` only after telegraph completion; uses `EnemyAnimationController` + fallback timer.
  - **adhesion_bug:** `scripts/enemy/adhesion_bug_lunge_attack.gd` — begins lunge and hit registration only after telegraph completion; same controller + fallback pattern.
  - **carapace_husk** and **claw_crawler:** Implementation must provide attack script(s) (or a shared component) attached to `EnemyInfection3D` instances for these families, satisfying ATS-1–5 and ATS-3. If no bespoke behavior exists yet, a **minimal** attack cycle (e.g. telegraph then placeholder active phase such as enabling a future hitbox or no-op damage with explicit TODO only if tests still prove telegraph contract) is acceptable **only** if tests demonstrate telegraph timing and no-damage-during-telegraph; production damage can follow `hitbox_and_damage_system`.
- **Constraints:** Do not duplicate `hitbox_and_damage_system` deliverables; coordinate on signal ordering (telegraph complete → enable hitbox).
- **Assumptions:** Generated scenes under `scenes/enemies/generated/` include `EnemyAnimationController` child where M7 completed.
- **Scope:** Scripts and scenes for the four families.

#### 2. Acceptance Criteria
- **AC-ATS-8.1:** Acid and adhesion paths remain the reference implementation for controller + fallback pattern.
- **AC-ATS-8.2:** Carapace and claw have identifiable attack entry points in code (new files or clear branches) by implementation completion.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Scope creep into full combat design for carapace/claw — mitigated by minimal viable telegraph + active stub.

#### 4. Clarifying Questions
- None.

---

## Requirement ATS-9: Verification Gate

#### 1. Spec Summary
- **Description:** All behavioral changes are covered by automated tests where feasible, and `timeout 300 ci/scripts/run_tests.sh` exits **0** before the ticket is marked complete.
- **Constraints:** Follow project norms: Godot tests under `tests/`, bounded timeouts.
- **Assumptions:** CI matches local project `run_tests.sh` contract.
- **Scope:** Full repository test gate for this ticket’s merge.

#### 2. Acceptance Criteria
- **AC-ATS-9.1:** `ci/scripts/run_tests.sh` (or project-canonical `run_tests.sh` with 300 s timeout) exits 0 after implementation.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Timing flakes — prefer signals and deterministic stubs over real-time sleeps in tests when possible.

#### 4. Clarifying Questions
- None.

---

## Requirement ATS-NF1: Determinism and Testability

#### 1. Spec Summary
- **Description:** Telegraph logic must be testable headlessly: completion should be observable via public signals, exported state, or injectable doubles without requiring rendered frames.
- **Constraints:** No reliance on `await` wall-clock in tests without harness control; prefer `SceneTreeTimer` with controllable process mode or direct method hooks for tests.
- **Assumptions:** Existing test patterns in `tests/scripts/enemy/` and `tests/scripts/combat/` apply.
- **Scope:** Test design and implementation.

#### 2. Acceptance Criteria
- **AC-ATS-NF1.1:** New tests can assert telegraph vs active ordering without nondeterministic race failures under headless Godot.

#### 3. Risk & Ambiguity Analysis
- **Edge case:** Physics order — document `process_physics_priority` if attack runs relative to `EnemyInfection3D`.

#### 4. Clarifying Questions
- None.

---

## Requirement ATS-NF2: Performance and Side Effects

#### 1. Spec Summary
- **Description:** Telegraph must not add per-frame allocations hot paths beyond existing attack loops; avoid connecting duplicate signals every frame.
- **Constraints:** One-shot connections (`CONNECT_ONE_SHOT`) for telegraph completion are acceptable; repeated `connect` without guard is not.
- **Assumptions:** Enemy count in prototype levels stays modest.
- **Scope:** Implementation of attack cycles.

#### 2. Acceptance Criteria
- **AC-ATS-NF2.1:** Telegraph start does not leak connections or grow listener lists unbounded across attack cycles (use one-shot or guarded connect).

#### 3. Risk & Ambiguity Analysis
- **Low risk** for prototype scale.

#### 4. Clarifying Questions
- None.

---

## Dependency Matrix

| Dependency ticket | Relationship |
|-------------------|----------------|
| `hitbox_and_damage_system` | **Upstream for Area3D hitboxes.** Telegraph ticket defines ordering: telegraph completes before hitbox enables. Does not implement HP/knockback. |
| `animation_controller_script` (M7) | **Upstream.** Provides `begin_ranged_attack_telegraph` + completion signal and `Attack` clip playback. |

---

## Traceability: Ticket Acceptance Criteria → Spec

| Ticket AC | Spec IDs |
|-----------|----------|
| Wind-up ≥ 0.3 s before hitbox/damage active | ATS-2, ATS-4 |
| Visual change during wind-up | ATS-3 |
| Hitbox/damage not during wind-up | ATS-4 |
| Exported duration, not hardcoded | ATS-5 |
| All four enemy families | ATS-6, ATS-8 |
| `run_tests.sh` exits 0 | ATS-9 |

---

## Document History

| Version | Date | Author | Notes |
|---------|------|--------|-------|
| 1 | 2026-04-06 | Spec Agent | Initial specification (ATS-*). |
