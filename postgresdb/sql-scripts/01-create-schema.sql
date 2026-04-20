-- ============================================================================
-- PostgreSQL Schema Creation Script for watsonx.data Labs
-- ============================================================================
-- Simplified version - Creates one sample table for testing
-- ============================================================================

-- Create schema for organizing tables
CREATE SCHEMA IF NOT EXISTS retail;

-- Set search path to use the retail schema
SET search_path TO retail, public;

-- ============================================================================
-- Table: customers
-- Description: Customer master data with demographic and loyalty information
-- ============================================================================
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    country VARCHAR(50) NOT NULL,
    city VARCHAR(100) NOT NULL,
    registration_date DATE NOT NULL,
    total_purchases DECIMAL(10,2) DEFAULT 0.00,
    loyalty_tier VARCHAR(20) CHECK (loyalty_tier IN ('Bronze', 'Silver', 'Gold', 'Platinum')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for customers table
CREATE INDEX idx_customers_country ON customers(country);
CREATE INDEX idx_customers_loyalty_tier ON customers(loyalty_tier);
CREATE INDEX idx_customers_registration_date ON customers(registration_date);
CREATE INDEX idx_customers_email ON customers(email);

-- Add comments to customers table
COMMENT ON TABLE customers IS 'Customer master data with demographic and loyalty information';
COMMENT ON COLUMN customers.customer_id IS 'Unique customer identifier';
COMMENT ON COLUMN customers.loyalty_tier IS 'Customer loyalty program tier: Bronze, Silver, Gold, or Platinum';

-- ============================================================================
-- Create trigger for automatic timestamp updates
-- ============================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for customers table
CREATE TRIGGER update_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Grant permissions
-- ============================================================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA retail TO PUBLIC;

-- Grant select on table
GRANT SELECT, INSERT, UPDATE, DELETE ON retail.customers TO PUBLIC;

-- ============================================================================
-- Display schema information
-- ============================================================================

-- Show table created
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname = 'retail'
ORDER BY tablename;

-- ============================================================================
-- End of schema creation script
-- ============================================================================

\echo 'Schema creation completed successfully!'
\echo 'Table created: customers'
\echo 'Next step: Run 02-load-data.sql to populate the table with sample data'

