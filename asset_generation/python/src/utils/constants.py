"""
Core constants for the enemy generation system
"""

from enum import Enum
from typing import Dict, List


class EnemyTypes:
    """Enemy type constants"""
    # Animated enemies
    ADHESION_BUG = "adhesion_bug"
    TAR_SLUG = "tar_slug"  
    EMBER_IMP = "ember_imp"
    
    # Animated enemies (extended)
    ACID_SPITTER = "acid_spitter"
    CLAW_CRAWLER = "claw_crawler"
    CARAPACE_HUSK = "carapace_husk"

    # Static enemies (future expansion)
    GLUE_DRONE = "glue_drone"
    MELT_WORM = "melt_worm"
    FROST_JELLY = "frost_jelly"
    STONE_BURROWER = "stone_burrower"
    FERRO_DRONE = "ferro_drone"

    @classmethod
    def get_animated(cls) -> List[str]:
        """Get list of animated enemy types"""
        return [cls.ADHESION_BUG, cls.TAR_SLUG, cls.EMBER_IMP, cls.ACID_SPITTER, cls.CLAW_CRAWLER, cls.CARAPACE_HUSK]

    @classmethod
    def get_static(cls) -> List[str]:
        """Get list of static-only enemy types (no animation support)"""
        return [
            cls.GLUE_DRONE, cls.MELT_WORM,
            cls.FROST_JELLY, cls.STONE_BURROWER, cls.FERRO_DRONE
        ]

    @classmethod
    def get_all(cls) -> List[str]:
        """Get all enemy types (animated + static-only)"""
        return cls.get_animated() + cls.get_static()


class AnimationTypes:
    """Animation sequence constants"""
    # Core animations (always included)
    IDLE = "idle"
    MOVE = "move"
    ATTACK = "attack"
    DAMAGE = "damage"
    DEATH = "death"
    
    # Extended animations
    SPAWN = "spawn"
    SPECIAL_ATTACK = "special_attack"
    DAMAGE_HEAVY = "damage_heavy"
    DAMAGE_FIRE = "damage_fire"
    DAMAGE_ICE = "damage_ice"
    STUNNED = "stunned"
    CELEBRATE = "celebrate"
    TAUNT = "taunt"
    
    @classmethod
    def get_core(cls) -> List[str]:
        """Get core animation types that all enemies have"""
        return [cls.IDLE, cls.MOVE, cls.ATTACK, cls.DAMAGE, cls.DEATH]
    
    @classmethod
    def get_extended(cls) -> List[str]:
        """Get extended animation types for variety"""
        return [cls.SPAWN, cls.SPECIAL_ATTACK, cls.DAMAGE_HEAVY, 
                cls.DAMAGE_FIRE, cls.DAMAGE_ICE, cls.STUNNED, 
                cls.CELEBRATE, cls.TAUNT]
    
    @classmethod
    def get_all(cls) -> List[str]:
        """Get all animation types in order"""
        return cls.get_core() + cls.get_extended()
    
    @classmethod
    def get_damage_types(cls) -> List[str]:
        """Get all damage animation variants"""
        return [cls.DAMAGE, cls.DAMAGE_HEAVY, cls.DAMAGE_FIRE, cls.DAMAGE_ICE]


class EnemyBodyTypes:
    """Enemy body type classifications for animation"""
    BLOB = "blob"
    SLIME = "slime"  # Same as blob
    QUADRUPED = "quadruped"
    HUMANOID = "humanoid"


class BoneNames:
    """Bone naming constants for armatures"""
    # Universal bones
    ROOT = "root"
    SPINE = "spine"
    HEAD = "head"
    BODY = "body"
    
    # Humanoid bones
    ARM_LEFT = "arm_l"
    ARM_RIGHT = "arm_r"
    LEG_LEFT = "leg_l"
    LEG_RIGHT = "leg_r"
    
    # Quadruped bones (6-legged)
    LEG_FRONT_LEFT = "leg_fl"
    LEG_FRONT_RIGHT = "leg_fr"
    LEG_MIDDLE_LEFT = "leg_ml"
    LEG_MIDDLE_RIGHT = "leg_mr"
    LEG_BACK_LEFT = "leg_bl"
    LEG_BACK_RIGHT = "leg_br"
    
    @classmethod
    def get_all_legs(cls) -> List[str]:
        """Get all leg bone names"""
        return [
            cls.LEG_FRONT_LEFT, cls.LEG_FRONT_RIGHT,
            cls.LEG_MIDDLE_LEFT, cls.LEG_MIDDLE_RIGHT,
            cls.LEG_BACK_LEFT, cls.LEG_BACK_RIGHT,
            cls.LEG_LEFT, cls.LEG_RIGHT
        ]
    
    @classmethod
    def get_quadruped_legs(cls) -> List[str]:
        """Get quadruped (6-legged) bone names"""
        return [
            cls.LEG_FRONT_LEFT, cls.LEG_FRONT_RIGHT,
            cls.LEG_MIDDLE_LEFT, cls.LEG_MIDDLE_RIGHT,
            cls.LEG_BACK_LEFT, cls.LEG_BACK_RIGHT
        ]
    
    @classmethod
    def get_humanoid_arms(cls) -> List[str]:
        """Get humanoid arm bone names"""
        return [cls.ARM_LEFT, cls.ARM_RIGHT]
    
    @classmethod
    def get_humanoid_legs(cls) -> List[str]:
        """Get humanoid leg bone names"""
        return [cls.LEG_LEFT, cls.LEG_RIGHT]


