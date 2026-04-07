# Architecture Summary

## Design Principles

- **Single responsibility** — each class has one clearly defined job
- **Body type system** — animation logic lives in the body type, not the enemy; new enemies inherit movement for free
- **Constants over magic strings** — enemy animation names/timings in `src/utils/constants.py`; body-family ids and bone names canonical in `src/body_families/`
- **Open/closed** — new enemy types and body types extend the system without modifying existing code

---

## Package Structure

```
src/
├── body_families/
│   ├── ids.py / bones.py     # EnemyBodyTypes, BoneNames
│   ├── keywords.py           # Smart-generation keywords (no Blender deps)
│   ├── motion_*.py           # BaseBodyType + blob / quadruped / humanoid motion
│   ├── factory.py            # BodyTypeFactory
│   └── registry.py           # BODY_FAMILY_REGISTRY, rig_definition_for_import
│
├── utils/
│   ├── constants.py      # EnemyTypes, AnimationTypes, AnimationConfig; re-exports body_families ids/bones
│   └── materials.py      # MaterialNames, MaterialColors, MaterialThemes, MaterialCategories
│
├── core/
│   └── blender_utils.py  # Scene ops, mesh creation, armature binding
│
├── materials/
│   └── material_system.py    # Procedural Principled BSDF materials
│
├── animations/
│   ├── keyframe_system.py    # set_bone_keyframe, create_simple_armature
│   ├── body_types.py         # Re-exports body_families (backward compatibility)
│   └── animation_system.py   # create_all_animations orchestrator
│
├── enemies/
│   ├── base_enemy.py         # BaseEnemy ABC + export_enemy() + get_attack_profile(); subclasses implement create_armature
│   ├── animated_acid_spitter.py  # AnimatedAcidSpitter
│   ├── animated_adhesion_bug.py  # AnimatedAdhesionBug
│   ├── animated_carapace_husk.py  # AnimatedCarapaceHusk
│   ├── animated_claw_crawler.py  # AnimatedClawCrawler
│   ├── animated_ember_imp.py   # AnimatedEmberImp
│   ├── animated_tar_slug.py   # AnimatedTarSlug
│   ├── animated/             # Package: registry (AnimatedEnemyBuilder) + re-exports
│   ├── base_models/          # Package: archetype models + ModelTypeFactory
│   └── example_new_enemy.py  # Annotated reference for new enemy authors
│
├── combat/
│   ├── attack_data.py             # AttackType, AttackData
│   └── enemy_attack_profiles.py   # Per-enemy attack lists with hit frames and combat stats
│
└── smart/
    └── smart_generation.py   # AI-assisted generation from text descriptions
```

---

## Body Type System

Each body type is a self-contained animation system that implements all 13 animations:

```python
class QuadrupedBodyType(BaseBodyType):
    def create_attack_animation(self, length: int):
        # Pounce: all 6 legs coil → spring → brace on landing
        # 4 distinct phases at frames 0, 12, 18, 27, 36

    def create_special_attack_animation(self, length: int):
        # Rearing slash: spine rears back, front legs slam down as claws
```

| Body Type | Enemy | Move Style | Attack |
|-----------|-------|------------|--------|
| `BlobBodyType` | tar_slug | Squash/stretch | Expansion slam |
| `QuadrupedBodyType` | adhesion_bug | Tripod 6-legged gait | Pounce |
| `HumanoidBodyType` | ember_imp | Bipedal walk + arm swing | Fire punch / overhead slam |

Any enemy can be assigned any body type. An insectoid model with `HumanoidBodyType` walks upright and punches.

---

## Combat System

Attack data is decoupled from animations:

```python
AttackData(
    name="pounce",
    animation_name=AnimationTypes.ATTACK,   # which animation drives it
    attack_type=AttackType.PHYSICAL,
    range=3.0,
    hit_frame=18,                           # frame when damage registers (at 24fps)
    cooldown_seconds=2.0,
    knockback_force=5.0,
)
```

`BaseEnemy.get_attack_profile()` looks up the profile by `self.name`, so every enemy automatically exposes its attacks without any boilerplate in the subclass.

`export_enemy()` writes a companion `.attacks.json` alongside the GLB so Godot can load combat stats without parsing the 3D file.

---

## Adding a New Enemy (10 lines)

```python
# src/enemies/animated_frost_jelly.py  (new module per enemy)
class AnimatedFrostJelly(BaseEnemy):
    def create_body(self):
        self.body_scale = random_variance(1.0, 0.2, self.rng)
        body = create_sphere(location=(0, 0, 0.3), scale=(self.body_scale,) * 3)
        self.parts.append(body)

    def create_head(self): ...   # add head geometry
    def create_limbs(self): ...  # optional extra parts

    def apply_materials(self):
        mats = get_enemy_materials('frost_jelly', self.materials, self.rng)
        apply_material_to_object(self.parts[0], mats['body'])

    def _armature_bones(self):
        # Per-enemy bone dict: name -> (head, tail, parent_name_or_None) — see animated_tar_slug.py
        ...

    def create_armature(self):
        return create_simple_armature("frost_jelly", self._armature_bones())

    def get_body_type(self):
        return EnemyBodyTypes.BLOB   # gets all blob animations for free


# Register it in src/enemies/animated/registry.py:
#   ENEMY_CLASSES['frost_jelly'] = AnimatedFrostJelly
```

Then add attacks to `src/combat/enemy_attack_profiles.py` and the type to `EnemyTypes` in `constants.py`.

---

## Adding a New Body Type

```python
# src/body_families/motion_flying.py (example)
class FlyingBodyType(BaseBodyType):
    def create_idle_animation(self, length: int):
        # Wing-tip hover oscillation
        ...

    def create_move_animation(self, length: int):
        # Banking turn with wing tilt
        ...

    def create_attack_animation(self, length: int):
        # Dive bomb with wing fold
        ...

    def create_damage_animation(self, length: int): ...
    def create_death_animation(self, length: int): ...

# Register it:
BodyTypeFactory.BODY_TYPES['flying'] = FlyingBodyType
```

The new body type is immediately available to all existing and future enemies.

---

## Test Coverage

```
tests/
├── combat/
│   ├── test_attack_data.py           # AttackData serialization, AttackType enum
│   └── test_enemy_attack_profiles.py # Profile completeness, hit frame validity
└── animations/
    └── test_attack_frames.py         # Frame ordering, bone coverage
                                      # Regression tests for the windup-overwrite bug
```

Run with: `uv run pytest tests/`

Key regression tests verify that windup and strike keyframes are always on **different** frames — the original bug set both on the same frame, silently discarding the windup.
