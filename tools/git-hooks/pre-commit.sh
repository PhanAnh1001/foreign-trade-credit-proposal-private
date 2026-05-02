#!/usr/bin/env bash
# Pre-commit orchestrator (workflow §5.5 + §6.7).
# Runs all 0X checks in tools/git-hooks/checks/. Fails fast.
# Bypass via `git commit --no-verify` is FORBIDDEN by workflow §quy tắc 49.

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOK_DIR="$REPO_ROOT/tools/git-hooks/checks"

if [ ! -d "$HOOK_DIR" ]; then
  echo "ERROR: $HOOK_DIR not found. Run 'make install' to set up hooks." >&2
  exit 1
fi

failed=0
for check in "$HOOK_DIR"/0*.sh; do
  [ -e "$check" ] || continue
  name=$(basename "$check" .sh)
  echo "▶ $name"
  if ! bash "$check"; then
    echo "✘ $name failed" >&2
    failed=1
    break
  fi
done

if [ $failed -ne 0 ]; then
  echo
  echo "Pre-commit hook failed. Fix the issue and commit again." >&2
  echo "DO NOT use --no-verify (workflow §quy tắc 49)." >&2
  exit 1
fi

echo "✓ All pre-commit checks passed"
