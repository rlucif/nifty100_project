'''Sector, peer, valuation and portfolio endpoint tests.'''

import pytest

from .conftest import API_PREFIX

# 10 real broad sectors plus the Unclassified bucket holding the two tickers absent from the truncated company master.
EXPECTED_SECTOR_COUNT = 11
EXPECTED_PEER_GROUPS = 11


def test_sectors_endpoint_returns_every_sector(client):
   payload = client.get(f'{API_PREFIX}/sectors').json()

   assert payload['count'] == EXPECTED_SECTOR_COUNT


def test_sectors_include_the_required_medians(client):
   payload = client.get(f'{API_PREFIX}/sectors').json()
   first = payload['sectors'][0]

   for field in ('company_count', 'median_roe', 'median_pe', 'median_de'):
      assert field in first


def test_sector_company_counts_sum_to_the_universe(client):
   payload = client.get(f'{API_PREFIX}/sectors').json()
   total = sum(row['company_count'] for row in payload['sectors'])

   assert total == 92


def test_sector_companies_returns_only_that_sector(client):
   payload = client.get(
      f'{API_PREFIX}/sectors/Information Technology/companies'
   ).json()

   assert payload['sector'] == 'Information Technology'
   assert payload['count'] > 0
   assert 'TCS' in {row['company_id'] for row in payload['companies']}


def test_sector_lookup_is_case_insensitive(client):
   response = client.get(f'{API_PREFIX}/sectors/financials/companies')

   assert response.status_code == 200
   assert response.json()['sector'] == 'Financials'


def test_unknown_sector_returns_404(client):
   response = client.get(f'{API_PREFIX}/sectors/Blockchain/companies')
   assert response.status_code == 404
   assert 'Unknown sector' in response.json()['detail']


def test_sector_companies_are_ranked_by_score(client):
   payload = client.get(
      f'{API_PREFIX}/sectors/Financials/companies'
   ).json()
   scores = [
      row['composite_quality_score'] for row in payload['companies']
   ]

   assert scores == sorted(scores, reverse=True)


# Peers
def test_peer_groups_endpoint_lists_all_eleven(client):
   # Acceptance gate AC-14.
   payload = client.get(f'{API_PREFIX}/peers').json()

   assert payload['count'] == EXPECTED_PEER_GROUPS


def test_peer_group_returns_ranked_metrics(client):
   payload = client.get(f'{API_PREFIX}/peers/IT Services').json()

   assert payload['peer_group_name'] == 'IT Services'
   assert payload['metrics_ranked'] == 10
   assert payload['benchmark_company'] == 'TCS'


def test_peer_group_marks_its_benchmark(client):
   payload = client.get(f'{API_PREFIX}/peers/IT Services').json()
   flagged = [
      row['company_id'] for row in payload['companies']
      if row['is_benchmark']
   ]

   assert flagged == ['TCS']


def test_highest_roe_in_group_has_the_top_percentile(client):
   payload = client.get(f'{API_PREFIX}/peers/IT Services').json()

   ranked = [
      (
         row['company_id'],
         row['metrics']['return_on_equity_pct']['value'],
         row['metrics']['return_on_equity_pct']['percentile_rank']
      )
      for row in payload['companies']
      if 'return_on_equity_pct' in row['metrics']
   ]
   best = max(ranked, key=lambda item: item[1])

   assert best[2] == 100.0


def test_unknown_peer_group_returns_404(client):
   response = client.get(f'{API_PREFIX}/peers/Not A Group')

   assert response.status_code == 404
   assert 'Unknown peer group' in response.json()['detail']


# Valuation and portfolio
def test_market_cap_history_spans_six_years(client):
   payload = client.get(f'{API_PREFIX}/market-cap/TCS').json()

   assert payload['count'] == 6
   assert payload['years'] == [2019, 2020, 2021, 2022, 2023, 2024]


def test_market_cap_response_declares_simulated_data(client):
   payload = client.get(f'{API_PREFIX}/market-cap/TCS').json()

   assert 'SIMULATED' in payload['note']


def test_market_cap_unknown_ticker_returns_404(client):
   assert client.get(
      f'{API_PREFIX}/market-cap/NOPE'
   ).status_code == 404


def test_portfolio_stats_covers_ten_kpis(client):
   payload = client.get(f'{API_PREFIX}/portfolio/stats').json()

   assert payload['count'] == 10


def test_portfolio_stats_include_every_percentile(client):
   payload = client.get(f'{API_PREFIX}/portfolio/stats').json()
   first = payload['stats'][0]

   for field in ('P10', 'P25', 'P50', 'P75', 'P90', 'Mean', 'Std'):
      assert field in first


def test_percentiles_are_monotonic(client):
   payload = client.get(f'{API_PREFIX}/portfolio/stats').json()

   for row in payload['stats']:
      assert row['P10'] <= row['P25'] <= row['P50'] <= row['P75'] <= row['P90']


def test_clusters_cover_all_companies(client):
   # Acceptance gate AC-15.
   payload = client.get(f'{API_PREFIX}/portfolio/clusters').json()

   if payload['count'] == 0:
      pytest.skip('cluster_labels.csv has not been generated')

   assert payload['count'] == 92
   assert len(payload['clusters']) == 5


def test_every_company_has_a_named_cluster(client):
   payload = client.get(f'{API_PREFIX}/portfolio/clusters').json()

   if payload['count'] == 0:
      pytest.skip('cluster_labels.csv has not been generated')

   assert all(
      row['cluster_name'] for row in payload['assignments']
   )


def test_outliers_endpoint_responds(client):
   payload = client.get(f'{API_PREFIX}/portfolio/outliers').json()

   assert 'count' in payload
