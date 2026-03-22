#!/usr/bin/env python3
"""
Locates the Blender executable across platforms.

Can be imported as a module or run directly to print the resolved path:
    python3 bin/find_blender.py

Resolution order:
  1. BLENDER_PATH environment variable
  2. Platform-specific common install locations
  3. System PATH (blender command)
"""

import os
import sys
import shutil
from pathlib import Path


_SEARCH_PATHS: dict[str, list[str]] = {
    "darwin": [
        "/Applications/Blender.app/Contents/MacOS/Blender",
        "/Applications/Blender/Blender.app/Contents/MacOS/Blender",
        str(Path.home() / "Applications/Blender.app/Contents/MacOS/Blender"),
    ],
    "linux": [
        "/usr/bin/blender",
        "/usr/local/bin/blender",
        "/snap/bin/blender",
        str(Path.home() / "blender/blender"),
    ],
    "win32": [
        r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender\blender.exe",
    ],
}


def _platform_key() -> str:
    if sys.platform == "darwin":
        return "darwin"
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "win32":
        return "win32"
    return ""


def _is_executable(path: str) -> bool:
    return os.path.isfile(path) and os.access(path, os.X_OK)


def resolve_blender_path() -> str:
    """Return the path to the Blender executable.

    Raises RuntimeError with a helpful message if Blender cannot be found.
    """
    # 1. Honour explicit override
    env_path = os.environ.get("BLENDER_PATH")
    if env_path:
        if _is_executable(env_path):
            return env_path
        raise RuntimeError(
            f"BLENDER_PATH is set to '{env_path}' but is not a valid executable."
        )

    # 2. Platform-specific common locations
    for candidate in _SEARCH_PATHS.get(_platform_key(), []):
        if _is_executable(candidate):
            return candidate

    # 3. System PATH
    blender_in_path = shutil.which("blender")
    if blender_in_path:
        return blender_in_path

    raise RuntimeError(
        "Blender executable not found.\n"
        "Install Blender from https://www.blender.org/download/ or set the\n"
        "BLENDER_PATH environment variable:\n"
        "  export BLENDER_PATH=/path/to/blender"
    )


if __name__ == "__main__":
    try:
        print(resolve_blender_path())
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
