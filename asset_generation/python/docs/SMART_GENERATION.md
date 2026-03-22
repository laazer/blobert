# 🧠 Smart Generation Guide

> AI-assisted enemy creation from natural language descriptions

## Overview

The Smart Generation system allows you to create game-ready enemies by simply describing them in natural language. The AI analyzes your description and automatically generates appropriate enemy designs with balanced stats, animations, and materials.

## Basic Usage

### Quick Start
```bash
# Generate from description
python main.py smart --description "a large fire spider with powerful attacks"

# Specify difficulty
python main.py smart --description "small ice blob that moves fast" --difficulty hard

# Export game-ready stats  
python main.py smart --description "armored metal warrior" --export-stats godot
```

### Available Commands
| Command | Purpose | Example |
|---------|---------|---------|
| `smart` | Generate from description | `python main.py smart --description "text"` |
| `stats` | Export stats for existing enemy | `python main.py stats adhesion_bug --export-stats unity` |
| `list` | View all available enemies | `python main.py list` |

## Description Language

### Body Type Keywords
The AI recognizes these keywords to determine enemy body type:

**Blob Enemies**: `blob`, `slime`, `ooze`, `jelly`
- Generates soft, squishy creatures with stretchy animations
- Examples: "toxic green blob", "ice jelly creature"

**Quadruped Enemies**: `spider`, `bug`, `insect`, `crawler`, `crab`  
- Creates multi-legged creatures with scuttling movement
- Examples: "fire spider", "armored crawler bug"

**Humanoid Enemies**: `humanoid`, `warrior`, `soldier`, `imp`, `golem`
- Builds bipedal creatures with walk/run animations
- Examples: "ice warrior", "flame imp", "stone golem"

### Size Modifiers
Control enemy scale with size keywords:

- **Large**: `big`, `large`, `huge`, `giant` → 1.2-1.8x scale
- **Normal**: Default size when no keywords detected
- **Small**: `small`, `tiny`, `little` → 0.6-0.9x scale

### Element Keywords
Influence materials and visual effects:

- **Fire**: `fire`, `flame`, `ember`, `lava` → Orange emissive materials
- **Ice**: `ice`, `frost`, `frozen`, `crystal` → Blue translucent materials  
- **Metal**: `metal`, `steel`, `iron`, `armor` → Metallic chrome/rust materials
- **Toxic**: `toxic`, `poison`, `acid` → Green glowing materials
- **Stone**: `stone`, `rock`, `earth` → Gray rocky textures

## Examples

### Fire Enemies
```bash
# Large fire spider with aggressive stats
python main.py smart --description "a large fire spider with powerful attacks" --difficulty normal

# Small ember imp - fast and agile
python main.py smart --description "small flame imp that dances around enemies" --difficulty easy
```

### Ice Enemies  
```bash
# Ice blob - defensive creature
python main.py smart --description "ice blob that moves slowly but has high armor" --difficulty hard

# Frost warrior - balanced fighter
python main.py smart --description "frozen humanoid warrior with ice weapons" --difficulty nightmare
```

### Metal Enemies
```bash
# Armored crawler
python main.py smart --description "metal spider with steel armor plating" --difficulty normal

# Battle drone
python main.py smart --description "flying metal drone with laser weapons" --difficulty hard
```

## Difficulty Scaling

| Difficulty | Health | Damage | Speed | Armor | Special Abilities |
|------------|--------|--------|-------|-------|-------------------|
| **Easy** | 40-80 | 15-25 | 1.0-1.5 | 0-5 | 1-2 abilities |
| **Normal** | 60-120 | 20-35 | 1.2-2.0 | 3-10 | 2-3 abilities |
| **Hard** | 80-160 | 25-45 | 1.5-2.5 | 5-15 | 3-4 abilities |
| **Nightmare** | 120-250 | 35-60 | 2.0-3.0 | 10-25 | 4-5 abilities |

### Size Scaling
- **Large enemies**: +30% health, +20% damage, -15% speed
- **Small enemies**: -40% health, -25% damage, +50% speed

## Animation Selection

The AI automatically selects appropriate animation sets:

