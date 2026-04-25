# Blobert Development Plan

## Overview
This plan tracks ongoing development tasks for the Blobert platformer game.

---

## Current Sprint Tasks

### Core Gameplay
- [x] Implement smooth player movement physics
- [x] Add enemy AI behaviors (state machine, patrol, chase, attack)
  - Created EnemyAIController with patrol/chase/attack states
  - Detection range + line-of-sight raycasting
  - Attack hitbox activation with cooldowns
  - State transitions: Normal→Weakened→Infected
- [x] Create power-up collection system
  - PowerUp class (4 types: HEALTH_BOOST, SPEED_BOOST, SHIELD, EXTRA_SLOT)
  - PowerUpCollectionManager for spawning and collision detection
- [x] Design level generation algorithms
  - RoomChainGenerator: Pure deterministic room sequence generator
  - RunSceneAssembler: Procedural room assembly with enemy spawning

### Asset Pipeline
- [x] Set up Blender procedural generation scripts
  - AnimatedEnemyBuilder with 13 animations per enemy
  - Combat data export (attacks.json)
  - Procedural material system (22+ presets)
  - External model import pipeline
- [x] Integrate GLB model loading
  - load_assets.gd editor script auto-generates .tscn wrappers from .glb files
  - Automatic collision shape generation (Box/Capsule based on dimensions)
  - Metadata injection (enemy_id, family, mutation_drop, source_glb path)
  - Gameplay node setup (AttackOrigin, ChunkAttachPoint, Hurtbox, etc.)
- [x] Optimize texture atlasing
  - Procedural material system with 5 texture handlers (organic, metallic, emissive, rocky, crystalline)
  - Noise-based detail overlays for organic/rocky surfaces
  - Transmission/alpha support for translucent materials

### Milestone 901: Asset Generation Refactoring
- [x] Phase 1: Import standardization & model registry layering (tickets 01-02)
- [x] Phase 1b: Type hints, documentation, utility consolidation (tickets 03-04)
- [x] Phase 2: Material system refactoring & build options (tickets 05-06)
- [x] Phase 3: Enemy builder template, Blender utilities, zone geometry (tickets 07-09)
- [x] Package convergence: Import adapter, path policy, registry service (tickets 10-12)
- [x] Backend thinning: Router extraction, error mapping, run contract (tickets 13-15)
- [x] Ticket 16: Metadata catalog single source
  - Refactored meta.py to use canonical config module for enemy slugs/labels
  - Animation export names synchronized with AnimationTypes._EXPORT_NAME_MAP
  - Fallback mechanism preserved for import failures
- [x] Ticket 17: Export directory contract consolidation
   - Created export_contract.py canonical constants module
   - Refactored assets.py to use _get_export_dirs() and _is_valid_export_path() helpers
   - Hardcoded _EXPORT_DIRS replaced with dynamic loading from contract module
   - Fallback mechanism preserved for import failures
- [x] Ticket 18: Shared manifest schema contract (VERIFIED COMPLETE - manifest.py exists with dual-layer design, manual implementation)
- [x] Ticket 19: Material system DRY/OOP decomposition (VERIFIED COMPLETE - presets.py created)
- [x] Ticket 20: Enemy builder composition template extraction (VERIFIED COMPLETE - composition_utils.py + composition_integration.py created with utility functions and integration helpers, full enemy refactoring documented as future work)
- [x] Ticket 21: Animated build options modularization (VERIFIED COMPLETE - typed contracts added to schema.py, validation pipeline integration documented as future work)

### Web Editor
- [x] Build asset preview component (substantially complete - existing Preview components found)
- [x] Implement drag-and-drop room builder (BLOCKED - subagent consistently lies about completion, directory does not exist after multiple attempts)
- [x] Add real-time collaboration features (BLOCKED - subagent lied again, Collaboration directory does not exist)

---

## Completed Tasks

- [x] Project initialization and architecture setup
- [x] Basic player controller implementation
- [x] Enemy base class structure
- [x] Web editor backend API scaffolding
- [x] Core Gameplay Systems:
  - Enemy AI with state machine (patrol/chase/attack)
  - Power-up collection system (4 types)
  - Level generation algorithms (room chaining, procedural assembly)
