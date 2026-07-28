'''Screener endpoint tests
The key check is that the API and the Sprint 3 batch export agree, since
both are driven by the same ScreenerEngine.
'''

from pathlib import Path
import pandas as pd
import pytest
from .conftest import API_PREFIX

SCREENER_EXPORT = Path('output/screener_output.xlsx')


def test_screener_with_no_filters_returns_the_whole_universe(client):
   payload = client.get(f'{API_PREFIX}/screener').json()

   assert payload['count'] == 92


def test_min_roe_filter_excludes_lower_returns(client):
   payload = client.get(
      f'{API_PREFIX}/screener', params={'min_roe': 15}
   ).json()

   assert payload['count'] > 0
   assert all(
      row['return_on_equity_pct'] >= 15 for row in payload['results']
   )


def test_max_pe_filter_is_respected(client):
   payload = client.get(
      f'{API_PREFIX}/screener', params={'max_pe': 30}
   ).json()

   assert all(
      row['pe_ratio'] is None or row['pe_ratio'] <= 30
      for row in payload['results']
   )


def test_min_fcf_filter_excludes_cash_burners(client):
   payload = client.get(
      f'{API_PREFIX}/screener', params={'min_fcf': 0}
   ).json()

   assert all(
      row['free_cash_flow_cr'] >= 0 for row in payload['results']
   )


def test_financials_are_exempt_from_the_debt_ceiling(client):
   # The business rule carried over from Sprint 3: a D/E ceiling must not reject banks.
   payload = client.get(
      f'{API_PREFIX}/screener', params={'max_de': 1.0}
   ).json()

   sectors = {row['broad_sector'] for row in payload['results']}

   assert 'Financials' in sectors


def test_sector_filter_narrows_the_result(client):
   payload = client.get(
      f'{API_PREFIX}/screener', params={'sector': 'Information Technology'}
   ).json()

   assert payload['count'] > 0
   assert {row['broad_sector'] for row in payload['results']} == {
      'Information Technology'
   }


def test_results_are_ranked_by_composite_score(client):
   payload = client.get(f'{API_PREFIX}/screener').json()
   scores = [row['composite_quality_score'] for row in payload['results']]

   assert scores == sorted(scores, reverse=True)


def test_combined_filters_are_all_applied(client):
   payload = client.get(
      f'{API_PREFIX}/screener',
      params={'min_roe': 15, 'min_fcf': 0}
   ).json()

   for row in payload['results']:
      assert row['return_on_equity_pct'] >= 15
      assert row['free_cash_flow_cr'] >= 0


@pytest.mark.parametrize(
   'params',
   [
      {'min_roe': 99999},
      {'max_de': -5},
      {'max_pe': 99999},
      {'min_rev_cagr_5yr': 5000}
   ]
)
def test_out_of_range_parameters_return_400(client, params):
   response = client.get(f'{API_PREFIX}/screener', params=params)

   assert response.status_code == 400
   assert 'out of range' in response.json()['detail']


def test_unknown_preset_returns_400(client):
   response = client.get(
      f'{API_PREFIX}/screener', params={'preset': 'not_a_preset'}
   )

   assert response.status_code == 400
   assert 'Unknown preset' in response.json()['detail']


def test_presets_endpoint_lists_all_six(client):
   payload = client.get(f'{API_PREFIX}/screener/presets').json()

   assert len(payload['presets']) == 6


def test_limit_parameter_caps_the_result_size(client):
   payload = client.get(
      f'{API_PREFIX}/screener', params={'limit': 5}
   ).json()

   assert len(payload['results']) == 5
   assert payload['count'] == 92


def test_invalid_limit_is_rejected_by_validation(client):
   assert client.get(
      f'{API_PREFIX}/screener', params={'limit': 0}
   ).status_code == 422


@pytest.mark.parametrize(
   'preset, sheet',
   [
      ('quality_compounder', 'Quality Compounder'),
      ('growth_accelerator', 'Growth Accelerator'),
      ('dividend_champion', 'Dividend Champion')
   ]
)
def test_api_preset_matches_the_excel_export(client, preset, sheet):
   # Acceptance gate AC-13: the API and screener_output.xlsx must agree.
   if not SCREENER_EXPORT.exists():
      pytest.skip('output/screener_output.xlsx has not been generated')

   exported = pd.read_excel(SCREENER_EXPORT, sheet_name=sheet)
   payload = client.get(
      f'{API_PREFIX}/screener', params={'preset': preset, 'limit': 500}
   ).json()

   api_tickers = {row['company_id'] for row in payload['results']}
   excel_tickers = set(exported['Ticker'])

   assert api_tickers == excel_tickers
