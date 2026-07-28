# Company data endpoints for the N100 API
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from src.analytics.periods import (
   add_period_columns,
   deduplicate_company_years,
   period_sort_key
)
from src.api.dependencies import (
   REPORTS_DIR,
   cached_universe,
   frame_to_records,
   query,
   read_output_csv
)

router = APIRouter(tags=['companies'])

# Statement tables reachable through /companies/{ticker}/<name>.
STATEMENT_TABLES = {
   'pl': 'profitandloss',
   'bs': 'balancesheet',
   'cashflow': 'cashflow'
}

# Metrics returned by the peer comparison radar.
RADAR_METRICS = [
   'return_on_equity_pct',
   'return_on_capital_employed_pct',
   'net_profit_margin_pct',
   'debt_to_equity',
   'free_cash_flow_cr',
   'pat_cagr_5yr',
   'revenue_cagr_5yr',
   'asset_turnover'
]


def _normalise_ticker(ticker):
   return str(ticker).strip().upper()


def _company_or_404(ticker):
   ticker = _normalise_ticker(ticker)
   companies = query(
      'SELECT * FROM companies WHERE UPPER(id) = ?', (ticker,)
   )

   if companies.empty:
      raise HTTPException(
         status_code=404,
         detail=f'Ticker {ticker} not found'
      )

   return ticker, companies.iloc[0]


def _year_bounds(from_year, to_year):
   def to_key(value):
      if not value:
         return None

      parts = str(value).split('-')
      if len(parts) != 2 or not all(part.isdigit() for part in parts):
         raise HTTPException(
            status_code=400,
            detail=f'Invalid year format: {value}. Expected YYYY-MM.'
         )

      return int(parts[0]) * 100 + int(parts[1])

   return to_key(from_year), to_key(to_year)


def _filter_history(frame, from_year, to_year):
   lower, upper = _year_bounds(from_year, to_year)
   working = add_period_columns(deduplicate_company_years(frame))
   working = working[working['period_sort_key'] > 0]

   if lower is not None:
      working = working[working['period_sort_key'] >= lower]
   if upper is not None:
      working = working[working['period_sort_key'] <= upper]

   return working.sort_values('period_sort_key').drop(
      columns=['period_sort_key', 'fiscal_year'], errors='ignore'
   )


@router.get('/companies')
def list_companies(
   sector: str | None = Query(None, description='Filter by broad sector'),
   market_cap_category: str | None = Query(None),
   search: str | None = Query(None, description='Partial name or ticker')
):
   '''List all companies, optionally filtered by sector, cap or search.'''
   companies = query(
      '''
      SELECT c.id AS company_id,
             c.company_name,
             s.broad_sector,
             s.sub_sector,
             s.market_cap_category,
             c.roe_percentage AS roe_pct,
             c.roce_percentage AS roce_pct
      FROM companies c
      LEFT JOIN sectors s ON s.company_id = c.id
      ORDER BY c.company_name
      '''
   )

   if sector:
      companies = companies[
         companies['broad_sector'].str.lower() == sector.strip().lower()
      ]

   if market_cap_category:
      companies = companies[
         companies['market_cap_category'].str.lower()
         == market_cap_category.strip().lower()
      ]

   if search:
      needle = search.strip().lower()
      companies = companies[
         companies['company_name'].str.lower().str.contains(needle, na=False)
         | companies['company_id'].str.lower().str.contains(needle, na=False)
      ]

   return {
      'count': len(companies),
      'companies': frame_to_records(companies)
   }


@router.get('/companies/{ticker}')
def get_company(ticker: str):
   '''Full company profile: master record, latest KPIs and sector data.'''
   ticker, company = _company_or_404(ticker)

   sectors = query(
      'SELECT * FROM sectors WHERE company_id = ?', (ticker,)
   )
   universe = cached_universe()
   latest = universe[universe['company_id'] == ticker]

   return {
      'company': frame_to_records(company.to_frame().T)[0],
      'sector': frame_to_records(sectors)[0] if not sectors.empty else None,
      'latest_kpis': (
         frame_to_records(latest)[0] if not latest.empty else None
      )
   }


@router.get('/companies/{ticker}/pl')
def get_profit_and_loss(
   ticker: str,
   from_year: str | None = Query(None, description='YYYY-MM'),
   to_year: str | None = Query(None, description='YYYY-MM')
):
   '''Profit and loss history, optionally bounded by period.'''
   ticker, _company = _company_or_404(ticker)
   frame = query(
      'SELECT * FROM profitandloss WHERE company_id = ?', (ticker,)
   )
   history = _filter_history(frame, from_year, to_year)

   return {
      'company_id': ticker,
      'count': len(history),
      'history': frame_to_records(history)
   }


@router.get('/companies/{ticker}/bs')
def get_balance_sheet(
   ticker: str,
   from_year: str | None = Query(None, description='YYYY-MM'),
   to_year: str | None = Query(None, description='YYYY-MM')
):
   '''Balance sheet history, optionally bounded by period.'''
   ticker, _company = _company_or_404(ticker)
   frame = query(
      'SELECT * FROM balancesheet WHERE company_id = ?', (ticker,)
   )
   history = _filter_history(frame, from_year, to_year)

   return {
      'company_id': ticker,
      'count': len(history),
      'history': frame_to_records(history)
   }


