# N100 Financial Intelligence Platform

Production-grade analytics for the 92 Nifty 100 companies present in the
supplied datasets: ETL pipeline, financial ratio engine, investment
screener, composite health scoring and peer comparison.

**Progress: Sprint 3 complete (Day 21 of 45).**

---

## Project Structure

```text
.
├── config/
│   └── screener_config.yaml     Analyst-editable thresholds and presets
│
├── data/
│   ├── nifty100.db              SQLite database
│   ├── raw/                     Core Excel datasets
│   └── supporting/              Sectors, peer groups, market cap
│
├── docs/                        Retrospectives and audit summaries
│
├── output/                      Generated data deliverables
│   ├── load_audit.csv
│   ├── validation_failures.csv
│   ├── capital_allocation.csv
│   ├── ratio_edge_cases.log
│   ├── screener_output.xlsx
│   └── peer_comparison.xlsx
│
├── reports/
│   ├── dq_review_report.md
│   └── radar_charts/            92 per-company radar PNGs
│
├── src/
│   ├── analytics/
│   │   ├── ratios.py            Profitability, leverage, efficiency
│   │   ├── cashflow_kpis.py     FCF, CFO quality, CapEx, allocation
│   │   ├── cagr.py              CAGR engine with edge case handling
│   │   ├── periods.py           Financial period parsing and ordering
│   │   └── peer.py              Peer percentile ranking
│   │
│   ├── etl/
│   │   ├── sqlite_loader.py     Excel to SQLite
│   │   ├── validator.py         Validation rules
│   │   ├── run_validation.py    Validation runner
│   │   ├── ratio_engine.py      Populates financial_ratios
│   │   └── ratio_edge_case_audit.py
│   │
│   ├── screener/
│   │   ├── universe.py          Latest-year screening universe
│   │   ├── engine.py            Filters, presets, composite score
│   │   ├── export.py            screener_output.xlsx
│   │   └── run_screener.py      Sprint 3 pipeline runner
│   │
│   └── reports/
│       ├── peer_comparison.py   peer_comparison.xlsx
│       └── radar_charts.py      Radar chart generation
│
├── tests/
├── Makefile
├── requirements.txt
└── README.md
```

---

## Installation

```bash
python -m venv .venv
```

Activate the environment:

**Windows**

```bash
.venv\Scripts\activate
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Commands

| Command | Purpose |
| --- | --- |
| `make load` | Load all Excel files into `data/nifty100.db` |
| `make validate` | Run the validation framework |
| `make ratios` | Populate the `financial_ratios` table |
| `make audit` | Regenerate `output/ratio_edge_cases.log` |
| `make screener` | Run the full Sprint 3 screener pipeline |
| `make peer` | Recompute peer percentiles only |
| `make report` | Generate all Excel reports and radar charts |
| `make test` | Run the test suite |
| `make clean` | Remove caches and test artifacts, database untouched |

If `make` is not installed, run any target's module directly, for example:

```bash
python -m src.screener.run_screener
```

---

## Features Implemented

### Sprint 1 - Data Foundation

- Excel ingestion into SQLite across 12 datasets
- Schema validation, duplicate detection, missing value checks
- Load audit and validation failure reporting

### Sprint 2 - Financial Ratio Engine

- Profitability, leverage and efficiency ratios
- Cash flow KPIs and the 8-pattern capital allocation classifier
- CAGR engine covering zero base, turnaround, decline-to-loss and
  both-negative cases
- 1,184 company-year rows in `financial_ratios`
- Edge case audit log with every anomaly categorised

### Sprint 3 - Screener & Peer Comparison

- 15 filterable metrics and 6 preset screeners
- Composite quality score, 0-100, with P10/P90 winsorisation and a
  sector-relative variant
- Peer percentile ranks for 10 metrics across 11 peer groups
- Colour-coded Excel exports and 92 radar charts

---

## Data Notes

- All monetary values are in **INR Crore**.
- `market_cap` and `stock_prices` are **SIMULATED** datasets. Any report
  showing P/E, P/B, dividend yield or market cap labels them accordingly.
- The supplied `companies.xlsx` is truncated at 92 rows, so eight tickers
  appear in the financial statements with no company master record. This
  and other source defects are documented in `docs/Sprint3_retrospective.md`.

---

## Testing

```bash
python -m pytest -q
```

Expected result:

```text
156 passed
```

This includes the 14 data quality rule tests required by the Sprint 3
exit criteria.

---

## Author

**Raj Sarania**
Summer Internship Program (SIP)
Data Analyst @Bluestock Fintech
