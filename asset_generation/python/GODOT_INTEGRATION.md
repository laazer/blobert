# Godot Integration Guide

## Quick Start

### 1. Generate enemies

```bash
python main.py animated adhesion_bug 1   # 1 adhesion bug
python main.py animated all              # one of each type
```

Output in `animated_exports/`:
- `adhesion_bug_animated_00.glb`
- `adhesion_bug_animated_00.attacks.json`

### 2. Import into Godot

Drag GLB files from `animated_exports/` into Godot's FileSystem dock. Godot automatically creates:

```
EnemyName (Node3D)
├── MeshInstance3D
├── Skeleton3D
└── AnimationPlayer    ← contains all 13 animations
```

### 3. Play animations

```gdscript
$AnimationPlayer.play("idle")
$AnimationPlayer.play("move")
$AnimationPlayer.play("attack")
```

---

## Animation Reference

All animations are at **24 fps**. Each starts and ends at rest pose for clean looping.

### Core animations (always included)

| Name | Frames | Duration | Loop |
|------|--------|----------|------|
| `idle` | 48 | 2.0s | ✅ |
| `move` | 24 | 1.0s | ✅ |
| `attack` | 36 | 1.5s | ❌ |
| `damage` | 12 | 0.5s | ❌ |
| `death` | 72 | 3.0s | ❌ |

### Extended animations (also included)

| Name | Frames | Duration | Loop |
|------|--------|----------|------|
| `spawn` | 48 | 2.0s | ❌ |
| `special_attack` | 60 | 2.5s | ❌ |
| `damage_heavy` | 24 | 1.0s | ❌ |
| `damage_fire` | 18 | 0.75s | ❌ |
| `damage_ice` | 30 | 1.25s | ❌ |
| `stunned` | 60 | 2.5s | ✅ |
| `celebrate` | 36 | 1.5s | ❌ |
| `taunt` | 24 | 1.0s | ❌ |

### Attack style by body type

| Enemy | `attack` | `special_attack` |
|-------|----------|-----------------|
| `adhesion_bug` (quadruped) | Pounce — all 6 legs coil then spring | Rearing slash — front legs slam down |
| `tar_slug` (blob) | Expansion slam — body inflates outward | Massive AoE expansion — lifts then crashes |
| `ember_imp` (humanoid) | Fire punch — spine twists, guard arm raises | Overhead two-handed slam |

---

## Attack Profile JSON

Every GLB has a companion `.attacks.json` file with combat data:

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
    },
    {
      "name": "acid_bite",
      "animation_name": "special_attack",
      "attack_type": "acid",
      "range": 1.5,
      "hit_frame": 40,
      "cooldown_seconds": 5.0,
      "knockback_force": 2.0,
      "is_area_of_effect": false,
      "aoe_radius": 0.0
    }
  ]
}
```

Use `hit_frame` to activate your hitbox at exactly the right frame instead of hardcoding a timer:

```gdscript
func perform_attack(attack_data: Dictionary) -> void:
    var anim_name = attack_data["animation_name"]
    var hit_frame = attack_data["hit_frame"]
    var fps = 24.0
    var hit_time = hit_frame / fps

    animation_player.play(anim_name)
    await get_tree().create_timer(hit_time).timeout

    if _target_in_range(attack_data["range"]):
        _apply_hit(attack_data)
```

---

## GDScript Examples

### Basic enemy controller

```gdscript
extends CharacterBody3D

@onready var animation_player := $AnimationPlayer

enum State { IDLE, MOVING, ATTACKING, DAMAGED, DEAD }
var state := State.IDLE

func _ready() -> void:
    animation_player.play("idle")
    animation_player.animation_finished.connect(_on_animation_finished)

func change_state(new_state: State) -> void:
    state = new_state
    match state:
        State.IDLE:      animation_player.play("idle")
        State.MOVING:    animation_player.play("move")
        State.ATTACKING: animation_player.play("attack")
        State.DAMAGED:   animation_player.play("damage")
        State.DEAD:      animation_player.play("death")

func _on_animation_finished(anim_name: String) -> void:
    match anim_name:
        "attack", "damage":
            change_state(State.IDLE)
        "death":
            set_collision_layer_value(1, false)
```

### Loading attack data from JSON

```gdscript
var attacks: Array = []

func _ready() -> void:
    _load_attack_profile()
    animation_player.play("idle")

func _load_attack_profile() -> void:
    # Assumes GLB and JSON share the same base name
    var json_path := "res://enemies/adhesion_bug_animated_00.attacks.json"
    var file := FileAccess.open(json_path, FileAccess.READ)
    if file:
        var data: Dictionary = JSON.parse_string(file.get_as_text())
        attacks = data.get("attacks", [])

