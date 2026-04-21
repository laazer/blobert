"""
Core constants, enums, and canonical enemy slug sequences for CLI and generation.

Merged from former ``constants`` + ``enemy_slug_registry`` (MAINT-ETRP). Slug tuples and
``ANIMATED_ENEMY_LABELS`` MUST stay ordered before ``EnemyTypes`` methods that reference them.
"""

from __future__ import annotations

# --- Registry (was enemy_slug_registry): must not create import cycles with other utils ---

ANIMATED_SLUGS: tuple[str, ...] = (
    "spider",
    "slug",
    "imp",
    "spitter",
    "claw_crawler",
    "carapace_husk",
)

ANIMATED_ENEMY_LABELS: dict[str, str] = {
    "spider": "Spider",
    "slug": "Slug",
    "imp": "Imp",
    "spitter": "Spitter",
    "claw_crawler": "Claw crawler",
    "carapace_husk": "Carapace husk",
}

if set(ANIMATED_ENEMY_LABELS.keys()) != set(ANIMATED_SLUGS):
    raise RuntimeError("ANIMATED_ENEMY_LABELS keys must match ANIMATED_SLUGS exactly")


def animated_enemies_for_api() -> list[dict[str, str]]:
    """[{slug, label}, ...] in ANIMATED_SLUGS order for HTTP clients."""
    return [{"slug": s, "label": ANIMATED_ENEMY_LABELS[s]} for s in ANIMATED_SLUGS]


STATIC_SLUGS: tuple[str, ...] = (
    "glue_drone",
    "melt_worm",
    "frost_jelly",
    "stone_burrower",
    "ferro_drone",
)


class EnemyTypes:
    """Enemy type constants"""

    SPIDER = "spider"
    SLUG = "slug"
    IMP = "imp"

    SPITTER = "spitter"
    CLAW_CRAWLER = "claw_crawler"
    CARAPACE_HUSK = "carapace_husk"

    GLUE_DRONE = "glue_drone"
    MELT_WORM = "melt_worm"
    FROST_JELLY = "frost_jelly"
    STONE_BURROWER = "stone_burrower"
    FERRO_DRONE = "ferro_drone"

    @classmethod
    def get_animated(cls) -> list[str]:
        return list(ANIMATED_SLUGS)

    @classmethod
    def get_static(cls) -> list[str]:
        return list(STATIC_SLUGS)

    @classmethod
    def get_all(cls) -> list[str]:
        return cls.get_animated() + cls.get_static()


class AnimationTypes:
    """Animation sequence constants"""

    IDLE = "idle"
    MOVE = "move"
    ATTACK = "attack"
    DAMAGE = "damage"
    DEATH = "death"

    SPAWN = "spawn"
    SPECIAL_ATTACK = "special_attack"
    DAMAGE_HEAVY = "damage_heavy"
    DAMAGE_FIRE = "damage_fire"
    DAMAGE_ICE = "damage_ice"
    STUNNED = "stunned"
    CELEBRATE = "celebrate"
    TAUNT = "taunt"

    @classmethod
    def get_core(cls) -> list[str]:
        return [cls.IDLE, cls.MOVE, cls.ATTACK, cls.DAMAGE, cls.DEATH]

    @classmethod
    def get_extended(cls) -> list[str]:
        return [
            cls.SPAWN,
            cls.SPECIAL_ATTACK,
            cls.DAMAGE_HEAVY,
            cls.DAMAGE_FIRE,
            cls.DAMAGE_ICE,
            cls.STUNNED,
            cls.CELEBRATE,
            cls.TAUNT,
        ]

    @classmethod
    def get_all(cls) -> list[str]:
        return cls.get_core() + cls.get_extended()

    @classmethod
    def get_damage_types(cls) -> list[str]:
        return [cls.DAMAGE, cls.DAMAGE_HEAVY, cls.DAMAGE_FIRE, cls.DAMAGE_ICE]

    _EXPORT_NAME_MAP: dict[str, str] = {
        "idle": "Idle",
        "move": "Walk",
        "attack": "Attack",
        "damage": "Hit",
        "death": "Death",
        "spawn": "Spawn",
        "special_attack": "SpecialAttack",
        "damage_heavy": "DamageHeavy",
        "damage_fire": "DamageFire",
        "damage_ice": "DamageIce",
        "stunned": "Stunned",
        "celebrate": "Celebrate",
        "taunt": "Taunt",
    }

    @classmethod
    def get_export_name(cls, internal_name: str) -> str:
        if internal_name in cls._EXPORT_NAME_MAP:
            return cls._EXPORT_NAME_MAP[internal_name]
        return "".join(word.title() for word in internal_name.split("_"))


try:
    from body_families.bones import BoneNames
    from body_families.ids import EnemyBodyTypes
except ImportError:
    from src.body_families import bones as _bones_mod
    from src.body_families import ids as _ids_mod

    BoneNames = _bones_mod.BoneNames
    EnemyBodyTypes = _ids_mod.EnemyBodyTypes


