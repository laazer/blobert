#!/usr/bin/env python3
"""Organization guardrails for staged GDScript files."""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

MAX_FILE_LINES = 900
MAX_FUNCTION_LINES = 180
MAX_CLASS_LINES = 450
MIN_DUPLICATE_BODY_LINES = 8

CLASS_RE = re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)")
FUNC_RE = re.compile(r"^\s*func\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def indent_level(line: str) -> int:
    expanded = line.replace("\t", "    ")
    return len(expanded) - len(expanded.lstrip(" "))


def block_end(lines: List[str], start_idx: int, block_indent: int) -> int:
    idx = start_idx + 1
    while idx < len(lines):
        raw = lines[idx]
        stripped = raw.strip()
        if stripped == "" or stripped.startswith("#"):
            idx += 1
            continue
        if indent_level(raw) <= block_indent:
            return idx - 1
        idx += 1
    return len(lines) - 1


def find_class_spans(lines: List[str]) -> List[Tuple[str, int, int]]:
    spans: List[Tuple[str, int, int]] = []
    for idx, line in enumerate(lines):
        match = CLASS_RE.match(line)
        if not match:
            continue
        start = idx
        end = block_end(lines, start, indent_level(line))
        spans.append((match.group(1), start + 1, end + 1))
    return spans


def find_function_spans(lines: List[str]) -> List[Tuple[str, int, int]]:
    spans: List[Tuple[str, int, int]] = []
    for idx, line in enumerate(lines):
        match = FUNC_RE.match(line)
        if not match:
            continue
        start = idx
        end = block_end(lines, start, indent_level(line))
        spans.append((match.group(1), start + 1, end + 1))
    return spans


def normalized_body(lines: List[str], start: int, end: int) -> List[str]:
    # start/end are 1-based inclusive; body starts after signature line.
    out: List[str] = []
    for raw in lines[start:end]:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        out.append(" ".join(stripped.split()))
    return out


def duplicate_function_groups(lines: List[str]) -> List[List[Tuple[str, int]]]:
    buckets = {}
    for func_name, start, end in find_function_spans(lines):
        body = normalized_body(lines, start, end)
        if len(body) < MIN_DUPLICATE_BODY_LINES:
            continue
        key = tuple(body)
        buckets.setdefault(key, []).append((func_name, start))
    return [group for group in buckets.values() if len(group) > 1]


def function_keys_for_file(path: Path) -> List[Tuple[Tuple[str, ...], str, int]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    keys: List[Tuple[Tuple[str, ...], str, int]] = []
    for func_name, start, end in find_function_spans(lines):
        body = normalized_body(lines, start, end)
        if len(body) < MIN_DUPLICATE_BODY_LINES:
            continue
        keys.append((tuple(body), func_name, start))
    return keys


def build_codebase_catalog(changed_files: List[Path]) -> Dict[Tuple[str, ...], List[Tuple[str, str, int]]]:
    changed_set = {p.resolve() for p in changed_files if p.exists()}
    catalog: Dict[Tuple[str, ...], List[Tuple[str, str, int]]] = {}
    for gd_file in Path(".").rglob("*.gd"):
        resolved = gd_file.resolve()
        if resolved in changed_set:
            continue
        for key, func_name, lineno in function_keys_for_file(gd_file):
            catalog.setdefault(key, []).append((gd_file.as_posix(), func_name, lineno))
    return catalog


def codebase_dry_errors(
    changed_files: List[Path], catalog: Dict[Tuple[str, ...], List[Tuple[str, str, int]]]
) -> List[str]:
    errors: List[str] = []
    for gd_file in changed_files:
        for key, func_name, lineno in function_keys_for_file(gd_file):
            matches = catalog.get(key, [])
            if not matches:
                continue
            refs = ", ".join(f"{path}:{name}@{line}" for path, name, line in matches[:3])
            errors.append(
                f"{gd_file}:{lineno}: function `{func_name}` duplicates existing code ({refs}); reuse existing logic to keep DRY"
            )
    return errors


def class_name_declared(lines: List[str]) -> bool:
    for line in lines:
        if line.startswith("class_name "):
            return True
    return False


def check_file(path: Path) -> List[str]:
    errors: List[str] = []
    if not path.exists():
        return errors

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    if len(lines) > MAX_FILE_LINES:
        errors.append(
            f"{path}: file is {len(lines)} lines (max {MAX_FILE_LINES}); split into smaller scripts"
        )

    path_posix = path.as_posix()
    if path_posix.startswith("scripts/"):
        if not class_name_declared(lines):
            errors.append(f"{path}: scripts should declare class_name for discoverability")

    for class_name, start, end in find_class_spans(lines):
        span = end - start + 1
        if span > MAX_CLASS_LINES:
            errors.append(
                f"{path}:{start}: class `{class_name}` is {span} lines (max {MAX_CLASS_LINES})"
            )

    for func_name, start, end in find_function_spans(lines):
        span = end - start + 1
        if span > MAX_FUNCTION_LINES:
            errors.append(
                f"{path}:{start}: function `{func_name}` is {span} lines (max {MAX_FUNCTION_LINES})"
            )

    for funcs in duplicate_function_groups(lines):
        refs = ", ".join(f"{name}@{line}" for name, line in funcs)
        errors.append(
            f"{path}: duplicated function bodies detected ({refs}); extract shared helper to keep DRY"
        )

    return errors


def main(argv: List[str]) -> int:
    files = [Path(arg) for arg in argv[1:] if arg.endswith(".gd")]
    if not files:
        return 0

    errors: List[str] = []
    codebase_catalog = build_codebase_catalog(files)
    for file_path in files:
        errors.extend(check_file(file_path))
    errors.extend(codebase_dry_errors(files, codebase_catalog))

    if errors:
        print("pre-commit: Godot organization checks failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print("pre-commit: Godot organization checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
