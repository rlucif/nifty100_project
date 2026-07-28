'''Health endpoint for the N100 API.'''

import time
from fastapi import APIRouter
from src.api.dependencies import API_VERSION, table_row_counts

router = APIRouter(tags=['health'])

# Process start, used to report uptime.
STARTED_AT = time.time()


@router.get('/health')
def get_health():
   '''Report service status, row counts for all 10 tables and uptime.'''
   return {
      'status': 'ok',
      'version': API_VERSION,
      'uptime_seconds': round(time.time() - STARTED_AT, 3),
      'db_row_counts': table_row_counts()
   }
