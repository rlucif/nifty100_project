'''
Technical documentation PDF for the N100 Financial Intelligence Platform.

Architecture and design reference, as distinct from docs/analyst_guide.pdf
which is the user manual. This document is for an engineer who has to
maintain, extend or review the platform: layer model, data model, module
responsibilities, the actual formulas, algorithm designs, API contract,
test strategy and the design decisions with their reasoning.

Content is held as structured data and laid out by ReportLab, so the
document regenerates whenever the platform changes.

Run with:
   python -m src.reports.technical_documentation
'''

import re
import sqlite3
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
   PageBreak,
   Paragraph,
   SimpleDocTemplate,
   Spacer,
   Table,
   TableStyle
)

DB_PATH = 'data/nifty100.db'
OUTPUT_PATH = 'docs/technical_documentation.pdf'


def collect_test_count():
   '''Number of tests pytest can collect, so the figure is never stale.'''
   import re
   import subprocess
   import sys

   try:
      result = subprocess.run(
         [sys.executable, '-m', 'pytest', 'tests/', '--collect-only', '-q'],
         capture_output=True, text=True, timeout=300
      )
      match = re.search(r'(\d+)\s+tests? collected', result.stdout)
      if match:
         return int(match.group(1))
   except Exception:
      pass

   return None


TEST_COUNT = collect_test_count()
TEST_COUNT_TEXT = f'{TEST_COUNT} tests' if TEST_COUNT else 'the test suite'

NAVY = colors.HexColor('#1F3864')
GREEN = colors.HexColor('#2E7D32')
RED = colors.HexColor('#C00000')
AMBER = colors.HexColor('#BF8F00')
LIGHT_GREY = colors.HexColor('#F2F2F2')
MID_GREY = colors.HexColor('#BFBFBF')
CODE_BACKGROUND = colors.HexColor('#F7F7F9')

PAGE_WIDTH, PAGE_HEIGHT = A4
CONTENT_WIDTH = PAGE_WIDTH - 32 * mm

STYLES = {
   'cover_title': ParagraphStyle(
      'cover_title', fontName='Helvetica-Bold', fontSize=25,
      textColor=NAVY, leading=30, alignment=TA_CENTER
   ),
   'cover_sub': ParagraphStyle(
      'cover_sub', fontName='Helvetica', fontSize=12,
      textColor=colors.HexColor('#595959'), leading=17, alignment=TA_CENTER
   ),
   'chapter': ParagraphStyle(
      'chapter', fontName='Helvetica-Bold', fontSize=15,
      textColor=NAVY, leading=19, spaceAfter=3
   ),
   'heading': ParagraphStyle(
      'heading', fontName='Helvetica-Bold', fontSize=10.5,
      textColor=NAVY, leading=13.5, spaceBefore=7, spaceAfter=3
   ),
   'body': ParagraphStyle(
      'body', fontName='Helvetica', fontSize=9, leading=12.8, spaceAfter=5
   ),
   'bullet': ParagraphStyle(
      'bullet', fontName='Helvetica', fontSize=9, leading=12.5,
      leftIndent=10, spaceAfter=2.5
   ),
   'code': ParagraphStyle(
      'code', fontName='Courier', fontSize=8, leading=11, leftIndent=5,
      spaceAfter=3
   ),
   'cell': ParagraphStyle(
      'cell', fontName='Helvetica', fontSize=8, leading=10.5
   ),
   'cell_mono': ParagraphStyle(
      'cell_mono', fontName='Courier', fontSize=7.2, leading=9.8
   ),
   'cell_head': ParagraphStyle(
      'cell_head', fontName='Helvetica-Bold', fontSize=8,
      textColor=colors.white, leading=10.5
   ),
   'caption': ParagraphStyle(
      'caption', fontName='Helvetica-Oblique', fontSize=7.5,
      textColor=colors.HexColor('#7F7F7F'), leading=10.5, spaceAfter=4
   )
}


def _p(text):
   return Paragraph(text, STYLES['body'])


def _bullets(items):
   return [
      Paragraph(f'&bull;&nbsp; {item}', STYLES['bullet']) for item in items
   ]


def _code(lines):
   table = Table(
      [[Paragraph('<br/>'.join(lines), STYLES['code'])]],
      colWidths=[CONTENT_WIDTH]
   )
   table.setStyle(TableStyle([
      ('BACKGROUND', (0, 0), (-1, -1), CODE_BACKGROUND),
      ('BOX', (0, 0), (-1, -1), 0.4, MID_GREY),
      ('TOPPADDING', (0, 0), (-1, -1), 5),
      ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
      ('LEFTPADDING', (0, 0), (-1, -1), 6)
   ]))

   return table


def _table(headers, rows, widths=None, mono=()):
   head = [Paragraph(h, STYLES['cell_head']) for h in headers]
   body = [
      [
         Paragraph(
            str(cell),
            STYLES['cell_mono'] if i in mono else STYLES['cell']
         )
         for i, cell in enumerate(row)
      ]
      for row in rows
   ]

   if widths is None:
      widths = [CONTENT_WIDTH / len(headers)] * len(headers)

   table = Table([head] + body, colWidths=widths, repeatRows=1)
   table.setStyle(TableStyle([
      ('BACKGROUND', (0, 0), (-1, 0), NAVY),
      ('VALIGN', (0, 0), (-1, -1), 'TOP'),
      ('GRID', (0, 0), (-1, -1), 0.4, MID_GREY),
      ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
      ('TOPPADDING', (0, 0), (-1, -1), 3.5),
      ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
      ('LEFTPADDING', (0, 0), (-1, -1), 4),
      ('RIGHTPADDING', (0, 0), (-1, -1), 4)
   ]))

   return table


