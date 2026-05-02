#!/usr/bin/env bash
# Secret scan on staged content (lỗ hổng #6.5.4).
set -e

if ! command -v gitleaks >/dev/null 2>&1; then
  echo "  ⚠ gitleaks not installed — install: brew install gitleaks (or apt/yum)" >&2
  exit 1
fi

gitleaks protect --staged --redact --no-banner
