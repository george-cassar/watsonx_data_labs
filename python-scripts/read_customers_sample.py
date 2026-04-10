"""
watsonx.data Iceberg Table Reader - Customer Sample
====================================================
Reads 10 sample rows from the customers table in watsonx.data.

Best Practices Implemented:
- Explicit Iceberg catalog configuration
- Proper error handling and logging
- Resource cleanup with context management
- Schema validation
- Performance monitoring
- Graceful shutdown
"""

from pyspark.sql import SparkSession
import traceback
import time
from datetime import datetime

# ============================================================================
# CONFIGURATION - Global Constants
# ============================================================================
CATALOG = "lab_catalog01"
SCHEMA = "retail"
TABLE = "customers"
SAMPLE_SIZE = 10

def create_spark_session():
    """
    Create Spark session with Iceberg support and watsonx.data best practices.
    
    Note: Resource allocation (driver/executor memory, cores, count) is configured
    via the JSON payload when submitting the Spark job, not in the application code.
    """
    return (
        SparkSession.builder
        .appName("watsonx.data-Customer-Sample-Reader")
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
    """
    # Set appropriate log level (WARN reduces noise, INFO for debugging)
    spark.sparkContext.setLogLevel("WARN")
    
    # Get JVM log4j logger for structured logging
    log4j = spark._jvm.org.apache.log4j
    logger = log4j.LogManager.getLogger("CustomerSampleReader")
    
    return logger

def log(logger, msg: str, level: str = "INFO"):
    """
    Log message with timestamp and level.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {msg}"
    
    if level == "INFO":
        logger.info(formatted_msg)
    elif level == "WARN":
        logger.warn(formatted_msg)
    elif level == "ERROR":
        logger.error(formatted_msg)
    
    # Also print to stdout for immediate visibility
    print(formatted_msg)

def validate_table_exists(spark, catalog: str, schema: str, table: str) -> bool:
    """
    Validate that the table exists before attempting to read.
    """
    try:
        tables = spark.sql(f"SHOW TABLES IN {catalog}.{schema}").collect()
        table_names = [row.tableName for row in tables]
        return table in table_names
    except Exception:
        return False

def read_customer_sample(spark, logger):
    """
    Read sample data from customers table with best practices.
    Uses global configuration constants defined at module level.
    """
    FULL_TABLE_NAME = f"{CATALOG}.{SCHEMA}.{TABLE}"
    
    log(logger, "=" * 80)
    log(logger, "watsonx.data Iceberg Table Reader - Customer Sample")
    log(logger, "=" * 80)
    log(logger, f"Catalog: {CATALOG}")
    log(logger, f"Schema: {SCHEMA}")
    log(logger, f"Table: {TABLE}")
    log(logger, f"Sample Size: {SAMPLE_SIZE} rows")
    log(logger, "=" * 80)
    
    # Validate table exists
    log(logger, "Validating table existence...")
    if not validate_table_exists(spark, CATALOG, SCHEMA, TABLE):
        log(logger, f"ERROR: Table {FULL_TABLE_NAME} does not exist!", "ERROR")
        log(logger, f"Available tables in {CATALOG}.{SCHEMA}:")
        try:
            tables = spark.sql(f"SHOW TABLES IN {CATALOG}.{SCHEMA}")
            tables.show(truncate=False)
        except Exception as e:
            log(logger, f"Could not list tables: {str(e)}", "ERROR")
        return False
    
    log(logger, "✓ Table exists")
    
    try:
        # Start timing
        start_time = time.time()
        
        # Read table with limit
        log(logger, f"\nReading {SAMPLE_SIZE} rows from {FULL_TABLE_NAME}...")
        df = spark.table(FULL_TABLE_NAME).limit(SAMPLE_SIZE)
        
        # Cache for multiple operations
        df.cache()
        
        # Get row count
        row_count = df.count()
        read_time = time.time() - start_time
        
        log(logger, f"✓ Successfully read {row_count} rows in {read_time:.2f} seconds")
        
        # Display schema
        log(logger, "\n" + "=" * 80)
        log(logger, "TABLE SCHEMA")
        log(logger, "=" * 80)
        schema_str = df._jdf.schema().treeString()
        log(logger, schema_str)
        
        # Display sample data
        log(logger, "\n" + "=" * 80)
        log(logger, "SAMPLE DATA (First 10 Rows)")
        log(logger, "=" * 80)
        
        # Show data in tabular format
        df.show(truncate=False)
        
        # Get column statistics
        log(logger, "\n" + "=" * 80)
        log(logger, "DATA STATISTICS")
        log(logger, "=" * 80)
        log(logger, f"Total Columns: {len(df.columns)}")
        log(logger, f"Column Names: {', '.join(df.columns)}")
        
        # Check for null values
        log(logger, "\nNull Value Check:")
        for col_name in df.columns:
            null_count = df.filter(df[col_name].isNull()).count()
            if null_count > 0:
                log(logger, f"  {col_name}: {null_count} null values", "WARN")
            else:
                log(logger, f"  {col_name}: No null values")
        
        # Optional: Export sample as JSON
        log(logger, "\n" + "=" * 80)
        log(logger, "SAMPLE DATA (JSON Format)")
        log(logger, "=" * 80)
        json_records = df.toJSON().collect()
        for i, record in enumerate(json_records, 1):
            log(logger, f"Record {i}: {record}")
        
        # Unpersist cache
        df.unpersist()
        
        log(logger, "\n" + "=" * 80)
        log(logger, "✓ Successfully completed customer sample read!")
        log(logger, "=" * 80)
        
        return True
        
    except Exception as e:
        log(logger, "\n" + "=" * 80, "ERROR")
        log(logger, "ERROR: Failed to read customer data", "ERROR")
        log(logger, "=" * 80, "ERROR")
        log(logger, f"Error Message: {str(e)}", "ERROR")
        log(logger, "\nFull Traceback:", "ERROR")
        log(logger, traceback.format_exc(), "ERROR")
        
        log(logger, "\n" + "=" * 80, "ERROR")
        log(logger, "TROUBLESHOOTING STEPS", "ERROR")
        log(logger, "=" * 80, "ERROR")
        log(logger, f"1. Verify catalog '{CATALOG}' is associated with your Spark engine")
        log(logger, f"2. Confirm schema '{SCHEMA}' exists in catalog '{CATALOG}'")
        log(logger, f"3. Ensure table '{TABLE}' exists in schema '{SCHEMA}'")
        log(logger, "4. Check Spark engine status in Infrastructure Manager")
        log(logger, "5. Verify you have read permissions on the table")
        log(logger, "6. Review Spark driver logs for additional details")
        
        return False

def main():
    """
    Main execution function with proper resource management.
    """
    spark = None
    logger = None
    
    try:
        # Initialize Spark session
        print("Initializing Spark session...")
        spark = create_spark_session()
        
        # Setup logging
        logger = setup_logging(spark)
        log(logger, "Spark session initialized successfully")
        log(logger, f"Spark Version: {spark.version}")
        log(logger, f"Application ID: {spark.sparkContext.applicationId}")
        
        # Execute main logic
        success = read_customer_sample(spark, logger)
        
        if success:
            log(logger, "\n✓ Application completed successfully")
            return 0
        else:
            log(logger, "\n✗ Application completed with errors", "ERROR")
            return 1
            
    except Exception as e:
        if logger:
            log(logger, f"\n✗ Fatal error: {str(e)}", "ERROR")
            log(logger, traceback.format_exc(), "ERROR")
        else:
            print(f"Fatal error: {str(e)}")
            print(traceback.format_exc())
        return 1
        
    finally:
        # Ensure Spark session is properly closed
        if spark:
            if logger:
                log(logger, "\nStopping Spark session...")
            else:
                print("Stopping Spark session...")
            spark.stop()
            if logger:
                log(logger, "✓ Spark session stopped")
            else:
                print("✓ Spark session stopped")

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
