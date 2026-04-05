#!/usr/bin/env bash
# Static contract checks for MAINT-TSGR (spec: project_board/specs/test_suite_green_and_runner_exit_codes_spec.md).
# Exit 0 when ci/scripts/run_tests.sh, .lefthook/scripts/godot-tests.sh, and CLAUDE.md satisfy TSGR-*.
# Intended to run from repo root: bash ci/scripts/verify_tsgr_runner_contract.sh

set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ERRORS=0

fail() {
	echo "TSGR contract: $*" >&2
	ERRORS=$((ERRORS + 1))
}

_collect_import_lines() {
	local file="$1"
	grep -nE 'godot.*--import|GODOT.*--import' "$file" 2>/dev/null || true
}

_check_import_lines() {
	local file="$1"
	local label="$2"
	local found=0
	while IFS= read -r entry; do
		[[ -z "$entry" ]] && continue
		local num line
		num="${entry%%:*}"
		line="${entry#*:}"
		if [[ "$line" =~ ^[[:space:]]*# ]]; then
			continue
		fi
		found=1
		if [[ "$line" != *timeout* ]]; then
			fail "${label}: TSGR-2 (line ${num}) import must use bounded timeout."
		fi
		if [[ "$line" == *'|| true'* ]]; then
			fail "${label}: TSGR-2 (line ${num}) import must not use '|| true' without narrow documented bypass."
		fi
		if [[ "$line" == *'2>/dev/null'* ]]; then
			fail "${label}: TSGR-2 (line ${num}) import must not discard stderr to /dev/null on the fail-fast path."
		fi
	done < <(_collect_import_lines "$file")
	if [[ "$found" -eq 0 ]]; then
		fail "${label}: TSGR-2 expected a non-comment Godot --import invocation; none found."
	fi
}

_check_godot_test_run() {
	local file="$1"
	local label="$2"
	if ! grep -qE 'run_tests\.gd' "$file"; then
		fail "${label}: TSGR-1/4 expected tests/run_tests.gd invocation."
		return
	fi
	while IFS= read -r entry; do
		[[ -z "$entry" ]] && continue
		local num line
		num="${entry%%:*}"
		line="${entry#*:}"
		if [[ "$line" != *timeout* ]]; then
			fail "${label}: TSGR-4 (line ${num}) Godot test run must use timeout."
		fi
		if [[ "$line" == *'|| true'* ]]; then
			fail "${label}: TSGR-5 (line ${num}) Godot test run must not use '|| true'."
		fi
	done < <(grep -nE 'run_tests\.gd' "$file")
}

_check_run_tests_python_phase() {
	local f="$ROOT/ci/scripts/run_tests.sh"
	if ! grep -qE 'pytest|py-tests\.sh' "$f"; then
		fail "run_tests.sh: TSGR-1 expected Python phase (pytest or .lefthook/scripts/py-tests.sh)."
		return
	fi
	if ! grep -qE 'asset_generation/python|tests/' "$f"; then
		fail "run_tests.sh: TSGR-1 expected Python tests path context (asset_generation/python or tests/)."
	fi
	# DRY: inline resolver duplicates drift from py-tests.sh — delegate to py-tests or ci helper.
	if grep -qE 'command -v uv|\.venv/bin/python' "$f"; then
		if ! grep -qE 'py-tests\.sh|(bash|source|[.]) .*ci/scripts/[a-z0-9_]+\.sh' "$f"; then
			fail "run_tests.sh: TSGR-3 inline .venv/uv resolver must not duplicate py-tests.sh; call py-tests.sh or a ci/scripts helper."
		fi
	fi
	local godot_line py_line
	godot_line=$(grep -nE 'run_tests\.gd' "$f" | head -1 | cut -d: -f1)
	py_line=$(grep -nE 'pytest|py-tests\.sh' "$f" | head -1 | cut -d: -f1)
	if [[ -n "$godot_line" && -n "$py_line" && "$py_line" -le "$godot_line" ]]; then
		fail "run_tests.sh: TSGR-1 expected Godot test phase before Python phase (line ${py_line} vs ${godot_line})."
	fi
}

_check_run_tests_errexit() {
	local f="$ROOT/ci/scripts/run_tests.sh"
	if ! grep -qE '^set -e$|^set -e |^set -euo pipefail|^set -eu$|^set -eu |^set -o errexit' "$f"; then
		fail "run_tests.sh: TSGR-4 expected 'set -e' (or equivalent errexit) so failures do not fall through."
	fi
}

_check_godot_hook() {
	local f="$ROOT/.lefthook/scripts/godot-tests.sh"
	if [[ ! -f "$f" ]]; then
		fail "Missing .lefthook/scripts/godot-tests.sh (TSGR-6.2)."
		return
	fi
	_check_import_lines "$f" "godot-tests.sh"
	_check_godot_test_run "$f" "godot-tests.sh"
}

_check_claude_md() {
	local f="$ROOT/CLAUDE.md"
	if [[ ! -f "$f" ]]; then
		fail "Missing CLAUDE.md (TSGR-6.1)."
		return
	fi
	if ! grep -q 'ci/scripts/run_tests.sh' "$f"; then
		fail "CLAUDE.md: TSGR-6.1 must name ci/scripts/run_tests.sh as the canonical full-suite entry (or equivalent explicit path)."
	fi
	if ! grep -qE 'asset_generation/python|pytest' "$f"; then
		fail "CLAUDE.md: TSGR-6.1 must document the Python / asset_generation test phase alongside Godot."
	fi
	if ! grep -qEi 'fail.fast|fail-fast' "$f"; then
		fail "CLAUDE.md: TSGR-6 must summarize bounded, fail-fast import policy (e.g. 'fail-fast' or 'fail fast')."
	fi
}

main() {
	local rt="$ROOT/ci/scripts/run_tests.sh"
	if [[ ! -f "$rt" ]]; then
		fail "Missing ci/scripts/run_tests.sh"
		exit 1
	fi
	_check_import_lines "$rt" "run_tests.sh"
	_check_godot_test_run "$rt" "run_tests.sh"
	_check_run_tests_python_phase
	_check_run_tests_errexit
	_check_godot_hook
	_check_claude_md
	if [[ "$ERRORS" -gt 0 ]]; then
		echo "verify_tsgr_runner_contract.sh: ${ERRORS} check(s) failed (MAINT-TSGR)." >&2
		exit 1
	fi
	echo "verify_tsgr_runner_contract.sh: OK (MAINT-TSGR static contract)."
	exit 0
}

main "$@"
