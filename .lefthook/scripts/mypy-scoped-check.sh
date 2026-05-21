#!/usr/bin/env bash
# Strict mypy on the scoped module manifest (ci/scripts/mypy_scoped_modules.txt).
# Invoked from py-tests.sh; shares the asset_generation/python venv with Ruff/pytest.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY_ROOT="$ROOT/asset_generation/python"
MANIFEST="$ROOT/ci/scripts/mypy_scoped_modules.txt"

if [[ ! -f "$MANIFEST" ]]; then
  echo "pre-push: missing mypy manifest at $MANIFEST" >&2
  exit 1
fi

_MYPY_TARGETS=()
while IFS= read -r rel; do
  [[ -z "$rel" ]] && continue
  _MYPY_TARGETS+=("$rel")
done < <(grep -vE '^\s*($|#)' "$MANIFEST")

if [[ "${#_MYPY_TARGETS[@]}" -eq 0 ]]; then
  echo "pre-push: mypy manifest has no targets: $MANIFEST" >&2
  exit 1
fi

for rel in "${_MYPY_TARGETS[@]}"; do
  if [[ ! -f "$PY_ROOT/$rel" ]]; then
    echo "pre-push: mypy manifest path missing: $PY_ROOT/$rel" >&2
    exit 1
  fi
done

if [[ -x "$PY_ROOT/.venv/bin/mypy" ]]; then
  MYPY_CMD=("$PY_ROOT/.venv/bin/mypy")
elif command -v uv >/dev/null 2>&1; then
  MYPY_CMD=(uv run --extra dev mypy)
else
  echo "pre-push: mypy required (uv sync --extra dev in asset_generation/python)." >&2
  exit 1
fi

echo "pre-push: running mypy --strict --follow-imports=skip on ${#_MYPY_TARGETS[@]} scoped module(s)..."
cd "$PY_ROOT"
if [[ "${MYPY_CMD[0]}" == "uv" ]]; then
  uv run --extra dev mypy --strict --follow-imports=skip "${_MYPY_TARGETS[@]}"
else
  "${MYPY_CMD[@]}" --strict --follow-imports=skip "${_MYPY_TARGETS[@]}"
fi
