#!/usr/bin/env bash
# Run Pylint (too-many-statements) on staged Python under asset_generation/python/ using
# asset_generation/python/pyproject.toml [tool.pylint.*].
set -euo pipefail

if [ "$#" -eq 0 ]; then
  exit 0
fi

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY_ROOT="$ROOT/asset_generation/python"
# Keep Pylint stats/cache inside the project (avoids $HOME/Caches and sandbox issues in CI).
export PYLINTHOME="${PYLINTHOME:-$PY_ROOT/.pylint_home}"

if [ ! -f "$PY_ROOT/pyproject.toml" ]; then
  echo "pre-commit: missing Pylint config at $PY_ROOT/pyproject.toml" >&2
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
      ;;
  esac
done

if [ "${#rel_args[@]}" -eq 0 ]; then
  exit 0
fi

cd "$PY_ROOT"

if [ -x ".venv/bin/pylint" ]; then
  PYLINT_CMD=(".venv/bin/pylint")
elif command -v uv >/dev/null 2>&1; then
  PYLINT_CMD=(uv run --extra dev pylint)
elif command -v pylint >/dev/null 2>&1; then
  PYLINT_CMD=(pylint)
else
  echo "pre-commit: pylint is required (uv sync --extra dev in asset_generation/python)." >&2
  exit 1
fi

echo "pre-commit: running Pylint (too-many-statements, pyproject.toml) on staged files..."
"${PYLINT_CMD[@]}" "${rel_args[@]}"
