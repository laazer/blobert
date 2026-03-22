# Usage Guide

## Interface

All commands are available through two equivalent entry points:

```bash
./enemy.sh <command> [args]        # shell wrapper
python main.py <command> [args]    # direct Python
```

---

## Commands

### `animated` — Generate animated enemies

```bash
python main.py animated <enemy> [count]

python main.py animated adhesion_bug          # 3 variants (default)
python main.py animated adhesion_bug 1        # 1 variant
python main.py animated tar_slug 3
python main.py animated all                   # all 3 animated types
```

**Output** in `animated_exports/`:
- `{enemy}_animated_{nn}.glb` — mesh, armature, and all 13 animations
- `{enemy}_animated_{nn}.attacks.json` — combat stats for game engine use

**Animated enemy types:**
- `adhesion_bug` — 6-legged quadruped; pounce attack
- `tar_slug` — blob; expansion AoE attack
- `ember_imp` — humanoid; fire punch + two-handed slam

---

### `test` — Quick sanity check

```bash
python main.py test
```

Generates one `adhesion_bug` variant. Use this to confirm Blender is found and the pipeline is working.

---

### `list` — Show all enemies and animations

```bash
python main.py list
```

Prints all enemy types and the full list of 13 animation names with durations.

---

### `smart` — AI-assisted generation

```bash
python main.py smart --description "large fire spider with powerful attacks"
python main.py smart --description "small ice blob" --difficulty hard
python main.py smart --description "armored warrior" --export-stats godot

# Material options
python main.py smart --description "veteran fighter" --material-preset battle_worn
python main.py smart --description "swamp thing" --environment swamp --damage-level 0.4
python main.py smart --description "fire elemental" --magical-effects fire
```

**Options:**
- `--difficulty` — `easy`, `normal`, `hard`, `nightmare` (default: `normal`)
- `--seed` — integer seed for reproducible output
- `--export-stats` — `json`, `godot`, `unity`
- `--material-preset` — `battle_worn`, `swamp_corrupted`, `volcanic_forged`, `ice_cursed`, `fire_blessed`, `shadow_touched`, `toxic_mutated`
- `--environment` — `swamp`, `volcanic`, `arctic`, `toxic`, `desert`
- `--damage-level` — `0.0`–`1.0` battle wear
- `--magical-effects` — `fire`, `ice`, `lightning`, `shadow`, `holy`

---

### `stats` — Export combat stats for an existing enemy

```bash
python main.py stats adhesion_bug
python main.py stats adhesion_bug --export-stats godot
python main.py stats tar_slug --export-stats unity --difficulty nightmare
```

---

### `view` — Open a generated enemy in Blender

```bash
python main.py view adhesion_bug_animated_00
python main.py view adhesion_bug_animated_00 --anim move
python main.py view tar_slug_animated_00 --anim attack
```

`--anim` defaults to `idle`. Valid names: `idle`, `move`, `attack`, `special_attack`, `damage`, `damage_heavy`, `damage_fire`, `damage_ice`, `death`, `spawn`, `stunned`, `celebrate`, `taunt`.

---

### `import` — Integrate an external model

```bash
python main.py import --model-path dragon.fbx
python main.py import --model-path warrior.glb --body-type humanoid
python main.py import --model-path creature.obj --body-type blob --animation-set core
```

**Options:**
- `--model-path` — path to model file (required)
- `--body-type` — `blob`, `quadruped`, `humanoid` (default: `quadruped`)
- `--animation-set` — `core` (5 animations), `extended` (8), `all` (13, default)

**Supported formats:** `.fbx`, `.obj`, `.dae`, `.gltf`, `.glb`, `.blend`

The importer will:
1. Analyse the model for an existing armature and animations
2. Create a matching armature if none exists
3. Generate any missing animations for the chosen body type
4. Apply pipeline materials
5. Export to `animated_exports/` in GLB format

---

## Output Files

| File | Location | Contents |
|------|----------|----------|
| `{name}.glb` | `animated_exports/` | Mesh + armature + all animations |
| `{name}.attacks.json` | `animated_exports/` | Hit frames, damage types, range, cooldown |
| `{name}_stats.{format}` | project root | AI-generated enemy stats (smart/stats commands) |

### Attack profile JSON

```json
{
  "filename": "adhesion_bug_animated_00",
  "attacks": [
    {
      "name": "pounce",
      "animation_name": "attack",
      "attack_type": "physical",
      "range": 3.0,
      "hit_frame": 18,
      "cooldown_seconds": 2.0,
      "knockback_force": 5.0,
      "is_area_of_effect": false,
      "aoe_radius": 0.0
    }
  ]
}
```

`hit_frame` is the frame within the animation when damage should register. At 24 fps:
- `attack` (36 frames total) — hit at frame 18
- `special_attack` (60 frames total) — hit at frame 40

---

## Blender Path

Blender is found automatically. Override with an environment variable if needed:

```bash
export BLENDER_PATH=/path/to/blender
python main.py animated adhesion_bug 1
```

Resolution order: `BLENDER_PATH` env var → platform default paths → `blender` on `$PATH`.

---

## Troubleshooting

**`python3 bin/find_blender.py` fails** — Blender not found in standard locations. Set `BLENDER_PATH`.

**`Mesh not valid` warnings** — Harmless mesh validation messages from Blender. GLB is still created correctly.

**`More than 4 joint influences`** — Normal for procedural rigging. Handled automatically during export.
