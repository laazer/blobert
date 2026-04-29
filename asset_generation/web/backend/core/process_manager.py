import asyncio
import uuid
from pathlib import Path
from typing import AsyncIterator, Optional


class ProcessManager:
    def __init__(self) -> None:
        self._process: Optional[asyncio.subprocess.Process] = None
        self._run_id: Optional[str] = None

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.returncode is None

    @property
    def run_id(self) -> Optional[str]:
        return self._run_id

    def exit_code(self) -> Optional[int]:
        if self._process is not None:
            return self._process.returncode
        return None

    async def start(self, cmd: list[str], cwd: Path, env: dict[str, str]) -> str:
        if self.is_running:
            raise RuntimeError("A process is already running")
        self._run_id = str(uuid.uuid4())
        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(cwd),
            env=env,
        )
        return self._run_id

    async def stream_output(self) -> AsyncIterator[str]:
        process = self._process
        if process is None or process.stdout is None:
            return
        stdout = process.stdout
        while True:
            line = await stdout.readline()
            if not line:
                break
            yield line.decode("utf-8", errors="replace").rstrip("\n")
        await process.wait()

    async def kill(self) -> None:
        if self._process and self._process.returncode is None:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()
        self._process = None
        self._run_id = None


process_manager = ProcessManager()
