#!/usr/bin/env bash
# Pre-push: generate a blog post for the session's commits, then clear the log.
# Picks the blog CLI from who invoked git: Claude Code → claude; Cursor → cursor-agent;
# unknown → claude. Override with BLOG_POST_PROVIDER=claude|cursor.
# Skipped if SKIP_BLOG_POST=1, no session log, HEAD already blogged.
# Never blocks push (always exits 0).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG="$ROOT/.blog-session.log"
STATE_DIR="$ROOT/.lefthook"
STATE_FILE="$STATE_DIR/.blog-last-blogged-commit"
CURSOR_AGENT_BIN="${CURSOR_AGENT_BIN:-cursor-agent}"

if [[ "${SKIP_BLOG_POST:-0}" == "1" ]]; then
  echo "blog-post: skipped (SKIP_BLOG_POST=1)"
  exit 0
fi

HEAD_FULL="$(git -C "$ROOT" rev-parse HEAD)"

if [[ -f "$STATE_FILE" ]]; then
  LAST_BLOGGED="$(tr -d ' \n\t\r' < "$STATE_FILE" || true)"
  if [[ -n "$LAST_BLOGGED" && "$LAST_BLOGGED" == "$HEAD_FULL" ]]; then
    echo "blog-post: skipped — already generated for HEAD ${HEAD_FULL:0:12}…"
    rm -f "$LOG"
    exit 0
  fi
fi

if [[ ! -f "$LOG" || ! -s "$LOG" ]]; then
  exit 0
fi

SESSION_COMMITS="$(cat "$LOG")"

# --- Provider detection (see lefthook.yml header) ---
_lower() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

_blog_parent_chain_suggests_cursor() {
  local pid="${PPID:-0}"
  local i cmd
  for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
    [[ -z "$pid" || ! "$pid" =~ ^[0-9]+$ || "$pid" -le 1 ]] && return 1
    cmd="$(ps -p "$pid" -o command= 2>/dev/null || true)"
    if echo "$cmd" | grep -qiE '(^|/)Cursor\.app|Cursor Helper|/Applications/Cursor|/Cursor/|[/ ]Cursor\.exe'; then
      return 0
    fi
    pid="$(ps -p "$pid" -o ppid= 2>/dev/null | tr -d ' ')"
  done
  return 1
}

blog_resolve_provider() {
  local o
  if [[ -n "${BLOG_POST_PROVIDER:-}" ]]; then
    o="$(_lower "$BLOG_POST_PROVIDER")"
    case "$o" in
      claude | cursor)
        printf '%s' "$o"
        return 0
        ;;
      *)
        echo "blog-post: ignoring unknown BLOG_POST_PROVIDER='$BLOG_POST_PROVIDER' (use claude or cursor)" >&2
        ;;
    esac
  fi
  # Claude Code sets CLAUDECODE=1 in shells it spawns (not in hook subprocesses — but push from same shell keeps it).
  if [[ "${CLAUDECODE:-}" == "1" ]]; then
    printf '%s' "claude"
    return 0
  fi
  if [[ -n "${CURSOR_TRACE_ID:-}" || -n "${CURSOR_AGENT:-}" || -n "${CURSOR_SESSION_ID:-}" ]]; then
    printf '%s' "cursor"
    return 0
  fi
  if _blog_parent_chain_suggests_cursor; then
    printf '%s' "cursor"
    return 0
  fi
  printf '%s' "claude"
}

PROVIDER="$(blog_resolve_provider)"
echo "blog-post: generating post for session commits (HEAD ${HEAD_FULL:0:12}…)"
echo "blog-post: provider=$PROVIDER (Claude Code → claude, Cursor → cursor-agent, else claude)"
echo "$SESSION_COMMITS"
echo ""

PROMPT="Read the agent role definition at agent_context/agents/10_blog_post/blog_post_v1.md and follow it exactly. This is a non-interactive run triggered by a pre-push git hook — no live session conversation is available. Use git history, project_board/checkpoints/ scoped logs, project_board/CHECKPOINTS.md index, LEARNINGS.md, and the diff of these commits as your primary sources. The session commits were: $SESSION_COMMITS

