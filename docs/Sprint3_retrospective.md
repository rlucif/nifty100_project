# Sprint 3 Retrospective

## N100 Financial Intelligence Platform

**Sprint:** Sprint 3 - Screener & Peer Comparison Engine (Days 15-21)

**Status:** Completed with two documented data limitations
**Prepared On:** Day 21

---

# Sprint Objective

Deliver a fully functional financial screener with six preset filters and
custom threshold support, and compute peer percentile rankings for all 11
peer groups across 10 metrics.

---

# Sprint 2 Items Closed First

Three Sprint 2 exit criteria were still open when Sprint 3 began. They were
closed before screener work started, because the growth presets depend on
them.

| Item | Resolution |
| --- | --- |
| CAGR columns absent from `financial_ratios` | `revenue_cagr_5yr`, `pat_cagr_5yr`, `eps_cagr_5yr` and `composite_quality_score` added and populated |
| `output/capital_allocation.csv` never generated | Exported by `ratio_engine.py`, 1,065 rows |
| `src/analytics/cashflow_kpis.py` missing | Cash flow KPIs moved out of `ratios.py`, re-exported for compatibility |
| `src/etl/ratio_edge_case_audit.py` empty | Implemented; regenerates the edge case log and reproduces the 18 ROE anomalies previously found by hand |

The Sprint 2 retrospective recorded CAGR integration as deferred technical
debt on the grounds that the schema had no CAGR fields. That reasoning was
inverted: `src/etl/schema.sql` already declared all four columns, and only
the live database file was missing them. The columns were added with
`ALTER TABLE` and back-filled.

---

# What Was Built

## Screening universe

`src/screener/universe.py` assembles one row per company at its latest
financial year, joining four tables. Two structural problems had to be
solved first.

**Duplicate company-year rows.** Sprint 2 deliberately preserved source
duplicates, so the Sprint 2 joins fan out: PNB carries 60 rows for 12
distinct years. Any screener built directly on `financial_ratios` would
count companies more than once. All analytics now de-duplicate on
company-year before use.

**Inconsistent period labels.** Companies do not share a financial year
end, and the raw files mix `Mar 2024`, `Dec 2023`, `TTM`, `Mar 2023 15`
and `Mar 2016 9m`. `src/analytics/periods.py` centralises parsing so
CAGR windows, latest-year selection and the `market_cap` join all agree
on what the latest year is.

## Filter engine

`src/screener/engine.py` supports all 15 filterable metrics. Two business
rules live in code rather than config:

1. **Financials D/E exemption.** An upper-bound D/E filter does not reject
   banks, NBFCs or insurers. The exemption deliberately does *not* apply
   to the equality test used by Debt-Free Blue Chip, because a bank with a
   D/E of 8.2 is not debt free. The sprint guide wording is "when D/E max
   filter is applied", which supports the narrower reading.
2. **Debt Free interest coverage.** `interest_coverage` is null precisely
   when interest expense is zero. Such a company has infinite coverage and
   passes any ICR minimum. For every other metric, a missing value fails.

## Composite quality score

Weighted 35% profitability, 30% cash quality, 20% growth, 15% leverage.
Each component is winsorised at P10/P90 before scaling to 0-100.

Winsorisation is doing real work here rather than being a formality. The
source data contains ROE values such as BEL at 4,744% and INDIGO at 893%,
caused by equity capital and profit figures being on different scales.
Without capping, those two companies would compress every other company
into a narrow band at the bottom of the profitability axis.

A missing metric scores a neutral 50 rather than 0. Scoring it 0 would
punish a company twice for a documented edge case: a turnaround company
already has a null PAT CAGR because its base year was a loss, and
assigning it the worst possible growth score would compound that.

A sector-relative variant normalises within `broad_sector`.

## Peer percentiles

`src/analytics/peer.py` computes SQL-style `PERCENT_RANK`,
`(rank - 1) / (n - 1)`, on a 0-100 scale for 10 metrics across the 11 peer
groups, writing 550 rows to the new `peer_percentiles` table.
Debt-to-equity is inverted so less debt earns the higher rank. Companies
absent from every peer group return the message `No peer group assigned`
rather than raising.

