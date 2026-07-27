import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.analytics.peer import load_peer_groups  # noqa: E402
from src.screener.engine import ScreenerEngine  # noqa: E402
from src.screener.universe import build_universe  # noqa: E402

DB_PATH = 'data/nifty100.db'
OUTPUT_DIR = 'reports/radar_charts'

# Axis label mapped to the universe column that feeds it.
RADAR_AXES = {
   'ROE': 'return_on_equity_pct',
   'ROCE': 'return_on_capital_employed_pct',
   'NPM': 'net_profit_margin_pct',
   'D/E\n(inverted)': 'debt_to_equity',
   'FCF': 'free_cash_flow_cr',
   'PAT CAGR 5y': 'pat_cagr_5yr',
   'Rev CAGR 5y': 'revenue_cagr_5yr',
   'Composite': 'composite_quality_score'
}

# Axes where a lower raw reading is the better outcome.
INVERTED_AXES = {'debt_to_equity'}

COMPANY_COLOUR = '#1F3864'
REFERENCE_COLOUR = '#C00000'


def get_connection():
   return sqlite3.connect(DB_PATH)


def build_scored_universe():
   # Universe with every radar axis normalised onto a 0-100 scale.
   connection = get_connection()

   try:
      universe_df = build_universe(connection)
      peer_groups_df = load_peer_groups(connection)
   finally:
      connection.close()

   engine = ScreenerEngine()
   engine.load_config()
   universe_df = engine.add_composite_scores(universe_df)

   score_config = engine.config['composite_score']
   lower_percentile = score_config['winsorise_lower_percentile']
   upper_percentile = score_config['winsorise_upper_percentile']

   for axis_label, column in RADAR_AXES.items():
      universe_df[f'axis::{axis_label}'] = engine._score_series(
         universe_df[column],
         lower_percentile,
         upper_percentile,
         higher_is_better=column not in INVERTED_AXES
      )

   return universe_df, peer_groups_df


def _draw_radar(axis_labels, company_values, reference_values,
                company_id, company_name, reference_label, output_path):
   angles = np.linspace(
      0,
      2 * np.pi,
      len(axis_labels),
      endpoint=False
   ).tolist()

   # Close the polygon.
   angles += angles[:1]
   company_values = list(company_values) + list(company_values[:1])
   reference_values = list(reference_values) + list(reference_values[:1])

   figure, axes = plt.subplots(
      figsize=(7, 7),
      subplot_kw={'projection': 'polar'}
   )

   axes.set_theta_offset(np.pi / 2)
   axes.set_theta_direction(-1)

   axes.plot(
      angles,
      company_values,
      color=COMPANY_COLOUR,
      linewidth=2,
      label=company_id
   )
   axes.fill(angles, company_values, color=COMPANY_COLOUR, alpha=0.25)

   axes.plot(
      angles,
      reference_values,
      color=REFERENCE_COLOUR,
      linewidth=1.8,
      linestyle='--',
      label=reference_label
   )

   axes.set_xticks(angles[:-1])
   axes.set_xticklabels(axis_labels, fontsize=10)

   axes.set_ylim(0, 100)
   axes.set_yticks([20, 40, 60, 80, 100])
   axes.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=8)
   axes.set_rlabel_position(22.5)
   axes.grid(color='#BFBFBF', linewidth=0.6)

   title = company_name if isinstance(company_name, str) else company_id
   axes.set_title(
      f'{title} ({company_id})\nPercentile-normalised, higher is better',
      fontsize=12,
      pad=24
   )

   axes.legend(loc='upper right', bbox_to_anchor=(1.28, 1.12), fontsize=9)

   figure.tight_layout()
   figure.savefig(output_path, dpi=110, bbox_inches='tight')
   plt.close(figure)


def generate_radar_charts(output_dir=OUTPUT_DIR):
   universe_df, peer_groups_df = build_scored_universe()

   axis_labels = list(RADAR_AXES.keys())
   axis_columns = [f'axis::{label}' for label in axis_labels]

   peer_lookup = dict(
      zip(peer_groups_df['company_id'], peer_groups_df['peer_group_name'])
   )
   universe_df['peer_group_name'] = universe_df['company_id'].map(peer_lookup)

   # Reference profiles.
   index_average = universe_df[axis_columns].mean()
   peer_averages = universe_df.groupby('peer_group_name')[
      axis_columns
   ].mean()

   destination = Path(output_dir)
   destination.mkdir(parents=True, exist_ok=True)

   peer_chart_count = 0
   standalone_chart_count = 0

   for _, company in universe_df.iterrows():
      company_id = company['company_id']
      peer_group_name = company['peer_group_name']

      if pd.notna(peer_group_name):
         reference_values = peer_averages.loc[peer_group_name]
         reference_label = f'{peer_group_name} average'
         peer_chart_count += 1
      else:
         reference_values = index_average
         reference_label = 'Nifty 100 average'
         standalone_chart_count += 1

      _draw_radar(
         axis_labels,
         company[axis_columns].values,
         reference_values.values,
         company_id,
         company['company_name'],
         reference_label,
         destination / f'{company_id}_radar.png'
      )

   print(f'Charts with a peer group reference : {peer_chart_count}')
   print(f'Charts with the index reference    : {standalone_chart_count}')
   print(f'Wrote {peer_chart_count + standalone_chart_count} PNGs '
         f'to {destination}')

   return destination


def main():
   generate_radar_charts()


if __name__ == '__main__':
   main()