Repository HEAD (full SHA) for this push: $HEAD_FULL"

cd "$ROOT"
OUT="$(mktemp)"
trap 'rm -f "$OUT"' EXIT

is_rate_limited() {
  grep -qiE 'rate limit|429|hit your limit|exceeded.*quota|too many requests' "$OUT" 2>/dev/null
}

is_cursor_auth_or_interactive_block() {
  grep -qiE 'not logged in|sign in|authenticate|login required|press any key' "$OUT" 2>/dev/null
}

run_claude() {
  if ! command -v claude >/dev/null 2>&1; then
    echo "blog-post: provider is claude but 'claude' is not on PATH"
    return 4
  fi
  set +e
  claude --print "$PROMPT" >"$OUT" 2>&1
  local rc=$?
  # Do not call set -e here — it leaks into the caller and makes a non-zero return exit the script.
  return "$rc"
}

run_cursor_agent() {
  if ! command -v "$CURSOR_AGENT_BIN" >/dev/null 2>&1; then
    echo "blog-post: provider is cursor but '${CURSOR_AGENT_BIN}' is not on PATH"
    return 4
  fi
  set +e
  printf '%s' "$PROMPT" | "$CURSOR_AGENT_BIN" --print --output-format text -f >"$OUT" 2>&1
  local rc=$?
  return "$rc"
}

: >"$OUT"
LAST_RC=1
# run_* return non-zero on failure; must not trigger set -e before we exit 0.
set +e
case "$PROVIDER" in
  claude)
    echo "blog-post: using Claude (claude --print)…"
    run_claude
    LAST_RC=$?
    ;;
  cursor)
    echo "blog-post: using Cursor Agent (${CURSOR_AGENT_BIN})…"
    run_cursor_agent
    LAST_RC=$?
    ;;
  *)
    echo "blog-post: internal error — unknown provider '$PROVIDER'"
    LAST_RC=2
    ;;
esac
set -e

cat "$OUT"

SUCCESS=0
if [[ "$LAST_RC" -eq 0 ]]; then
  SUCCESS=1
fi

SAW_RATE_LIMIT=0
SAW_CURSOR_AUTH=0
if [[ "$SUCCESS" -ne 1 ]]; then
  if is_rate_limited; then
    SAW_RATE_LIMIT=1
  fi
  if is_cursor_auth_or_interactive_block; then
    SAW_CURSOR_AUTH=1
  fi
fi

trap - EXIT
rm -f "$OUT"

if [[ "$SUCCESS" -eq 1 ]]; then
  mkdir -p "$STATE_DIR"
  printf '%s\n' "$HEAD_FULL" >"$STATE_FILE"
  rm -f "$LOG"
  echo "blog-post: done — recorded $HEAD_FULL as blogged; session log cleared."
elif [[ "$LAST_RC" -eq 4 ]]; then
  echo "blog-post: required CLI missing — session log preserved at $LOG"
  echo "           Override provider: BLOG_POST_PROVIDER=claude|cursor  or  SKIP_BLOG_POST=1"
elif [[ "$SAW_RATE_LIMIT" -eq 1 ]]; then
  echo "blog-post: rate limit or quota message — not treating as hook failure."
  echo "blog-post: session log preserved at $LOG"
elif [[ "$SAW_CURSOR_AUTH" -eq 1 ]]; then
  echo "blog-post: Cursor Agent may need login — not treating as hook failure."
  echo "blog-post: session log preserved at $LOG"
else
  echo "blog-post: generator exited $LAST_RC — session log preserved at $LOG"
  echo "           Re-run: claude --print \"…\"  or  stdin → ${CURSOR_AGENT_BIN} --print --output-format text -f"
  echo "           Force provider: BLOG_POST_PROVIDER=claude|cursor  SKIP_BLOG_POST=1 to skip"
fi

exit 0
