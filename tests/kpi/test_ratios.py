import pytest
from src.analytics.ratios import (
   calculate_net_profit_margin,
   calculate_operating_profit_margin,
   calculate_roe,
   calculate_roce,
   calculate_debt_to_equity,
   calculate_high_leverage_flag,
   calculate_interest_coverage,
   calculate_icr_label,
   calculate_icr_warning_flag,
   calculate_net_debt,
   calculate_asset_turnover,
   calculate_free_cash_flow,
   calculate_fcf_concern_flag,
   calculate_capital_allocation,
   calculate_cfo_quality_score,
   calculate_average_cfo_quality_score,
   get_cfo_quality_label,
   calculate_capex_intensity,
   get_capex_intensity_label,
   calculate_fcf_conversion,
   get_fcf_conversion_label
)


@pytest.mark.parametrize(
'net_profit, sales, expected',[
      (20, 100, 20.0),
      (-10, 100, -10.0),
      (50, 0, None),
   ]
)
def test_calculate_net_profit_margin(net_profit, sales, expected):
   assert calculate_net_profit_margin(net_profit, sales) == expected


@pytest.mark.parametrize(
   'operating_profit, sales, source_opm, expected',[
      (25, 100, 25.0, 25.0),
      (30, 120, 25.0, 25.0),
      (50, 0, None, None),
   ]
)
def test_calculate_operating_profit_margin(operating_profit, sales, source_opm, expected):
   assert calculate_operating_profit_margin(
      operating_profit,
      sales,
      source_opm
   ) == expected


@pytest.mark.parametrize(
   'net_profit, equity_capital, reserves, expected',[
      (20, 50, 50, 20.0),
      (10, -20, 10, None),
      (10, 0, 0, None),
   ]
)
def test_calculate_roe(net_profit, equity_capital, reserves, expected):
   assert calculate_roe(
      net_profit,
      equity_capital,
      reserves
   ) == expected


@pytest.mark.parametrize(
   'operating_profit, other_income, equity_capital, reserves, borrowings, expected',[
      (80, 20, 50, 30, 20, 100.0),
      (60, 4, 20, 20, 24, 100.0),
      (10, 2, 0, 0, 0, None),
   ]
)
def test_calculate_roce(
   operating_profit,
   other_income,
   equity_capital,
   reserves,
   borrowings,
   expected
):
   assert calculate_roce(
      operating_profit,
      other_income,
      equity_capital,
      reserves,
      borrowings
   ) == expected


@pytest.mark.parametrize(
   'borrowings, equity_capital, reserves, expected',[
      (100, 50, 50, 1.0),
      (0, 50, 50, 0),
      (100, -50, 0, None),
   ]
)
def test_calculate_debt_to_equity(
   borrowings,
   equity_capital,
   reserves,
   expected
):
   assert calculate_debt_to_equity(
      borrowings,
      equity_capital,
      reserves
   ) == expected


@pytest.mark.parametrize(
   'debt_to_equity, sector, expected',[
      (6.2, 'Industrials', True),
      (6.2, 'Financials', False),
      (2.5, 'Industrials', False),
      (None, 'Industrials', False),
   ]
)
def test_calculate_high_leverage_flag(
   debt_to_equity,
   sector,
   expected
):
   assert calculate_high_leverage_flag(
      debt_to_equity,
      sector
   ) == expected


@pytest.mark.parametrize(
   'operating_profit, other_income, interest, expected',[
      (120, 30, 30, 5.0),
      (100, 0, 20, 5.0),
      (100, 10, 0, None),
   ]
)
def test_calculate_interest_coverage(
   operating_profit,
   other_income,
   interest,
   expected
):
   assert calculate_interest_coverage(
      operating_profit,
      other_income,
      interest
   ) == expected


@pytest.mark.parametrize(
   'interest_coverage, expected',[
      (None, 'Debt Free'),
      (4.8, None),
   ]
)
def test_calculate_icr_label(
   interest_coverage,
   expected
):
   assert calculate_icr_label(
      interest_coverage
   ) == expected


@pytest.mark.parametrize(
   'interest_coverage, expected',[
      (0.8, True),
      (1.4, True),
      (1.5, False),
      (3.2, False),
      (None, False),
   ]
)
def test_calculate_icr_warning_flag(
   interest_coverage,
   expected
):
   assert calculate_icr_warning_flag(
      interest_coverage
   ) == expected