func get_attack(name: String) -> Dictionary:
    for atk in attacks:
        if atk["name"] == name:
            return atk
    return {}
```

### Hit-frame-accurate attack

```gdscript
func perform_attack(attack_name: String) -> void:
    var attack := get_attack(attack_name)
    if attack.is_empty():
        return

    animation_player.play(attack["animation_name"])

    # Activate hitbox exactly when the attack lands
    var hit_time := attack["hit_frame"] / 24.0
    await get_tree().create_timer(hit_time).timeout

    if _target_in_range(attack["range"]):
        var is_aoe: bool = attack["is_area_of_effect"]
        if is_aoe:
            _apply_area_damage(attack["aoe_radius"], attack["knockback_force"])
        else:
            target.take_damage(attack["knockback_force"])
```

### State machine with special attack

```gdscript
extends CharacterBody3D

@onready var animation_player := $AnimationPlayer
@onready var detection_area := $DetectionArea

var player: Node3D
var health := 100
var last_attack_time := 0.0
var attacks: Array = []

enum State { PATROL, CHASE, ATTACK, SPECIAL, DAMAGED, DEAD }
var state := State.PATROL

func _ready() -> void:
    _load_attack_profile()
    animation_player.play("idle")
    animation_player.animation_finished.connect(_on_animation_finished)
    detection_area.body_entered.connect(_on_player_detected)
    detection_area.body_exited.connect(_on_player_lost)

func _physics_process(delta: float) -> void:
    match state:
        State.PATROL:  _handle_patrol(delta)
        State.CHASE:   _handle_chase(delta)
        State.ATTACK:  _handle_attack()
        State.SPECIAL: pass  # wait for animation
        State.DAMAGED: pass
        State.DEAD:    pass

func _handle_chase(delta: float) -> void:
    animation_player.play("move")
    velocity = (player.global_position - global_position).normalized() * 3.0
    move_and_slide()

func _handle_attack() -> void:
    var now := Time.get_ticks_msec() / 1000.0
    var basic := get_attack("pounce")
    if now - last_attack_time > basic.get("cooldown_seconds", 2.0):
        last_attack_time = now
        # Use special attack every 3rd time
        var use_special := int(now) % 3 == 0
        perform_attack("acid_bite" if use_special else "pounce")
        state = State.SPECIAL if use_special else State.ATTACK

func _on_animation_finished(anim_name: String) -> void:
    match anim_name:
        "attack", "special_attack", "damage":
            state = State.CHASE if player else State.PATROL
        "death":
            set_collision_layer_value(1, false)

func take_damage(amount: int) -> void:
    health -= amount
    if health <= 0:
        state = State.DEAD
        animation_player.play("death")
    else:
        state = State.DAMAGED
        animation_player.play("damage")

func _on_player_detected(body: Node3D) -> void:
    if body.is_in_group("player"):
        player = body
        state = State.CHASE

func _on_player_lost(body: Node3D) -> void:
    if body == player:
        player = null
        state = State.PATROL

func _load_attack_profile() -> void:
    var json_path := "res://enemies/adhesion_bug_animated_00.attacks.json"
    var file := FileAccess.open(json_path, FileAccess.READ)
    if file:
        var data: Dictionary = JSON.parse_string(file.get_as_text())
        attacks = data.get("attacks", [])

func get_attack(name: String) -> Dictionary:
    for atk in attacks:
        if atk["name"] == name:
            return atk
    return {}
```

---

## Performance

### Disable animations when far away

```gdscript
func _process(_delta: float) -> void:
    if not player:
        return
    var dist := global_position.distance_to(player.global_position)
    if dist > 50.0:
        animation_player.pause()
    elif dist > 25.0:
        animation_player.speed_scale = 0.5
    else:
        animation_player.speed_scale = 1.0
        if not animation_player.is_playing():
            animation_player.play("idle")
```

### Cull off-screen enemies

```gdscript
func _ready() -> void:
    var vis := VisibleOnScreenNotifier3D.new()
    add_child(vis)
    vis.screen_exited.connect(func(): set_physics_process(false); animation_player.pause())
    vis.screen_entered.connect(func(): set_physics_process(true); animation_player.play())
```

---

## Troubleshooting

**Animations not playing** — Verify animation names match exactly (lowercase). Use `python main.py list` to confirm available names.

**Wrong frame rate** — All animations are authored at 24 fps. If your Godot project runs at a different rate the durations will be off; either adjust the project fps or recalculate hit times using `hit_frame / 24.0`.

**Large file sizes** — Animated GLBs are ~500KB–1MB. For background enemies consider switching to `--animation-set core` (5 animations only) to reduce size.

**Weird deformation** — Procedural armatures are low-poly by design. Expected behaviour; increase geometry subdivisions in the generator for smoother deformation.
