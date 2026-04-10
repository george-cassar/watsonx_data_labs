# Lab 3: Data Ingestion with Presto

**Duration:** 75 minutes
**Difficulty:** Intermediate
**Prerequisites:** Completion of Lab 1 and Lab 2
**Last Updated:** April 2026

---

## Lab Objectives

By the end of this lab, you will be able to:
- Insert data using INSERT statements
- Use CREATE TABLE AS SELECT (CTAS) for data ingestion
- Perform bulk data loading
- Understand MOR (Merge-On-Read) vs COW (Copy-On-Write) strategies
- Validate data integrity after ingestion

---

## Part 1: Inserting Data with INSERT Statements (15 minutes)

### Step 1: Insert Single Row

1. Navigate to **Query Workspace**

2. Insert a single customer record:
   ```sql
   INSERT INTO lab_catalog01.retail.customers VALUES (
       1,
       'John',
       'Doe',
       'john.doe@email.com',
       '+1-555-0101',
       '123 Main St',
       'New York',
       'NY',
       '10001',
       'USA',
       DATE '2024-01-15',
       DATE '2024-03-20',
       1250.50,
       'ACTIVE'
   );
   ```

3. Verify the insert:
   ```sql
   SELECT * FROM lab_catalog01.retail.customers;
   ```

### Step 2: Insert Multiple Rows

1. Insert multiple customers at once:
   ```sql
   INSERT INTO lab_catalog01.retail.customers VALUES
   (2, 'Jane', 'Smith', 'jane.smith@email.com', '+1-555-0102', 
    '456 Oak Ave', 'Los Angeles', 'CA', '90001', 'USA', 
    DATE '2024-01-20', DATE '2024-03-25', 2100.75, 'ACTIVE'),
   (3, 'Bob', 'Johnson', 'bob.j@email.com', '+1-555-0103',
    '789 Pine Rd', 'Chicago', 'IL', '60601', 'USA',
    DATE '2024-02-01', DATE '2024-03-15', 850.25, 'ACTIVE'),
   (4, 'Alice', 'Williams', 'alice.w@email.com', '+1-555-0104',
    '321 Elm St', 'Houston', 'TX', '77001', 'USA',
    DATE '2024-02-10', DATE '2024-02-28', 450.00, 'INACTIVE'),
   (5, 'Charlie', 'Brown', 'charlie.b@email.com', '+1-555-0105',
    '654 Maple Dr', 'Phoenix', 'AZ', '85001', 'USA',
    DATE '2024-02-15', DATE '2024-03-22', 3200.50, 'ACTIVE');
   ```

2. Verify the count:
   ```sql
   SELECT COUNT(*) as total_customers
   FROM lab_catalog01.retail.customers;
   ```

### Step 3: Insert with Column Specification

1. Insert data specifying only certain columns:
   ```sql
   INSERT INTO lab_catalog01.retail.customers
   (customer_id, first_name, last_name, email, country, registration_date, customer_status)
   VALUES
   (6, 'David', 'Miller', 'david.m@email.com', 'USA', CURRENT_DATE, 'ACTIVE'),
   (7, 'Emma', 'Davis', 'emma.d@email.com', 'USA', CURRENT_DATE, 'ACTIVE');
   ```

2. Query to see NULL values in unspecified columns:
   ```sql
   SELECT customer_id, first_name, last_name, phone, city, total_purchases
   FROM lab_catalog01.retail.customers
   WHERE customer_id IN (6, 7);
   ```

---

## Part 2: Generating Sample Data with SQL (20 minutes)

### Important Note on Data Loading

In this lab, we'll focus on generating sample data using SQL statements and CTAS (CREATE TABLE AS SELECT).

### Step 1: Generate Sample Products Data

