"""
Material constants and configuration
"""

from typing import Dict, List, Tuple


class MaterialColors:
    """Material color definitions (RGBA tuples)"""
    
    # Organic/Biological materials
    TOXIC_GREEN = (0.2, 0.8, 0.3, 1.0)
    SLIME_GREEN = (0.4, 0.9, 0.2, 0.8)  # Semi-transparent
    ORGANIC_BROWN = (0.6, 0.4, 0.2, 1.0)
    ROT_PURPLE = (0.5, 0.2, 0.8, 1.0)
    FLESH_PINK = (0.8, 0.4, 0.5, 1.0)
    BONE_WHITE = (0.9, 0.9, 0.8, 1.0)
    BLOOD_RED = (0.8, 0.1, 0.1, 1.0)
    TAR_BLACK = (0.1, 0.1, 0.1, 1.0)
    
    # Elemental materials
    FIRE_ORANGE = (1.0, 0.5, 0.1, 1.0)
    EMBER_RED = (1.0, 0.2, 0.0, 1.0)
    FROST_BLUE = (0.3, 0.6, 1.0, 0.9)  # Semi-transparent
    ICE_WHITE = (0.8, 0.9, 1.0, 0.7)   # Very translucent
    ACID_YELLOW = (0.9, 0.9, 0.2, 0.85)
    
    # Metallic materials
    METAL_GRAY = (0.5, 0.5, 0.6, 1.0)
    RUST_ORANGE = (0.8, 0.4, 0.2, 1.0)
    COPPER_GREEN = (0.3, 0.6, 0.4, 1.0)
    CHROME_SILVER = (0.8, 0.8, 0.9, 1.0)
    
    # Stone/Earth materials
    STONE_GRAY = (0.4, 0.4, 0.4, 1.0)
    DIRT_BROWN = (0.3, 0.2, 0.1, 1.0)
    CRYSTAL_PURPLE = (0.6, 0.3, 0.8, 0.8)
    
    @classmethod
    def get_all(cls) -> Dict[str, Tuple[float, float, float, float]]:
        """Get all material colors as a dictionary"""
        return {
            'toxic_green': cls.TOXIC_GREEN,
            'slime_green': cls.SLIME_GREEN,
            'organic_brown': cls.ORGANIC_BROWN,
            'rot_purple': cls.ROT_PURPLE,
            'flesh_pink': cls.FLESH_PINK,
            'bone_white': cls.BONE_WHITE,
            'blood_red': cls.BLOOD_RED,
            'tar_black': cls.TAR_BLACK,
            'fire_orange': cls.FIRE_ORANGE,
            'ember_red': cls.EMBER_RED,
            'frost_blue': cls.FROST_BLUE,
            'ice_white': cls.ICE_WHITE,
            'acid_yellow': cls.ACID_YELLOW,
            'metal_gray': cls.METAL_GRAY,
            'rust_orange': cls.RUST_ORANGE,
            'copper_green': cls.COPPER_GREEN,
            'chrome_silver': cls.CHROME_SILVER,
            'stone_gray': cls.STONE_GRAY,
            'dirt_brown': cls.DIRT_BROWN,
            'crystal_purple': cls.CRYSTAL_PURPLE,
        }


class MaterialNames:
    """Material name constants"""
    # Organic/Biological
    TOXIC_GREEN = "toxic_green"
    SLIME_GREEN = "slime_green"
    ORGANIC_BROWN = "organic_brown"
    ROT_PURPLE = "rot_purple"
    FLESH_PINK = "flesh_pink"
    BONE_WHITE = "bone_white"
    BLOOD_RED = "blood_red"
    TAR_BLACK = "tar_black"
    
    # Elemental
    FIRE_ORANGE = "fire_orange"
    EMBER_RED = "ember_red"
    FROST_BLUE = "frost_blue"
    ICE_WHITE = "ice_white"
    ACID_YELLOW = "acid_yellow"
    
    # Metallic
    METAL_GRAY = "metal_gray"
    RUST_ORANGE = "rust_orange"
    COPPER_GREEN = "copper_green"
    CHROME_SILVER = "chrome_silver"
    
    # Stone/Earth
    STONE_GRAY = "stone_gray"
    DIRT_BROWN = "dirt_brown"
    CRYSTAL_PURPLE = "crystal_purple"


