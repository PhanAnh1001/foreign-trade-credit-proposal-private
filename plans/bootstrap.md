# Epic — Bootstrap (one-time scaffolding)

> Epic ĐẦU TIÊN khi adopt workflow. **KHÔNG bỏ qua.** Sau khi pass, các epic sau không phải làm lại scaffolding (xem `docs/workflow.md` §6.8).
>
> Định nghĩa thành công: tất cả file/hook bên dưới tồn tại + 1 dry-run epic "hello-world" chạy 0→7 với mọi gate hoạt động.

## Checklist

- [ ] T1. `docs/reviewers.txt` — danh sách reviewer hợp lệ (có sẵn trong starter kit, cần điền tên thật).
      DoD: `grep -v '^#' docs/reviewers.txt | grep -v '^$'` ≥ 1 dòng
- [ ] T2. `docs/adr/0000-template.md` + `docs/adr/0001-adopt-this-workflow.md`
      DoD: 2 file tồn tại, 0001 có Status=Accepted
- [ ] T3. `.pre-commit-config.yaml` — gitleaks + bandit -ll + ruff + mypy --strict + pip-audit
      DoD: `pre-commit run --all-files` chạy được, không error config
- [ ] T4. `tools/check_approver.py` — verify name trong feedback/commit ⊂ `docs/reviewers.txt`
      DoD: `python tools/check_approver.py --file <test>` exit 0 nếu hợp lệ, 1 nếu sai
- [ ] T5. `tools/check_t_in_commit.py` — reject commit message không có `T<n>:`
      DoD: hook chạy ở commit-msg stage, reject commit "chore: foo" và pass commit "T1: foo"
- [ ] T6. `tools/check_golden_signoff.py` — reject `git diff` chạm `tests/fixtures/golden_*` không có `*.feedback.md` ký
      DoD: thay đổi golden không có feedback → exit 1
- [ ] T7. `tools/verify_evidence.py` — crosscheck log SHA + junit timestamp trong evidence dir
      DoD: với evidence giả (REPORT viết PASS nhưng log rỗng) → exit 1
- [ ] T8. `tools/run_e2e_thrice.py` — chạy 3 lần consecutive cùng input, ghép transcript, output 3-of-3 verdict
      DoD: chạy thành công với scenario `hello-world` → tạo 3 run-id + verdict file
- [ ] T9. `tools/cascade_branch.sh` — tạo branch `cascade/<F-id>` + setup
      DoD: `bash tools/cascade_branch.sh F1-PRD-criteria` tạo branch + commit khởi tạo
- [ ] T10. `tests/security/test_prompt_injection.py` — 5 vector cơ bản
      DoD: `pytest tests/security/test_prompt_injection.py -q` 5/5 pass với system prompt baseline
- [ ] T11. `data/baselines/.gitkeep` + `tools/perf_diff.py`
      DoD: `python tools/perf_diff.py --scenario hello-world --run-id <id>` so sánh được latency/tokens
- [ ] T12. `.claude/scripts/auto-save.sh` — patch skip khi đang giữa task (check task lock file)
      DoD: file tồn tại, có comment giải thích lock file mechanism
- [ ] T13. Templates §9 trong `docs/workflow.md` đã có template trong starter kit:
      - REPORT.md (`ete-evidence/_template/REPORT.md`)
      - REVIEW_SUMMARY.md (`plans/_review-summary-template.md`)
      - ADR (`docs/adr/0000-template.md`)
      - Resume pointer (đoạn cuối `plans/_template.md`)
      - Multi-reviewer feedback (`*_feedback-template.md`)
      DoD: `find . -name '_template*' -o -name '*-template*'` ≥ 8 file
- [ ] T14. `.github/workflows/ci.yml` — chạy `pre-commit run --all-files`
      DoD: `gh workflow view ci` xanh trên 1 PR thử
- [ ] T15. Dry-run: tạo `docs/intent/hello-world.md`, chạy đủ 0→7, mọi gate hoạt động
      DoD: `ete-evidence/.../hello-world/<run-id>/REPORT.md` PASS với scenario adversarial + normal

---

## Approved by <tên> @ <YYYY-MM-DD>
<!-- Tick khi mọi T1–T15 done. -->

## Tracking

| Task | Commit | Test result | Note |
|---|---|---|---|
| T1 | … | … | |

## Last session — <YYYY-MM-DD HH:MM>
- Ended at: T<n>
- Status: <…>
- Next: T<n+1>
- Blockers: none | [!] reason

## Session log
- <ts>: started, completed T1–T<n>