1. Insert sample products using SQL:
   ```sql
   INSERT INTO lab_catalog01.retail.products
   (product_id, product_name, category, subcategory, brand, price, cost, in_stock, stock_quantity, created_date, last_updated)
   VALUES
   (101, 'Laptop Pro 15', 'Electronics', 'Computers', 'TechBrand', 1299.99, 850.00, true, 45, CURRENT_DATE, CAST(CURRENT_TIMESTAMP AS TIMESTAMP)),
   (102, 'Wireless Mouse', 'Electronics', 'Accessories', 'TechBrand', 29.99, 12.50, true, 200, CURRENT_DATE, CAST(CURRENT_TIMESTAMP AS TIMESTAMP)),
   (103, 'USB-C Cable', 'Electronics', 'Accessories', 'TechBrand', 19.99, 5.00, true, 500, CURRENT_DATE, CAST(CURRENT_TIMESTAMP AS TIMESTAMP)),
   (104, 'Office Chair', 'Furniture', 'Seating', 'ComfortCo', 299.99, 150.00, true, 30, CURRENT_DATE, CAST(CURRENT_TIMESTAMP AS TIMESTAMP)),
   (105, 'Standing Desk', 'Furniture', 'Desks', 'ComfortCo', 599.99, 300.00, true, 15, CURRENT_DATE, CAST(CURRENT_TIMESTAMP AS TIMESTAMP)),
   (106, 'LED Monitor 27', 'Electronics', 'Displays', 'TechBrand', 349.99, 200.00, true, 60, CURRENT_DATE, CAST(CURRENT_TIMESTAMP AS TIMESTAMP)),
   (107, 'Keyboard Mechanical', 'Electronics', 'Accessories', 'TechBrand', 89.99, 40.00, true, 80, CURRENT_DATE, CAST(CURRENT_TIMESTAMP AS TIMESTAMP)),
   (108, 'Desk Lamp', 'Furniture', 'Lighting', 'ComfortCo', 49.99, 20.00, true, 100, CURRENT_DATE, CAST(CURRENT_TIMESTAMP AS TIMESTAMP)),
   (109, 'Notebook Set', 'Office', 'Stationery', 'WriteCo', 12.99, 5.00, true, 300, CURRENT_DATE, CAST(CURRENT_TIMESTAMP AS TIMESTAMP)),
   (110, 'Pen Pack', 'Office', 'Stationery', 'WriteCo', 8.99, 3.00, true, 500, CURRENT_DATE, CAST(CURRENT_TIMESTAMP AS TIMESTAMP));
   ```

2. Verify the products:
   ```sql
   SELECT COUNT(*) FROM lab_catalog01.retail.products;
   SELECT * FROM lab_catalog01.retail.products LIMIT 5;
   ```

### Step 1b: Insert Data into COW Table (Product Categories)

1. Insert product categories into the COW table:
   ```sql
   INSERT INTO lab_catalog01.retail.product_categories VALUES
   (1, 'Electronics', 'Electronic devices and accessories', NULL, true, CURRENT_DATE),
   (2, 'Computers', 'Desktop and laptop computers', 'Electronics', true, CURRENT_DATE),
   (3, 'Accessories', 'Computer and electronic accessories', 'Electronics', true, CURRENT_DATE),
   (4, 'Displays', 'Monitors and screens', 'Electronics', true, CURRENT_DATE),
   (5, 'Furniture', 'Office and home furniture', NULL, true, CURRENT_DATE),
   (6, 'Seating', 'Chairs and seating solutions', 'Furniture', true, CURRENT_DATE),
   (7, 'Desks', 'Work desks and tables', 'Furniture', true, CURRENT_DATE),
   (8, 'Lighting', 'Lamps and lighting fixtures', 'Furniture', true, CURRENT_DATE),
   (9, 'Office', 'Office supplies and stationery', NULL, true, CURRENT_DATE),
   (10, 'Stationery', 'Writing and paper supplies', 'Office', true, CURRENT_DATE);
   ```

2. Verify the product categories:
   ```sql
   SELECT COUNT(*) FROM lab_catalog01.retail.product_categories;
   SELECT * FROM lab_catalog01.retail.product_categories ORDER BY category_id;
   ```

### Step 2: Generate Sample Orders Data

