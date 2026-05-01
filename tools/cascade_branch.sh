#!/usr/bin/env bash
# Tạo branch riêng cho 1 cascade từ feedback upstream — chống lỗ hổng #6.6.8
# (cascade fail giữa chừng làm vỡ main, rollback thủ công cực).
#
# Usage:
#   bash tools/cascade_branch.sh F1-PRD-criteria
# Tạo:
#   - branch cascade/F1-PRD-criteria nhánh từ HEAD hiện tại
#   - commit khởi tạo "Tboot: cascade scaffold for F1-PRD-criteria"
#   - thư mục .cascade/F1-PRD-criteria/ với note + checklist

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "usage: $0 <feedback-id>  (e.g. F1-PRD-criteria, F2-design-judge)"
  exit 2
fi

FB_ID="$1"
BR="cascade/${FB_ID}"
DIR=".cascade/${FB_ID}"

if git rev-parse --verify "${BR}" >/dev/null 2>&1; then
  echo "Branch ${BR} already exists. Switching to it."
  git switch "${BR}"
  exit 0
fi

git switch -c "${BR}"
mkdir -p "${DIR}"
cat > "${DIR}/checklist.md" <<EOF
# Cascade ${FB_ID}

Created: $(date -Iseconds)
Branch: ${BR}
Base: $(git rev-parse --short HEAD)

## Checklist (theo workflow §7g)
- [ ] Impact analysis viết vào file feedback gốc dưới '## AI Response — impact analysis'
- [ ] Update artifact gốc (PRD/Design/Plan) — bump version + changelog cuối file
- [ ] Re-derive downstream theo dependency, mỗi cái qua gate riêng
- [ ] Thêm task vào plans/<epic>.md mục 'Cascade từ feedback'
- [ ] Re-run đầy đủ Bước 5 → 5.5 → 6 (3-of-3)
- [ ] REPORT.md run mới có mục 'Upstream feedback addressed'
- [ ] Người approve → merge vào branch epic chính
- [ ] Nếu fail giữa chừng: \`git reset --hard origin/\$(base)\` và rebuild

## Rollback
git switch <epic-branch> && git branch -D ${BR}
EOF

git add "${DIR}/checklist.md"
git commit -m "Tboot: cascade scaffold for ${FB_ID}" --allow-empty
echo "Created ${BR} with ${DIR}/checklist.md"
