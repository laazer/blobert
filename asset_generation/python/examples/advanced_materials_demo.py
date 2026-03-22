#!/usr/bin/env python3
"""
Advanced Materials Demo
Demonstrates the enhanced material system capabilities
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def main():
    """Run advanced materials demo"""
    print("🎨 Advanced Materials System Demo")
    print("=" * 50)
    
    print("\n🚀 WHAT'S NEW IN THE MATERIAL SYSTEM:")
    print("✅ Multi-layered materials (base + wear + detail + effects)")
    print("✅ Environmental adaptation (swamp, volcanic, arctic, etc.)")  
    print("✅ Battle damage simulation (scratches, wear, battle scars)")
    print("✅ Magical enhancement effects (fire, ice, lightning, shadow)")
    print("✅ Subsurface scattering for organic materials")
    print("✅ Advanced procedural textures with displacement")
    print("✅ 7 material presets for instant professional looks")
    
    print("\n🎯 EXAMPLES TO TRY:")
    
    examples = [
        {
            'title': '🔥 Volcanic Fire Spider',
            'command': 'python main.py smart --description "large fire spider from volcanic caves" --environment volcanic',
            'description': 'Creates spider with heat-damaged materials, ember glow, and lava textures'
        },
        {
            'title': '❄️ Ice-Cursed Warrior',
            'command': 'python main.py smart --description "cursed ice warrior" --magical-effects ice',
            'description': 'Humanoid with crystalline ice effects and frost coating'
        },
        {
            'title': '⚔️ Battle-Worn Veteran',
            'command': 'python main.py smart --description "veteran crawler with many battle scars" --material-preset battle_worn',
            'description': 'Heavily damaged materials showing wear, scratches, and combat history'
        },
        {
            'title': '🧪 Toxic Swamp Mutant',
            'command': 'python main.py smart --description "mutated swamp blob" --environment swamp --damage-level 0.6',
            'description': 'Corroded materials with toxic glow and swamp contamination'
        },
        {
            'title': '⚡ Lightning-Charged Drone',
            'command': 'python main.py smart --description "electric metal drone" --magical-effects lightning',
            'description': 'Metallic materials with electric arcing and energy effects'
        },
        {
            'title': '👻 Shadow-Touched Specter', 
            'command': 'python main.py smart --description "dark shadowy creature" --magical-effects shadow',
            'description': 'Dark materials with ethereal void effects and nightmare textures'
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}")
        print(f"   Command: {example['command']}")
        print(f"   Result:  {example['description']}")
    
    print("\n🔧 MATERIAL PRESETS AVAILABLE:")
    presets = {
        'battle_worn': 'Weathered, scarred, veteran appearance',
        'swamp_corrupted': 'Muddy, rotting, contaminated look',  
        'volcanic_forged': 'Heat-damaged with ember glow',
        'ice_cursed': 'Frost-covered with ice crystals',
        'fire_blessed': 'Holy fire with divine radiance',
        'shadow_touched': 'Dark void with nightmare effects',
        'toxic_mutated': 'Poisonous with corrosion damage'
    }
    
    for preset, description in presets.items():
        print(f"  • {preset}: {description}")
    
    print("\n🌍 ENVIRONMENTAL ADAPTATIONS:")
    environments = {
        'swamp': 'Mud coating, moisture effects, slime trails',
        'volcanic': 'Heat distortion, ember particles, lava glow',
        'arctic': 'Ice crystals, frost coating, cold mist', 
        'toxic': 'Corrosion effects, poison glow, chemical burns',
        'desert': 'Sand wear, heat shimmer, sun bleaching'
    }
    
    for env, description in environments.items():
        print(f"  • {env}: {description}")
    
    print("\n✨ MAGICAL EFFECTS:")
    magic_effects = {
        'fire': 'Burning aura, flame trails, ember sparks',
        'ice': 'Frost crystals, cold mist, ice shards',
        'lightning': 'Electric arcs, energy glow, static discharge',
        'shadow': 'Void effects, dark energy, nightmare wisps',
        'holy': 'Divine radiance, pure light, blessing aura'
    }
    
    for effect, description in magic_effects.items():
        print(f"  • {effect}: {description}")
    
    print("\n📈 TECHNICAL IMPROVEMENTS:")
    print("  • Layered Material System: Stack multiple effects")
    print("  • Subsurface Scattering: Realistic skin/organic materials")
    print("  • Displacement Mapping: Real 3D surface details") 
    print("  • Animated Properties: Time-based material effects")
    print("  • Context Awareness: Materials adapt to enemy type")
    print("  • Performance Optimized: LOD-friendly material complexity")
    
    print(f"\n🎮 TRY IT NOW:")
    print("Run any of the example commands above to see the enhanced materials!")
    print("\nFor detailed material guide: docs/SMART_GENERATION.md")

if __name__ == "__main__":
    main()