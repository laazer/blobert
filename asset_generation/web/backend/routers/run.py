import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Optional

from core.config import settings
from core.process_manager import process_manager
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/run", tags=["run"])

_ALLOWED_CMDS = {"animated", "player", "level", "smart", "stats", "test"}
_EXPORT_START_INDEX_ENV = "BLOBERT_EXPORT_START_INDEX"


def _sync_registry_for_family(family: str) -> None:
    """Register any on-disk GLBs for *family* that are not yet in the manifest.

    Called after a successful animated run so that the new variant is visible
    in the registry immediately (as ``draft: true``) without requiring a manual
    "Add slot → Scanning…" cycle.  Failures are non-fatal — logged and swallowed.
    """
    try:
        from routers.registry import _ensure_python_import_path  # noqa: PLC0415
        _ensure_python_import_path()
        from model_registry import service as reg  # noqa: PLC0415
        reg.sync_discovered_animated_glb_versions(settings.python_root, family)
    except Exception:
        logger.warning("post-run registry sync failed for family %r", family, exc_info=True)


def _next_start_index(export_dir: Path, stem_prefix: str) -> int:
    """Return max existing variant index + 1 for files matching ``{stem_prefix}_*.glb``."""
    indices = []
    for p in export_dir.glob(f"{stem_prefix}_*.glb"):
        m = re.search(r"_(\d{2})$", p.stem)
        if m:
            indices.append(int(m.group(1)))
    return max(indices) + 1 if indices else 0


def _build_command(
    cmd: str,
    enemy: Optional[str],
    count: Optional[int],
    description: Optional[str],
    difficulty: Optional[str],
    finish: Optional[str],
    hex_color: Optional[str],
) -> list[str]:
    parts = [sys.executable, "main.py", cmd]
    if enemy:
        parts.append(enemy)
    if count is not None and cmd not in ("smart", "test"):
        parts.append(str(count))
    if description:
        parts.extend(["--description", description])
    if difficulty:
        parts.extend(["--difficulty", difficulty])
    if cmd in ("player", "animated") and finish:
        parts.extend(["--finish", finish])
    if cmd in ("player", "animated") and hex_color:
        parts.extend(["--hex-color", hex_color])
    return parts


def _guess_output_file(
    cmd: str,
    enemy: Optional[str],
    count: Optional[int],
    *,
    start_index: int = 0,
    output_draft: bool = False,
) -> Optional[str]:
    draft_seg = "draft/" if output_draft else ""
    n = max(1, min(99, int(count) if count is not None else 1))
    last = start_index + n - 1
    if cmd == "animated" and enemy:
        return f"animated_exports/{draft_seg}{enemy}_animated_{last:02d}.glb"
    if cmd == "test":
        return "animated_exports/spider_animated_00.glb"
    if cmd == "player" and enemy:
        return f"player_exports/{draft_seg}player_slime_{enemy}_{last:02d}.glb"
    if cmd == "level" and enemy:
        return f"level_exports/{draft_seg}{enemy}_{last:02d}.glb"
    return None


