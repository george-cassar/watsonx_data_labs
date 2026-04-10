"""
Customer Analysis Application
==============================
Analyzes customer purchase patterns and generates summary reports.

This application performs the following operations:
1. Reads customer and order data from Iceberg tables
2. Joins and aggregates data to create customer summaries
3. Identifies top customers by spending
4. Analyzes sales patterns by geographic location (state/country)
5. Writes results to an analytics table for reporting

Best Practices Implemented:
- Global configuration constants for easy maintenance
- Proper error handling and logging with timestamps
- Resource management with DataFrame caching and cleanup
- Performance monitoring with execution timing
- Graceful shutdown with proper Spark session cleanup
- Exit codes for automation (0=success, 1=failure)

Usage:
    Submit via watsonx.data UI or API with accompanying JSON payload
    that defines resource allocation (driver/executor memory, cores, etc.)
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum, avg, max, min, round as spark_round
import traceback
import time
from datetime import datetime

# ============================================================================
# CONFIGURATION - Global Constants
# ============================================================================

# Catalog and Schema Configuration
CATALOG = "lab_catalog01"
SCHEMA_RETAIL = "retail"
SCHEMA_ANALYTICS = "analytics"

# Source Tables
TABLE_CUSTOMERS = "customers"
TABLE_ORDERS = "orders"

# Output Table
OUTPUT_TABLE = "customer_summary_spark"

# Analysis Parameters
TOP_CUSTOMERS_LIMIT = 10
STATE_SUMMARY_LIMIT = 10

def create_spark_session():
    """
    Create and configure Spark session with Iceberg support.
    
    Configuration includes:
    - Iceberg Spark extensions for table format support
    - Hive metastore integration for catalog access
    - Adaptive Query Execution (AQE) for performance optimization
    - Partition coalescing to reduce small files
    
    Note: Resource allocation (driver/executor memory, cores, instances)
          is configured via the JSON payload when submitting the job,
          not in the application code.
    
    Returns:
        SparkSession: Configured Spark session instance
    """
    return (
        SparkSession.builder
        .appName("Customer-Analysis")
        # Enable Iceberg extensions
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        # Enable Hive support for metastore access
        .enableHiveSupport()
        # Performance optimizations
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .getOrCreate()
    )

def setup_logging(spark):
    """
    Configure logging for the application.
    
    Sets up JVM log4j logger for structured logging that integrates
    with Spark's logging infrastructure. Log level is set to WARN
    to reduce noise while maintaining visibility of important events.
    
    Args:
        spark: Active SparkSession instance
        
    Returns:
        Logger: Configured log4j logger instance
    """
    spark.sparkContext.setLogLevel("WARN")
    log4j = spark._jvm.org.apache.log4j
    logger = log4j.LogManager.getLogger("CustomerAnalysis")
    return logger

def log(logger, msg: str, level: str = "INFO"):
    """
    Log message with timestamp to both logger and stdout.
    
    Provides dual output for immediate visibility (stdout) and
    persistent logging (log4j) for troubleshooting and auditing.
    
    Args:
        logger: log4j logger instance
        msg: Message to log
        level: Log level - "INFO", "WARN", or "ERROR" (default: "INFO")
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {msg}"
    
    if level == "INFO":
        logger.info(formatted_msg)
    elif level == "WARN":
        logger.warn(formatted_msg)
    elif level == "ERROR":
        logger.error(formatted_msg)
    
    print(formatted_msg)

