#!/usr/bin/env bash
# Commit message must start with T<n>: (lỗ hổng #6.5.9).
# $1 = commit message file path.
set -e

exec python3 tools/check_t_in_commit.py "$1"
