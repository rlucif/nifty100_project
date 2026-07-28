'''Sector endpoints for the N100 API.'''

import pandas as pd
from fastapi import APIRouter, HTTPException
from src.api.dependencies import cached_universe, frame_to_records

router = APIRouter(tags=['sectors'])

UNCLASSIFIED_SECTOR = 'Unclassified'

COMPANY_COLUMNS = [
   'company_id',
   'company_name',
   'sub_sector',
   'year',
   'composite_quality_score',
   'return_on_equity_pct',
   'return_on_capital_employed_pct',
   'net_profit_margin_pct',
   'operating_profit_margin_pct',
   'debt_to_equity',
   'revenue_cagr_5yr',
   'free_cash_flow_cr',
   'pe_ratio'
]


def _sector_frame():
   universe = cached_universe().copy()
   universe['broad_sector'] = universe['broad_sector'].fillna(
      UNCLASSIFIED_SECTOR
   )

   return universe


@router.get('/sectors')
def list_sectors():
   '''Every sector with its company count and median ROE, P/E and D/E.'''
   universe = _sector_frame()

   grouped = universe.groupby('broad_sector').agg(
      company_count=('company_id', 'count'),
      median_roe=('return_on_equity_pct', 'median'),
      median_pe=('pe_ratio', 'median'),
      median_de=('debt_to_equity', 'median'),
      median_composite_score=('composite_quality_score', 'median')
   ).round(3).reset_index().rename(columns={'broad_sector': 'sector'})

   grouped = grouped.sort_values('company_count', ascending=False)

   return {
      'count': len(grouped),
      'sectors': frame_to_records(grouped)
   }


@router.get('/sectors/{sector}/companies')
def get_sector_companies(sector: str):
   '''All companies in a sector with their latest-year KPIs.'''
   universe = _sector_frame()

   available = universe['broad_sector'].dropna().unique()
   matches = [
      name for name in available
      if name.lower() == sector.strip().lower()
   ]

   if not matches:
      raise HTTPException(
         status_code=404,
         detail=(
            f'Unknown sector {sector}. '
            f'Available: {", ".join(sorted(available))}'
         )
      )

   resolved = matches[0]
   companies = universe[universe['broad_sector'] == resolved]

   columns = [
      column for column in COMPANY_COLUMNS if column in companies.columns
   ]
   companies = companies[columns].sort_values(
      'composite_quality_score', ascending=False
   )

   medians = {
      column: (
         None if pd.isna(companies[column].median())
         else round(float(companies[column].median()), 3)
      )
      for column in columns
      if pd.api.types.is_numeric_dtype(companies[column])
   }

   return {
      'sector': resolved,
      'count': len(companies),
      'medians': medians,
      'companies': frame_to_records(companies)
   }
