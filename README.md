# N100 Financial Intelligence Platform

Production-grade analytics for the 92 Nifty 100 companies present in the
supplied datasets: ETL pipeline, financial ratio engine, investment
screener, composite health scoring and peer comparison.

**Progress: Sprint 4 complete (Day 28 of 45).**

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
│   ├── peer_comparison.xlsx
│   ├── valuation_summary.xlsx
│   └── valuation_flags.csv
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
│   │   ├── peer.py              Peer percentile ranking
│   │   └── valuation.py         FCF yield and overvaluation flags
│   │
│   ├── etl/
│   │   ├── sqlite_loader.py     Excel to SQLite
│   │   ├── validator.py         Validation rules
│   │   ├── run_validation.py    Validation runner
│   │   ├── ratio_engine.py      Populates financial_ratios
│   │   └── ratio_edge_case_audit.py
│   │
│   ├── dashboard/
│   │   ├── app.py               Streamlit entry point
│   │   ├── pages/               8 screen files
│   │   └── utils/
│   │       ├── db.py            Cached data loader (ttl=600)
│   │       └── ui.py            Shared formatting helpers
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
| `make valuation` | Generate `valuation_summary.xlsx` and the flags CSV |
| `make report` | Generate all Excel reports and radar charts |
| `make dashboard` | Launch the Streamlit dashboard on `localhost:8501` |
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

### Sprint 4 - Dashboard & Valuation

- Eight screen Streamlit dashboard with a ten minute query cache
- Valuation module: FCF yield, sector median P/E and
  Caution / Discount / Fair flags

---

## Running the Dashboard

```bash
streamlit run src/dashboard/app.py
```

The app serves on **http://localhost:8501**. Run `make ratios`,
`make screener` and `make valuation` first so every screen has data.

### Screens

| # | Screen | What it shows |
| --- | --- | --- |
| 1 | **Home** | Six index-level KPI tiles, a sector breakdown donut, the top five companies by composite quality score, and a sidebar year selector that re-points the valuation tiles |
| 2 | **Company Profile** | Search by name or ticker, then a company card, six KPI tiles, a ten-year revenue and net profit bar chart, a dual-axis ROE/ROCE line chart, and analyst pros and cons |
| 3 | **Screener** | Ten metric sliders plus six preset buttons. The results table updates live and downloads as CSV |
| 4 | **Peer Comparison** | Pick one of the 11 peer groups, see a radar of any member against the peer average, and a side-by-side table with the benchmark highlighted |
| 5 | **Trend Analysis** | Overlay up to three metrics across ten years, each point annotated with its year-on-year change |
| 6 | **Sector Analysis** | Revenue against ROE as a bubble chart sized by market cap and coloured by sub-sector, plus sector median bars |
| 7 | **Capital Allocation** | A treemap of every company grouped by the eight capital allocation patterns, with drill-down into any pattern |
| 8 | **Annual Reports** | Available report years with clickable BSE PDF links. Missing links show a red *Report unavailable* badge; live link checking is opt-in |

Screener presets on screen approximate three of the six preset rules,
because the specified ten sliders cannot express an equality test, a
payout cap or a year-on-year direction. Run `make screener` for
`output/screener_output.xlsx`, which applies every rule in full. The
screen explains this in place.

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
183 passed
```

This includes the 14 data quality rule tests required by the Sprint 3
exit criteria and the headless dashboard smoke tests that load all
eight screens.

---

## Author

**Raj Sarania**
Summer Internship Program (SIP)
Data Analyst @Bluestock Fintech