1. Generate orders using SQL with random data:
   ```sql
   INSERT INTO lab_catalog01.retail.orders
   SELECT
       CAST(ROW_NUMBER() OVER (ORDER BY RANDOM()) AS BIGINT) as order_id,
       CAST((RANDOM() * 7 + 1) AS BIGINT) as customer_id,
       CURRENT_DATE - INTERVAL '1' DAY * CAST((RANDOM() * 90) AS INTEGER) as order_date,
       CASE CAST((RANDOM() * 4) AS INTEGER)
           WHEN 0 THEN 'PENDING'
           WHEN 1 THEN 'PROCESSING'
           WHEN 2 THEN 'SHIPPED'
           ELSE 'DELIVERED'
       END as order_status,
       CAST((RANDOM() * 500 + 50) AS DECIMAL(10,2)) as total_amount,
       CASE CAST((RANDOM() * 3) AS INTEGER)
           WHEN 0 THEN 'CREDIT_CARD'
           WHEN 1 THEN 'DEBIT_CARD'
           ELSE 'PAYPAL'
       END as payment_method,
       '123 Shipping St' as shipping_address,
       'Sample City' as shipping_city,
       'ST' as shipping_state,
       '12345' as shipping_zip,
       CAST(CURRENT_TIMESTAMP - INTERVAL '1' DAY * CAST((RANDOM() * 90) AS INTEGER) AS TIMESTAMP) as order_timestamp
   FROM (SELECT * FROM UNNEST(SEQUENCE(1, 100)));
   ```

2. Verify the orders:
   ```sql
   SELECT COUNT(*) FROM lab_catalog01.retail.orders;

   SELECT order_date, COUNT(*) as order_count
   FROM lab_catalog01.retail.orders
   GROUP BY order_date
   ORDER BY order_date DESC
   LIMIT 10;
   ```

---

## Part 3: Using CREATE TABLE AS SELECT (CTAS) (15 minutes)

### Step 1: Create Aggregated Table with CTAS

1. Create a customer summary table:
   ```sql
   CREATE TABLE lab_catalog01.analytics.customer_summary
   WITH (
       format = 'PARQUET',
       partitioning = ARRAY['country']
   )
   AS
   SELECT 
       c.customer_id,
       c.first_name,
       c.last_name,
       c.email,
       c.city,
       c.state,
       c.country,
       c.registration_date,
       c.customer_status,
       COUNT(o.order_id) as total_orders,
       COALESCE(SUM(o.total_amount), 0) as lifetime_value,
       MAX(o.order_date) as last_order_date,
       CURRENT_DATE as summary_date
   FROM lab_catalog01.retail.customers c
   LEFT JOIN lab_catalog01.retail.orders o ON c.customer_id = o.customer_id
   GROUP BY
       c.customer_id, c.first_name, c.last_name, c.email,
       c.city, c.state, c.country, c.registration_date, c.customer_status;
   ```

2. Query the summary table:
   ```sql
   SELECT * FROM lab_catalog01.analytics.customer_summary
   ORDER BY lifetime_value DESC;
   ```

### Step 2: Create Daily Sales Summary

1. Create a daily sales aggregation:
   ```sql
   CREATE TABLE lab_catalog01.analytics.daily_sales
   WITH (
       format = 'PARQUET',
       partitioning = ARRAY['sale_date']
   )
   AS
   SELECT 
       order_date as sale_date,
       COUNT(DISTINCT customer_id) as unique_customers,
       COUNT(*) as total_orders,
       SUM(total_amount) as total_revenue,
       AVG(total_amount) as avg_order_value,
       MIN(total_amount) as min_order_value,
       MAX(total_amount) as max_order_value
   FROM lab_catalog01.retail.orders
   GROUP BY order_date;
   ```

2. Analyze the daily sales:
   ```sql
   SELECT 
       sale_date,
       total_orders,
       ROUND(total_revenue, 2) as revenue,
       ROUND(avg_order_value, 2) as avg_value
   FROM lab_catalog01.analytics.daily_sales
   ORDER BY sale_date DESC;
   ```

---

## Part 4: Bulk Data Loading (10 minutes)

### Step 1: Generate Bulk Order Items Data

