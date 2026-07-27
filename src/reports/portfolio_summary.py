'''
Trend arrows
   up     the metric improved in the latest year
   down   the metric declined
   flat   the change is within 2% either way
'''

from pathlib import Path

import pandas as pd
from reportlab.graphics.shapes import Drawing, Polygon
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

from src.nlp.features import build_company_features, load_history

OUTPUT_PATH = 'reports/portfolio/portfolio_summary.pdf'

# Percentage change within this band counts as flat.
FLAT_TOLERANCE_PCT = 2.0

NAVY = colors.HexColor('#1F3864')
GREEN = colors.HexColor('#2E7D32')
RED = colors.HexColor('#C00000')
GREY = colors.HexColor('#7F7F7F')
LIGHT_GREY = colors.HexColor('#F2F2F2')
MID_GREY = colors.HexColor('#BFBFBF')

PAGE_WIDTH, PAGE_HEIGHT = A4
CONTENT_WIDTH = PAGE_WIDTH - 24 * mm

# (label, latest feature key, history series key, decimals, suffix, higher_is_better)
KPI_SPECS = [
   ('Return on equity', 'roe', 'roe_series', 1, '%', True),
   ('Operating margin', 'opm', 'opm_series', 1, '%', True),
   ('Revenue', None, 'sales_series', 0, ' Cr', True),
   ('Earnings per share', None, 'eps_series', 2, '', True),
   ('Free cash flow', 'free_cash_flow', 'fcf_series', 0, ' Cr', True),
   ('Debt to equity', 'debt_to_equity', 'de_series', 2, '', False)
]

STYLES = {
   'title': ParagraphStyle(
      'title', fontName='Helvetica-Bold', fontSize=15,
      textColor=colors.white, leading=19
   ),
   'subtitle': ParagraphStyle(
      'subtitle', fontName='Helvetica', fontSize=9,
      textColor=colors.HexColor('#D6DCE5'), leading=12
   ),
   'cover_title': ParagraphStyle(
      'cover_title', fontName='Helvetica-Bold', fontSize=22,
      textColor=NAVY, leading=27, alignment=TA_CENTER
   ),
   'cover_body': ParagraphStyle(
      'cover_body', fontName='Helvetica', fontSize=10,
      leading=15, alignment=TA_CENTER
   ),
   'section': ParagraphStyle(
      'section', fontName='Helvetica-Bold', fontSize=11,
      textColor=NAVY, spaceAfter=4, leading=14
   ),
   'kpi_label': ParagraphStyle(
      'kpi_label', fontName='Helvetica', fontSize=9, leading=12
   ),
   'kpi_value': ParagraphStyle(
      'kpi_value', fontName='Helvetica-Bold', fontSize=12,
      textColor=NAVY, leading=15
   ),
   'kpi_change': ParagraphStyle(
      'kpi_change', fontName='Helvetica', fontSize=8,
      textColor=GREY, leading=11
   ),
   'caption': ParagraphStyle(
      'caption', fontName='Helvetica-Oblique', fontSize=7.5,
      textColor=GREY, leading=10
   )
}


def _fmt(value, decimals=1, suffix=''):
   if value is None or pd.isna(value):
      return 'N/A'

   try:
      return f'{float(value):,.{decimals}f}{suffix}'
   except (TypeError, ValueError):
      return 'N/A'


def classify_trend(current, previous, higher_is_better=True):
   # Returns 'up', 'down', 'flat' or None when it cannot be determined.
   if current is None or previous is None:
      return None
   if pd.isna(current) or pd.isna(previous) or previous == 0:
      return None

   change_pct = (current - previous) / abs(previous) * 100

   if abs(change_pct) <= FLAT_TOLERANCE_PCT:
      return 'flat'

   improved = change_pct > 0 if higher_is_better else change_pct < 0

   return 'up' if improved else 'down'


def percent_change(current, previous):
   if current is None or previous is None:
      return None
   if pd.isna(current) or pd.isna(previous) or previous == 0:
      return None

   return (current - previous) / abs(previous) * 100

# Arrow marker
def _arrow(direction):
   size = 7
   drawing = Drawing(size + 2, size + 2)

   if direction == 'up':
      points = [1, 1, size, 1, size / 2 + 0.5, size]
      colour = GREEN
   elif direction == 'down':
      points = [1, size, size, size, size / 2 + 0.5, 1]
      colour = RED
   elif direction == 'flat':
      points = [1, 1, 1, size, size, size / 2 + 0.5]
      colour = GREY
   else:
      return Paragraph('', STYLES['kpi_change'])

   drawing.add(Polygon(points, fillColor=colour, strokeColor=colour))

   return drawing


def _series_pair(series):
   # Latest and previous values from an ordered series.
   values = [value for value in list(series)]

   if len(values) < 2:
      latest = values[-1] if values else None
      return latest, None

   return values[-1], values[-2]


