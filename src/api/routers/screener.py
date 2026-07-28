'''Screener endpoint for the N100 API.'''

from fastapi import APIRouter, HTTPException, Query

from src.api.dependencies import (
   cached_engine,
   cached_universe,
   frame_to_records
)

router = APIRouter(tags=['screener'])

# Query parameter mapped to (universe column, operator, threshold key).
FILTER_PARAMS = {
   'min_roe': ('return_on_equity_pct', '>=', 'min'),
   'max_de': ('debt_to_equity', '<=', 'max'),
   'min_fcf': ('free_cash_flow_cr', '>=', 'min'),
   'min_rev_cagr_5yr': ('revenue_cagr_5yr', '>=', 'min'),
   'min_pat_cagr_5yr': ('pat_cagr_5yr', '>=', 'min'),
   'max_pe': ('pe_ratio', '<=', 'max')
}

RESULT_COLUMNS = [
   'company_id',
   'company_name',
   'broad_sector',
   'year',
   'composite_quality_score',
   'return_on_equity_pct',
   'return_on_capital_employed_pct',
   'debt_to_equity',
   'free_cash_flow_cr',
   'revenue_cagr_5yr',
   'pat_cagr_5yr',
   'operating_profit_margin_pct',
   'pe_ratio',
   'pb_ratio',
   'dividend_yield_pct',
   'interest_coverage'
]

# Guard rails
PARAM_BOUNDS = {
   'min_roe': (-100.0, 1000.0),
   'max_de': (0.0, 100.0),
   'min_fcf': (-1_000_000.0, 1_000_000.0),
   'min_rev_cagr_5yr': (-100.0, 200.0),
   'min_pat_cagr_5yr': (-100.0, 200.0),
   'max_pe': (0.0, 1000.0)
}


@router.get('/screener')
def run_screener(
   min_roe: float | None = Query(None),
   max_de: float | None = Query(None),
   min_fcf: float | None = Query(None),
   min_rev_cagr_5yr: float | None = Query(None),
   min_pat_cagr_5yr: float | None = Query(None),
   max_pe: float | None = Query(None),
   sector: str | None = Query(None),
   preset: str | None = Query(None, description='Run a named preset'),
   limit: int = Query(200, ge=1, le=500)
):
   '''Screen the universe on any combination of metric thresholds.'''
   supplied = {
      'min_roe': min_roe,
      'max_de': max_de,
      'min_fcf': min_fcf,
      'min_rev_cagr_5yr': min_rev_cagr_5yr,
      'min_pat_cagr_5yr': min_pat_cagr_5yr,
      'max_pe': max_pe
   }

   for name, value in supplied.items():
      if value is None:
         continue

      lower, upper = PARAM_BOUNDS[name]
      if not lower <= value <= upper:
         raise HTTPException(
            status_code=400,
            detail=(
               f'{name}={value} is out of range. '
               f'Expected between {lower} and {upper}.'
            )
         )

   engine = cached_engine()
   universe = cached_universe()

   if preset:
      if preset not in engine.preset_names():
         raise HTTPException(
            status_code=400,
            detail=(
               f'Unknown preset {preset}. '
               f'Available: {", ".join(engine.preset_names())}'
            )
         )
      results = engine.run_preset(preset, universe)
      applied = {'preset': preset}
   else:
      filters = {}
      for name, value in supplied.items():
         if value is None:
            continue

         column, operator, threshold_key = FILTER_PARAMS[name]
         filters[column] = {
            'operator': operator,
            'threshold': {threshold_key: value}
         }

      results = engine.apply_filters(universe, filters)
      applied = {
         name: value for name, value in supplied.items() if value is not None
      }

   if sector:
      results = results[
         results['broad_sector'].str.lower() == sector.strip().lower()
      ]
      applied['sector'] = sector

   results = results.sort_values(
      'composite_quality_score', ascending=False
   )

   available = [
      column for column in RESULT_COLUMNS if column in results.columns
   ]

   return {
      'count': len(results),
      'filters_applied': applied,
      'results': frame_to_records(results[available].head(limit))
   }


@router.get('/screener/presets')
def list_presets():
   '''List the available preset screeners and their labels.'''
   engine = cached_engine()

   return {
      'presets': [
         {
            'name': name,
            'label': engine.preset_label(name),
            'filters': list(
               engine.config['presets'][name].get('filters', {}).keys()
            )
         }
         for name in engine.preset_names()
      ]
   }
