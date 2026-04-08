#!/usr/bin/env python3
"""Block unexplained numeric literals on staged *added* GDScript lines (CLAUDE.md Code review agents)."""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path
from typing import List, Tuple

from precommit_git_diff import git_diff_cached, git_repo_root, parse_staged_additions

# Tuning / domain literals; exempt trivial identities per CLAUDE.md (subset safe for automation).
_EXEMPT_INTS = frozenset({-1, 0, 1, 2})
_EXEMPT_FLOATS = frozenset({0.0, 1.0, -1.0, 2.0})

_NUM_RE = re.compile(
    r"(?<![.\w])"
    r"(-?(?:\d+\.\d+(?:[eE][+-]?\d+)?|\d+(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?))"
    r"(?!\w)"
)

_SKIP_LINE_PREFIXES = (
    "##",  # doc comment line
)

_SKIP_LINE_START_RE = re.compile(
    r"^\s*(?:@export\b|const\s|enum\s|class_name\s|signal\s|extends\s|func\s|static\s+func\s)"
)


def _strip_gd_strings(line: str) -> str:
    out: List[str] = []
    i = 0
    n = len(line)
    while i < n:
        c = line[i]
        if c in "\"'":
            quote = c
            out.append(" ")
            i += 1
            while i < n:
                if line[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                if line[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _scan_line_for_magic(line: str) -> List[str]:
    stripped = line.strip()
    if not stripped or stripped.lstrip().startswith("#"):
        return []
    if any(stripped.startswith(p) for p in _SKIP_LINE_PREFIXES):
        return []
    if _SKIP_LINE_START_RE.match(line):
        return []

    no_strings = _strip_gd_strings(line)
    if "#" in no_strings:
        no_strings = no_strings[: no_strings.index("#")]
    scan = no_strings.strip()
    if not scan:
        return []

    hits: List[str] = []
    for m in _NUM_RE.finditer(scan):
        raw = m.group(1)
        try:
            val = float(raw)
        except ValueError:
            continue
        if math.isfinite(val) and val == int(val):
            iv = int(val)
            if iv in _EXEMPT_INTS:
                continue
        elif any(math.isclose(val, e, rel_tol=0.0, abs_tol=1e-9) for e in _EXEMPT_FLOATS):
            continue
        hits.append(raw)
    return hits


def check_staged_gd_files(repo: Path, paths: List[Path], additions: dict) -> List[str]:
    errors: List[str] = []
    for p in paths:
        if p.suffix != ".gd":
            continue
        try:
            rel_posix = p.resolve().relative_to(repo).as_posix()
        except ValueError:
            rel_posix = p.as_posix()

        if rel_posix.startswith("tests/") or rel_posix.startswith("reference_projects/"):
            continue

        added = additions.get(rel_posix)
        if not added:
            continue

        for lineno, body in added:
            bad = _scan_line_for_magic(body)
            for token in bad:
                errors.append(
                    f"{rel_posix}:{lineno}: numeric literal `{token}` — name it "
                    f"(const / @export) or adjust line; see CLAUDE.md Code review agents → GDScript"
                )
    return errors


def main(argv: List[str]) -> int:
    repo = git_repo_root()
    if repo is None:
        print("pre-commit: gd_magic_number_check: not a git repo; skipping magic-number policy.")
        return 0

    paths = [Path(a) for a in argv[1:] if a.endswith(".gd")]
    if not paths:
        return 0

    diff = git_diff_cached(repo)
    additions = parse_staged_additions(diff)
    errors = check_staged_gd_files(repo, paths, additions)

    if errors:
        print("pre-commit: GDScript magic-number policy failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print("pre-commit: GDScript magic-number policy passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
