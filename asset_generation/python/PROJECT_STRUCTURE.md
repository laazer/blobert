# Project Structure

```
blender-experiments/
│
├── main.py                      # CLI (commands: animated, smart, stats, view, import, list, test)
├── enemy.sh                     # Shell wrapper — delegates to main.py
│
├── bin/
│   ├── __init__.py
│   └── find_blender.py          # Cross-platform Blender resolver (env var → default paths → $PATH)
│
├── src/
│   ├── core/
│   │   └── blender_utils.py     # Scene setup, mesh ops, armature binding, random helpers
│   │
│   ├── materials/
│   │   └── material_system.py   # Procedural material creation (Principled BSDF + textures)
│   │
│   ├── body_families/           # Body-family hub: ids, bones, motion_*, factory, registry, keywords
│   │   ├── ids.py               # EnemyBodyTypes
│   │   ├── bones.py             # BoneNames (enemy armatures)
│   │   ├── keywords.py          # Smart-generation keywords (no Blender/rig deps)
│   │   ├── motion_*.py          # BaseBodyType + Blob / Quadruped / Humanoid motion
│   │   ├── factory.py           # BodyTypeFactory
│   │   └── registry.py          # BODY_FAMILY_REGISTRY + rig_definition_for_import
│   │
│   ├── animations/
│   │   ├── keyframe_system.py   # set_bone_keyframe, create_simple_armature
│   │   ├── body_types.py        # Re-exports body_families (backward compatibility)
│   │   └── animation_system.py  # create_all_animations orchestrator
│   │
│   ├── enemies/
│   │   ├── base_enemy.py        # BaseEnemy ABC, export_enemy(), get_attack_profile()
│   │   ├── animated_acid_spitter.py  # AnimatedAcidSpitter
│   │   ├── animated_adhesion_bug.py  # AnimatedAdhesionBug
│   │   ├── animated_carapace_husk.py  # AnimatedCarapaceHusk
│   │   ├── animated_claw_crawler.py  # AnimatedClawCrawler
│   │   ├── animated_ember_imp.py  # AnimatedEmberImp
│   │   ├── animated_tar_slug.py  # AnimatedTarSlug
│   │   ├── animated/            # Package: registry.py (AnimatedEnemyBuilder) + __init__ re-exports
│   │   ├── base_models/         # Body archetypes: BaseModelType, *Model, ModelTypeFactory
│   │   └── example_new_enemy.py # Reference implementation for adding new enemies
│   │
│   ├── combat/
│   │   ├── attack_data.py             # AttackType enum, AttackData dataclass
│   │   └── enemy_attack_profiles.py   # Per-enemy attack lists with hit frames, ranges, cooldowns
│   │
│   ├── smart/
│   │   └── smart_generation.py  # SmartGenerator, TextToEnemyGenerator, blueprint system
│   │
│   ├── integration/
│   │   └── external_model_importer.py # ExternalModelImporter, import_external_model()
│   │
│   ├── utils/
│   │   ├── constants.py         # EnemyTypes, AnimationTypes, AnimationConfig; re-exports EnemyBodyTypes, BoneNames from body_families
│   │   ├── materials.py         # MaterialNames, MaterialColors, MaterialThemes, MaterialCategories
│   │   ├── simple_viewer.py     # Blender viewer script (used by `view` command)
│   │   └── demo.py
│   │
│   └── generator.py             # Blender-side script, invoked as subprocess for `animated` command
│
├── tests/
│   ├── combat/
│   │   ├── test_attack_data.py           # AttackData, AttackType, to_dict() serialization
│   │   └── test_enemy_attack_profiles.py # Profile completeness, hit frame validity, JSON safety
│   └── animations/
│       └── test_attack_frames.py         # Frame ordering, bone coverage, windup regression tests
│
├── animated_exports/            # Generated GLB + companion .attacks.json
├── exports/                     # Static model exports
├── docs/                        # Extended documentation
│
├── pyproject.toml               # Project metadata, Python >=3.11, dev deps (pytest)
└── uv.lock                      # Locked dependency versions
```

---

## Refactor backlog (oversized / multi-responsibility files)

These are tracked for future work; not blocking current pipelines.

| Area | File | Suggested direction |
|------|------|---------------------|
| CLI | `main.py` | Split handlers and Blender runner under `cli/` |
| Constants | `src/utils/constants.py` | Split by domain (enemy, animation, player, level, export) after stabilizing imports |
| Smart | `src/smart/smart_generation.py` | Split blueprint, parsing, stats, evolution |
| Godot | `scripts/player/player_controller_3d.gd` | Extract chunk / infection helpers |
| Tests | `tests/enemies/test_animated_enemy_classes_adversarial.py` | Split by theme or per-enemy modules |
| Web | `asset_generation/web/frontend/.../quickSourceNav.ts` | Split part-tree data vs path routing |

---

## Key Data Flows

### Animated generation (`python main.py animated adhesion_bug 1`)

```
main.py
  └─ subprocess: blender --background --python src/generator.py -- adhesion_bug 1
       └─ AnimatedEnemyBuilder.create_enemy()
            ├─ AnimatedAdhesionBug.build()
            │    ├─ create_body() / create_head() / create_limbs()
            │    ├─ apply_materials()        →  material_system.py
            │    ├─ create_armature()        →  same enemy class (_armature_bones + create_simple_armature)
            │    └─ create_all_animations()  →  body_families.QuadrupedBodyType (all 13)
            └─ get_attack_profile()          →  combat/enemy_attack_profiles.py
       └─ export_enemy(armature, mesh, filename, dir, attack_profile)
            ├─ {filename}.glb
            └─ {filename}.attacks.json
```

---

## How to Extend

### Add a new animated enemy type

1. Add a module under `src/enemies/` (e.g. `animated_<slug>.py`) with a `BaseEnemy` subclass implementing `create_body()`, `create_head()`, `create_limbs()`, `apply_materials()`, `create_armature()`, `get_body_type()`; register the class in `src/enemies/animated/registry.py` (`ENEMY_CLASSES`) and re-export from `animated/__init__.py` if it should be a public import
2. Ensure `AnimatedEnemyBuilder.ENEMY_CLASSES` maps the slug string to that class
3. Add attack data to `src/combat/enemy_attack_profiles.py`
4. Add the string constant to `EnemyTypes` in `src/utils/constants.py`

### Add a new body type

1. Subclass `BaseBodyType` in `src/body_families/motion_base.py` (or add `motion_<name>.py`), implement the five core methods and optional extended overrides
2. Register the class in `BodyTypeFactory.BODY_TYPES` in `src/body_families/factory.py`; wire keywords in `src/body_families/keywords.py` and `BODY_FAMILY_REGISTRY` in `registry.py` if needed

See `src/enemies/example_new_enemy.py` for a worked example.
