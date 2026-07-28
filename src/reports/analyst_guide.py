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

OUTPUT_PATH = 'docs/analyst_guide.pdf'

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
      'cover_title', fontName='Helvetica-Bold', fontSize=26,
      textColor=NAVY, leading=31, alignment=TA_CENTER
   ),
   'cover_subtitle': ParagraphStyle(
      'cover_subtitle', fontName='Helvetica', fontSize=12,
      textColor=colors.HexColor('#595959'), leading=17,
      alignment=TA_CENTER
   ),
   'chapter': ParagraphStyle(
      'chapter', fontName='Helvetica-Bold', fontSize=16,
      textColor=NAVY, leading=20, spaceAfter=3
   ),
   'heading': ParagraphStyle(
      'heading', fontName='Helvetica-Bold', fontSize=11,
      textColor=NAVY, leading=14, spaceBefore=7, spaceAfter=3
   ),
   'body': ParagraphStyle(
      'body', fontName='Helvetica', fontSize=9.5, leading=13.5,
      spaceAfter=5
   ),
   'bullet': ParagraphStyle(
      'bullet', fontName='Helvetica', fontSize=9.5, leading=13.5,
      leftIndent=10, spaceAfter=2.5
   ),
   'code': ParagraphStyle(
      'code', fontName='Courier', fontSize=8.5, leading=12,
      leftIndent=6, spaceAfter=3
   ),
   'cell': ParagraphStyle(
      'cell', fontName='Helvetica', fontSize=8.5, leading=11
   ),
   'cell_mono': ParagraphStyle(
      'cell_mono', fontName='Courier', fontSize=7.8, leading=10.5
   ),
   'cell_header': ParagraphStyle(
      'cell_header', fontName='Helvetica-Bold', fontSize=8.5,
      textColor=colors.white, leading=11
   ),
   'caption': ParagraphStyle(
      'caption', fontName='Helvetica-Oblique', fontSize=8,
      textColor=colors.HexColor('#7F7F7F'), leading=11, spaceAfter=4
   )
}


def _paragraph(text):
   return Paragraph(text, STYLES['body'])


def _bullets(items):
   return [
      Paragraph(f'&bull;&nbsp; {item}', STYLES['bullet']) for item in items
   ]


def _code_block(lines):
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