1. Create order items in bulk:
   ```sql
   INSERT INTO lab_catalog01.retail.order_items
   SELECT
       CAST(ROW_NUMBER() OVER (ORDER BY o.order_id, p.product_id) AS BIGINT) as order_item_id,
       o.order_id,
       p.product_id,
       CAST((RANDOM() * 5 + 1) AS INTEGER) as quantity,
       p.price as unit_price,
       CAST((RANDOM() * 20) AS DECIMAL(5,2)) as discount_percent,
       CAST(p.price * CAST((RANDOM() * 5 + 1) AS INTEGER) *
           (1 - CAST((RANDOM() * 20) AS DECIMAL(5,2)) / 100) AS DECIMAL(10,2)) as line_total,
       CAST(o.order_timestamp AS TIMESTAMP) as created_timestamp
   FROM lab_catalog01.retail.orders o
   CROSS JOIN lab_catalog01.retail.products p
   WHERE RANDOM() < 0.3  -- 30% chance of including each product in each order
   LIMIT 500;
   ```

2. Verify the bulk insert:
   ```sql
   SELECT COUNT(*) as total_items FROM lab_catalog01.retail.order_items;

   SELECT 
       order_id,
       COUNT(*) as items_count,
       SUM(line_total) as order_total
   FROM lab_catalog01.retail.order_items
   GROUP BY order_id
   ORDER BY order_total DESC
   LIMIT 10;
   ```

---

## Part 5: Understanding MOR vs COW (10 minutes)

### Understanding Iceberg Metadata Tables

Apache Iceberg provides special metadata tables that allow you to inspect table internals. These tables are accessed using the `$` prefix:

#### **`$properties` - Table Properties**
Shows all configuration properties for the table, including write modes, format settings, and partitioning.

```sql
SELECT * FROM lab_catalog01.retail."orders$properties";
```

**Key Properties to Look For:**
- `write.delete.mode` - How deletes are handled (merge-on-read or copy-on-write)
- `write.update.mode` - How updates are handled (merge-on-read or copy-on-write)
- `write.format.default` - File format (PARQUET, ORC, AVRO)
- `format-version` - Iceberg table format version (1 or 2)

#### **`$files` - Data Files**
Lists all data files in the table with their metadata.

```sql
SELECT
    file_path,
    file_size_in_bytes,
    record_count
FROM lab_catalog01.retail."orders$files"
ORDER BY file_path;
```

**Columns Available:**
- `file_path` - Full path to the data file (includes partition information in the path)
- `file_size_in_bytes` - Size of the file
- `record_count` - Number of records in the file
- `file_format` - Format of the file (PARQUET, ORC, etc.)

**Note:** For partitioned tables like orders, the partition values are embedded in the `file_path` (e.g., `/orders/data/order_date=2024-01-15/data-file.parquet`).

#### **`$snapshots` - Table Snapshots**
Shows the history of all table operations (inserts, updates, deletes).

```sql
SELECT
    committed_at,
    snapshot_id,
    parent_id,
    operation,
    summary
FROM lab_catalog01.retail."orders$snapshots"
ORDER BY committed_at DESC;
```

**Columns Available:**
- `committed_at` - Timestamp when snapshot was created
- `snapshot_id` - Unique identifier for the snapshot
- `parent_id` - Previous snapshot ID (for tracking history)
- `operation` - Type of operation (append, overwrite, delete, replace)
- `summary` - JSON with operation details (records added/deleted, files added/removed)

**Other Metadata Tables:**
- `$history` - Simplified view of table history
- `$manifests` - Lists manifest files
- `$partitions` - Shows partition information
- `$refs` - Shows branches and tags (Iceberg v2)

---

### Step 1: Check Current Write Mode

1. View table properties to see write mode:
   ```sql
   SHOW CREATE TABLE lab_catalog01.retail.orders;
   ```

   **Expected Output:** You should see `"write.delete.mode" = 'merge-on-read'` and `"write.update.mode" = 'merge-on-read'` in the table properties.

### Step 2: Verify Orders Table Write Mode and Understand MOR

1. First, verify the orders table write mode:
   ```sql
   SHOW CREATE TABLE lab_catalog01.retail.orders;
   ```

   **Look for these properties in the output:**
   - `"write.delete.mode" = 'merge-on-read'` ✓
   - `"write.update.mode" = 'merge-on-read'` ✓
   
   **Expected Result:** The orders table should be configured with Merge-On-Read (MOR).

