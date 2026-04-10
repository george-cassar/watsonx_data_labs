# Lab 2: Catalog and Table Creation

**Duration:** 60 minutes  
**Difficulty:** Beginner to Intermediate  
**Prerequisites:** Completion of Lab 1

---

## Lab Objectives

By the end of this lab, you will be able to:
- Create an Apache Iceberg catalog
- Create schemas (databases) within a catalog
- Create tables with various data types
- Understand table properties and formats
- Create external tables
- Manage table metadata

---

## Part 1: Adding Storage and Creating a Catalog (15 minutes)

**Important:** In watsonx.data, you add storage (MinIO bucket) and create an associated catalog in a single workflow. This section guides you through both steps.

### Step 1: Navigate to Infrastructure Manager

1. Login to watsonx.data web console
2. Click on **Infrastructure Manager** in the left navigation
3. You can add storage from:
   - **Add component** button → Select MinIO from Storage section

### Step 2: Select MinIO Storage Type

1. Click **Add component** button

2. In the "Add component" dialog, scroll to the **Storage** section

3. Click on **MinIO** tile
   - Description: "Register a MinIO storage bucket"

4. Click **Next** to proceed to configuration

### Step 3: Configure General Information

In the **General information** section:

1. **Display name:**
   ```
   lab-minio-bucket01
   ```
   This is the friendly name that will appear in the watsonx.data UI.

### Step 4: Configure Storage Connection

In the **Storage configuration** section:

1. **Bucket name:**
   ```
   lab-minio-bucket01
   ```
   This is the actual MinIO bucket name. Should match the display name for consistency.

2. **Endpoint:**
   ```
   https://<minio-service-url>:9000
   ```
   Example:
   ```
   http://ibm-lh-lakehouse-minio-svc.cpd.svc.cluster.local:9000
   ```
   (Obtain the correct endpoint from your instructor)

3. **Access key:**
   ```
   <your-minio-access-key>
   ```
   (Obtain from your instructor or MinIO admin console)

4. **Secret key:**
   ```
   <your-minio-secret-key>
   ```
   (Obtain from your instructor or MinIO admin console)

5. **Connection status:**
   - Click **Test connection** button
   - Wait for "Connection successful" message
   - If connection fails, verify:
     - Endpoint URL is correct and accessible
     - Access key and secret key are valid
     - Network connectivity to MinIO service
     - MinIO service is running

### Step 5: Associate Catalog

In the **Associated catalog** section:

1. **Toggle "Associate Catalog" to ON** (enable the switch)

2. **Type:** Select **Apache Iceberg** from the dropdown

3. **Name:** Enter the catalog name
   ```
   lab_catalog01
   ```
   This creates an Iceberg catalog that will use this MinIO bucket for storage.

4. **Base path:** (Optional)
   ```
   /basepath/
   ```
   Leave blank or enter `/` to use the root of the bucket.
   
   **Note:** Base path restricts catalog operations to a specific folder. If left blank, it defaults to "/" which allows the catalog to use the entire bucket.

5. Review the configuration:
   - Storage: lab-minio-bucket01
   - Catalog: lab_catalog01 (Apache Iceberg)
   - Connection: Tested and successful

### Step 6: Complete the Registration

1. Click **Associate** button (bottom right)

2. Wait for the registration to complete

3. You should see success messages for:
   - Storage bucket registered
   - Catalog created and associated

4. The system will return you to Infrastructure Manager

### Step 7: Verify the Setup

1. **Verify Storage:**
   - Go to **Infrastructure Manager** → **Buckets** tab
   - You should see `lab-minio-bucket01` with status **Active**
   - Click on it to view details

2. **Verify Catalog:**
   - Go to **Infrastructure Manager** → **Catalogs** tab
   - You should see `lab_catalog01` with type **Apache Iceberg**
   - It should show associated with `lab-minio-bucket01`
   - Status should be **Active**

**What you've accomplished:**
- ✅ Added MinIO storage bucket to watsonx.data
- ✅ Created an Apache Iceberg catalog
- ✅ Associated the catalog with the storage bucket
- ✅ The catalog is now ready to store schemas and tables

### Step 3: Verify Bucket Access

1. In the Storage list, click on your newly created `lab-minio-bucket01`

2. You should see:
   - Bucket details (name, type, endpoint)
   - Connection status (Active)

3. Click **Objects** to view the bucket contents
   - You should see an empty bucket or existing folders
   - This confirms the connection is working

