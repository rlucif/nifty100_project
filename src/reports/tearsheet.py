'''
Sprint 5 Day 33, built with ReportLab.
   Page 1  navy header bar, six KPI tiles in two rows of three,
           revenue and net profit bars, ROE and ROCE dual axis
   Page 2  balance sheet composition, cash flow waterfall,
           pros and cons, capital allocation badge

Charts are rendered with matplotlib to an in-memory PNG and placed as
images, which keeps the chart code shared with the rest of the project
instead of reimplementing plotting in ReportLab primitives.
Every table cell is a Paragraph so that long text wraps rather than
overflowing its column, which is the Day 33 layout requirement.

Run with:
   python -m src.reports.tearsheet TCS HDFCBANK RELIANCE
'''

import io
import sqlite3
import sys
from pathlib import Path
import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_LEFT  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.platypus import (  # noqa: E402
   Image,
   PageBreak,
   Paragraph,
   SimpleDocTemplate,
   Spacer,
   Table,
   TableStyle
)

from src.nlp.features import build_company_features, load_history  # noqa: E402

DB_PATH = 'data/nifty100.db'
OUTPUT_DIR = 'reports/tearsheets'
PROS_CONS_PATH = 'output/pros_cons_generated.csv'
CAPITAL_ALLOCATION_PATH = 'output/capital_allocation.csv'

# Companies with less history than this are skipped on Day 34.
MINIMUM_YEARS = 3

HISTORY_YEARS = 10
MAX_BULLETS = 5

NAVY = colors.HexColor('#1F3864')
RED = colors.HexColor('#C00000')
GREEN = colors.HexColor('#2E7D32')
LIGHT_GREY = colors.HexColor('#F2F2F2')
MID_GREY = colors.HexColor('#BFBFBF')

PAGE_WIDTH, PAGE_HEIGHT = A4
CONTENT_WIDTH = PAGE_WIDTH - 24 * mm

STYLES = {
   'title': ParagraphStyle(
      'title', fontName='Helvetica-Bold', fontSize=17,
      textColor=colors.white, leading=21
   ),
   'subtitle': ParagraphStyle(
      'subtitle', fontName='Helvetica', fontSize=9.5,
      textColor=colors.HexColor('#D6DCE5'), leading=13
   ),
   'section': ParagraphStyle(
      'section', fontName='Helvetica-Bold', fontSize=11,
      textColor=NAVY, spaceAfter=4, leading=14
   ),
   'tile_label': ParagraphStyle(
      'tile_label', fontName='Helvetica', fontSize=7.5,
      textColor=colors.HexColor('#595959'), alignment=TA_CENTER, leading=10
   ),
   'tile_value': ParagraphStyle(
      'tile_value', fontName='Helvetica-Bold', fontSize=14,
      textColor=NAVY, alignment=TA_CENTER, leading=17
   ),
   'body': ParagraphStyle(
      'body', fontName='Helvetica', fontSize=8.5,
      leading=11.5, alignment=TA_LEFT
   ),
   'pro': ParagraphStyle(
      'pro', fontName='Helvetica', fontSize=8.5,
      leading=11.5, textColor=colors.HexColor('#1B5E20')
   ),
   'con': ParagraphStyle(
      'con', fontName='Helvetica', fontSize=8.5,
      leading=11.5, textColor=colors.HexColor('#8B0000')
   ),
   'caption': ParagraphStyle(
      'caption', fontName='Helvetica-Oblique', fontSize=7,
      textColor=colors.HexColor('#7F7F7F'), leading=9
   ),
   'badge': ParagraphStyle(
      'badge', fontName='Helvetica-Bold', fontSize=9.5,
      textColor=colors.white, alignment=TA_CENTER, leading=13
   )
}


def get_connection():
   return sqlite3.connect(DB_PATH)


# Formatting helpers
def _fmt(value, suffix='', decimals=1):
   if value is None or pd.isna(value):
      return 'N/A'

   try:
      return f'{float(value):,.{decimals}f}{suffix}'
   except (TypeError, ValueError):
      return 'N/A'


def _chart_image(figure, width, height):
   buffer = io.BytesIO()
   figure.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
   plt.close(figure)
   buffer.seek(0)

   return Image(buffer, width=width, height=height)