def _kpi_rows(features):
   rows = []

   for label, latest_key, series_key, decimals, suffix, higher_is_better \
         in KPI_SPECS:
      series = features.get(series_key, pd.Series(dtype='float64'))
      series_latest, previous = _series_pair(series)

      latest = (
         features.get(latest_key) if latest_key else series_latest
      )
      if latest is None:
         latest = series_latest

      direction = classify_trend(latest, previous, higher_is_better)
      change = percent_change(latest, previous)

      change_text = (
         f'{change:+.1f}% vs prior year' if change is not None
         else 'no prior year'
      )

      rows.append([
         Paragraph(label, STYLES['kpi_label']),
         Paragraph(_fmt(latest, decimals, suffix), STYLES['kpi_value']),
         _arrow(direction),
         Paragraph(change_text, STYLES['kpi_change'])
      ])

   table = Table(
      rows,
      colWidths=[
         CONTENT_WIDTH * 0.34,
         CONTENT_WIDTH * 0.26,
         CONTENT_WIDTH * 0.08,
         CONTENT_WIDTH * 0.32
      ]
   )
   table.setStyle(TableStyle([
      ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
      ('GRID', (0, 0), (-1, -1), 0.4, MID_GREY),
      ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, LIGHT_GREY]),
      ('TOPPADDING', (0, 0), (-1, -1), 5),
      ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
      ('LEFTPADDING', (0, 0), (-1, -1), 6),
      ('RIGHTPADDING', (0, 0), (-1, -1), 6)
   ]))

   return table


def _company_page(features):
   name = features.get('company_name') or features['company_id']
   sector = features.get('broad_sector') or 'Unclassified'

   header = Table(
      [[
         Paragraph(str(name), STYLES['title']),
         Paragraph(
            f'{features["company_id"]}<br/>{sector}',
            STYLES['subtitle']
         )
      ]],
      colWidths=[CONTENT_WIDTH * 0.68, CONTENT_WIDTH * 0.32]
   )
   header.setStyle(TableStyle([
      ('BACKGROUND', (0, 0), (-1, -1), NAVY),
      ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
      ('LEFTPADDING', (0, 0), (-1, -1), 8),
      ('RIGHTPADDING', (0, 0), (-1, -1), 8),
      ('TOPPADDING', (0, 0), (-1, -1), 7),
      ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
      ('ALIGN', (1, 0), (1, 0), 'RIGHT')
   ]))

   return [
      header,
      Spacer(1, 6 * mm),
      Paragraph(
         f'Headline metrics for {features.get("latest_year")}',
         STYLES['section']
      ),
      _kpi_rows(features),
      Spacer(1, 4 * mm),
      Paragraph(
         'Arrows compare the latest financial year against the previous '
         f'one. A change within {FLAT_TOLERANCE_PCT:.0f}% either way is '
         'shown as flat. For debt to equity a fall is an improvement. '
         f'{features.get("years_of_data")} years of history available.',
         STYLES['caption']
      )
   ]


def _cover_page(company_count):
   return [
      Spacer(1, 60 * mm),
      Paragraph('N100 Portfolio Summary', STYLES['cover_title']),
      Spacer(1, 6 * mm),
      Paragraph(
         f'{company_count} companies, one page each, in alphabetical '
         'order by ticker.',
         STYLES['cover_body']
      ),
      Spacer(1, 3 * mm),
      Paragraph(
         'Generated by the N100 Financial Intelligence Platform. '
         'All monetary figures in INR Crore. '
         'Valuation inputs are simulated data.',
         STYLES['cover_body']
      )
   ]


def generate_portfolio_summary(output_path=OUTPUT_PATH):
   history = load_history()
   features = build_company_features(history)
   destination = Path(output_path)
   destination.parent.mkdir(parents=True, exist_ok=True)
   ordered_tickers = sorted(features)

   document = SimpleDocTemplate(
      str(destination),
      pagesize=A4,
      leftMargin=12 * mm,
      rightMargin=12 * mm,
      topMargin=12 * mm,
      bottomMargin=12 * mm,
      title='N100 Portfolio Summary',
      author='N100 Financial Intelligence Platform'
   )

   story = _cover_page(len(ordered_tickers))

   for ticker in ordered_tickers:
      story.append(PageBreak())
      story.extend(_company_page(features[ticker]))

   document.build(story)

   return destination, len(ordered_tickers)


def main():
   destination, company_count = generate_portfolio_summary()
   size_kb = destination.stat().st_size / 1024

   print(f'Wrote {destination}')
   print(f'  companies : {company_count}')
   print(f'  pages     : {company_count + 1} (cover plus one per company)')
   print(f'  size      : {size_kb:,.1f} KB')


if __name__ == '__main__':
   main()