def _prepare_run_environment(
    cmd: str,
    enemy: Optional[str],
    count: Optional[int],
    description: Optional[str],
    difficulty: Optional[str],
    finish: Optional[str],
    hex_color: Optional[str],
    build_options: Optional[str],
    output_draft: bool,
    replace_variant_index: Optional[int] = None,
) -> tuple[list[str], dict[str, str], int]:
    """Shared command/env/start_index setup for SSE and completion endpoints."""
    command = _build_command(cmd, enemy, count, description, difficulty, finish, hex_color)

    env = os.environ.copy()
    python_root = str(settings.python_root)
    bin_path = str(settings.python_root / "bin")
    src_path = str(settings.python_root / "src")
    env["PYTHONPATH"] = os.pathsep.join([python_root, bin_path, src_path] +
                                         env.get("PYTHONPATH", "").split(os.pathsep))
    if build_options and str(build_options).strip():
        env["BLOBERT_BUILD_OPTIONS_JSON"] = str(build_options).strip()
    if output_draft and cmd in ("animated", "player", "level"):
        env["BLOBERT_EXPORT_USE_DRAFT_SUBDIR"] = "1"

    start_index = 0
    use_fixed_index = (
        replace_variant_index is not None
        and cmd in ("animated", "player", "level")
    )
    if use_fixed_index:
        assert replace_variant_index is not None
        start_index = replace_variant_index
        env[_EXPORT_START_INDEX_ENV] = str(start_index)
    elif cmd == "animated" and enemy and enemy != "all":
        draft_subdir = "draft" if output_draft else ""
        export_dir = settings.python_root / "animated_exports" / draft_subdir if draft_subdir else settings.python_root / "animated_exports"
        start_index = _next_start_index(export_dir, f"{enemy}_animated")
        env[_EXPORT_START_INDEX_ENV] = str(start_index)
    elif cmd == "player" and enemy:
        draft_subdir = "draft" if output_draft else ""
        export_dir = settings.python_root / "player_exports" / draft_subdir if draft_subdir else settings.python_root / "player_exports"
        start_index = _next_start_index(export_dir, f"player_slime_{enemy}")
        env[_EXPORT_START_INDEX_ENV] = str(start_index)

    return command, env, start_index


def _bound_log_text(lines: list[str], max_bytes: int) -> str:
    """Join log lines and truncate UTF-8 tail if over *max_bytes* (APMCP-RUN-3)."""
    text = "\n".join(lines)
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    prefix = "…\n[log truncated — tail only]\n"
    prefix_b = prefix.encode("utf-8")
    budget = max_bytes - len(prefix_b)
    if budget < 1:
        return prefix.strip()
    tail = encoded[-budget:]
    return prefix + tail.decode("utf-8", errors="replace")


async def _run_stream(
    cmd: str,
    enemy: Optional[str],
    count: Optional[int],
    description: Optional[str],
    difficulty: Optional[str],
    finish: Optional[str],
    hex_color: Optional[str],
    build_options: Optional[str],
    output_draft: bool = False,
    replace_variant_index: Optional[int] = None,
):
    if cmd not in _ALLOWED_CMDS:
        yield {"event": "error", "data": json.dumps({"exit_code": -1, "message": f"Unknown command: {cmd}"})}
        return

    if process_manager.is_running:
        yield {"event": "error", "data": json.dumps({"exit_code": -1, "message": "A process is already running"})}
        return

    command, env, start_index = _prepare_run_environment(
        cmd,
        enemy,
        count,
        description,
        difficulty,
        finish,
        hex_color,
        build_options,
        output_draft,
        replace_variant_index=replace_variant_index,
    )

    try:
        run_id = await process_manager.start(command, cwd=settings.python_root, env=env)
    except Exception as e:
        yield {"event": "error", "data": json.dumps({"exit_code": -1, "message": str(e)})}
        return

    async for line in process_manager.stream_output():
        yield {"event": "log", "data": json.dumps({"line": line, "run_id": run_id})}

    exit_code = process_manager.exit_code()
    output_file = _guess_output_file(cmd, enemy, count, start_index=start_index, output_draft=output_draft)

    if exit_code == 0:
        if cmd == "animated" and enemy and enemy != "all":
            _sync_registry_for_family(enemy)
        yield {"event": "done", "data": json.dumps({"exit_code": 0, "output_file": output_file})}
    else:
        yield {"event": "error", "data": json.dumps({"exit_code": exit_code, "message": "Process exited with error"})}


@router.get("/stream")
async def run_stream(
    cmd: str = Query(...),
    enemy: Optional[str] = Query(None),
    count: Optional[int] = Query(None),
    description: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    finish: Optional[str] = Query(None),
    hex_color: Optional[str] = Query(None),
    build_options: Optional[str] = Query(None),
    output_draft: bool = Query(False),
    replace_variant_index: Optional[int] = Query(None, ge=0, le=99),
):
    return EventSourceResponse(
        _run_stream(
            cmd,
            enemy,
            count,
            description,
            difficulty,
            finish,
            hex_color,
            build_options,
            output_draft=output_draft,
            replace_variant_index=replace_variant_index,
        )
    )