# Charts
def _revenue_profit_chart(group):
   figure, axes = plt.subplots(figsize=(4.4, 2.5))
   recent = group.tail(HISTORY_YEARS)

   positions = range(len(recent))
   width = 0.4

   axes.bar(
      [p - width / 2 for p in positions], recent['sales'],
      width=width, label='Revenue', color='#1F3864'
   )
   axes.bar(
      [p + width / 2 for p in positions], recent['net_profit'],
      width=width, label='Net profit', color='#2E7D32'
   )

   axes.set_xticks(list(positions))
   axes.set_xticklabels(
      [str(year)[-4:] for year in recent['year']], fontsize=6, rotation=45
   )
   axes.set_ylabel('INR Crore', fontsize=7)
   axes.tick_params(axis='y', labelsize=6)
   axes.legend(fontsize=6, frameon=False)
   axes.grid(axis='y', color='#E0E0E0', linewidth=0.5)
   axes.set_axisbelow(True)
   for spine in ('top', 'right'):
      axes.spines[spine].set_visible(False)

   return _chart_image(figure, CONTENT_WIDTH / 2 - 3 * mm, 44 * mm)


def _returns_chart(group):
   figure, axes = plt.subplots(figsize=(4.4, 2.5))
   recent = group.tail(HISTORY_YEARS)
   labels = [str(year)[-4:] for year in recent['year']]

   axes.plot(
      labels, recent['return_on_equity_pct'],
      color='#1F3864', marker='o', markersize=3, linewidth=1.6, label='ROE %'
   )
   axes.set_ylabel('ROE %', fontsize=7, color='#1F3864')
   axes.tick_params(axis='y', labelsize=6, colors='#1F3864')
   axes.tick_params(axis='x', labelsize=6, rotation=45)

   twin = axes.twinx()
   twin.plot(
      labels, recent['return_on_capital_employed_pct'],
      color='#C00000', marker='s', markersize=3, linewidth=1.6,
      linestyle='--', label='ROCE %'
   )
   twin.set_ylabel('ROCE %', fontsize=7, color='#C00000')
   twin.tick_params(axis='y', labelsize=6, colors='#C00000')

   axes.grid(axis='y', color='#E0E0E0', linewidth=0.5)
   axes.set_axisbelow(True)
   axes.spines['top'].set_visible(False)
   twin.spines['top'].set_visible(False)

   handles = axes.get_lines() + twin.get_lines()
   axes.legend(
      handles, [line.get_label() for line in handles],
      fontsize=6, frameon=False, loc='best'
   )

   return _chart_image(figure, CONTENT_WIDTH / 2 - 3 * mm, 44 * mm)


def _balance_sheet_chart(group):
   figure, axes = plt.subplots(figsize=(4.4, 2.5))
   recent = group.tail(HISTORY_YEARS)
   labels = [str(year)[-4:] for year in recent['year']]

   equity = pd.to_numeric(recent['equity_capital'], errors='coerce').fillna(0)
   reserves = pd.to_numeric(recent['reserves'], errors='coerce').fillna(0)
   borrowings = pd.to_numeric(recent['borrowings'], errors='coerce').fillna(0)
   total_assets = pd.to_numeric(
      recent['total_assets'], errors='coerce'
   ).fillna(0)

   net_worth = equity + reserves
   other = (total_assets - net_worth - borrowings).clip(lower=0)

   axes.bar(labels, net_worth, label='Net worth', color='#1F3864')
   axes.bar(
      labels, borrowings, bottom=net_worth,
      label='Borrowings', color='#C00000'
   )
   axes.bar(
      labels, other, bottom=net_worth + borrowings,
      label='Other liabilities', color='#BFBFBF'
   )

   axes.set_ylabel('INR Crore', fontsize=7)
   axes.tick_params(axis='y', labelsize=6)
   axes.tick_params(axis='x', labelsize=6, rotation=45)
   axes.legend(fontsize=6, frameon=False)
   axes.grid(axis='y', color='#E0E0E0', linewidth=0.5)
   axes.set_axisbelow(True)
   for spine in ('top', 'right'):
      axes.spines[spine].set_visible(False)

   return _chart_image(figure, CONTENT_WIDTH / 2 - 3 * mm, 44 * mm)


def _cash_flow_waterfall(latest):
   figure, axes = plt.subplots(figsize=(4.4, 2.5))

   cfo = float(latest.get('operating_activity') or 0)
   cfi = float(latest.get('investing_activity') or 0)
   cff = float(latest.get('financing_activity') or 0)
   net = cfo + cfi + cff

   labels = ['CFO', 'CFI', 'CFF', 'Net']
   values = [cfo, cfi, cff, net]
   bottoms = [0, cfo, cfo + cfi, 0]
   bar_colours = [
      '#2E7D32' if value >= 0 else '#C00000' for value in values[:3]
   ] + ['#1F3864']

   axes.bar(labels, values, bottom=bottoms, color=bar_colours)
   axes.axhline(0, color='#595959', linewidth=0.8)

   for index, value in enumerate(values):
      offset = bottoms[index] + value
      axes.annotate(
         f'{value:,.0f}',
         (index, offset),
         ha='center',
         va='bottom' if value >= 0 else 'top',
         fontsize=6
      )

   axes.set_ylabel('INR Crore', fontsize=7)
   axes.tick_params(axis='both', labelsize=6)
   axes.grid(axis='y', color='#E0E0E0', linewidth=0.5)
   axes.set_axisbelow(True)
   for spine in ('top', 'right'):
      axes.spines[spine].set_visible(False)

   return _chart_image(figure, CONTENT_WIDTH / 2 - 3 * mm, 44 * mm)


