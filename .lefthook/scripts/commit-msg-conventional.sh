#!/usr/bin/env bash
set -euo pipefail

msg_file="${1:-}"
if [[ -z "$msg_file" || ! -f "$msg_file" ]]; then
  exit 0
fi

subject="$(sed -n '1p' "$msg_file")"
if [[ -z "${subject}" ]]; then
  exit 0
fi

pattern='^(feat|fix|refactor|test|docs|chore)(\([a-z0-9._/-]+\))?!?: .+'
if [[ "$subject" =~ $pattern ]]; then
  exit 0
fi

echo "[commit-msg] Advisory: prefer Conventional Commits."
echo "[commit-msg] Expected: type(scope): message"
echo "[commit-msg] Examples: feat(asset-editor): add model preview endpoint"
echo "[commit-msg]           fix(godot): prevent wall-cling timer underflow"
echo "[commit-msg] Current:  $subject"
exit 0
