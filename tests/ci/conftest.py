"""
Root conftest for tests/ci/ — shared fixtures for gate framework tests.

Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/01_validation_gate_framework.md
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Repo root (tests/ci/ is under tests/ which is under repo root)
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
CI_SCRIPTS = _REPO_ROOT / "ci" / "scripts"
GATE_RUNNER = CI_SCRIPTS / "gate_runner.py"
GATE_REGISTRY = CI_SCRIPTS / "gate_registry.json"
GATE_SCHEMAS = CI_SCRIPTS / "gate_schemas"
GATES_PKG = CI_SCRIPTS / "gates"
CHECKPOINTS = _REPO_ROOT / "project_board" / "checkpoints"


@pytest.fixture()
def repo_root() -> Path:
    return _REPO_ROOT


@pytest.fixture()
def gate_runner() -> Path:
    return GATE_RUNNER


@pytest.fixture()
def gate_registry() -> Path:
    return GATE_REGISTRY


@pytest.fixture()
def gate_schemas() -> Path:
    return GATE_SCHEMAS


@pytest.fixture()
def gates_pkg() -> Path:
    return GATES_PKG


@pytest.fixture()
def checkpoints() -> Path:
    return CHECKPOINTS


@pytest.fixture()
def tmp_gate_results(tmp_path: Path) -> Path:
    """Create a temp output dir mimicking checkpoints/<ticket-id>/gate-results/."""
    d = tmp_path / "gate-results"
    d.mkdir(parents=True)
    return d


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_gate_runner(
    *extra_args: str,
    input_json: str | None = None,
    output_dir: str | None = None,
    ticket_id: str = "M902-01",
) -> subprocess.CompletedProcess[str]:
    """Run gate_runner.py and return the CompletedProcess.

    Args:
        extra_args: Additional CLI arguments (gate name, --mode, etc.).
        input_json: Inline JSON to pass as --input.
        output_dir: Override --output-dir.
        ticket_id: Ticket ID for default output path.
    """
    cmd = [sys.executable, str(GATE_RUNNER), *extra_args]
    if input_json is not None:
        cmd += ["--input", input_json]
    if output_dir is not None:
        cmd += ["--output-dir", output_dir]
    cmd += ["--ticket-id", ticket_id]
    # Ensure --mode is not set (tests should control this explicitly)
    env = {**dict(__import__("os").environ)}
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def load_json(path: Path) -> dict[str, Any]:
    """Load and return parsed JSON from *path*."""
    return json.loads(path.read_text())
