"""
Medallion ETL Pipeline: Bronze -> Silver -> Gold
=================================================

Implements a multi-layer data processing pipeline following the Medallion architecture
for retail data processing with watsonx.data and Apache Iceberg.

Architecture Layers:
    - Bronze: Raw data ingestion with metadata tracking
    - Silver: Cleaned, validated, and enriched data
    - Gold: Business-level aggregates and analytics

Features:
    - Multi-layer data processing (Bronze/Silver/Gold)
    - Data quality validation and cleansing
    - Partitioned Iceberg tables for performance
    - Comprehensive error handling and logging
    - Performance monitoring and metrics
    - Automatic resource cleanup

Usage:
    Submit via watsonx.data UI or API with accompanying JSON payload
    that defines resource allocation (driver/executor memory, cores, etc.)

Requirements:
    - PySpark with Iceberg support
    - Access to watsonx.data catalog
    - Source table: lab_catalog01.retail.orders

Output Tables:
    - lab_catalog01.analytics.silver_orders
    - lab_catalog01.analytics.gold_daily_sales
    - lab_catalog01.analytics.gold_customer_segments

"""

from typing import Optional, Tuple
import traceback
import time
from datetime import datetime

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, when, lit, current_timestamp,
    year, month, dayofmonth,
    sum as spark_sum, count, avg, max as spark_max, min as spark_min,
    round as spark_round
)

# ============================================================================
# Configuration Constants
# ============================================================================

# Catalog and Schema Configuration
CATALOG_NAME = "lab_catalog01"
SOURCE_SCHEMA = "retail"
TARGET_SCHEMA = "analytics"

# Source Tables
SOURCE_ORDERS_TABLE = f"{CATALOG_NAME}.{SOURCE_SCHEMA}.orders"

# Target Tables - Silver Layer
SILVER_ORDERS_TABLE = f"{CATALOG_NAME}.{TARGET_SCHEMA}.silver_orders"

# Target Tables - Gold Layer
GOLD_DAILY_SALES_TABLE = f"{CATALOG_NAME}.{TARGET_SCHEMA}.gold_daily_sales"
GOLD_CUSTOMER_SEGMENTS_TABLE = f"{CATALOG_NAME}.{TARGET_SCHEMA}.gold_customer_segments"

# Business Logic Constants
AMOUNT_THRESHOLDS = {
    "LOW": 100,
    "MEDIUM": 500,
    "HIGH": 1000
}

CUSTOMER_SEGMENT_THRESHOLDS = {
    "VIP": 5000,
    "PREMIUM": 2000,
    "REGULAR": 500
}

# Spark Configuration
SPARK_APP_NAME = "Retail-ETL-Pipeline"
SPARK_CATALOG_TYPE = "hive"

def create_spark_session() -> SparkSession:
    """
    Create and configure Spark session with Iceberg support.
    
    Configures:
        - Iceberg Spark extensions for table format support
        - Hive metastore catalog integration
        - Adaptive query execution for performance
        - Partition coalescing optimization
    
    Returns:
        SparkSession: Configured Spark session with Iceberg support
        
    Example:
        >>> spark = create_spark_session()
        >>> spark.version
        '3.3.0'
    """
    return (
        SparkSession.builder
        .appName(SPARK_APP_NAME)
        # Enable Iceberg extensions
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        # Enable Hive support for metastore access
        .enableHiveSupport()
        # Performance optimizations
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .getOrCreate()
    )


def setup_logging(spark: SparkSession):
    """
    Configure Log4j logging for the ETL pipeline.
    
    Sets the Spark context log level to WARN to reduce noise and creates
    a dedicated logger for ETL pipeline operations.
    
    Args:
        spark: Active Spark session
        
    Returns:
        Log4j Logger instance for ETL pipeline logging
        
    Example:
        >>> logger = setup_logging(spark)
        >>> logger.info("Pipeline started")
    """
    spark.sparkContext.setLogLevel("WARN")
    log4j = spark._jvm.org.apache.log4j
    logger = log4j.LogManager.getLogger("ETLPipeline")
    return logger