### Step 4: Create a Folder in MinIO (Optional)

If you have access to the MinIO console:

1. Open MinIO console in a browser:
   ```
   https://<minio-service-url>:9001
   ```

2. Login with your MinIO credentials

3. Navigate to your bucket (`lab-minio-bucket01`)

4. Create a new folder:
   - Click **Create new path** or **+** button
   - Enter folder name: `lab_data`
   - Click **Create**

5. This folder will be used as the base path for your catalog

**Note:** If you don't have access to MinIO console, the folder will be created automatically when you create the catalog.

### Troubleshooting MinIO Connection

If you encounter connection issues:

**Problem: Connection timeout**
- Solution: Verify the MinIO endpoint URL is correct
- Check if MinIO service is running: `kubectl get pods -n watsonx-data | grep minio`

**Problem: Authentication failed**
- Solution: Verify access key and secret key are correct
- Check MinIO admin console for valid credentials

**Problem: SSL/TLS errors**
- Solution: If using self-signed certificates, you may need to:
  - Add certificate to trusted store
  - Or use HTTP instead of HTTPS (not recommended for production)

**Problem: Bucket not found**
- Solution: Create the bucket in MinIO console first
- Or verify the bucket name matches exactly (case-sensitive)

---

## Part 2: Associate Catalog with Engine and Verify (10 minutes)

Now that you've created the storage and catalog in Part 1, you need to associate the catalog with a query engine (Presto) so you can run queries against it.

### Step 1: Associate Catalog with Presto Engine

1. Navigate to **Infrastructure Manager** → **Catalogs** tab

2. Locate your `lab_catalog01` in the list

3. Click on the catalog name to open its details

4. Click on **Manage associations** or **Associate engines** button

5. In the dialog, select your Presto engine:
   - Check the box next to your Presto engine (e.g., `presto-01`)
   - You may see multiple engines if available

6. Click **Save** or **Associate**

7. Verify the engine is now listed under "Associated engines" in the catalog details

**Why this is important:** A catalog must be associated with at least one engine before you can query the data. The engine provides the compute power to execute SQL queries against the catalog's data.

### Step 2: Verify Catalog and Storage Setup via SQL

1. Navigate to **Query Workspace**

2. Run the following query to list all catalogs:
   ```sql
   SHOW CATALOGS;
   ```

3. Verify that `lab_catalog01` appears in the results

4. Show schemas in the new catalog:
   ```sql
   SHOW SCHEMAS FROM lab_catalog01;
   ```

   You should see only the `information_schema` schema at this point.

---

## Part 3: Creating Schemas (10 minutes)

### Step 1: Create a Schema via SQL

1. In the Query Workspace, create a new schema:
   ```sql
   CREATE SCHEMA lab_catalog01.retail
   WITH (location = 's3a://lab-minio-bucket01/lab_data/retail');
   ```

2. Create additional schemas for our lab:
   ```sql
   CREATE SCHEMA lab_catalog01.staging
   WITH (location = 's3a://lab-minio-bucket01/lab_data/staging');
   
   CREATE SCHEMA lab_catalog01.analytics
   WITH (location = 's3a://lab-minio-bucket01/lab_data/analytics');
   ```

### Step 2: Verify Schema Creation

1. List all schemas in the catalog:
   ```sql
   SHOW SCHEMAS FROM lab_catalog01;
   ```

2. You should see:
   - `retail`
   - `staging`
   - `analytics`

### Step 3: Explore Schema via Data Manager

1. Navigate to **Data Manager**

2. Expand `lab_catalog01`

3. You should see your newly created schemas

---

## Part 4: Creating Tables (20 minutes)

### Step 1: Create a Simple Table

1. Create a customer table:
   ```sql
   CREATE TABLE lab_catalog01.retail.customers (
       customer_id BIGINT,
       first_name VARCHAR,
       last_name VARCHAR,
       email VARCHAR,
       phone VARCHAR,
       address VARCHAR,
       city VARCHAR,
       state VARCHAR,
       zip_code VARCHAR,
       country VARCHAR,
       registration_date DATE,
       last_purchase_date DATE,
       total_purchases DECIMAL(10,2),
       customer_status VARCHAR
   )
   WITH (
       format = 'PARQUET',
       location = 's3a://lab-minio-bucket01/lab_data/retail/customers'
   );
   ```

   **Note:** This table uses the default Merge-On-Read (MOR) mode for Iceberg v2 tables, which:
   - Supports UPDATE and DELETE operations in Presto
   - Provides faster write performance
   - Is suitable for tables that require data modifications
   - Same mode as the orders table for consistency

