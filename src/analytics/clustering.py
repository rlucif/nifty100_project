'''
KMeans clustering 

Pipeline
   1. Take the five features at each company's latest financial year.
   2. Impute anything missing with that company's sector median, so a
      missing CAGR does not drag a company toward the origin.
   3. StandardScaler, because the features span percentages, ratios and
      growth rates.
   4. KMeans with k=5 and random_state=42 for reproducibility.
'''

import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.cluster import KMeans  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from src.screener.universe import build_universe  # noqa: E402

DB_PATH = 'data/nifty100.db'
LABELS_PATH = 'output/cluster_labels.csv'
ELBOW_PLOT_PATH = 'reports/elbow_plot.png'
PROFILE_PATH = 'output/cluster_profiles.csv'

CLUSTER_COUNT = 5
RANDOM_STATE = 42
ELBOW_RANGE = range(2, 11)

# Percentiles used to cap features before scaling.
#
# StandardScaler alone is not enough here. The source data carries ROE
# values of 4,744% for BEL and 3,817% for HAL, caused by equity figures
# that are not on the same scale as profit, plus a 229% FCF CAGR for
# CIPLA. Left uncapped, those three companies dominate the scaled space
# and KMeans spends three of its five clusters isolating them: one
# cluster of 1, one of 2, and 58 companies dumped together in a third.
#
# Capping at the 5th and 95th percentile keeps every company in the
# analysis while stopping a handful of data artifacts from deciding the
# geometry. This mirrors the P10/P90 winsorisation the composite quality
# score already applies for the same reason.
WINSORISE_LOWER_PERCENTILE = 5
WINSORISE_UPPER_PERCENTILE = 95

FEATURE_COLUMNS = [
   'return_on_equity_pct',
   'debt_to_equity',
   'revenue_cagr_5yr',
   'fcf_cagr_5yr',
   'operating_profit_margin_pct'
]

UNCLASSIFIED_SECTOR = 'Unclassified'


def get_connection():
   return sqlite3.connect(DB_PATH)


def impute_with_sector_median(frame, columns):
   result = frame.copy()
   result['broad_sector'] = result['broad_sector'].fillna(
      UNCLASSIFIED_SECTOR
   )

   imputed_counts = {}

   for column in columns:
      values = pd.to_numeric(result[column], errors='coerce')
      missing_before = int(values.isna().sum())

      sector_median = values.groupby(result['broad_sector']).transform(
         'median'
      )
      values = values.fillna(sector_median)
      values = values.fillna(values.median())

      result[column] = values
      imputed_counts[column] = missing_before

   return result, imputed_counts


def winsorise(frame, columns):
   result = frame.copy()
   capped_counts = {}

   for column in columns:
      values = pd.to_numeric(result[column], errors='coerce')
      lower = np.percentile(values.dropna(), WINSORISE_LOWER_PERCENTILE)
      upper = np.percentile(values.dropna(), WINSORISE_UPPER_PERCENTILE)

      capped_counts[column] = int(
         ((values < lower) | (values > upper)).sum()
      )
      result[column] = values.clip(lower, upper)

   return result, capped_counts


def build_elbow_plot(scaled_features, output_path=ELBOW_PLOT_PATH):
   # Inertia against k, to show that k=5 sits near the elbow.
   inertias = []

   for k in ELBOW_RANGE:
      model = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
      model.fit(scaled_features)
      inertias.append(model.inertia_)

   figure, axes = plt.subplots(figsize=(7, 4.5))
   axes.plot(
      list(ELBOW_RANGE), inertias,
      marker='o', color='#1F3864', linewidth=2
   )

   chosen_index = list(ELBOW_RANGE).index(CLUSTER_COUNT)
   axes.scatter(
      [CLUSTER_COUNT], [inertias[chosen_index]],
      s=160, facecolors='none', edgecolors='#C00000', linewidths=2,
      label=f'k = {CLUSTER_COUNT} (chosen)'
   )

   axes.set_xlabel('Number of clusters (k)')
   axes.set_ylabel('Inertia (within-cluster sum of squares)')
   axes.set_title('KMeans elbow curve - N100 company archetypes')
   axes.set_xticks(list(ELBOW_RANGE))
   axes.grid(color='#E0E0E0', linewidth=0.6)
   axes.set_axisbelow(True)
   axes.legend(frameon=False)
   for spine in ('top', 'right'):
      axes.spines[spine].set_visible(False)

   destination = Path(output_path)
   destination.parent.mkdir(parents=True, exist_ok=True)
   figure.tight_layout()
   figure.savefig(destination, dpi=130)
   plt.close(figure)

   return destination, dict(zip(ELBOW_RANGE, inertias))