def run_customer_analysis(spark, logger):
    """
    Execute the complete customer analysis workflow.
    
    Workflow Steps:
    1. Load customer and order data from Iceberg tables
    2. Join datasets and aggregate metrics per customer
    3. Display top customers by total spending
    4. Analyze sales by geographic location (state/country)
    5. Write results to analytics table for downstream consumption
    
    Performance Optimizations:
    - DataFrame caching for reused datasets
    - Explicit unpersist to free memory
    - Execution timing for performance monitoring
    
    Args:
        spark: Active SparkSession instance
        logger: Configured logger for output
        
    Returns:
        bool: True if analysis completed successfully, False otherwise
    """
    try:
        log(logger, "=" * 80)
        log(logger, "Customer Analysis Application Started")
        log(logger, "=" * 80)
        
        # Step 1: Read customers table
        log(logger, "\n1. Reading customers table...")
        start_time = time.time()
        customers_table = f"{CATALOG}.{SCHEMA_RETAIL}.{TABLE_CUSTOMERS}"
        customers_df = spark.table(customers_table)
        customers_df.cache()
        
        customer_count = customers_df.count()
        log(logger, f"✓ Total customers: {customer_count:,} (loaded in {time.time() - start_time:.2f}s)")
        
        # Step 2: Read orders table
        log(logger, "\n2. Reading orders table...")
        start_time = time.time()
        orders_table = f"{CATALOG}.{SCHEMA_RETAIL}.{TABLE_ORDERS}"
        orders_df = spark.table(orders_table)
        orders_df.cache()
        
        order_count = orders_df.count()
        log(logger, f"✓ Total orders: {order_count:,} (loaded in {time.time() - start_time:.2f}s)")
        
        # Step 3: Perform customer analysis
        log(logger, "\n3. Analyzing customer purchase patterns...")
        start_time = time.time()
        
        # Join customers with orders and aggregate metrics
        customer_summary = customers_df.join(
            orders_df,
            customers_df.customer_id == orders_df.customer_id,
            "left"
        ).groupBy(
            customers_df.customer_id,
            customers_df.first_name,
            customers_df.last_name,
            customers_df.state,
            customers_df.country
        ).agg(
            count(orders_df.order_id).alias("order_count"),
            sum(orders_df.total_amount).alias("total_spent"),
            avg(orders_df.total_amount).alias("avg_order_value"),
            max(orders_df.order_date).alias("last_order_date")
        )
        
        customer_summary.cache()
        summary_count = customer_summary.count()
        log(logger, f"✓ Analysis complete: {summary_count:,} customer records (processed in {time.time() - start_time:.2f}s)")
        
        # Step 4: Identify top customers by spending
        log(logger, f"\n4. Top {TOP_CUSTOMERS_LIMIT} customers by total spent:")
        top_customers = customer_summary.orderBy(col("total_spent").desc()) \
            .select("customer_id", "first_name", "last_name", "order_count",
                    spark_round("total_spent", 2).alias("total_spent")) \
            .limit(TOP_CUSTOMERS_LIMIT)
        top_customers.show(truncate=False)
        
        # Step 5: Analyze sales by geographic location
        log(logger, "\n5. Sales by state:")
        state_summary = customer_summary.groupBy("state", "country") \
            .agg(
                count("customer_id").alias("customer_count"),
                sum("total_spent").alias("total_revenue"),
                avg("avg_order_value").alias("avg_order_value")
            ) \
            .orderBy(col("total_revenue").desc())
        
        state_summary.show(STATE_SUMMARY_LIMIT, truncate=False)
        
        # Step 6: Write results to analytics table
        log(logger, "\n6. Writing results to analytics table...")
        start_time = time.time()
        
        output_table = f"{CATALOG}.{SCHEMA_ANALYTICS}.{OUTPUT_TABLE}"
        customer_summary.write \
            .format("iceberg") \
            .mode("overwrite") \
            .saveAsTable(output_table)
        
        log(logger, f"✓ Results saved to {output_table} (written in {time.time() - start_time:.2f}s)")
        
        # Step 7: Cleanup cached DataFrames to free memory
        customers_df.unpersist()
        orders_df.unpersist()
        customer_summary.unpersist()
        
        log(logger, "\n" + "=" * 80)
        log(logger, "✓ Customer Analysis completed successfully!")
        log(logger, "=" * 80)
        
        return True
        
    except Exception as e:
        log(logger, "\n" + "=" * 80, "ERROR")
        log(logger, "ERROR: Customer analysis failed", "ERROR")
        log(logger, "=" * 80, "ERROR")
        log(logger, f"Error: {str(e)}", "ERROR")
        log(logger, traceback.format_exc(), "ERROR")
        return False

def main():
    """
    Main execution function with proper resource management.
    
    Handles:
    - Spark session initialization
    - Logger configuration
    - Application execution
    - Error handling and reporting
    - Resource cleanup (Spark session stop)
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    spark = None
    logger = None
    
    try:
        print("Initializing Spark session...")
        spark = create_spark_session()
        
        logger = setup_logging(spark)
        log(logger, "Spark session initialized successfully")
        log(logger, f"Spark Version: {spark.version}")
        log(logger, f"Application ID: {spark.sparkContext.applicationId}")
        
        success = run_customer_analysis(spark, logger)
        
        return 0 if success else 1
        
    except Exception as e:
        if logger:
            log(logger, f"Fatal error: {str(e)}", "ERROR")
            log(logger, traceback.format_exc(), "ERROR")
        else:
            print(f"Fatal error: {str(e)}")
            print(traceback.format_exc())
        return 1
        
    finally:
        if spark:
            if logger:
                log(logger, "\nStopping Spark session...")
            spark.stop()
            if logger:
                log(logger, "✓ Spark session stopped")

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)