#!/usr/bin/env bash
# Sync Claude Code skills and subagent definitions between agent_context and .claude/.
#
# Canonical layout under agent_context (resolved from repo agent_context symlink by default):
#   skills/<skill-name>/SKILL.md     -> .claude/skills/
#   claude_agents/*.md               -> .claude/agents/
#
# Environment:
#   BLOBERT_AGENT_CONTEXT  Absolute path to agent_context root (overrides repo symlink).

set -euo pipefail

usage() {
  cat <<'EOF'
Sync Claude Code skills and subagent files between agent_context and .claude/.

Usage:
  bash scripts/sync_claude_agent_context.sh [install|export] [--delete]

  install   (default) Copy agent_context/skills and agent_context/claude_agents into .claude/
  export    Copy .claude/skills and .claude/agents into agent_context/

  --delete  Pass rsync --delete (remove files in destination that are absent from source)

Examples:
  bash scripts/sync_claude_agent_context.sh
  BLOBERT_AGENT_CONTEXT=/path/to/context bash scripts/sync_claude_agent_context.sh export
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$REPO_ROOT" ]]; then
  REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

MODE="install"
RSYNC_DELETE=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h | --help)
      usage
      exit 0
      ;;
    install)
      MODE="install"
      shift
      ;;
    export)
      MODE="export"
      shift
      ;;
    --delete)
      RSYNC_DELETE=(--delete)
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -n "${BLOBERT_AGENT_CONTEXT:-}" ]]; then
  AGENT_CTX="${BLOBERT_AGENT_CONTEXT}"
else
  AGENT_CTX="$(realpath "${REPO_ROOT}/agent_context" 2>/dev/null || true)"
  if [[ -z "$AGENT_CTX" || ! -d "$AGENT_CTX" ]]; then
    AGENT_CTX="$(cd "${REPO_ROOT}/agent_context" && pwd)"
  fi
fi

if [[ ! -d "$AGENT_CTX" ]]; then
  echo "error: agent_context directory not found: ${AGENT_CTX}" >&2
  echo "Set BLOBERT_AGENT_CONTEXT to the blobert_agent_context root." >&2
  exit 1
fi

SK_SRC="${AGENT_CTX}/skills"
AG_SRC="${AGENT_CTX}/claude_agents"
SK_DST="${REPO_ROOT}/.claude/skills"
AG_DST="${REPO_ROOT}/.claude/agents"

rsync_sync() {
  local -a args=(-a)
  if [[ ${#RSYNC_DELETE[@]} -gt 0 ]]; then
    args+=("${RSYNC_DELETE[@]}")
  fi
  # Preserve skill dirs and agent .md files; exclude macOS junk.
  args+=(--exclude '.DS_Store')
  rsync "${args[@]}" "$1" "$2"
}

if [[ "$MODE" == "install" ]]; then
  if [[ ! -d "$SK_SRC" ]]; then
    echo "error: missing ${SK_SRC} (run export from a machine that has .claude/skills)" >&2
    exit 1
  fi
  if [[ ! -d "$AG_SRC" ]]; then
    echo "error: missing ${AG_SRC} (run export from a machine that has .claude/agents)" >&2
    exit 1
  fi
  mkdir -p "$SK_DST" "$AG_DST"
  echo "Installing Claude skills + agents from:"
  echo "  ${AGENT_CTX}"
  rsync_sync "${SK_SRC}/" "${SK_DST}/"
  rsync_sync "${AG_SRC}/" "${AG_DST}/"
  echo "Done -> ${REPO_ROOT}/.claude/"
else
  mkdir -p "$SK_SRC" "$AG_SRC"
  if [[ ! -d "$SK_DST" ]]; then
    echo "error: missing ${SK_DST}" >&2
    exit 1
  fi
  if [[ ! -d "$AG_DST" ]]; then
    echo "error: missing ${AG_DST}" >&2
    exit 1
  fi
  echo "Exporting Claude skills + agents to:"
  echo "  ${AGENT_CTX}"
  rsync_sync "${SK_DST}/" "${SK_SRC}/"
  rsync_sync "${AG_DST}/" "${AG_SRC}/"
  echo "Done -> ${AGENT_CTX}/skills and .../claude_agents"
fi