2. Verify table creation:
   ```sql
   SHOW TABLES FROM lab_catalog01.retail;
   ```

3. View table schema:
   ```sql
   DESCRIBE lab_catalog01.retail.customers;
   ```

### Step 2: Create a Partitioned Table

**Understanding Partitioning:**

Partitioning is a data organization technique that divides a table into separate subdirectories based on the values of one or more columns. Each partition contains data with the same partition key value, creating a hierarchical directory structure.

**What is Partitioning?**
- Divides data into separate directories based on column values
- Each unique value (or combination) creates a new partition
- Organizes data in a hierarchical folder structure
- Example: `partitioning = ARRAY['order_date']` creates one directory per date

**When to Use Partitioning:**

1. **Time-Series Data**: When data has a natural time dimension
   - Examples: order_date, transaction_date, event_timestamp
   - Enables efficient time-range queries
   - Common pattern: daily, monthly, or yearly partitions

2. **Low-Cardinality Columns**: Columns with limited distinct values
   - Examples: country, region, status, category
   - Typically < 10,000 distinct values
   - Prevents creating too many small partitions

3. **Query Patterns**: When queries frequently filter on specific columns
   - WHERE order_date = '2024-01-15'
   - WHERE country = 'USA'
   - Partition pruning skips irrelevant data

4. **Data Lifecycle Management**: When data has retention policies
   - Easy to drop old partitions
   - Efficient archival and deletion
   - Example: Drop partitions older than 7 years

**Why Use Partitioning?**

✅ **Query Performance**: Dramatically faster queries with partition filters
✅ **Partition Pruning**: Skips reading irrelevant partitions entirely
✅ **Data Management**: Easy to add, drop, or archive partitions
✅ **Cost Efficiency**: Reduces data scanned, lowering compute costs
✅ **Maintenance**: Simplifies data lifecycle operations

**Partitioning Strategies:**

| Strategy | Example | Use Case | Partitions Created |
|----------|---------|----------|-------------------|
| **Single Column** | `ARRAY['order_date']` | Time-series queries | One per date |
| **Multi-Column** | `ARRAY['year', 'month']` | Hierarchical time queries | year/month structure |
| **Composite** | `ARRAY['country', 'order_date']` | Geographic + time queries | country/date structure |

**Partition Pruning Example:**

```sql
-- Without partitioning: Scans entire table (1TB)
SELECT * FROM orders WHERE order_date = '2024-01-15';

-- With partitioning: Scans only one partition (~3GB)
-- Reads only: /orders/order_date=2024-01-15/
-- 300x faster! Skips 364 other date partitions
```

**Best Practices:**

1. **Choose Low-Cardinality Columns**: Avoid columns with millions of unique values
2. **Align with Query Patterns**: Partition on frequently filtered columns
3. **Consider Data Volume**: Each partition should have reasonable size (100MB-1GB)
4. **Avoid Over-Partitioning**: Too many small partitions hurt performance
5. **Use Date Partitioning**: Most common and effective for time-series data

**Partitioning vs Bucketing:**

| Aspect | Partitioning | Bucketing |
|--------|-------------|-----------|
| Structure | Creates subdirectories | Single directory, multiple files |
| Best For | Low-cardinality (date, region) | High-cardinality (IDs) |
| Partitions | Variable (one per value) | Fixed number |
| Query Pruning | Skips entire directories | Reads specific buckets |
| File Count | Can be very high | Controlled and fixed |

**Example Use Case:**

For an orders table with 5 years of data:
- **Without partitioning**: One huge directory with millions of files
- **With date partitioning**: 1,825 directories (365 days × 5 years)
- **Benefit**: Query for one day reads only that day's partition
- **Performance**: 1,825x faster for single-day queries

**Directory Structure Created:**

```
orders/
├── order_date=2024-01-01/
│   └── data files
├── order_date=2024-01-02/
│   └── data files
├── order_date=2024-01-03/
│   └── data files
└── ...
```

1. Create an orders table with partitioning:
   ```sql
   CREATE TABLE lab_catalog01.retail.orders (
       order_id BIGINT,
       customer_id BIGINT,
       order_date DATE,
       order_status VARCHAR,
       total_amount DECIMAL(10,2),
       payment_method VARCHAR,
       shipping_address VARCHAR,
       shipping_city VARCHAR,
       shipping_state VARCHAR,
       shipping_zip VARCHAR,
       order_timestamp TIMESTAMP
   )
   WITH (
       format = 'PARQUET',
       partitioning = ARRAY['order_date'],
       location = 's3a://lab-minio-bucket01/lab_data/retail/orders'
   );
   ```

