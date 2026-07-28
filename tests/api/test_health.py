'''Health endpoint tests.'''

from src.api.dependencies import CORE_TABLES
from .conftest import API_PREFIX


def test_health_returns_200(client):
   assert client.get(f'{API_PREFIX}/health').status_code == 200


def test_health_status_is_ok(client):
   assert client.get(f'{API_PREFIX}/health').json()['status'] == 'ok'


def test_health_reports_all_ten_tables(client):
   counts = client.get(f'{API_PREFIX}/health').json()['db_row_counts']

   assert len(CORE_TABLES) == 10
   assert set(counts) == set(CORE_TABLES)


def test_health_row_counts_are_populated(client):
   counts = client.get(f'{API_PREFIX}/health').json()['db_row_counts']
   empty = [table for table, count in counts.items() if not count]

   assert empty == [], f'tables reporting no rows: {empty}'


def test_health_reports_uptime_and_version(client):
   payload = client.get(f'{API_PREFIX}/health').json()

   assert payload['uptime_seconds'] >= 0
   assert isinstance(payload['version'], str)


def test_root_endpoint_points_at_the_docs(client):
   payload = client.get('/').json()

   assert payload['docs'] == '/docs'
   assert payload['health'] == f'{API_PREFIX}/health'


def test_response_time_header_is_set(client):
   # The logging middleware also stamps the elapsed time on the response.
   response = client.get(f'{API_PREFIX}/health')

   assert 'X-Response-Time-ms' in response.headers
   assert float(response.headers['X-Response-Time-ms']) >= 0


def test_openapi_schema_is_served(client):
   payload = client.get('/openapi.json').json()

   assert payload['openapi'].startswith('3.')
   assert len(payload['paths']) >= 16
