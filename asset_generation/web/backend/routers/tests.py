import json
import os
import sys

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from core.config import settings
from core.process_manager import ProcessManager

router = APIRouter(prefix="/api/tests", tags=["tests"])

# Separate process manager so pytest doesn't conflict with run
_test_manager = ProcessManager()


async def _test_stream():
    if _test_manager.is_running:
        yield {"event": "error", "data": json.dumps({"exit_code": -1, "message": "Tests already running"})}
        return

    command = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]
    env = os.environ.copy()

    try:
        run_id = await _test_manager.start(command, cwd=settings.python_root, env=env)
    except Exception as e:
        yield {"event": "error", "data": json.dumps({"exit_code": -1, "message": str(e)})}
        return

    async for line in _test_manager.stream_output():
        yield {"event": "log", "data": json.dumps({"line": line, "run_id": run_id})}

    exit_code = _test_manager.exit_code()
    if exit_code == 0:
        yield {"event": "done", "data": json.dumps({"exit_code": 0, "output_file": None})}
    else:
        yield {"event": "error", "data": json.dumps({"exit_code": exit_code, "message": "Tests failed"})}


@router.get("/stream")
async def test_stream():
    return EventSourceResponse(_test_stream())
