# Performance Notes

**Sprint 6 Day 43** — N100 Financial Intelligence Platform

Measured on the development machine (Windows 11, SQLite file database,
single process). All figures are medians unless stated otherwise.

---

## Load test: 10 concurrent screener calls

Ten threads each calling `GET /api/v1/screener` with different
thresholds.

| Measure | Result | Target |
| --- | --- | --- |
| All calls returned HTTP 200 | Yes | Yes |
| Wall clock for all 10 | **0.150 s** | under 10 s |
| Slowest single call | 147 ms | — |
| Median call | 140 ms | — |

Verdict: **PASS**, by roughly 66x.

The concurrent calls each take ~140 ms while a single warm call takes
~13 ms. That gap is the Python GIL serialising ten pandas filter
operations, not I/O contention — the work is CPU-bound in-process. It is
well inside target, so no change was made.

---

## Endpoint latency

Median and p95 over 20 calls each, after cache warm-up.

| Endpoint | Median | p95 |
| --- | --- | --- |
| `/health` | 5.8 ms | 6.8 ms |
| `/portfolio/stats` | 9.8 ms | 13.1 ms |
| `/companies` | 11.1 ms | 12.0 ms |
| `/screener` | 12.5 ms | 49.1 ms |
| `/companies/{ticker}/ratios` | 14.4 ms | 20.5 ms |
| `/sectors` | 17.5 ms | 20.1 ms |
| `/peers/{group}` | 19.1 ms | 21.2 ms |
| `/companies/{ticker}` | 19.7 ms | 23.8 ms |

Nothing approaches a problematic latency.

---

## Dashboard performance

Measured across every ticker in the Company Profile, Trend Analysis and
Annual Reports screens using Streamlit's headless `AppTest` — 270 page
renders in total.

| Screen | Mean | p95 | Worst | Target |
| --- | --- | --- | --- | --- |
| Company Profile | 0.13 s | 0.16 s | 0.99 s | under 3 s |
| Trend Analysis | 0.09 s | 0.13 s | 0.15 s | — |
| Annual Reports | 0.06 s | 0.08 s | 0.08 s | — |

Verdict: **PASS**. The worst single render is 0.99 s, a third of budget.

The first page load of a session is slower because it builds the
screening universe and the composite score. `@st.cache_data(ttl=600)`
means that cost is paid once per ten minutes rather than per interaction.

---

## End-to-end: both servers together

FastAPI on 8000 and Streamlit on 8501 were started simultaneously.

| Check | Result |
| --- | --- |
| FastAPI `/api/v1/health` | HTTP 200 in 0.216 s |
| Streamlit root | HTTP 200 in 0.218 s |
| FastAPI `/docs` | HTTP 200 |
| Port conflict | None |
| Health row counts | All 10 tables populated |

---

## SQLite indexes

Twelve indexes were added on the columns every analytics query filters
on. A composite `(company_id, year)` index also serves lookups on
`company_id` alone, so no separate single-column index was created for
those tables.

| Query | Before | After | Change |
| --- | --- | --- | --- |
| `financial_ratios` by company | 0.111 ms | 0.056 ms | −49% |
| `profitandloss` by company + year | 0.091 ms | 0.028 ms | −69% |
| `peer_percentiles` by company | 0.066 ms | 0.036 ms | −45% |

Indexes created:

```text
idx_profitandloss_company_id_year     idx_documents_company_id
idx_balancesheet_company_id_year      idx_sectors_company_id
idx_cashflow_company_id_year          idx_peer_groups_company_id
idx_financial_ratios_company_id_year  idx_peer_percentiles_company_id
idx_market_cap_company_id_year        idx_analysis_company_id
idx_stock_prices_company_id           idx_prosandcons_company_id
```

Regenerate with:

```bash
python -m src.etl.create_indexes
```

Honest caveat: at these table sizes (largest is 5,520 rows) SQLite was
never the bottleneck. The absolute saving is tens of microseconds. The
indexes are worth keeping because they cost nothing and the queries are
called in loops, but they did not fix a real problem.

---

## Where the real cost sits

Ranked by actual wall clock, not by query time:

1. **Tearsheet batch — several minutes for 91 companies.** Each tearsheet
   renders four matplotlib figures. This is the only genuinely slow part
   of the platform. It is a batch job and must stay one; it should never
   sit inside a web request.
2. **Composite score — a full-universe computation.** The score is
   cross-sectional, so it cannot be computed for one company alone. It is
   cached per process in the API (`lru_cache`) and for ten minutes in the
   dashboard.
3. **Radar charts — 92 PNGs.** Same shape of cost as the tearsheets.
4. **Everything else is effectively free.**

No optimisation was applied to items 1 and 3 because both are offline
batch steps whose output is committed to the repository.
