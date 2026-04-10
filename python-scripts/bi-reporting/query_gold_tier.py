"""
Gold Tier Analytics Module
Query and analyze gold tier tables from Lab 6 ETL pipeline
"""

import pandas as pd
from presto_connection import PrestoConnection
from tabulate import tabulate


class GoldTierAnalytics:
    """
    Query and analyze gold tier tables from Lab 6
    """
    
    def __init__(self):
        """Initialize connection to Presto"""
        self.presto = PrestoConnection()
        self.presto.connect()
    
    def query_to_dataframe(self, query):
        """
        Execute query and return pandas DataFrame
        
        Args:
            query (str): SQL query to execute
            
        Returns:
            pandas.DataFrame: Query results as DataFrame
        """
        columns, results = self.presto.execute_query(query)
        df = pd.DataFrame(results, columns=columns)
        return df
    
    def get_daily_sales_summary(self, limit=10):
        """
        Query gold_daily_sales table
        This table was created in Lab 6 ETL pipeline
        
        Args:
            limit (int): Number of days to return
            
        Returns:
            pandas.DataFrame: Daily sales summary
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
        Query gold_customer_segments table
        This table was created in Lab 6 ETL pipeline
        
        Returns:
            pandas.DataFrame: Customer segment analysis with aggregated metrics
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
        Query for top-selling products
        
        Args:
            limit (int): Number of products to return
            
        Returns:
            pandas.DataFrame: Top products by revenue
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
        Get sales trends over time from gold_daily_sales table
        
        Args:
            days (int): Number of days to analyze
            
        Returns:
            pandas.DataFrame: Daily sales trends
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
        """Close connection"""
        self.presto.close()


# Example usage
if __name__ == "__main__":
    print("Querying Gold Tier Analytics Tables...")
    print("=" * 80)
    
    try:
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

# Made with Bob
