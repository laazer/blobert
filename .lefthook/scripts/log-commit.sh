#!/usr/bin/env bash
# Post-commit: append the latest commit subject + hash to the session log.
# Does not invoke claude, cursor-agent, or blog_post_v1 — pre-push runs that via blog-post-on-push.sh.
set -e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG="$ROOT/.blog-session.log"

HASH="$(git rev-parse --short HEAD)"
SUBJECT="$(git log -1 --format='%s')"

echo "$HASH $SUBJECT" >> "$LOG"