def name_clusters(profile):
   # Names describe what actually separates each cluster, taken in order
   # of how distinctive that feature is.
   # The sprint guide offers five example names. Two of them do not fit
   # what KMeans found in this data, so they are not forced on:
   #
   #   - The most leveraged cluster is entirely banks and NBFCs with a
   #     mean D/E near 7. Calling that "Emerging Growth" would be wrong,
   #     so it is named for its leverage.
   #   - One cluster carries ~80% operating margins with modest ROE. It
   #     is a high-margin group, not a distressed one, so it is named
   #     for its margins.
   #
   # Nothing in this dataset resembles a genuinely distressed cluster:
   # the weakest group still averages 13% ROE.
   overall = {
      column: profile[f'{column}_mean'].mean()
      for column in FEATURE_COLUMNS
   }
   spread = {
      column: profile[f'{column}_mean'].std() or 1.0
      for column in FEATURE_COLUMNS
   }

   def z(cluster, column):
      return (
         profile.loc[cluster, f'{column}_mean'] - overall[column]
      ) / spread[column]

   names = {}
   remaining = list(profile.index)

   # 1. Leverage is the single strongest separator in this universe.
   leverage_cluster = max(
      remaining, key=lambda c: z(c, 'debt_to_equity')
   )
   if z(leverage_cluster, 'debt_to_equity') > 1.0:
      names[leverage_cluster] = 'Leveraged Financials'
      remaining.remove(leverage_cluster)

   # 2. A genuinely weak cluster: poor returns and shrinking cash.
   for cluster in list(remaining):
      if (z(cluster, 'return_on_equity_pct') < -0.8
            and profile.loc[cluster, 'fcf_cagr_5yr_mean'] < 0):
         names[cluster] = 'Distressed or Turnaround'
         remaining.remove(cluster)
         break

   # 3. Highest returns.
   if remaining:
      quality_cluster = max(
         remaining, key=lambda c: z(c, 'return_on_equity_pct')
      )
      names[quality_cluster] = 'High-Quality Compounders'
      remaining.remove(quality_cluster)

   # 4. Highest margins among what is left.
   if remaining:
      margin_cluster = max(
         remaining, key=lambda c: z(c, 'operating_profit_margin_pct')
      )
      names[margin_cluster] = 'High-Margin Franchises'
      remaining.remove(margin_cluster)

   # 5. Of the rest, the faster grower is emerging growth and the slower one is the mature, cash-returning group.
   remaining.sort(
      key=lambda c: profile.loc[c, 'revenue_cagr_5yr_mean'],
      reverse=True
   )

   if remaining:
      names[remaining[0]] = 'Emerging Growth'
   for cluster in remaining[1:]:
      names[cluster] = 'Defensive Dividend Payers'

   return names


def build_cluster_profile(labelled_df):
   # Mean and median of every input feature, per cluster.
   aggregations = {}
   for column in FEATURE_COLUMNS:
      aggregations[f'{column}_mean'] = (column, 'mean')
      aggregations[f'{column}_median'] = (column, 'median')

   profile = labelled_df.groupby('cluster_id').agg(
      companies=('company_id', 'count'),
      **aggregations
   )

   return profile.round(3)


def run_clustering(connection=None):
   owns_connection = connection is None
   if owns_connection:
      connection = get_connection()

   try:
      universe_df = build_universe(connection)
   finally:
      if owns_connection:
         connection.close()

   working = universe_df[
      ['company_id', 'company_name', 'broad_sector'] + FEATURE_COLUMNS
   ].copy()

   working, imputed_counts = impute_with_sector_median(
      working, FEATURE_COLUMNS
   )

   capped, capped_counts = winsorise(working, FEATURE_COLUMNS)
   scaler = StandardScaler()
   scaled_features = scaler.fit_transform(capped[FEATURE_COLUMNS])
   elbow_path, inertias = build_elbow_plot(scaled_features)

   model = KMeans(
      n_clusters=CLUSTER_COUNT,
      random_state=RANDOM_STATE,
      n_init=10
   )
   working['cluster_id'] = model.fit_predict(scaled_features)

   # Euclidean distance from the assigned centroid, in scaled space.
   centroids = model.cluster_centers_
   working['distance_from_centroid'] = [
      round(float(np.linalg.norm(row - centroids[cluster])), 4)
      for row, cluster in zip(scaled_features, working['cluster_id'])
   ]

   # Profile on capped values so the cluster means describe the space KMeans actually partitioned.
   capped['cluster_id'] = working['cluster_id']
   profile = build_cluster_profile(capped)
   names = name_clusters(profile)
   working['cluster_name'] = working['cluster_id'].map(names)
   profile['cluster_name'] = profile.index.map(names)

   return (
      working, profile, elbow_path, inertias,
      imputed_counts, capped_counts
   )


def export_cluster_labels(labelled_df, profile):
   labels_path = Path(LABELS_PATH)
   labels_path.parent.mkdir(parents=True, exist_ok=True)

   labelled_df[[
      'company_id',
      'cluster_id',
      'cluster_name',
      'distance_from_centroid'
   ]].sort_values('company_id').to_csv(labels_path, index=False)

   profile_path = Path(PROFILE_PATH)
   profile.to_csv(profile_path)

   return labels_path, profile_path


def main():
   (
      labelled_df, profile, elbow_path, inertias,
      imputed, capped
   ) = run_clustering()
   labels_path, profile_path = export_cluster_labels(labelled_df, profile)

   print(f'Wrote {labels_path} ({len(labelled_df)} companies)')
   print(f'Wrote {profile_path}')
   print(f'Wrote {elbow_path}')
   print()

   print('Imputed values per feature (filled from sector median):')
   for column, count in imputed.items():
      print(f'  {column:32} {count}')
   print()

   print(f'Values capped at P{WINSORISE_LOWER_PERCENTILE}/'
         f'P{WINSORISE_UPPER_PERCENTILE} before scaling:')
   for column, count in capped.items():
      print(f'  {column:32} {count}')
   print()

   print('Cluster profile:')
   display_columns = ['companies', 'cluster_name'] + [
      f'{column}_mean' for column in FEATURE_COLUMNS
   ]
   print(profile[display_columns].to_string())
   print()

   print('Elbow inertia:')
   for k, inertia in inertias.items():
      marker = '  <- chosen' if k == CLUSTER_COUNT else ''
      print(f'  k={k:2}  {inertia:9.2f}{marker}')

   print()
   print('Example members of each cluster:')
   for cluster_id, group in labelled_df.groupby('cluster_id'):
      closest = group.nsmallest(4, 'distance_from_centroid')
      print(
         f'  {cluster_id} {group["cluster_name"].iloc[0]:28} '
         f'{", ".join(closest["company_id"])}'
      )


if __name__ == '__main__':
   main()
