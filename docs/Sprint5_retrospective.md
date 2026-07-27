# Sprint 5 Retrospective

## N100 Financial Intelligence Platform

**Sprint:** Sprint 5 - Intelligence, NLP & PDF Reports (Days 29-35)

**Status:** Completed
**Prepared On:** Day 35

---

# Sprint Objective

Auto-generate pros and cons for all 92 companies with confidence scores,
classify every company by CFO quality, CapEx intensity and capital
allocation pattern, and generate 92 company tearsheet PDFs plus 11 sector
PDFs with no text overflow or layout errors.

---

# What Was Built

| Deliverable | Output | Result |
| --- | --- | --- |
| Analysis text parser | `output/analysis_parsed.csv` | 63 values parsed, 17 logged as failures |
| Parse failure log | `output/parse_failures.csv` | 17 rows, all TTM or Last Year labels |
| Pros and cons generator | `output/pros_cons_generated.csv` | 519 statements, 381 pros and 138 cons |
| Cash flow intelligence | `output/cashflow_intelligence.xlsx` | 92 rows, 3 sheets |
| Distress alerts | `output/distress_alerts.csv` | 13 companies |
| Pattern changes | `output/pattern_changes.csv` | 530 year-over-year moves |
| Company tearsheets | `reports/tearsheets/` | 91 PDFs, 85 to 106 KB |
| Skipped tearsheets | `output/skipped_tearsheets.csv` | 1 company |
| Sector reports | `reports/sector/` | 11 PDFs |
| Portfolio summary | `reports/portfolio/portfolio_summary.pdf` | 93 pages, 145 KB |

---

# Exit Criteria

| Criterion | Result |
| --- | --- |
| At least 1 pro and 1 con for every company | Pass - 0 gaps |
| All tearsheets exist and are at least 30 KB | Pass - 91 of 91, smallest 85 KB |
| No text overflow and no blank pages | Pass - all 91 are exactly 2 pages |
| `cashflow_intelligence.xlsx` has 92 rows with all required columns | Pass |
| Test suite | Pass - 229 tests, up from 183 |

The guide allows the tearsheet count to be 92 minus skipped tickers.
JIOFIN was skipped because it carries 2 years of data against the 3 year
floor, so 91 is the expected total.

Page count is used as the overflow check. ReportLab flows content that
does not fit onto an extra page, so a tearsheet that is exactly 2 pages
cannot have overflowed its frames. All 91 are exactly 2 pages.

---

# An Independent Check That Passed

The Day 29 cross-validation turned out to be the most useful thing in
the sprint. The analysis dataset carries the vendor's own published 5
year growth figures as text, which gave a way to check the Sprint 2 CAGR
engine against a source it had never seen.

| Company | Metric | Vendor | Computed | Divergence |
| --- | --- | --- | --- | --- |
| HDFCBANK | Sales growth | 22.0% | 21.95% | 0.05 |
| HDFCBANK | Profit growth | 23.0% | 23.87% | 0.87 |
| INFY | Sales growth | 13.0% | 13.20% | 0.20 |
| INFY | Profit growth | 11.0% | 11.24% | 0.24 |
| SBILIFE | Sales growth | 24.0% | 24.23% | 0.23 |
| SBILIFE | Profit growth | 6.0% | 7.37% | 1.37 |
| TCS | Sales growth | 10.0% | 10.46% | 0.46 |
| TCS | Profit growth | 8.0% | 7.87% | 0.13 |

All 8 comparisons agree within 1.4 percentage points against a 5 point
tolerance. The vendor rounds to whole numbers, which accounts for most of
the remaining gap. This is independent confirmation that the CAGR engine
and the period-ordering logic are both correct.

---

# Decisions

## The exit criterion needed a relative fallback

Implementing the 24 specified rules exactly produced a gap: 47 companies
tripped no con rule and 4 tripped no pro rule, against an exit criterion
requiring at least one of each for every company.

The gap was not a bug. TCS, ITC and NESTLEIND all carry negative net
debt, interest coverage above 40x, rising revenue and no loss, so none of
the 12 con rules apply to them. BHEL sits at the other end with 1.2% ROE,
3% operating margin and revenue shrinking at 4.7% a year, so none of the
12 pro rules apply.

Two extra rules were added rather than loosening the specified 24:

- `PRO-13` and `CON-13` name the company's strongest and weakest metric
  relative to its sector.
- They fire only when no absolute rule did.
- Their confidence is capped at 78, below the absolute rules, and the
  text says "no absolute red flag, but ranks in only the Nth percentile",
  so a relative weakness can never be read as a red flag.

The two tickers with no sector are ranked against the whole index
instead, since a group of two carries no ranking information.

## The distress flag needs a sector caveat

`CFO < 0 AND CFF > 0` flagged 13 companies, of which 9 are profitable
Financials: AXISBANK, BAJAJFINSV, BAJFINANCE, BANKBARODA, CHOLAFIN, PFC,
PNB, RECLTD and SHRIRAMFIN. BAJFINANCE was flagged as distressed on
14,451 Cr of net profit.

For a lender this is the ordinary signature of growth: expanding the loan
book is an operating outflow and taking deposits or borrowing is a
financing inflow. The flag itself is left exactly as specified, and
`distress_alerts.csv` carries a `structurally_normal_for_sector` column
plus an `interpretation` column so a profitable lender is never read as
distressed. GRASIM and M&M are also flagged and both run large financing
arms, so the same mechanism is at work, but they are left unmarked
because they are not classified as Financials.

This mirrors the carve-out the sprint guide itself applies to the D/E
screener filter.

## Arrows are drawn, not typed

The portfolio summary needs up, down and flat arrows. The standard PDF
fonts have no arrow glyphs, and substituting one silently renders as a
blank box in some viewers, so the arrows are ReportLab polygons.

## Charts are matplotlib images

Tearsheet charts are rendered by matplotlib into an in-memory PNG and
placed as images rather than redrawn in ReportLab primitives. That keeps
one charting approach across the project instead of two.

---

# Data Findings

| Finding | Detail |
| --- | --- |
| The analysis table covers 5 companies | 20 rows for HDFCBANK, INFY, SBILIFE, TCS and one other, not 92. Every parser output is a 5 company sample and says so on each run |
| 17 of 80 text values do not parse | All are `TTM:` or `Last Year:` labels. The specified regex requires a digit before "Year", so these are correct rejections rather than failures |
| `prosandcons` was not usable as a source | It covers 16 companies, so all 519 statements are generated from financial rules rather than the supplied text |
| CON-09 never fires | No company shows EPS declining across 3 strictly consecutive years. The rule is correct and simply does not apply to this dataset |
| The cashflow table holds 100 tickers | 8 more than the platform universe. Without a filter the intelligence report ran to 100 rows with 8 unclassified, so it is now restricted to the 92 companies that survived the Sprint 2 statement joins |
| Operating profit stands in for EBITDA | The supplied datasets carry no depreciation line. Recorded on the Notes sheet |
| 11 sector PDFs, 10 real sectors | The eleventh is the Unclassified bucket holding the two tickers with no company master record |

---

# Technical Debt Carried Forward

1. **No PDF renderer is installed**, so overflow was verified by page
   count rather than by rendering each page to an image. The four chart
   types were inspected individually.
2. **`make` is still not installed.** Targets were verified by running
   each module directly.
3. **The tearsheet batch takes several minutes** for 91 companies because
   each one renders four matplotlib figures. Acceptable as a batch job,
   but it is not something to run inside a web request.
4. **Sector reports carry no charts**, only median tiles and a company
   table. The guide asks for medians and a company list, which is met,
   but a chart per sector would read better.

---

# Lessons Learned

- A dataset that duplicates work already done is worth more as a check
  than as a source. The analysis table only covers 5 companies, but
  those 5 confirmed the CAGR engine against an independent figure.
- An exit criterion can conflict with the rules that feed it. Saying so
  and adding a labelled fallback is better than quietly loosening the
  rules until the number comes out right.
- A rule that is correct in general can be wrong for a sector. Negative
  operating cash flow means trouble for a manufacturer and growth for a
  lender, and the output has to carry that distinction or it will be
  misread.

---

# Recommendation for Sprint 6

Sprint 6 covers clustering, the FastAPI server with 16 endpoints, the
pytest HTML report and final documentation. The API should read the
existing outputs rather than recompute them; the composite score and the
tearsheet batch are both too slow to sit inside a request. The cached
loader in `src/dashboard/utils/db.py` is the pattern to follow.
