'''
Portfolio statistics
Three outputs built on the latest year of all 92 companies:
   reports/correlation_heatmap.png  Pearson correlation of 10 KPIs
   output/outlier_report.csv        companies with |Z| > 3 within sector
   output/portfolio_stats.csv       P10 to P90, mean and std per KPI

'''

import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

from src.screener.engine import ScreenerEngine  # noqa: E402
from src.screener.universe import build_universe  # noqa: E402

DB_PATH = 'data/nifty100.db'
HEATMAP_PATH = 'reports/correlation_heatmap.png'
OUTLIER_PATH = 'output/outlier_report.csv'
STATS_PATH = 'output/portfolio_stats.csv'

OUTLIER_Z_THRESHOLD = 3.0
MINIMUM_SECTOR_SIZE = 4
UNCLASSIFIED_SECTOR = 'Unclassified'

KPI_COLUMNS = {
   'return_on_equity_pct': 'ROE %',
   'return_on_capital_employed_pct': 'ROCE %',
   'net_profit_margin_pct': 'NPM %',
   'operating_profit_margin_pct': 'OPM %',
   'debt_to_equity': 'D/E',
   'interest_coverage': 'ICR',
   'asset_turnover': 'Asset turnover',
   'revenue_cagr_5yr': 'Rev CAGR 5y %',
   'pat_cagr_5yr': 'PAT CAGR 5y %',
   'free_cash_flow_cr': 'FCF (Cr)'
}

PERCENTILES = [0.10, 0.25, 0.50, 0.75, 0.90]


def get_connection():
   return sqlite3.connect(DB_PATH)


def load_kpi_frame(connection=None):
   owns_connection = connection is None
   if owns_connection:
      connection = get_connection()

   try:
      universe_df = build_universe(connection)
   finally:
      if owns_connection:
         connection.close()

   engine = ScreenerEngine()
   engine.load_config()
   universe_df = engine.add_composite_scores(universe_df)

   universe_df['broad_sector'] = universe_df['broad_sector'].fillna(
      UNCLASSIFIED_SECTOR
   )

   for column in KPI_COLUMNS:
      universe_df[column] = pd.to_numeric(
         universe_df[column], errors='coerce'
      )

   return universe_df


def build_correlation_heatmap(kpi_df, output_path=HEATMAP_PATH):
   labelled = kpi_df[list(KPI_COLUMNS)].rename(columns=KPI_COLUMNS)
   correlation = labelled.corr(method='pearson')
   rank_correlation = labelled.corr(method='spearman')

   figure, axes = plt.subplots(figsize=(9.5, 8.6))

   sns.heatmap(
      correlation,
      annot=True,
      fmt='.2f',
      cmap='RdBu_r',
      center=0,
      vmin=-1,
      vmax=1,
      square=True,
      linewidths=0.5,
      linecolor='white',
      cbar_kws={'shrink': 0.8, 'label': 'Pearson correlation'},
      annot_kws={'size': 8},
      ax=axes
   )

   axes.set_title(
      'Pearson correlation of 10 KPIs across 92 companies (latest year)',
      fontsize=11,
      pad=14
   )
   axes.tick_params(axis='x', labelsize=8, rotation=45)
   axes.tick_params(axis='y', labelsize=8, rotation=0)

   for label in axes.get_xticklabels():
      label.set_horizontalalignment('right')

   divergence = (correlation - rank_correlation).abs()
   flagged = []
   seen = set()

   for left, right in divergence.stack().sort_values(
      ascending=False
   ).index:
      if left == right or frozenset((left, right)) in seen:
         continue
      seen.add(frozenset((left, right)))
      flagged.append(
         f'{left} vs {right}: '
         f'Pearson {correlation.loc[left, right]:+.2f}, '
         f'Spearman {rank_correlation.loc[left, right]:+.2f}'
      )
      if len(flagged) == 2:
         break

   figure.text(
      0.5, 0.015,
      'Pearson is sensitive to the extreme source values documented in '
      'output/ratio_edge_cases.log.\nWhere rank correlation disagrees, '
      'the coefficient reflects a few companies rather than the index:\n'
      + '   |   '.join(flagged),
      ha='center',
      fontsize=7.5,
      color='#595959'
   )

   destination = Path(output_path)
   destination.parent.mkdir(parents=True, exist_ok=True)
   figure.tight_layout(rect=[0, 0.055, 1, 1])
   figure.savefig(destination, dpi=130)
   plt.close(figure)

   return destination, correlation


