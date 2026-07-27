'''
Peer percentile engine unit tests.

Verifies the PERCENT_RANK definition, the debt-to-equity inversion and
the no-peer-group contract required by Sprint 3 Day 18.
'''

import pandas as pd
import pytest

from src.analytics.peer import (
   NO_PEER_GROUP_MESSAGE,
   PEER_METRICS,
   build_peer_percentiles,
   get_company_percentiles,
   percent_rank
)


@pytest.fixture
def sample_universe():
   return pd.DataFrame({
      'company_id': ['TCS', 'INFY', 'HCLTECH', 'WIPRO'],
      'year': ['Mar 2024'] * 4,
      'return_on_equity_pct': [50.0, 30.0, 23.0, 14.0],
      'return_on_capital_employed_pct': [60.0, 38.0, 29.0, 17.0],
      'net_profit_margin_pct': [19.0, 17.0, 14.0, 12.0],
      'debt_to_equity': [0.09, 0.10, 0.05, 0.20],
      'free_cash_flow_cr': [4000.0, 3000.0, 2000.0, 1000.0],
      'pat_cagr_5yr': [10.0, 9.0, 8.0, 4.0],
      'revenue_cagr_5yr': [8.0, 12.0, 11.0, 5.0],
      'eps_cagr_5yr': [11.0, 10.0, 9.0, 3.0],
      'interest_coverage': [40.0, 30.0, 25.0, 15.0],
      'asset_turnover': [1.2, 1.1, 1.0, 0.9]
   })


@pytest.fixture
def sample_peer_groups():
   return pd.DataFrame({
      'peer_group_name': ['IT Services'] * 4,
      'company_id': ['TCS', 'INFY', 'HCLTECH', 'WIPRO'],
      'is_benchmark': ['1', '0', '0', '0']
   })


def test_percent_rank_spans_zero_to_one_hundred():
   ranks = percent_rank(pd.Series([10.0, 20.0, 30.0, 40.0]))

   assert ranks.min() == 0
   assert ranks.max() == 100


def test_percent_rank_uses_the_sql_definition():
   # (rank - 1) / (n - 1) on a 0-100 scale.
   ranks = percent_rank(pd.Series([10.0, 20.0, 30.0]))

   assert list(ranks) == [0.0, 50.0, 100.0]


def test_percent_rank_excludes_missing_values():
   ranks = percent_rank(pd.Series([10.0, None, 30.0]))

   assert pd.isna(ranks.iloc[1])
   assert ranks.iloc[0] == 0
   assert ranks.iloc[2] == 100


def test_percent_rank_handles_a_single_company():
   ranks = percent_rank(pd.Series([42.0]))

   assert ranks.iloc[0] == 100


def test_highest_roe_gets_the_highest_percentile(
   sample_universe,
   sample_peer_groups
):
   # Sprint 3 Day 21 spot-check.
   percentiles = build_peer_percentiles(sample_universe, sample_peer_groups)
   roe = percentiles[percentiles['metric'] == 'return_on_equity_pct']
   best = roe.loc[roe['value'].idxmax()]

   assert best['company_id'] == 'TCS'
   assert best['percentile_rank'] == 100.0


def test_lowest_debt_gets_the_highest_percentile(
   sample_universe,
   sample_peer_groups
):
   # D/E is inverted: less debt is the better outcome.
   percentiles = build_peer_percentiles(sample_universe, sample_peer_groups)
   debt = percentiles[percentiles['metric'] == 'debt_to_equity']
   best = debt.loc[debt['value'].idxmin()]

   assert best['company_id'] == 'HCLTECH'
   assert best['percentile_rank'] == 100.0


def test_all_ten_metrics_are_ranked(sample_universe, sample_peer_groups):
   percentiles = build_peer_percentiles(sample_universe, sample_peer_groups)

   assert len(PEER_METRICS) == 10
   assert set(percentiles['metric']) == set(PEER_METRICS)


def test_company_without_a_peer_group_returns_a_message(
   sample_universe,
   sample_peer_groups
):
   # Must return a message rather than raising.
   percentiles = build_peer_percentiles(sample_universe, sample_peer_groups)
   result = get_company_percentiles(percentiles, 'NOTLISTED')

   assert result == NO_PEER_GROUP_MESSAGE


def test_company_with_a_peer_group_returns_rows(
   sample_universe,
   sample_peer_groups
):
   percentiles = build_peer_percentiles(sample_universe, sample_peer_groups)
   result = get_company_percentiles(percentiles, 'TCS')

   assert isinstance(result, pd.DataFrame)
   assert len(result) == len(PEER_METRICS)
