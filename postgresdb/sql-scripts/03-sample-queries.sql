-- ============================================================================
-- PostgreSQL Sample Queries for watsonx.data Labs
-- ============================================================================
-- Simplified version - Example queries for customers table
-- ============================================================================

-- Set search path to use the retail schema
SET search_path TO retail, public;

\echo '============================================================================'
\echo 'PostgreSQL Sample Queries - Customer Analytics'
\echo '============================================================================'

-- ============================================================================
-- SECTION 1: Basic Queries
-- ============================================================================

\echo ''
\echo '--- SECTION 1: Basic Queries ---'
\echo ''

-- Query 1.1: Count all customers
\echo 'Query 1.1: Total customer count'
SELECT COUNT(*) as total_customers FROM customers;

-- Query 1.2: List all customers from a specific country
\echo ''
\echo 'Query 1.2: Customers from USA'
SELECT customer_id, name, email, city, loyalty_tier, total_purchases
FROM customers
WHERE country = 'USA'
ORDER BY total_purchases DESC;

-- Query 1.3: Customers with high purchases
\echo ''
\echo 'Query 1.3: High-value customers (purchases > $15,000)'
SELECT customer_id, name, country, total_purchases, loyalty_tier
FROM customers
WHERE total_purchases > 15000
ORDER BY total_purchases DESC;

-- ============================================================================
-- SECTION 2: Aggregation Queries
-- ============================================================================

\echo ''
\echo '--- SECTION 2: Aggregation Queries ---'
\echo ''

-- Query 2.1: Customers by country
\echo 'Query 2.1: Customer count and average purchases by country'
SELECT 
    country,
    COUNT(*) as customer_count,
    ROUND(AVG(total_purchases)::numeric, 2) as avg_purchases,
    ROUND(SUM(total_purchases)::numeric, 2) as total_purchases
FROM customers
GROUP BY country
ORDER BY total_purchases DESC;

-- Query 2.2: Customers by loyalty tier
\echo ''
\echo 'Query 2.2: Customer distribution by loyalty tier'
SELECT 
    loyalty_tier,
    COUNT(*) as customer_count,
    ROUND(AVG(total_purchases)::numeric, 2) as avg_purchases,
    ROUND(MIN(total_purchases)::numeric, 2) as min_purchases,
    ROUND(MAX(total_purchases)::numeric, 2) as max_purchases,
    ROUND(SUM(total_purchases)::numeric, 2) as total_value
FROM customers
GROUP BY loyalty_tier
ORDER BY 
    CASE loyalty_tier
        WHEN 'Platinum' THEN 1
        WHEN 'Gold' THEN 2
        WHEN 'Silver' THEN 3
        WHEN 'Bronze' THEN 4
    END;

-- Query 2.3: Monthly registration trend
\echo ''
\echo 'Query 2.3: Customer registrations by month'
SELECT 
    TO_CHAR(registration_date, 'YYYY-MM') as month,
    COUNT(*) as new_customers,
    ROUND(AVG(total_purchases)::numeric, 2) as avg_purchases
FROM customers
GROUP BY TO_CHAR(registration_date, 'YYYY-MM')
ORDER BY month;

-- ============================================================================
-- SECTION 3: Advanced Analytics
-- ============================================================================

\echo ''
\echo '--- SECTION 3: Advanced Analytics ---'
\echo ''

-- Query 3.1: Customer segmentation by purchase behavior
\echo 'Query 3.1: Customer segmentation by purchase value'
SELECT 
    CASE 
        WHEN total_purchases >= 20000 THEN 'High Value'
        WHEN total_purchases >= 10000 THEN 'Medium Value'
        ELSE 'Low Value'
    END as customer_segment,
    COUNT(*) as customer_count,
    ROUND(AVG(total_purchases)::numeric, 2) as avg_purchases,
    ROUND(MIN(total_purchases)::numeric, 2) as min_purchases,
    ROUND(MAX(total_purchases)::numeric, 2) as max_purchases,
    ROUND((COUNT(*)::numeric / (SELECT COUNT(*) FROM customers)::numeric * 100), 2) as percentage
FROM customers
GROUP BY customer_segment
ORDER BY avg_purchases DESC;

