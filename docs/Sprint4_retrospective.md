# Sprint 4 Retrospective

## N100 Financial Intelligence Platform

**Sprint:** Sprint 4 - Dashboard & Valuation Module (Days 22-28)

**Status:** Completed
**Prepared On:** Day 28

---

# Sprint Objective

Deliver a working eight screen Streamlit dashboard on localhost:8501 that
loads without errors for any of the 92 tickers, plus a valuation module
producing `valuation_summary.xlsx` with FCF yield, P/E flags and
overvaluation labels.

---

# What Was Built

## Dashboard

| Screen | File | Contents |
| --- | --- | --- |
| Home | `01_home.py` | 6 KPI tiles, sector donut, top 5 by composite score, sidebar year selector |
| Company Profile | `02_profile.py` | Search, company card, 6 KPI tiles, revenue/profit bars, ROE-ROCE dual axis, pros and cons |
| Screener | `03_screener.py` | 10 sliders, 6 preset buttons, live table, CSV download |
| Peer Comparison | `04_peers.py` | Group dropdown, Scatterpolar radar, benchmark-highlighted table |
| Trend Analysis | `05_trends.py` | Up to 3 overlaid metrics, YoY annotations |
| Sector Analysis | `06_sectors.py` | Revenue/ROE bubble chart sized by market cap, sector median bars |
| Capital Allocation | `07_capital.py` | Treemap over the 8 patterns with drill-down |
| Annual Reports | `08_reports.py` | BSE PDF links with unavailable badges |

`src/dashboard/utils/db.py` wraps every query in
`@st.cache_data(ttl=600)`. `src/dashboard/utils/ui.py` centralises
formatting so that a missing metric renders as `N/A` on every screen
rather than crashing one of them.

The screener screen drives the same `ScreenerEngine` as the Sprint 3
batch export, so the dashboard and `output/screener_output.xlsx` cannot
disagree about what a filter means.

## Valuation module

`src/analytics/valuation.py` computes FCF yield as free cash flow over
market cap, each company's own five year median P/E, and the sector
median P/E in the latest year. Flags follow the specification: Caution
above 1.5x the sector median, Discount below 0.7x, Fair in between.

Result across the 92 companies: 46 Fair, 30 Discount, 14 Caution, and 2
unflagged because they have no valuation data at all.

---

# Exit Criteria

| Criterion | Result |
| --- | --- |
| All 8 screens load without errors for any of the 92 tickers | Pass |
| Company Profile loads in under 3 seconds | Pass - p95 0.16s, worst case 0.99s |
| Screener CSV download produces valid headers | Pass |
| `valuation_summary.xlsx` has 92 rows with all required columns | Pass |
| Test suite | Pass - 183 tests, up from 156 |

The 92-ticker sweep ran every company through the Profile, Trends and
Reports screens: 270 page renders, zero exceptions after the fix below.

---

# Defect Found and Fixed

**PNB crashed the Company Profile screen.**

`calculate_roce` raised `TypeError: unsupported operand type(s) for +:
'NoneType' and 'int'`. PNB reports no operating profit in any of its 61
rows, which is normal for a bank, and the profile screen guarded only
equity and borrowings before calling the function.

The fix went into `calculate_roce` itself rather than the screen. Three
call sites now depend on that function, and guarding each caller
separately would have left the same trap for the next one. The function
returns `None` when any input is missing, which is what the rest of the
pipeline already expects.

This is exactly the class of bug the Day 27 sweep exists to catch: it
only appears on 1 of 92 companies and would have surfaced during the
demo.

---

# Decisions

## Annual report link checking is opt-in

The sprint guide asks for a "Report unavailable" badge when a URL
returns 404. Verifying every link on each render would fire dozens of
requests to bseindia.com behind a single page load and break the three
second target. The screen renders instantly from the database, flags
missing URLs immediately, and only contacts BSE when the analyst ticks
the verification box. Results are cached for an hour.

## Preset buttons approximate three presets

The guide specifies ten sliders, and three preset rules cannot be
expressed as one:

| Preset | Rule that has no slider | Dashboard | Excel |
| --- | --- | --- | --- |
| Debt-Free Blue Chip | `D/E == 0` exactly, revenue > 5,000 Cr | 33 | 2 |
| Dividend Champion | payout ratio < 80% | 33 | 30 |
| Turnaround Watch | D/E falling year on year | 40 | 34 |

The screen documents this in an expander pointing at
`make screener` for the full rules. The alternative, adding sliders the
guide did not ask for, would have diverged from the specification.

## Composite score is computed in process

`get_universe()` builds the screening universe and scores it inside the
dashboard rather than reading a scored table. The composite score is
cross-sectional, so it has to be recomputed whenever the universe
changes. The ten minute cache makes this a one-off cost per session.

---

# Data Findings

| Finding | Detail |
| --- | --- |
| Only 10 broad sectors exist | The project document and Sprint 4 guide both refer to 11 sectors, but `sectors` contains 10. The donut renders the 10 actual sectors plus an Unclassified bucket for the 2 orphan tickers |
| `prosandcons` covers 16 of 92 companies | The profile screen shows an explanatory note rather than an empty panel for the other 76 |
| 52 annual report URLs are missing | Those years render the red unavailable badge |
| 3 companies have under 10 years of history | ADANIGREEN, JIOFIN and LICI. Charts show the available history with a caption |
| 2 tickers never appear in the selector | ULTRACEMCO and UNIONBANK have no company master record, so they cannot be searched for. They still appear in aggregate metrics |
| One capital allocation sign combination is unnamed | The guide lists eight patterns, but two of them (Reinvestor and Shareholder Returns) share the `(+,-,-)` signs, so only seven of the eight possible combinations are named. ICICIPRULI and JIOFIN are `(-,+,-)` and render as Unknown Pattern, which the screen explains |
| Average ROE reads 122.63% | Skewed by the same source defect behind the Sprint 2 ROE anomalies: a few companies report equity that is not on the same scale as their profit. The tile carries a tooltip giving the median (15.8%) and pointing at the edge case log |

---

# Technical Debt Carried Forward

1. **`make` is still not installed on the development machine.** Targets
   were verified by running the underlying modules directly.
2. **The valuation module reads simulated multiples.** Every flag is a
   demonstration of the logic, not an investment view. The workbook
   carries a Notes sheet saying so.
3. **The 92-ticker sweep is a manual QA script**, not part of
   `make test`. The suite covers the eight screens plus three
   regression tickers to keep the default run fast.
4. **Sector-relative composite score is computed but not surfaced** on
   any screen yet.

---

# Lessons Learned

- Sweeping every ticker through every screen found a defect that no
  amount of spot-checking would have. One company in 92 broke a screen,
  and it was a bank, which is the segment most likely to be demoed.
- Fix a missing-data crash in the shared function, not in the caller
  that happened to hit it first.
- When a specification limits the UI, say so in the UI. The screener
  presets genuinely cannot reproduce the batch export, and a one
  paragraph expander is cheaper than an analyst filing a bug.

---

# Recommendation for Sprint 5

Sprint 5 covers cash flow intelligence, NLP over the pros and cons and
analysis tables, company tearsheets and sector PDFs. Two constraints
carry forward: `prosandcons` covers only 16 companies and `analysis`
only 20, so any NLP deliverable should state its coverage up front
rather than implying it spans the index.
