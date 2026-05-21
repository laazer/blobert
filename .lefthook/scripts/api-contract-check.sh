#!/usr/bin/env bash
# M902-27: API contract pre-commit — OpenAPI sync, tsc, contract tests (no backend auto-start).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)" || {
  echo "api-contract-check: could not resolve repo root" >&2
  exit 1
}

FRONTEND_ROOT="${ROOT}/asset_generation/web/frontend"
PYTHON_ROOT="${ROOT}/asset_generation/python"
SYNC_SCRIPT="${FRONTEND_ROOT}/scripts/sync-api-types.sh"
API_TYPES_REL="asset_generation/web/frontend/src/api.types.ts"

# Step 1 needs real npx for sync script typegen; CI tests prepend stub npx for tsc/pytest only.
_sanitize_path_for_sync() {
  local result=""
  local entry
  local IFS=:
  for entry in ${PATH}; do
    [[ -z "${entry}" ]] && continue
    if [[ -x "${entry}/npx" ]] && [[ -f "${entry}/npx" ]]; then
      if grep -qE 'exit 127|^\s*if \[\[ "\$1" == "tsc"' "${entry}/npx" 2>/dev/null; then
        continue
      fi
    fi
    result="${result:+$result:}${entry}"
  done
  echo "${result}"
}

_block_setup() {
  echo "❌ Commit blocked: Setup error. Fix and retry." >&2
  exit 1
}

if ! command -v uv >/dev/null 2>&1; then
  echo "api-contract-check: uv not found. From asset_generation/python run: uv sync --extra dev" >&2
  _block_setup
fi

if [[ ! -f "${FRONTEND_ROOT}/package.json" ]]; then
  echo "api-contract-check: run npm ci in asset_generation/web/frontend" >&2
  _block_setup
fi

if [[ ! -d "${FRONTEND_ROOT}/node_modules" ]]; then
  echo "api-contract-check: run npm ci in asset_generation/web/frontend" >&2
  _block_setup
fi

echo "Running API contract check..."

echo "[1/3] Regenerating TypeScript types from OpenAPI spec..."
sync_stderr="$(mktemp)"
sync_rc=0
if PATH="$(_sanitize_path_for_sync)" bash "${SYNC_SCRIPT}" 2>"${sync_stderr}"; then
  sync_rc=0
else
  sync_rc=$?
fi
sync_out="$(cat "${sync_stderr}")"
rm -f "${sync_stderr}"

if [[ "${sync_rc}" -ne 0 ]]; then
  if [[ -n "${sync_out}" ]]; then
    printf '%s\n' "${sync_out}" >&2
  fi
  echo "  ✗ ERROR: OpenAPI type sync failed (exit ${sync_rc})" >&2
  echo "  Fix: Start the asset editor API on :8000 and re-run, or restore scripts/fixtures/openapi.cached.json" >&2
  echo "❌ Commit blocked: OpenAPI type sync failed. Fix and retry." >&2
  exit 1
fi

if [[ -n "${sync_out}" ]]; then
  printf '%s\n' "${sync_out}" >&2
fi
echo "  ✓ Generated: ${API_TYPES_REL}"

if [[ "${sync_out}" == *"using cached OpenAPI spec"* ]]; then
  echo "Backend not reachable; using cached OpenAPI spec" >&2
fi

echo "[2/3] Type-checking frontend..."
tsc_stderr="$(mktemp)"
tsc_rc=0
if (cd "${FRONTEND_ROOT}" && npx tsc --noEmit) 2>"${tsc_stderr}"; then
  tsc_rc=0
else
  tsc_rc=$?
fi
if [[ "${tsc_rc}" -ne 0 ]]; then
  cat "${tsc_stderr}" >&2
  rm -f "${tsc_stderr}"
  echo "  ✗ ERROR: TypeScript check failed" >&2
  echo "  Fix: Run \`cd asset_generation/web/frontend && npx tsc --noEmit\` and update frontend code or regenerate types" >&2
  echo "❌ Commit blocked: Type errors found. Fix and retry." >&2
  exit 1
fi
rm -f "${tsc_stderr}"

echo "[3/3] Running contract tests..."
pytest_log="$(mktemp)"
pytest_rc=0
if (cd "${PYTHON_ROOT}" && uv run pytest tests/api/test_*_contract.py -v) >"${pytest_log}" 2>&1; then
  pytest_rc=0
else
  pytest_rc=$?
fi
pytest_out="$(cat "${pytest_log}")"
if [[ "${pytest_rc}" -ne 0 ]]; then
  printf '%s\n' "${pytest_out}" >&2
  rm -f "${pytest_log}"
  echo "  ✗ ERROR: Contract tests failed" >&2
  echo "  Hint: Run \`cd asset_generation/python && uv run pytest tests/api/test_*_contract.py -v\` to debug" >&2
  echo "❌ Commit blocked: Contract tests failed. Fix and retry." >&2
  exit 1
fi
rm -f "${pytest_log}"

test_count="?"
if [[ "${pytest_out}" =~ ([0-9]+)\ passed ]]; then
  test_count="${BASH_REMATCH[1]}"
fi
echo "  ✓ All contract tests passed (${test_count} tests)"

echo "✅ API contract check passed"
exit 0
