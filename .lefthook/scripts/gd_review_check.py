#!/usr/bin/env python3
"""Fast reviewer-style hygiene checks for staged GDScript files."""

import re
import sys
from pathlib import Path
from typing import List

from gd_magic_number_check import check_staged_gd_files
from precommit_git_diff import git_diff_cached, git_repo_root, parse_staged_additions

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

    repo = git_repo_root()
    if repo is not None:
        diff = git_diff_cached(repo)
        additions = parse_staged_additions(diff)
        errors.extend(check_staged_gd_files(repo, files, additions))
    else:
        print("pre-commit: gd_review_check: not a git repo; skipping magic-number policy.")

    if errors:
        print("pre-commit: Godot reviewer checks failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print("pre-commit: Godot reviewer checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
