#!/usr/bin/env bash
# Hygiene: large files, merge conflict markers, yaml/json validity, trailing whitespace.
set -e

MAX_BYTES=512000  # 500 KB

files=$(git diff --cached --name-only --diff-filter=ACMR)
[ -z "$files" ] && exit 0

failed=0
while IFS= read -r f; do
  [ -z "$f" ] && continue
  [ -f "$f" ] || continue

  # Large file
  size=$(wc -c < "$f" | tr -d ' ')
  if [ "$size" -gt "$MAX_BYTES" ]; then
    echo "  ✘ Large file: $f ($size bytes > $MAX_BYTES)" >&2
    failed=1
  fi

  # Merge conflict markers
  if grep -nE '^(<<<<<<<|=======|>>>>>>>) ' "$f" >/dev/null 2>&1; then
    echo "  ✘ Merge conflict marker in $f" >&2
    failed=1
  fi

  # Detect private key patterns
  if grep -nE -- '-----BEGIN (RSA|DSA|EC|OPENSSH|PGP) PRIVATE KEY-----' "$f" >/dev/null 2>&1; then
    echo "  ✘ Private key detected in $f" >&2
    failed=1
  fi

  # YAML/JSON validity
  case "$f" in
    *.yaml|*.yml)
      python3 -c "import yaml,sys; yaml.safe_load(open('$f'))" 2>/dev/null || {
        echo "  ✘ Invalid YAML: $f" >&2
        failed=1
      }
      ;;
    *.json)
      python3 -c "import json,sys; json.load(open('$f'))" 2>/dev/null || {
        echo "  ✘ Invalid JSON: $f" >&2
        failed=1
      }
      ;;
  esac
done <<< "$files"

exit $failed
