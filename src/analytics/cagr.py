'''
CAGR calculations for the N100 Financial Intelligence Platform.
This module contains reusable functions for computing revenue,
PAT and EPS CAGR values across different time windows.
'''

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# CAGR Engine
# ---------------------------------------------------------------------
def calculate_cagr(start_value, end_value, years):
   if years <= 0:
      logger.warning('CAGR calculation skipped because years is less than or equal to zero')
      return None, None

   if start_value == 0:
      logger.warning('CAGR calculation skipped because start value is zero')
      return None, 'ZERO_BASE'

   if start_value < 0 and end_value < 0:
      logger.warning('CAGR calculation skipped because both values are negative')
      return None, 'BOTH_NEGATIVE'

   if start_value > 0 and end_value < 0:
      logger.warning('CAGR calculation skipped because company declined into loss')
      return None, 'DECLINE_TO_LOSS'

   if start_value < 0 and end_value > 0:
      logger.warning('CAGR calculation skipped because company turned around from loss to profit')
      return None, 'TURNAROUND'

   cagr = ((end_value / start_value) ** (1 / years) - 1) * 100
   return cagr, None

def calculate_revenue_cagr(start_sales, end_sales, years):
   return calculate_cagr(start_sales, end_sales, years)

def calculate_pat_cagr(start_pat, end_pat, years):
   return calculate_cagr(start_pat, end_pat, years)

def calculate_eps_cagr(start_eps, end_eps, years):
   return calculate_cagr(start_eps, end_eps, years)