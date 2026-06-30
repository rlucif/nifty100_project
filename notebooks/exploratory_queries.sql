-- =====================================================
-- Query 1
-- List all tables in the SQLite database
-- =====================================================
SELECT name
FROM sqlite_master
WHERE type = 'table'
ORDER BY name;

-- =====================================================
-- Query 2
-- Verify row counts for all tables
-- =====================================================
SELECT 'analysis' AS table_name, COUNT(*) AS row_count FROM analysis
UNION ALL
SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL
SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL
SELECT 'companies', COUNT(*) FROM companies
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'financial_ratios', COUNT(*) FROM financial_ratios
UNION ALL
SELECT 'market_cap', COUNT(*) FROM market_cap
UNION ALL
SELECT 'peer_groups', COUNT(*) FROM peer_groups
UNION ALL
SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL
SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL
SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL
SELECT 'stock_prices', COUNT(*) FROM stock_prices;

-- =====================================================
-- Query 3
-- Company coverage across all datasets
-- =====================================================
SELECT 'analysis' AS table_name, COUNT(DISTINCT company_id) AS companies_covered FROM analysis
UNION ALL
SELECT 'balancesheet', COUNT(DISTINCT company_id) FROM balancesheet
UNION ALL
SELECT 'cashflow', COUNT(DISTINCT company_id) FROM cashflow
UNION ALL
SELECT 'documents', COUNT(DISTINCT company_id) FROM documents
UNION ALL
SELECT 'financial_ratios', COUNT(DISTINCT company_id) FROM financial_ratios
UNION ALL
SELECT 'market_cap', COUNT(DISTINCT company_id) FROM market_cap
UNION ALL
SELECT 'peer_groups', COUNT(DISTINCT company_id) FROM peer_groups
UNION ALL
SELECT 'profitandloss', COUNT(DISTINCT company_id) FROM profitandloss
UNION ALL
SELECT 'prosandcons', COUNT(DISTINCT company_id) FROM prosandcons
UNION ALL
SELECT 'sectors', COUNT(DISTINCT company_id) FROM sectors
UNION ALL
SELECT 'stock_prices', COUNT(DISTINCT company_id) FROM stock_prices;

-- =====================================================
-- Query 4
-- Company IDs present in Profit & Loss but missing
-- from the Companies master table
-- =====================================================
SELECT DISTINCT
   p.company_id
FROM profitandloss p
LEFT JOIN companies c
   ON p.company_id = c.id
WHERE c.id IS NULL
ORDER BY p.company_id;

-- =====================================================
-- Query 5
-- Companies covered in the Analysis dataset
-- =====================================================
SELECT DISTINCT
   c.id,
   c.company_name
FROM companies c
INNER JOIN analysis a
   ON c.id = a.company_id
ORDER BY c.company_name;

-- =====================================================
-- Query 6
-- Check for NULL company_id values
-- =====================================================
SELECT 'analysis' AS table_name, COUNT(*) AS null_company_ids
FROM analysis
WHERE company_id IS NULL
UNION ALL
SELECT 'balancesheet', COUNT(*)
FROM balancesheet
WHERE company_id IS NULL
UNION ALL
SELECT 'cashflow', COUNT(*)
FROM cashflow
WHERE company_id IS NULL
UNION ALL
SELECT 'documents', COUNT(*)
FROM documents
WHERE company_id IS NULL
UNION ALL
SELECT 'profitandloss', COUNT(*)
FROM profitandloss
WHERE company_id IS NULL
UNION ALL
SELECT 'prosandcons', COUNT(*)
FROM prosandcons
WHERE company_id IS NULL;

-- =====================================================
-- Query 7
-- Check for NULL year values
-- =====================================================
SELECT 'balancesheet' AS table_name, COUNT(*) AS null_years
FROM balancesheet
WHERE year IS NULL
UNION ALL
SELECT 'cashflow', COUNT(*)
FROM cashflow
WHERE year IS NULL
UNION ALL
SELECT 'profitandloss', COUNT(*)
FROM profitandloss
WHERE year IS NULL
UNION ALL
SELECT 'financial_ratios', COUNT(*)
FROM financial_ratios
WHERE year IS NULL;

-- =====================================================
-- Query 8
-- Reporting period coverage per company
-- =====================================================
SELECT
   company_id,
   COUNT(DISTINCT year) AS reporting_periods
FROM profitandloss
GROUP BY company_id
ORDER BY reporting_periods DESC, company_id;

-- =====================================================
-- Query 9
-- Earliest and latest annual reporting year per company
-- (excluding TTM reporting periods)
-- =====================================================
SELECT
   company_id,
   MIN(year) AS earliest_year,
   MAX(year) AS latest_annual_year
FROM profitandloss
WHERE year <> 'TTM'
GROUP BY company_id
ORDER BY company_id;

-- =====================================================
-- Query 10
-- Check for duplicate company-year records
-- =====================================================
SELECT
   company_id,
   year,
   COUNT(*) AS record_count
FROM profitandloss
GROUP BY company_id, year
HAVING COUNT(*) > 1
ORDER BY company_id, year;


-- =====================================================
-- Query 11
-- Distribution of records by reporting period
-- =====================================================
SELECT
   year,
   COUNT(*) AS total_records
FROM profitandloss
GROUP BY year
ORDER BY total_records DESC, year;