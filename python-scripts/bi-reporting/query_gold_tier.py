"""
Gold Tier Analytics Module

This module provides high-level analytics functions for querying gold tier tables
created by the Lab 6 ETL pipeline. It wraps Presto queries in easy-to-use methods
that return pandas DataFrames for analysis and visualization.

Gold Tier Tables:
    - gold_daily_sales: Daily aggregated sales metrics
    - gold_customer_segments: Customer segmentation analysis
    - order_items: Detailed order line items
    - products: Product catalog information

Key Features:
    - Pre-built queries for common analytics
    - Returns pandas DataFrames for easy manipulation
    - Formatted console output with tabulate
    - Automatic connection management
    - Type-safe query execution

Usage:
    from query_gold_tier import GoldTierAnalytics
    
    analytics = GoldTierAnalytics()
    
    # Get daily sales summary
    daily_sales = analytics.get_daily_sales_summary(limit=10)
    
    # Get customer segments
    segments = analytics.get_customer_segments()
    
    # Get top products
    top_products = analytics.get_top_products(limit=20)
    
    # Get sales trends
    trends = analytics.get_sales_trends(days=60)
    
    analytics.close()

Dependencies:
    - presto_connection: For Presto connectivity
    - pandas: For DataFrame manipulation
    - tabulate: For formatted console output

Author: Bob
Created: 2026
"""

import pandas as pd
from presto_connection import PrestoConnection
from tabulate import tabulate


