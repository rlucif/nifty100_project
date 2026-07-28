'''Shared data access and caching for the N100 API.'''

import sqlite3
from functools import lru_cache
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / 'data' / 'nifty100.db'
OUTPUT_DIR = PROJECT_ROOT / 'output'
REPORTS_DIR = PROJECT_ROOT / 'reports'

API_VERSION = '1.0.0'

# Tables reported by the health endpoint.
CORE_TABLES = [
   'companies',
   'sectors',
   'peer_groups',
   'market_cap',
   'stock_prices',
   'profitandloss',
   'balancesheet',
   'cashflow',
   'financial_ratios',
   'documents'
]


def get_connection():
   '''Open a read-only-style connection to the project database.'''
   connection = sqlite3.connect(DB_PATH, check_same_thread=False)
   connection.row_factory = sqlite3.Row

   return connection


def query(sql, params=()):
   '''Run a SQL query and return the result as a DataFrame.'''
   connection = get_connection()

   try:
      return pd.read_sql(sql, connection, params=params)
   finally:
      connection.close()


def table_row_counts():
   '''Row count for each core table, used by the health endpoint.'''
   connection = get_connection()
   counts = {}

   try:
      cursor = connection.cursor()
      for table in CORE_TABLES:
         try:
            counts[table] = cursor.execute(
               f'SELECT COUNT(*) FROM "{table}"'
            ).fetchone()[0]
         except sqlite3.Error:
            counts[table] = None
   finally:
      connection.close()

   return counts


@lru_cache(maxsize=1)
def cached_universe():
   '''Latest-year universe with composite scores, built once per process.

   The composite score is cross-sectional, so it cannot be computed for a
   single company on demand. Building it per request would put a full
   index recomputation behind every call, so it is cached for the life of
   the process.
   '''
   from src.screener.engine import ScreenerEngine
   from src.screener.universe import build_universe

   connection = get_connection()
   try:
      universe_df = build_universe(connection)
   finally:
      connection.close()

   engine = ScreenerEngine()
   engine.load_config()

   return engine.add_composite_scores(universe_df)


@lru_cache(maxsize=1)
def cached_engine():
   '''Screener engine with its configuration already loaded.'''
   from src.screener.engine import ScreenerEngine

   engine = ScreenerEngine()
   engine.load_config()

   return engine


def read_output_csv(filename):
   '''Load a generated CSV from output/, or an empty frame if absent.'''
   path = OUTPUT_DIR / filename

   if not path.exists():
      return pd.DataFrame()

   return pd.read_csv(path)


def frame_to_records(frame):
   '''Convert a DataFrame to JSON-safe records, NaN becoming null.'''
   if frame.empty:
      return []

   return frame.astype(object).where(pd.notna(frame), None).to_dict(
      orient='records'
   )


def clear_caches():
   '''Drop the cached universe and engine. Used by tests.'''
   cached_universe.cache_clear()
   cached_engine.cache_clear()
