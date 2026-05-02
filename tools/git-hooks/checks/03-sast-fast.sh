#!/usr/bin/env bash
# Fast SAST on staged source files (low-confidence only — full scan in pre-push).
set -e

files=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '^src/.*\.py$' || true)
[ -z "$files" ] && exit 0

if ! command -v bandit >/dev/null 2>&1; then
  echo "  ⚠ bandit not installed — pip install bandit" >&2
  exit 1
fi

# shellcheck disable=SC2086
bandit -ll -q $files
