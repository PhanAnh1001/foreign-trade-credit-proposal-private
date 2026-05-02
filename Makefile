.PHONY: help install hooks 01 02 03 04 05 test security e2e e2e-thrice eval verify-evidence perf-diff perf-baseline cascade adr all clean

SCENARIO     ?= happy_default
RUN_ID       ?= $(shell date +%Y%m%d_%H%M%S)_$(SCENARIO)
EVIDENCE_DIR ?= ete-evidence/_runs/$(RUN_ID)
FB_ID        ?=
ADR_TITLE    ?=

help:
	@echo "Workflow targets (theo docs/workflow.md):"
	@echo ""
	@echo "  Setup:"
	@echo "    install            - Cài deps + git hooks (pre-commit, commit-msg)"
	@echo "    hooks              - Symlink lại git hooks từ tools/git-hooks/"
	@echo ""
	@echo "  Test layered (Bước 5):"
	@echo "    01..05             - Từng tầng test, fail-fast"
	@echo "    test               - 02 + 04 + 05"
	@echo ""
	@echo "  Security gate (Bước 5.5):"
	@echo "    security           - 5 lớp scan, sinh security.json"
	@echo ""
	@echo "  E2E + Evidence (Bước 6):"
	@echo "    e2e                - 1 run (yêu cầu Bước 5.5 pass)"
	@echo "    e2e-thrice         - 3 runs liên tiếp, gate 3-of-3 (chống #6.6.2)"
	@echo "    eval               - Self-eval cho 1 run"
	@echo ""
	@echo "  Verify (chống confabulation):"
	@echo "    verify-evidence    - Crosscheck log SHA, junit, timestamp (#6.6.1)"
	@echo "    perf-diff          - So sánh với baseline (#6.6.10)"
	@echo "    perf-baseline      - Cập nhật baseline (cần human sign-off)"
	@echo ""
	@echo "  Helpers:"
	@echo "    cascade FB_ID=<id>      - Tạo branch cascade/<id> (§7g)"
	@echo "    adr ADR_TITLE='<t>'     - Tạo ADR mới"
	@echo "    all                     - 01 → 05 → 5.5 (fail-fast)"
	@echo ""
	@echo "Vars: SCENARIO=$(SCENARIO)  RUN_ID=$(RUN_ID)  EVIDENCE_DIR=$(EVIDENCE_DIR)"

install:
	pip install -r requirements.txt -r requirements-dev.txt
	$(MAKE) hooks

hooks:
	@bash scripts/install-git-hooks.sh

# Bước 5 — Test layered
01:
	@echo ">> 01_env_setup"
	python -m src.config.check_env | tee -a logs/run_$(RUN_ID).log

02:
	@echo ">> 02_tools"
	pytest tests/unit/tools/ -q --junit-xml=$(EVIDENCE_DIR)/pytest_junit.xml 2>&1 | tee -a logs/run_$(RUN_ID).log

03:
	@echo ">> 03_nodes (LLM-backed, real calls)"
	pytest tests/unit/nodes/ -q --maxfail=1 2>&1 | tee -a logs/run_$(RUN_ID).log

04:
	@echo ">> 04_pipeline"
	pytest tests/integration/test_pipeline.py -q 2>&1 | tee -a logs/run_$(RUN_ID).log

05:
	@echo ">> 05_output"
	pytest tests/integration/test_output_validation.py -q 2>&1 | tee -a logs/run_$(RUN_ID).log

test: 02 04 05

# Bước 5.5 — Security & supply-chain gate
security:
	@mkdir -p $(EVIDENCE_DIR)/security
	@echo ">> 5.5.1 Secret scan (gitleaks)"
	-gitleaks detect --no-git --report-path $(EVIDENCE_DIR)/security/gitleaks.json
	@echo ">> 5.5.2 SAST (bandit + semgrep)"
	-bandit -r src/ -f json -o $(EVIDENCE_DIR)/security/bandit.json
	-semgrep --config auto src/ --json -o $(EVIDENCE_DIR)/security/semgrep.json
	@echo ">> 5.5.3 Dependency CVE (pip-audit)"
	-pip-audit -f json -o $(EVIDENCE_DIR)/security/pip-audit.json
	@echo ">> 5.5.4 License"
	-pip-licenses --format=json --fail-on="GPL;AGPL" > $(EVIDENCE_DIR)/security/licenses.json
	@echo ">> 5.5.5 AI-safety tests"
	pytest tests/security/ -q --json-report --json-report-file=$(EVIDENCE_DIR)/security/ai-safety.json
	@echo ">> compose security.json"
	python -m src.security.compose_report --evidence-dir $(EVIDENCE_DIR)
	@test -f $(EVIDENCE_DIR)/security.json || (echo "ERROR: security.json not generated"; exit 1)

# Bước 6 — E2E
e2e: security
	@echo ">> E2E scenario=$(SCENARIO) run_id=$(RUN_ID)"
	python -m src.e2e.runner --scenario $(SCENARIO) --run-id $(RUN_ID) --evidence-dir $(EVIDENCE_DIR)
	@echo ">> verify-evidence"
	python tools/verify_evidence.py --evidence-dir $(EVIDENCE_DIR)
	@echo ">> perf-diff"
	-python tools/perf_diff.py --scenario $(SCENARIO) --evidence-dir $(EVIDENCE_DIR)
	@echo ">> Evidence: $(EVIDENCE_DIR)/"

# 3-of-3 — chống non-determinism (#6.6.2)
e2e-thrice:
	python tools/run_e2e_thrice.py --scenario $(SCENARIO)

eval:
	@if [ -z "$(RUN_ID)" ]; then echo "ERROR: RUN_ID required"; exit 1; fi
	python -m src.eval.run --run-id $(RUN_ID) --evidence-dir $(EVIDENCE_DIR)

verify-evidence:
	python tools/verify_evidence.py --evidence-dir $(EVIDENCE_DIR)

perf-diff:
	python tools/perf_diff.py --scenario $(SCENARIO) --evidence-dir $(EVIDENCE_DIR)

perf-baseline:
	python tools/perf_diff.py --scenario $(SCENARIO) --evidence-dir $(EVIDENCE_DIR) --update-baseline
	@echo ">> Baseline updated. Tạo data/baselines/$(SCENARIO).json.feedback.md với '## Approved by <name>'"

# Helpers
cascade:
	@if [ -z "$(FB_ID)" ]; then echo "ERROR: FB_ID required (e.g. make cascade FB_ID=F1-PRD-criteria)"; exit 1; fi
	bash tools/cascade_branch.sh $(FB_ID)

adr:
	@if [ -z "$(ADR_TITLE)" ]; then echo "ERROR: ADR_TITLE required"; exit 1; fi
	@N=$$(ls docs/adr/ 2>/dev/null | grep -E '^[0-9]{4}-' | sort | tail -1 | cut -d'-' -f1); \
	NEXT=$$(printf "%04d" $$((10#$${N:-0} + 1))); \
	SLUG=$$(echo "$(ADR_TITLE)" | tr '[:upper:] ' '[:lower:]-' | tr -cd 'a-z0-9-'); \
	cp docs/adr/0000-template.md docs/adr/$${NEXT}-$${SLUG}.md; \
	sed -i.bak "s/<NNNN>/$${NEXT}/; s/<Title>/$(ADR_TITLE)/" docs/adr/$${NEXT}-$${SLUG}.md && rm docs/adr/$${NEXT}-$${SLUG}.md.bak; \
	echo ">> created docs/adr/$${NEXT}-$${SLUG}.md"

all: 01 02 03 04 05 security

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -rf .mypy_cache .ruff_cache
