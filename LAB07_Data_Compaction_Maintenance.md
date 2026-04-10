# Lab 7: Data Compaction and Maintenance

**Duration:** 45 minutes
**Difficulty:** Intermediate
**Prerequisites:** Completion of Labs 1-6, Understanding of Iceberg table internals
**Last Updated:** April 2026

---

## Lab Objectives

By the end of this lab, you will understand:
- MOR (Merge-on-Read) vs COW (Copy-on-Write) table formats
- When and how to convert between MOR and COW
- How to use Spark procedures for data reorganization
- File compaction strategies using `rewrite_data_files`
- Manifest optimization using `rewrite_manifests`
- Best practices for table maintenance

---

## Part 1: Understanding MOR vs COW (15 minutes)

### What is MOR (Merge-on-Read)?

**Merge-on-Read (MOR)** tables optimize for write performance by storing updates and deletes as separate delta files. When reading data, the query engine merges these delta files with the base data files at read time.

**Characteristics:**
- ✅ **Fast writes**: Updates and deletes are written as delta files
- ✅ **Lower write amplification**: Only changed data is written
- ⚠️ **Slower reads**: Requires merging delta files during queries
- ⚠️ **More files**: Accumulates delta files over time

**Use Cases:**
- High-frequency updates and deletes
- Write-heavy workloads
- Real-time data ingestion
- Streaming applications

### What is COW (Copy-on-Write)?

**Copy-on-Write (COW)** tables optimize for read performance by rewriting entire data files when updates or deletes occur. This ensures data files always contain the latest state.

**Characteristics:**
- ✅ **Fast reads**: No merge required, data is already consolidated
- ✅ **Fewer files**: Maintains optimal file structure
- ⚠️ **Slower writes**: Must rewrite entire files for updates
- ⚠️ **Higher write amplification**: Rewrites more data than changed

**Use Cases:**
- Read-heavy workloads
- Infrequent updates
- Analytical queries
- Data warehousing

### Comparison Table

| Feature | MOR (Merge-on-Read) | COW (Copy-on-Write) |
|---------|---------------------|---------------------|
| **Write Performance** | Fast | Slower |
| **Read Performance** | Slower (merge overhead) | Fast |
| **File Count** | Higher (delta files) | Lower (consolidated) |
| **Write Amplification** | Low | High |
| **Best For** | Write-heavy, updates | Read-heavy, analytics |
| **Maintenance Needs** | Regular compaction | Less frequent |

---

## Part 2: MOR to COW Conversion (10 minutes)

### When to Convert MOR to COW

Convert MOR tables to COW when:
- Read performance becomes critical
- Update frequency decreases
- Delta files accumulate excessively
- Query latency increases
- Moving from streaming to batch processing

### Submitting Spark Jobs for MOR/COW Conversion

watsonx.data provides Spark-based procedures to convert between MOR and COW formats. This is done by submitting Spark jobs that reorganize the table data.

