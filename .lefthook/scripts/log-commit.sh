#!/usr/bin/env bash
# Post-commit: append the latest commit subject + hash to the session log.
# This gives the blog post agent a precise list of what changed this session.
set -e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG="$ROOT/.blog-session.log"

HASH="$(git rev-parse --short HEAD)"
SUBJECT="$(git log -1 --format='%s')"

echo "$HASH $SUBJECT" >> "$LOG"