# Layout blocks
def _header(features):
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

   return header


def _kpi_tiles(features):
   tiles = [
      ('ROE', _fmt(features['roe'], '%')),
      ('ROCE', _fmt(features['roce'], '%')),
      ('Net profit margin', _fmt(features['npm'], '%')),
      ('Debt / Equity', _fmt(features['debt_to_equity'], '', 2)),
      ('Revenue CAGR 5y', _fmt(features['revenue_cagr_5yr'], '%')),
      ('Free cash flow', _fmt(features['free_cash_flow'], ' Cr', 0))
   ]

   rows = []
   for start in (0, 3):
      rows.append([
         Table(
            [
               [Paragraph(label, STYLES['tile_label'])],
               [Paragraph(value, STYLES['tile_value'])]
            ],
            colWidths=[CONTENT_WIDTH / 3 - 4 * mm]
         )
         for label, value in tiles[start:start + 3]
      ])

   for row in rows:
      for tile in row:
         tile.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GREY),
            ('BOX', (0, 0), (-1, -1), 0.5, MID_GREY),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
         ]))

   grid = Table(rows, colWidths=[CONTENT_WIDTH / 3] * 3)
   grid.setStyle(TableStyle([
      ('LEFTPADDING', (0, 0), (-1, -1), 2),
      ('RIGHTPADDING', (0, 0), (-1, -1), 2),
      ('TOPPADDING', (0, 0), (-1, -1), 2),
      ('BOTTOMPADDING', (0, 0), (-1, -1), 2)
   ]))

   return grid


def _side_by_side(left, right):
   table = Table(
      [[left, right]],
      colWidths=[CONTENT_WIDTH / 2, CONTENT_WIDTH / 2]
   )
   table.setStyle(TableStyle([
      ('VALIGN', (0, 0), (-1, -1), 'TOP'),
      ('LEFTPADDING', (0, 0), (-1, -1), 0),
      ('RIGHTPADDING', (0, 0), (-1, -1), 0)
   ]))

   return table


def _bullet_block(entries, style, empty_text):
   if not entries:
      return [Paragraph(empty_text, STYLES['caption'])]

   return [
      Paragraph(
         f'&bull; {text} <font size="7">({confidence:.0f}%)</font>',
         style
      )
      for text, confidence in entries
   ]


def _capital_allocation_badge(label):
   text = label or 'Not classified'

   badge = Table(
      [[Paragraph(f'Capital allocation: {text}', STYLES['badge'])]],
      colWidths=[CONTENT_WIDTH]
   )
   badge.setStyle(TableStyle([
      ('BACKGROUND', (0, 0), (-1, -1), NAVY),
      ('TOPPADDING', (0, 0), (-1, -1), 5),
      ('BOTTOMPADDING', (0, 0), (-1, -1), 5)
   ]))

   return badge


