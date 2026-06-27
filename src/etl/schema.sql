-- =====================================
-- Companies Master Table
-- =====================================
DROP TABLE IF EXISTS companies;

CREATE TABLE companies (
   id TEXT PRIMARY KEY,
   company_logo TEXT,
   company_name TEXT NOT NULL,
   chart_link TEXT,
   about_company TEXT,
   website TEXT,
   nse_profile TEXT,
   bse_profile TEXT,
   face_value REAL,
   book_value REAL,
   roce_percentage REAL,
   roe_percentage REAL
);

-- =====================================
-- Company Analysis Table
-- =====================================
DROP TABLE IF EXISTS analysis;

CREATE TABLE analysis (
   id INTEGER PRIMARY KEY,
   company_id TEXT NOT NULL,
   compounded_sales_growth TEXT,
   compounded_profit_growth TEXT,
   stock_price_cagr TEXT,
   roe TEXT
);

-- =====================================
-- Balance Sheet Table
-- =====================================
DROP TABLE IF EXISTS balancesheet;

CREATE TABLE balancesheet (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    equity_capital REAL,
    reserves INTEGER,
    borrowings INTEGER,
    other_liabilities INTEGER,
    total_liabilities INTEGER,
    fixed_assets INTEGER,
    cwip INTEGER,
    investments INTEGER,
    other_asset INTEGER,
    total_assets INTEGER
);

-- =====================================
-- Cash Flow Table
-- =====================================
DROP TABLE IF EXISTS cashflow;

CREATE TABLE cashflow (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    net_cash_flow REAL
);

-- =====================================
-- Documents Table
-- =====================================
DROP TABLE IF EXISTS documents;

CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    Year INTEGER,
    Annual_Report TEXT
);

-- =====================================
-- Profit and Loss Table
-- =====================================
DROP TABLE IF EXISTS profitandloss;

CREATE TABLE profitandloss (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    sales INTEGER,
    expenses INTEGER,
    operating_profit REAL,
    opm_percentage REAL,
    other_income INTEGER,
    interest INTEGER,
    depreciation INTEGER,
    profit_before_tax INTEGER,
    tax_percentage REAL,
    net_profit INTEGER,
    eps REAL,
    dividend_payout REAL
);

-- =====================================
-- Pros and Cons Table
-- =====================================
DROP TABLE IF EXISTS prosandcons;

CREATE TABLE prosandcons (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    pros TEXT,
    cons TEXT
);

-- =====================================================
-- Financial Ratios
-- =====================================================
CREATE TABLE IF NOT EXISTS financial_ratios (
    id INTEGER PRIMARY KEY,
    company_id TEXT,
    year TEXT,
    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,
    debt_to_equity REAL,
    interest_coverage REAL,
    asset_turnover REAL,
    free_cash_flow_cr REAL,
    capex_cr REAL,
    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    total_debt_cr REAL,
    cash_from_operations_cr REAL
);

-- =====================================================
-- Market Cap
-- =====================================================
CREATE TABLE IF NOT EXISTS market_cap (
    id INTEGER PRIMARY KEY,
    company_id TEXT,
    year INTEGER,
    market_cap_crore REAL,
    enterprise_value_crore REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    ev_ebitda REAL,
    dividend_yield_pct REAL
);

-- =====================================================
-- Peer Groups
-- =====================================================
CREATE TABLE IF NOT EXISTS peer_groups (
    id INTEGER PRIMARY KEY,
    peer_group_name TEXT,
    company_id TEXT,
    is_benchmark TEXT
);

-- =====================================================
-- Sectors
-- =====================================================
CREATE TABLE IF NOT EXISTS sectors (
    id INTEGER PRIMARY KEY,
    company_id TEXT,
    broad_sector TEXT,
    sub_sector TEXT,
    index_weight_pct REAL,
    market_cap_category TEXT
);

-- =====================================================
-- Stock Prices
-- =====================================================
CREATE TABLE IF NOT EXISTS stock_prices (
    id INTEGER PRIMARY KEY,
    company_id TEXT,
    date TEXT,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    adjusted_close REAL
);