**📚 Official Documentation:**
- [Submitting Spark jobs for MOR/COW conversion](https://www.ibm.com/docs/en/watsonxdata/standard/2.3.x?topic=engine-submitting-spark-jobs-mor-cow-conversion)

### Conversion Process Overview

The conversion process involves:

1. **Analyze Current Format**: Determine if table is MOR or COW
2. **Submit Spark Job**: Use watsonx.data UI or API to submit conversion job
3. **Monitor Progress**: Track job execution in Spark History Server
4. **Verify Conversion**: Confirm table format and file structure

### Example: Converting MOR to COW

**Using watsonx.data UI:**

1. Navigate to **Infrastructure Manager** → **Spark Engines**
2. Select your Spark engine
3. Click **Create Application**
4. Configure the conversion job:
   ```json
   {
     "application_details": {
       "application": "mor_to_cow_conversion",
       "conf": {
         "spark.app.name": "MOR to COW Conversion",
         "spark.sql.catalog.iceberg_catalog": "org.apache.iceberg.spark.SparkCatalog",
         "spark.sql.catalog.iceberg_catalog.type": "hadoop",
         "spark.sql.catalog.iceberg_catalog.warehouse": "s3a://bucket/warehouse"
       },
       "arguments": [
         "--catalog", "lab_catalog01",
         "--schema", "retail",
         "--table", "orders",
         "--target-format", "COW"
       ]
     }
   }
   ```

**Using cpdctl:**

```bash
cpdctl wx-data sparkjob create \
  --engine-id spark01 \
  --local-path ./scripts/mor_to_cow_conversion.py \
  --bucket-name lab-minio-bucket01 \
  --conf '{
    "spark.app.name":"MOR to COW Conversion",
    "spark.sql.catalog.iceberg_catalog":"org.apache.iceberg.spark.SparkCatalog"
  }' \
  --api-key $API_KEY \
  --instance-id $INSTANCE_ID
```

### Monitoring Conversion

After submitting the conversion job:

1. **Check Job Status**: Monitor in Spark History Server
2. **Review Logs**: Check for errors or warnings
3. **Verify File Structure**: Confirm delta files are consolidated
4. **Test Queries**: Validate read performance improvement

---

## Part 3: Data Reorganization with Spark Procedures (15 minutes)

When you need to reorganize data in your Iceberg tables, you can use Spark procedures directly in your application code. These procedures are more flexible than SQL-based maintenance and can be integrated into automated workflows.

### Using `rewrite_data_files` Procedure

The `rewrite_data_files` procedure compacts small files and reorganizes data for better query performance.

**📚 Official Documentation:**
- [rewrite_data_files Spark Procedure](https://iceberg.apache.org/docs/latest/spark-procedures/#rewrite_data_files)

**Purpose:**
- Compact small files into larger, optimally-sized files
- Reorganize data for better scan performance
- Reduce metadata overhead
- Improve query performance

**Syntax:**

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("Data File Rewrite") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.lab_catalog", "org.apache.iceberg.spark.SparkCatalog") \
    .getOrCreate()

# Rewrite data files for entire table
spark.sql("""
    CALL lab_catalog.system.rewrite_data_files(
        table => 'retail.orders',
        strategy => 'binpack',
        options => map(
            'target-file-size-bytes', '134217728',  -- 128MB
            'min-input-files', '5',
            'max-concurrent-file-group-rewrites', '4'
        )
    )
""").show()

# Rewrite data files for specific partition
spark.sql("""
    CALL lab_catalog.system.rewrite_data_files(
        table => 'retail.orders',
        strategy => 'binpack',
        where => 'order_date >= DATE ''2024-03-01'' AND order_date < DATE ''2024-04-01''',
        options => map('target-file-size-bytes', '134217728')
    )
""").show()
```

**Parameters:**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `table` | Table identifier (required) | - |
| `strategy` | Rewrite strategy: `binpack` or `sort` | `binpack` |
| `where` | Filter expression for partitions | All partitions |
| `options` | Map of additional options | Empty map |

**Common Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `target-file-size-bytes` | Target size for output files | 536870912 (512MB) |
| `min-input-files` | Minimum files to rewrite | 5 |
| `max-concurrent-file-group-rewrites` | Parallelism level | 5 |
| `partial-progress.enabled` | Enable partial progress | false |
| `partial-progress.max-commits` | Max commits for partial progress | 10 |

**Example: Complete Rewrite Script**

```python
from pyspark.sql import SparkSession
import sys

def rewrite_table_data(catalog, schema, table, target_size_mb=128):
    """
    Rewrite data files for an Iceberg table
    
    Args:
        catalog: Catalog name
        schema: Schema name
        table: Table name
        target_size_mb: Target file size in MB
    """
    spark = SparkSession.builder \
        .appName(f"Rewrite Data Files: {schema}.{table}") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config(f"spark.sql.catalog.{catalog}", "org.apache.iceberg.spark.SparkCatalog") \
        .getOrCreate()
    
    target_size_bytes = target_size_mb * 1024 * 1024
    table_identifier = f"{catalog}.{schema}.{table}"
    
    print(f"Rewriting data files for {table_identifier}")
    print(f"Target file size: {target_size_mb}MB")
    
    # Execute rewrite
    result = spark.sql(f"""
        CALL {catalog}.system.rewrite_data_files(
            table => '{schema}.{table}',
            strategy => 'binpack',
            options => map(
                'target-file-size-bytes', '{target_size_bytes}',
                'min-input-files', '5',
                'max-concurrent-file-group-rewrites', '4',
                'partial-progress.enabled', 'true',
                'partial-progress.max-commits', '10'
            )
        )
    """)
    
    result.show(truncate=False)
    print(f"✓ Data file rewrite completed for {table_identifier}")
    
    spark.stop()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python rewrite_data_files.py <catalog> <schema> <table> [target_size_mb]")
        sys.exit(1)
    
    catalog = sys.argv[1]
    schema = sys.argv[2]
    table = sys.argv[3]
    target_size_mb = int(sys.argv[4]) if len(sys.argv) > 4 else 128
    
    rewrite_table_data(catalog, schema, table, target_size_mb)
```

### Using `rewrite_manifests` Procedure

The `rewrite_manifests` procedure consolidates manifest files to reduce metadata overhead and improve query planning performance.

**📚 Official Documentation:**
- [rewrite_manifests Spark Procedure](https://iceberg.apache.org/docs/latest/spark-procedures/#rewrite_manifests)

**Purpose:**
- Consolidate small manifest files
- Reduce metadata overhead
- Improve query planning performance
- Optimize table metadata structure

**Syntax:**

```python
# Rewrite manifests for entire table
spark.sql("""
    CALL lab_catalog.system.rewrite_manifests(
        table => 'retail.orders'
    )
""").show()

# Rewrite manifests with options
spark.sql("""
    CALL lab_catalog.system.rewrite_manifests(
        table => 'retail.orders',
        options => map(
            'use-caching', 'true',
            'max-manifest-file-size-bytes', '8388608'  -- 8MB
        )
    )
""").show()
```

**Parameters:**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `table` | Table identifier (required) | - |
| `options` | Map of additional options | Empty map |

**Common Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `use-caching` | Cache manifest content | true |
| `max-manifest-file-size-bytes` | Maximum manifest file size | 8388608 (8MB) |

**Example: Complete Manifest Rewrite Script**

```python
from pyspark.sql import SparkSession
import sys

def rewrite_table_manifests(catalog, schema, table):
    """
    Rewrite manifest files for an Iceberg table
    
    Args:
        catalog: Catalog name
        schema: Schema name
        table: Table name
    """
    spark = SparkSession.builder \
        .appName(f"Rewrite Manifests: {schema}.{table}") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config(f"spark.sql.catalog.{catalog}", "org.apache.iceberg.spark.SparkCatalog") \
        .getOrCreate()
    
    table_identifier = f"{catalog}.{schema}.{table}"
    
    print(f"Rewriting manifests for {table_identifier}")
    
    # Execute rewrite
    result = spark.sql(f"""
        CALL {catalog}.system.rewrite_manifests(
            table => '{schema}.{table}',
            options => map(
                'use-caching', 'true',
                'max-manifest-file-size-bytes', '8388608'
            )
        )
    """)
    
    result.show(truncate=False)
    print(f"✓ Manifest rewrite completed for {table_identifier}")
    
    spark.stop()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python rewrite_manifests.py <catalog> <schema> <table>")
        sys.exit(1)
    
    catalog = sys.argv[1]
    schema = sys.argv[2]
    table = sys.argv[3]
    
    rewrite_table_manifests(catalog, schema, table)
```

### Combined Maintenance Script

Here's a complete maintenance script that combines both procedures:

```python
from pyspark.sql import SparkSession
from datetime import datetime
import sys

class TableMaintenance:
    def __init__(self, catalog):
        self.catalog = catalog
        self.spark = SparkSession.builder \
            .appName("Table Maintenance") \
            .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
            .config(f"spark.sql.catalog.{catalog}", "org.apache.iceberg.spark.SparkCatalog") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
    
    def run_maintenance(self, schema, table, target_file_size_mb=128):
        """
        Run complete maintenance workflow
        
        Args:
            schema: Schema name
            table: Table name
            target_file_size_mb: Target file size for compaction
        """
        table_identifier = f"{self.catalog}.{schema}.{table}"
        
        print(f"\n{'='*80}")
        print(f"TABLE MAINTENANCE: {table_identifier}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        try:
            # Step 1: Rewrite data files
            print("1. Rewriting data files...")
            target_size_bytes = target_file_size_mb * 1024 * 1024
            
            self.spark.sql(f"""
                CALL {self.catalog}.system.rewrite_data_files(
                    table => '{schema}.{table}',
                    strategy => 'binpack',
                    options => map(
                        'target-file-size-bytes', '{target_size_bytes}',
                        'min-input-files', '5',
                        'max-concurrent-file-group-rewrites', '4'
                    )
                )
            """).show(truncate=False)
            print("   ✓ Data file rewrite completed\n")
            
            # Step 2: Rewrite manifests
            print("2. Rewriting manifests...")
            self.spark.sql(f"""
                CALL {self.catalog}.system.rewrite_manifests(
                    table => '{schema}.{table}',
                    options => map(
                        'use-caching', 'true',
                        'max-manifest-file-size-bytes', '8388608'
                    )
                )
            """).show(truncate=False)
            print("   ✓ Manifest rewrite completed\n")
            
            print(f"{'='*80}")
            print(f"✓ MAINTENANCE COMPLETED SUCCESSFULLY")
            print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*80}\n")
            
            return True
            
        except Exception as e:
            print(f"\n✗ ERROR: Maintenance failed - {str(e)}")
            return False
    
    def run_batch_maintenance(self, tables, target_file_size_mb=128):
        """
        Run maintenance on multiple tables
        
        Args:
            tables: List of (schema, table) tuples
            target_file_size_mb: Target file size for compaction
        """
        print(f"\n{'='*80}")
        print(f"BATCH MAINTENANCE JOB")
        print(f"Tables to process: {len(tables)}")
        print(f"{'='*80}\n")
        
        results = []
        
        for schema, table in tables:
            success = self.run_maintenance(schema, table, target_file_size_mb)
            results.append((f"{schema}.{table}", "SUCCESS" if success else "FAILED"))
        
        # Summary
        print(f"\n{'='*80}")
        print(f"MAINTENANCE SUMMARY")
        print(f"{'='*80}")
        for table, status in results:
            symbol = "✓" if status == "SUCCESS" else "✗"
            print(f"  {symbol} {table}: {status}")
        print(f"{'='*80}\n")
        
        self.spark.stop()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python table_maintenance.py <catalog> [target_size_mb]")
        sys.exit(1)
    
    catalog = sys.argv[1]
    target_size_mb = int(sys.argv[2]) if len(sys.argv) > 2 else 128
    
    maintenance = TableMaintenance(catalog)
    
    # Define tables to maintain
    tables = [
        ("retail", "orders"),
        ("retail", "customers"),
        ("retail", "products")
    ]
    
    maintenance.run_batch_maintenance(tables, target_size_mb)
```

---

## Part 4: Best Practices (5 minutes)

### When to Run Maintenance

**Data File Compaction (`rewrite_data_files`):**
- After many small writes or updates
- When >30% of files are smaller than 10MB
- Before running large analytical queries
- During scheduled maintenance windows
- After bulk data ingestion

**Manifest Rewriting (`rewrite_manifests`):**
- After many write operations
- When manifest count grows significantly
- Periodically (e.g., weekly)
- After major table reorganization
- When query planning becomes slow

### Maintenance Schedule Recommendations

| Workload Type | Data Files | Manifests | Frequency |
|---------------|------------|-----------|-----------|
| **High-frequency writes** | Daily | Weekly | Automated |
| **Moderate writes** | Weekly | Bi-weekly | Scheduled |
| **Low-frequency writes** | Monthly | Monthly | Manual |
| **Read-only** | As needed | Rarely | On-demand |

### Performance Considerations

**Resource Allocation:**
- Allocate sufficient Spark resources for maintenance jobs
- Use appropriate parallelism settings
- Run during low-traffic periods
- Monitor job execution time

**File Size Targets:**
- **Optimal**: 128MB - 512MB per file
- **Too small**: < 10MB (causes metadata overhead)
- **Too large**: > 1GB (reduces parallelism)

**Monitoring:**
- Track file count and sizes before/after
- Monitor query performance improvements
- Log maintenance job execution
- Alert on failures

---

## Summary

In this lab, you learned about:

✅ **MOR vs COW**: Understanding the trade-offs between Merge-on-Read and Copy-on-Write formats

✅ **Format Conversion**: How to submit Spark jobs for MOR/COW conversion using watsonx.data

✅ **Data Reorganization**: Using `rewrite_data_files` Spark procedure for file compaction

✅ **Manifest Optimization**: Using `rewrite_manifests` Spark procedure for metadata optimization

✅ **Best Practices**: When and how to run maintenance operations

### Key Takeaways

1. **Choose the right format**: MOR for write-heavy, COW for read-heavy workloads
2. **Regular maintenance**: Schedule periodic compaction and manifest rewrites
3. **Use Spark procedures**: Integrate maintenance into application code
4. **Monitor performance**: Track improvements after maintenance operations
5. **Automate when possible**: Create scripts for batch maintenance

---

## Additional Resources

- [watsonx.data: Submitting Spark jobs for MOR/COW conversion](https://www.ibm.com/docs/en/watsonxdata/standard/2.3.x?topic=engine-submitting-spark-jobs-mor-cow-conversion)
- [Apache Iceberg: rewrite_data_files Procedure](https://iceberg.apache.org/docs/latest/spark-procedures/#rewrite_data_files)
- [Apache Iceberg: rewrite_manifests Procedure](https://iceberg.apache.org/docs/latest/spark-procedures/#rewrite_manifests)
- [Apache Iceberg: Table Maintenance](https://iceberg.apache.org/docs/latest/maintenance/)
- [Apache Iceberg: Performance Tuning](https://iceberg.apache.org/docs/latest/performance/)

---

## Next Steps

Proceed to **[Lab 8: Third-party Tool Integration](LAB08_Third_Party_Integration.md)** where you will:
- Connect BI tools (Tableau, Power BI)
- Use JDBC/ODBC drivers
- Integrate with Python and Java
- Build applications

---

**Lab Completed!** ✓

Please inform your instructor that you have completed Lab 7 before proceeding to Lab 8.