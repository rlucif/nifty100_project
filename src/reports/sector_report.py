'''
Sector count
   The supplied sectors table contains 10 broad sectors, not the 11 the
   project document refers to. Two tickers have no company master record
   and therefore no sector; they are reported together as Unclassified,
   which brings the file count to 11. The count is reported on each run
   so the total is never mistaken for 11 genuine sectors.
'''

import sqlite3
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
   Paragraph,
   SimpleDocTemplate,
   Spacer,
   Table,
   TableStyle
)

from src.screener.engine import ScreenerEngine
from src.screener.universe import build_universe

DB_PATH = 'data/nifty100.db'
OUTPUT_DIR = 'reports/sector'
UNCLASSIFIED = 'Unclassified'

NAVY = colors.HexColor('#1F3864')
LIGHT_GREY = colors.HexColor('#F2F2F2')
MID_GREY = colors.HexColor('#BFBFBF')
PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)
CONTENT_WIDTH = PAGE_WIDTH - 24 * mm

# The eight metrics shown per company.
COMPANY_METRICS = [
   ('return_on_equity_pct', 'ROE %', 1),
   ('return_on_capital_employed_pct', 'ROCE %', 1),
   ('net_profit_margin_pct', 'NPM %', 1),
   ('operating_profit_margin_pct', 'OPM %', 1),
   ('debt_to_equity', 'D/E', 2),
   ('revenue_cagr_5yr', 'Rev CAGR 5y %', 1),
   ('free_cash_flow_cr', 'FCF (Cr)', 0),
   ('composite_quality_score', 'Score', 1)
]

MEDIAN_METRICS = [
   ('return_on_equity_pct', 'Median ROE %', 1),
   ('return_on_capital_employed_pct', 'Median ROCE %', 1),
   ('net_profit_margin_pct', 'Median NPM %', 1),
   ('debt_to_equity', 'Median D/E', 2),
   ('revenue_cagr_5yr', 'Median Rev CAGR 5y %', 1),
   ('composite_quality_score', 'Median score', 1)
]

STYLES = {
   'title': ParagraphStyle(
      'title', fontName='Helvetica-Bold', fontSize=16,
      textColor=colors.white, leading=20
   ),
   'subtitle': ParagraphStyle(
      'subtitle', fontName='Helvetica', fontSize=9,
      textColor=colors.HexColor('#D6DCE5'), leading=12
   ),
   'section': ParagraphStyle(
      'section', fontName='Helvetica-Bold', fontSize=11,
      textColor=NAVY, spaceAfter=4, leading=14
   ),
   'cell': ParagraphStyle(
      'cell', fontName='Helvetica', fontSize=7.5, leading=9.5
   ),
   'cell_bold': ParagraphStyle(
      'cell_bold', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5
   ),
   'header_cell': ParagraphStyle(
      'header_cell', fontName='Helvetica-Bold', fontSize=7.5,
      textColor=colors.white, leading=9.5, alignment=TA_CENTER
   ),
   'tile_label': ParagraphStyle(
      'tile_label', fontName='Helvetica', fontSize=7,
      textColor=colors.HexColor('#595959'), alignment=TA_CENTER, leading=9
   ),
   'tile_value': ParagraphStyle(
      'tile_value', fontName='Helvetica-Bold', fontSize=12,
      textColor=NAVY, alignment=TA_CENTER, leading=15
   ),
   'caption': ParagraphStyle(
      'caption', fontName='Helvetica-Oblique', fontSize=7,
      textColor=colors.HexColor('#7F7F7F'), leading=9
   )
}


def get_connection():
   return sqlite3.connect(DB_PATH)


def _fmt(value, decimals=1):
   if value is None or pd.isna(value):
      return 'N/A'

   try:
      return f'{float(value):,.{decimals}f}'
   except (TypeError, ValueError):
      return 'N/A'


