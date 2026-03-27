#!/usr/bin/env bash
# Pre-push: generate a blog post for the session's commits, then clear the log.
# Skipped if SKIP_BLOG_POST=1 or if no session log exists.
set -e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG="$ROOT/.blog-session.log"

if [[ "${SKIP_BLOG_POST:-0}" == "1" ]]; then
  echo "blog-post: skipped (SKIP_BLOG_POST=1)"
  exit 0
fi

if [[ ! -f "$LOG" || ! -s "$LOG" ]]; then
  exit 0
fi

SESSION_COMMITS="$(cat "$LOG")"
echo "blog-post: generating post for session commits..."
echo "$SESSION_COMMITS"
echo ""

PROMPT="Read the agent role definition at agent_context/agents/10_blog_post/blog_post_v1.md and follow it exactly. This is a non-interactive run triggered by a pre-push git hook — no live session conversation is available. Use git history, CHECKPOINTS.md, LEARNINGS.md, and the diff of these commits as your primary sources. The session commits were: $SESSION_COMMITS"

cd "$ROOT"
claude --print "$PROMPT"

# Clear the session log after the post is written.
rm -f "$LOG"
