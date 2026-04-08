#!/usr/bin/env python3
"""Batch-migrate simulate() detach arguments to array-only form (8-arg API)."""
from __future__ import annotations

import sys
from pathlib import Path


def split_top_level_commas(s: str) -> list[str]:
    parts: list[str] = []
    depth_paren = depth_bracket = 0
    start = 0
    for i, c in enumerate(s):
        if c == "(":
            depth_paren += 1
        elif c == ")":
            depth_paren -= 1
        elif c == "[":
            depth_bracket += 1
        elif c == "]":
            depth_bracket -= 1
        elif c == "," and depth_paren == 0 and depth_bracket == 0:
            parts.append(s[start:i].strip())
            start = i + 1
    parts.append(s[start:].strip())
    return parts


def find_simulate_calls(text: str) -> list[tuple[int, int, str]]:
    out: list[tuple[int, int, str]] = []
    i = 0
    while True:
        idx = text.find("simulate(", i)
        if idx == -1:
            break
        if idx >= 5 and text[idx - 5 : idx] == "func ":
            i = idx + 1
            continue
        if idx > 0 and (text[idx - 1].isalnum() or text[idx - 1] == "_"):
            i = idx + 1
            continue
        open_paren = idx + len("simulate")
        assert text[open_paren] == "("
        depth = 1
        k = open_paren + 1
        while k < len(text):
            if text[k] == "(":
                depth += 1
            elif text[k] == ")":
                depth -= 1
                if depth == 0:
                    inner = text[open_paren + 1 : k]
                    out.append((open_paren, k, inner))
                    i = k + 1
                    break
            k += 1
        else:
            break
    return out


def transform_inner(inner: str) -> str | None:
    parts = split_top_level_commas(inner)
    if len(parts) == 8:
        if parts[6].startswith("["):
            return None
        return ", ".join(parts[:6] + [f"[{parts[6]}, false]"] + [parts[7]])
    if len(parts) == 9:
        return ", ".join(parts[:6] + [f"[{parts[6]}, {parts[8]}]"] + [parts[7]])
    return None


def process_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    calls = find_simulate_calls(text)
    if not calls:
        return False
    new_text = text
    for open_paren, close_paren, inner in reversed(calls):
        repl = transform_inner(inner)
        if repl is None:
            continue
        new_text = new_text[: open_paren + 1] + repl + new_text[close_paren:]
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    targets: list[Path] = []
    for pat in ("tests/**/*.gd", "scripts/**/*.gd"):
        targets.extend(root.glob(pat))
    changed_any = False
    for p in sorted(set(targets)):
        if p.name == "migrate_simulate_detach_array.py":
            continue
        if process_file(p):
            print(f"updated: {p.relative_to(root)}")
            changed_any = True
    if not changed_any:
        print("no changes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
