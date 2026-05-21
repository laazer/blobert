#!/usr/bin/env bash
# Map a staged file path to a Ruff/Pylint argument relative to asset_generation/python/.
# Prints the relative path on stdout when mapped; prints nothing when out of scope.
set -euo pipefail

py_staged_ruff_rel() {
  local f="$1"
  local py_root="$2"

  case "$f" in
    "$py_root"/*)
      printf '%s\n' "${f#"$py_root"/}"
      ;;
    */asset_generation/python/*)
      printf '%s\n' "${f##*asset_generation/python/}"
      ;;
    asset_generation/python/*)
      printf '%s\n' "${f#asset_generation/python/}"
      ;;
    ci/scripts/*)
      printf '%s\n' "../../$f"
      ;;
    tests/ci/*)
      printf '%s\n' "../../$f"
      ;;
    *"/ci/scripts/"*)
      printf '%s\n' "../../ci/scripts/${f#*ci/scripts/}"
      ;;
    *"/tests/ci/"*)
      printf '%s\n' "../../tests/ci/${f#*tests/ci/}"
      ;;
    *)
      ;;
  esac
}