def log(logger, msg: str, level: str = "INFO") -> None:
    """
    Log a message with timestamp to both Log4j and console.
    
    Formats messages with ISO timestamp and outputs to both the Log4j
    logger and standard output for visibility.
    
    Args:
        logger: Log4j logger instance
        msg: Message to log
        level: Log level - "INFO", "WARN", or "ERROR" (default: "INFO")
        
    Example:
        >>> log(logger, "Processing started", "INFO")
        [2024-01-15 10:30:45] Processing started
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

def process_bronze_layer(spark: SparkSession, logger) -> DataFrame:
    """
    Process Bronze Layer: Raw data ingestion with metadata tracking.
    
    The Bronze layer represents the raw data as ingested from source systems,
    with additional metadata columns for lineage and audit purposes.
    
    Operations:
        - Load raw orders from source table
        - Add ingestion timestamp for tracking
        - Add source system identifier
        - Cache for downstream processing
    
    Args:
        spark: Active Spark session
        logger: Log4j logger instance
        
    Returns:
        DataFrame: Bronze layer orders with metadata columns
        
    Raises:
        Exception: If source table cannot be read
        
    Example:
        >>> bronze_df = process_bronze_layer(spark, logger)
        >>> bronze_df.columns
        ['order_id', 'customer_id', ..., 'ingestion_timestamp', 'source_system']
    """
    log(logger, "\n" + "=" * 80)
    log(logger, "[BRONZE LAYER] Loading raw data...")
    log(logger, f"Source Table: {SOURCE_ORDERS_TABLE}")
    log(logger, "=" * 80)
    
    start_time = time.time()
    
    # Read raw orders
    bronze_orders = spark.table(SOURCE_ORDERS_TABLE)
    
    # Add metadata columns
    bronze_orders = bronze_orders \
        .withColumn("ingestion_timestamp", current_timestamp()) \
        .withColumn("source_system", lit(SOURCE_SCHEMA))
    
    bronze_orders.cache()
    record_count = bronze_orders.count()
    
    log(logger, f"✓ Bronze orders loaded: {record_count:,} records (in {time.time() - start_time:.2f}s)")
    
    return bronze_orders


def process_silver_layer(spark: SparkSession, logger, bronze_orders: DataFrame) -> DataFrame:
    """
    Process Silver Layer: Data cleansing, validation, and enrichment.
    
    The Silver layer contains cleaned, validated, and enriched data ready
    for analytics. Applies data quality rules and business transformations.
    
    Data Quality Rules:
        - Remove records with null order_id or customer_id
        - Filter out orders with zero or negative amounts
        - Standardize null status values to "UNKNOWN"
    
    Enrichments:
        - Extract date components (year, month, day)
        - Categorize order amounts (LOW/MEDIUM/HIGH/PREMIUM)
        - Clean and standardize status values
    
    Args:
        spark: Active Spark session
        logger: Log4j logger instance
        bronze_orders: Bronze layer DataFrame
        
    Returns:
        DataFrame: Cleaned and enriched Silver layer orders
        
    Output Table:
        Configured via SILVER_ORDERS_TABLE constant (partitioned by year, month)
        
    Example:
        >>> silver_df = process_silver_layer(spark, logger, bronze_df)
        >>> silver_df.filter(col("amount_category") == "PREMIUM").count()
        1523
    """
    log(logger, "\n" + "=" * 80)
    log(logger, "[SILVER LAYER] Cleaning and validating data...")
    log(logger, f"Target Table: {SILVER_ORDERS_TABLE}")
    log(logger, "=" * 80)
    
    start_time = time.time()
    
    # Data quality checks and transformations
    silver_orders = bronze_orders \
        .filter(col("order_id").isNotNull()) \
        .filter(col("customer_id").isNotNull()) \
        .filter(col("total_amount") > 0) \
        .withColumn("order_year", year(col("order_date"))) \
        .withColumn("order_month", month(col("order_date"))) \
        .withColumn("order_day", dayofmonth(col("order_date"))) \
        .withColumn("order_status_clean",
                    when(col("order_status").isNull(), "UNKNOWN")
                    .otherwise(col("order_status"))) \
        .withColumn("amount_category",
                    when(col("total_amount") < AMOUNT_THRESHOLDS["LOW"], "LOW")
                    .when(col("total_amount") < AMOUNT_THRESHOLDS["MEDIUM"], "MEDIUM")
                    .when(col("total_amount") < AMOUNT_THRESHOLDS["HIGH"], "HIGH")
                    .otherwise("PREMIUM"))
    
    silver_orders.cache()
    clean_count = silver_orders.count()
    
    log(logger, f"✓ Silver orders after cleaning: {clean_count:,} records (in {time.time() - start_time:.2f}s)")
    
    # Write to Silver layer
    log(logger, "Writing to Silver layer table...")
    write_start = time.time()
    
    silver_orders.write \
        .format("iceberg") \
        .mode("overwrite") \
        .partitionBy("order_year", "order_month") \
        .saveAsTable(SILVER_ORDERS_TABLE)
    
    log(logger, f"✓ Silver layer written successfully (in {time.time() - write_start:.2f}s)")
    
    return silver_orders

def process_gold_layer(spark: SparkSession, logger, silver_orders: DataFrame) -> bool:
    """
    Process Gold Layer: Business-level aggregates and analytics.
    
    The Gold layer contains business-ready aggregated data optimized for
    reporting and analytics. Creates two key business views:
    
    1. Daily Sales Summary:
        - Total orders and revenue per day
        - Unique customer counts
        - Average, min, max order values
        - Revenue per customer metrics
    
    2. Customer Segments:
        - Customer lifetime value calculation
        - Segmentation (VIP/PREMIUM/REGULAR/NEW)
        - Order frequency and recency
    
    Segment Thresholds (from CUSTOMER_SEGMENT_THRESHOLDS):
        - VIP: Lifetime value >= $5,000
        - PREMIUM: Lifetime value >= $2,000
        - REGULAR: Lifetime value >= $500
        - NEW: Lifetime value < $500
    
    Args:
        spark: Active Spark session
        logger: Log4j logger instance
        silver_orders: Cleaned Silver layer DataFrame
        
    Returns:
        bool: True if processing completed successfully
        
    Output Tables:
        Configured via GOLD_DAILY_SALES_TABLE and GOLD_CUSTOMER_SEGMENTS_TABLE constants
        
    Example:
        >>> success = process_gold_layer(spark, logger, silver_df)
        >>> spark.table(GOLD_DAILY_SALES_TABLE).count()
        365
    """
    log(logger, "\n" + "=" * 80)
    log(logger, "[GOLD LAYER] Creating business aggregates...")
    log(logger, "=" * 80)
    
    # Daily sales summary
    log(logger, "Creating daily sales summary...")
    log(logger, f"Target Table: {GOLD_DAILY_SALES_TABLE}")
    start_time = time.time()
    
    daily_summary = silver_orders.groupBy(
        "order_date",
        "order_year",
        "order_month"
    ).agg(
        count("order_id").alias("total_orders"),
        count(col("customer_id")).alias("unique_customers"),
        spark_sum("total_amount").alias("total_revenue"),
        avg("total_amount").alias("avg_order_value"),
        spark_min("total_amount").alias("min_order_value"),
        spark_max("total_amount").alias("max_order_value")
    ).withColumn("revenue_per_customer",
                 spark_round(col("total_revenue") / col("unique_customers"), 2))
    
    daily_summary.cache()
    
    # Write daily summary
    daily_summary.write \
        .format("iceberg") \
        .mode("overwrite") \
        .partitionBy("order_year", "order_month") \
        .saveAsTable(GOLD_DAILY_SALES_TABLE)
    
    daily_count = daily_summary.count()
    log(logger, f"✓ Gold daily summary created: {daily_count:,} records (in {time.time() - start_time:.2f}s)")
    
    # Customer segment analysis
    log(logger, "\nCreating customer segments...")
    log(logger, f"Target Table: {GOLD_CUSTOMER_SEGMENTS_TABLE}")
    start_time = time.time()
    
    customer_segments = silver_orders.groupBy("customer_id").agg(
        count("order_id").alias("order_count"),
        spark_sum("total_amount").alias("lifetime_value"),
        avg("total_amount").alias("avg_order_value"),
        spark_max("order_date").alias("last_order_date")
    ).withColumn("customer_segment",
                 when(col("lifetime_value") >= CUSTOMER_SEGMENT_THRESHOLDS["VIP"], "VIP")
                 .when(col("lifetime_value") >= CUSTOMER_SEGMENT_THRESHOLDS["PREMIUM"], "PREMIUM")
                 .when(col("lifetime_value") >= CUSTOMER_SEGMENT_THRESHOLDS["REGULAR"], "REGULAR")
                 .otherwise("NEW"))
    
    customer_segments.cache()
    
    # Write customer segments
    customer_segments.write \
        .format("iceberg") \
        .mode("overwrite") \
        .saveAsTable(GOLD_CUSTOMER_SEGMENTS_TABLE)
    
    segment_count = customer_segments.count()
    log(logger, f"✓ Gold customer segments created: {segment_count:,} records (in {time.time() - start_time:.2f}s)")
    
    # Show sample results
    log(logger, "\n" + "=" * 80)
    log(logger, "[RESULTS] Sample Gold Layer Data")
    log(logger, "=" * 80)
    
    log(logger, "\nDaily Sales Summary (last 5 days):")
    daily_summary.orderBy(col("order_date").desc()).show(5, truncate=False)
    
    log(logger, "\nCustomer Segments Distribution:")
    customer_segments.groupBy("customer_segment") \
        .agg(count("*").alias("customer_count"),
             spark_round(avg("lifetime_value"), 2).alias("avg_lifetime_value")) \
        .orderBy(col("avg_lifetime_value").desc()) \
        .show(truncate=False)
    
    # Cleanup
    daily_summary.unpersist()
    customer_segments.unpersist()
    
    return True


def run_etl_pipeline(spark: SparkSession, logger) -> bool:
    """
    Execute the complete ETL pipeline across all layers.
    
    Orchestrates the end-to-end data processing workflow:
    1. Bronze Layer: Raw data ingestion
    2. Silver Layer: Data cleansing and validation
    3. Gold Layer: Business aggregations
    
    Includes comprehensive error handling, performance monitoring,
    and automatic resource cleanup.
    
    Args:
        spark: Active Spark session
        logger: Log4j logger instance
        
    Returns:
        bool: True if pipeline completed successfully, False otherwise
        
    Raises:
        Exception: Logs and returns False on any processing error
        
    Example:
        >>> success = run_etl_pipeline(spark, logger)
        >>> if success:
        ...     print("Pipeline completed successfully")
    """
    try:
        log(logger, "=" * 80)
        log(logger, "ETL Pipeline: Bronze -> Silver -> Gold")
        log(logger, "=" * 80)
        
        pipeline_start = time.time()
        
        # Process Bronze layer
        bronze_orders = process_bronze_layer(spark, logger)
        
        # Process Silver layer
        silver_orders = process_silver_layer(spark, logger, bronze_orders)
        
        # Process Gold layer
        process_gold_layer(spark, logger, silver_orders)
        
        # Cleanup
        bronze_orders.unpersist()
        silver_orders.unpersist()
        
        total_time = time.time() - pipeline_start
        
        log(logger, "\n" + "=" * 80)
        log(logger, f"✓ ETL Pipeline completed successfully in {total_time:.2f}s!")
        log(logger, "=" * 80)
        
        return True
        
    except Exception as e:
        log(logger, "\n" + "=" * 80, "ERROR")
        log(logger, "ERROR: ETL Pipeline failed", "ERROR")
        log(logger, "=" * 80, "ERROR")
        log(logger, f"Error: {str(e)}", "ERROR")
        log(logger, traceback.format_exc(), "ERROR")
        return False


def main() -> int:
    """
    Main execution function with comprehensive error handling.
    
    Initializes Spark session, configures logging, executes the ETL pipeline,
    and ensures proper cleanup of resources.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
        
    Example:
        >>> exit_code = main()
        >>> sys.exit(exit_code)
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
        
        success = run_etl_pipeline(spark, logger)
        
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
    """
    Script entry point.
    
    Executes the ETL pipeline and exits with appropriate status code.
    """
    exit_code = main()
    exit(exit_code)