2. Verify the partitioning:
   ```sql
   SHOW CREATE TABLE lab_catalog01.retail.orders;
   ```

### Step 3: Create a Table with Complex Data Types

1. Create a products table with arrays and maps:
   ```sql
   CREATE TABLE lab_catalog01.retail.products (
       product_id BIGINT,
       product_name VARCHAR,
       category VARCHAR,
       subcategory VARCHAR,
       brand VARCHAR,
       price DECIMAL(10,2),
       cost DECIMAL(10,2),
       description VARCHAR,
       specifications MAP(VARCHAR, VARCHAR),
       tags ARRAY(VARCHAR),
       dimensions ROW(length DOUBLE, width DOUBLE, height DOUBLE, weight DOUBLE),
       in_stock BOOLEAN,
       stock_quantity INTEGER,
       created_date DATE,
       last_updated TIMESTAMP
   )
   WITH (
       format = 'PARQUET',
       location = 's3a://lab-minio-bucket01/lab_data/retail/products'
   );
   ```

2. Describe the table to see the complex types:
   ```sql
   DESCRIBE lab_catalog01.retail.products;
   ```

### Step 4: Create a Table with Bucketing

**Understanding Bucketing:**

Bucketing is a data organization technique that distributes data into a fixed number of buckets (files) based on a hash function applied to one or more columns. This is different from partitioning, which creates directories based on column values.

**What is Bucketing?**
- Divides data into a predetermined number of buckets using a hash function
- Each bucket contains a subset of rows with similar hash values
- Creates a fixed number of files regardless of data volume
- Example: `bucket(order_id, 16)` creates 16 buckets based on order_id hash

**When to Use Bucketing:**

1. **High-Cardinality Columns**: When a column has too many unique values for effective partitioning
   - Example: order_id, customer_id, transaction_id
   - Partitioning would create too many small directories

2. **Join Optimization**: When frequently joining tables on the bucketed column
   - Co-located data reduces shuffle operations
   - Improves join performance significantly

3. **Even Data Distribution**: When you need uniform file sizes
   - Prevents data skew issues
   - Ensures balanced query processing

4. **Sampling Queries**: When you need to sample data efficiently
   - Can read specific buckets instead of full table scan

**Why Use Bucketing?**

✅ **Performance**: Faster queries on bucketed columns
✅ **Join Efficiency**: Optimizes joins when both tables use same bucketing
✅ **File Management**: Controls number of files created
✅ **Data Skew Prevention**: Distributes data evenly across buckets
✅ **Scalability**: Works well with large datasets

**Bucketing vs Partitioning:**

| Aspect | Partitioning | Bucketing |
|--------|-------------|-----------|
| Files Created | Variable (based on distinct values) | Fixed number |
| Best For | Low-cardinality columns (date, region) | High-cardinality columns (IDs) |
| Directory Structure | Creates subdirectories | Single directory |
| Query Pruning | Skips entire partitions | Reads specific buckets |
| Use Case | Time-series, geographic data | Transaction data, user data |

**Example Use Case:**

For an order_items table with millions of orders:
- **Without bucketing**: Could create millions of files (one per order)
- **With bucketing**: Creates exactly 16 files, evenly distributed
- **Benefit**: Manageable file count, optimized for joins on order_id

1. Create an order_items table with bucketing:
   ```sql
   CREATE TABLE lab_catalog01.retail.order_items (
       order_item_id BIGINT,
       order_id BIGINT,
       product_id BIGINT,
       quantity INTEGER,
       unit_price DECIMAL(10,2),
       discount_percent DECIMAL(5,2),
       line_total DECIMAL(10,2),
       created_timestamp TIMESTAMP
   )
   WITH (
       format = 'PARQUET',
       partitioning = ARRAY['bucket(order_id, 16)'],
       location = 's3a://lab-minio-bucket01/lab_data/retail/order_items'
   );
   ```

### Step 5: Create a Copy-On-Write (COW) Table

**Understanding COW Tables:**
- COW tables are optimized for read-heavy, insert-only workloads
- Best for dimension tables or reference data that rarely changes
- **Important:** Presto does not support UPDATE/DELETE on COW tables
- For updates, you must use Spark (see Lab 6)