-- Query 3.2: Top customers by country
\echo ''
\echo 'Query 3.2: Top customer in each country'
WITH ranked_customers AS (
    SELECT 
        customer_id,
        name,
        country,
        total_purchases,
        loyalty_tier,
        RANK() OVER (PARTITION BY country ORDER BY total_purchases DESC) as rank
    FROM customers
)
SELECT 
    customer_id,
    name,
    country,
    total_purchases,
    loyalty_tier
FROM ranked_customers
WHERE rank = 1
ORDER BY total_purchases DESC;

-- Query 3.3: Loyalty tier upgrade candidates
\echo ''
\echo 'Query 3.3: Customers close to next loyalty tier'
SELECT 
    customer_id,
    name,
    country,
    loyalty_tier as current_tier,
    total_purchases,
    CASE loyalty_tier
        WHEN 'Bronze' THEN 'Silver'
        WHEN 'Silver' THEN 'Gold'
        WHEN 'Gold' THEN 'Platinum'
        ELSE 'Max Tier'
    END as next_tier,
    CASE loyalty_tier
        WHEN 'Bronze' THEN 10000 - total_purchases
        WHEN 'Silver' THEN 15000 - total_purchases
        WHEN 'Gold' THEN 20000 - total_purchases
        ELSE 0
    END as amount_needed
FROM customers
WHERE 
    (loyalty_tier = 'Bronze' AND total_purchases > 8000) OR
    (loyalty_tier = 'Silver' AND total_purchases > 12000) OR
    (loyalty_tier = 'Gold' AND total_purchases > 18000)
ORDER BY amount_needed;

-- ============================================================================
-- SECTION 4: Window Functions
-- ============================================================================

\echo ''
\echo '--- SECTION 4: Window Functions ---'
\echo ''

-- Query 4.1: Customer ranking by total purchases
\echo 'Query 4.1: Top 10 customers ranked by total purchases'
SELECT 
    customer_id,
    name,
    country,
    loyalty_tier,
    total_purchases,
    RANK() OVER (ORDER BY total_purchases DESC) as purchase_rank,
    DENSE_RANK() OVER (ORDER BY total_purchases DESC) as dense_rank,
    ROW_NUMBER() OVER (ORDER BY total_purchases DESC) as row_num
FROM customers
ORDER BY total_purchases DESC
LIMIT 10;

-- Query 4.2: Running total of purchases by registration date
\echo ''
\echo 'Query 4.2: Running total of customer value by registration date'
SELECT 
    registration_date,
    COUNT(*) as daily_registrations,
    ROUND(SUM(total_purchases)::numeric, 2) as daily_value,
    ROUND(SUM(SUM(total_purchases)) OVER (ORDER BY registration_date)::numeric, 2) as running_total,
    ROUND(AVG(SUM(total_purchases)) OVER (ORDER BY registration_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)::numeric, 2) as moving_avg_3day
FROM customers
GROUP BY registration_date
ORDER BY registration_date;

-- Query 4.3: Percentile analysis
\echo ''
\echo 'Query 4.3: Customer purchase percentiles'
SELECT 
    customer_id,
    name,
    country,
    total_purchases,
    loyalty_tier,
    ROUND(PERCENT_RANK() OVER (ORDER BY total_purchases)::numeric * 100, 2) as percentile_rank,
    NTILE(4) OVER (ORDER BY total_purchases) as quartile
FROM customers
ORDER BY total_purchases DESC
LIMIT 15;

-- ============================================================================
-- SECTION 5: Statistical Analysis
-- ============================================================================

\echo ''
\echo '--- SECTION 5: Statistical Analysis ---'
\echo ''

-- Query 5.1: Overall statistics
\echo 'Query 5.1: Overall customer purchase statistics'
SELECT 
    COUNT(*) as total_customers,
    ROUND(AVG(total_purchases)::numeric, 2) as avg_purchases,
    ROUND(STDDEV(total_purchases)::numeric, 2) as std_deviation,
    ROUND(MIN(total_purchases)::numeric, 2) as min_purchases,
    ROUND(MAX(total_purchases)::numeric, 2) as max_purchases,
    ROUND(SUM(total_purchases)::numeric, 2) as total_value,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_purchases)::numeric, 2) as median_purchases
