# Environment Texture Usage Guide

## Blobert Platformer Project

This document explains how to use the **Lab**, **Cave**, and **Forest**
texture sets generated for the Blobert platformer project.

The goal is to provide a clear reference for: - Level building - Tilemap
setup - Material usage - Visual consistency - Asset organization

------------------------------------------------------------------------

# Texture Sets Overview

The project currently uses three primary environment texture groups:

  Environment   Theme                     Purpose
  ------------- ------------------------- -----------------------
  Lab           Sci‑fi testing facility   Tutorial / early game
  Cave          Underground caverns       Mid‑game exploration
  Forest        Surface wilderness        Later game levels

Each set contains tiles suitable for:

-   Platforms
-   Background walls
-   Decorations
-   Hazards
-   Environmental storytelling

------------------------------------------------------------------------

# Recommended Tile Sizes

Use one of the following sizes for consistency across all environments:

**Preferred**

    128 x 128 tiles

**Retro option**

    64 x 64 tiles

Use the same tile size across every tileset to simplify level
construction.

------------------------------------------------------------------------

# Tilemap Structure (Godot)

Recommended TileMap layers:

  Layer     Purpose
  --------- ---------------------
  Layer 0   Background walls
  Layer 1   Structural terrain
  Layer 2   Platforms
  Layer 3   Hazards
  Layer 4   Decorations
  Layer 5   Interactive objects

Example structure:

    Layer 5  Collectibles / triggers
    Layer 4  Decorations
    Layer 3  Hazards
    Layer 2  Platforms
    Layer 1  Walls
    Layer 0  Background

------------------------------------------------------------------------

# Lab Texture Set

## Theme

Clean futuristic testing facility.

Inspired by: - Portal test chambers - Sci‑fi laboratories - Research
facilities

## Tile Types

### Wall Panels

Used for background and structural surfaces.

    ████████████
    █          █
    █          █
    ████████████

Features: - panel seams - smooth metallic surfaces - subtle color
variation

### Platform Tops

Flat metal walking surfaces.

    ████████████

### Hazard Edges

Used for platform borders.

    ///////\\\

These visually indicate dangerous edges or industrial machinery.

### Control Panels

Decorative machinery blocks.

Uses: - puzzle terminals - level decoration - story elements

### Pipes and Conduits

Background details connecting machinery.

### Containment Tubes

Glass containers holding experimental materials.

Uses: - enemy spawning - environmental storytelling - puzzle mechanics

### Laser Barriers

Vertical or horizontal energy gates.

    |  |
    |  |
    |  |

Used for: - hazards - locked areas - puzzle gates

------------------------------------------------------------------------

# Cave Texture Set

## Theme

Natural underground caverns.

Inspired by: - crystal caves - subterranean rivers - rocky caverns

## Tile Types

### Rock Walls

Used for structural cave boundaries.

### Rock Platforms

    ████████

Used for: - jumping sections - narrow pathways - elevation changes

### Cracked Stone Floors

Flat cave floors.

### Crystal Nodes

Glowing crystals embedded in rock.

Uses: - collectibles - power sources - visual highlights

### Water Pools

Underground streams or pools.

------------------------------------------------------------------------

# Forest Texture Set

## Theme

Surface wilderness and overgrown ruins.

Inspired by: - mossy forests - ancient ruins - lush environments

## Tile Types

### Grass Platforms

    ████████

Green grassy surfaces used for walking platforms.

### Mossy Stone

Rock surfaces with vegetation.

### Forest Floor

Dirt and stone paths.

### Mushrooms and Plants

Decorative flora.

### Wooden Structures

Old cabins or bridges.

------------------------------------------------------------------------

# Platform Construction

Typical platform design:

    platform top
    ████████████

    hazard edge
    ///////\\\

Use contrasting colors so the player can easily recognize:

-   walkable surfaces
-   hazards
-   decorative background

------------------------------------------------------------------------

# Environmental Storytelling

Each environment should visually communicate progression.

## Level Progression Example

    Lab Facility
        ↓
    Cave Network
        ↓
    Surface Forest

Example narrative:

-   Blobert escapes the laboratory
-   travels through underground tunnels
-   emerges into the natural world

------------------------------------------------------------------------

# Asset Organization

Recommended project structure:

    assets/
      textures/
        lab/
        cave/
        forest/
      tilesets/
      enemies/
      effects/

Example:

    assets/textures/lab/lab_tileset.png
    assets/textures/cave/cave_tileset.png
    assets/textures/forest/forest_tileset.png

------------------------------------------------------------------------

# Visual Consistency Rules

To maintain a unified art style:

-   Use simple shapes
-   Avoid heavy texture noise
-   Keep colors vibrant but readable
-   Maintain consistent lighting direction
-   Avoid overly detailed surfaces

The target style combines:

-   Nintendo platformer readability
-   N64‑era simplicity
-   modern lighting and color

------------------------------------------------------------------------

# Additional Textures Needed

The following textures will likely be required later:

### Platform Corners

    left corner
    right corner
    center tile

### Slopes

    gentle slope
    steep slope

### Hazards

    spikes
    acid pools
    laser emitters

### Interactive Objects

    switches
    buttons
    terminals
    doors

### Collectibles

    coins
    mutation crystals
    energy orbs

------------------------------------------------------------------------

# Godot Import Workflow

1.  Import the texture atlas.
2.  Create a TileSet resource.
3.  Define tile regions.
4.  Assign collision shapes where necessary.
5.  Paint levels using the TileMap node.

------------------------------------------------------------------------

# Future Texture Sheets

Planned additional assets:

-   Enemy texture atlas
-   Attack effect textures
-   Mutation effect textures
-   UI icons
-   Animated environment tiles

------------------------------------------------------------------------

# Summary

These texture sets provide the foundation for building levels in:

-   Lab environments
-   Cave systems
-   Forest regions

By combining these tiles with enemies, hazards, and collectibles, you
can construct the full gameplay environments for Blobert's platformer
adventure.
