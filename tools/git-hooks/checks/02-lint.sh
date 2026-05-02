#!/usr/bin/env bash
# Lint + format check + type check on staged Python files.
set -e

files=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.py$' || true)
[ -z "$files" ] && exit 0

if ! command -v ruff >/dev/null 2>&1; then
  echo "  ⚠ ruff not installed — pip install ruff" >&2
  exit 1
fi

# shellcheck disable=SC2086
ruff check $files
# shellcheck disable=SC2086
ruff format --check $files

if command -v mypy >/dev/null 2>&1; then
  # shellcheck disable=SC2086
  mypy --strict --ignore-missing-imports $files
else
  echo "  ⚠ mypy not installed — skipping type check (install: pip install mypy)" >&2
fi