FROM customers;

-- Query 5.2: Statistics by loyalty tier
\echo ''
\echo 'Query 5.2: Purchase statistics by loyalty tier'
SELECT 
    loyalty_tier,
    COUNT(*) as customer_count,
    ROUND(AVG(total_purchases)::numeric, 2) as avg_purchases,
    ROUND(STDDEV(total_purchases)::numeric, 2) as std_deviation,
    ROUND(MIN(total_purchases)::numeric, 2) as min_purchases,
    ROUND(MAX(total_purchases)::numeric, 2) as max_purchases,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_purchases)::numeric, 2) as median_purchases
FROM customers
GROUP BY loyalty_tier
ORDER BY 
    CASE loyalty_tier
        WHEN 'Platinum' THEN 1
        WHEN 'Gold' THEN 2
        WHEN 'Silver' THEN 3
        WHEN 'Bronze' THEN 4
    END;

-- ============================================================================
-- SECTION 6: Search and Filter Examples
-- ============================================================================

\echo ''
\echo '--- SECTION 6: Search and Filter Examples ---'
\echo ''

-- Query 6.1: Search by name pattern
\echo 'Query 6.1: Customers with names starting with "M"'
SELECT customer_id, name, country, total_purchases, loyalty_tier
FROM customers
WHERE name LIKE 'M%'
ORDER BY name;

-- Query 6.2: Search by email domain
\echo ''
\echo 'Query 6.2: Customers by email domain'
SELECT 
    SUBSTRING(email FROM '@(.*)$') as email_domain,
    COUNT(*) as customer_count
FROM customers
GROUP BY email_domain
ORDER BY customer_count DESC;

-- Query 6.3: Recent registrations
\echo ''
\echo 'Query 6.3: Most recent customer registrations (Last 10)'
SELECT 
    customer_id,
    name,
    country,
    registration_date,
    total_purchases,
    loyalty_tier,
    EXTRACT(DAY FROM CURRENT_DATE - registration_date) as days_since_registration
FROM customers
ORDER BY registration_date DESC
LIMIT 10;

-- ============================================================================
-- SECTION 7: Data Quality Checks
-- ============================================================================

\echo ''
\echo '--- SECTION 7: Data Quality Checks ---'
\echo ''

-- Query 7.1: Check for duplicate emails
\echo 'Query 7.1: Check for duplicate emails'
SELECT 
    email,
    COUNT(*) as count
FROM customers
GROUP BY email
HAVING COUNT(*) > 1;

-- Query 7.2: Validate loyalty tier assignments
\echo ''
\echo 'Query 7.2: Customers with potentially incorrect loyalty tier'
SELECT 
    customer_id,
    name,
    total_purchases,
    loyalty_tier,
    CASE 
        WHEN total_purchases >= 20000 THEN 'Platinum'
        WHEN total_purchases >= 15000 THEN 'Gold'
        WHEN total_purchases >= 10000 THEN 'Silver'
        ELSE 'Bronze'
    END as expected_tier
FROM customers
WHERE loyalty_tier != CASE 
    WHEN total_purchases >= 20000 THEN 'Platinum'
    WHEN total_purchases >= 15000 THEN 'Gold'
    WHEN total_purchases >= 10000 THEN 'Silver'
    ELSE 'Bronze'
END;

-- Query 7.3: Data completeness check
\echo ''
\echo 'Query 7.3: Data completeness check'
SELECT 
    'Total Records' as metric,
    COUNT(*) as value
FROM customers
UNION ALL
SELECT 
    'Records with Email',
    COUNT(*) 
FROM customers 
WHERE email IS NOT NULL AND email != ''
UNION ALL
SELECT 
    'Records with Country',
    COUNT(*) 
FROM customers 
WHERE country IS NOT NULL AND country != ''
UNION ALL
SELECT 
    'Records with Loyalty Tier',
    COUNT(*) 
FROM customers 
WHERE loyalty_tier IS NOT NULL;

-- ============================================================================
-- End of Sample Queries
-- ============================================================================

\echo ''
\echo '============================================================================'
\echo 'Sample queries completed successfully!'
\echo 'You can modify these queries or create your own based on these examples.'
\echo '============================================================================'
