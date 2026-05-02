#!/usr/bin/env bash
# Commit-msg orchestrator. $1 = path to commit message file.
# Runs all 1X checks in tools/git-hooks/checks/.

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOK_DIR="$REPO_ROOT/tools/git-hooks/checks"

if [ ! -d "$HOOK_DIR" ]; then
  echo "ERROR: $HOOK_DIR not found. Run 'make install' to set up hooks." >&2
  exit 1
fi

for check in "$HOOK_DIR"/1*.sh; do
  [ -e "$check" ] || continue
  name=$(basename "$check" .sh)
  echo "▶ $name"
  if ! bash "$check" "$1"; then
    echo "✘ $name failed" >&2
    exit 1
  fi
done
