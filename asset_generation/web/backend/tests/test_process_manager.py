from __future__ import annotations

import asyncio

from core.process_manager import ProcessManager


class _Stdout:
    def __init__(self, lines: list[bytes]) -> None:
        self._lines = list(lines)

    async def readline(self) -> bytes:
        await asyncio.sleep(0)
        if self._lines:
            return self._lines.pop(0)
        return b""


class _Proc:
    def __init__(self, lines: list[bytes]) -> None:
        self.stdout = _Stdout(lines)
        self.returncode: int | None = 0

    async def wait(self) -> int:
        await asyncio.sleep(0)
        return 0


def test_stream_output_uses_stable_process_snapshot() -> None:
    async def _run() -> None:
        pm = ProcessManager()
        pm._process = _Proc([b"alpha\n", b"beta\n"])  # type: ignore[assignment]
        lines: list[str] = []
        async for line in pm.stream_output():
            lines.append(line)
            # Simulate concurrent kill/reset while stream is active.
            pm._process = None
        assert lines == ["alpha", "beta"]

    asyncio.run(_run())
