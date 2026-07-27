'''
Cash flow KPIs for the N100 Financial Intelligence Platform.

Sprint 2 Day 11 deliverable: free cash flow, CFO quality score,
CapEx intensity, FCF conversion and the eight-pattern capital
allocation classifier.

These functions were originally written inside src/analytics/ratios.py.
They live here to match the Sprint 2 deliverable list; ratios.py
re-exports them so existing imports keep working.
'''

import logging

logger = logging.getLogger(__name__)

# Sign combinations of (CFO, CFI, CFF) mapped to their capital
# allocation pattern label.
CAPITAL_ALLOCATION_PATTERNS = {
   (True, False, False): 'Reinvestor',
   (True, True, False): 'Liquidating Assets',
   (False, True, True): 'Distress Signal',
   (False, False, True): 'Growth Funded by Debt',
   (True, True, True): 'Cash Accumulator',
   (False, False, False): 'Pre-Revenue',
   (True, False, True): 'Mixed'
}


# ---------------------------------------------------------------------
# Free Cash Flow
# ---------------------------------------------------------------------
def calculate_free_cash_flow(operating_activity, investing_activity):
   # Negative free cash flow is a valid business outcome, not an error.
   return operating_activity + investing_activity


def calculate_fcf_concern_flag(fcf_values):
   if len(fcf_values) < 3:
      return False

   return all(value < 0 for value in fcf_values[-3:])


# ---------------------------------------------------------------------
# Capital Allocation
# ---------------------------------------------------------------------
def calculate_capital_allocation(
   operating_activity,
   investing_activity,
   financing_activity,
   cfo_quality_score=None):
   signs = (
      operating_activity >= 0,
      investing_activity >= 0,
      financing_activity >= 0
   )

   # A reinvestor with CFO/PAT above 1.0 is returning cash to
   # shareholders rather than funding growth.
   if signs == (True, False, False):
      if cfo_quality_score is not None and cfo_quality_score > 1:
         return 'Shareholder Returns'

      return 'Reinvestor'

   return CAPITAL_ALLOCATION_PATTERNS.get(signs, 'Unknown Pattern')


def get_cash_flow_sign(value):
   # Sign character used by output/capital_allocation.csv.
   if value is None:
      return None

   return '+' if value >= 0 else '-'


# ---------------------------------------------------------------------
# CFO Quality
# ---------------------------------------------------------------------
def calculate_cfo_quality_score(operating_activity, net_profit):
   if net_profit == 0:
      logger.debug(
         'CFO Quality Score calculation skipped because net profit is zero'
      )
      return None

   return round(operating_activity / net_profit, 4)


def calculate_average_cfo_quality_score(cfo_quality_scores):
   valid_scores = [
      score for score in cfo_quality_scores if score is not None
   ]
   if not valid_scores:
      logger.debug(
         'Average CFO Quality Score calculation skipped '
         'because no valid scores are available'
      )
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


# ---------------------------------------------------------------------
# CapEx Intensity
# ---------------------------------------------------------------------
def calculate_capex_intensity(investing_activity, sales):
   if sales == 0:
      logger.debug(
         'CapEx Intensity calculation skipped because sales is zero'
      )
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


# ---------------------------------------------------------------------
# FCF Conversion
# ---------------------------------------------------------------------
def calculate_fcf_conversion(free_cash_flow, operating_profit):
   if operating_profit == 0:
      logger.debug(
         'FCF Conversion calculation skipped because operating profit is zero'
      )
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
