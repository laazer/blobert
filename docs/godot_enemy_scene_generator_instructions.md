# Godot Enemy Scene Auto‑Generator Instructions

This guide explains how to automatically generate reusable Godot enemy
scenes from exported `.glb` models.

The goal is to avoid repetitive manual setup for every enemy variant.

------------------------------------------------------------------------

## What This Script Does

For every `.glb` file in your generated enemy folder, the script will:

-   load the model
-   instantiate it
-   wrap it in a standard enemy root
-   add a collision shape
-   add a hurtbox
-   add common marker nodes
-   assign metadata like enemy family and mutation drop
-   save the result as a reusable `.tscn` scene

This turns raw imported art into game‑ready scene wrappers.

------------------------------------------------------------------------

## Recommended Folder Structure

Use this structure in your Godot project:

    res://assets/enemies/generated_glb/
    res://scenes/enemies/generated/
    res://scripts/enemies/
    res://tools/

Explanation:

-   `generated_glb` holds Blender exports
-   `generated` will hold auto‑created `.tscn` wrapper scenes
-   `scripts/enemies` holds your gameplay scripts
-   `tools` holds the editor automation script

------------------------------------------------------------------------

## Where to Save the Script

Save the generator script here:

    res://tools/generate_enemy_scenes.gd

------------------------------------------------------------------------

## Optional Shared Enemy Script

If you want every generated enemy to automatically get a shared gameplay
script, create this file:

    res://scripts/enemies/enemy_base.gd

Example starter version:

``` gdscript
extends CharacterBody3D

@export var enemy_id: String = ""
@export var enemy_family: String = ""
@export var mutation_drop: String = ""

func _ready() -> void:
    pass
```

If this file exists, the generator script will attach it to generated
enemies.

If it does not exist, the generator will still work.

------------------------------------------------------------------------

## Required Naming Convention

Your exported `.glb` files should follow this format:

    acid_spitter_00.glb
    acid_spitter_01.glb
    blade_sentinel_00.glb
    ring_drone_02.glb

This is important.

The script uses the filename to infer:

-   enemy id
-   enemy family
-   mutation drop

Example:

    acid_spitter_00.glb

becomes:

-   `enemy_id = acid_spitter_00`
-   `enemy_family = acid_spitter`
-   `mutation_drop = acid`

------------------------------------------------------------------------

## Generated Scene Structure

Each generated scene will look roughly like this:

    EnemyRoot
      Visual
        Model
      CollisionShape3D
      Hurtbox
        CollisionShape3D
      AttackOrigin
      ChunkAttachPoint
      PickupAnchor
      VisibleOnScreenNotifier3D

Explanation:

-   **EnemyRoot** is the gameplay root node
-   **Visual** contains the imported `.glb` instance
-   **CollisionShape3D** is the main collision body
-   **Hurtbox** is a child `Area3D` for damage detection
-   **AttackOrigin** is where attacks/projectiles can spawn
-   **ChunkAttachPoint** is where Blobert's chunk can visually attach
-   **PickupAnchor** is a general-purpose grab/carry point
-   **VisibleOnScreenNotifier3D** helps with culling/activation logic

------------------------------------------------------------------------

## Collision Generation Rules

The script builds collision automatically based on mesh bounds.

Heuristic behavior:

-   tall and narrow enemies get a `CapsuleShape3D`
-   other enemies get a `BoxShape3D`

This is not perfect, but it is fast and good enough for first-pass
generated enemies.

You can manually tweak important enemies later.

------------------------------------------------------------------------

## Metadata Added to Each Enemy

Each generated root node gets metadata:

-   `enemy_id`
-   `enemy_family`
-   `mutation_drop`
-   `source_glb`

These are stored using `set_meta()`.

The script also tries to set matching exported variables on the attached
script if they exist.

------------------------------------------------------------------------

## How to Use the Script

### Step 1

Export your enemy models from Blender into:

    res://assets/enemies/generated_glb/

### Step 2

Save the generator script into:

    res://tools/generate_enemy_scenes.gd

### Step 3

Open Godot.

### Step 4

Open the script in the script editor.

### Step 5

Run it.

You can run it from:

-   the Script Editor
-   **File → Run**
-   or by right-clicking the script and selecting run

### Step 6

Generated scenes will appear in:

    res://scenes/enemies/generated/

------------------------------------------------------------------------

## What the Script Automates

The script automatically handles:

-   scanning for `.glb` files
-   loading imported models
-   wrapping models in standardized scenes
-   adding collision
-   adding a hurtbox
-   adding markers
-   assigning metadata
-   saving `.tscn` files

This saves a lot of repetitive setup time.

------------------------------------------------------------------------

## What the Script Does NOT Automate Yet

The script does not yet handle:

-   family-specific AI scripts
-   perfect custom hitboxes
-   special attack tuning
-   animation state setup
-   behavior trees or state machines
-   unique VFX nodes

Those are best added in a second pass.

------------------------------------------------------------------------

## Why This Is Worth Doing

Without automation, you would need to manually repeat the same setup for
every enemy variant:

-   instantiate model
-   add collision
-   add hurtbox
-   add markers
-   save scene

If you have many generated enemies, that becomes a lot of repetitive
work.

With this script, your pipeline becomes:

    Blender generator
    → export GLB
    → Godot auto-wraps models into scenes
    → manual tweak only important enemies

This is a very efficient solo-dev workflow.

------------------------------------------------------------------------

## Best Practices

-   keep filenames consistent
-   use one shared base script at first
-   let collisions be approximate initially
-   hand-tweak only enemies that really need it
-   regenerate scenes any time you update the `.glb` pipeline

------------------------------------------------------------------------

## Summary

This system lets you:

-   generate low‑poly enemies in Blender
-   export them as `.glb`
-   automatically convert them into game-ready Godot scenes

That gives you a scalable pipeline for lots of enemies without lots of
manual editor setup.
