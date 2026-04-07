#!/usr/bin/env python3
"""Fast reviewer-style hygiene checks for staged GDScript files."""

import re
import sys
from pathlib import Path
from typing import List

CONFLICT_MARKERS = ("<<<<<<<", "=======", ">>>>>>>")
TRAILING_WS_RE = re.compile(r"[ \t]+$")


def check_file(path: Path) -> List[str]:
    errors: List[str] = []
    if not path.exists():
        return errors

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    class_name_count = 0
    for idx, line in enumerate(lines, start=1):
        if any(marker in line for marker in CONFLICT_MARKERS):
            errors.append(f"{path}:{idx}: merge-conflict marker present")
        if TRAILING_WS_RE.search(line):
            errors.append(f"{path}:{idx}: trailing whitespace")
        if line.startswith("class_name "):
            class_name_count += 1

    if class_name_count > 1:
        errors.append(f"{path}: multiple class_name declarations ({class_name_count})")
    if text and not text.endswith("\n"):
        errors.append(f"{path}: file should end with a newline")

    return errors


def main(argv: List[str]) -> int:
    files = [Path(arg) for arg in argv[1:] if arg.endswith(".gd")]
    if not files:
        return 0

    errors: List[str] = []
    for file_path in files:
        errors.extend(check_file(file_path))

    if errors:
        print("pre-commit: Godot reviewer checks failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print("pre-commit: Godot reviewer checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