class AnimationConfig:
    """Animation timing configuration (frames at 24fps)"""

    LENGTHS = {
        AnimationTypes.IDLE: 48,
        AnimationTypes.MOVE: 24,
        AnimationTypes.ATTACK: 36,
        AnimationTypes.DAMAGE: 12,
        AnimationTypes.DEATH: 72,
        AnimationTypes.SPAWN: 48,
        AnimationTypes.SPECIAL_ATTACK: 60,
        AnimationTypes.DAMAGE_HEAVY: 24,
        AnimationTypes.DAMAGE_FIRE: 18,
        AnimationTypes.DAMAGE_ICE: 30,
        AnimationTypes.STUNNED: 60,
        AnimationTypes.CELEBRATE: 36,
        AnimationTypes.TAUNT: 24,
    }

    FPS = 24

    @classmethod
    def get_length(cls, animation_type: str) -> int:
        return cls.LENGTHS.get(animation_type, 24)

    @classmethod
    def get_duration_seconds(cls, animation_type: str) -> float:
        return cls.get_length(animation_type) / cls.FPS


class PlayerAnimationTypes:
    """Animation constants for the player character"""

    IDLE = "idle"
    MOVE = "move"
    JUMP = "jump"
    LAND = "land"
    ATTACK = "attack"
    DAMAGE = "damage"
    DEATH = "death"
    CELEBRATE = "celebrate"

    @classmethod
    def get_all(cls) -> list[str]:
        return [
            cls.IDLE,
            cls.MOVE,
            cls.JUMP,
            cls.LAND,
            cls.ATTACK,
            cls.DAMAGE,
            cls.DEATH,
            cls.CELEBRATE,
        ]

    @classmethod
    def get_looping(cls) -> list[str]:
        return [cls.IDLE, cls.MOVE]

    @classmethod
    def get_non_looping(cls) -> list[str]:
        return [cls.JUMP, cls.LAND, cls.ATTACK, cls.DAMAGE, cls.DEATH, cls.CELEBRATE]


class PlayerAnimationConfig:
    """Frame lengths for player animations at 24 fps"""

    FPS = 24
    LENGTHS = {
        PlayerAnimationTypes.IDLE: 48,
        PlayerAnimationTypes.MOVE: 24,
        PlayerAnimationTypes.JUMP: 20,
        PlayerAnimationTypes.LAND: 16,
        PlayerAnimationTypes.ATTACK: 30,
        PlayerAnimationTypes.DAMAGE: 12,
        PlayerAnimationTypes.DEATH: 60,
        PlayerAnimationTypes.CELEBRATE: 36,
    }

    @classmethod
    def get_length(cls, animation_type: str) -> int:
        return cls.LENGTHS.get(animation_type, 24)

    @classmethod
    def get_duration_seconds(cls, animation_type: str) -> float:
        return cls.get_length(animation_type) / cls.FPS


class PlayerBoneNames:
    """Bone names for the player slime armature"""

    ROOT = "root"
    BODY = "body"
    EYE_LEFT = "eye_l"
    EYE_RIGHT = "eye_r"
    ARM_LEFT = "arm_l"
    ARM_RIGHT = "arm_r"

    @classmethod
    def get_all(cls) -> list[str]:
        return [cls.ROOT, cls.BODY, cls.EYE_LEFT, cls.EYE_RIGHT, cls.ARM_LEFT, cls.ARM_RIGHT]

    @classmethod
    def get_eyes(cls) -> list[str]:
        return [cls.EYE_LEFT, cls.EYE_RIGHT]

    @classmethod
    def get_arms(cls) -> list[str]:
        return [cls.ARM_LEFT, cls.ARM_RIGHT]


class PlayerExportConfig:
    """Export directory and naming for the player character"""

    PLAYER_DIR = "player_exports"
    FILENAME_PATTERN = "player_slime_{color}_{variant:02d}"


class LevelObjectTypes:
    """Level object type constants"""

    FLAT_PLATFORM = "flat_platform"
    MOVING_PLATFORM = "moving_platform"
    CRUMBLING_PLATFORM = "crumbling_platform"

    SOLID_WALL = "solid_wall"
    CRENELLATED_WALL = "crenellated_wall"

    SPIKE_TRAP = "spike_trap"
    FIRE_TRAP = "fire_trap"

    CHECKPOINT = "checkpoint"

    @classmethod
    def get_all(cls) -> list[str]:
        return (
            cls.get_platforms()
            + cls.get_walls()
            + cls.get_traps()
            + cls.get_checkpoints()
        )

    @classmethod
    def get_platforms(cls) -> list[str]:
        return [cls.FLAT_PLATFORM, cls.MOVING_PLATFORM, cls.CRUMBLING_PLATFORM]

    @classmethod
    def get_walls(cls) -> list[str]:
        return [cls.SOLID_WALL, cls.CRENELLATED_WALL]

    @classmethod
    def get_traps(cls) -> list[str]:
        return [cls.SPIKE_TRAP, cls.FIRE_TRAP]

    @classmethod
    def get_checkpoints(cls) -> list[str]:
        return [cls.CHECKPOINT]


class LevelExportConfig:
    """Export directory and file configuration for level objects"""

    LEVEL_DIR = "level_exports"
    OBJECT_DATA_SUFFIX = ".object.json"
    OBJECT_FILENAME_PATTERN = "{object_type}_{variant:02d}"


class ExportConfig:
    """Export directory and file configuration"""

    STATIC_DIR = "exports"
    ANIMATED_DIR = "animated_exports"
    FORMAT = "GLB"

    # File naming patterns (animated stems are built in utils.export.animated_export_stem)
    STATIC_PATTERN = "{enemy_type}_{variant:02d}.{format}"
    ANIMATED_PATTERN = "{enemy_type}_animated_{variant:02d}.{format}"