def build_outlier_report(kpi_df, output_path=OUTLIER_PATH):
   # Z-score per metric within each broad_sector.
   records = []
   skipped_sectors = []

   for sector, group in kpi_df.groupby('broad_sector'):
      if len(group) < MINIMUM_SECTOR_SIZE:
         skipped_sectors.append((sector, len(group)))
         continue

      for column, label in KPI_COLUMNS.items():
         values = group[column]
         mean = values.mean()
         std = values.std()

         if pd.isna(std) or std == 0:
            continue

         z_scores = (values - mean) / std

         for company_id, company_name, value, z_score in zip(
            group['company_id'], group['company_name'], values, z_scores
         ):
            if pd.isna(z_score) or abs(z_score) <= OUTLIER_Z_THRESHOLD:
               continue

            records.append({
               'company_id': company_id,
               'company_name': company_name,
               'broad_sector': sector,
               'metric': column,
               'metric_label': label,
               'value': round(float(value), 3),
               'sector_mean': round(float(mean), 3),
               'sector_std': round(float(std), 3),
               'z_score': round(float(z_score), 2),
               'direction': 'high' if z_score > 0 else 'low'
            })

   outliers_df = pd.DataFrame(records)
   if not outliers_df.empty:
      outliers_df = outliers_df.reindex(
         outliers_df['z_score'].abs().sort_values(ascending=False).index
      )

   destination = Path(output_path)
   destination.parent.mkdir(parents=True, exist_ok=True)
   outliers_df.to_csv(destination, index=False)

   return destination, outliers_df, skipped_sectors


def build_portfolio_stats(kpi_df, output_path=STATS_PATH):
   rows = []

   for column, label in KPI_COLUMNS.items():
      values = kpi_df[column].dropna()

      if values.empty:
         continue

      quantiles = values.quantile(PERCENTILES)

      rows.append({
         'metric': column,
         'metric_label': label,
         'companies': int(values.count()),
         'P10': round(float(quantiles.loc[0.10]), 3),
         'P25': round(float(quantiles.loc[0.25]), 3),
         'P50': round(float(quantiles.loc[0.50]), 3),
         'P75': round(float(quantiles.loc[0.75]), 3),
         'P90': round(float(quantiles.loc[0.90]), 3),
         'Mean': round(float(values.mean()), 3),
         'Std': round(float(values.std()), 3)
      })

   stats_df = pd.DataFrame(rows)

   destination = Path(output_path)
   destination.parent.mkdir(parents=True, exist_ok=True)
   stats_df.to_csv(destination, index=False)

   return destination, stats_df


def main():
   kpi_df = load_kpi_frame()

   heatmap_path, correlation = build_correlation_heatmap(kpi_df)
   outlier_path, outliers_df, skipped = build_outlier_report(kpi_df)
   stats_path, stats_df = build_portfolio_stats(kpi_df)

   print(f'Wrote {heatmap_path}')
   print(f'Wrote {outlier_path} ({len(outliers_df)} outlier readings)')
   print(f'Wrote {stats_path} ({len(stats_df)} KPIs)')
   print()

   print('Portfolio statistics:')
   print(stats_df[[
      'metric_label', 'companies', 'P10', 'P50', 'P90', 'Mean', 'Std'
   ]].to_string(index=False))
   print()

   if skipped:
      print('Sectors too small for a Z-score '
            f'(under {MINIMUM_SECTOR_SIZE} companies):')
      for sector, size in skipped:
         print(f'  {sector:26} {size}')
      print()

   if not outliers_df.empty:
      print('Strongest outliers:')
      print(outliers_df.head(12)[[
         'company_id', 'broad_sector', 'metric_label', 'value', 'z_score'
      ]].to_string(index=False))
      print()

   strongest = (
      correlation.where(correlation.abs() < 0.999).abs().unstack().dropna()
      .sort_values(ascending=False)
   )
   print('Strongest KPI correlations:')
   seen = set()
   for (left, right), value in strongest.items():
      pair = frozenset((left, right))
      if pair in seen:
         continue
      seen.add(pair)
      signed = correlation.loc[left, right]
      print(f'  {left:16} vs {right:16} {signed:+.2f}')
      if len(seen) >= 5:
         break


if __name__ == '__main__':
   main()
