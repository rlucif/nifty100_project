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

# ---------------------------------------------------------------------
# Cash Flow Ratios
# ---------------------------------------------------------------------
def calculate_free_cash_flow(operating_activity, investing_activity):
   return operating_activity + investing_activity

def calculate_fcf_concern_flag(fcf_values):
   if len(fcf_values) < 3:
      return False
   return all(value < 0 for value in fcf_values[-3:])

def calculate_capital_allocation(
   operating_activity,
   investing_activity,
   financing_activity,
   cfo_quality_score=None):
   cfo_positive = operating_activity >= 0
   cfi_positive = investing_activity >= 0
   cff_positive = financing_activity >= 0

   if cfo_positive and not cfi_positive and not cff_positive:
      if cfo_quality_score is not None and cfo_quality_score > 1:
         return 'Shareholder Returns'
      return 'Reinvestor'
   if cfo_positive and cfi_positive and not cff_positive:
      return 'Liquidating Assets'
   if not cfo_positive and cfi_positive and cff_positive:
      return 'Distress Signal'
   if not cfo_positive and not cfi_positive and cff_positive:
      return 'Growth Funded by Debt'
   if cfo_positive and cfi_positive and cff_positive:
      return 'Cash Accumulator'
   if not cfo_positive and not cfi_positive and not cff_positive:
      return 'Pre-Revenue'
   if cfo_positive and not cfi_positive and cff_positive:
      return 'Mixed'

   return 'Unknown Pattern'

def calculate_cfo_quality_score(operating_activity, net_profit):
   if net_profit == 0:
      logger.warning('CFO Quality Score calculation skipped because net profit is zero')
      return None

   return round(operating_activity / net_profit, 4)

def calculate_average_cfo_quality_score(cfo_quality_scores):
   valid_scores = [score for score in cfo_quality_scores if score is not None]
   if not valid_scores:
      logger.warning('Average CFO Quality Score calculation skipped because no valid scores are available')
      return None

   return round(sum(valid_scores) / len(valid_scores), 4)


def get_cfo_quality_label(cfo_quality_score):
   if cfo_quality_score is None:
      return None
   if cfo_quality_score > 1.0:
      return 'High Quality Earnings'
   if cfo_quality_score < 0.5:
      return 'Accrual Risk'

   return 'Moderate'


def calculate_capex_intensity(investing_activity, sales):
   if sales == 0:
      logger.warning('CapEx Intensity calculation skipped because sales is zero')
      return None

   return round((abs(investing_activity) / sales) * 100, 2)

def get_capex_intensity_label(capex_intensity):
   if capex_intensity is None:
      return None
   if capex_intensity < 3:
      return 'Asset Light'
   if capex_intensity <= 8:
      return 'Moderate'

   return 'Capital Intensive'

def calculate_fcf_conversion(free_cash_flow, operating_profit):
   if operating_profit == 0:
      logger.warning('FCF Conversion calculation skipped because operating profit is zero')
      return None

   return round((free_cash_flow / operating_profit) * 100, 2)

def get_fcf_conversion_label(fcf_conversion):
   if fcf_conversion is None:
      return None
   if fcf_conversion > 60:
      return 'Efficient'
   if fcf_conversion >= 30:
      return 'Moderate'

   return 'CapEx Heavy'