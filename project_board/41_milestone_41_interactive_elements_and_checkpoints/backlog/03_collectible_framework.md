# TICKET: 03_collectible_framework

**Milestone:** M41 Interactive Elements & Checkpoints  
**Status:** Backlog  
**Type:** Implementation

## Title

Collectible Framework — pickup items (potions, chests, buffs)

## Description

Collectible element: contact with player triggers pickup, grants in-game reward (health, mutation, temporary buff). Disappears after pickup. Supports rarity visual feedback.

## Acceptance Criteria

- [x] Collectible inherits InteractiveElement
- [x] On player contact, grant reward and remove from scene
- [x] Reward types: health_potion (+25 HP), mutation_drop, temporary_buff
- [x] Rarity visualization (common/uncommon/rare colors)
- [x] Pickup feedback: sound, particle effect, HUD notification
- [x] Can't pick up twice (removed after contact)
- [x] Tests verify pickup and removal
- [x] `run_tests.sh` exits 0

## Dependencies

- M41:01 (interactive element base)
- M35 (mutation drop system for compatibility)

## Implementation Notes

**Collectible types:**
```gdscript
enum RewardType { HEALTH, MUTATION, TEMPORARY_BUFF }

class Collectible extends InteractiveElement:
    @export var reward_type: RewardType
    @export var reward_value: int
    @export var rarity: String  # "common", "uncommon", "rare"

func on_interact():
    match reward_type:
        RewardType.HEALTH:
            player.heal(reward_value)
        RewardType.MUTATION:
            player.grant_mutation(mutation_id)
    queue_free()
```

## Scope Notes

- Temporary buff duration fixed (not parameterized)
- No visual animation (disappear instant OK)