@pytest.mark.parametrize(
   'borrowings, investments, expected',[
      (500, 150, 350),
      (200, 250, -50),
      (0, 100, -100),
   ]
)
def test_calculate_net_debt(
   borrowings,
   investments,
   expected
):
   assert calculate_net_debt(
      borrowings,
      investments
   ) == expected


@pytest.mark.parametrize(
   'sales, total_assets, expected',[
      (1000, 500, 2.0),
      (750, 300, 2.5),
      (1000, 0, None),
   ]
)
def test_calculate_asset_turnover(
   sales,
   total_assets,
   expected
):
   assert calculate_asset_turnover(
      sales,
      total_assets
   ) == expected

   # ---------------------------------------------------------------------
# Free Cash Flow
# ---------------------------------------------------------------------
def test_calculate_free_cash_flow_positive():
   assert calculate_free_cash_flow(100, -40) == 60


def test_calculate_free_cash_flow_negative():
   assert calculate_free_cash_flow(100, -150) == -50


def test_calculate_free_cash_flow_zero():
   assert calculate_free_cash_flow(120, 0) == 120


# ---------------------------------------------------------------------
# FCF Concern Flag
# ---------------------------------------------------------------------
def test_fcf_concern_true():
   assert calculate_fcf_concern_flag([-10, -20, -30]) is True


def test_fcf_concern_false():
   assert calculate_fcf_concern_flag([10, -20, -30]) is False


def test_fcf_concern_less_than_three_years():
   assert calculate_fcf_concern_flag([-10, -20]) is False


def test_fcf_concern_last_three_negative():
   assert calculate_fcf_concern_flag([50, -10, -20, -30]) is True


# -------------------------------------------------------
# CFO Quality Score
# -------------------------------------------------------
def test_calculate_cfo_quality_score():
   assert calculate_cfo_quality_score(1200, 1000) == 1.2


def test_calculate_cfo_quality_score_zero_profit():
   assert calculate_cfo_quality_score(500, 0) is None

# -------------------------------------------------------
# CapEx Intensity
# -------------------------------------------------------
def test_calculate_capex_intensity():
   assert calculate_capex_intensity(-250, 5000) == 5.0

def test_calculate_capex_intensity_zero_sales():
   assert calculate_capex_intensity(-250, 0) is None

# -------------------------------------------------------
# FCF Conversion
# -------------------------------------------------------
def test_calculate_fcf_conversion():
   assert calculate_fcf_conversion(600, 1000) == 60.0

def test_calculate_fcf_conversion_zero_operating_profit():
   assert calculate_fcf_conversion(600, 0) is None

def test_calculate_average_cfo_quality_score():
   scores = [1.2, 1.1, 1.0, 0.9, 0.8]

   assert calculate_average_cfo_quality_score(scores) == 1.0


def test_get_cfo_quality_label():
   assert get_cfo_quality_label(1.2) == 'High Quality Earnings'
   assert get_cfo_quality_label(0.8) == 'Moderate'
   assert get_cfo_quality_label(0.4) == 'Accrual Risk'
   assert get_cfo_quality_label(None) is None

def test_get_capex_intensity_label():
   assert get_capex_intensity_label(2.5) == 'Asset Light'
   assert get_capex_intensity_label(5.0) == 'Moderate'
   assert get_capex_intensity_label(12.0) == 'Capital Intensive'
   assert get_capex_intensity_label(None) is None

def test_get_fcf_conversion_label():
   assert get_fcf_conversion_label(75) == 'Efficient'
   assert get_fcf_conversion_label(45) == 'Moderate'
   assert get_fcf_conversion_label(20) == 'CapEx Heavy'
   assert get_fcf_conversion_label(None) is None

def test_calculate_capital_allocation():
   assert calculate_capital_allocation(100, -50, -20) == 'Reinvestor'
   assert (
      calculate_capital_allocation(100, -50, -20, 1.2)
      == 'Shareholder Returns'
   )
   assert (
      calculate_capital_allocation(100, 50, -20)
      == 'Liquidating Assets'
   )
   assert (
      calculate_capital_allocation(-100, 50, 20)
      == 'Distress Signal'
   )
   assert (
      calculate_capital_allocation(-100, -50, 20)
      == 'Growth Funded by Debt'
   )
   assert (
      calculate_capital_allocation(100, 50, 20)
      == 'Cash Accumulator'
   )
   assert (
      calculate_capital_allocation(-100, -50, -20)
      == 'Pre-Revenue'
   )
   assert (
      calculate_capital_allocation(100, -50, 20)
      == 'Mixed'
   )
   assert (
      calculate_capital_allocation(-100, 50, -20)
      == 'Unknown Pattern'
   )