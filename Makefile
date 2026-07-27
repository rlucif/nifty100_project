# =====================================================================
# Command contract from the project deliverables checklist.
# Every target runs module-style from the repository root so that
# "src." imports resolve.
# On Windows the virtual environment interpreter lives in Scripts/,
# on Linux and macOS in bin/. PYTHON picks whichever exists.
# =====================================================================

ifeq ($(OS),Windows_NT)
    PYTHON ?= .venv/Scripts/python.exe
else
    PYTHON ?= .venv/bin/python
endif

.PHONY: help load validate ratios audit screener peer valuation nlp \
        cashflow tearsheets report dashboard api test clean all

help:
	@echo "N100 Financial Intelligence Platform"
	@echo ""
	@echo "  make load       Load all Excel files into data/nifty100.db"
	@echo "  make validate   Run the validation framework"
	@echo "  make ratios     Populate the financial_ratios table"
	@echo "  make audit      Regenerate output/ratio_edge_cases.log"
	@echo "  make screener   Run the full Sprint 3 screener pipeline"
	@echo "  make peer       Recompute peer percentiles only"
	@echo "  make valuation  Generate valuation_summary.xlsx and flags"
	@echo "  make nlp        Parse analysis text and generate pros/cons"
	@echo "  make cashflow   Generate cashflow_intelligence.xlsx and alerts"
	@echo "  make tearsheets Batch build company and sector PDFs"
	@echo "  make report     Generate every Excel, chart and PDF output"
	@echo "  make dashboard  Launch the Streamlit dashboard on :8501"
	@echo "  make test       Run the test suite"
	@echo "  make clean      Remove caches and test artifacts"
	@echo "  make all        load -> ratios -> screener -> valuation -> test"

# ---------------------------------------------------------------------
# Sprint 1 - Data foundation
# ---------------------------------------------------------------------
load:
	$(PYTHON) -m src.etl.sqlite_loader

validate:
	$(PYTHON) -m src.etl.run_validation

# ---------------------------------------------------------------------
# Sprint 2 - Ratio engine
# ---------------------------------------------------------------------
ratios:
	$(PYTHON) -m src.etl.ratio_engine

audit:
	$(PYTHON) -m src.etl.ratio_edge_case_audit

# ---------------------------------------------------------------------
# Sprint 3 - Screener and peer comparison
# ---------------------------------------------------------------------
screener:
	$(PYTHON) -m src.screener.run_screener

peer:
	$(PYTHON) -m src.analytics.peer

report:
	$(PYTHON) -m src.screener.export
	$(PYTHON) -m src.reports.peer_comparison
	$(PYTHON) -m src.reports.radar_charts
	$(PYTHON) -m src.reports.cashflow_intelligence
	$(PYTHON) -m src.reports.batch_reports
	$(PYTHON) -m src.reports.portfolio_summary

# ---------------------------------------------------------------------
# Sprint 5 - Intelligence, NLP and PDF reports
# ---------------------------------------------------------------------
nlp:
	$(PYTHON) -m src.nlp.parser
	$(PYTHON) -m src.nlp.pros_cons_generator

cashflow:
	$(PYTHON) -m src.reports.cashflow_intelligence

tearsheets:
	$(PYTHON) -m src.reports.batch_reports
	$(PYTHON) -m src.reports.portfolio_summary

# ---------------------------------------------------------------------
# Sprint 4 - Dashboard and valuation
# ---------------------------------------------------------------------
valuation:
	$(PYTHON) -m src.analytics.valuation

dashboard:
	$(PYTHON) -m streamlit run src/dashboard/app.py

# ---------------------------------------------------------------------
# Quality gates
# ---------------------------------------------------------------------
test:
	$(PYTHON) -m pytest -q

clean:
	@echo "Removing caches and test artifacts. The database is untouched."
	-@find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	-@rm -rf .pytest_cache .ruff_cache 2>/dev/null || true

all: load ratios screener valuation test
