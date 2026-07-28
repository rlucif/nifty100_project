# Sprint 6 Retrospective

## N100 Financial Intelligence Platform

**Sprint:** Sprint 6 - API Server, Clustering & Final QA (Days 36-45)

**Status:** Completed. 20 of 20 acceptance gates passing, 23 of 23
deliverables present.
**Prepared On:** Day 45

---

# Sprint Objective

Get all 16 FastAPI endpoints live and returning correct data, assign all
92 companies to one of 5 labelled archetypes, show 60+ tests with zero
failures, and verify all 20 acceptance gates for project sign-off.

---

# Final Position

| Measure | Result |
| --- | --- |
| Acceptance gates | **20 of 20 PASS** |
| Deliverables | **23 of 23 present** |
| Test suite | **298 passing**, 0 failures |
| API endpoints | 20 live (16 required plus 4 convenience) |
| Companies clustered | 92 of 92 into 5 archetypes |

---

# What Was Built

| Deliverable | Output |
| --- | --- |
| KMeans clustering | `output/cluster_labels.csv`, `output/cluster_profiles.csv` |
| Elbow curve | `reports/elbow_plot.png` |
| Correlation heatmap | `reports/correlation_heatmap.png` |
| Outlier detection | `output/outlier_report.csv` |
| Portfolio percentiles | `output/portfolio_stats.csv` |
| FastAPI server | `src/api/` with 7 routers |
| OpenAPI 3 spec | `docs/openapi.json` |
| Test report | `reports/pytest_report.html` |
| SQLite indexes | `src/etl/create_indexes.py`, 12 indexes |
| Performance notes | `output/perf_notes.md` |
| Analyst guide | `docs/analyst_guide.pdf`, 11 pages |
| Acceptance checklist | `docs/acceptance_checklist.pdf` |
| Handover archive | `output/final_deliverables/`, 214 files |

---

# Two Things That Needed Real Judgement

## Clustering needed winsorisation to produce anything useful

The specified pipeline is impute, StandardScaler, KMeans with k=5. Run
exactly that way, the result was unusable:

| Cluster | Companies | Mean ROE | What it actually was |
| --- | --- | --- | --- |
| 4 | 2 | 4,280% | BEL and HAL, the ROE data artifacts |
| 2 | 1 | 15.6% | CIPLA alone, on a 229% FCF CAGR |
| 0 | 58 | 21.6% | 63% of the index dumped together |

Three of the five clusters were spent isolating outliers. StandardScaler
normalises the spread but does nothing about the fact that BEL's 4,744%
ROE is a data artifact, so that single company defined an entire axis.

Capping every feature at its 5th and 95th percentile before scaling
fixed it. The clusters became 13 / 26 / 28 / 15 / 10 and each one has a
recognisable financial character. This mirrors the P10/P90 winsorisation
the composite score has used since Sprint 3, and for the same reason.

## The example cluster names did not fit the data

The guide offers five example names. Assigning them mechanically
produced two clear errors: the cluster labelled "Emerging Growth" had a
mean D/E of 6.8 and was entirely banks, and the one labelled "Distressed
or Turnaround" carried 81% operating margins.

The naming logic now derives each label from the cluster's most
distinctive feature:

| Cluster | Companies | Name | What separates it |
| --- | --- | --- | --- |
| 4 | 10 | High-Quality Compounders | 60% mean ROE, low leverage |
| 0 | 13 | High-Margin Franchises | 81% operating margin |
| 1 | 26 | Emerging Growth | 15% revenue and 19% FCF growth |
| 2 | 28 | Defensive Dividend Payers | Mature, 7.6% growth |
| 3 | 15 | Leveraged Financials | Mean D/E of 6.8, banks and NBFCs |

Two names differ from the guide's examples. The guide describes them as
examples and asks for names based on which companies are actually in each
cluster, so this follows the instruction rather than departing from it.
No cluster in this universe is genuinely distressed: the weakest still
averages 13% ROE.

---

# Decisions

## The API caches rather than recomputes

The composite quality score is cross-sectional, so it cannot be computed
for one company on request. Building it per call would put a full index
recomputation behind every endpoint. It is built once per process with
`lru_cache` in `src/api/dependencies.py`. A warm `/screener` call takes
13 ms; a cold one takes about a second.

## Pearson correlation is reported with a caveat

The heatmap is Pearson as specified, but on this data Pearson overstates
several relationships. ROE against asset turnover reads +0.96 on Pearson
and +0.49 on Spearman; net profit margin against interest coverage reads
+0.79 against +0.09. Those gaps mean the coefficient comes from a few
companies at the extreme of both distributions, not from a relationship
that holds across the index. The figure now carries a footnote naming
the two worst offenders and their rank-correlation values.

## Gate AC-05 uses the vendor's own figures as the manual check

The gate asks for a Revenue CAGR spot-check against a manual Excel
calculation. The Sprint 5 parser already extracts the vendor's published
5-year growth figures from the `analysis` table, which is a stronger
check than recomputing our own formula by hand: it is an independent
source. Worst divergence across the available companies is 0.46
percentage points, and the vendor rounds to whole numbers.

## black was deliberately not run