def _header(sector_name, company_count):
   header = Table(
      [[
         Paragraph(f'{sector_name} sector report', STYLES['title']),
         Paragraph(
            f'{company_count} companies<br/>'
            'N100 Financial Intelligence Platform',
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


def _median_tiles(sector_df):
   tiles = []
   for column, label, decimals in MEDIAN_METRICS:
      value = (
         sector_df[column].median() if column in sector_df.columns else None
      )
      tiles.append(
         Table(
            [
               [Paragraph(label, STYLES['tile_label'])],
               [Paragraph(_fmt(value, decimals), STYLES['tile_value'])]
            ],
            colWidths=[CONTENT_WIDTH / 6 - 3 * mm]
         )
      )

   for tile in tiles:
      tile.setStyle(TableStyle([
         ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GREY),
         ('BOX', (0, 0), (-1, -1), 0.5, MID_GREY),
         ('TOPPADDING', (0, 0), (-1, -1), 4),
         ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
      ]))

   grid = Table([tiles], colWidths=[CONTENT_WIDTH / 6] * 6)
   grid.setStyle(TableStyle([
      ('LEFTPADDING', (0, 0), (-1, -1), 2),
      ('RIGHTPADDING', (0, 0), (-1, -1), 2)
   ]))

   return grid


def _company_table(sector_df):
   header = [
      Paragraph('Ticker', STYLES['header_cell']),
      Paragraph('Company', STYLES['header_cell'])
   ] + [
      Paragraph(label, STYLES['header_cell'])
      for _column, label, _decimals in COMPANY_METRICS
   ]

   rows = [header]

   ordered = sector_df.sort_values(
      'composite_quality_score', ascending=False
   )

   for row in ordered.itertuples():
      cells = [
         Paragraph(str(row.company_id), STYLES['cell_bold']),
         Paragraph(str(row.company_name or row.company_id), STYLES['cell'])
      ]

      for column, _label, decimals in COMPANY_METRICS:
         cells.append(
            Paragraph(
               _fmt(getattr(row, column, None), decimals),
               STYLES['cell']
            )
         )

      rows.append(cells)

   metric_width = (CONTENT_WIDTH - 60 * mm) / len(COMPANY_METRICS)
   table = Table(
      rows,
      colWidths=[18 * mm, 42 * mm] + [metric_width] * len(COMPANY_METRICS),
      repeatRows=1
   )

   table.setStyle(TableStyle([
      ('BACKGROUND', (0, 0), (-1, 0), NAVY),
      ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
      ('GRID', (0, 0), (-1, -1), 0.4, MID_GREY),
      ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
      ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
      ('TOPPADDING', (0, 0), (-1, -1), 3),
      ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
      ('LEFTPADDING', (0, 0), (-1, -1), 3),
      ('RIGHTPADDING', (0, 0), (-1, -1), 3)
   ]))

   return table


def build_sector_report(sector_name, sector_df, output_path):
   document = SimpleDocTemplate(
      str(output_path),
      pagesize=landscape(A4),
      leftMargin=12 * mm,
      rightMargin=12 * mm,
      topMargin=10 * mm,
      bottomMargin=10 * mm,
      title=f'{sector_name} sector report',
      author='N100 Financial Intelligence Platform'
   )

   story = [
      _header(sector_name, len(sector_df)),
      Spacer(1, 5 * mm),
      Paragraph('Sector medians', STYLES['section']),
      _median_tiles(sector_df),
      Spacer(1, 5 * mm),
      Paragraph('Companies', STYLES['section']),
      _company_table(sector_df),
      Spacer(1, 3 * mm),
      Paragraph(
         'Ranked by composite quality score. All monetary figures in INR '
         'Crore. Valuation inputs are simulated data.',
         STYLES['caption']
      )
   ]

   document.build(story)

   return output_path


def _safe_filename(sector_name):
   return (
      sector_name.replace(' ', '_')
      .replace('&', 'and')
      .replace('/', '-')
   )


def generate_sector_reports(output_dir=OUTPUT_DIR):
   connection = get_connection()

   try:
      universe_df = build_universe(connection)
   finally:
      connection.close()

   engine = ScreenerEngine()
   engine.load_config()
   universe_df = engine.add_composite_scores(universe_df)

   universe_df['broad_sector'] = universe_df['broad_sector'].fillna(
      UNCLASSIFIED
   )

   destination = Path(output_dir)
   destination.mkdir(parents=True, exist_ok=True)

   generated = []

   for sector_name, sector_df in universe_df.groupby('broad_sector'):
      output_path = (
         destination / f'{_safe_filename(sector_name)}_report.pdf'
      )
      build_sector_report(sector_name, sector_df, output_path)

      generated.append({
         'sector': sector_name,
         'companies': len(sector_df),
         'path': str(output_path),
         'size_kb': round(output_path.stat().st_size / 1024, 1)
      })

   return pd.DataFrame(generated)


def main():
   generated_df = generate_sector_reports()

   print(f'Generated {len(generated_df)} sector reports')
   print(generated_df[['sector', 'companies', 'size_kb']].to_string(
      index=False
   ))

   real_sectors = generated_df[generated_df['sector'] != UNCLASSIFIED]
   print()
   print(
      f'{len(real_sectors)} genuine sectors plus the {UNCLASSIFIED} '
      f'bucket = {len(generated_df)} files.'
   )


if __name__ == '__main__':
   main()
