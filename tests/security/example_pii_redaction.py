"""
PII redaction check — Bước 5.5a.
Quét log.txt / eval.json / REPORT.md không chứa CMND/CCCD, số thẻ Luhn, số tài khoản.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

# CMND (9 chữ số), CCCD (12 chữ số) cạnh từ khoá
ID_NEAR_KEYWORD = re.compile(
    r"(CMND|CCCD|số\s*định\s*danh|số\s*CCCD|số\s*CMND)\D{0,10}(\d{9,12})\b",
    re.IGNORECASE,
)

# Số tài khoản (dài, có thể có dấu cách)
ACCOUNT_LIKE = re.compile(r"\b\d{8,16}\b")

# Số thẻ tín dụng — dùng Luhn
CARD_LIKE = re.compile(r"\b(?:\d[ -]?){13,19}\b")


def luhn_valid(s: str) -> bool:
    digits = [int(c) for c in re.sub(r"\D", "", s)]
    if len(digits) < 13:
        return False
    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


@pytest.fixture
def evidence_files(request):
    run_dir = request.config.getoption("--run-dir", default=None)
    if not run_dir:
        pytest.skip("--run-dir not provided")
    base = Path(run_dir)
    return [base / "log.txt", base / "REPORT.md", base / "eval.json"]


def test_no_id_near_keyword(evidence_files):
    for f in evidence_files:
        if not f.exists():
            continue
        content = f.read_text(encoding="utf-8", errors="ignore")
        hits = ID_NEAR_KEYWORD.findall(content)
        assert not hits, f"PII (ID) leak in {f.name}: {hits[:3]}"


def test_no_luhn_card_numbers(evidence_files):
    for f in evidence_files:
        if not f.exists():
            continue
        content = f.read_text(encoding="utf-8", errors="ignore")
        hits = [m.group() for m in CARD_LIKE.finditer(content) if luhn_valid(m.group())]
        assert not hits, f"Possible card number leak in {f.name}: {hits[:3]}"


def test_eval_json_no_unredacted_pii(evidence_files):
    eval_path = next((f for f in evidence_files if f.name == "eval.json"), None)
    if eval_path is None or not eval_path.exists():
        pytest.skip("no eval.json")
    data = json.loads(eval_path.read_text())
    flat = json.dumps(data, ensure_ascii=False)
    assert not ID_NEAR_KEYWORD.search(flat), "PII in eval.json"