class AnimationConfig:
    """Animation timing configuration (frames at 24fps)"""
    LENGTHS = {
        # Core animations
        AnimationTypes.IDLE: 48,           # 2.0s - Breathing, waiting
        AnimationTypes.MOVE: 24,           # 1.0s - Locomotion loop  
        AnimationTypes.ATTACK: 36,         # 1.5s - Basic attack sequence
        AnimationTypes.DAMAGE: 12,         # 0.5s - Quick damage reaction
        AnimationTypes.DEATH: 72,          # 3.0s - Dramatic death sequence
        
        # Extended animations
        AnimationTypes.SPAWN: 48,          # 2.0s - Materialize/emerge
        AnimationTypes.SPECIAL_ATTACK: 60, # 2.5s - Powerful signature attack
        AnimationTypes.DAMAGE_HEAVY: 24,   # 1.0s - Major damage reaction
        AnimationTypes.DAMAGE_FIRE: 18,    # 0.75s - Fire damage + burning
        AnimationTypes.DAMAGE_ICE: 30,     # 1.25s - Ice damage + freezing
        AnimationTypes.STUNNED: 60,        # 2.5s - Dazed/incapacitated
        AnimationTypes.CELEBRATE: 36,      # 1.5s - Victory pose
        AnimationTypes.TAUNT: 24,          # 1.0s - Provocative gesture
    }
    
    # Frame rates
    FPS = 24
    
    @classmethod
    def get_length(cls, animation_type: str) -> int:
        """Get frame length for an animation type"""
        return cls.LENGTHS.get(animation_type, 24)
    
    @classmethod  
    def get_duration_seconds(cls, animation_type: str) -> float:
        """Get duration in seconds for an animation type"""
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
    def get_all(cls) -> List[str]:
        return [
            cls.IDLE, cls.MOVE, cls.JUMP, cls.LAND,
            cls.ATTACK, cls.DAMAGE, cls.DEATH, cls.CELEBRATE,
        ]

    @classmethod
    def get_looping(cls) -> List[str]:
        """Animations that loop cleanly."""
        return [cls.IDLE, cls.MOVE]

    @classmethod
    def get_non_looping(cls) -> List[str]:
        return [cls.JUMP, cls.LAND, cls.ATTACK, cls.DAMAGE, cls.DEATH, cls.CELEBRATE]


class PlayerAnimationConfig:
    """Frame lengths for player animations at 24 fps"""
    FPS = 24
    LENGTHS = {
        PlayerAnimationTypes.IDLE:      48,   # 2.0s — gentle bob + blink
        PlayerAnimationTypes.MOVE:      24,   # 1.0s — two bouncing hops
        PlayerAnimationTypes.JUMP:      20,   # 0.83s — charge-up + launch
        PlayerAnimationTypes.LAND:      16,   # 0.67s — squash + settle
        PlayerAnimationTypes.ATTACK:    30,   # 1.25s — lean back → spit
        PlayerAnimationTypes.DAMAGE:    12,   # 0.5s  — shake/wobble
        PlayerAnimationTypes.DEATH:     60,   # 2.5s  — deflate into puddle
        PlayerAnimationTypes.CELEBRATE: 36,   # 1.5s  — happy bouncing
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
    def get_all(cls) -> List[str]:
        return [cls.ROOT, cls.BODY, cls.EYE_LEFT, cls.EYE_RIGHT, cls.ARM_LEFT, cls.ARM_RIGHT]

    @classmethod
    def get_eyes(cls) -> List[str]:
        return [cls.EYE_LEFT, cls.EYE_RIGHT]

    @classmethod
    def get_arms(cls) -> List[str]:
        return [cls.ARM_LEFT, cls.ARM_RIGHT]


class PlayerExportConfig:
    """Export directory and naming for the player character"""
    PLAYER_DIR = "player_exports"
    FILENAME_PATTERN = "player_slime_{color}_{variant:02d}"


class LevelObjectTypes:
    """Level object type constants"""
    # Platforms
    FLAT_PLATFORM = "flat_platform"
    MOVING_PLATFORM = "moving_platform"
    CRUMBLING_PLATFORM = "crumbling_platform"

    # Walls
    SOLID_WALL = "solid_wall"
    CRENELLATED_WALL = "crenellated_wall"

    # Traps
    SPIKE_TRAP = "spike_trap"
    FIRE_TRAP = "fire_trap"

    # Checkpoints
    CHECKPOINT = "checkpoint"

    @classmethod
    def get_all(cls) -> List[str]:
        return (
            cls.get_platforms()
            + cls.get_walls()
            + cls.get_traps()
            + cls.get_checkpoints()
        )

    @classmethod
    def get_platforms(cls) -> List[str]:
        return [cls.FLAT_PLATFORM, cls.MOVING_PLATFORM, cls.CRUMBLING_PLATFORM]

    @classmethod
    def get_walls(cls) -> List[str]:
        return [cls.SOLID_WALL, cls.CRENELLATED_WALL]

    @classmethod
    def get_traps(cls) -> List[str]:
        return [cls.SPIKE_TRAP, cls.FIRE_TRAP]

    @classmethod
    def get_checkpoints(cls) -> List[str]:
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
    
    # File naming patterns
    STATIC_PATTERN = "{enemy_type}_{variant:02d}.{format}"
    ANIMATED_PATTERN = "{enemy_type}_animated_{variant:02d}.{format}"