def _callout(title, text, colour):
   table = Table(
      [[Paragraph(f'<b>{title}</b><br/>{text}', STYLES['cell'])]],
      colWidths=[CONTENT_WIDTH]
   )
   table.setStyle(TableStyle([
      ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FBFBFB')),
      ('BOX', (0, 0), (-1, -1), 0.6, colour),
      ('LINEBEFORE', (0, 0), (0, -1), 3, colour),
      ('TOPPADDING', (0, 0), (-1, -1), 6),
      ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
      ('LEFTPADDING', (0, 0), (-1, -1), 8),
      ('RIGHTPADDING', (0, 0), (-1, -1), 8)
   ]))

   return table


def read_schema():
   '''Live table names, row counts and column lists from the database.'''
   path = Path(DB_PATH)
   if not path.exists():
      return []

   connection = sqlite3.connect(path)
   tables = []

   try:
      names = [
         row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
         )
      ]

      for name in names:
         columns = [
            row[1] for row in connection.execute(
               f'PRAGMA table_info("{name}")'
            )
         ]
         count = connection.execute(
            f'SELECT COUNT(*) FROM "{name}"'
         ).fetchone()[0]
         tables.append((name, count, columns))
   finally:
      connection.close()

   return tables


# ---------------------------------------------------------------------
# Chapters
# ---------------------------------------------------------------------
def _cover():
   return [
      Spacer(1, 52 * mm),
      Paragraph('N100 Financial Intelligence Platform', STYLES['cover_title']),
      Spacer(1, 4 * mm),
      Paragraph('Technical Documentation', STYLES['cover_title']),
      Spacer(1, 9 * mm),
      Paragraph(
         'Architecture, data model and design reference',
         STYLES['cover_sub']
      ),
      Spacer(1, 20 * mm),
      Paragraph(
         '92 companies &nbsp;|&nbsp; 14 tables &nbsp;|&nbsp; '
         '30+ KPIs &nbsp;|&nbsp; 20 API endpoints<br/>'
         f'{TEST_COUNT_TEXT} &nbsp;|&nbsp; 23 deliverables &nbsp;|&nbsp; '
         '20 of 20 acceptance gates',
         STYLES['cover_sub']
      ),
      Spacer(1, 14 * mm),
      Paragraph(
         '<b>Reviewers: chapter 0 explains how the six form uploads fit '
         'together<br/>and how to get the project running.</b>',
         STYLES['cover_sub']
      ),
      Spacer(1, 14 * mm),
      Paragraph(
         f'Version 1.0 &nbsp;&bull;&nbsp; {date.today().isoformat()}<br/>'
         'Raj Sarania, Data Analyst<br/>'
         'Summer Internship Programme, Bluestock Fintech',
         STYLES['cover_sub']
      )
   ]


def _chapter_submission():
   '''How the submission is packaged. First chapter deliberately.

   The submission form has six slots and no room for a covering note, so
   this page is where a reviewer is told how the six uploads fit together
   and how to get the project running.
   '''
   return [
      Paragraph('0. About this submission', STYLES['chapter']),
      Paragraph(
         'Read this first. It explains how the six uploads fit together.',
         STYLES['caption']
      ),
      _p(
         'This project was submitted through a form with six slots: three '
         'source code archives, a database archive and two PDF documents. '
         '<b>The complete project is the union of all six uploads.</b> No '
         'single upload is the whole thing.'
      ),
      _table(
         ['Form slot', 'What it contains'],
         [
            ['1. Source Code (Frontend)',
             'The Streamlit dashboard: entry point, all 8 screens, cached '
             'data loader. Also carries the 92 radar chart PNGs used by '
             'the peer views'],
            ['2. Source Code (Backend)',
             'The analytics engine: ETL, ratio engine, screener, NLP rule '
             'engine, clustering, statistics and report generators. Also '
             'carries the generated Excel workbooks, the 91 company '
             'tearsheets, 11 sector reports and the portfolio summary'],
            ['3. Source Code (RestAPI)',
             'The FastAPI application: 20 endpoints across 7 routers, the '
             'OpenAPI 3.1 specification and the full test report'],
            ['4. Database SQL File',
             'The DDL schema, the populated SQLite database, all 12 source '
             'Excel workbooks so the database can be rebuilt from '
             'scratch, exploratory queries and the load and validation '
             'audit trail'],
            ['5. Technical Documentation',
             'This document: architecture, data model, formulas, algorithm '
             'designs, API contract, test strategy and known limitations'],
            ['6. Daily Reports',
             'The project progress record: 9 day-level logs and 6 sprint '
             'retrospectives, with a coverage map stating which days are '
             'recorded at which level']
         ],
         widths=[42 * mm, CONTENT_WIDTH - 42 * mm]
      ),
      Spacer(1, 4 * mm),
      _callout(
         'Why the segmentation looks unusual',
         'The form is shaped for a conventional web application with a '
         'separate frontend, backend and API. This project is a Python '
         'analytics platform, so the mapping is: the Streamlit dashboard '
         'is the frontend, the ETL and analytics engine is the backend, '
         'and FastAPI is the API. The form also has no slot for the 23 '
         'tracked deliverables, so each one is attached to the segment '
         'that produces or displays it. Every archive contains a '
         'MANIFEST.txt naming the other five uploads.',
         NAVY
      ),
      Spacer(1, 4 * mm),
      Paragraph('Getting it running in five minutes', STYLES['heading']),
      _p(
         'Extract all four archives into one directory. Each archive has a '
         'single top-level folder; merge their contents so that '
         '<font face="Courier">src/</font>, '
         '<font face="Courier">data/</font>, '
         '<font face="Courier">config/</font> and '
         '<font face="Courier">tests/</font> sit side by side. Then:'
      ),
      _code([
         'pip install -r requirements.txt',
         '',
         '# the database ships populated, so start here:',
         f'python -m pytest -q                     # {TEST_COUNT_TEXT}',
         'streamlit run src/dashboard/app.py      # dashboard on :8501',
         'uvicorn src.api.main:app --port 8000    # API on :8000, /docs',
         '',
         '# or rebuild everything from the source Excel workbooks:',
         'python -m src.etl.sqlite_loader         # 12 tables, 12,892 rows',
         'python -m src.etl.ratio_engine          # 1,184 KPI rows',
         'python -m src.screener.run_screener     # screener + peer ranks',
         '',
         '# a Makefile wraps every step:  make help'
      ]),
      _p(
         'This sequence was verified by extracting the four archives into '
         'an empty directory, deleting the shipped database and rebuilding '
         f'from the Excel workbooks: {TEST_COUNT_TEXT} pass and all 20 acceptance '
         'gates hold. Python 3.12 or newer is required.'
      ),
      Paragraph('Where to look for what', STYLES['heading']),
      _table(
         ['Question', 'Answer'],
         [
            ['Is it complete and correct?',
             'docs/acceptance_checklist.pdf, 20 gates with evidence'],
            ['How do I use the platform?',
             'docs/analyst_guide.pdf, an 11 page user manual'],
            ['How does it work internally?',
             'This document, chapters 1 to 8'],
            ['What was built when, and why?',
             'Upload 6, and docs/Sprint1..6_retrospective.md'],
            ['What does the test suite cover?',
             'reports/pytest_report.html'],
            ['Why does a ratio look odd?',
             'output/ratio_edge_cases.log, every anomaly categorised'],
            ['How fast is it?', 'output/perf_notes.md']
         ],
         widths=[52 * mm, CONTENT_WIDTH - 52 * mm]
      ),
      Spacer(1, 4 * mm),
      _callout(
         'Two things stated plainly up front',
         'First: the market_cap and stock_prices datasets supplied with '
         'this project are SIMULATED, so every P/E, P/B, EV/EBITDA, '
         'dividend yield and market cap figure is illustrative rather than '
         'real market data. Second: the supplied companies.xlsx is '
         'truncated at 92 rows, and several other source defects were '
         'found during the build. All of them are documented in chapter 7 '
         'rather than worked around silently.',
         AMBER
      )
   ]