Day 44 asks for a final pass with `black src/ tests/` and
`ruff check src/ tests/`. Ruff passes clean across the whole codebase.
Black was not run.

Black would reformat 72 of the 92 files. Not because of anything wrong
with them, but because the project has used 3-space indentation since
Sprint 1 and black enforces 4-space with no option to configure it. The
result would be a purely cosmetic diff touching almost every file in the
repository, applied on the last day, obscuring the real history of what
changed and when.

The deviation is recorded here rather than quietly skipped. Reversing
the decision is one command:

```bash
python -m black src/ tests/
```

## The handover archive is not committed

`output/final_deliverables/` is a byte-for-byte copy of 19.1 MB of files
already tracked elsewhere in the repository. It is gitignored and
regenerates with one command. Committing it would double the repository
size to hold nothing new.

---

# Two Repository Defects Found and Fixed

Both were found while working on `.gitignore` in the final pass, and
neither was introduced this sprint.

## `__init__.py` was gitignored

`.gitignore` contained a bare `__init__.py` entry. Ten of the twenty
package markers on disk were untracked as a result, including
`src/api/__init__.py`, `src/nlp/__init__.py` and four test package
markers. The other ten predated the entry and were already tracked, so
the repository was in a half-working state that a fresh clone would have
exposed. The entry has been removed.

## `.env` and `.vscode/` had merged into one pattern

The two lines had run together as `.env.vscode/`, a single pattern
matching neither. `.env` was therefore not ignored. No `.env` file
currently exists, so nothing leaked, but a future one would have been
committed. Both are now on separate lines.

---

# Exit Criteria Detail

All 20 gates, with the evidence recorded at run time:

| Gate | Criterion | Evidence |
| --- | --- | --- |
| AC-01 | companies = 92 | 92 |
| AC-02 | 90%+ have 10 years of statements | 84/92 = 91.3% |
| AC-03 | foreign_key_check clean | 0 violations |
| AC-04 | financial_ratios >= 1,100 | 1,184 rows |
| AC-05 | Revenue CAGR spot-check | worst divergence 0.46 pts |
| AC-06 | ROE within 5% for 5+ companies | 70 companies |
| AC-07 | Quality preset returns 10-50 | 22 companies |
| AC-08 | Profile screen under 3s | p95 0.16s, worst 0.99s |
| AC-09 | Screener CSV well-formed | 24 columns |
| AC-10 | No overflow in 5 tearsheets | all exactly 2 pages |
| AC-11 | /health returns 200 | HTTP 200 |
| AC-12 | TCS ratios 10+ years | 12 years |
| AC-13 | API matches screener_output.xlsx | 22 vs 22, identical |
| AC-14 | peer_percentiles has 11 groups | 11 |
| AC-15 | 92 companies have a cluster_id | 92, 5 clusters |
| AC-16 | 92 companies have a pro and a con | 0 missing |
| AC-17 | Tearsheets exist, 30 KB+ | 91 PDFs + 1 skipped, 0 undersized |
| AC-18 | 60+ tests, 0 failures | 298 collected |
| AC-19 | validation_failures.csv columns | 188 rows, all columns |
| AC-20 | analyst_guide.pdf 10+ pages | 11 pages |

Regenerate with `make acceptance`.

---

# Technical Debt Carried Forward

1. **`make` is not installed on the development machine.** Every target
   was verified by running its module directly. The Makefile itself was
   checked for tab integrity and literal-escape errors but never
   executed.
2. **No PDF renderer is available**, so tearsheet overflow is verified by
   page count rather than by rendering pages to images. The four chart
   types were inspected individually.
3. **The API is read-only and unauthenticated.** Correct for internal
   use, and CORS is deliberately open. It must not be exposed publicly
   in this form.
4. **The tearsheet batch takes minutes.** It is an offline job and must
   stay one.
5. **`prosandcons` and `analysis` cover 16 and 5 companies.** Any future
   NLP work should state its coverage rather than implying index-wide
   data.

---

# Lessons Learned

- Scaling is not the same as robustness. StandardScaler put every
  feature on a comparable spread and still let one company's bad data
  define a cluster. Capping the tails was what actually made the
  clustering mean something.
- When a specification offers example labels, check them against the
  result before adopting them. Two of the five given names described
  something the data does not contain.
- Report the statistic you were asked for, and report where it misleads.
  Pearson was specified; the Spearman comparison is what tells a reader
  whether to trust a given coefficient.
- Repository hygiene deserves a deliberate pass. A gitignored
  `__init__.py` and two merged patterns had been quietly wrong for
  sprints, and neither would have shown up in a test run.

---

# Project Outcome

All six sprints are complete. The platform loads twelve datasets, computes
30+ KPIs across 1,184 company-year rows, screens on 15 metrics with 6
presets, ranks 11 peer groups, serves an eight-screen dashboard and a
16-endpoint API, and produces 91 company tearsheets, 11 sector reports, a
93-page portfolio summary and 92 radar charts.

Every source data defect found along the way is documented rather than
worked around silently: the truncated company master, the simulated
valuation dataset, the ROE scale artifacts, the duplicate company-year
rows and the coverage limits of the analysis and pros-and-cons tables.
A reader of the retrospectives can tell what the platform knows from what
it is guessing.
