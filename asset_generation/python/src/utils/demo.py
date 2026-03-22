#!/usr/bin/env python3
"""
Demonstration script showing utility constants usage
"""

from .constants import EnemyTypes, AnimationTypes, AnimationConfig, BoneNames
from .materials import MaterialNames, MaterialThemes, MaterialCategories

def demonstrate_constants():
    """Demonstrate the utility of the new constants"""
    
    print("🎮 Enemy Generation Constants Demo")
    print("=" * 50)
    
    # Enemy types
    print("\n📦 Available Enemy Types:")
    print("Animated:", EnemyTypes.get_animated())
    print("Static:", EnemyTypes.get_static())
    
    # Animation system  
    print(f"\n🎬 Animation System:")
    for anim_type in AnimationTypes.get_all():
        duration = AnimationConfig.get_duration_seconds(anim_type)
        frames = AnimationConfig.get_length(anim_type)
        print(f"  {anim_type}: {frames} frames ({duration}s)")
    
    # Bone structure
    print(f"\n🦴 Bone Structure:")
    print("Quadruped legs:", BoneNames.get_quadruped_legs())
    print("Humanoid arms:", BoneNames.get_humanoid_arms())
    print("Humanoid legs:", BoneNames.get_humanoid_legs())
    
    # Material system
    print(f"\n🎨 Material System:")
    print("Available materials:", len(MaterialNames.__dict__))
    
    # Enemy themes
    print(f"\n🎭 Enemy Material Themes:")
    for enemy_type in EnemyTypes.get_animated():
        theme = MaterialThemes.get_theme(enemy_type)
        print(f"  {enemy_type}: {theme}")
    
    # Material categories  
    print(f"\n🏷️ Material Categories:")
    print("Emissive materials:", MaterialCategories.EMISSIVE)
    print("Metallic materials:", MaterialCategories.METALLIC)
    print("Crystalline materials:", MaterialCategories.CRYSTALLINE)
    
    print("\n✨ Benefits of Constants:")
    print("• No more typos in bone names or material names")
    print("• Centralized configuration for easy tweaking")  
    print("• Type safety and IDE auto-completion")
    print("• Easy to extend with new enemies/animations")
    print("• Clear separation of data from logic")


if __name__ == "__main__":
    demonstrate_constants()