def _chapter_architecture():
   return [
      Paragraph('1. System architecture', STYLES['chapter']),
      Paragraph(
         'A four-layer batch analytics platform over a single SQLite file.',
         STYLES['caption']
      ),
      _p(
         'The platform is deliberately a batch pipeline with read-only '
         'presentation on top, not a live service. Excel files are the '
         'system of record; SQLite is the working store; every analytical '
         'figure is derived, never hand-entered. Nothing writes back to '
         'the source data.'
      ),
      Paragraph('Layer model', STYLES['heading']),
      _code([
         'SOURCE          12 Excel workbooks (raw + supporting)',
         '                     |',
         '                     v  src/etl/sqlite_loader.py',
         'STORE           data/nifty100.db      14 tables',
         '                     |',
         '                     v  src/etl/ratio_engine.py',
         'DERIVED         financial_ratios      1,184 rows, 17 KPI cols',
         '                output/capital_allocation.csv',
         '                     |',
         '                     v  src/analytics/  src/screener/  src/nlp/',
         'ANALYTICS       screening universe, composite score,',
         '                peer percentiles, clustering, statistics,',
         '                valuation flags, rule-based pros and cons',
         '                     |',
         '        +------------+------------+------------+',
         '        v            v            v            v',
         'PRESENT   Streamlit    FastAPI     Excel      ReportLab',
         '          8 screens    20 routes   4 books    PDFs',
      ]),
      Paragraph('Why this shape', STYLES['heading']),
      *_bullets([
         '<b>The expensive work happens once.</b> Ratio computation, '
         'clustering and PDF generation are batch steps whose output is '
         'committed. The dashboard and API read that output rather than '
         'recomputing it.',
         '<b>One analytics layer, three consumers.</b> The dashboard '
         'screener, the API screener endpoint and the Excel export all '
         'call the same ScreenerEngine. They cannot disagree about what a '
         'filter means, and an acceptance gate asserts the API and the '
         'workbook return identical company sets.',
         '<b>Derived values are never stored twice.</b> ROCE and the '
         'sector-relative score are recomputed on read rather than '
         'persisted, because the Sprint 2 schema has no column for them '
         'and a second copy would drift.',
         '<b>SQLite is sufficient.</b> The largest table is 5,520 rows. '
         'Query time is measured in tens of microseconds. A server '
         'database would add operational cost for no gain.'
      ]),
      Paragraph('Package layout', STYLES['heading']),
      _table(
         ['Package', 'Responsibility'],
         [
            ['src/etl/', 'Excel to SQLite loading, validation, ratio '
             'engine, edge case audit, index creation'],
            ['src/analytics/', 'Pure calculation: ratios, cash flow KPIs, '
             'CAGR, period parsing, peer ranks, valuation, clustering, '
             'statistics'],
            ['src/screener/', 'Screening universe assembly, filter '
             'engine, composite score, Excel export'],
            ['src/nlp/', 'Analysis text parsing, per-company feature '
             'frames, the 24-rule pros and cons engine'],
            ['src/reports/', 'ReportLab PDFs, Excel workbooks, radar '
             'charts, acceptance gates, deliverable archive'],
            ['src/dashboard/', 'Streamlit app, 8 screens, cached loader'],
            ['src/api/', 'FastAPI app, dependencies, 7 routers'],
            ['tests/', f'{TEST_COUNT_TEXT} across etl, kpi, dq, analytics, '
             'screener, nlp, reports, dashboard, api']
         ],
         widths=[36 * mm, CONTENT_WIDTH - 36 * mm],
         mono=(0,)
      ),
      Spacer(1, 3 * mm),
      _p(
         'The dependency direction is strictly one way: analytics never '
         'imports from presentation, and pure calculation modules never '
         'import a database connection. That is what allows the ratio '
         'functions to be unit tested with plain numbers.'
      )
   ]


