"""MAINT-TSGR: combined runner + exit-code contract (TSGR-1..6).

Spec: project_board/specs/test_suite_green_and_runner_exit_codes_spec.md
Verifier: ci/scripts/verify_tsgr_runner_contract.sh (static; fails until implementation).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def _repo_root() -> Path:
    # .../asset_generation/python/tests/ci/this_file.py → repo root is parents[4].
    return Path(__file__).resolve().parents[4]


def test_TSGR_static_combined_runner_contract() -> None:
    root = _repo_root()
    script = root / "ci" / "scripts" / "verify_tsgr_runner_contract.sh"
    assert script.is_file(), f"missing {script}"
    proc = subprocess.run(
        ["bash", str(script)],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
