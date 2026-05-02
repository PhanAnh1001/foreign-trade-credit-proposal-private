#!/usr/bin/env bash
# Approver whitelist on staged MD files (lỗ hổng #6.5.1).
# Forbids AI from self-ticking ## Approved by ...
set -e

md_files=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.md$' || true)
[ -z "$md_files" ] && exit 0

exec python3 tools/check_approver.py --staged