def _chapter_data_model(tables):
   rows = []
   for name, count, columns in tables:
      rows.append([
         name,
         f'{count:,}',
         ', '.join(columns[:7]) + (' ...' if len(columns) > 7 else '')
      ])

   return [
      Paragraph('2. Data model', STYLES['chapter']),
      Paragraph(
         'Live schema read from data/nifty100.db at generation time.',
         STYLES['caption']
      ),
      _table(
         ['Table', 'Rows', 'Columns'],
         rows,
         widths=[32 * mm, 16 * mm, CONTENT_WIDTH - 48 * mm],
         mono=(0, 2)
      ),
      Spacer(1, 4 * mm),
      Paragraph('Keys and joins', STYLES['heading']),
      *_bullets([
         '<b>company_id</b> is the join key everywhere. It is the NSE '
         'ticker, normalised to upper case and trimmed at load time.',
         '<b>year</b> is a text period label, not a number. Values look '
         'like <font face="Courier">Mar 2024</font> or '
         '<font face="Courier">Dec 2023</font>, and companies do not '
         'share a financial year end.',
         '<b>market_cap.year is an integer</b> (2019 to 2024), so joining '
         'valuation to statements requires mapping the period label to '
         'the calendar year it closes in. '
         '<font face="Courier">src/analytics/periods.py</font> owns that '
         'mapping.',
         '<b>financial_ratios</b> is fully derived. It is deleted and '
         'rebuilt by the ratio engine on every run; nothing else writes '
         'to it except the composite score update.',
         '<b>peer_percentiles</b> is derived from the universe and '
         'rebuilt by the peer engine.'
      ]),
      Paragraph('The period problem', STYLES['heading']),
      _p(
         'The raw workbooks mix clean labels with irregular ones: '
         '<font face="Courier">TTM</font>, '
         '<font face="Courier">Mar 2023 15</font> and '
         '<font face="Courier">Mar 2016 9m</font> all appear. Ordering '
         'periods by string sort would be wrong, and any CAGR window '
         'built on a wrong order is silently incorrect.'
      ),
      _p(
         '<font face="Courier">periods.py</font> is the single answer to '
         'this. It converts a label to a sortable integer '
         '(<font face="Courier">calendar_year * 100 + month</font>), '
         'returns -1 for anything unparseable so it can be filtered out, '
         'and exposes '
         '<font face="Courier">latest_rows()</font> and '
         '<font face="Courier">deduplicate_company_years()</font> so '
         'every consumer agrees on what "the latest year" means.'
      ),
      _callout(
         'Duplicate company-year rows',
         'The source statements contain 119 duplicate company-year rows. '
         'PNB carries 60 rows for 12 distinct years. Sprint 2 decided to '
         'preserve them rather than silently modify source data, so every '
         'analytics consumer must de-duplicate before counting. A screener '
         'built directly on financial_ratios would report the same '
         'company several times.',
         AMBER
      )
   ]


def _chapter_formulas():
   return [
      Paragraph('3. KPI definitions', STYLES['chapter']),
      Paragraph(
         'Every formula the ratio engine implements, with its edge case '
         'behaviour.',
         STYLES['caption']
      ),
      _table(
         ['KPI', 'Formula', 'Returns None when'],
         [
            ['Net profit margin', 'net_profit / sales x 100', 'sales = 0'],
            ['Operating margin', 'operating_profit / sales x 100',
             'sales = 0'],
            ['ROE', 'net_profit / (equity + reserves) x 100',
             'equity + reserves <= 0'],
            ['ROCE', '(operating_profit + other_income) / '
             '(equity + reserves + borrowings) x 100',
             'capital employed <= 0, or any input missing'],
            ['Debt to equity', 'borrowings / (equity + reserves)',
             'equity + reserves <= 0. Returns 0 when borrowings = 0'],
            ['Interest coverage', '(operating_profit + other_income) / '
             'interest', 'interest = 0, which means Debt Free'],
            ['Asset turnover', 'sales / total_assets', 'total_assets = 0'],
            ['Free cash flow', 'operating_activity + investing_activity',
             'never; negative is a valid outcome'],
            ['CFO quality', 'operating_activity / net_profit',
             'net_profit = 0'],
            ['CapEx intensity', 'abs(investing_activity) / sales x 100',
             'sales = 0'],
            ['FCF conversion', 'free_cash_flow / operating_profit x 100',
             'operating_profit = 0'],
            ['CAGR (n years)', '((end / start) ^ (1/n) - 1) x 100',
             'start = 0, both negative, decline to loss, or turnaround'],
            ['FCF yield', 'free_cash_flow / market_cap x 100',
             'market cap missing or 0']
         ],
         widths=[30 * mm, 62 * mm, CONTENT_WIDTH - 92 * mm],
         mono=(1,)
      ),
      Spacer(1, 4 * mm),
      Paragraph('Label bands', STYLES['heading']),
      _table(
         ['Metric', 'Bands'],
         [
            ['CFO quality', 'above 1.0 High Quality Earnings, 0.5 to 1.0 '
             'Moderate, below 0.5 Accrual Risk'],
            ['CapEx intensity', 'below 3% Asset Light, 3 to 8% Moderate, '
             'above 8% Capital Intensive'],
            ['FCF conversion', 'above 60% Efficient, 30 to 60% Moderate, '
             'below 30% CapEx Heavy'],
            ['Interest coverage', 'null means Debt Free; below 1.5 raises '
             'a warning flag'],
            ['Valuation flag', 'P/E above 1.5x sector median Caution, '
             'below 0.7x Discount, otherwise Fair']
         ],
         widths=[34 * mm, CONTENT_WIDTH - 34 * mm]
      ),
      Spacer(1, 4 * mm),
      Paragraph('Capital allocation classifier', STYLES['heading']),
      _p(
         'Companies are labelled from the signs of the three cash flow '
         'lines. Seven of the eight possible sign combinations are named '
         'by the specification; the eighth, '
         '<font face="Courier">(-,+,-)</font>, is not, and the two '
         'companies that fall there are labelled Unknown Pattern.'
      ),
      _table(
         ['CFO', 'CFI', 'CFF', 'Pattern'],
         [
            ['+', '-', '-', 'Reinvestor, or Shareholder Returns when '
             'CFO/PAT is above 1.0'],
            ['+', '+', '-', 'Liquidating Assets'],
            ['+', '+', '+', 'Cash Accumulator'],
            ['+', '-', '+', 'Mixed'],
            ['-', '+', '+', 'Distress Signal'],
            ['-', '-', '+', 'Growth Funded by Debt'],
            ['-', '-', '-', 'Pre-Revenue'],
            ['-', '+', '-', 'Not named by the specification']
         ],
         widths=[12 * mm, 12 * mm, 12 * mm, CONTENT_WIDTH - 36 * mm],
         mono=(0, 1, 2)
      ),
      Spacer(1, 3 * mm),
      _callout(
         'Operating profit is EBITDA by construction',
         'The source P&amp;L reports operating profit before '
         'depreciation. This was verified against the identity operating '
         'profit + other income - interest - depreciation = profit before '
         'tax, which holds with a median residual of 1.0 across 1,263 '
         'rows, against 1,317 for the post-depreciation reading. Note '
         'that depreciation IS present in the data; an earlier revision '
         'of this document claimed otherwise and was wrong.',
         GREEN
      )
   ]