class GoldTierAnalytics:
    """
    Query and analyze gold tier tables from Lab 6 ETL pipeline.
    
    This class provides convenient methods to query pre-aggregated analytics
    tables (gold tier) created by the Lab 6 Spark ETL pipeline. All methods
    return pandas DataFrames for easy analysis and visualization.
    
    Attributes:
        presto (PrestoConnection): Active Presto connection instance
    
    Methods:
        query_to_dataframe: Execute any query and return DataFrame
        get_daily_sales_summary: Query gold_daily_sales table
        get_customer_segments: Query gold_customer_segments table
        get_top_products: Query top-selling products
        get_sales_trends: Query sales trends over time
        close: Close the Presto connection
    """
    
    def __init__(self):
        """
        Initialize connection to Presto.
        
        Creates a PrestoConnection instance and establishes connection
        to watsonx.data. Connection parameters are read from .env file.
        
        Raises:
            ValueError: If required environment variables are missing
            Exception: If connection fails
        """
        self.presto = PrestoConnection()
        self.presto.connect()
    
    def query_to_dataframe(self, query):
        """
        Execute query and return pandas DataFrame.
        
        This is a utility method that executes any SQL query and converts
        the results to a pandas DataFrame for easy manipulation.
        
        Args:
            query (str): SQL query to execute
            
        Returns:
            pandas.DataFrame: Query results as DataFrame with column names
            
        Example:
            >>> query = "SELECT * FROM gold_daily_sales LIMIT 5"
            >>> df = analytics.query_to_dataframe(query)
            >>> print(df.head())
        """
        columns, results = self.presto.execute_query(query)
        df = pd.DataFrame(results, columns=columns)
        return df
    
    def get_daily_sales_summary(self, limit=10):
        """
        Query gold_daily_sales table for daily aggregated metrics.
        
        This table was created in Lab 6 ETL pipeline and contains daily
        aggregated sales metrics including revenue, order counts, and
        customer statistics.
        
        Table Columns:
            - order_date: Date of orders
            - order_year: Year extracted from order_date
            - order_month: Month extracted from order_date
            - total_orders: Count of orders for the day
            - unique_customers: Count of unique customers
            - total_revenue: Sum of all order amounts
            - avg_order_value: Average order amount
            - min_order_value: Minimum order amount
            - max_order_value: Maximum order amount
            - revenue_per_customer: Average revenue per customer
        
        Args:
            limit (int): Number of most recent days to return (default: 10)
            
        Returns:
            pandas.DataFrame: Daily sales summary, sorted by date descending
            
        Example:
            >>> daily_sales = analytics.get_daily_sales_summary(limit=30)
            >>> print(f"Total revenue: ${daily_sales['total_revenue'].sum():,.2f}")
        """
        query = f"""
        SELECT
            order_date,
            order_year,
            order_month,
            total_orders,
            unique_customers,
            total_revenue,
            avg_order_value,
            min_order_value,
            max_order_value,
            revenue_per_customer
        FROM gold_daily_sales
        ORDER BY order_date DESC
        LIMIT {limit}
        """
        
        print("\n" + "="*80)
        print("DAILY SALES SUMMARY")
        print("="*80)
        
        df = self.query_to_dataframe(query)
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
        
        return df
    
    def get_customer_segments(self):
        """
        Query gold_customer_segments table and aggregate by segment.
        
        This method queries the gold_customer_segments table created in Lab 6
        and aggregates metrics by customer segment (e.g., High Value, Medium Value,
        Low Value, New Customer).
        
        Aggregated Metrics:
            - customer_count: Number of customers in segment
            - total_revenue: Sum of lifetime value for segment
            - avg_revenue_per_customer: Average lifetime value per customer
            - revenue_percentage: Percentage of total revenue from segment
        
        Returns:
            pandas.DataFrame: Customer segment analysis, sorted by revenue descending
            
        Example:
            >>> segments = analytics.get_customer_segments()
            >>> high_value = segments[segments['customer_segment'] == 'High Value']
            >>> print(f"High value customers: {high_value['customer_count'].values[0]}")
        
        Note:
            The revenue_percentage is calculated using a window function to show
            each segment's contribution to total revenue.
        """
        query = """
        SELECT
            customer_segment,
            COUNT(*) as customer_count,
            SUM(lifetime_value) as total_revenue,
            AVG(avg_order_value) as avg_revenue_per_customer,
            ROUND(SUM(lifetime_value) * 100.0 / SUM(SUM(lifetime_value)) OVER (), 2) as revenue_percentage
        FROM gold_customer_segments
        GROUP BY customer_segment
        ORDER BY total_revenue DESC
        """
        
        print("\n" + "="*80)
        print("CUSTOMER SEGMENTS")
        print("="*80)
        
        df = self.query_to_dataframe(query)
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
        
        return df
    
    def get_top_products(self, limit=10):
        """
        Query for top-selling products by revenue.
        
        Joins order_items and products tables to calculate product-level
        metrics including order count, quantity sold, and total revenue.
        
        Joined Tables:
            - retail.order_items: Order line items with quantities and prices
            - retail.products: Product catalog with names, categories, brands
        
        Calculated Metrics:
            - order_count: Number of distinct orders containing the product
            - total_quantity_sold: Sum of quantities across all orders
            - total_revenue: Sum of line_total (quantity * unit_price)
            - avg_unit_price: Average unit price across all orders
        
        Args:
            limit (int): Number of top products to return (default: 10)
            
        Returns:
            pandas.DataFrame: Top products sorted by revenue descending
            
        Example:
            >>> top_10 = analytics.get_top_products(limit=10)
            >>> best_seller = top_10.iloc[0]
            >>> print(f"Best seller: {best_seller['product_name']}")
            >>> print(f"Revenue: ${best_seller['total_revenue']:,.2f}")
        """
        query = f"""
        SELECT
            p.product_name,
            p.category,
            p.brand,
            COUNT(DISTINCT oi.order_id) as order_count,
            SUM(oi.quantity) as total_quantity_sold,
            ROUND(SUM(oi.line_total), 2) as total_revenue,
            ROUND(AVG(oi.unit_price), 2) as avg_unit_price
        FROM retail.order_items oi
        JOIN retail.products p ON oi.product_id = p.product_id
        GROUP BY p.product_name, p.category, p.brand
        ORDER BY total_revenue DESC
        LIMIT {limit}
        """
        
        print("\n" + "="*80)
        print(f"TOP {limit} PRODUCTS BY REVENUE")
        print("="*80)
        
        df = self.query_to_dataframe(query)
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
        
        return df
    
    def get_sales_trends(self, days=30):
        """
        Get sales trends over time from gold_daily_sales table.
        
        Retrieves daily sales metrics for the specified number of days,
        useful for trend analysis and time-series visualizations.
        
        Time Range:
            Uses CURRENT_DATE - INTERVAL to get recent data. The interval
            is specified in days parameter.
        
        Returned Columns:
            - order_date: Date of sales
            - order_count: Number of orders (renamed from total_orders)
            - daily_revenue: Total revenue (renamed from total_revenue)
            - avg_order_value: Average order value
        
        Args:
            days (int): Number of days to analyze (default: 30)
            
        Returns:
            pandas.DataFrame: Daily sales trends, sorted by date ascending
            
        Example:
            >>> trends = analytics.get_sales_trends(days=60)
            >>> # Calculate 7-day moving average
            >>> trends['revenue_ma7'] = trends['daily_revenue'].rolling(7).mean()
            >>> print(trends[['order_date', 'daily_revenue', 'revenue_ma7']])
        
        Note:
            Results are ordered by date ascending (oldest first) to facilitate
            time-series analysis and visualization.
        """
        query = f"""
        SELECT
            order_date,
            total_orders as order_count,
            total_revenue as daily_revenue,
            avg_order_value
        FROM gold_daily_sales
        WHERE order_date >= CURRENT_DATE - INTERVAL '{days}' DAY
        ORDER BY order_date
        """
        
        print("\n" + "="*80)
        print(f"SALES TRENDS (Last {days} Days)")
        print("="*80)
        
        df = self.query_to_dataframe(query)
        print(tabulate(df.head(10), headers='keys', tablefmt='psql', showindex=False))
        print(f"... ({len(df)} total days)")
        
        return df
    
    def close(self):
        """
        Close the Presto connection.
        
        Properly closes the underlying Presto connection to free resources.
        Always call this when done with analytics to avoid connection leaks.
        
        Example:
            >>> analytics = GoldTierAnalytics()
            >>> # ... perform analysis ...
            >>> analytics.close()
            ✓ Connection closed
        """
        self.presto.close()


