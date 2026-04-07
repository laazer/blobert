import subprocess
import sys
from pathlib import Path


def test_player_list_works_without_bpy():
    repo_root = Path(__file__).resolve().parents[4]
    main_py = repo_root / "asset_generation" / "python" / "main.py"
    result = subprocess.run(
        [sys.executable, str(main_py), "player", "list"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "AVAILABLE SLIME COLORS" in result.stdout
    assert "blue" in result.stdout


def test_player_rejects_invalid_hex_color():
    repo_root = Path(__file__).resolve().parents[4]
    main_py = repo_root / "asset_generation" / "python" / "main.py"
    result = subprocess.run(
        [sys.executable, str(main_py), "player", "blue", "1", "--hex-color", "#1234"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Invalid --hex-color" in result.stdout


def test_animated_rejects_invalid_hex_color_before_blender():
    repo_root = Path(__file__).resolve().parents[4]
    main_py = repo_root / "asset_generation" / "python" / "main.py"
    result = subprocess.run(
        [sys.executable, str(main_py), "animated", "adhesion_bug", "1", "--hex-color", "#1234"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Invalid --hex-color" in result.stdout