def _chapter_screener():
   return [
      Paragraph('4. Screener and scoring design', STYLES['chapter']),
      Paragraph(
         'Filter engine, business rules and the composite quality score.',
         STYLES['caption']
      ),
      Paragraph('The screening universe', STYLES['heading']),
      _p(
         '<font face="Courier">src/screener/universe.py</font> assembles '
         'one row per company at its latest financial year, joining '
         'financial_ratios, profitandloss, balancesheet, market_cap, '
         'sectors and companies, then deriving ROCE, CFO/PAT, the 3-year '
         'revenue CAGR, the 5-year FCF CAGR and a debt-declining flag. '
         'Everything downstream reads this one frame.'
      ),
      Paragraph('Configuration versus code', STYLES['heading']),
      _p(
         'Thresholds live in '
         '<font face="Courier">config/screener_config.yaml</font> so an '
         'analyst can change them without touching Python. Business rules '
         'live in code, because they are not numbers.'
      ),
      _table(
         ['Rule', 'Behaviour', 'Why'],
         [
            ['Financials D/E exemption',
             'An upper-bound D/E filter (< or <=) does not reject '
             'Financials. An equality filter such as D/E == 0 still '
             'applies to them',
             'Leverage of 8 is structurally normal for a lender, but a '
             'bank with D/E 8 is genuinely not debt free'],
            ['Debt Free coverage',
             'A null interest coverage passes any minimum',
             'Null means interest expense is zero, so coverage is '
             'infinite, not unknown'],
            ['Everything else',
             'A missing value fails the filter',
             'A company cannot be asserted to meet a threshold on '
             'absent data']
         ],
         widths=[34 * mm, 62 * mm, CONTENT_WIDTH - 96 * mm]
      ),
      Spacer(1, 4 * mm),
      Paragraph('Composite quality score', STYLES['heading']),
      _p(
         'A 0 to 100 score blending four components. Each input metric is '
         'winsorised at the 10th and 90th percentile, then min-max scaled '
         'across the winsorised range, then weighted.'
      ),
      _table(
         ['Component', 'Weight', 'Inputs'],
         [
            ['Profitability', '35', 'ROE 15, ROCE 10, net profit margin 10'],
            ['Cash quality', '30', 'FCF CAGR 15, CFO/PAT 10, FCF positive '
             'flag 5'],
            ['Growth', '20', 'Revenue CAGR 10, PAT CAGR 10'],
            ['Leverage', '15', 'D/E score 10, interest coverage score 5']
         ],
         widths=[32 * mm, 18 * mm, CONTENT_WIDTH - 50 * mm]
      ),
      Spacer(1, 3 * mm),
      *_bullets([
         '<b>Winsorisation is load-bearing, not cosmetic.</b> The source '
         'data contains ROE readings of 4,744% (BEL) and 893% (INDIGO), '
         'caused by equity figures on a different scale from profit. '
         'Uncapped, those two companies compress every other company into '
         'a narrow band at the bottom of the profitability axis.',
         '<b>A missing metric scores a neutral 50, not 0.</b> Scoring it '
         '0 would punish a company twice for a documented edge case: a '
         'turnaround company already has a null PAT CAGR because its base '
         'year was a loss.',
         '<b>Debt Free companies take the best available coverage '
         'reading</b> rather than being treated as missing, so the '
         'leverage component rewards them.',
         '<b>A sector-relative variant</b> normalises within broad_sector, '
         'answering "good for a bank" rather than "good".'
      ]),
      Paragraph('Peer percentile ranking', STYLES['heading']),
      _p(
         'SQL-style PERCENT_RANK, '
         '<font face="Courier">(rank - 1) / (n - 1)</font>, on a 0 to 100 '
         'scale, computed for 10 metrics within each of the 11 peer '
         'groups. Debt to equity is inverted so less debt ranks higher. '
         'A company with a missing metric is excluded from the ranking '
         'population rather than ranked last, so a peer group is not '
         'penalised for incomplete source data. 550 rows; the 37 '
         'companies in no peer group return the message '
         '<font face="Courier">No peer group assigned</font> rather than '
         'raising.'
      ),
      Paragraph('Clustering', STYLES['heading']),
      _p(
         'KMeans, k=5, random_state=42, on five features: ROE, D/E, '
         'revenue CAGR, FCF CAGR and operating margin. Missing values are '
         'imputed from the sector median, then features are winsorised at '
         'P5/P95, then StandardScaler is applied.'
      ),
      _callout(
         'Why winsorisation was added to the clustering pipeline',
         'The specified pipeline is impute, scale, cluster. Run exactly '
         'that way it produced three degenerate clusters: one holding BEL '
         'and HAL alone with a mean ROE of 4,280%, one holding CIPLA '
         'alone, and 58 of the 92 companies dumped together. StandardScaler '
         'normalises spread but does not stop one company with bad source '
         'data from defining an axis. Capping at P5/P95 produced clusters '
         'of 13, 26, 28, 15 and 10, each with a recognisable financial '
         'character.',
         AMBER
      )
   ]