def _table(headers, rows, widths=None, mono_columns=()):
   header_row = [
      Paragraph(header, STYLES['cell_header']) for header in headers
   ]
   body_rows = []

   for row in rows:
      body_rows.append([
         Paragraph(
            str(cell),
            STYLES['cell_mono'] if index in mono_columns
            else STYLES['cell']
         )
         for index, cell in enumerate(row)
      ])

   if widths is None:
      widths = [CONTENT_WIDTH / len(headers)] * len(headers)

   table = Table([header_row] + body_rows, colWidths=widths, repeatRows=1)
   table.setStyle(TableStyle([
      ('BACKGROUND', (0, 0), (-1, 0), NAVY),
      ('VALIGN', (0, 0), (-1, -1), 'TOP'),
      ('GRID', (0, 0), (-1, -1), 0.4, MID_GREY),
      ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
      ('TOPPADDING', (0, 0), (-1, -1), 4),
      ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
      ('LEFTPADDING', (0, 0), (-1, -1), 5),
      ('RIGHTPADDING', (0, 0), (-1, -1), 5)
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


def _cover():
   return [
      Spacer(1, 55 * mm),
      Paragraph('N100 Financial Intelligence Platform', STYLES['cover_title']),
      Spacer(1, 5 * mm),
      Paragraph('Analyst Guide', STYLES['cover_title']),
      Spacer(1, 10 * mm),
      Paragraph(
         'Fundamental analytics for the Nifty 100 constituents<br/>'
         '92 companies &nbsp;|&nbsp; 30+ KPIs &nbsp;|&nbsp; '
         '6 preset screeners &nbsp;|&nbsp; 16 API endpoints',
         STYLES['cover_subtitle']
      ),
      Spacer(1, 25 * mm),
      Paragraph(
         f'Version 1.0 &nbsp;&bull;&nbsp; {date.today().isoformat()}<br/>'
         'Prepared by Raj Sarania, Data Analyst',
         STYLES['cover_subtitle']
      )
   ]


def _chapter_one():
   return [
      Paragraph('1. What this platform is', STYLES['chapter']),
      Paragraph(
         'A read-only analytics layer over the financial statements of '
         'the Nifty 100 companies present in the supplied datasets.',
         STYLES['caption']
      ),
      _paragraph(
         'The platform takes twelve Excel datasets, loads them into a '
         'SQLite database, computes a standard set of financial KPIs, and '
         'exposes them four ways: an interactive dashboard, Excel '
         'workbooks, PDF tearsheets and a REST API. Nothing in it places '
         'trades or gives advice; it organises published financials so an '
         'analyst can compare companies quickly.'
      ),
      Paragraph('What is in the database', STYLES['heading']),
      _table(
         ['Table', 'Rows', 'What it holds'],
         [
            ['companies', '92', 'Company master: name, sector links, '
             'about text'],
            ['profitandloss', '1,276', 'Revenue, operating profit, net '
             'profit, EPS by year'],
            ['balancesheet', '1,312', 'Equity, reserves, borrowings, '
             'assets by year'],
            ['cashflow', '1,187', 'Operating, investing and financing '
             'cash flow'],
            ['financial_ratios', '1,184', 'Computed KPIs: margins, '
             'returns, leverage, CAGRs'],
            ['market_cap', '552', 'P/E, P/B, EV/EBITDA, dividend yield '
             '(SIMULATED)'],
            ['sectors', '92', 'Broad sector, sub-sector, market cap '
             'category'],
            ['peer_groups', '56', '11 peer groups with a benchmark '
             'company each'],
            ['peer_percentiles', '550', 'Percentile rank per metric '
             'within a peer group'],
            ['documents', '1,585', 'Annual report links filed with BSE']
         ],
         widths=[38 * mm, 18 * mm, CONTENT_WIDTH - 56 * mm],
         mono_columns=(0,)
      ),
      Spacer(1, 4 * mm),
      _callout(
         'Read this before quoting any valuation number',
         'The market_cap and stock_prices datasets are SIMULATED. Every '
         'P/E, P/B, EV/EBITDA, dividend yield and market cap figure in '
         'this platform derives from them. They demonstrate the '
         'calculations working; they are not market data. Anything '
         'labelled SIMULATED must not be used to justify an investment '
         'decision.',
         AMBER
      ),
      Spacer(1, 4 * mm),
      Paragraph('Getting set up', STYLES['heading']),
      _code_block([
         'python -m venv .venv',
         '.venv\\Scripts\\activate          # Windows',
         'source .venv/bin/activate        # macOS or Linux',
         'pip install -r requirements.txt'
      ]),
      _paragraph(
         'The repository already contains a populated database and every '
         'generated output, so you can go straight to the dashboard. '
         'Rebuild from the source Excel files only if the data changes.'
      ),
      _code_block([
         'make load        # Excel to SQLite',
         'make ratios      # populate financial_ratios',
         'make screener    # screener, peer ranks, radar charts',
         'make valuation   # valuation summary and flags',
         'make nlp         # parse analysis text, generate pros/cons',
         'make cashflow    # cash flow intelligence',
         'make tearsheets  # 91 company PDFs, 11 sector PDFs, portfolio',
         'make test        # full test suite'
      ]),
      _paragraph(
         'If <font face="Courier">make</font> is not installed, run any '
         'target directly, for example '
         '<font face="Courier">python -m src.screener.run_screener</font>.'
      )
   ]


def _chapter_two():
   return [
      Paragraph('2. Using the screener', STYLES['chapter']),
      Paragraph(
         'The fastest way to narrow 92 companies down to a shortlist.',
         STYLES['caption']
      ),
      _paragraph(
         'Start the dashboard and open the Screener screen from the '
         'sidebar:'
      ),
      _code_block(['streamlit run src/dashboard/app.py',
                   '# then open http://localhost:8501']),
      Paragraph('The two ways to screen', STYLES['heading']),
      *_bullets([
         '<b>Preset buttons</b> fill in the sliders for a named investment '
         'style. Click Quality, Value, Growth, Dividend, Debt-Free or '
         'Turnaround.',
         '<b>Sliders</b> let you set any of ten thresholds yourself. The '
         'results table updates as you move them.'
      ]),
      _paragraph(
         'A slider parked at its neutral end is not applied, so leaving a '
         'metric alone does not silently exclude companies that happen to '
         'be missing that figure.'
      ),
      Paragraph('The six presets', STYLES['heading']),
      _table(
         ['Preset', 'Looks for', 'Returns'],
         [
            ['Quality Compounder', 'ROE above 15%, D/E under 1, positive '
             'free cash flow, revenue growth above 10%', '22 companies'],
            ['Value Pick', 'P/E under 20, P/B under 3, dividend yield '
             'above 1%', '2 companies'],
            ['Growth Accelerator', 'PAT CAGR above 20%, revenue CAGR '
             'above 15%', '18 companies'],
            ['Dividend Champion', 'Dividend yield above 2%, payout under '
             '80%, positive free cash flow', '30 companies'],
            ['Debt-Free Blue Chip', 'Zero borrowings, ROE above 12%, '
             'revenue above 5,000 Cr', '2 companies'],
            ['Turnaround Watch', 'Revenue CAGR 3yr above 10%, positive '
             'free cash flow, falling leverage', '34 companies']
         ],
         widths=[36 * mm, CONTENT_WIDTH - 66 * mm, 30 * mm]
      ),
      Spacer(1, 4 * mm),
      _callout(
         'Why Value Pick and Debt-Free return so few companies',
         'Both are working correctly. Value Pick screens on P/E and P/B, '
         'which are uncorrelated in the simulated dataset (r = -0.11) '
         'where in real markets they move together: 15 companies pass the '
         'P/E test and 9 pass the P/B test, but only 2 pass both. '
         'Debt-Free requires literally zero borrowings, and only 3 of 92 '
         'companies report that. Relaxing D/E to below 0.05, the '
         'conventional market definition of debt free, returns 16. Both '
         'calibrations are documented in config/screener_config.yaml.',
         AMBER
      ),
      Spacer(1, 4 * mm),
      Paragraph('Two rules that are not on the sliders', STYLES['heading']),
      *_bullets([
         '<b>Banks are exempt from the D/E ceiling.</b> A debt-to-equity '
         'limit does not reject Financials, because leverage of 8 is '
         'structurally normal for a lender. In the Excel export those '
         'cells appear red: the company was admitted by the rule, not by '
         'the number.',
         '<b>No interest expense means infinite coverage.</b> A company '
         'with no debt has no interest coverage ratio to compute. It '
         'passes any coverage minimum rather than failing on a blank.'
      ]),
      Paragraph('Exporting', STYLES['heading']),
      _paragraph(
         'The Download CSV button exports exactly the rows and columns on '
         'screen. For the full preset run with colour coding, use '
         '<font face="Courier">output/screener_output.xlsx</font>, which '
         'has one sheet per preset plus a summary.'
      ),
      _callout(
         'The dashboard presets are an approximation',
         'Three preset rules cannot be expressed as a slider: an equality '
         'test (D/E exactly zero), a payout cap, and a year-on-year '
         'direction. The dashboard therefore returns more companies than '
         'the workbook for Debt-Free (33 vs 2), Dividend (33 vs 30) and '
         'Turnaround (40 vs 34). Run make screener for the authoritative '
         'result.',
         NAVY
      )
   ]


def _chapter_three():
   return [
      Paragraph('3. The eight dashboard screens', STYLES['chapter']),
      Paragraph(
         'What each screen is for and what to watch out for on it.',
         STYLES['caption']
      ),
      Paragraph('1. Home', STYLES['heading']),
      _paragraph(
         'Index-level summary: six KPI tiles, a sector donut, the top five '
         'companies by composite quality score, and a table of sector '
         'medians. The sidebar year selector re-points the valuation '
         'tiles between 2019 and 2024.'
      ),
      _callout(
         'Average ROE reads 122%',
         'That is not a bug in the calculation. A handful of companies '
         'report equity figures that are not on the same scale as their '
         'profit, which inflates the mean. The tile tooltip gives the '
         'median, 15.8%, which is the figure to quote. All such cases are '
         'itemised in output/ratio_edge_cases.log.',
         AMBER
      ),
      Spacer(1, 3 * mm),
      Paragraph('2. Company Profile', STYLES['heading']),
      _paragraph(
         'One company in detail. Search by name or ticker, then read the '
         'company card, six KPI tiles, a ten-year revenue and profit bar '
         'chart, a dual-axis ROE and ROCE line chart, and the generated '
         'pros and cons. A company with fewer than ten years of data '
         'shows what it has, with a note saying so.'
      ),
      Paragraph('3. Screener', STYLES['heading']),
      _paragraph('Covered in chapter 2.'),
      Paragraph('4. Peer Comparison', STYLES['heading']),
      _paragraph(
         'Pick one of the 11 peer groups and see any member drawn against '
         'the peer average on eight axes, plus a side-by-side table with '
         'the benchmark company highlighted in amber. The radar plots '
         'percentile ranks, not raw values, because an ROE of 30 and a '
         'D/E of 0.3 cannot share a radius. Debt to equity is inverted, '
         'so further from the centre is better on every axis.'
      ),
      Paragraph('5. Trend Analysis', STYLES['heading']),
      _paragraph(
         'Overlay up to three metrics across ten years. Each point is '
         'annotated with its change against the prior year. Each metric '
         'gets its own axis so a percentage and a crore figure can share '
         'the chart.'
      ),
      Paragraph('6. Sector Analysis', STYLES['heading']),
      _paragraph(
         'Revenue against ROE as a bubble chart, sized by market cap and '
         'coloured by sub-sector, with sector median bars underneath. '
         'Companies without a market cap are drawn at the smallest bubble '
         'size rather than dropped.'
      ),
      Paragraph('7. Capital Allocation', STYLES['heading']),
      _paragraph(
         'A treemap of every company grouped by what it does with its '
         'cash, derived from the signs of operating, investing and '
         'financing cash flow. Click a pattern to list its members.'
      ),
      _table(
         ['Pattern', 'CFO', 'CFI', 'CFF', 'Reading'],
         [
            ['Reinvestor', '+', '-', '-', 'Generates cash, reinvests it'],
            ['Shareholder Returns', '+', '-', '-',
             'As above but CFO exceeds profit'],
            ['Cash Accumulator', '+', '+', '+', 'Cash in from everywhere'],
            ['Liquidating Assets', '+', '+', '-',
             'Selling assets, repaying capital'],
            ['Growth Funded by Debt', '-', '-', '+',
             'Investing while operations consume cash'],
            ['Mixed', '+', '-', '+',
             'Generates cash, invests, still raises funds'],
            ['Distress Signal', '-', '+', '+',
             'Burning cash, selling assets, borrowing'],
            ['Pre-Revenue', '-', '-', '-', 'Cash out across the board']
         ],
         widths=[38 * mm, 11 * mm, 11 * mm, 11 * mm,
                 CONTENT_WIDTH - 71 * mm]
      ),
      Spacer(1, 3 * mm),
      _paragraph(
         'Two companies fall into a ninth sign combination that the eight '
         'standard patterns do not name, and show as Unknown Pattern.'
      ),
      Paragraph('8. Annual Reports', STYLES['heading']),
      _paragraph(
         'Available report years with clickable BSE PDF links. 52 links '
         'are missing from the source data and show a red Report '
         'unavailable badge. Link checking against bseindia.com is '
         'opt-in, because verifying every URL on each page load would '
         'take the screen past its three second budget.'
      )
   ]


def _chapter_four():
   return [
      Paragraph('4. Reading a tearsheet', STYLES['chapter']),
      Paragraph(
         'The two-page PDF summary produced for each company.',
         STYLES['caption']
      ),
      _paragraph(
         'Tearsheets live in '
         '<font face="Courier">reports/tearsheets/</font>, one per '
         'company, named '
         '<font face="Courier">{TICKER}_tearsheet.pdf</font>.'
      ),
      Paragraph('Page 1', STYLES['heading']),
      *_bullets([
         'Navy header with the company name, ticker and sector',
         'Six KPI tiles: ROE, ROCE, net profit margin, D/E, revenue CAGR '
         'and free cash flow',
         'Ten-year revenue and net profit bars',
         'ROE and ROCE on a dual axis, so a scale difference between them '
         'does not flatten one line'
      ]),
      Paragraph('Page 2', STYLES['heading']),
      *_bullets([
         'Balance sheet composition: net worth, borrowings and other '
         'liabilities stacked by year',
         'Cash flow waterfall for the latest year, ending in net cash '
         'flow',
         'A capital allocation badge naming the pattern',
         'Pros in green and cons in red, each with a confidence percentage'
      ]),
      Paragraph('What the confidence percentage means', STYLES['heading']),
      _paragraph(
         'Each pro and con comes from a rule. The percentage is how '
         'strongly the company clears that rule\'s threshold, not a '
         'probability of anything happening. A rule reports 60 when a '
         'company only just qualifies and 100 when it clears the bar '
         'comfortably. Only statements scoring above 60 are printed.'
      ),
      _callout(
         'Two rule ids to treat differently',
         'PRO-13 and CON-13 are relative, not absolute. They appear only '
         'when a company triggered no absolute rule at all, and they name '
         'its strongest or weakest metric against its sector. A CON-13 '
         'reading "no absolute red flag, but ranks in only the 40th '
         'percentile" is not a warning; it means nothing was found. 47 of '
         'the 92 companies trip no absolute con rule because they are '
         'genuinely clean.',
         NAVY
      ),
      Spacer(1, 4 * mm),
      Paragraph('Generating tearsheets', STYLES['heading']),
      _code_block([
         '# every company, plus sector and portfolio PDFs',
         'make tearsheets',
         '',
         '# a specific few',
         'python -m src.reports.tearsheet TCS HDFCBANK RELIANCE'
      ]),
      _paragraph(
         'The batch takes a few minutes because each tearsheet renders '
         'four charts. Companies with fewer than three years of data are '
         'skipped and logged to '
         '<font face="Courier">output/skipped_tearsheets.csv</font>; at '
         'present that is one company, JIOFIN.'
      ),
      Paragraph('The other PDF outputs', STYLES['heading']),
      _table(
         ['Output', 'Location', 'Contents'],
         [
            ['Sector reports', 'reports/sector/', 'One PDF per sector: '
             'median KPIs and every company with 8 metrics'],
            ['Portfolio summary', 'reports/portfolio/', 'One page per '
             'company with six KPIs and trend arrows'],
            ['Radar charts', 'reports/radar_charts/', 'One PNG per '
             'company against its peer or index average']
         ],
         widths=[34 * mm, 44 * mm, CONTENT_WIDTH - 78 * mm],
         mono_columns=(1,)
      ),
      Spacer(1, 3 * mm),
      _paragraph(
         'In the portfolio summary, a green triangle means the metric '
         'improved against the prior year, red means it declined, and a '
         'grey marker means the change was within 2% either way. For debt '
         'to equity a fall counts as an improvement.'
      )
   ]


def _chapter_five():
   return [
      Paragraph('5. Calling the API', STYLES['chapter']),
      Paragraph(
         '16 read-only endpoints under /api/v1.',
         STYLES['caption']
      ),
      _code_block([
         'uvicorn src.api.main:app --port 8000',
         '# interactive docs at http://localhost:8000/docs'
      ]),
      _paragraph(
         'The API and the dashboard can run at the same time; they use '
         'different ports and there is no conflict.'
      ),
      Paragraph('Endpoints', STYLES['heading']),
      _table(
         ['Endpoint', 'Returns'],
         [
            ['GET /health', 'Status, row counts for all 10 tables, '
             'uptime, version'],
            ['GET /companies', 'All 92 companies; filter by sector, '
             'market_cap_category or search'],
            ['GET /companies/{ticker}', 'Full profile: master record, '
             'sector, latest KPIs'],
            ['GET /companies/{ticker}/pl', 'Profit and loss history'],
            ['GET /companies/{ticker}/bs', 'Balance sheet history'],
            ['GET /companies/{ticker}/cashflow', 'Cash flow history'],
            ['GET /companies/{ticker}/ratios', 'Computed KPIs per year'],
            ['GET /companies/{ticker}/tearsheet', 'The tearsheet PDF as '
             'a download'],
            ['GET /companies/{ticker}/peers/compare', 'Radar data: 8 '
             'axes, peer average, benchmark'],
            ['GET /companies/{ticker}/documents', 'Annual report links '
             'with a validity flag'],
            ['GET /screener', 'Ranked results for any threshold '
             'combination'],
            ['GET /sectors', 'Every sector with counts and medians'],
            ['GET /sectors/{sector}/companies', 'Companies in a sector '
             'with latest KPIs'],
            ['GET /peers/{group_name}', 'Peer group with a percentile '
             'rank per metric'],
            ['GET /market-cap/{ticker}', 'Valuation multiples 2019 to '
             '2024 (SIMULATED)'],
            ['GET /portfolio/stats', 'P10 to P90, mean and std for 10 '
             'KPIs']
         ],
         widths=[74 * mm, CONTENT_WIDTH - 74 * mm],
         mono_columns=(0,)
      ),
      Spacer(1, 4 * mm),
      Paragraph('Worked examples', STYLES['heading']),
      _code_block([
         '# is the service healthy?',
         'curl http://localhost:8000/api/v1/health',
         '',
         '# quality companies: ROE above 15, D/E under 1',
         'curl "http://localhost:8000/api/v1/screener?min_roe=15&max_de=1"',
         '',
         '# run a named preset instead of raw thresholds',
         'curl "http://localhost:8000/api/v1/screener'
         '?preset=quality_compounder"',
         '',
         '# one company in full',
         'curl http://localhost:8000/api/v1/companies/TCS',
         '',
         '# ten years of computed ratios',
         'curl http://localhost:8000/api/v1/companies/TCS/ratios',
         '',
         '# a single year',
         'curl "http://localhost:8000/api/v1/companies/TCS/ratios'
         '?year=Mar%202024"',
         '',
         '# profit and loss for a date range',
         'curl "http://localhost:8000/api/v1/companies/TCS/pl'
         '?from_year=2020-03&to_year=2024-03"',
         '',
         '# download a tearsheet',
         'curl -o tcs.pdf '
         'http://localhost:8000/api/v1/companies/TCS/tearsheet',
         '',
         '# peer group with percentile ranks',
         'curl "http://localhost:8000/api/v1/peers/IT%20Services"',
         '',
         '# index-wide percentile table',
         'curl http://localhost:8000/api/v1/portfolio/stats'
      ]),
      Paragraph('Status codes', STYLES['heading']),
      _table(
         ['Code', 'When'],
         [
            ['200', 'Success'],
            ['400', 'A threshold is out of range, a preset name is '
             'unknown, or a year is not YYYY-MM'],
            ['404', 'Unknown ticker, sector or peer group; or no '
             'tearsheet exists for that company'],
            ['422', 'FastAPI rejected the query type, for example '
             'limit=0']
         ],
         widths=[18 * mm, CONTENT_WIDTH - 18 * mm],
         mono_columns=(0,)
      ),
      Spacer(1, 3 * mm),
      _paragraph(
         'A company with no peer group returns HTTP 200 with the message '
         '"No peer group assigned" rather than a 404. 37 of the 92 '
         'companies are in that position, and it is a normal answer '
         'rather than an error.'
      ),
      _paragraph(
         'The OpenAPI 3 specification is exported to '
         '<font face="Courier">docs/openapi.json</font> and can be '
         'imported into Postman.'
      )
   ]


def _chapter_six():
   return [
      Paragraph('6. Company archetypes and statistics', STYLES['chapter']),
      Paragraph(
         'What the clustering says and how to read the supporting files.',
         STYLES['caption']
      ),
      _paragraph(
         'Every company is assigned to one of five archetypes by KMeans '
         'clustering on five features: ROE, debt to equity, revenue CAGR, '
         'free cash flow CAGR and operating margin. Assignments are in '
         '<font face="Courier">output/cluster_labels.csv</font>.'
      ),
      _table(
         ['Archetype', 'Companies', 'Profile'],
         [
            ['High-Quality Compounders', '10', 'Very high returns with '
             'low leverage'],
            ['High-Margin Franchises', '13', 'Operating margins near '
             '80%, moderate returns'],
            ['Emerging Growth', '26', 'Strong revenue and cash flow '
             'growth'],
            ['Defensive Dividend Payers', '28', 'Mature, slower growth, '
             'low leverage'],
            ['Leveraged Financials', '15', 'Banks and NBFCs, mean D/E '
             'near 7']
         ],
         widths=[52 * mm, 22 * mm, CONTENT_WIDTH - 74 * mm]
      ),
      Spacer(1, 4 * mm),
      _callout(
         'Why two names differ from the project document',
         'The document offers five example archetype names. Two do not '
         'describe what the clustering actually found: the most leveraged '
         'cluster is entirely banks and NBFCs, so it is named for its '
         'leverage rather than called Emerging Growth; and one cluster '
         'carries 80% margins with modest returns, which makes it a '
         'high-margin group rather than a distressed one. No cluster in '
         'this universe is genuinely distressed, since the weakest still '
         'averages 13% ROE.',
         NAVY
      ),
      Spacer(1, 4 * mm),
      Paragraph('Supporting files', STYLES['heading']),
      _table(
         ['File', 'What it tells you'],
         [
            ['output/portfolio_stats.csv', 'P10 to P90, mean and '
             'standard deviation for 10 KPIs. Use it to judge whether a '
             'company is unusual before quoting a number'],
            ['output/outlier_report.csv', 'Companies more than 3 '
             'standard deviations from their sector mean on any metric'],
            ['output/cluster_profiles.csv', 'Mean and median of each '
             'feature per cluster'],
            ['reports/elbow_plot.png', 'Inertia against k, showing why '
             'five clusters was chosen'],
            ['reports/correlation_heatmap.png', 'Pearson correlation of '
             '10 KPIs across the index'],
            ['output/cashflow_intelligence.xlsx', 'CFO quality, CapEx '
             'intensity, distress and deleveraging flags per company'],
            ['output/distress_alerts.csv', 'Companies burning operating '
             'cash while raising financing']
         ],
         widths=[62 * mm, CONTENT_WIDTH - 62 * mm],
         mono_columns=(0,)
      ),
      Spacer(1, 4 * mm),
      _callout(
         'The distress flag over-reports lenders',
         'The flag fires when operating cash flow is negative and '
         'financing cash flow is positive. For a bank or NBFC that is the '
         'ordinary signature of loan book growth, not trouble: 9 of the '
         '13 flagged companies are profitable Financials, including one '
         'with 14,451 Cr of net profit. distress_alerts.csv carries a '
         'structurally_normal_for_sector column that separates those from '
         'the four worth reviewing.',
         RED
      ),
      Spacer(1, 4 * mm),
      _callout(
         'Read the correlation heatmap with care',
         'Pearson correlation is sensitive to the extreme source values '
         'documented in ratio_edge_cases.log. ROE against asset turnover '
         'reads +0.96 on Pearson but only +0.49 on rank correlation, and '
         'net profit margin against interest coverage reads +0.79 against '
         '+0.09. Where those disagree, the coefficient reflects a few '
         'companies rather than a relationship across the index. The '
         'figure carries a footnote naming the worst offenders.',
         AMBER
      )
   ]


def _chapter_seven():
   return [
      Paragraph('7. Troubleshooting', STYLES['chapter']),
      Paragraph(
         'Things that look wrong but are not, and things that are.',
         STYLES['caption']
      ),
      Paragraph('Numbers that look wrong but are correct',
                STYLES['heading']),
      _table(
         ['What you see', 'Why', 'What to do'],
         [
            ['A ratio shows N/A',
             'The input was missing or the denominator was zero. The '
             'engine returns nothing rather than dividing by zero',
             'Check the company on the Profile screen; the note says how '
             'many years exist'],
            ['Interest coverage is blank',
             'The company has no interest expense, so there is nothing '
             'to divide by. It is debt free',
             'Read it as infinite coverage. It passes coverage filters'],
            ['PAT CAGR is blank but revenue CAGR is not',
             'The company was loss-making in the base year, so a growth '
             'rate would be meaningless',
             'Nothing. This is the documented TURNAROUND case'],
            ['Average ROE is 122%',
             'A few companies report equity on a different scale from '
             'profit',
             'Use the median, 15.8%. See ratio_edge_cases.log'],
            ['A bank passed a D/E filter it should have failed',
             'Financials are exempt from D/E ceilings by design',
             'Nothing. Red cells in the Excel export mark these rows'],
            ['A profitable company is flagged distressed',
             'It is a lender, and lending growth looks like negative '
             'operating cash flow',
             'Check structurally_normal_for_sector in '
             'distress_alerts.csv']
         ],
         widths=[46 * mm, 58 * mm, CONTENT_WIDTH - 104 * mm]
      ),
      Spacer(1, 4 * mm),
      Paragraph('Things that are actually broken', STYLES['heading']),
      _table(
         ['Symptom', 'Cause', 'Fix'],
         [
            ['Dashboard says the database was not found',
             'data/nifty100.db is missing',
             'Run make load then make ratios'],
            ['A screen errors on a missing column',
             'The ratio engine has not been run since a schema change',
             'Run make ratios'],
            ['Capital Allocation screen is empty',
             'output/capital_allocation.csv has not been generated',
             'Run make ratios'],
            ['Tearsheet endpoint returns 404',
             'That company was skipped for having under 3 years of data, '
             'or the batch has not run',
             'Check output/skipped_tearsheets.csv, then run '
             'make tearsheets'],
            ['Clusters endpoint returns 0',
             'cluster_labels.csv has not been generated',
             'Run python -m src.analytics.clustering'],
            ['Two tickers cannot be found in any search',
             'ULTRACEMCO and UNIONBANK appear in the statements but have '
             'no company master record',
             'A source data defect. They still appear in aggregates']
         ],
         widths=[46 * mm, 58 * mm, CONTENT_WIDTH - 104 * mm]
      ),
      Spacer(1, 5 * mm),
      Paragraph('Known data limitations', STYLES['heading']),
      *_bullets([
         '<b>companies.xlsx is truncated.</b> It holds 92 rows and stops '
         'part way through the alphabet, so eight tickers appear in the '
         'financial statements with no master record.',
         '<b>SBIN has no computed financials</b> despite being the '
         'designated Public Sector Banks benchmark, so that peer group '
         'has no highlighted benchmark row.',
         '<b>The analysis table covers 5 companies</b>, not 92. It is '
         'used to cross-check the CAGR engine, not as a data source.',
         '<b>prosandcons covers 16 companies</b>, so all generated pros '
         'and cons come from financial rules rather than supplied text.',
         '<b>There are 10 broad sectors, not 11.</b> The eleventh entry '
         'in sector listings is the Unclassified bucket.',
         '<b>119 duplicate company-year rows</b> exist in the source '
         'statements. Analytics de-duplicate before counting.',
         '<b>Operating profit is EBITDA by construction.</b> The source '
         'P&amp;L reports operating profit before depreciation, confirmed '
         'against the P&amp;L identity across 1,263 rows.'
      ]),
      Spacer(1, 3 * mm),
      Paragraph('Where to look next', STYLES['heading']),
      _table(
         ['Question', 'Document'],
         [
            ['Why was a ratio implemented this way?',
             'output/ratio_edge_cases.log'],
            ['What was decided in a given sprint?',
             'docs/Sprint2_retrospective.md through Sprint6'],
            ['Is the platform meeting its acceptance criteria?',
             'docs/acceptance_checklist.pdf'],
            ['How fast is it, and where is the cost?',
             'output/perf_notes.md'],
            ['What does the test suite cover?',
             'reports/pytest_report.html']
         ],
         widths=[74 * mm, CONTENT_WIDTH - 74 * mm],
         mono_columns=(1,)
      ),
      Spacer(1, 5 * mm),
      _callout(
         'One closing note',
         'This platform organises published financial statements. It does '
         'not value companies, forecast anything, or recommend action. '
         'The rule confidence scores measure how strongly a threshold was '
         'cleared, not the likelihood of any outcome. Every valuation '
         'metric comes from simulated data. Treat the output as a '
         'starting point for analysis, not a conclusion.',
         GREEN
      )
   ]


def build_guide(output_path=OUTPUT_PATH):
   '''Render the analyst guide to a PDF and return its path.'''
   destination = Path(output_path)
   destination.parent.mkdir(parents=True, exist_ok=True)

   document = SimpleDocTemplate(
      str(destination),
      pagesize=A4,
      leftMargin=16 * mm,
      rightMargin=16 * mm,
      topMargin=15 * mm,
      bottomMargin=15 * mm,
      title='N100 Analyst Guide',
      author='N100 Financial Intelligence Platform'
   )

   chapters = [
      _chapter_one(),
      _chapter_two(),
      _chapter_three(),
      _chapter_four(),
      _chapter_five(),
      _chapter_six(),
      _chapter_seven()
   ]

   story = list(_cover())

   for chapter in chapters:
      story.append(PageBreak())
      story.extend(chapter)

   document.build(story)

   return destination


def main():
   destination = build_guide()
   size_kb = destination.stat().st_size / 1024

   import re
   pages = len(
      re.findall(rb'/Type\s*/Page[^s]', destination.read_bytes())
   )

   print(f'Wrote {destination}')
   print(f'  pages : {pages}')
   print(f'  size  : {size_kb:,.1f} KB')

   if pages < 10:
      print(f'  WARNING: AC-20 requires at least 10 pages, found {pages}')


if __name__ == '__main__':
   main()