# Example usage and testing
if __name__ == "__main__":
    """
    Test script to demonstrate GoldTierAnalytics usage.
    
    Run this script directly to test gold tier queries:
        python query_gold_tier.py
    
    This will:
        1. Connect to Presto
        2. Query all gold tier tables
        3. Display formatted results
        4. Close connection
    
    Prerequisites:
        - Lab 6 ETL pipeline must be executed
        - Gold tier tables must exist in analytics schema
        - .env file must be configured correctly
    """
    print("Querying Gold Tier Analytics Tables...")
    print("=" * 80)
    
    try:
        # Create analytics instance
        analytics = GoldTierAnalytics()
        
        # Query gold tier tables
        print("\n1. Daily Sales Summary")
        daily_sales = analytics.get_daily_sales_summary(limit=10)
        
        print("\n2. Customer Segments")
        customer_segments = analytics.get_customer_segments()
        
        print("\n3. Top Products")
        top_products = analytics.get_top_products(limit=10)
        
        print("\n4. Sales Trends")
        sales_trends = analytics.get_sales_trends(days=30)
        
        # Clean up
        analytics.close()
        
        print("\n" + "="*80)
        print("✓ Query execution completed successfully!")
        print("="*80)
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\nPlease ensure:")
        print("  1. Lab 6 ETL pipeline has been executed")
        print("  2. Gold tier tables exist in the analytics schema")
        print("  3. Connection configuration is correct")
        print("  4. Virtual environment is activated")
        print("  5. All dependencies are installed")