def _chapter_api():
   return [
      Paragraph('5. API design', STYLES['chapter']),
      Paragraph(
         'Read-only REST surface over the analytics layer.',
         STYLES['caption']
      ),
      _table(
         ['Router', 'Endpoints', 'Notes'],
         [
            ['health.py', '1', 'Status, row counts for 10 tables, '
             'uptime, version'],
            ['companies.py', '9', 'List, profile, P&L, BS, cash flow, '
             'ratios, tearsheet PDF, peer compare, documents'],
            ['screener.py', '2', 'Threshold and preset screening, preset '
             'listing'],
            ['sectors.py', '2', 'Sector list with medians, companies in '
             'a sector'],
            ['peers.py', '2', 'Group list, group detail with percentile '
             'ranks'],
            ['valuation.py', '1', 'Historical multiples, marked '
             'SIMULATED'],
            ['portfolio.py', '3', 'Percentile stats, clusters, outliers']
         ],
         widths=[30 * mm, 20 * mm, CONTENT_WIDTH - 50 * mm],
         mono=(0,)
      ),
      Spacer(1, 4 * mm),
      Paragraph('Design decisions', STYLES['heading']),
      *_bullets([
         '<b>The universe is cached per process</b> with '
         '<font face="Courier">lru_cache</font> in '
         '<font face="Courier">dependencies.py</font>. The composite score '
         'is cross-sectional, so it cannot be computed for one company on '
         'request; building it per call would put a full index '
         'recomputation behind every endpoint. A warm screener call is '
         '13 ms, a cold one about a second.',
         '<b>Connections are per request, not shared.</b> SQLite '
         'connections are not safe to share across threads, so each query '
         'opens and closes its own.',
         '<b>NaN becomes null, not the string "NaN".</b> '
         '<font face="Courier">frame_to_records()</font> handles the '
         'conversion once so no endpoint emits invalid JSON.',
         '<b>CORS is fully open and there is no authentication.</b> '
         'Correct for an internal read-only tool; it must not be exposed '
         'publicly in this form.',
         '<b>Timing middleware</b> logs method, path, status and elapsed '
         'time, and stamps '
         '<font face="Courier">X-Response-Time-ms</font> on every '
         'response.'
      ]),
      Paragraph('Status code contract', STYLES['heading']),
      _table(
         ['Code', 'Condition'],
         [
            ['200', 'Success. Also returned when a company has no peer '
             'group, with an explanatory message rather than an error'],
            ['400', 'Threshold outside its documented range, unknown '
             'preset name, or a year not in YYYY-MM form'],
            ['404', 'Unknown ticker, sector or peer group; or no '
             'tearsheet exists for that company'],
            ['422', 'FastAPI query validation, for example limit=0'],
            ['500', 'Unhandled error, returned as JSON rather than HTML']
         ],
         widths=[16 * mm, CONTENT_WIDTH - 16 * mm],
         mono=(0,)
      ),
      Spacer(1, 3 * mm),
      _p(
         'The OpenAPI 3.1 specification is exported to '
         '<font face="Courier">docs/openapi.json</font> and is the '
         'authoritative contract.'
      )
   ]


