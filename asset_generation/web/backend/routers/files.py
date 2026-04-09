from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from core.config import settings
from core.path_guard import resolve_src_path

router = APIRouter(prefix="/api/files", tags=["files"])


class FileTreeFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["file"] = "file"
    path: str
    name: str


class FileTreeDir(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["dir"] = "dir"
    path: str
    name: str
    children: list[FileTreeFile | FileTreeDir]


FileTreeNode = FileTreeFile | FileTreeDir


def _build_tree(directory: Path, base: Path) -> list[FileTreeNode]:
    """Recursively build a file tree of .py files."""
    entries: list[FileTreeNode] = []
    try:
        items = sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name))
    except PermissionError:
        return entries

    for item in items:
        rel = item.relative_to(base)
        if item.is_dir():
            children = _build_tree(item, base)
            if children:
                entries.append(
                    FileTreeDir(
                        type="dir",
                        path=str(rel),
                        name=item.name,
                        children=children,
                    ),
                )
        elif item.is_file() and item.suffix == ".py":
            entries.append(FileTreeFile(type="file", path=str(rel), name=item.name))
    return entries


@router.get("")
async def list_files() -> JSONResponse:
    src_root = settings.python_root / "src"
    if not src_root.exists():
        raise HTTPException(status_code=404, detail="src/ directory not found")
    tree = _build_tree(src_root, src_root)
    return JSONResponse({"tree": [n.model_dump() for n in tree]})


@router.get("/{file_path:path}")
async def read_file(file_path: str) -> JSONResponse:
    resolved = resolve_src_path(file_path)
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="File not found")
    content = resolved.read_text(encoding="utf-8")
    return JSONResponse({"path": file_path, "content": content})


class FileWrite(BaseModel):
    content: str


@router.put("/{file_path:path}")
async def write_file(file_path: str, body: FileWrite) -> JSONResponse:
    resolved = resolve_src_path(file_path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    # Atomic write: write to temp file then rename
    fd, tmp_path = tempfile.mkstemp(dir=resolved.parent, prefix=".tmp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(body.content)
        os.replace(tmp_path, resolved)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    return JSONResponse({"path": file_path, "saved": True})
