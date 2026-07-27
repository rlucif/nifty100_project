'''
Sprint 3 pipeline runner for the N100 Financial Intelligence Platform.

Executes the full screener and peer comparison chain in dependency
order and reports the Sprint 3 exit criteria:

   1. Build the screening universe (latest year per company)
   2. Compute composite quality scores and persist them
   3. Export output/screener_output.xlsx        (D-07)
   4. Compute peer percentiles into SQLite      (Day 18)
   5. Export output/peer_comparison.xlsx        (D-09)
   6. Export reports/radar_charts/              (D-10)

composite_quality_score is written back to financial_ratios for the
latest year of each company only. The score is cross-sectional: it
ranks a company against the rest of the index as it stands today, so
back-filling it onto historical rows would imply a comparison that was
never made.

Run with:
   python -m src.screener.run_screener
'''

import sqlite3

import pandas as pd

from src.analytics.peer import (
   build_peer_percentiles,
   load_peer_groups,
   save_peer_percentiles
)
from src.reports.peer_comparison import export_peer_comparison
from src.reports.radar_charts import generate_radar_charts
from src.screener.engine import ScreenerEngine
from src.screener.export import export_screener_output
from src.screener.universe import build_universe

DB_PATH = 'data/nifty100.db'

MIN_PRESET_RESULTS = 5
MAX_PRESET_RESULTS = 50


def get_connection():
   return sqlite3.connect(DB_PATH)


def save_composite_scores(connection, scored_df):
   # Persist the composite score onto the latest-year financial_ratios row.
   cursor = connection.cursor()

   updates = [
      (
         None if pd.isna(score) else float(score),
         company_id,
         year
      )
      for company_id, year, score in zip(
         scored_df['company_id'],
         scored_df['year'],
         scored_df['composite_quality_score']
      )
   ]

   cursor.executemany(
      'UPDATE financial_ratios SET composite_quality_score = ? '
      'WHERE company_id = ? AND year = ?',
      updates
   )
   connection.commit()

   print(f'Persisted {len(updates)} composite scores to financial_ratios.')


def main():
   connection = get_connection()

   try:
      print('=' * 62)
      print('SPRINT 3 PIPELINE - SCREENER & PEER COMPARISON')
      print('=' * 62)

      print('\n[1/6] Building screening universe')
      universe_df = build_universe(connection)
      print(f'      {len(universe_df)} companies at their latest period')

      print('\n[2/6] Computing composite quality scores')
      engine = ScreenerEngine()
      engine.load_config()
      scored_df = engine.add_composite_scores(universe_df)
      save_composite_scores(connection, scored_df)

      print('\n[3/6] Exporting screener_output.xlsx')
      preset_counts = {}
      for preset_name in engine.preset_names():
         result_df = engine.run_preset(preset_name, scored_df)
         preset_counts[engine.preset_label(preset_name)] = len(result_df)

      export_screener_output(universe_df=universe_df)

      print('\n[4/6] Computing peer percentiles')
      peer_groups_df = load_peer_groups(connection)
      percentiles_df = build_peer_percentiles(scored_df, peer_groups_df)
      save_peer_percentiles(connection, percentiles_df)

      print('\n[5/6] Exporting peer_comparison.xlsx')
      export_peer_comparison()

      print('\n[6/6] Generating radar charts')
      generate_radar_charts()

      print('\n' + '=' * 62)
      print('SPRINT 3 EXIT CRITERIA')
      print('=' * 62)

      for label, count in preset_counts.items():
         within_range = MIN_PRESET_RESULTS <= count <= MAX_PRESET_RESULTS
         status = 'PASS' if within_range else 'REVIEW'
         print(f'  [{status:>6}] {label:<22} {count:>3} companies')

      group_count = percentiles_df['peer_group_name'].nunique()
      print(f'  [{"PASS" if group_count == 11 else "REVIEW":>6}] '
            f'{"Peer groups ranked":<22} {group_count:>3} of 11')

   finally:
      connection.close()


if __name__ == '__main__':
   main()