class MaterialThemes:
    """Material theme assignments for enemies"""
    
    ENEMY_THEMES = {
        'adhesion_bug': [MaterialNames.TOXIC_GREEN, MaterialNames.ORGANIC_BROWN, MaterialNames.BONE_WHITE],
        'tar_slug': [MaterialNames.TAR_BLACK, MaterialNames.SLIME_GREEN, MaterialNames.DIRT_BROWN],
        'ember_imp': [MaterialNames.FIRE_ORANGE, MaterialNames.EMBER_RED, MaterialNames.BONE_WHITE],
        'glue_drone': [MaterialNames.METAL_GRAY, MaterialNames.CHROME_SILVER, MaterialNames.RUST_ORANGE],
        'acid_spitter': [MaterialNames.ACID_YELLOW, MaterialNames.TOXIC_GREEN, MaterialNames.SLIME_GREEN],
        'melt_worm': [MaterialNames.FLESH_PINK, MaterialNames.BLOOD_RED, MaterialNames.ORGANIC_BROWN],
        'claw_crawler': [MaterialNames.STONE_GRAY, MaterialNames.DIRT_BROWN, MaterialNames.BONE_WHITE],
        'frost_jelly': [MaterialNames.ICE_WHITE, MaterialNames.FROST_BLUE, MaterialNames.CRYSTAL_PURPLE],
        'stone_burrower': [MaterialNames.STONE_GRAY, MaterialNames.DIRT_BROWN, MaterialNames.RUST_ORANGE],
        'ferro_drone': [MaterialNames.CHROME_SILVER, MaterialNames.METAL_GRAY, MaterialNames.COPPER_GREEN],
        'carapace_husk': [MaterialNames.STONE_GRAY, MaterialNames.BONE_WHITE, MaterialNames.CHROME_SILVER],
    }
    
    @classmethod
    def get_theme(cls, enemy_type: str) -> List[str]:
        """Get material theme for an enemy type"""
        return cls.ENEMY_THEMES.get(enemy_type, [MaterialNames.ORGANIC_BROWN])
    
    @classmethod
    def has_theme(cls, enemy_type: str) -> bool:
        """Check if enemy type has a defined theme"""
        return enemy_type in cls.ENEMY_THEMES


class MaterialCategories:
    """Material categorization for different texture types"""
    
    ORGANIC = [
        MaterialNames.TOXIC_GREEN, MaterialNames.SLIME_GREEN, MaterialNames.ORGANIC_BROWN,
        MaterialNames.ROT_PURPLE, MaterialNames.FLESH_PINK, MaterialNames.BONE_WHITE,
        MaterialNames.BLOOD_RED, MaterialNames.TAR_BLACK
    ]
    
    ELEMENTAL = [
        MaterialNames.FIRE_ORANGE, MaterialNames.EMBER_RED, MaterialNames.FROST_BLUE,
        MaterialNames.ICE_WHITE, MaterialNames.ACID_YELLOW
    ]
    
    METALLIC = [
        MaterialNames.METAL_GRAY, MaterialNames.RUST_ORANGE, MaterialNames.COPPER_GREEN,
        MaterialNames.CHROME_SILVER
    ]

    ROCKY = [MaterialNames.STONE_GRAY, MaterialNames.DIRT_BROWN]

    STONE = [
        MaterialNames.STONE_GRAY, MaterialNames.DIRT_BROWN, MaterialNames.CRYSTAL_PURPLE
    ]
    
    # Materials that should use emissive shaders
    EMISSIVE = [MaterialNames.FIRE_ORANGE, MaterialNames.EMBER_RED, MaterialNames.ACID_YELLOW]
    
    # Materials that should use metallic shaders
    METALLIC_SHADER = [
        MaterialNames.CHROME_SILVER, MaterialNames.METAL_GRAY, MaterialNames.COPPER_GREEN
    ]
    
    # Materials that should use crystalline/transparent shaders
    CRYSTALLINE = [MaterialNames.ICE_WHITE, MaterialNames.FROST_BLUE, MaterialNames.CRYSTAL_PURPLE]
    
    @classmethod
    def get_texture_type(cls, material_name: str) -> str:
        """Get the texture type for a material"""
        if material_name in cls.EMISSIVE:
            return "emissive"
        elif material_name in cls.METALLIC_SHADER:
            return "metallic"
        elif material_name in cls.CRYSTALLINE:
            return "crystalline"
        elif material_name in cls.ROCKY:
            return "rocky"
        elif material_name in cls.ORGANIC:
            return "organic"
        else:
            return "basic"


class BodyPartMaterials:
    """Constants for body part material assignment"""
    BODY = "body"
    HEAD = "head" 
    LIMBS = "limbs"
    EXTRA = "extra"  # For additional parts like eyes, details
    
    @classmethod
    def get_all(cls) -> List[str]:
        """Get all body part categories"""
        return [cls.BODY, cls.HEAD, cls.LIMBS, cls.EXTRA]