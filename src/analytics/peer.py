'''
Peer percentile engine for the N100 Financial Intelligence Platform.

Sprint 3 Day 18. Computes PERCENT_RANK for 10 metrics within each of the
11 peer groups and populates the peer_percentiles table.

Ranking direction
   Nine of the ten metrics rank higher-is-better. Debt-to-equity is
   inverted (1 - PERCENT_RANK) so that a company carrying less debt
   receives the higher percentile rank.

Companies with no peer group
   36 of the 92 companies are not members of any peer group. Requesting
   their ranks returns the message 'No peer group assigned' rather than
   raising an error.

Run with:
   python -m src.analytics.peer
'''

import sqlite3

import pandas as pd

from src.screener.universe import build_universe

DB_PATH = 'data/nifty100.db'

NO_PEER_GROUP_MESSAGE = 'No peer group assigned'

# The 10 metrics ranked within each peer group.
PEER_METRICS = [
   'return_on_equity_pct',
   'return_on_capital_employed_pct',
   'net_profit_margin_pct',
   'debt_to_equity',
   'free_cash_flow_cr',
   'pat_cagr_5yr',
   'revenue_cagr_5yr',
   'eps_cagr_5yr',
   'interest_coverage',
   'asset_turnover'
]

# Metrics where a lower reading earns the higher percentile rank.
INVERTED_METRICS = {'debt_to_equity'}

CREATE_PEER_PERCENTILES_SQL = '''
CREATE TABLE IF NOT EXISTS peer_percentiles (
    id INTEGER PRIMARY KEY,
    company_id TEXT,
    peer_group_name TEXT,
    metric TEXT,
    value REAL,
    percentile_rank REAL,
    year TEXT
)
'''


def get_connection():
   return sqlite3.connect(DB_PATH)


def load_peer_groups(connection):
   return pd.read_sql(
      'SELECT peer_group_name, company_id, is_benchmark FROM peer_groups',
      connection
   )


def percent_rank(series):
   # SQL PERCENT_RANK: (rank - 1) / (n - 1), expressed on a 0-100 scale.
   #
   # Companies with a missing metric are excluded from the ranking
   # population rather than being ranked last, so a peer group is not
   # penalised for incomplete source data.
   values = pd.to_numeric(series, errors='coerce')
   ranked = values.rank(method='min', na_option='keep')
   population = values.notna().sum()

   if population <= 1:
      # A single ranked company sits at the top of its own distribution.
      return ranked.notna().astype(float) * 100

   return (ranked - 1) / (population - 1) * 100


def build_peer_percentiles(universe_df, peer_groups_df):
   # Long-format percentile table: one row per company-metric.
   member_df = peer_groups_df.merge(
      universe_df,
      on='company_id',
      how='inner'
   )

   records = []

   for peer_group_name, group_df in member_df.groupby('peer_group_name'):
      for metric in PEER_METRICS:
         ranks = percent_rank(group_df[metric])

         if metric in INVERTED_METRICS:
            # Lower debt earns the higher rank. Missing values stay
            # missing because NaN propagates through the subtraction.
            ranks = 100 - ranks

         for company_id, value, rank in zip(
            group_df['company_id'],
            group_df[metric],
            ranks
         ):
            records.append({
               'company_id': company_id,
               'peer_group_name': peer_group_name,
               'metric': metric,
               'value': None if pd.isna(value) else float(value),
               'percentile_rank': None if pd.isna(rank) else round(
                  float(rank), 2
               ),
               'year': group_df.loc[
                  group_df['company_id'] == company_id, 'year'
               ].iloc[0]
            })

   return pd.DataFrame(records)


def get_company_percentiles(percentiles_df, company_id):
   # Percentile ranks for one company, or a message if it has no peers.
   company_rows = percentiles_df[
      percentiles_df['company_id'] == company_id
   ]

   if company_rows.empty:
      return NO_PEER_GROUP_MESSAGE

   return company_rows


def save_peer_percentiles(connection, percentiles_df):
   cursor = connection.cursor()
   cursor.execute(CREATE_PEER_PERCENTILES_SQL)
   cursor.execute('DELETE FROM peer_percentiles')

   percentiles_df.to_sql(
      'peer_percentiles',
      connection,
      if_exists='append',
      index=False
   )

   connection.commit()

   print(f'Saved {len(percentiles_df)} rows to peer_percentiles.')


def main():
   connection = get_connection()

   try:
      universe_df = build_universe(connection)
      peer_groups_df = load_peer_groups(connection)

      percentiles_df = build_peer_percentiles(universe_df, peer_groups_df)
      save_peer_percentiles(connection, percentiles_df)

      ranked_companies = set(percentiles_df['company_id'])
      unassigned = sorted(
         set(universe_df['company_id']) - ranked_companies
      )

      print(f'Peer groups ranked : {percentiles_df["peer_group_name"].nunique()}')
      print(f'Companies ranked   : {len(ranked_companies)}')
      print(f'Companies without a peer group: {len(unassigned)}')

   finally:
      connection.close()


if __name__ == '__main__':
   main()
