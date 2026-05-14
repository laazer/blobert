#!/usr/bin/env python3
"""
Gate runner — executes named validation gates and emits structured JSON results.

Usage:
    python ci/scripts/gate_runner.py <gate_name> \\
        --upstream-agent <name> \\
        --downstream-agent <name> \\
        --ticket-id <id> \\
        [--mode shadow|blocking] \\
        [--input <json>] \\
        [--output-dir <path>]

Exit codes:
    0  — gate passed or shadow mode (non-blocking)
    1  — gate failed in blocking mode
    2  — usage error
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict

_REGISTRY_DEFAULT = Path(__file__).resolve().parent / "gate_registry.json"
_GATES_PKG = Path(__file__).resolve().parent / "gates"


class _GateRegistryEntry(TypedDict, total=False):
    """Typed contract for a single gate registry entry."""
    name: str
    module: str
    required_inputs: list[str]
    default_mode: str
    description: str
    category: str


def _load_registry() -> list[dict[str, Any]]:
    path = Path(os.environ.get("GATE_REGISTRY_PATH", str(_REGISTRY_DEFAULT)))
    if not path.exists():
        print(f"ERROR: gate registry not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        print(f"ERROR: gate registry is invalid JSON: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, list):
        print("ERROR: gate registry must be a JSON array", file=sys.stderr)
        sys.exit(2)
    return data


def _find_gate(registry: list[dict[str, Any]], name: str) -> _GateRegistryEntry | None:
    for entry in registry:
        if not isinstance(entry, dict):
            continue
        if entry.get("name") == name:
            return entry
    return None


def _run_gate(gate_entry: _GateRegistryEntry, inputs: dict[str, Any], mode: str) -> dict[str, Any]:
    module_name = gate_entry.get("module", "")
    module_path = _GATES_PKG / f"{module_name}.py"

    if not module_path.exists():
        return {
            "status": "FAIL",
            "message": f"Gate module not found: {module_path}",
            "violations": [
                {
                    "file": str(module_path),
                    "line": 0,
                    "rule": "module_missing",
                    "message": f"Gate module file does not exist: {module_path}",
                    "severity": "ERROR",
                }
            ],
            "remediation_hints": [f"Create {module_path} or update the registry entry."],
        }

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        return {
            "status": "FAIL",
            "message": f"Could not load gate module: {module_name}",
            "violations": [
                {
                    "file": str(module_path),
                    "line": 0,
                    "rule": "module_load",
                    "message": f"Failed to load module: {module_name}",
                    "severity": "ERROR",
                }
            ],
            "remediation_hints": [f"Check that {module_path} is valid Python."],
        }

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    run_fn = getattr(mod, "run", None)
    if run_fn is None:
        return {
            "status": "FAIL",
            "message": f"Gate module missing run() function: {module_name}",
            "violations": [
                {
                    "file": str(module_path),
                    "line": 0,
                    "rule": "run_missing",
                    "message": f"Module {module_name} does not define run(inputs)",
                    "severity": "ERROR",
                }
            ],
            "remediation_hints": [f"Add a run(inputs) -> dict function to {module_name}."],
        }

    try:
        result = run_fn(inputs)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as exc:
        return {
            "status": "FAIL",
            "message": f"Gate raised: {exc}",
            "violations": [
                {
                    "file": str(module_path),
                    "line": 0,
                    "rule": "gate_exception",
                    "message": str(exc),
                    "severity": "ERROR",
                }
            ],
            "remediation_hints": [f"Fix the error in gate module {module_name}."],
        }

    if not isinstance(result, dict):
        return {
            "status": "FAIL",
            "message": f"Gate returned non-dict: {type(result).__name__}",
            "violations": [
                {
                    "file": str(module_path),
                    "line": 0,
                    "rule": "invalid_return",
                    "message": f"run() must return a dict, got {type(result).__name__}",
                    "severity": "ERROR",
                }
            ],
            "remediation_hints": [f"Update {module_name}.run() to return a dict."],
        }

    return result


def _write_result(output_dir: Path, gate_name: str, result: dict[str, Any]) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{gate_name}_{ts}.json"
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        print(f"WARNING: gate_runner: failed to create output directory {output_dir}", file=sys.stderr)
        raise
    out_path = output_dir / filename
    try:
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    except OSError:
        print(f"WARNING: gate_runner: failed to write result to {out_path}", file=sys.stderr)
        raise
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="gate_runner",
        description="Execute validation gates and emit structured JSON results.",
    )
    parser.add_argument("gate_name", help="Name of the gate to run (must be registered).")
    parser.add_argument("--upstream-agent", required=True, help="Name of the upstream agent.")
    parser.add_argument("--downstream-agent", required=True, help="Name of the downstream agent.")
    parser.add_argument("--ticket-id", required=True, help="Ticket ID for this gate run.")
    parser.add_argument(
        "--mode",
        choices=["shadow", "blocking"],
        default="shadow",
        help="Execution mode (default: shadow).",
    )
    parser.add_argument(
        "--input",
        default=None,
        help="Inline JSON input for the gate. Omitted → empty dict.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to write result JSON. Default: ./gate-results.",
    )

    args = parser.parse_args()

    gate_name = args.gate_name
    if not gate_name or not gate_name.strip():
        print("ERROR: gate name must not be empty.", file=sys.stderr)
        return 2

    registry = _load_registry()
    gate_entry = _find_gate(registry, gate_name)
    if gate_entry is None:
        print(f"ERROR: unknown gate '{gate_name}' not found in registry.", file=sys.stderr)
        return 2

    inputs: dict[str, Any] = {}
    if args.input is not None:
        try:
            inputs = json.loads(args.input)
        except json.JSONDecodeError as exc:
            print(f"ERROR: invalid --input JSON: {exc}", file=sys.stderr)
            return 2
        if inputs is None:
            inputs = {}
        if not isinstance(inputs, dict):
            print("ERROR: --input must be a JSON object (dict).", file=sys.stderr)
            return 2

    # Validate spec_file exists before running gate (usage error = exit 2)
    spec_file = inputs.get("spec_file")
    spec_missing = False
    if spec_file is not None:
        spec_path = Path(spec_file)
        if not spec_path.exists():
            spec_missing = True

    mode = args.mode
    output_dir = Path(args.output_dir) if args.output_dir else Path("./gate-results")

    start = time.monotonic()
    raw_result = _run_gate(gate_entry, inputs, mode)
    duration_ms = int((time.monotonic() - start) * 1000)

    result = {
        "version": "0.1.0",
        "status": raw_result.get("status", "FAIL"),
        "gate": gate_name,
        "upstream_agent": args.upstream_agent,
        "downstream_agent": args.downstream_agent,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "ticket_id": args.ticket_id,
        "mode": mode,
        "_shadow_mode": mode == "shadow",
        "artifacts": raw_result.get("artifacts", []),
        "duration_ms": duration_ms,
        "message": raw_result.get("message", ""),
    }

    if "violations" in raw_result:
        result["violations"] = raw_result["violations"]
    if "remediation_hints" in raw_result:
        result["remediation_hints"] = raw_result["remediation_hints"]

    _write_result(output_dir, gate_name, result)

    print(f"gate-runner: {gate_name} → {result['status']}  ({duration_ms}ms)")

    if spec_missing:
        if mode == "blocking":
            return 2
        # Shadow mode: log the issue but do not block CI
        print(f"WARNING: gate_runner: spec file not found: {spec_file}", file=sys.stderr)

    if mode == "blocking" and result["status"] == "FAIL":
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