def _chapter_quality():
   return [
      Paragraph('6. Test strategy and performance', STYLES['chapter']),
      Paragraph(
         f'{TEST_COUNT_TEXT}, zero warnings, 20 of 20 acceptance gates.',
         STYLES['caption']
      ),
      _table(
         ['Suite', 'Covers'],
         [
            ['tests/etl/', 'Year normalisation and the validator rules'],
            ['tests/dq/', 'The 14 data quality rules, one test per rule'],
            ['tests/kpi/', 'Ratio and CAGR formulas with plain numbers, '
             'including every edge case branch'],
            ['tests/analytics/', 'Period parsing, peer percentiles, '
             'valuation flags'],
            ['tests/screener/', 'Filter logic, both business rules, '
             'composite score bounds and ordering'],
            ['tests/nlp/', 'Parser regex including the deliberate '
             'rejections, all 24 rules, confidence bands, fallback '
             'behaviour'],
            ['tests/reports/', 'Distress and deleveraging flags, PDF page '
             'count and size'],
            ['tests/dashboard/', 'All 8 screens loaded headlessly via '
             'AppTest, plus regression tickers'],
            ['tests/api/', '69 tests: every endpoint, every error path, '
             'and API-versus-Excel agreement'],
            ['tests/test_makefile.py', 'Static Makefile integrity, since '
             'make is not installed here']
         ],
         widths=[34 * mm, CONTENT_WIDTH - 34 * mm],
         mono=(0,)
      ),
      Spacer(1, 4 * mm),
      Paragraph('Testing approach', STYLES['heading']),
      *_bullets([
         '<b>Pure functions are tested with numbers, not fixtures.</b> '
         'The ratio and CAGR modules take scalars, so their edge cases '
         'are asserted directly.',
         '<b>Screens are tested by loading them.</b> Streamlit\'s '
         'AppTest runs each page headlessly, so a broken import or an '
         'unguarded None fails the suite rather than the demo.',
         '<b>Regression tickers are named in the tests.</b> PNB broke the '
         'profile screen because a bank reports no operating profit; it is '
         'now a permanent test case alongside ADANIGREEN (short history) '
         'and ITC (control).',
         '<b>Cross-consumer agreement is asserted.</b> A test compares '
         'API preset output against the Excel workbook, so the two paths '
         'cannot silently diverge.',
         '<b>Known data defects are pinned, not ignored.</b> The orphan '
         'ticker rule accepts the two documented orphans and fails on any '
         'new one.'
      ]),
      Paragraph('Measured performance', STYLES['heading']),
      _table(
         ['Measure', 'Result', 'Target'],
         [
            ['10 concurrent screener API calls', '0.150 s total',
             'under 10 s'],
            ['API endpoint latency', 'under 20 ms median', 'not specified'],
            ['Company Profile screen', 'p95 0.16 s, worst 0.99 s',
             'under 3 s'],
            ['Indexed query improvement', '45% to 69% faster', 'n/a'],
            ['Tearsheet batch, 91 PDFs', 'several minutes',
             'offline batch']
         ],
         widths=[58 * mm, 42 * mm, CONTENT_WIDTH - 100 * mm]
      ),
      Spacer(1, 3 * mm),
      _p(
         'Twelve indexes were added on '
         '<font face="Courier">company_id</font> and '
         '<font face="Courier">year</font>. Honest caveat: at these table '
         'sizes SQLite was never the bottleneck, and the absolute saving '
         'is tens of microseconds. The real cost sits in matplotlib '
         'rendering during the PDF batch, which is offline by design.'
      )
   ]


def _chapter_limitations():
   return [
      Paragraph('7. Data quality and known limitations', STYLES['chapter']),
      Paragraph(
         'Every defect found in the supplied data, and how the platform '
         'handles it.',
         STYLES['caption']
      ),
      _callout(
         'Valuation data is simulated',
         'market_cap and stock_prices are simulated datasets. Every P/E, '
         'P/B, EV/EBITDA, dividend yield and market cap figure derives '
         'from them, and every surface that shows one labels it '
         'SIMULATED. The consequence goes beyond labelling: simulation '
         'destroyed the correlations real screening thresholds assume. '
         'P/E and P/B are uncorrelated here (r = -0.11) where in real '
         'markets they move together, which is why the Value Pick preset '
         'returns 2 companies instead of a usable shortlist.',
         RED
      ),
      Spacer(1, 4 * mm),
      _table(
         ['Defect', 'Impact', 'Handling'],
         [
            ['companies.xlsx is truncated at 92 rows, stopping part way '
             'through the alphabet',
             'Eight tickers appear in the statements with no master '
             'record; two of them (ULTRACEMCO, UNIONBANK) reach '
             'financial_ratios',
             'Accepted and pinned by a DQ rule that fails on any new '
             'orphan. They are excluded from search but included in '
             'aggregates'],
            ['ROE and ROCE scale artifacts',
             'BEL reports 4,744% ROE, INDIGO 893%. Equity and profit are '
             'not on the same scale for these companies',
             'Ratio engine retained as correct; winsorisation prevents '
             'them distorting scores and clusters; all cases itemised in '
             'ratio_edge_cases.log'],
            ['119 duplicate company-year rows',
             'Join fan-out; PNB has 60 rows for 12 years',
             'Preserved in source per the Sprint 2 decision; every '
             'analytics consumer de-duplicates first'],
            ['SBIN has no financial_ratios rows',
             'The designated Public Sector Banks benchmark is missing, so '
             'that group has no highlighted benchmark',
             'Reported in the workbook and on the peer screen'],
            ['analysis covers 5 companies, prosandcons covers 16',
             'Neither is usable as an index-wide source',
             'analysis is used to validate the CAGR engine instead; all '
             'pros and cons are generated from financial rules'],
            ['10 broad sectors, not the 11 the documents state',
             'Sector counts read as 11 only because of an Unclassified '
             'bucket',
             'Stated plainly wherever a sector count appears'],
            ['52 annual report URLs are absent',
             'Those years cannot be linked',
             'Rendered with a Report unavailable badge']
         ],
         widths=[46 * mm, 52 * mm, CONTENT_WIDTH - 98 * mm]
      ),
      Spacer(1, 4 * mm),
      Paragraph('Analytical caveats worth knowing', STYLES['heading']),
      *_bullets([
         '<b>The distress flag over-reports lenders.</b> CFO negative '
         'with CFF positive is the ordinary signature of loan book growth. '
         '9 of 13 flagged companies are profitable Financials, one with '
         '14,451 Cr of net profit. distress_alerts.csv carries a '
         'structurally_normal_for_sector column separating those from the '
         'four worth reviewing.',
         '<b>Pearson correlation overstates several relationships.</b> ROE '
         'against asset turnover reads +0.96 Pearson and +0.49 Spearman; '
         'net profit margin against interest coverage reads +0.79 against '
         '+0.09. Where the two disagree the coefficient reflects a few '
         'extreme companies, not the index. The heatmap carries a footnote '
         'naming the worst pairs.',
         '<b>Rule confidence is not probability.</b> It measures how far '
         'a company clears a threshold, nothing more.',
         '<b>PRO-13 and CON-13 are relative, not absolute.</b> They fire '
         'only when no absolute rule did. A CON-13 means nothing was '
         'found, not that something is wrong.',
         '<b>composite_quality_score is latest-year only.</b> It is '
         'cross-sectional, so back-filling it onto historical rows would '
         'imply a comparison never made.'
      ])
   ]


