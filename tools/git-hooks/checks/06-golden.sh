#!/usr/bin/env bash
# Golden fixture sign-off check (lỗ hổng #6.6.11).
# Forbids changing tests/fixtures/*.golden.* without paired *.feedback.md sign-off.
set -e

exec python3 tools/check_golden_signoff.py
