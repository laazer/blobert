# TICKET: 03_modifier_unlock_system

**Milestone:** M36 Ability Progression & Leveling  
**Status:** Backlog  
**Type:** Implementation

## Title

Modifier Unlock System — level-gated ability enhancements

## Description

Each mutation can unlock special modifiers at certain levels (e.g., Claw level 3 = armor piercing, Acid level 4 = lingering cloud). Modifiers add effects or stat tweaks tied to level milestones.

## Acceptance Criteria

- [x] Mutation resources support `modifiers: Dictionary[int, Modifier]` (level → effect)
- [x] At least 2 mutations with 1–2 modifiers each defined
- [x] Modifiers unlock when level reached (checked at attack execution)
- [x] Modifier effect applies to attack resource (add effect_type flag or stat)
- [x] Level 3 unlock visible in HUD (M37 integration)
- [x] Tests verify unlock detection
- [x] `run_tests.sh` exits 0

## Dependencies

- M36:01–02 (level tracking and scaling)
- M11-M12 (mutation/attack system)

## Implementation Notes

**Modifier definition:**
```gdscript
class Modifier:
    var name: String
    var effect: String  # "armor_piercing", "lingering_cloud", etc.
    var stat_bonus: Dictionary  # optional {"damage": 0.5, ...}

var modifiers: Dictionary[int, Modifier] = {
    3: Modifier.new("Armor Pierce", "armor_piercing", {}),
    5: Modifier.new("Claw Mastery", "increased_range", {"range": 0.3})
}

func get_active_modifiers(level: int) -> Array[Modifier]:
    return modifiers.keys().filter(func(l): return l <= level).map(func(l): return modifiers[l])
```

## Scope Notes

- Modifiers don't create new attacks (cosmetic or stat-only in base implementation)
- Visual indicator in HUD (M37 owns UI feedback)

