"""
FastAPI backend for the Live Asset Editor.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from routers import files, run, assets, meta, tests

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
app.include_router(tests.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
