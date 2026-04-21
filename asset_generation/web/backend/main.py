"""
FastAPI backend for the Live Asset Editor.
"""
from __future__ import annotations

import sys
from pathlib import Path

def _bootstrap_asset_generation_python_path() -> None:
    """Expose ``asset_generation/python`` and ``.../python/src`` for ``src.*`` and legacy flat imports."""
    backend_dir = Path(__file__).resolve().parent
    python_root = backend_dir.parent.parent / "python"
    src_dir = python_root / "src"
    for p in (str(python_root), str(src_dir)):
        if p not in sys.path:
            sys.path.insert(0, p)


_bootstrap_asset_generation_python_path()

from core.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import assets, files, meta, registry, run

app = FastAPI(title="Blobert Asset Editor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(files.router)
app.include_router(run.router)
app.include_router(assets.router)
app.include_router(meta.router)
app.include_router(registry.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
