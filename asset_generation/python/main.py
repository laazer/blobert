#!/usr/bin/env python3
"""
Blender Enemy Generator - Main Entry Point
Unified command-line interface for generating game-ready enemies
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# Add src and bin directories to Python path
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, 'src'))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, 'bin'))

from find_blender import resolve_blender_path
from utils.constants import EnemyTypes, ExportConfig, LevelObjectTypes, LevelExportConfig, PlayerExportConfig


def _get_blender_path() -> str:
    try:
        return resolve_blender_path()
    except RuntimeError as error:
        print_colored(f"❌ {error}", Colors.RED)
        sys.exit(1)

class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # No Color

def print_colored(text, color):
    print(f"{color}{text}{Colors.NC}")

def print_header(title):
    print_colored(f"🎮 {title}", Colors.BLUE)
    print("=" * (len(title) + 3))

def check_blender() -> bool:
    """Verify Blender is resolvable and accessible"""
    try:
        path = resolve_blender_path()
        return bool(path)
    except RuntimeError as error:
        print_colored(f"❌ {error}", Colors.RED)
        return False

def list_enemies():
    """List all available enemies"""
    print_header("Available Enemies")
    
    static_enemies = EnemyTypes.get_all()
    animated_enemies = EnemyTypes.get_animated()
    animated_enemy_details = {
        'adhesion_bug': 'Multi-segment bug (6-legged quadruped movement)',
        'tar_slug': 'Elongated slug (dramatic squash/stretch movement)',
        'ember_imp': 'Humanoid fire creature (bipedal walk, punch attack)',
    }

    print_colored(f"📦 STATIC ENEMIES ({len(static_enemies)} types):", Colors.YELLOW)
    for i, enemy in enumerate(static_enemies, 1):
        print(f"{i:2d}. {enemy}")

    print()
    print_colored(f"🎬 ANIMATED ENEMIES ({len(animated_enemies)} types) - WORKING VISIBLE ANIMATIONS:", Colors.GREEN)
    for i, enemy in enumerate(animated_enemies, 1):
        print(f"{i:2d}. {enemy} - {animated_enemy_details[enemy]}")
    
    print()
    print_colored("🎯 ANIMATION SETS (13 per animated enemy):", Colors.BLUE)
    print()
    print_colored("CORE ANIMATIONS:", Colors.GREEN)
    print("• idle (2.0s)          - Breathing & waiting")
    print("• move (1.0s)          - Locomotion loop") 
    print("• attack (1.5s)        - Basic attack sequence")
    print("• damage (0.5s)        - Quick damage reaction")
    print("• death (3.0s)         - Dramatic death sequence")
    print()
    print_colored("EXTENDED ANIMATIONS:", Colors.YELLOW)
    print("• spawn (2.0s)         - Materialize/emerge from ground")
    print("• special_attack (2.5s)- Powerful signature attack")
    print("• damage_heavy (1.0s)  - Major damage with knockback")
    print("• damage_fire (0.75s)  - Fire damage with burning effect")
    print("• damage_ice (1.25s)   - Ice damage with freezing")
    print("• stunned (2.5s)       - Dazed/incapacitated state")
    print("• celebrate (1.5s)     - Victory pose")
    print("• taunt (1.0s)         - Provocative gesture")
    print()
    print_colored("✅ Enhanced materials and textures included!", Colors.GREEN)

def handle_smart_commands(args):
    """Handle smart generation, description, and stats commands"""
    try:
        from src.smart.smart_generation import SmartGenerator, TextToEnemyGenerator
    except ImportError:
        print_colored("❌ Smart generation system not available", Colors.RED)
        return False
    
    smart_gen = SmartGenerator()
    
    if args.command == 'smart':
        return handle_smart_generation(args, smart_gen)
    elif args.command == 'stats':
        return handle_stats_export(args, smart_gen)
    
    return False

def _print_blueprint_design(blueprint) -> None:
    """Print the generated enemy design summary"""
    print()
    print_colored("🎯 Generated Enemy Design:", Colors.GREEN)
    print(f"Name: {blueprint.name}")
    print(f"Type: {blueprint.enemy_type} ({blueprint.body_type})")
    print(f"Size: {blueprint.size_scale:.1f}x")
    print(f"Animation Set: {blueprint.animation_set}")
    print()


def _print_blueprint_stats(stats) -> None:
    """Print the generated enemy stats"""
    print_colored("📊 Enemy Stats:", Colors.BLUE)
    print(f"Health: {stats.health}")
    print(f"Damage: {stats.damage}")
    print(f"Speed: {stats.speed:.1f}")
    print(f"Armor: {stats.armor}")
    print(f"Threat Level: {stats.threat_level}")
    if stats.special_abilities:
        print(f"Abilities: {', '.join(stats.special_abilities)}")
    if stats.weaknesses:
        print(f"Weaknesses: {', '.join(stats.weaknesses)}")


def _export_blueprint_stats(smart_gen, blueprint, format_type: str) -> None:
    """Export blueprint stats to a file"""
    stats_output = smart_gen.export_stats(blueprint, format_type)
    stats_file = f"{blueprint.name}_stats.{format_type}"
    with open(stats_file, 'w') as f:
        f.write(stats_output)
    print()
    print_colored(f"📄 Stats exported to: {stats_file}", Colors.GREEN)


def handle_smart_generation(args, smart_gen) -> bool:
    """Handle AI-assisted enemy generation"""
    if not args.description:
        print_colored("❌ Description required for smart generation", Colors.RED)
        print("Example: python main.py smart --description 'a large fire spider with powerful attacks'")
        return False

    print_header("🧠 AI-Assisted Enemy Generation")
    print_colored(f"📝 Description: {args.description}", Colors.BLUE)
    print_colored(f"⚡ Difficulty: {args.difficulty}", Colors.YELLOW)

    try:
        blueprint = smart_gen.generate_from_text(
            args.description,
            difficulty=args.difficulty,
            seed=args.seed,
        )

        _print_blueprint_design(blueprint)
        _print_blueprint_stats(blueprint.stats)

        if args.export_stats:
            _export_blueprint_stats(smart_gen, blueprint, args.export_stats)

        print()
        print_colored("🎮 Generating 3D Model...", Colors.BLUE)
        success = generate_animated_enemy_from_blueprint(blueprint)

        if success:
            print_colored("✅ Smart generation complete!", Colors.GREEN)
        else:
            print_colored("❌ 3D generation failed", Colors.RED)
        return success

    except Exception as error:
        print_colored(f"❌ Smart generation error: {error}", Colors.RED)
        return False

def handle_stats_export(args, smart_gen):
    """Export stats for existing enemies"""
    if not args.enemy:
        print_colored("❌ Enemy name required for stats export", Colors.RED)
        return False
    
    print_header("📊 Stats Export")
    print_colored(f"Generating stats for {args.enemy}...", Colors.BLUE)
    
    # Generate basic stats for existing enemy types
    description = f"A {args.enemy} enemy"
    blueprint = smart_gen.generate_from_text(description, args.difficulty, args.seed)
    blueprint.name = args.enemy
    
    format_type = args.export_stats or 'json'
    stats_output = smart_gen.export_stats(blueprint, format_type)
    
    print()
    print_colored(f"📄 {blueprint.name} Stats ({format_type.upper()}):", Colors.GREEN)
    print(stats_output)
    
    # Save to file
    stats_file = f"{blueprint.name}_stats.{format_type}"
    with open(stats_file, 'w') as f:
        f.write(stats_output)
    
    print_colored(f"💾 Saved to: {stats_file}", Colors.BLUE)
    return True

def run_blender_script(script_content):
    """Run a Python script in Blender"""
    import tempfile
    try:
        # Create temporary script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            temp_script = f.name
        
        # Run Blender
        result = subprocess.run([
            _get_blender_path(), "--background", "--python", temp_script
        ], capture_output=True, text=True)
        
        # Clean up
        if os.path.exists(temp_script):
            os.remove(temp_script)
        
        # Check for errors
        if result.returncode != 0:
            print_colored("❌ Blender execution failed:", Colors.RED)
            if result.stderr:
                print(result.stderr)
            return False
        
        # Show output
        if result.stdout:
            print(result.stdout)
            
        return result.returncode == 0
        
    except Exception as e:
        print_colored(f"❌ Error running Blender: {e}", Colors.RED)
        return False

def handle_view_command(args):
    """Handle view command to open enemy in Blender"""
    if not args.enemy:
        print_colored("❌ Error: Filename required", Colors.RED)
        print("Usage: python main.py view <filename> [--anim animation_name]")
        return False
    
    filename = args.enemy
    animation = args.anim
    
    animated_dir = ExportConfig.ANIMATED_DIR
    glb_file = f"{animated_dir}/{filename}.glb"
    if not os.path.exists(glb_file):
        print_colored(f"❌ Error: File not found: {glb_file}", Colors.RED)
        print("Available files:")
        try:
            files = [f.replace('.glb', '') for f in os.listdir(animated_dir) if f.endswith('.glb')]
            for f in sorted(files):
                print(f"  {f}")
        except Exception:
            print("  (no files found)")
        return False
    
    print_header(f"Viewing {filename}")
    print_colored(f"🎬 Loading with {animation} animation...", Colors.BLUE)
    
    # Use simple animation viewer script to load GLB with specific animation
    viewer_script = "src/utils/simple_viewer.py"
    glb_full_path = os.path.abspath(glb_file)
    
    try:
        # Run Blender in foreground with animation viewer script
        result = subprocess.run([
            _get_blender_path(),
            "--python", viewer_script,
            "--", glb_full_path, animation
        ])
        return True
    except Exception as e:
        print_colored(f"❌ Error: {e}", Colors.RED)
        return False

def handle_import_command(args):
    """Handle external model import command"""
    if not args.model_path:
        print_colored("❌ Error: Model path required for import", Colors.RED)
        print("Usage: python main.py import --model-path /path/to/model.fbx")
        print("Supported formats: .fbx, .obj, .dae, .gltf, .glb, .blend")
        return False
    
    if not check_blender():
        return False
    
    model_path = os.path.abspath(args.model_path)
    if not os.path.exists(model_path):
        print_colored(f"❌ Error: Model file not found: {model_path}", Colors.RED)
        return False
    
    print_header("External Model Integration")
    print_colored(f"📁 Model: {os.path.basename(model_path)}", Colors.BLUE)
    print_colored(f"🦴 Body Type: {args.body_type}", Colors.YELLOW)
    print_colored(f"🎬 Animation Set: {args.animation_set}", Colors.GREEN)
    
    # Create Blender script for import
    project_root = os.path.dirname(__file__)
    script_content = f'''
import sys
import os

# Add project paths
sys.path.insert(0, "{project_root}")
sys.path.insert(0, os.path.join("{project_root}", "src"))

try:
    from src.integration.external_model_importer import import_external_model
    
    # Import and integrate the model
    output_path = import_external_model(
        "{model_path}",
        "{args.body_type}",
        "{args.animation_set}",
        "{ExportConfig.ANIMATED_DIR}"
    )
    
    print(f"\\n🎊 SUCCESS: Integrated model exported to {{output_path}}")
    
except Exception as e:
    print(f"❌ IMPORT FAILED: {{e}}")
    import traceback
    traceback.print_exc()
'''
    
    try:
        success = run_blender_script(script_content)
        if success:
            print_colored("✅ Model integration completed!", Colors.GREEN)
            print(f"Check animated_exports/ for your integrated model")
        else:
            print_colored("❌ Model integration failed", Colors.RED)
        return success
    except Exception as e:
        print_colored(f"❌ Integration error: {e}", Colors.RED)
        return False

def generate_animated_enemy_from_blueprint(blueprint):
    """Generate actual 3D enemy from blueprint"""
    print(f"Generating {blueprint.enemy_type} as {blueprint.name}...")
    
    # Use existing generation system
    project_root = os.path.dirname(__file__)
    script_content = f"""