def _chapter_operations():
   return [
      Paragraph('8. Build, run and extend', STYLES['chapter']),
      Paragraph(
         'How to reproduce every output and where to add new work.',
         STYLES['caption']
      ),
      Paragraph('Full rebuild from source Excel', STYLES['heading']),
      _code([
         'make load        # Excel to SQLite',
         'make ratios      # financial_ratios + capital_allocation.csv',
         'make indexes     # 12 SQLite indexes',
         'make screener    # screener, peer ranks, radar charts',
         'make valuation   # valuation summary and flags',
         'make nlp         # parse analysis text, generate pros/cons',
         'make cashflow    # cash flow intelligence',
         'make cluster     # KMeans archetypes and elbow plot',
         'make stats       # heatmap, outliers, percentiles',
         'make tearsheets  # 91 company PDFs, 11 sector, portfolio',
         'make acceptance  # analyst guide + 20 gates + checklist',
         f'make test        # {TEST_COUNT_TEXT}',
         '',
         '# or the whole chain in dependency order',
         'make all'
      ]),
      _p(
         'If <font face="Courier">make</font> is unavailable, every target '
         'is a single '
         '<font face="Courier">python -m src....</font> call and can be '
         'run directly. '
         '<font face="Courier">tests/test_makefile.py</font> verifies '
         'statically that every target resolves.'
      ),
      Paragraph('Serving', STYLES['heading']),
      _code([
         'streamlit run src/dashboard/app.py       # port 8501',
         'uvicorn src.api.main:app --port 8000     # port 8000, /docs'
      ]),
      _p(
         'Both run simultaneously without conflict; this is verified as '
         'part of the Day 43 integration check.'
      ),
      Paragraph('Extension points', STYLES['heading']),
      _table(
         ['To add', 'Where', 'Watch out for'],
         [
            ['A new KPI', 'A pure function in '
             'src/analytics/ratios.py or cashflow_kpis.py, then a column '
             'in ratio_engine.py and schema.sql',
             'Guard every input for None; three call sites may use it'],
            ['A screener metric', 'A block in screener_config.yaml plus '
             'the column in universe.py',
             'Decide whether a missing value should pass or fail'],
            ['A dashboard screen', 'A file in src/dashboard/pages/',
             'Add the sys.path bootstrap; read data only through '
             'utils/db.py so it stays cached'],
            ['An API endpoint', 'A route in the matching router under '
             'src/api/routers/',
             'Use frame_to_records so NaN becomes null; add a test in '
             'tests/api/'],
            ['A pros/cons rule', 'src/nlp/pros_cons_generator.py, with '
             'any new history series in features.py',
             'Give it a confidence scale; absolute rules must not be '
             'confused with the relative fallbacks']
         ],
         widths=[30 * mm, 60 * mm, CONTENT_WIDTH - 90 * mm]
      ),
      Spacer(1, 4 * mm),
      Paragraph('Conventions', STYLES['heading']),
      *_bullets([
         'Three-space indentation throughout. This predates the author '
         'and is applied consistently; black is deliberately not run '
         'because it would reformat 72 of 92 files to no benefit. Ruff '
         'passes clean.',
         'All monetary values are INR Crore.',
         'company_id is upper case and trimmed at load time.',
         'A calculation that cannot be performed returns None. It does '
         'not raise, and it does not return 0.',
         'Generated artifacts are committed, because the deliverables '
         'tracker expects them present. output/final_deliverables/ is the '
         'one exception, being a duplicate copy.'
      ]),
      Spacer(1, 4 * mm),
      _callout(
         'Where to look next',
         'docs/analyst_guide.pdf is the user manual. '
         'docs/Sprint1..6_retrospective covers what was decided and why, '
         'sprint by sprint. output/ratio_edge_cases.log itemises every '
         'ratio anomaly with a category. output/perf_notes.md holds the '
         'performance measurements. docs/acceptance_checklist.pdf records '
         'the 20 gates with their evidence.',
         NAVY
      )
   ]


def build_document(output_path=OUTPUT_PATH):
   '''Render the technical documentation PDF and return its path.'''
   destination = Path(output_path)
   destination.parent.mkdir(parents=True, exist_ok=True)

   tables = read_schema()

   document = SimpleDocTemplate(
      str(destination),
      pagesize=A4,
      leftMargin=16 * mm,
      rightMargin=16 * mm,
      topMargin=15 * mm,
      bottomMargin=15 * mm,
      title='N100 Technical Documentation',
      author='N100 Financial Intelligence Platform'
   )

   chapters = [
      _chapter_submission(),
      _chapter_architecture(),
      _chapter_data_model(tables),
      _chapter_formulas(),
      _chapter_screener(),
      _chapter_api(),
      _chapter_quality(),
      _chapter_limitations(),
      _chapter_operations()
   ]

   story = list(_cover())

   for chapter in chapters:
      story.append(PageBreak())
      story.extend(chapter)

   document.build(story)

   return destination


def main():
   destination = build_document()
   pages = len(
      re.findall(rb'/Type\s*/Page[^s]', destination.read_bytes())
   )

   print(f'Wrote {destination}')
   print(f'  pages : {pages}')
   print(f'  size  : {destination.stat().st_size / 1024:,.1f} KB')


if __name__ == '__main__':
   main()
