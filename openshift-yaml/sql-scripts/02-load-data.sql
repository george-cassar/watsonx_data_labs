-- ============================================================================
-- PostgreSQL Data Loading Script for watsonx.data Labs
-- ============================================================================
-- Simplified version - Loads sample data into customers table only
-- ============================================================================

-- Set search path to use the retail schema
SET search_path TO retail, public;

-- ============================================================================
-- Load Customers Data
-- ============================================================================

\echo 'Loading customers data...'

INSERT INTO customers (customer_id, name, email, country, city, registration_date, total_purchases, loyalty_tier) VALUES
(1001, 'John Smith', 'john.smith@email.com', 'USA', 'New York', '2023-01-15', 15420.50, 'Gold'),
(1002, 'Maria Garcia', 'maria.garcia@email.com', 'Spain', 'Madrid', '2023-02-20', 8750.25, 'Silver'),
(1003, 'Li Wei', 'li.wei@email.com', 'China', 'Beijing', '2023-01-10', 22340.75, 'Platinum'),
(1004, 'Emma Johnson', 'emma.johnson@email.com', 'UK', 'London', '2023-03-05', 12890.00, 'Gold'),
(1005, 'Ahmed Hassan', 'ahmed.hassan@email.com', 'Egypt', 'Cairo', '2023-02-28', 5420.30, 'Bronze'),
(1006, 'Sophie Martin', 'sophie.martin@email.com', 'France', 'Paris', '2023-01-22', 18750.60, 'Gold'),
(1007, 'Carlos Silva', 'carlos.silva@email.com', 'Brazil', 'São Paulo', '2023-03-12', 9340.80, 'Silver'),
(1008, 'Yuki Tanaka', 'yuki.tanaka@email.com', 'Japan', 'Tokyo', '2023-02-15', 25670.90, 'Platinum'),
(1009, 'Anna Kowalski', 'anna.kowalski@email.com', 'Poland', 'Warsaw', '2023-01-30', 7890.45, 'Silver'),
(1010, 'David Brown', 'david.brown@email.com', 'Australia', 'Sydney', '2023-03-08', 14230.20, 'Gold'),
(1011, 'Fatima Al-Rashid', 'fatima.alrashid@email.com', 'UAE', 'Dubai', '2023-02-05', 31250.75, 'Platinum'),
(1012, 'Hans Mueller', 'hans.mueller@email.com', 'Germany', 'Berlin', '2023-01-18', 11450.30, 'Gold'),
(1013, 'Priya Sharma', 'priya.sharma@email.com', 'India', 'Mumbai', '2023-03-01', 6780.50, 'Bronze'),
(1014, 'Marco Rossi', 'marco.rossi@email.com', 'Italy', 'Rome', '2023-02-22', 13560.40, 'Gold'),
(1015, 'Olga Ivanova', 'olga.ivanova@email.com', 'Russia', 'Moscow', '2023-01-25', 9870.65, 'Silver'),
(1016, 'James Wilson', 'james.wilson@email.com', 'Canada', 'Toronto', '2023-03-15', 16340.85, 'Gold'),
(1017, 'Mei Chen', 'mei.chen@email.com', 'Singapore', 'Singapore', '2023-02-10', 19450.20, 'Gold'),
(1018, 'Lars Andersen', 'lars.andersen@email.com', 'Denmark', 'Copenhagen', '2023-01-28', 8920.75, 'Silver'),
(1019, 'Isabella Santos', 'isabella.santos@email.com', 'Portugal', 'Lisbon', '2023-03-18', 7230.90, 'Silver'),
(1020, 'Kim Min-jun', 'kim.minjun@email.com', 'South Korea', 'Seoul', '2023-02-18', 21890.35, 'Platinum'),
(1021, 'Sarah O''Connor', 'sarah.oconnor@email.com', 'Ireland', 'Dublin', '2023-01-12', 10560.80, 'Silver'),
(1022, 'Mohammed Ali', 'mohammed.ali@email.com', 'Saudi Arabia', 'Riyadh', '2023-03-20', 28340.50, 'Platinum'),
(1023, 'Nina Petrov', 'nina.petrov@email.com', 'Ukraine', 'Kyiv', '2023-02-25', 6450.25, 'Bronze'),
(1024, 'Tom Anderson', 'tom.anderson@email.com', 'Sweden', 'Stockholm', '2023-01-20', 15780.40, 'Gold'),
(1025, 'Lucia Fernandez', 'lucia.fernandez@email.com', 'Mexico', 'Mexico City', '2023-03-10', 11230.60, 'Gold'),
(1026, 'Raj Patel', 'raj.patel@email.com', 'India', 'Delhi', '2023-02-12', 8340.75, 'Silver'),
(1027, 'Elena Popescu', 'elena.popescu@email.com', 'Romania', 'Bucharest', '2023-01-16', 7890.30, 'Silver'),
(1028, 'Michael Lee', 'michael.lee@email.com', 'USA', 'Los Angeles', '2023-03-22', 19670.85, 'Gold'),
(1029, 'Aisha Ibrahim', 'aisha.ibrahim@email.com', 'Nigeria', 'Lagos', '2023-02-08', 5670.40, 'Bronze'),
(1030, 'Pierre Dubois', 'pierre.dubois@email.com', 'France', 'Lyon', '2023-01-24', 13450.95, 'Gold');

\echo 'Loaded 30 customers'

-- ============================================================================
-- Verify Data Loading
-- ============================================================================

\echo ''
\echo '============================================================================'
\echo 'Data Loading Summary'
\echo '============================================================================'

SELECT 'customers' as table_name, COUNT(*) as record_count FROM customers;

\echo ''
\echo '============================================================================'
\echo 'Sample Data Verification'
\echo '============================================================================'

\echo ''
\echo 'Top 10 Customers by Total Purchases:'
SELECT customer_id, name, country, total_purchases, loyalty_tier
FROM customers
ORDER BY total_purchases DESC
LIMIT 10;

\echo ''
\echo 'Customers by Loyalty Tier:'
SELECT 
    loyalty_tier,
    COUNT(*) as customer_count,
    ROUND(AVG(total_purchases)::numeric, 2) as avg_purchases,
    ROUND(MIN(total_purchases)::numeric, 2) as min_purchases,
    ROUND(MAX(total_purchases)::numeric, 2) as max_purchases
FROM customers
GROUP BY loyalty_tier
ORDER BY 
    CASE loyalty_tier
        WHEN 'Platinum' THEN 1
        WHEN 'Gold' THEN 2
        WHEN 'Silver' THEN 3
        WHEN 'Bronze' THEN 4
    END;

\echo ''
\echo 'Customers by Country (Top 10):'
SELECT 
    country,
    COUNT(*) as customer_count,
    ROUND(AVG(total_purchases)::numeric, 2) as avg_purchases
FROM customers
GROUP BY country
ORDER BY customer_count DESC, avg_purchases DESC
LIMIT 10;

\echo ''
\echo '============================================================================'
\echo 'Data loading completed successfully!'
\echo 'Next step: Run 03-sample-queries.sql to test the data with example queries'
\echo '============================================================================'