1. Create a product categories reference table with COW mode:
   ```sql
   CREATE TABLE lab_catalog01.retail.product_categories (
       category_id INTEGER,
       category_name VARCHAR,
       category_description VARCHAR,
       parent_category VARCHAR,
       is_active BOOLEAN,
       created_date DATE
   )
   WITH (
       format = 'PARQUET',
       location = 's3a://lab-minio-bucket01/lab_data/retail/product_categories',
       "format-version" = '2',
       "write.delete.mode" = 'copy-on-write',
       "write.update.mode" = 'copy-on-write'
   );
   ```

2. Verify the table was created with COW mode:
   ```sql
   SHOW CREATE TABLE lab_catalog01.retail.product_categories;
   ```

   **Look for these properties:**
   - `"write.delete.mode" = 'copy-on-write'`
   - `"write.update.mode" = 'copy-on-write'`

---

## Part 5: Table Properties and Metadata (10 minutes)

### Step 1: View Table Properties

1. Get detailed table information:
   ```sql
   SELECT * FROM lab_catalog01.information_schema.tables
   WHERE table_schema = 'retail';
   ```

2. View column information:
   ```sql
   SELECT * FROM lab_catalog01.information_schema.columns
   WHERE table_schema = 'retail' 
     AND table_name = 'customers';
   ```

### Step 2: View Iceberg Table Metadata

1. Check table snapshots:
   ```sql
   SELECT * FROM lab_catalog01.retail."customers$snapshots";
   ```

2. View table files:
   ```sql
   SELECT * FROM lab_catalog01.retail."customers$files";
   ```

3. View table history:
   ```sql
   SELECT * FROM lab_catalog01.retail."customers$history";
   ```
   
---

## Part 6: Advanced Table Operations (15 minutes)

### Step 1: Create Table As Select (CTAS)

1. Create a summary table from existing data:
   ```sql
   CREATE TABLE lab_catalog01.analytics.customer_summary
   WITH (
       format = 'PARQUET',
       partitioning = ARRAY['country']
   )
   AS
   SELECT 
       country,
       state,
       COUNT(*) as customer_count,
       AVG(total_purchases) as avg_purchases,
       MAX(last_purchase_date) as latest_purchase,
       CURRENT_DATE as summary_date
   FROM lab_catalog01.retail.customers
   GROUP BY country, state;
   ```

   Note: This will fail if customers table is empty. We'll populate it in Lab 3.

### Step 2: Create Table with Sorted Data

1. Create a table with sorting:
   ```sql
   CREATE TABLE lab_catalog01.retail.customer_transactions (
       transaction_id BIGINT,
       customer_id BIGINT,
       transaction_date DATE,
       transaction_type VARCHAR,
       amount DECIMAL(10,2),
       description VARCHAR
   )
   WITH (
       format = 'PARQUET',
       partitioning = ARRAY['transaction_date'],
       sorted_by = ARRAY['customer_id', 'transaction_date'],
       location = 's3a://lab-minio-bucket01/lab_data/retail/transactions'
   );
   ```

### Step 3: Create a View

1. Create a view for active customers:
   ```sql
   CREATE VIEW lab_catalog01.retail.active_customers AS
   SELECT 
       customer_id,
       first_name,
       last_name,
       email,
       total_purchases,
       last_purchase_date
   FROM lab_catalog01.retail.customers
   WHERE customer_status = 'ACTIVE'
     AND last_purchase_date >= CURRENT_DATE - INTERVAL '90' DAY;
   ```

2. Query the view:
   ```sql
   SELECT * FROM lab_catalog01.retail.active_customers LIMIT 10;
   ```

---

## Part 7: Table Management via Data Manager (5 minutes)

### Step 1: Explore Tables in Data Manager

1. Navigate to **Data Manager**

2. Expand `lab_catalog01` → `retail`

3. Click on the `customers` table

4. Explore the tabs:
   - **Schema** - View column definitions
   - **Data** - Preview data (will be empty until Lab 3)
   - **Details** - Table properties and statistics
   - **Partitions** - Partition information

### Step 2: View Table Statistics

1. In the **Details** tab, observe:
   - Table format (Parquet)
   - Location in object storage
   - Number of files
   - Total size
   - Row count

---

## Verification Checklist

Mark each item as you complete it:

- [ ] Created `lab_catalog01` Iceberg catalog
- [ ] Associated catalog with Presto engine
- [ ] Created `retail`, `staging`, and `analytics` schemas
- [ ] Created `customers` table with basic data types
- [ ] Created `orders` table with date partitioning
- [ ] Created `products` table with complex data types (MAP, ARRAY, ROW)
- [ ] Created `order_items` table with bucketing
- [ ] Created external tables in staging schema
- [ ] Viewed table metadata and properties
- [ ] Added comments to tables and columns
- [ ] Created views
- [ ] Explored tables via Data Manager

---

## Lab Questions

Answer the following questions:

1. **What is the default format for Iceberg tables if not specified?**
   
   Answer: _________________

2. **How many schemas did you create in lab_catalog01?**
   
   Answer: _________________

3. **Which table is partitioned by date?**
   
   Answer: _________________

4. **What is the bucket count for the order_items table?**
   
   Answer: _________________

5. **What metadata tables are available for Iceberg tables?**
   
   Answer: _________________

---

## SQL Reference Sheet

### Create Catalog
```sql
CREATE CATALOG catalog_name
WITH (
    type = 'iceberg',
    warehouse = 's3a://bucket/path'
);
```

### Create Schema
```sql
CREATE SCHEMA catalog.schema_name
WITH (location = 's3a://bucket/path');
```

### Create Table
```sql
CREATE TABLE catalog.schema.table_name (
    column1 TYPE,
    column2 TYPE
)
WITH (
    format = 'PARQUET',
    partitioning = ARRAY['column'],
    location = 's3a://bucket/path'
);
```

### Create Partitioned Table
```sql
-- Date partitioning
partitioning = ARRAY['date_column']

-- Bucket partitioning
partitioning = ARRAY['bucket(column, N)']

-- Truncate partitioning
partitioning = ARRAY['truncate(column, N)']

-- Multiple partitions
partitioning = ARRAY['year(date_col)', 'month(date_col)']
```

### View Table Metadata
```sql
-- Snapshots
SELECT * FROM catalog.schema."table$snapshots";

-- Files
SELECT * FROM catalog.schema."table$files";

-- History
SELECT * FROM catalog.schema."table$history";

-- Manifests
SELECT * FROM catalog.schema."table$manifests";

-- Partitions
SELECT * FROM catalog.schema."table$partitions";
```

---

## Troubleshooting

### Issue: Cannot create catalog
**Solution:**
- Verify you have admin permissions
- Check bucket exists and is accessible
- Ensure bucket path is correct
- Verify engine is running

### Issue: Schema creation fails
**Solution:**
- Check catalog exists and is active
- Verify location path is valid
- Ensure you have write permissions to the bucket

### Issue: Table creation fails
**Solution:**
- Verify schema exists
- Check data types are valid
- Ensure location path doesn't conflict with existing tables
- Verify partitioning syntax is correct

### Issue: Cannot see tables in Data Manager
**Solution:**
- Refresh the page
- Check if catalog is associated with an engine
- Verify you have read permissions
- Ensure tables were created successfully

---

## Best Practices

1. **Naming Conventions:**
   - Use lowercase for catalog, schema, and table names
   - Use underscores to separate words
   - Be descriptive but concise

2. **Partitioning:**
   - Partition on columns frequently used in WHERE clauses
   - Avoid over-partitioning (too many small partitions)
   - Consider data distribution and query patterns

3. **Data Types:**
   - Use appropriate precision for DECIMAL types
   - Use VARCHAR instead of CHAR for variable-length strings
   - Consider using DATE instead of TIMESTAMP when time is not needed

4. **Table Organization:**
   - Group related tables in the same schema
   - Use separate schemas for different data zones (staging, analytics, etc.)
   - Document tables with comments

5. **Storage Format:**
   - Use PARQUET for analytical workloads (default and recommended)
   - Use ORC if migrating from Hive
   - Avoid CSV for large tables (poor performance)

---

## Additional Resources

- [Apache Iceberg Table Spec](https://iceberg.apache.org/spec/)
- [Presto CREATE TABLE Documentation](https://prestodb.io/docs/current/sql/create-table.html)
- [watsonx.data Table Management](https://www.ibm.com/docs/en/watsonxdata)

---

## Next Steps

Proceed to **[Lab 3: Data Ingestion with Presto](LAB03_Data_Ingestion_Presto.md)** where you will:
- Insert data into tables
- Load data from CSV and Parquet files
- Use CTAS to populate tables
- Perform bulk data loading
- Validate data integrity

---

**Lab Completed!** ✓

Please inform your instructor that you have completed Lab 2 before proceeding to Lab 3.