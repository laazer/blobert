import asyncio
import json
import logging
from typing import Optional

from core.config import settings
from core.process_manager import process_manager
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from services.error_mapping import map_exception_to_http
from services.python_bridge import bootstrap_python_runtime, import_asset_module
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/run", tags=["run"])
bootstrap_python_runtime()
run_contract = import_asset_module("src.utils.run_contract")


def _sync_registry_for_family(family: str) -> None:
    """Register any on-disk GLBs for *family* that are not yet in the manifest.

    Called after a successful animated run so that the new variant is visible
    in the registry immediately (as ``draft: true``) without requiring a manual
    "Add slot → Scanning…" cycle.  Failures are non-fatal — logged and swallowed.
    """
    try:
        bootstrap_python_runtime()
        reg = import_asset_module("src.model_registry.service")
        reg.sync_discovered_animated_glb_versions(settings.python_root, family)
    except Exception:
        logger.warning("post-run registry sync failed for family %r", family, exc_info=True)


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
    if not run_contract.is_allowed_command(cmd):
        yield {"event": "error", "data": json.dumps({"exit_code": -1, "message": f"Unknown command: {cmd}"})}
        return

    if process_manager.is_running:
        yield {"event": "error", "data": json.dumps({"exit_code": -1, "message": "A process is already running"})}
        return

    command, env, start_index = run_contract.prepare_run_environment(
        python_root=settings.python_root,
        cmd=cmd,
        enemy=enemy,
        count=count,
        description=description,
        difficulty=difficulty,
        finish=finish,
        hex_color=hex_color,
        build_options=build_options,
        output_draft=output_draft,
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
    output_file = run_contract.predict_output_file(
        cmd=cmd,
        enemy=enemy,
        count=count,
        start_index=start_index,
        output_draft=output_draft,
    )

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
    if not run_contract.is_allowed_command(cmd):
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

    command, env, start_index = run_contract.prepare_run_environment(
        python_root=settings.python_root,
        cmd=cmd,
        enemy=enemy,
        count=count,
        description=description,
        difficulty=difficulty,
        finish=finish,
        hex_color=hex_color,
        build_options=build_options,
        output_draft=output_draft,
        replace_variant_index=replace_variant_index,
    )

    try:
        run_id = await process_manager.start(command, cwd=settings.python_root, env=env)
    except Exception as e:
        if isinstance(e, OSError):
            return JSONResponse(
                status_code=200,
                content={"exit_code": -1, "message": str(e)},
            )
        mapped = map_exception_to_http(
            e,
            route="/api/run/complete",
            logger=logger,
            rules=(),
        )
        return JSONResponse(
            status_code=mapped.status_code,
            content={"detail": mapped.detail},
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
    output_file = run_contract.predict_output_file(
        cmd=cmd,
        enemy=enemy,
        count=count,
        start_index=start_index,
        output_draft=output_draft,
    )
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