2. Query the properties table to confirm:
   ```sql
   SELECT key, value
   FROM lab_catalog01.retail."orders$properties"
   WHERE key IN ('write.delete.mode', 'write.update.mode', 'format-version');
   ```

   **Expected Output:**
   | key | value |
   |-----|-------|
   | write.delete.mode | merge-on-read |
   | write.update.mode | merge-on-read |

**Understanding Merge-On-Read (MOR):**
- Writes delta files for updates and deletes
- Faster writes (no need to rewrite entire data files)
- Slightly slower reads (must merge delta files on read)
- Less storage during writes
- Suitable for write-heavy workloads

3. Perform an update to see MOR behavior:
   ```sql
   UPDATE lab_catalog01.retail.orders
   SET order_status = 'DELIVERED'
   WHERE order_status = 'SHIPPED' AND order_date < CURRENT_DATE - INTERVAL '7' DAY;
   ```

2. Check the files created:
   ```sql
   SELECT
       file_path,
       file_size_in_bytes,
       record_count
   FROM lab_catalog01.retail."orders$files"
   ORDER BY file_path;
   ```

   **Note:** With MOR, you may see multiple files per partition. Delete operations create position delete files that are merged during reads, but these are managed internally by Iceberg and not directly queryable via `$delete_files` in Presto.

3. View table snapshots to see MOR operations:
   ```sql
   SELECT
       committed_at,
       snapshot_id,
       operation,
       summary
   FROM lab_catalog01.retail."orders$snapshots"
   ORDER BY committed_at DESC
   LIMIT 10;
   ```

### Step 3: Verify Customers Table Write Mode

1. First, verify the customers table write mode:
   ```sql
   SHOW CREATE TABLE lab_catalog01.retail.customers;
   ```

   **Look for these properties in the output:**
   - `"write.delete.mode" = 'merge-on-read'` ✓
   - `"write.update.mode" = 'merge-on-read'` ✓
   
   **Expected Result:** The customers table is configured with Merge-On-Read (MOR) mode, same as the orders table.

2. Query the properties table to confirm:
   ```sql
   SELECT key, value
   FROM lab_catalog01.retail."customers$properties"
   WHERE key IN ('write.delete.mode', 'write.update.mode', 'format-version');
   ```

   **Expected Output:**
   | key | value |
   |-----|-------|
   | write.delete.mode | merge-on-read |
   | write.update.mode | merge-on-read |

**Why Both Tables Use MOR:**
- **Presto Compatibility:** MOR is the only mode that supports UPDATE/DELETE in Presto
- **Flexibility:** Both tables may need updates (customer status, order status)
- **Consistency:** Using the same mode for all tables simplifies operations

3. Test UPDATE operations on customers table:
   ```sql
   -- Update customer status (MOR supports this in Presto)
   UPDATE lab_catalog01.retail.customers
   SET customer_status = 'PREMIUM'
   WHERE total_purchases > 2000;
   
   -- Check the files created
   SELECT
       file_path,
       file_size_in_bytes,
       record_count
   FROM lab_catalog01.retail."customers$files"
   ORDER BY file_path;
   ```

   **Observation:** With MOR, UPDATE operations work in Presto. You may see multiple files as updates create position delete files that are merged during reads.

4. View snapshots to see MOR operations:
   ```sql
   SELECT
       committed_at,
       snapshot_id,
       operation,
       summary
   FROM lab_catalog01.retail."customers$snapshots"
   ORDER BY committed_at DESC
   LIMIT 10;
   ```

   **Observation:** Each UPDATE operation creates a new snapshot. The `operation` column will show 'overwrite' or 'delete' for updates.

### Step 4: Understand Copy-On-Write (COW) with Product Categories Table

1. First, verify the product_categories table write mode:
   ```sql
   SHOW CREATE TABLE lab_catalog01.retail.product_categories;
   ```

   **Look for these properties in the output:**
   - `"write.delete.mode" = 'copy-on-write'` ✓
   - `"write.update.mode" = 'copy-on-write'` ✓
   
   **Expected Result:** The product_categories table is configured with Copy-On-Write (COW) mode.

