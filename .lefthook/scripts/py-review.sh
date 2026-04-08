#!/usr/bin/env bash
# Run Ruff on staged Python files using asset_generation/python/pyproject.toml.
# Rule set: [tool.ruff.lint] select (E9, F, I) — standard tooling; GDScript policy
# stays in .lefthook/scripts/gd_*.
#
# Always runs from PY_ROOT with paths relative to that dir so isort/first-party
# resolution matches `cd asset_generation/python && ruff check`.
set -euo pipefail

if [ "$#" -eq 0 ]; then
  exit 0
fi

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY_ROOT="$ROOT/asset_generation/python"

if [ ! -f "$PY_ROOT/pyproject.toml" ]; then
  echo "pre-commit: missing Ruff config at $PY_ROOT/pyproject.toml" >&2
  exit 1
fi

if [ -x "$PY_ROOT/.venv/bin/ruff" ]; then
  RUFF_CMD=("$PY_ROOT/.venv/bin/ruff")
elif command -v uv >/dev/null 2>&1; then
  RUFF_CMD=(uv run --extra dev ruff)
elif command -v ruff >/dev/null 2>&1; then
  RUFF_CMD=(ruff)
elif command -v uvx >/dev/null 2>&1; then
  RUFF_CMD=(uvx --from ruff ruff)
else
  echo "pre-commit: ruff is required (uv sync --extra dev in asset_generation/python)." >&2
  exit 1
fi

rel_args=()
for f in "$@"; do
  case "$f" in
    "$PY_ROOT"/*)
      rel_args+=("${f#"$PY_ROOT"/}")
      ;;
    */asset_generation/python/*)
      rel_args+=("${f##*asset_generation/python/}")
      ;;
    asset_generation/python/*)
      rel_args+=("${f#asset_generation/python/}")
      ;;
    *)
      # Staged Python outside asset_generation/python (e.g. web backend) uses its own tooling.
      ;;
  esac
done

if [ "${#rel_args[@]}" -eq 0 ]; then
  exit 0
fi

echo "pre-commit: running Ruff (from pyproject.toml) on staged files..."
cd "$PY_ROOT"
if [ "${RUFF_CMD[0]}" = "uv" ]; then
  uv run --extra dev ruff check --config pyproject.toml "${rel_args[@]}"
else
  "${RUFF_CMD[@]}" check --config pyproject.toml "${rel_args[@]}"
fi