@router.get("/complete")
async def run_complete(
    cmd: str = Query(..., description="Pipeline command (same allowlist as /stream)."),
    enemy: Optional[str] = Query(None),
    count: Optional[int] = Query(None),
    description: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    finish: Optional[str] = Query(None),
    hex_color: Optional[str] = Query(None),
    build_options: Optional[str] = Query(None),
    output_draft: bool = Query(False),
    replace_variant_index: Optional[int] = Query(None, ge=0, le=99),
    max_wait_ms: Optional[int] = Query(
        None,
        ge=1,
        description="Max milliseconds to wait for the subprocess to exit. Default and cap from server settings.",
    ),
) -> JSONResponse:
    """Agent-oriented completion: one JSON with bounded logs (GET /api/run/complete)."""
    if cmd not in _ALLOWED_CMDS:
        return JSONResponse(
            status_code=400,
            content={"detail": f"Unknown command: {cmd}"},
        )

    if process_manager.is_running:
        return JSONResponse(
            status_code=409,
            content={
                "detail": "A process is already running",
                "run_id": process_manager.run_id,
            },
        )

    command, env, start_index = _prepare_run_environment(
        cmd,
        enemy,
        count,
        description,
        difficulty,
        finish,
        hex_color,
        build_options,
        output_draft,
        replace_variant_index=replace_variant_index,
    )

    try:
        run_id = await process_manager.start(command, cwd=settings.python_root, env=env)
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={
                "exit_code": -1,
                "log_text": "",
                "output_file": None,
                "run_id": None,
                "message": str(e),
            },
        )

    log_lines: list[str] = []

    async def _drain() -> None:
        async for line in process_manager.stream_output():
            log_lines.append(line)

    drain_task = asyncio.create_task(_drain())
    max_log = settings.run_complete_max_log_bytes
    raw_cap = max_wait_ms if max_wait_ms is not None else settings.run_complete_default_max_wait_ms
    effective_ms = min(raw_cap, settings.run_complete_absolute_max_wait_ms)
    effective_ms = max(1, effective_ms)
    timeout_s = effective_ms / 1000.0

    try:
        await asyncio.wait_for(asyncio.shield(drain_task), timeout=timeout_s)
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=504,
            content={
                "exit_code": None,
                "log_text": _bound_log_text(log_lines, max_log),
                "output_file": None,
                "run_id": run_id,
                "message": (
                    "max_wait_ms exceeded; subprocess may still be running — "
                    "poll GET /api/run/status or POST /api/run/kill"
                ),
                "timed_out": True,
            },
        )

    if not drain_task.done():
        await drain_task

    exit_code = process_manager.exit_code()
    output_file = _guess_output_file(cmd, enemy, count, start_index=start_index, output_draft=output_draft)
    if exit_code == 0:
        if cmd == "animated" and enemy and enemy != "all":
            _sync_registry_for_family(enemy)
        return JSONResponse(
            status_code=200,
            content={
                "exit_code": 0,
                "log_text": _bound_log_text(log_lines, max_log),
                "output_file": output_file,
                "run_id": run_id,
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "exit_code": exit_code,
            "log_text": _bound_log_text(log_lines, max_log),
            "output_file": None,
            "run_id": run_id,
            "message": "Process exited with error",
        },
    )


@router.post("/kill")
async def kill_process() -> JSONResponse:
    if not process_manager.is_running:
        return JSONResponse({"killed": False, "message": "No process running"})
    await process_manager.kill()
    return JSONResponse({"killed": True})


@router.get("/status")
async def run_status() -> JSONResponse:
    return JSONResponse({
        "is_running": process_manager.is_running,
        "run_id": process_manager.run_id,
    })
