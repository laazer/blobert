from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable

REGISTRY_FILENAME = "model_registry.json"


def registry_path(python_root: Path) -> Path:
    return python_root / REGISTRY_FILENAME


def read_registry_object(python_root: Path) -> dict[str, Any] | None:
    path = registry_path(python_root)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON in {path}: {e}") from e
    if not isinstance(raw, dict):
        raise ValueError("registry file must contain a JSON object")
    return raw


def write_registry_json_atomic(
    python_root: Path,
    data: dict[str, Any],
    *,
    replace_fn: Callable[[str, Path], None] = os.replace,
) -> None:
    path = registry_path(python_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".tmp_model_registry_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        replace_fn(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