---

# Exit Criteria

| Criterion | Result |
| --- | --- |
| 6 presets each return 5-50 companies | **4 of 6** - see limitations |
| `peer_comparison.xlsx` has 11 sheets | Pass - 11 sheets |
| Peer percentile ranks correct | Pass - spot-checked on IT Services and FMCG |
| All 14 DQ rule unit tests pass | Pass - 14/14 |
| Full test suite | Pass - 156/156 |

Preset results on the delivered dataset:

| Preset | Companies | Status |
| --- | --- | --- |
| Quality Compounder | 22 | Pass |
| Value Pick | 2 | Below range |
| Growth Accelerator | 18 | Pass |
| Dividend Champion | 30 | Pass |
| Debt-Free Blue Chip | 2 | Below range |
| Turnaround Watch | 34 | Pass |

---

# Data Limitations

Both preset shortfalls come from the supplied data, not the filter logic.
The specified thresholds are retained as the shipped defaults because the
sprint guide is the governing specification and they are correct for live
market data. The calibrated alternatives are documented in
`config/screener_config.yaml` for the analyst to switch.

## Value Pick returns 2 companies

`P/E` and `P/B` come from the simulated `market_cap` dataset, in which the
two are uncorrelated (r = -0.11). In real markets they move together, so a
company that is cheap on earnings is usually also cheap on book value.
15 companies pass `P/E < 20` and 9 pass `P/B < 3.0`, but only 2 pass both,
which is roughly what independence predicts.

Relaxing to `P/E < 30` and `P/B < 6.0` returns 13 companies.

## Debt-Free Blue Chip returns 2 companies

Only 3 of 92 companies report literally zero borrowings in their latest
year. Using `D/E < 0.05`, the conventional market definition of debt free,
returns 16 companies.

## Source data defects confirmed

| Defect | Detail |
| --- | --- |
| `companies.xlsx` truncated | 92 rows ending part way through the alphabet. ULTRACEMCO, UNIONBANK, UNITDSPR, VBL, VEDL, WIPRO, ZOMATO and ZYDUSLIFE appear in the statements with no master record |
| SBIN missing from statements | SBIN is the designated Public Sector Banks benchmark but has no `financial_ratios` rows, so that peer group has no highlighted benchmark |
| 119 duplicate company-year rows | Preserved per the Sprint 2 decision; de-duplicated in analytics |
| ROE/ROCE snapshot mismatches | 18 companies, all categorised in `output/ratio_edge_cases.log` |

---

# Technical Debt Carried Forward

1. **`composite_quality_score` is latest-year only.** The score is
   cross-sectional, so back-filling it onto historical rows would imply a
   comparison that was never made. Sprint 4 should decide whether it wants
   a historical score series.
2. **ROCE is still not persisted.** It is recomputed in the universe
   builder each run because the Sprint 2 schema has no ROCE column.
3. **`make` is not installed on the development machine.** The `Makefile`
   matches the documented command contract but was not executed; every
   target was verified by running its underlying module directly.
4. **`book_value_per_share` remains unreconciled**, carried over from
   Sprint 2.

---

# Lessons Learned

- Verify a deferral before accepting it. The CAGR columns were recorded as
  blocked by the schema when the schema already defined them.
- Simulated data does not preserve the correlations that real screening
  thresholds assume. Presets that filter on two related valuation metrics
  behave very differently once that relationship is removed.
- A filter engine needs to distinguish "missing because the concept does
  not apply" from "missing because the data is absent". Debt Free interest
  coverage is the clearest case: the same null means infinite coverage,
  not unknown coverage.

---

# Recommendation for Sprint 4

The screener and peer layers should now be treated as dependencies.
Sprint 4 should consume `composite_quality_score`, `peer_percentiles` and
the screener presets rather than modifying them, and should surface the
SIMULATED labelling on every valuation metric it displays.
