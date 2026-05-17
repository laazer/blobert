# M35: Enemy Ability Drop System

**Status:** Planning  
**Depends:** M2, M11-M12

## Overview

Formalize enemy mutation drop mechanic with rarity tiers, drop rates, and integration into infection loop. When enemy is absorbed, determine which mutation is granted with probability weighting.

## Key Systems

- **Drop table**: Per-enemy-family mutation probability
- **Rarity tiers**: Common/uncommon/rare/epic mutations
- **Mutation grants**: Add to player inventory on absorption
- **Visual feedback**: Drop particle, notification, unlock animation

## Tickets

- 01_mutation_drop_table_system
- 02_weighted_drop_probability
- 03_inventory_integration_and_feedback
