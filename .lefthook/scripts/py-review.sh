#!/usr/bin/env bash
# Run lightweight Python code review checks on staged files.
# This gate focuses on correctness + import hygiene without requiring a full
# repository reformat/lint migration in one step.
set -euo pipefail

if [ "$#" -eq 0 ]; then
  exit 0
fi

if command -v ruff >/dev/null 2>&1; then
  RUFF_CMD=(ruff)
elif command -v uvx >/dev/null 2>&1; then
  RUFF_CMD=(uvx --from ruff ruff)
else
  echo "pre-commit: ruff is required (install via 'uv tool install ruff' or ensure uvx is available)." >&2
  exit 1
fi

echo "pre-commit: running Python reviewer checks (ruff E9/F/I) on staged files..."
"${RUFF_CMD[@]}" check --select E9,F,I "$@"
