'''Shared fixtures for the N100 API tests.'''

import warnings
from pathlib import Path
import pytest

warnings.filterwarnings('ignore')
DB_PATH = Path('data/nifty100.db')
API_PREFIX = '/api/v1'


@pytest.fixture(scope='session')
def client():
   '''TestClient bound to the FastAPI app.'''
   if not DB_PATH.exists():
      pytest.skip('data/nifty100.db is not present')

   from fastapi.testclient import TestClient

   from src.api.main import app

   with TestClient(app) as test_client:
      yield test_client
