# N100 Financial Intelligence Platform

Production-grade analytics for the 92 Nifty 100 companies present in the
supplied datasets: ETL pipeline, financial ratio engine, investment
screener, composite health scoring and peer comparison.

**Status: Complete — all 6 sprints, 23 of 23 deliverables, 20 of 20 acceptance gates passing.**

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
│   ├── valuation_flags.csv
│   ├── analysis_parsed.csv
│   ├── parse_failures.csv
│   ├── pros_cons_generated.csv
│   ├── cashflow_intelligence.xlsx
│   ├── distress_alerts.csv
│   ├── pattern_changes.csv
│   └── skipped_tearsheets.csv
│
├── reports/
│   ├── dq_review_report.md
│   ├── radar_charts/            92 per-company radar PNGs
│   ├── tearsheets/              91 two-page company PDFs
│   ├── sector/                  11 sector PDFs
│   └── portfolio/               portfolio_summary.pdf
│
├── src/
│   ├── analytics/
│   │   ├── ratios.py            Profitability, leverage, efficiency
│   │   ├── cashflow_kpis.py     FCF, CFO quality, CapEx, allocation
│   │   ├── cagr.py              CAGR engine with edge case handling
│   │   ├── periods.py           Financial period parsing and ordering
│   │   ├── peer.py              Peer percentile ranking
│   │   ├── valuation.py         FCF yield and overvaluation flags
│   │   ├── clustering.py        KMeans company archetypes
│   │   └── statistics.py        Correlation, outliers, percentiles
│   │
│   ├── api/
│   │   ├── main.py              FastAPI app, CORS, request logging
│   │   ├── dependencies.py      Cached data access
│   │   └── routers/             7 routers, 20 endpoints
│   │
│   ├── nlp/
│   │   ├── parser.py            Analysis text parsing
│   │   ├── features.py          Per-company history for the rules
│   │   └── pros_cons_generator.py  24 rules + relative fallback
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
│       ├── radar_charts.py      Radar chart generation
│       ├── cashflow_intelligence.py
│       ├── tearsheet.py         2-page company PDF
│       ├── sector_report.py     Per-sector PDF
│       ├── batch_reports.py     Day 34 batch runner
│       └── portfolio_summary.py Portfolio PDF
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
| `make nlp` | Parse the analysis text and generate pros/cons |
| `make cashflow` | Generate `cashflow_intelligence.xlsx` and alerts |
| `make tearsheets` | Batch build the company, sector and portfolio PDFs |
| `make cluster` | KMeans clustering and the elbow plot |
| `make stats` | Correlation heatmap, outliers, percentile table |
| `make indexes` | Create SQLite indexes and benchmark them |
| `make api` | Launch the FastAPI server on `localhost:8000` |
| `make acceptance` | Run the 20 acceptance gates and build the checklist |
| `make archive` | Copy all 23 deliverables to `output/final_deliverables/` |
| `make testreport` | Run tests and write `reports/pytest_report.html` |
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

### Sprint 5 - Intelligence, NLP & PDF Reports

- Analysis text parser, which independently confirmed the CAGR engine
  against the vendor's published figures to within 1.4 points
- 24 rule pros and cons generator with confidence scores, plus a
  sector-relative fallback so every company is covered
- Cash flow intelligence: CFO quality, CapEx intensity, distress and
  deleveraging flags, capital allocation patterns
- 91 two-page company tearsheets, 11 sector reports and a 93 page
  portfolio summary, all built with ReportLab

### Sprint 6 - API Server, Clustering & Final QA

- KMeans clustering of all 92 companies into 5 named archetypes
- FastAPI server, 16 endpoints under `/api/v1`, OpenAPI 3 spec exported
- Correlation heatmap, sector-relative outlier detection, percentile table
- 12 SQLite indexes, load test, 11-page analyst guide, acceptance checklist

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

## Running the API

```bash
uvicorn src.api.main:app --port 8000
```

Interactive documentation is at **http://localhost:8000/docs**. The API
and the dashboard can run simultaneously; they use different ports.

All 16 endpoints are read-only and sit under `/api/v1`:

| Endpoint | Returns |
| --- | --- |
| `GET /health` | Status, row counts for all 10 tables, uptime, version |
| `GET /companies` | All 92 companies; filter by `sector`, `market_cap_category`, `search` |
| `GET /companies/{ticker}` | Full profile: master record, sector, latest KPIs |
| `GET /companies/{ticker}/pl` | P&L history; `from_year` / `to_year` as `YYYY-MM` |
| `GET /companies/{ticker}/bs` | Balance sheet history |
| `GET /companies/{ticker}/cashflow` | Cash flow history |
| `GET /companies/{ticker}/ratios` | Computed KPIs per year, or one `year` |
| `GET /companies/{ticker}/tearsheet` | The tearsheet PDF as a download |
| `GET /companies/{ticker}/peers/compare` | Radar data: 8 axes, peer average, benchmark |
| `GET /companies/{ticker}/documents` | Annual report links with `is_url_valid` |
| `GET /screener` | Ranked results for any threshold combination, or a `preset` |
| `GET /sectors` | Every sector with company count and medians |
| `GET /sectors/{sector}/companies` | Companies in a sector with latest KPIs |
| `GET /peers/{group_name}` | Peer group with a percentile rank per metric |
| `GET /market-cap/{ticker}` | Valuation multiples 2019-2024 (SIMULATED) |
| `GET /portfolio/stats` | P10 to P90, mean and std for 10 KPIs |

Examples:

```bash
curl "http://localhost:8000/api/v1/screener?min_roe=15&max_de=1"
```

```bash
curl http://localhost:8000/api/v1/companies/TCS/ratios
```

Returns `400` for an out-of-range threshold or a bad year format, `404`
for an unknown ticker, sector or peer group.

---

## Data Notes

- All monetary values are in **INR Crore**.
- `market_cap` and `stock_prices` are **SIMULATED** datasets. Any report
  showing P/E, P/B, dividend yield or market cap labels them accordingly.
- The supplied `companies.xlsx` is truncated at 92 rows, so eight tickers
  appear in the financial statements with no company master record. This
  and other source defects are documented in `docs/Sprint3_retrospective.md`.
- The `analysis` table covers **5 companies**, not 92, so
  `output/analysis_parsed.csv` is a 5 company sample. It is used as an
  independent check on the CAGR engine rather than as a data source.
- `prosandcons` covers 16 companies, so every statement in
  `output/pros_cons_generated.csv` is generated from financial rules.
- The distress flag marks banks and NBFCs whose lending growth produces
  negative operating cash flow. `output/distress_alerts.csv` carries a
  `structurally_normal_for_sector` column that separates those from
  genuine concerns. See `docs/Sprint5_retrospective.md`.

---

## Testing

```bash
python -m pytest -q
```

Expected result:

```text
298 passed
```

This includes the 14 data quality rule tests required by the Sprint 3
exit criteria and the headless dashboard smoke tests that load all
eight screens.

---

## Author

**Raj Sarania**
Summer Internship Program (SIP)
Data Analyst @Bluestock Fintech
