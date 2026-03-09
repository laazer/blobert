# Efficient Workflow for Creating Low-Poly 3D Enemy Models (Godot Friendly)

Goal: create many simple enemies quickly that run well in Godot.

Key principles:
- Low poly
- Reusable parts
- Consistent style
- Fast assembly
- Minimal materials

The best approach is **Blender + primitive kitbashing**.

---

# Core Idea: Build a Creature Parts Kit

Create a small reusable library of meshes you can assemble like Lego.

Parts library example:

BaseBlob  
BaseSphere  
BaseCapsule  
EyeNode  
Spike  
Claw  
Shell  
Tentacle  
Wing  
OrbCore  
Blade  

Keep each piece extremely simple.

Example triangle budgets:

Sphere: ~64  
Capsule: ~32  
Tentacle: ~50  
Claw: ~40  
Wing: ~30  

Once these exist, every enemy becomes a combination of them.

---

# Step 1 — Create the Parts in Blender

Make a single Blender file called:

enemy_parts.blend

Inside it, create the primitive components.

Example creation methods:

Sphere → body or core  
Capsule → legs, arms, antenna  
Cone → spikes, horns, burrow noses  
Cube → mechanical parts  
Cylinder → joints or mechanical limbs  

---

# Step 2 — Assemble Enemies Quickly

Each enemy should take about 1–2 minutes.

Example enemy builds:

Adhesion Bug
- Sphere body
- 6 capsule legs
- 2 eye nodes

Acid Spitter
- Blob base
- Large mouth sphere
- Acid sack sphere

Electric Node
- Sphere
- Orb core
- Antenna capsule

Carapace Husk
- Sphere body
- Half sphere shell
- 4 capsule legs

Blade Sentinel
- Blade mesh
- Orb core

Most enemies will only need **5–8 meshes**.

---

# Step 3 — Keep Materials Simple

Use a very small shared color palette.

Example palette:

Green slime  
Blue ice  
Orange fire  
Gray metal  
Purple corruption  
Brown earth  

Avoid textures whenever possible.

Godot handles simple materials very efficiently.

---

# Step 4 — Use Smooth Shading Instead of Extra Polygons

In Blender:

Right Click → Shade Smooth

Use edge creases if needed to preserve sharp edges.

This creates a clean look without increasing geometry.

---

# Step 5 — Minimal Animation

Most enemies only need 3–4 animations:

Idle  
Move  
Attack  
Death  

For slime creatures, a simple Y-scale bounce animation often works perfectly.

Example idle animation:

Scale Y = 1.0 → 1.05 → 1.0

---

# Step 6 — Export to Godot

Use the `.glb` format.

Export settings:

Apply Transform = true  
Apply Modifiers = true  
Include Animation = true  

Godot imports `.glb` files very cleanly.

---

# Performance Targets

Recommended triangle counts:

Enemy triangle budget: 300 – 1500 triangles

Examples:

Adhesion Bug: ~500  
Acid Spitter: ~400  
Carapace Husk: ~600  
Electric Node: ~300  
Blade Sentinel: ~350  
Tendril Beast: ~800  

Even dozens of enemies will run smoothly.

---

# Organizing Your Blender File

Use collections.

Example structure:

Enemies
  AdhesionBug
  AcidSpitter
  ElectricNode

Parts
  Tentacle
  Claw
  Eye
  Core
  Shell

You can build every enemy in one file.

---

# Speed Trick: Geometry Nodes (Optional)

Use Geometry Nodes to create variations automatically.

Examples:

Random spike placement  
Random tentacle length  
Random eye size  

This allows one enemy template to generate many variants.

---

# Example Quick Enemy Build

Stone Burrower:

1. Add sphere
2. Flatten slightly
3. Add cone nose
4. Add two eyes
5. Assign earth color

Done.

---

# Another Powerful Trick: Vertex Colors Instead of Textures

Advantages:

No texture memory  
Faster rendering  
Cleaner style  
Easy recoloring  

Many stylized indie games use this approach.

---

# Ideal Pipeline

Blender  
→ Build enemies with low-poly kitbash parts  
→ Assign vertex colors or simple materials  
→ Export as `.glb`  
→ Import into Godot  
→ Add simple animation

---

# Expected Production Speed

Once your parts kit exists:

You can realistically create **all ~49 enemies in a weekend**.

Each enemy becomes a quick assembly of primitive parts.