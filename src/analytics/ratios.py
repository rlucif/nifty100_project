'''
Financial ratio calculations for the N100 Financial Intelligence Platform: This module contains reusable functions for computing profitability
ratios used throughout the analytics engine.
'''

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Profitability Ratios
# ---------------------------------------------------------------------
def calculate_net_profit_margin(net_profit, sales):
   if sales == 0:
      logger.warning('NPM calculation skipped because sales is zero')
      return None
   return (net_profit / sales) * 100

def calculate_operating_profit_margin(operating_profit, sales, source_opm=None, tolerance=1.0):
   if sales == 0:
      logger.warning('OPM calculation skipped because sales is zero')
      return None
   
   calculated_opm = (operating_profit / sales) * 100
   if source_opm is not None:
      difference = abs(calculated_opm - source_opm)
      if difference > tolerance:
         logger.warning('OPM mismatch detected. ' f'Calculated={calculated_opm:.2f}, ' f'Source={source_opm:.2f}')
   
   return calculated_opm

def calculate_roe(net_profit, equity_capital, reserves):
   total_equity = equity_capital + reserves

   if total_equity <= 0:
      logger.warning('ROE calculation skipped because total equity is less than or equal to zero')
      return None
   
   return (net_profit / total_equity) * 100

def calculate_roce(operating_profit, other_income, equity_capital, reserves, borrowings):
   capital_employed = equity_capital + reserves + borrowings
   if capital_employed <= 0:
      logger.warning('ROCE calculation skipped because capital employed is less than or equal to zero')
      return None
   
   ebit = operating_profit + other_income
   return (ebit / capital_employed) * 100

# ---------------------------------------------------------------------
# Leverage & Efficiency Ratios
# ---------------------------------------------------------------------
def calculate_debt_to_equity(borrowing, equity_capital, reserves):
   if borrowing == 0:
      return 0
   
   total_equity = equity_capital + reserves

   if total_equity <= 0:
      logger.warning('Debt-to-Equity calculation skipped because total equity is less than or equal to zero')
      return None
   
   return borrowing / total_equity

def calculate_high_leverage_flag(debt_to_equity, sector):
   if debt_to_equity is None:
      return False
   if sector is None:
      return False
   if sector.strip().lower() == 'financials':
      return False
   
   return debt_to_equity > 5

def calculate_interest_coverage(operating_profit, other_income, interest):
   if interest == 0:
      logger.warning('Interest Coverage calculation skipped because interest is zero')
      return None
   
   ebit = operating_profit + other_income
   return ebit / interest

def calculate_icr_label(interest_coverage):
   if interest_coverage is None:
      return 'Debt Free'
   
   return None

def calculate_icr_warning_flag(interest_coverage):
   if interest_coverage is None:
      return False
   
   return interest_coverage < 1.5

def calculate_net_debt(borrowings, investments):
   return borrowings - investments

def calculate_asset_turnover(sales, total_assets):
   if total_assets == 0:
      logger.warning('Asset Turnover calculation skipped because total assets is zero')
      return None
   
   return sales / total_assets