2. Query the properties table to confirm:
   ```sql
   SELECT key, value
   FROM lab_catalog01.retail."product_categories$properties"
   WHERE key IN ('write.delete.mode', 'write.update.mode', 'format-version');
   ```

   **Expected Output:**
   | key | value |
   |-----|-------|
   | write.delete.mode | copy-on-write |
   | write.update.mode | copy-on-write |
   | format-version | 2 |

**Understanding Copy-On-Write (COW):**
- Rewrites entire data files on updates
- Better read performance (no merge needed)
- Slower writes (must rewrite full files)
- Suitable for read-heavy, insert-only workloads
- **Limitation:** Presto does NOT support UPDATE/DELETE on COW tables

**Why Product Categories Uses COW:**
- Reference/dimension table with stable data
- Mostly read operations (lookups, joins)
- Rare inserts (new categories added infrequently)
- No updates needed in normal operations
- Optimized for analytical queries

3. Test INSERT operations on COW table (this works):
   ```sql
   -- Insert a new category (COW supports inserts in Presto)
   INSERT INTO lab_catalog01.retail.product_categories VALUES
   (11, 'Sports', 'Sports and fitness equipment', NULL, true, CURRENT_DATE);
   
   -- Verify the insert
   SELECT * FROM lab_catalog01.retail.product_categories
   WHERE category_id = 11;
   ```

4. Check the files created by COW:
   ```sql
   SELECT
       file_path,
       file_size_in_bytes,
       record_count
   FROM lab_catalog01.retail."product_categories$files"
   ORDER BY file_path;
   ```

   **Observation:** With COW, INSERT operations create new data files. No delete files are created - all data is in complete data files.

5. View snapshots to see COW operations:
   ```sql
   SELECT
       committed_at,
       snapshot_id,
       operation,
       summary
   FROM lab_catalog01.retail."product_categories$snapshots"
   ORDER BY committed_at DESC
   LIMIT 10;
   ```

   **Observation:** Each INSERT operation creates a new snapshot with `operation` = 'append'.

6. **Demonstrate COW Limitation - UPDATE fails in Presto:**
   ```sql
   -- This will FAIL with COW table in Presto
   UPDATE lab_catalog01.retail.product_categories
   SET is_active = false
   WHERE category_id = 11;
   ```

   **Expected Error:**
   ```
   Iceberg table updates require at least format version 2 and update mode must be merge-on-read
   ```

   **Solution:** To update COW tables, use Spark (see Lab 6):
   ```python
   # This works in Spark
   spark.sql("""
       UPDATE lab_catalog01.retail.product_categories
       SET is_active = false
       WHERE category_id = 11
   """)
   ```

### Step 5: Compare MOR vs COW

| Aspect | Merge-On-Read (MOR) | Copy-On-Write (COW) |
|--------|---------------------|---------------------|
| **Write Performance** | ✅ Fast (delta files) | ❌ Slower (rewrites files) |
| **Read Performance** | ❌ Slightly slower (merge) | ✅ Fast (no merge) |
| **Storage During Write** | ✅ Less (delta only) | ❌ More (full rewrite) |
| **File Count** | ❌ More files | ✅ Fewer files |
| **Best For** | Write-heavy workloads | Read-heavy workloads |
| **Update/Delete in Presto** | ✅ Supported | ❌ NOT Supported |
| **Update/Delete in Spark** | ✅ Supported | ✅ Supported |
| **Compaction Need** | ✅ Yes (periodic) | ❌ Less frequent |

### Step 6: Lab Table Architecture Summary

| Table | Mode | Reason | Presto UPDATE/DELETE |
|-------|------|--------|---------------------|
| **orders** | MOR | Frequent status updates needed | ✅ Yes |
| **customers** | MOR | May need status/total updates | ✅ Yes |
| **product_categories** | COW | Reference data, read-only | ❌ No (use Spark) |

### Step 7: When to Use Each Mode

