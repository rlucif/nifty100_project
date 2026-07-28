'''Valuation endpoints for the N100 API'''

from fastapi import APIRouter, HTTPException
from src.api.dependencies import frame_to_records, query

router = APIRouter(tags=['valuation'])

SIMULATED_NOTE = (
   'P/E, P/B, EV/EBITDA, dividend yield and market cap come from a '
   'SIMULATED dataset supplied with the project. Illustrative only.'
)


@router.get('/market-cap/{ticker}')
def get_market_cap_history(ticker: str):
   '''Historical valuation multiples for one company, 2019 to 2024.'''
   normalised = str(ticker).strip().upper()

   history = query(
      'SELECT * FROM market_cap WHERE UPPER(company_id) = ? '
      'ORDER BY year',
      (normalised,)
   )

   if history.empty:
      raise HTTPException(
         status_code=404,
         detail=f'No valuation history for ticker {normalised}'
      )

   history = history.drop(columns=['id'], errors='ignore')

   return {
      'company_id': normalised,
      'count': len(history),
      'years': [int(year) for year in history['year']],
      'history': frame_to_records(history),
      'note': SIMULATED_NOTE
   }
