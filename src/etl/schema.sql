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