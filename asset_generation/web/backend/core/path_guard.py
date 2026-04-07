from pathlib import Path
from fastapi import HTTPException

from .config import settings


def resolve_src_path(rel_path: str) -> Path:
    """Resolve a client-supplied path within src/. Rejects traversal escapes and non-.py files."""
    src_root = (settings.python_root / "src").resolve()
    try:
        resolved = (src_root / rel_path).resolve()
        resolved.relative_to(src_root)
    except (ValueError, OSError):
        raise HTTPException(status_code=400, detail="Path outside src/ directory")
    if resolved.suffix != ".py":
        raise HTTPException(status_code=400, detail="Only .py files are allowed")
    return resolved