### Core Animations (Always Included)
- `idle` - Breathing and waiting
- `move` - Locomotion loop  
- `attack` - Basic attack sequence
- `damage` - Quick damage reaction
- `death` - Dramatic death sequence

### Extended Animations (Smart Generation)
- `spawn` - Materialize from ground
- `special_attack` - Signature powerful attack
- `damage_heavy` - Major damage with knockback
- `damage_fire` - Fire damage with burning
- `damage_ice` - Ice damage with freezing
- `stunned` - Dazed state
- `celebrate` - Victory pose
- `taunt` - Provocative gesture

## Game Engine Export

### Godot (GDScript)
```bash
python main.py smart --description "fire spider" --export-stats godot
```

Creates `Fire_Spider_normal_stats.godot`:
```gdscript
# Fire_Spider_normal Enemy Stats
extends Resource
class_name Fire_Spider_normalStats

export var health: int = 85
export var damage: int = 28
export var speed: float = 1.80
export var armor: int = 6
export var special_abilities: PoolStringArray = ['Fire Aura', 'Web Attack']
export var weaknesses: PoolStringArray = ['Vulnerable to Water', 'Slow Movement']
```

### Unity (C#)
```bash
python main.py smart --description "ice warrior" --export-stats unity
```

Creates `Ice_Warrior_normal_stats.unity`:
```csharp
[System.Serializable]
public class Ice_Warrior_normalStats
{
    public int health = 95;
    public int damage = 32;
    public float speed = 1.60f;
    public int armor = 12;
    public string[] specialAbilities = {"Frost Aura", "Ice Shield", "Freezing Strike"};
    public string[] weaknesses = {"Vulnerable to Fire", "Slow Speed"};
}
```

### JSON Export
```bash  
python main.py smart --description "metal drone" --export-stats json
```

Creates `Metal_Drone_normal_stats.json`:
```json
{
  "name": "Metal_Drone_normal",
  "health": 75,
  "damage": 30,
  "speed": 2.1,
  "armor": 8,
  "threat_level": "Medium (Normal)",
  "special_abilities": ["Hover Flight", "Laser Beam", "Shield Boost"],
  "weaknesses": ["EMP Vulnerability", "Lightning Damage"]
}
```

## Advanced Usage

### Reproducible Generation
Use seeds for consistent results:
```bash
python main.py smart --description "fire spider" --seed 12345
```

### Batch Stats Export
Generate stats for existing enemies:
```bash
# Export all difficulties
python main.py stats adhesion_bug --export-stats godot --difficulty easy
python main.py stats adhesion_bug --export-stats godot --difficulty normal  
python main.py stats adhesion_bug --export-stats godot --difficulty hard
python main.py stats adhesion_bug --export-stats godot --difficulty nightmare
```

### Complex Descriptions
The AI handles complex descriptions:
```bash
python main.py smart --description "a massive armored fire spider with steel plating that shoots lava webs and has glowing red eyes"
```

## Tips for Best Results

### ✅ Good Descriptions
- **Specific**: "fire spider with lava attacks" vs "spider"  
- **Clear body type**: Include "spider", "blob", "humanoid", etc.
- **Element mentioned**: "fire", "ice", "metal" for proper materials
- **Size indicators**: "large", "small", "tiny", "huge"

### ❌ Avoid These
- **Vague descriptions**: "scary monster" 
- **Conflicting elements**: "fire ice creature"
- **Non-game terms**: "cute friendly pet"

### 🎯 Perfect Examples
```bash
"large metal spider with armor plating and laser weapons"
"small toxic blob that leaves poison trails"  
"humanoid ice warrior with frozen sword and shield"
"tiny fire imp that teleports and throws fireballs"
"massive stone golem with earthquake attacks"
```

## Integration Workflow

1. **Generate Enemy**: Use smart generation to create base enemy
2. **Review Stats**: Check generated stats file for balance
3. **Import Model**: Load .glb file into your game engine
4. **Apply Stats**: Use exported stats script in your game
5. **Test Animations**: Verify all 13 animations work correctly
6. **Fine-tune**: Adjust stats as needed for your game balance

---

🎮 **Ready to create intelligent enemies?** Start with `python main.py smart --description "your enemy idea"`!