import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / 'data' / 'nifty100.db'

CACHE_TTL_SECONDS = 600

SIMULATED_NOTE = (
   'P/E, P/B, EV/EBITDA, dividend yield and market cap are SIMULATED data.'
)


def _query(sql, params=()):
   connection = sqlite3.connect(DB_PATH)

   try:
      return pd.read_sql(sql, connection, params=params)
   finally:
      connection.close()


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def get_companies():
   return _query(
      '''
      SELECT c.id AS company_id,
             c.company_name,
             c.about_company,
             c.website,
             c.nse_profile,
             c.bse_profile,
             c.face_value,
             c.book_value,
             s.broad_sector,
             s.sub_sector,
             s.market_cap_category,
             s.index_weight_pct
      FROM companies c
      LEFT JOIN sectors s ON s.company_id = c.id
      ORDER BY c.company_name
      '''
   )


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def get_ratios(ticker=None, year=None):
   sql = 'SELECT * FROM financial_ratios'
   clauses = []
   params = []

   if ticker:
      clauses.append('company_id = ?')
      params.append(ticker)

   if year:
      clauses.append('year = ?')
      params.append(year)

   if clauses:
      sql += ' WHERE ' + ' AND '.join(clauses)

   return _query(sql, tuple(params))


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def get_pl(ticker):
   return _query(
      'SELECT * FROM profitandloss WHERE company_id = ?',
      (ticker,)
   )


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def get_bs(ticker):
   return _query(
      'SELECT * FROM balancesheet WHERE company_id = ?',
      (ticker,)
   )


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def get_cf(ticker):
   return _query(
      'SELECT * FROM cashflow WHERE company_id = ?',
      (ticker,)
   )


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def get_sectors():
   return _query('SELECT * FROM sectors')


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def get_peers(group_name=None):
   if group_name:
      return _query(
         'SELECT * FROM peer_groups WHERE peer_group_name = ?',
         (group_name,)
      )

   return _query('SELECT * FROM peer_groups')


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def get_peer_percentiles(group_name=None):
   if group_name:
      return _query(
         'SELECT * FROM peer_percentiles WHERE peer_group_name = ?',
         (group_name,)
      )

   return _query('SELECT * FROM peer_percentiles')


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def get_valuation(ticker=None):
   if ticker:
      return _query(
         'SELECT * FROM market_cap WHERE company_id = ? ORDER BY year',
         (ticker,)
      )

   return _query('SELECT * FROM market_cap ORDER BY company_id, year')


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def get_documents(ticker):
   return _query(
      'SELECT * FROM documents WHERE company_id = ?',
      (ticker,)
   )


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def get_pros_and_cons(ticker):
   return _query(
      'SELECT * FROM prosandcons WHERE company_id = ?',
      (ticker,)
   )


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def get_universe():
   from src.screener.engine import ScreenerEngine
   from src.screener.universe import build_universe

   connection = sqlite3.connect(DB_PATH)

   try:
      universe_df = build_universe(connection)
   finally:
      connection.close()

   engine = ScreenerEngine()
   engine.load_config()

   return engine.add_composite_scores(universe_df)


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def get_valuation_summary():
   from src.analytics.valuation import build_valuation_summary
   connection = sqlite3.connect(DB_PATH)

   try:
      return build_valuation_summary(connection)
   finally:
      connection.close()


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def get_capital_allocation():
   path = PROJECT_ROOT / 'output' / 'capital_allocation.csv'

   if not path.exists():
      return pd.DataFrame(
         columns=[
            'company_id', 'year', 'cfo_sign',
            'cfi_sign', 'cff_sign', 'pattern_label'
         ]
      )

   return pd.read_csv(path)


def database_is_available():
   return DB_PATH.exists()