@router.get('/companies/{ticker}/cashflow')
def get_cash_flow(
   ticker: str,
   from_year: str | None = Query(None, description='YYYY-MM'),
   to_year: str | None = Query(None, description='YYYY-MM')
):
   '''Cash flow history, optionally bounded by period.'''
   ticker, _company = _company_or_404(ticker)
   frame = query(
      'SELECT * FROM cashflow WHERE company_id = ?', (ticker,)
   )
   history = _filter_history(frame, from_year, to_year)

   return {
      'company_id': ticker,
      'count': len(history),
      'history': frame_to_records(history)
   }


@router.get('/companies/{ticker}/ratios')
def get_ratios(
   ticker: str,
   year: str | None = Query(None, description='Exact period, e.g. Mar 2024')
):
   '''Computed KPIs per year, or a single year when year is supplied.'''
   ticker, _company = _company_or_404(ticker)

   frame = deduplicate_company_years(
      query(
         'SELECT * FROM financial_ratios WHERE company_id = ?', (ticker,)
      )
   )

   if year:
      frame = frame[frame['year'] == year]
      if frame.empty:
         raise HTTPException(
            status_code=404,
            detail=f'No ratios for {ticker} in period {year}'
         )

   frame = frame.assign(
      _sort=frame['year'].map(period_sort_key)
   ).sort_values('_sort').drop(columns=['_sort'])

   return {
      'company_id': ticker,
      'count': len(frame),
      'ratios': frame_to_records(frame)
   }


@router.get('/companies/{ticker}/tearsheet')
def get_tearsheet(ticker: str):
   '''Download the pre-generated tearsheet PDF.'''
   ticker, _company = _company_or_404(ticker)
   path = REPORTS_DIR / 'tearsheets' / f'{ticker}_tearsheet.pdf'

   if not path.exists():
      skipped = read_output_csv('skipped_tearsheets.csv')
      reason = 'not generated'

      if not skipped.empty and ticker in set(skipped['company_id']):
         reason = str(
            skipped.loc[
               skipped['company_id'] == ticker, 'reason'
            ].iloc[0]
         )

      raise HTTPException(
         status_code=404,
         detail=f'No tearsheet for {ticker}: {reason}'
      )

   return FileResponse(
      path,
      media_type='application/pdf',
      filename=path.name
   )


@router.get('/companies/{ticker}/peers/compare')
def compare_with_peers(ticker: str):
   '''Radar data: 8 metrics for the company, its peer average and benchmark.'''
   ticker, _company = _company_or_404(ticker)

   membership = query(
      'SELECT * FROM peer_groups WHERE company_id = ?', (ticker,)
   )

   if membership.empty:
      return {
         'company_id': ticker,
         'peer_group': None,
         'message': 'No peer group assigned',
         'metrics': []
      }

   group_name = membership.iloc[0]['peer_group_name']
   members = query(
      'SELECT * FROM peer_groups WHERE peer_group_name = ?', (group_name,)
   )

   universe = cached_universe()
   group = universe[universe['company_id'].isin(members['company_id'])]
   company_row = universe[universe['company_id'] == ticker]

   benchmark_flag = pd.to_numeric(members['is_benchmark'], errors='coerce')
   benchmark_rows = members[benchmark_flag == 1]
   benchmark_id = (
      benchmark_rows['company_id'].iloc[0]
      if not benchmark_rows.empty else None
   )
   benchmark_row = universe[universe['company_id'] == benchmark_id]

   def value_of(frame, metric):
      if frame.empty:
         return None

      value = frame.iloc[0][metric]

      return None if pd.isna(value) else round(float(value), 4)

   metrics = []
   for metric in RADAR_METRICS:
      peer_values = pd.to_numeric(group[metric], errors='coerce').dropna()

      metrics.append({
         'metric': metric,
         'company_value': value_of(company_row, metric),
         'peer_group_average': (
            round(float(peer_values.mean()), 4)
            if not peer_values.empty else None
         ),
         'benchmark_value': value_of(benchmark_row, metric)
      })

   return {
      'company_id': ticker,
      'peer_group': group_name,
      'peer_count': len(group),
      'benchmark_company': benchmark_id,
      'metrics': metrics
   }


@router.get('/companies/{ticker}/documents')
def get_documents(ticker: str):
   '''Annual report links with a validity flag for each URL.'''
   ticker, _company = _company_or_404(ticker)

   documents = query(
      'SELECT * FROM documents WHERE company_id = ?', (ticker,)
   )

   records = []
   for row in documents.itertuples():
      url = getattr(row, 'Annual_Report', None)
      is_valid = (
         isinstance(url, str)
         and url.strip().lower().startswith(('http://', 'https://'))
      )

      records.append({
         'company_id': ticker,
         'year': str(getattr(row, 'Year', '')),
         'annual_report_url': url if is_valid else None,
         'is_url_valid': is_valid
      })

   records.sort(key=lambda item: item['year'], reverse=True)

   return {
      'company_id': ticker,
      'count': len(records),
      'documents': records
   }