**Use Merge-On-Read (MOR) when:**
- High frequency of updates/deletes
- Write performance is critical
- Partitioned tables with frequent updates
- Real-time data ingestion
- **Examples:** orders, customers, transactions, event logs

**Use Copy-On-Write (COW) when:**
- Read performance is critical
- Insert-only workloads (no updates needed)
- Reference/dimension tables
- Analytical queries dominate
- Can use Spark for rare updates
- **Examples:** product_categories, country codes, lookup tables

---

## Verification Checklist

Mark each item as you complete it:

- [ ] Inserted single and multiple rows using INSERT
- [ ] Generated sample products and orders data
- [ ] Created tables using CTAS
- [ ] Performed bulk data loading
- [ ] Understood MOR vs COW strategies
- [ ] Validated row counts across tables

---

## Lab Questions

Answer the following questions:

1. **How many customers did you insert into the customers table?**
   
   Answer: _________________

2. **What is the default write mode for Iceberg tables (MOR or COW)?**
   
   Answer: _________________

3. **Which format is better for analytical queries: CSV or Parquet?**
   
   Answer: _________________

4. **What is the total number of order items created?**
   
   Answer: _________________

5. **What is the advantage of using CTAS over INSERT INTO?**
   
   Answer: _________________

---

## SQL Reference Sheet

### INSERT Statements
```sql
-- Single row
INSERT INTO table VALUES (val1, val2, ...);

-- Multiple rows
INSERT INTO table VALUES
(val1, val2, ...),
(val1, val2, ...);

-- With column specification
INSERT INTO table (col1, col2) VALUES (val1, val2);

-- From SELECT
INSERT INTO table SELECT * FROM source_table;
```

### CTAS
```sql
CREATE TABLE new_table
WITH (
    format = 'PARQUET',
    partitioning = ARRAY['column']
)
AS
SELECT * FROM source_table;
```

---

## Best Practices

1. **Batch Inserts:**
   - Use multi-row INSERT statements instead of single-row inserts
   - Batch size: 1000-10000 rows per statement
   - Use CTAS for large data loads

2. **File Formats:**
   - Use Parquet for production tables (best compression and performance)
   - For loading CSV/Parquet files, use Spark (Lab 6)
   - Presto is best for SQL-based data transformations

3. **Performance:**
   - Use partitioning for large tables
   - Monitor file sizes (target: 128MB - 1GB per file)
   - Avoid too many small files
   - Use appropriate data types

4. **Error Handling:**
   - Test with small datasets first
   - Use staging tables for validation
   - Keep source data until validation is complete
   - Log ingestion metrics

---

## Troubleshooting

### Issue: INSERT fails with "Table not found"
**Solution:**
- Verify catalog and schema names
- Check table exists: `SHOW TABLES FROM catalog.schema`
- Ensure catalog is associated with engine

### Issue: Need to load data from CSV/Parquet files
**Solution:**
- Use Apache Spark for file-based data loading
- See Lab 6: Spark Application Development
- Presto is designed for SQL queries, not file ingestion
- Use Spark for ETL, Presto for analytics

### Issue: Slow INSERT performance
**Solution:**
- Use batch inserts instead of single rows
- Consider using CTAS for large datasets
- Check if table is over-partitioned
- Monitor file sizes

### Issue: Data validation fails
**Solution:**
- Check source data quality
- Verify data type conversions
- Look for NULL values
- Check for duplicates in source

---

## Additional Resources

- [Presto INSERT Documentation](https://prestodb.io/docs/current/sql/insert.html)
- [Apache Iceberg Write Operations](https://iceberg.apache.org/docs/latest/writes/)
- [watsonx.data Data Loading Guide](https://www.ibm.com/docs/en/watsonxdata)

---

## Next Steps

Proceed to **[Lab 4: Partitioning and Optimization](LAB04_Partitioning_Optimization.md)** where you will:
- Implement advanced partitioning strategies
- Optimize query performance
- Analyze query execution plans
- Tune table properties for better performance

---

**Lab Completed!** ✓

Please inform your instructor that you have completed Lab 3 before proceeding to Lab 4.