'''Company endpoint tests.'''

from .conftest import API_PREFIX
EXPECTED_COMPANY_COUNT = 92


def test_companies_returns_all_records(client):
   payload = client.get(f'{API_PREFIX}/companies').json()

   assert payload['count'] == EXPECTED_COMPANY_COUNT
   assert len(payload['companies']) == EXPECTED_COMPANY_COUNT


def test_companies_can_be_filtered_by_sector(client):
   payload = client.get(
      f'{API_PREFIX}/companies', params={'sector': 'Financials'}
   ).json()

   assert payload['count'] > 0
   assert {row['broad_sector'] for row in payload['companies']} == {
      'Financials'
   }


def test_companies_search_matches_a_ticker(client):
   payload = client.get(
      f'{API_PREFIX}/companies', params={'search': 'TCS'}
   ).json()

   assert 'TCS' in {row['company_id'] for row in payload['companies']}


def test_companies_search_matches_a_partial_name(client):
   payload = client.get(
      f'{API_PREFIX}/companies', params={'search': 'consultancy'}
   ).json()

   assert payload['count'] >= 1


def test_companies_search_with_no_match_returns_empty(client):
   payload = client.get(
      f'{API_PREFIX}/companies', params={'search': 'zzzznotacompany'}
   ).json()

   assert payload['count'] == 0
   assert payload['companies'] == []


def test_single_company_returns_profile_sections(client):
   payload = client.get(f'{API_PREFIX}/companies/TCS').json()

   assert payload['company']['company_name']
   assert payload['sector']['broad_sector'] == 'Information Technology'
   assert payload['latest_kpis']['company_id'] == 'TCS'


def test_unknown_ticker_returns_404(client):
   response = client.get(f'{API_PREFIX}/companies/INVALID')

   assert response.status_code == 404
   assert 'not found' in response.json()['detail'].lower()


def test_ticker_lookup_is_case_insensitive(client):
   assert client.get(f'{API_PREFIX}/companies/tcs').status_code == 200


def test_profit_and_loss_history_is_returned(client):
   payload = client.get(f'{API_PREFIX}/companies/TCS/pl').json()

   assert payload['count'] > 0
   assert 'sales' in payload['history'][0]


def test_profit_and_loss_year_filter_narrows_the_result(client):
   full = client.get(f'{API_PREFIX}/companies/TCS/pl').json()
   filtered = client.get(
      f'{API_PREFIX}/companies/TCS/pl',
      params={'from_year': '2020-03', 'to_year': '2024-03'}
   ).json()

   assert filtered['count'] < full['count']
   assert filtered['count'] > 0


def test_invalid_year_format_returns_400(client):
   response = client.get(
      f'{API_PREFIX}/companies/TCS/pl', params={'from_year': 'March2020'}
   )

   assert response.status_code == 400
   assert 'YYYY-MM' in response.json()['detail']


def test_balance_sheet_history_is_returned(client):
   payload = client.get(f'{API_PREFIX}/companies/TCS/bs').json()

   assert payload['count'] > 0
   assert 'total_assets' in payload['history'][0]


def test_cash_flow_history_is_returned(client):
   payload = client.get(f'{API_PREFIX}/companies/TCS/cashflow').json()

   assert payload['count'] > 0
   assert 'operating_activity' in payload['history'][0]


def test_ratios_cover_at_least_ten_years(client):
   # Acceptance gate AC-12.
   payload = client.get(f'{API_PREFIX}/companies/TCS/ratios').json()

   assert payload['count'] >= 10


def test_ratios_include_the_cagr_columns(client):
   payload = client.get(f'{API_PREFIX}/companies/TCS/ratios').json()

   assert 'revenue_cagr_5yr' in payload['ratios'][0]
   assert 'composite_quality_score' in payload['ratios'][0]


def test_ratios_year_filter_returns_a_single_period(client):
   payload = client.get(
      f'{API_PREFIX}/companies/TCS/ratios', params={'year': 'Mar 2024'}
   ).json()

   assert payload['count'] == 1
   assert payload['ratios'][0]['year'] == 'Mar 2024'


def test_ratios_unknown_year_returns_404(client):
   response = client.get(
      f'{API_PREFIX}/companies/TCS/ratios', params={'year': 'Mar 1990'}
   )

   assert response.status_code == 404


def test_tearsheet_downloads_as_a_pdf(client):
   response = client.get(f'{API_PREFIX}/companies/TCS/tearsheet')

   assert response.status_code == 200
   assert response.headers['content-type'] == 'application/pdf'
   assert response.content.startswith(b'%PDF')


def test_peer_compare_returns_eight_axes(client):
   payload = client.get(
      f'{API_PREFIX}/companies/TCS/peers/compare'
   ).json()

   assert payload['peer_group'] == 'IT Services'
   assert len(payload['metrics']) == 8
   assert payload['benchmark_company'] == 'TCS'


def test_peer_compare_reports_no_group_without_raising(client):
   # 37 companies belong to no peer group; that is a message, not an error.
   response = client.get(f'{API_PREFIX}/companies/ABB/peers/compare')

   assert response.status_code == 200
   assert response.json()['message'] == 'No peer group assigned'


def test_documents_flag_url_validity(client):
   payload = client.get(f'{API_PREFIX}/companies/TCS/documents').json()

   assert payload['count'] > 0
   assert all('is_url_valid' in row for row in payload['documents'])
