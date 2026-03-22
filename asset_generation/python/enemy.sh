#!/bin/bash

# Enemy Generator - Professional 3D Enemy Creation System
# Primary interface for all enemy generation functionality

set -e  # Exit on any error

# Configuration
PYTHON_GENERATOR="src/generator.py"
MAIN_PY="main.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Helper functions
print_colored() {
    echo -e "${2}${1}${NC}"
}

print_header() {
    print_colored "🎮 $1" "$BLUE"
    echo "$(printf '=%.0s' {1..50})"
}

check_requirements() {
    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        print_colored "❌ Error: python3 not found. Please install Python 3" "$RED"
        exit 1
    fi

    # Verify Blender can be resolved (delegates to the Python resolver)
    if ! python3 bin/find_blender.py > /dev/null 2>&1; then
        python3 bin/find_blender.py  # Re-run to surface the error message
        exit 1
    fi

    # Check if organized system exists
    if [ ! -f "$PYTHON_GENERATOR" ]; then
        print_colored "❌ Error: Organized system not found at $PYTHON_GENERATOR" "$RED"
        echo "Run setup or check project structure"
        exit 1
    fi
}

show_help() {
    print_header "Enemy Generator Help"
    echo ""
    print_colored "USAGE:" "$YELLOW"
    echo "  ./enemy.sh <command> [arguments]"
    echo ""
    print_colored "COMMANDS:" "$YELLOW"
    echo "  list                          - List all available enemies"
    echo "  test                          - Quick test (generates adhesion_bug)"
    echo ""
    echo "  animated <enemy> [count]      - Generate animated enemy"
    echo "  smart <description>           - 🧠 AI-powered generation from text"
    echo ""
    echo "  view <filename> [--anim name] - View generated enemy in Blender"
    echo ""
    print_colored "EXAMPLES:" "$YELLOW"
    echo "  ./enemy.sh list"
    echo "  ./enemy.sh test"
    echo "  ./enemy.sh animated adhesion_bug 3"
    echo "  ./enemy.sh animated tar_slug 1"
    echo "  ./enemy.sh view adhesion_bug_animated_00 --anim move"
    echo ""
    print_colored "🧠 SMART GENERATION EXAMPLES:" "$BLUE"
    echo "  ./enemy.sh smart \"large fire spider with powerful attacks\""
    echo "  ./enemy.sh smart \"battle-worn ice warrior\""
    echo "  ./enemy.sh smart \"toxic swamp blob with corrosion\""
    echo ""
    print_colored "ANIMATED ENEMIES:" "$GREEN"
    echo "  • adhesion_bug - 6-legged insectoid with quadruped movement"
    echo "  • tar_slug     - Blob creature with squash/stretch movement"
    echo "  • ember_imp    - Humanoid fire creature with bipedal movement"
    echo ""
    print_colored "ANIMATION SYSTEM (13 types):" "$BLUE"
    echo "  Core: idle, move, attack, damage, death (always included)"
    echo "  Extended: spawn, special_attack, damage_heavy, damage_fire,"
    echo "           damage_ice, stunned, celebrate, taunt (smart generation)"
    echo ""
    print_colored "🎨 ADVANCED MATERIALS:" "$YELLOW"
    echo "  • Environmental adaptation (swamp, volcanic, arctic, toxic)"
    echo "  • Battle damage simulation (0.0-1.0 wear levels)"
    echo "  • Magical effects (fire, ice, lightning, shadow, holy)"
    echo "  • 7 material presets (battle_worn, volcanic_forged, etc.)"
}

# Main command processing
case "${1:-}" in
    "help"|"-h"|"--help"|"")
        show_help
        ;;
    
    "smart")
        # Handle smart command with description conversion
        if [ -z "${2:-}" ]; then
            print_colored "❌ Error: Description required for smart generation" "$RED"
            echo "Usage: ./enemy.sh smart \"description of enemy\""
            echo "Example: ./enemy.sh smart \"large fire spider with powerful attacks\""
            exit 1
        fi
        check_requirements
        # Convert positional description to --description flag
        shift  # Remove 'smart'
        python3 "$MAIN_PY" smart --description "$1" "${@:2}"
        ;;
    
    *)
        # Delegate all other commands to Python main.py
        check_requirements
        python3 "$MAIN_PY" "$@"
        ;;
esac