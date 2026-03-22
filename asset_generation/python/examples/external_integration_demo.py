#!/usr/bin/env python3
"""
External Model Integration Demo
Demonstrates integration capabilities and file format support
"""

import sys
import os
from pathlib import Path

def demo_basic_import():
    """Demonstrate basic model import commands"""
    print("🎮 Demo: Basic Model Import Commands")
    print("=" * 50)
    
    # Show available model files
    if os.path.exists("animated_exports"):
        models = [f for f in os.listdir("animated_exports") if f.endswith('.glb')]
        print("📁 Available Models for Import Testing:")
        for model in models[:5]:  # Show first 5
            print(f"   • {model}")
        
        if models:
            sample_model = models[0]
            print(f"\n💡 Example Import Commands:")
            print(f"   python main.py import --model-path 'animated_exports/{sample_model}' --body-type quadruped")
            print(f"   python main.py import --model-path 'animated_exports/{sample_model}' --body-type humanoid --animation-set core")
    else:
        print("📁 No models found. Run 'python main.py test' to generate sample models")
    
    return True

def demo_full_integration():
    """Demonstrate complete integration workflow"""
    print("\n🔧 Demo: Integration Workflow Examples")
    print("=" * 50)
    
    print("🎯 Complete Integration Examples:")
    print()
    
    print("📥 Scenario 1: External FBX with No Animations")
    print("   Command: python main.py import --model-path dragon.fbx --body-type quadruped --animation-set all")
    print("   Result:  Complete creature with all 13 animations generated")
    print()
    
    print("📥 Scenario 2: GLB with Partial Animations")
    print("   Command: python main.py import --model-path warrior.glb --body-type humanoid --animation-set extended")
    print("   Result:  Preserves existing animations, adds missing ones")
    print()
    
    print("📥 Scenario 3: OBJ Mesh Only")
    print("   Command: python main.py import --model-path creature.obj --body-type blob --animation-set core")
    print("   Result:  Creates armature, binds mesh, generates essential animations")
    
    return True

def demo_step_by_step():
    """Demonstrate step-by-step integration process"""
    print("\n🎯 Demo: Integration Process Steps")
    print("=" * 50)
    
    print("🔄 What Happens During Integration:")
    print()
    
    print("1️⃣ Import & Analysis")
    print("   • Load model from file (FBX, GLB, OBJ, etc.)")
    print("   • Detect armatures, meshes, animations")
    print("   • Count vertices and bones")
    print("   • Identify existing animations")
    print()
    
    print("2️⃣ Compatibility Enhancement")
    print("   • Create armature if missing")  
    print("   • Optimize mesh binding")
    print("   • Apply body part recognition")
    print("   • Enhance materials")
    print()
    
    print("3️⃣ Animation Generation")
    print("   • Identify missing required animations")
    print("   • Generate animations for target body type")
    print("   • Preserve existing animations")
    print("   • Ensure animation compatibility")
    print()
    
    print("4️⃣ Export & Integration")
    print("   • Export as .blend and .glb")
    print("   • Generate integration report")
    print("   • Ready for game engine use")
    
    return True

def demo_format_compatibility():
    """Demonstrate different file format handling"""
    print("\n📁 Demo: File Format Compatibility")
    print("=" * 50)
    
    # Show supported formats
    supported_formats = {'.fbx', '.obj', '.dae', '.gltf', '.glb', '.blend'}
    required_animations = ['idle', 'move', 'attack', 'damage', 'death']
    
    print("🔧 Supported File Formats:")
    format_info = [
        (".fbx", "FBX (Autodesk)", "Industry standard, animations", "✅ Excellent"),
        (".glb", "GLTF Binary", "Web, real-time engines", "✅ Excellent"),
        (".gltf", "GLTF Text", "Web, real-time engines", "✅ Excellent"), 
        (".blend", "Blender Native", "Blender projects", "✅ Perfect"),
        (".dae", "Collada", "Game engines, exchange", "✅ Good"),
        (".obj", "Wavefront OBJ", "Simple meshes, static", "⚠️ Mesh only")
    ]
    
    for ext, name, use, quality in format_info:
        print(f"   • {ext:<6} {name:<15} - {use:<20} ({quality})")
    
    print("\n📋 Required Core Animations:")
    for anim in required_animations:
        print(f"   • {anim}")
    
    print("\n🔍 Format Usage Examples:")
    examples = [
        ("dragon.fbx", "From 3D modeling software", "✅ Full import with animations"),
        ("warrior.glb", "From web/game engines", "✅ Complete with textures"),
        ("creature.obj", "Legacy mesh format", "⚠️ Mesh only, armature created"),
        ("scene.dae", "From other game engines", "✅ Good compatibility"),
        ("project.blend", "Native Blender file", "✅ Perfect fidelity")
    ]
    
    for filename, source, result in examples:
        print(f"   {filename:<15} ({source:<25}) → {result}")

def main():
    """Run all integration demos"""
    print("🎮 External Model Integration Demos")
    print("=" * 50)
    
    # Ensure demo directories exist
    os.makedirs('demo_exports', exist_ok=True)
    
    # Run demos
    demos = [
        demo_format_compatibility,
        demo_basic_import,
        demo_full_integration,
        demo_step_by_step
    ]
    
    results = []
    for demo in demos:
        try:
            result = demo()
            results.append(result)
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            results.append(False)
        
        print()  # Spacing between demos
    
    # Summary
    print("📊 Demo Results Summary:")
    print("=" * 30)
    demo_names = [
        "Format Compatibility",
        "Basic Import", 
        "Full Integration",
        "Step-by-Step"
    ]
    
    for i, (name, success) in enumerate(zip(demo_names, results)):
        status = "✅ Passed" if success else "❌ Failed"
        print(f"{i+1}. {name}: {status}")
    
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"\n🎯 Overall: {passed}/{total} demos successful")
    
    if passed == total:
        print("🎊 All integration demos completed successfully!")
    else:
        print("⚠️ Some demos failed - check error messages above")

if __name__ == "__main__":
    main()