# Document build
def build_tearsheet(company_id, group, features, pros, cons,
                    allocation_label, output_path):
   document = SimpleDocTemplate(
      str(output_path),
      pagesize=A4,
      leftMargin=12 * mm,
      rightMargin=12 * mm,
      topMargin=10 * mm,
      bottomMargin=10 * mm,
      title=f'{features.get("company_name") or company_id} tearsheet',
      author='N100 Financial Intelligence Platform'
   )

   story = [
      _header(features),
      Spacer(1, 5 * mm),
      Paragraph('Key metrics', STYLES['section']),
      _kpi_tiles(features),
      Spacer(1, 4 * mm),
      Paragraph('Revenue, profit and returns', STYLES['section']),
      _side_by_side(
         _revenue_profit_chart(group),
         _returns_chart(group)
      ),
      Spacer(1, 2 * mm),
      Paragraph(
         f'Latest period {features.get("latest_year")}. '
         f'{features.get("years_of_data")} years of history available. '
         'All figures in INR Crore.',
         STYLES['caption']
      ),
      PageBreak(),

      _header(features),
      Spacer(1, 5 * mm),
      Paragraph('Balance sheet and cash flow', STYLES['section']),
      _side_by_side(
         _balance_sheet_chart(group),
         _cash_flow_waterfall(group.iloc[-1])
      ),
      Spacer(1, 4 * mm),
      _capital_allocation_badge(allocation_label),
      Spacer(1, 4 * mm)
   ]

   pros_cell = [Paragraph('Pros', STYLES['section'])]
   pros_cell.extend(
      _bullet_block(pros, STYLES['pro'], 'No pro signals triggered.')
   )

   cons_cell = [Paragraph('Cons', STYLES['section'])]
   cons_cell.extend(
      _bullet_block(cons, STYLES['con'], 'No con signals triggered.')
   )

   analysis = Table(
      [[pros_cell, cons_cell]],
      colWidths=[CONTENT_WIDTH / 2 - 2 * mm, CONTENT_WIDTH / 2 - 2 * mm]
   )
   analysis.setStyle(TableStyle([
      ('VALIGN', (0, 0), (-1, -1), 'TOP'),
      ('LEFTPADDING', (0, 0), (-1, -1), 4),
      ('RIGHTPADDING', (0, 0), (-1, -1), 4),
      ('TOPPADDING', (0, 0), (-1, -1), 4),
      ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
      ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#F1F8F1')),
      ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#FDF2F2')),
      ('BOX', (0, 0), (0, 0), 0.5, GREEN),
      ('BOX', (1, 0), (1, 0), 0.5, RED)
   ]))

   story.append(analysis)
   story.append(Spacer(1, 3 * mm))
   story.append(Paragraph(
      'Pros and cons are generated from the Sprint 5 rule engine. '
      'Percentages are rule confidence, not probability of outcome. '
      'Valuation inputs are simulated data.',
      STYLES['caption']
   ))

   document.build(story)

   return output_path


# Data assembly
def load_pros_and_cons():
   path = Path(PROS_CONS_PATH)
   if not path.exists():
      return {}

   frame = pd.read_csv(path)
   lookup = {}

   for company_id, group in frame.groupby('company_id'):
      ordered = group.sort_values('confidence_pct', ascending=False)
      lookup[company_id] = {
         'pro': [
            (row.text, row.confidence_pct)
            for row in ordered[ordered['type'] == 'pro'].itertuples()
         ][:MAX_BULLETS],
         'con': [
            (row.text, row.confidence_pct)
            for row in ordered[ordered['type'] == 'con'].itertuples()
         ][:MAX_BULLETS]
      }

   return lookup


def load_allocation_labels():
   path = Path(CAPITAL_ALLOCATION_PATH)
   if not path.exists():
      return {}

   from src.analytics.periods import add_period_columns

   frame = add_period_columns(pd.read_csv(path))
   frame = frame[frame['period_sort_key'] > 0]
   frame = frame.sort_values(['company_id', 'period_sort_key'])
   latest = frame.groupby('company_id').tail(1)

   return dict(zip(latest['company_id'], latest['pattern_label']))


def generate_tearsheets(company_ids=None, output_dir=OUTPUT_DIR):
   history = load_history()
   features = build_company_features(history)
   pros_cons = load_pros_and_cons()
   allocation_labels = load_allocation_labels()
   destination = Path(output_dir)
   destination.mkdir(parents=True, exist_ok=True)
   targets = company_ids or sorted(features)
   generated = []
   skipped = []

   for company_id in targets:
      company_features = features.get(company_id)

      if company_features is None:
         skipped.append({
            'company_id': company_id,
            'reason': 'No financial history available',
            'years_of_data': 0
         })
         continue

      if company_features['years_of_data'] < MINIMUM_YEARS:
         skipped.append({
            'company_id': company_id,
            'reason': f'Fewer than {MINIMUM_YEARS} years of data',
            'years_of_data': company_features['years_of_data']
         })
         continue

      group = history[history['company_id'] == company_id].sort_values('period_sort_key')
      entries = pros_cons.get(company_id, {'pro': [], 'con': []})

      output_path = destination / f'{company_id}_tearsheet.pdf'

      build_tearsheet(
         company_id,
         group,
         company_features,
         entries['pro'],
         entries['con'],
         allocation_labels.get(company_id),
         output_path
      )

      generated.append({
         'company_id': company_id,
         'path': str(output_path),
         'size_kb': round(output_path.stat().st_size / 1024, 1)
      })

   return pd.DataFrame(generated), pd.DataFrame(skipped)


def main():
   requested = sys.argv[1:] or None
   generated_df, skipped_df = generate_tearsheets(requested)

   print(f'Generated {len(generated_df)} tearsheets')
   if not generated_df.empty:
      print(generated_df.to_string(index=False))
   if not skipped_df.empty:
      print()
      print(f'Skipped {len(skipped_df)}:')
      print(skipped_df.to_string(index=False))


if __name__ == '__main__':
   main()
