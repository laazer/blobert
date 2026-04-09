import json
import os
import sys
from typing import Optional

from core.config import settings
from core.process_manager import process_manager
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/api/run", tags=["run"])

_ALLOWED_CMDS = {"animated", "player", "level", "smart", "stats", "test"}


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
    output_draft: bool = False,
) -> Optional[str]:
    draft_seg = "draft/" if output_draft else ""
    if cmd == "animated" and enemy:
        n = max(1, min(99, int(count) if count is not None else 1))
        last = n - 1
        return f"animated_exports/{draft_seg}{enemy}_animated_{last:02d}.glb"
    if cmd == "test":
        return "animated_exports/spider_animated_00.glb"
    if cmd == "player" and enemy:
        n = max(1, min(99, int(count) if count is not None else 1))
        last = n - 1
        return f"player_exports/{draft_seg}player_slime_{enemy}_{last:02d}.glb"
    if cmd == "level" and enemy:
        n = max(1, min(99, int(count) if count is not None else 1))
        last = n - 1
        return f"level_exports/{draft_seg}{enemy}_{last:02d}.glb"
    return None


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
):
    if cmd not in _ALLOWED_CMDS:
        yield {"event": "error", "data": json.dumps({"exit_code": -1, "message": f"Unknown command: {cmd}"})}
        return

    if process_manager.is_running:
        yield {"event": "error", "data": json.dumps({"exit_code": -1, "message": "A process is already running"})}
        return

    command = _build_command(cmd, enemy, count, description, difficulty, finish, hex_color)

    # Forward BLENDER_PATH and current env into subprocess
    env = os.environ.copy()
    # Ensure the python package src paths are available (main.py sets them itself, but just in case)
    python_root = str(settings.python_root)
    bin_path = str(settings.python_root / "bin")
    src_path = str(settings.python_root / "src")
    env["PYTHONPATH"] = os.pathsep.join([python_root, bin_path, src_path] +
                                         env.get("PYTHONPATH", "").split(os.pathsep))
    if build_options and str(build_options).strip():
        env["BLOBERT_BUILD_OPTIONS_JSON"] = str(build_options).strip()
    if output_draft and cmd in ("animated", "player", "level"):
        env["BLOBERT_EXPORT_USE_DRAFT_SUBDIR"] = "1"

    try:
        run_id = await process_manager.start(command, cwd=settings.python_root, env=env)
    except Exception as e:
        yield {"event": "error", "data": json.dumps({"exit_code": -1, "message": str(e)})}
        return

    async for line in process_manager.stream_output():
        yield {"event": "log", "data": json.dumps({"line": line, "run_id": run_id})}

    exit_code = process_manager.exit_code()
    output_file = _guess_output_file(cmd, enemy, count, output_draft=output_draft)

    if exit_code == 0:
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
        )
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
