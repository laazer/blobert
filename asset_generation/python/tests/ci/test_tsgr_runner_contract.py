"""MAINT-TSGR: combined runner + exit-code contract (TSGR-1..6).

Spec: project_board/specs/test_suite_green_and_runner_exit_codes_spec.md
Verifier: ci/scripts/verify_tsgr_runner_contract.sh (static; fails until implementation).
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path


def _repo_root() -> Path:
    # .../asset_generation/python/tests/ci/this_file.py → repo root is parents[4].
    return Path(__file__).resolve().parents[4]


def _verifier_script() -> Path:
    return _repo_root() / "ci" / "scripts" / "verify_tsgr_runner_contract.sh"


def test_TSGR_static_combined_runner_contract() -> None:
    root = _repo_root()
    script = _verifier_script()
    assert script.is_file(), f"missing {script}"
    proc = subprocess.run(
        ["bash", str(script)],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    assert "OK (MAINT-TSGR static contract)" in proc.stdout, (
        "success path must print an explicit OK banner (observability / hollow-script guard)"
    )


def test_TSGR_verifier_bash_syntax_ok() -> None:
    # CHECKPOINT: adversarial — catch truncated or merge-broken verifier before runtime surprises.
    script = _verifier_script()
    assert script.is_file()
    subprocess.run(
        ["bash", "-n", str(script)],
        check=True,
        timeout=30,
        capture_output=True,
        text=True,
    )


def test_TSGR_verifier_source_retains_required_probes() -> None:
    # CHECKPOINT: adversarial — if someone replaces the script with `exit 0`, contract tests still fail.
    text = _verifier_script().read_text(encoding="utf-8")
    required = (
        "_check_import_lines",
        "_check_godot_test_run",
        "_check_run_tests_python_phase",
        "_check_run_tests_errexit",
        "_check_claude_md",
        "_check_godot_hook",
        "run_tests.gd",
        "TSGR-2",
        "set -u",
    )
    missing = [frag for frag in required if frag not in text]
    assert not missing, f"verifier missing expected fragments: {missing}"


def test_TSGR_verifier_invocation_independent_of_subprocess_cwd() -> None:
    # CHECKPOINT: adversarial / boundary — ROOT must derive from script location, not caller cwd (mutation: use pwd).
    script = _verifier_script()
    root = _repo_root()
    with tempfile.TemporaryDirectory() as tmp:
        a = subprocess.run(
            ["bash", str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=60,
        )
        b = subprocess.run(
            ["bash", str(script)],
            cwd=tmp,
            capture_output=True,
            text=True,
            timeout=60,
        )
    assert a.returncode == b.returncode, (
        "verifier exit code must not depend on subprocess cwd; "
        f"root cwd={a.returncode}, other cwd={b.returncode}"
    )
    assert a.stderr == b.stderr


def test_TSGR_verifier_process_boundary_observable() -> None:
    # CHECKPOINT: adversarial — forbid silent no-op success/failure (empty stderr on fail, missing banner on pass).
    script = _verifier_script()
    proc = subprocess.run(
        ["bash", str(script)],
        cwd=str(_repo_root()),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode == 0:
        assert "OK (MAINT-TSGR static contract)" in proc.stdout
    else:
        assert proc.returncode == 1
        assert "TSGR contract:" in proc.stderr
        assert "MAINT-TSGR" in proc.stderr


def _non_comment_lines(path: Path) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw.strip()
        if stripped.startswith("#"):
            continue
        lines.append((i, raw))
    return lines


def test_TSGR_run_tests_godot_lines_require_timeout_no_masking() -> None:
    # CHECKPOINT: adversarial — mirror TSGR-4/5 grep rules so a broken bash verifier cannot hide regressions.
    root = _repo_root()
    rt = root / "ci" / "scripts" / "run_tests.sh"
    assert rt.is_file()
    matches: list[tuple[int, str]] = []
    for num, line in _non_comment_lines(rt):
        if re.search(r"run_tests\.gd", line):
            matches.append((num, line))
    assert matches, "expected at least one run_tests.gd invocation in run_tests.sh"
    for num, line in matches:
        assert "timeout" in line, f"run_tests.sh:{num} TSGR-4 Godot test run must use timeout"
        assert "|| true" not in line, f"run_tests.sh:{num} TSGR-5 must not use '|| true' on run_tests.gd line"


def test_TSGR_godot_tests_hook_godot_lines_require_timeout_no_masking() -> None:
    # CHECKPOINT: adversarial — same invariants for lefthook mirror (TSGR-6.2).
    root = _repo_root()
    hook = root / ".lefthook" / "scripts" / "godot-tests.sh"
    assert hook.is_file()
    matches: list[tuple[int, str]] = []
    for num, line in _non_comment_lines(hook):
        if re.search(r"run_tests\.gd", line):
            matches.append((num, line))
    assert matches, "expected run_tests.gd invocation in godot-tests.sh"
    for num, line in matches:
        assert "timeout" in line, f"godot-tests.sh:{num} TSGR-4 Godot test run must use timeout"
        assert "|| true" not in line, f"godot-tests.sh:{num} TSGR-5 must not use '|| true' on run_tests.gd line"


def test_TSGR_when_python_phase_present_godot_before_python_line_order() -> None:
    # CHECKPOINT: adversarial / order — TSGR-1 sequential default: Godot test phase before Python phase.
    root = _repo_root()
    rt = root / "ci" / "scripts" / "run_tests.sh"
    text = rt.read_text(encoding="utf-8")
    if not re.search(r"pytest|py-tests\.sh", text):
        return
    godot_first = None
    py_first = None
    for num, line in _non_comment_lines(rt):
        if godot_first is None and re.search(r"run_tests\.gd", line):
            godot_first = num
        if py_first is None and re.search(r"pytest|py-tests\.sh", line):
            py_first = num
    assert godot_first is not None and py_first is not None
    assert godot_first < py_first, (
        f"TSGR-1 expected Godot test line before Python phase (godot@{godot_first}, python@{py_first})"
    )


def test_TSGR_run_tests_sh_enables_errexit() -> None:
    # CHECKPOINT: adversarial — TSGR-4 shell must not fall through on failure.
    rt = _repo_root() / "ci" / "scripts" / "run_tests.sh"
    text = rt.read_text(encoding="utf-8")
    assert re.search(
        r"(?m)^set -e$|^set -e |^set -euo pipefail|^set -eu$|^set -eu |^set -o errexit",
        text,
    ), "run_tests.sh: TSGR-4 expected 'set -e' (or equivalent errexit)"


def test_TSGR_run_tests_invokes_python_phase_when_present() -> None:
    # CHECKPOINT: adversarial — TSGR-1 mirror for pytest/py-tests presence + path context.
    rt = _repo_root() / "ci" / "scripts" / "run_tests.sh"
    text = rt.read_text(encoding="utf-8")
    assert re.search(r"pytest|py-tests\.sh", text), (
        "run_tests.sh: TSGR-1 expected Python phase (pytest or .lefthook/scripts/py-tests.sh)"
    )
    assert re.search(r"asset_generation/python|tests/", text), (
        "run_tests.sh: TSGR-1 expected Python tests path context (asset_generation/python or tests/)"
    )


def test_TSGR_run_tests_inline_resolver_requires_ci_delegate() -> None:
    # CHECKPOINT: adversarial — TSGR-3 DRY: inline uv/.venv without calling py-tests or ci helper must fail tests.
    root = _repo_root()
    rt = root / "ci" / "scripts" / "run_tests.sh"
    text = rt.read_text(encoding="utf-8")
    if not re.search(r"command -v uv|\.venv/bin/python", text):
        return
    assert re.search(
        r"py-tests\.sh|(bash|source|[.]) .*ci/scripts/[a-z0-9_]+\.sh",
        text,
    ), "TSGR-3: inline .venv/uv resolver must delegate to py-tests.sh or a ci/scripts helper"


def _import_lines(path: Path) -> list[tuple[int, str]]:
    # Align with verify_tsgr_runner_contract.sh: godot/GODOT before --import (incl. "$GODOT" --import).
    out: list[tuple[int, str]] = []
    for num, line in _non_comment_lines(path):
        if re.search(r"(?i)godot.*--import", line):
            out.append((num, line))
    return out


def test_TSGR_run_tests_import_phase_bounded_fail_fast() -> None:
    # CHECKPOINT: adversarial — TSGR-2 mirror for CI script (fails until import is fail-fast).
    root = _repo_root()
    path = root / "ci" / "scripts" / "run_tests.sh"
    rows = _import_lines(path)
    assert rows, "run_tests.sh: TSGR-2 expected a non-comment Godot --import invocation"
    for num, line in rows:
        assert "timeout" in line, f"run_tests.sh:{num} TSGR-2 import must use bounded timeout"
        assert "|| true" not in line, f"run_tests.sh:{num} TSGR-2 import must not use '|| true'"
        assert "2>/dev/null" not in line, f"run_tests.sh:{num} TSGR-2 import must not discard stderr to /dev/null"


def test_TSGR_claude_md_documents_canonical_runner_python_and_failfast() -> None:
    # CHECKPOINT: adversarial — TSGR-6.1/6 mirror; catches doc drift if bash verifier is gutted.
    claude = _repo_root() / "CLAUDE.md"
    assert claude.is_file()
    text = claude.read_text(encoding="utf-8")
    assert "ci/scripts/run_tests.sh" in text, "TSGR-6.1 must name ci/scripts/run_tests.sh as canonical full-suite entry"
    assert re.search(r"asset_generation/python|pytest", text), (
        "TSGR-6.1 must document Python / asset_generation test phase alongside Godot"
    )
    assert re.search(r"fail.fast|fail-fast", text, re.IGNORECASE), (
        "TSGR-6 must summarize bounded fail-fast import policy"
    )


def test_TSGR_godot_tests_hook_import_phase_bounded_fail_fast() -> None:
    # CHECKPOINT: adversarial — TSGR-2 / TSGR-6.2 mirror for lefthook Godot hook.
    root = _repo_root()
    path = root / ".lefthook" / "scripts" / "godot-tests.sh"
    rows = _import_lines(path)
    assert rows, "godot-tests.sh: TSGR-2 expected a non-comment Godot --import invocation"
    for num, line in rows:
        assert "timeout" in line, f"godot-tests.sh:{num} TSGR-2 import must use bounded timeout"
        assert "|| true" not in line, f"godot-tests.sh:{num} TSGR-2 import must not use '|| true'"
        assert "2>/dev/null" not in line, f"godot-tests.sh:{num} TSGR-2 import must not discard stderr to /dev/null"
