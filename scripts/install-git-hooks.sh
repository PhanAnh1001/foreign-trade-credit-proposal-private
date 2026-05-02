#!/usr/bin/env bash
# Install git hooks by symlinking from tools/git-hooks/ to .git/hooks/.
# Symlink (not copy) so hook stays in sync with versioned source.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"
if [ -z "$REPO_ROOT" ]; then
  echo "ERROR: not inside a git repo" >&2
  exit 1
fi

HOOKS_SRC="$REPO_ROOT/tools/git-hooks"
HOOKS_DST="$REPO_ROOT/.git/hooks"

if [ ! -d "$HOOKS_SRC" ]; then
  echo "ERROR: $HOOKS_SRC not found" >&2
  exit 1
fi

mkdir -p "$HOOKS_DST"

# Make all scripts executable
chmod +x "$HOOKS_SRC"/*.sh "$HOOKS_SRC"/checks/*.sh 2>/dev/null || true

# Symlink hooks (relative path so it works after rename/move)
for hook in pre-commit commit-msg; do
  src_rel="../../tools/git-hooks/$hook.sh"
  dst="$HOOKS_DST/$hook"
  ln -sfn "$src_rel" "$dst"
  echo "  ✓ $dst → $src_rel"
done

echo
echo "Installed git hooks:"
ls -l "$HOOKS_DST"/pre-commit "$HOOKS_DST"/commit-msg

echo
echo "Required tools (install if missing):"
for tool in gitleaks ruff mypy bandit python3; do
  if command -v "$tool" >/dev/null 2>&1; then
    echo "  ✓ $tool"
  else
    echo "  ✗ $tool — required, install before committing"
  fi
done

echo
echo "Test hook: stage a file then run 'git commit -m \"T1: test\"'"
echo "WORKFLOW RULE: KHÔNG dùng 'git commit --no-verify' — CLAUDE.md §quy tắc 49."