import sys, os
import random

# Add project paths
sys.path.insert(0, "{project_root}")
sys.path.insert(0, os.path.join("{project_root}", "src"))

import bpy
from src.core.blender_utils import clear_scene
from src.materials.material_system import setup_materials
from src.enemies.animated_enemies import AnimatedEnemyBuilder
from src.enemies.base_enemy import export_enemy

# Clear and setup
clear_scene()
materials = setup_materials()

# Generate with blueprint settings
rng = random.Random({blueprint.generation_seed})
armature, mesh, attack_profile = AnimatedEnemyBuilder.create_enemy("{blueprint.enemy_type}", materials, rng)

if armature and mesh:
    export_enemy(armature, mesh, "{blueprint.name}", "{ExportConfig.ANIMATED_DIR}", attack_profile)
    print("✅ Generated {blueprint.name}")
else:
    print("❌ Generation failed")
"""
    
    return run_blender_script(script_content)

def handle_player_command(args):
    """Handle player slime generation command."""
    # Import here to avoid loading the full player package at CLI startup
    from player.player_materials import SLIME_COLORS

    color = args.enemy or "blue"

    if color == 'list':
        _print_player_colors(SLIME_COLORS)
        return True

    if not check_blender():
        return False

    if color not in SLIME_COLORS:
        print_colored(f"❌ Unknown slime color: {color!r}", Colors.RED)
        _print_player_colors(SLIME_COLORS)
        return False

    print_header(f"Generating Player Slime: {color}")
    print_colored(f"🫧 Color: {color}  ×{args.count} variants", Colors.BLUE)
    if args.prefab:
        print_colored(f"📦 Prefab mesh: {args.prefab}", Colors.YELLOW)

    blender_args = [color, str(args.count)]
    if args.prefab:
        blender_args += ['--prefab', args.prefab]

    result = subprocess.run([
        _get_blender_path(), "--background", "--python", "src/player_generator.py",
        "--", *blender_args
    ])

    if result.returncode == 0:
        print_colored("✅ Player slime generated!", Colors.GREEN)
        print(f"Check {PlayerExportConfig.PLAYER_DIR}/ for output files.")
        return True
    else:
        print_colored("❌ Player slime generation failed", Colors.RED)
        return False


def _print_player_colors(slime_colors: dict):
    print()
    print_colored("🫧 AVAILABLE SLIME COLORS:", Colors.BLUE)
    for color_name in slime_colors:
        print(f"  {color_name}")
    print()


def handle_level_command(args):
    """Handle level object generation command."""
    if not args.enemy:
        print_colored("❌ Error: Object type required", Colors.RED)
        print("Use 'python main.py level list' or see available types below.")
        _print_level_object_types()
        return False

    if args.enemy == 'list':
        _print_level_object_types()
        return True

    if not check_blender():
        return False

    available = LevelObjectTypes.get_all()
    if args.enemy != 'all' and args.enemy not in available:
        print_colored(f"❌ Unknown level object type: {args.enemy}", Colors.RED)
        _print_level_object_types()
        return False

    object_types = available if args.enemy == 'all' else [args.enemy]

    print_header(f"Generating Level Objects: {args.enemy}")

    all_succeeded = True
    for object_type in object_types:
        print(f"\n🏗️  Generating {object_type}...")
        result = subprocess.run([
            _get_blender_path(), "--background", "--python", "src/level_generator.py",
            "--", object_type, str(args.count)
        ])
        if result.returncode == 0:
            print_colored(f"✅ Generated {object_type}!", Colors.GREEN)
        else:
            print_colored(f"❌ Failed to generate {object_type}", Colors.RED)
            all_succeeded = False

    if args.enemy != 'all':
        print(f"Check {LevelExportConfig.LEVEL_DIR}/ for output files.")

    return all_succeeded


def _print_level_object_types():
    print()
    print_colored("🏗️  LEVEL OBJECT TYPES:", Colors.BLUE)
    print()
    print_colored("  PLATFORMS:", Colors.GREEN)
    for object_type in LevelObjectTypes.get_platforms():
        print(f"    {object_type}")
    print()
    print_colored("  WALLS:", Colors.GREEN)
    for object_type in LevelObjectTypes.get_walls():
        print(f"    {object_type}")
    print()
    print_colored("  TRAPS:", Colors.GREEN)
    for object_type in LevelObjectTypes.get_traps():
        print(f"    {object_type}")
    print()
    print_colored("  CHECKPOINTS:", Colors.GREEN)
    for object_type in LevelObjectTypes.get_checkpoints():
        print(f"    {object_type}")
    print()


def _handle_prefabs_command(args) -> bool:
    """List registered prefabs with download status and instructions."""
    from src.prefabs.prefab_library import get_all_names, get_prefab, is_prefab_downloaded

    prefab_name = args.enemy  # reuse the 'enemy' positional for the prefab name

    if prefab_name and prefab_name != 'list':
        # Show download instructions for a specific prefab
        try:
            from src.prefabs.prefab_library import get_download_instructions
            print(get_download_instructions(prefab_name))
        except KeyError as error:
            print_colored(f"❌ {error}", Colors.RED)
            return False
        return True

    # List all registered prefabs
    print_header("Available Prefabs")
    print_colored("Place downloaded files in the prefabs/ directory to use them.", Colors.BLUE)
    print()

    names = get_all_names()
    for name in names:
        entry = get_prefab(name)
        downloaded = is_prefab_downloaded(name)
        status = "✅" if downloaded else "⬇️ "
        print(f"  {status} {name:<25} [{entry.body_type:<10}] {entry.description}")

    print()
    downloaded_count = sum(1 for n in names if is_prefab_downloaded(n))
    print_colored(
        f"{downloaded_count}/{len(names)} prefabs downloaded.",
        Colors.GREEN if downloaded_count > 0 else Colors.YELLOW,
    )
    print()
    print("To get instructions for a specific prefab:")
    print("  python main.py prefabs <prefab_name>")
    print()
    print("To use a prefab in generation:")
    print("  python main.py animated adhesion_bug --prefab mantis")
    print("  python main.py player blue --prefab simple_slime")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Blender Enemy Generator - Create static and animated low-poly enemies with AI assistance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  🧠 AI-POWERED GENERATION:
  python main.py smart --description "large fire spider with powerful attacks"
  python main.py smart --description "small ice blob that moves fast" --difficulty hard  
  python main.py smart --description "armored metal warrior" --export-stats godot
  
  🎨 ADVANCED MATERIALS:
  python main.py smart --description "battle veteran spider" --material-preset battle_worn
  python main.py smart --description "swamp crawler" --environment swamp --damage-level 0.4
  python main.py smart --description "fire elemental" --magical-effects fire
  
  📊 STATS EXPORT:
  python main.py stats adhesion_bug --export-stats unity --difficulty nightmare
  python main.py stats tar_slug --export-stats json --difficulty easy
  
  🎬 TRADITIONAL GENERATION:
  python main.py animated adhesion_bug 1  # Generate 1 animated variant
  python main.py animated tar_slug 3      # Generate 3 variants
  python main.py animated all             # Generate all 3 animated enemies
  
  🔍 DISCOVERY:
  python main.py list                     # List all enemies + 13 animation types
  python main.py test                     # Quick test (1 animated adhesion_bug)
  python main.py view adhesion_bug_animated_00 --anim move  # View in Blender
  
  🫧 PLAYER SLIME GENERATION:
  python main.py player                    # default blue slime, 3 variants
  python main.py player blue 1            # 1 blue slime
  python main.py player pink              # 3 pink slime variants
  python main.py player list              # list all 8 color options

  🏗️  LEVEL OBJECT GENERATION:
  python main.py level flat_platform 3      # 3 flat platform variants
  python main.py level spike_trap 1         # 1 spike trap
  python main.py level checkpoint           # 3 checkpoints (default count)
  python main.py level all                  # one of every level object type
  python main.py level list                 # list all available types

  📦 PREFAB MODELS (downloaded Sketchfab models as mesh bases):
  python main.py prefabs                              # list all prefabs + download status
  python main.py prefabs simple_slime                 # show download instructions
  python main.py animated adhesion_bug --prefab mantis           # enemy with prefab mesh
  python main.py player blue --prefab simple_slime               # player with prefab mesh

  📥 EXTERNAL MODEL INTEGRATION:
  python main.py import --model-path model.fbx --body-type quadruped
  python main.py import --model-path creature.glb --body-type humanoid --animation-set core

For detailed smart generation guide: docs/SMART_GENERATION.md
        """
    )
    
    parser.add_argument('command', choices=[
        'animated', 'level', 'player', 'prefabs', 'list', 'test', 'smart', 'stats', 'view', 'import'
    ], help='Command to execute')
    
    parser.add_argument('enemy', nargs='?',
                       help='Enemy name or "all" (animated command); '
                            'level object type, "all", or "list" (level command)')
    
    parser.add_argument('count', nargs='?', type=int, default=3,
                       help='Number of variants to generate (default: 3)')
    
    parser.add_argument('--description', type=str,
                       help='Text description for smart generation')
    
    parser.add_argument('--difficulty', choices=['easy', 'normal', 'hard', 'nightmare'],
                       default='normal', help='Difficulty scaling (default: normal)')
    
    parser.add_argument('--seed', type=int, 
                       help='Random seed for reproducible generation')
    
    parser.add_argument('--export-stats', choices=['json', 'godot', 'unity'],
                       help='Export stats in specified format')
    
    parser.add_argument('--material-preset', 
                       choices=['battle_worn', 'swamp_corrupted', 'volcanic_forged', 'ice_cursed', 
                               'fire_blessed', 'shadow_touched', 'toxic_mutated'],
                       help='Apply advanced material preset')
    
    parser.add_argument('--environment',
                       choices=['swamp', 'volcanic', 'arctic', 'toxic', 'desert'],
                       help='Environmental adaptation for materials')
    
    parser.add_argument('--damage-level', type=float, default=0.0,
                       help='Battle damage level (0.0-1.0)')
    
    parser.add_argument('--magical-effects',
                       choices=['fire', 'ice', 'lightning', 'shadow', 'holy'],
                       help='Add magical enhancement effects')
    
    parser.add_argument('--anim', type=str, default='idle',
                       help='Animation name for view command')
    
    parser.add_argument('--model-path', type=str,
                       help='Path to external model file for import command')

    parser.add_argument('--body-type', choices=['blob', 'quadruped', 'humanoid'],
                       default='quadruped',
                       help='Body type for imported model animations')

    parser.add_argument('--animation-set', choices=['core', 'extended', 'all'],
                       default='all',
                       help='Animation set to generate for imported models')

    parser.add_argument('--prefab', type=str, metavar='NAME',
                       help='Use a downloaded Sketchfab model as the mesh base instead of '
                            'procedural geometry (animated and player commands). '
                            'The file must exist in the prefabs/ directory. '
                            'Run: python main.py prefabs  to list available prefabs.')
    
    args = parser.parse_args()
    
    # Handle prefab listing
    if args.command == 'prefabs':
        return _handle_prefabs_command(args)

    # Handle player slime generation
    if args.command == 'player':
        return handle_player_command(args)

    # Handle level object generation
    if args.command == 'level':
        return handle_level_command(args)

    # Handle list command
    if args.command == 'list':
        list_enemies()
        return
    
    # Handle smart generation commands
    if args.command in ['smart', 'stats']:
        return handle_smart_commands(args)
    
    # Handle view command
    if args.command == 'view':
        return handle_view_command(args)
    
    # Handle import command
    if args.command == 'import':
        return handle_import_command(args)
    
    # Handle test command  
    if args.command == 'test':
        print_header("Quick Test - Animated Adhesion Bug")
        if not check_blender():
            sys.exit(1)
        
        try:
            result = subprocess.run([
                _get_blender_path(), "--background", "--python", "src/generator.py",
                "--", "adhesion_bug", "1"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print_colored("✅ Test completed successfully!", Colors.GREEN)
                print("Generated adhesion_bug_animated_00.glb in animated_exports/")
            else:
                print_colored("❌ Test failed", Colors.RED)
                print(result.stderr)
                
        except Exception as e:
            print_colored(f"❌ Error running test: {e}", Colors.RED)
        
        sys.exit(0)
    
    # Handle animated generation
    if args.command == 'animated':
        if not args.enemy:
            print_colored("❌ Error: Enemy name required", Colors.RED)
            print("Use 'python main.py list' to see available enemies")
            sys.exit(1)

        if not check_blender():
            sys.exit(1)

        if args.enemy != 'all' and args.enemy not in EnemyTypes.get_animated():
            print_colored(f"❌ Unknown animated enemy: {args.enemy}", Colors.RED)
            print("Available animated enemies:", EnemyTypes.get_animated())
            sys.exit(1)

        print_header(f"Generating Animated Enemy: {args.enemy}")

        if args.prefab:
            print_colored(f"📦 Prefab mesh: {args.prefab}", Colors.YELLOW)

        enemies_to_generate = EnemyTypes.get_animated() if args.enemy == 'all' else [args.enemy]
        for enemy_type in enemies_to_generate:
            print(f"\n🎬 Generating {enemy_type}...")
            blender_args = [enemy_type, str(args.count)]
            if args.prefab:
                blender_args += ['--prefab', args.prefab]
            result = subprocess.run([
                _get_blender_path(), "--background", "--python", "src/generator.py",
                "--", *blender_args
            ])
            if result.returncode == 0:
                print_colored(f"✅ Generated {enemy_type}!", Colors.GREEN)
            else:
                print_colored(f"❌ Failed to generate {enemy_type}", Colors.RED)

        if args.enemy != 'all':
            print(f"Check {ExportConfig.ANIMATED_DIR}/ for {args.enemy}_animated_*.glb files")

if __name__ == "__main__":
    main()