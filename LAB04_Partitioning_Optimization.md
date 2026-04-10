# Lab 4: Partitioning and Optimization

**Duration:** 60 minutes
**Difficulty:** Intermediate to Advanced
**Prerequisites:** Completion of Labs 1-3
**Last Updated:** April 2026

---

## Lab Objectives

By the end of this lab, you will be able to:
- Implement various partitioning strategies
- Understand partition pruning and its benefits
- Optimize queries using EXPLAIN and EXPLAIN ANALYZE
- Configure table properties for better performance
- Use bucketing for join optimization
- Implement sorting strategies
- Enable and configure result caching

---

## Part 1: Understanding Partitioning Strategies (15 minutes)

### Step 1: Review Current Partitioning

1. Check which tables or views exist in the retail schema:
   ```sql
   SELECT
       table_name,
       table_type
   FROM lab_catalog01.information_schema.tables
   WHERE table_schema = 'retail'
   ORDER BY table_name;
   ```

   **Note:** This shows table names and types, but NOT partitioning information.

2. Identify partitioned tables using SHOW CREATE TABLE:
   ```sql
   -- Check orders table
   SHOW CREATE TABLE lab_catalog01.retail.orders;
   
   -- Check order_items table
   SHOW CREATE TABLE lab_catalog01.retail.order_items;
   
   -- Check customers table
   SHOW CREATE TABLE lab_catalog01.retail.customers;
   ```

   **Look for:** `partitioning = ARRAY[...]` in the output.
   
   **Expected Results:**
   - **orders:** `partitioning = ARRAY['order_date']` ✓ Partitioned
   - **order_items:** `partitioning = ARRAY['bucket(order_id, 16)']` ✓ Partitioned (bucketed)
   - **customers:** No partitioning clause ✗ Not partitioned

3. View file paths to identify partitioning (indirect method):
   ```sql
   -- Partitioned tables have partition values in file paths
   SELECT DISTINCT file_path
   FROM lab_catalog01.retail."orders$files"
   LIMIT 5;
   ```

   **Partitioned path example:** `/orders/data/order_date=2026-01-15/data-file.parquet`
   **Non-partitioned path example:** `/customers/data-file.parquet`

### Step 2: Analyze Partition Distribution

**Note:** The `$partitions` metadata table is not available in Presto. Use alternative methods to analyze partitions.

1. Analyze data distribution by partition column (order_date):
   ```sql
   SELECT
       order_date,
       COUNT(*) as order_count,
       SUM(total_amount) as total_revenue,
       AVG(total_amount) as avg_order_value
   FROM lab_catalog01.retail.orders
   GROUP BY order_date
   ORDER BY order_date DESC;
   ```

2. Check file distribution using $files metadata:
   ```sql
   SELECT
       file_path,
       file_size_in_bytes,
       record_count
   FROM lab_catalog01.retail."orders$files"
   ORDER BY file_path
   LIMIT 10;
   ```

   **Observation:** File paths contain partition information (e.g., `/order_date=2026-01-15/`)

3. Count files per partition (extract from file_path):
   ```sql
   SELECT
       COUNT(*) as total_files,
       SUM(file_size_in_bytes) as total_size_bytes,
       SUM(file_size_in_bytes) / 1024 / 1024 as total_size_mb,
       SUM(record_count) as total_records
   FROM lab_catalog01.retail."orders$files";
   ```

### Step 3: Create Multi-Level Partitioned Table

1. Create a table with year and month partitioning:
   ```sql
   CREATE TABLE lab_catalog01.retail.sales_transactions (
       transaction_id BIGINT,
       customer_id BIGINT,
       product_id BIGINT,
       quantity INTEGER,
       unit_price DECIMAL(10,2),
       total_amount DECIMAL(10,2),
       transaction_date DATE,
       transaction_year INTEGER,
       transaction_month INTEGER,
       transaction_timestamp TIMESTAMP
   )
   WITH (
       format = 'PARQUET',
       partitioning = ARRAY['transaction_year', 'transaction_month'],
       location = 's3a://lab-minio-bucket01/lab_data/retail/sales_transactions'
   );
   ```

2. Insert data with computed partition columns:
   ```sql
   INSERT INTO lab_catalog01.retail.sales_transactions
   SELECT
       CAST(ROW_NUMBER() OVER (ORDER BY o.order_id, oi.order_item_id) AS BIGINT) as transaction_id,
       o.customer_id,
       oi.product_id,
       oi.quantity,
       oi.unit_price,
       oi.line_total as total_amount,
       o.order_date as transaction_date,
       CAST(YEAR(o.order_date) AS INTEGER) as transaction_year,
       CAST(MONTH(o.order_date) AS INTEGER) as transaction_month,
       CAST(o.order_timestamp AS TIMESTAMP) as transaction_timestamp
   FROM lab_catalog01.retail.orders o
   JOIN lab_catalog01.retail.order_items oi ON o.order_id = oi.order_id;
   ```

3. Verify partitions created:
   ```sql
   -- Check partition distribution by querying the data
   SELECT
       transaction_year,
       transaction_month,
       COUNT(*) as transaction_count,
       SUM(total_amount) as total_revenue
   FROM lab_catalog01.retail.sales_transactions
   GROUP BY transaction_year, transaction_month
   ORDER BY transaction_year, transaction_month;
   ```

   **Note:** The `$partitions` metadata table is not available in Presto. Use data queries or `$files` to verify partitions.

4. View partition structure in file paths:
   ```sql
   SELECT DISTINCT file_path
   FROM lab_catalog01.retail."sales_transactions$files"
   ORDER BY file_path
   LIMIT 10;
   ```

   **Expected:** File paths will show partition structure like:
   `/sales_transactions/data/transaction_year=2026/transaction_month=1/data-file.parquet`

---

## Part 2: Partition Pruning and Query Optimization (15 minutes)

### Step 1: Query Without Partition Pruning

1. Run a query that scans all partitions:
   ```sql
   EXPLAIN
   SELECT 
       COUNT(*) as total_transactions,
       SUM(total_amount) as total_revenue
   FROM lab_catalog01.retail.sales_transactions;
   ```

2. Note the number of partitions scanned in the execution plan

### Step 2: Query With Partition Pruning

1. Run a query with partition filter:
   ```sql
   EXPLAIN
   SELECT 
       COUNT(*) as total_transactions,
       SUM(total_amount) as total_revenue
   FROM lab_catalog01.retail.sales_transactions
   WHERE transaction_year = 2026
     AND transaction_month = 3;
   ```

2. Compare the execution plan - fewer partitions should be scanned

3. Execute both queries and compare performance:
   ```sql
   -- Without partition pruning
   SELECT
       COUNT(*) as total_transactions,
       SUM(total_amount) as total_revenue
   FROM lab_catalog01.retail.sales_transactions;

   -- With partition pruning
   SELECT
       COUNT(*) as total_transactions,
       SUM(total_amount) as total_revenue
   FROM lab_catalog01.retail.sales_transactions
   WHERE transaction_year = 2026
     AND transaction_month = 3;
   ```

### Step 3: Analyze the Performance Difference

Taking as example the below output, the analysis is as follows:

#### Example Output 1: Without Partition Pruning (Full Table Scan)
```
TableScan => Estimates: {rows: 312 (7.92kB), cpu: 2,808.00, memory: 0.00, network: 0.00}
```

**Analysis:**
- Presto scanned **ALL partitions** in the table
- Read **312 rows** (the entire table)
- Processed **7.92 KB** of data
- CPU cost: **2,808 units**
- No partition filter applied

#### Example Output 2: With Partition Pruning (Filtered Query)
```
TableScan => Estimates: {rows: 98 (2.49kB), cpu: 882.00, memory: 0.00, network: 0.00}
Partition filter: (transaction_year = 2026) AND (transaction_month = 3)
```

**Analysis:**
- Presto scanned **ONLY 1 partition** (year=2026, month=3)
- Read **98 rows** (only the matching partition)
- Processed **2.49 KB** of data
- CPU cost: **882 units**
- Partition filter successfully applied ✅

#### Performance Comparison

| Metric | Full Scan | Partition Pruning | Improvement |
|--------|-----------|-------------------|-------------|
| **Rows Scanned** | 312 | 98 | **68% fewer** ✅ |
| **Data Size** | 7.92 KB | 2.49 KB | **69% less** ✅ |
| **CPU Cost** | 2,808 | 882 | **69% reduction** ✅ |
| **Partitions Read** | ALL (~3-4) | 1 | **~75% fewer** ✅ |
| **Query Speed** | Baseline | **~3x faster** | **200% improvement** ✅ |

#### Key Observations:

**1. Partition Filter Evidence:**
The EXPLAIN output clearly shows:
```
Partition filter: 8:transaction_year:integer :: [["2026"]] 9:transaction_month:integer :: [["3"]]
```
This confirms Presto successfully identified and applied the partition filter, eliminating unnecessary partition scans.

**2. Resource Efficiency:**
- **68% fewer rows** means less I/O operations
- **69% less data** means reduced network transfer
- **69% lower CPU cost** means faster query execution
- Result: **~3x performance improvement**

**3. Scaling Impact:**

**In this lab (small dataset):**
- 312 rows → 98 rows = **3x faster**
- Noticeable improvement

**In production (large dataset):**
- 1 billion rows → 2.7 million rows = **370x faster**
- Hours → Minutes
- Significant cost savings

**4. Real-World Example:**

Consider a sales table with 5 years of daily partitions:
- **Without partition pruning:** Scan 1,825 partitions (5 years × 365 days)
- **With partition pruning:** Scan 1 partition (today's data)
- **Result:** Query is **1,825x faster!**

#### Best Practices Demonstrated:

✅ **DO:** Filter directly on partition columns
```sql
WHERE transaction_year = 2026 AND transaction_month = 3
```

❌ **DON'T:** Use functions on partition columns (prevents pruning)
```sql
WHERE YEAR(transaction_date) = 2026  -- Presto cannot prune!
```

✅ **DO:** Store partition values as separate columns
```sql
transaction_year INTEGER,  -- Partition column
transaction_month INTEGER  -- Partition column
```

#### Verification Checklist:

1. ✅ Check EXPLAIN output for "Partition filter" line
2. ✅ Compare rows/data size between queries
3. ✅ Verify CPU cost reduction
4. ✅ Confirm actual execution time in Query History

**Expected Results:**
- Query without filter: Slower, scans all data
- Query with filter: Faster, scans only relevant partition
- Performance gap increases with table size

**Key Takeaway:** Partition pruning is one of the most powerful optimization techniques in big data. Always filter on partition columns when possible to achieve dramatic performance improvements and cost savings.

### Step 3: Analyze Query Performance

1. Use EXPLAIN ANALYZE for detailed metrics:
   ```sql
   EXPLAIN ANALYZE
   SELECT 
       transaction_date,
       COUNT(*) as transaction_count,
       SUM(total_amount) as daily_revenue
   FROM lab_catalog01.retail.sales_transactions
   WHERE transaction_year = 2026
     AND transaction_month = 3
   GROUP BY transaction_date
   ORDER BY transaction_date;
   ```

2. Review the output:
   - CPU time
   - Wall time
   - Rows processed
   - Data scanned

---

## Part 3: Bucketing for Join Optimization (15 minutes)

### Step 1: Create Bucketed Tables

**What is Bucketing?**

Bucketing is a data organization technique that distributes rows into a fixed number of "buckets" based on a hash function applied to one or more columns. Think of it as pre-sorting data into numbered bins.

**How Bucketing Works:**
```
customer_id → hash(customer_id) → bucket_number (0-15)

Example:
customer_id: 1001 → hash → bucket 7
customer_id: 1002 → hash → bucket 3
customer_id: 1003 → hash → bucket 7
```

**What We Achieve with Bucketing:**

1. **Optimized Joins** ✅
   - When joining two tables bucketed on the same column (e.g., `customer_id`)
   - Presto knows matching rows are in the same bucket number
   - Eliminates need to shuffle data across the cluster
   - Result: **Faster joins, less network traffic**

2. **Co-located Data** ✅
   - Rows with the same bucket key are stored together
   - Reduces data movement during query execution
   - Improves query performance for aggregations and joins

3. **Predictable Data Distribution** ✅
   - Data is evenly distributed across buckets
   - Prevents data skew (some partitions being much larger than others)
   - Better parallelism during query execution

**Example in This Lab:**

We're creating a bucketed customer table with **16 buckets** based on `customer_id`:
```sql
partitioning = ARRAY['bucket(customer_id, 16)']
```

This means:
- Customer data is distributed into 16 buckets
- Each bucket contains customers whose `customer_id` hashes to that bucket number
- When joining with orders (also bucketed on `customer_id`), Presto can perform a **bucket join**
- Bucket joins are much faster because matching rows are already co-located

**Bucketing vs Partitioning:**

| Feature | Partitioning | Bucketing |
|---------|-------------|-----------|
| **Purpose** | Filter data (skip irrelevant files) | Optimize joins (co-locate data) |
| **Number of divisions** | Variable (based on data) | Fixed (you specify) |
| **Best for** | WHERE clause filtering | JOIN operations |
| **Example** | `PARTITION BY year, month` | `bucket(customer_id, 16)` |

**When to Use Bucketing:**
- ✅ Tables frequently joined on the same column
- ✅ Large tables with expensive joins
- ✅ Need to reduce data shuffling in distributed queries
- ✅ Want predictable data distribution

1. Create a bucketed customer table:
   ```sql
   CREATE TABLE lab_catalog01.retail.customers_bucketed (
       customer_id BIGINT,
       first_name VARCHAR,
       last_name VARCHAR,
       email VARCHAR,
       city VARCHAR,
       state VARCHAR,
       country VARCHAR,
       customer_status VARCHAR
   )
   WITH (
       format = 'PARQUET',
       partitioning = ARRAY['bucket(customer_id, 16)'],
       location = 's3a://lab-minio-bucket01/lab_data/retail/customers_bucketed'
   );
   ```

2. Populate the bucketed table:
   ```sql
   INSERT INTO lab_catalog01.retail.customers_bucketed
   SELECT 
       customer_id,
       first_name,
       last_name,
       email,
       city,
       state,
       country,
       customer_status
   FROM lab_catalog01.retail.customers;
   ```

### Step 2: Compare Join Performance

1. Join without bucketing:
   ```sql
   EXPLAIN ANALYZE
   SELECT 
       c.customer_id,
       c.first_name,
       c.last_name,
       COUNT(o.order_id) as order_count,
       SUM(o.total_amount) as total_spent
   FROM lab_catalog01.retail.customers c
   JOIN lab_catalog01.retail.orders o ON c.customer_id = o.customer_id
   GROUP BY c.customer_id, c.first_name, c.last_name;
   ```

2. Join with bucketing (if both tables are bucketed on join key):
   ```sql
   EXPLAIN ANALYZE
   SELECT 
       c.customer_id,
       c.first_name,
       c.last_name,
       COUNT(o.order_id) as order_count,
       SUM(o.total_amount) as total_spent
   FROM lab_catalog01.retail.customers_bucketed c
   JOIN lab_catalog01.retail.orders o ON c.customer_id = o.customer_id
   GROUP BY c.customer_id, c.first_name, c.last_name;
   ```

3. Compare the execution plans and performance metrics

### Step 3: Analyze the Bucketing Performance Difference

Taking as example the below outputs, the analysis is as follows:

#### Query 1: Without Bucketing (Regular Join)
```
Fragment 1 [HASH]
CPU: 369.13ms, Scheduled: 1.15s, Input: 107 rows (3.78kB)

Fragment 2 [SOURCE] - Orders Table
CPU: 775.51ms, Scheduled: 17.70s, Input: 116 rows (11.37kB)

Fragment 3 [SOURCE] - Customers Table
CPU: 61.23ms, Scheduled: 1.30s, Input: 9 rows (658B), Filtered: 22.22%
```

#### Query 2: With Bucketing (Optimized Join)
```
Fragment 1 [HASH]
CPU: 213.67ms, Scheduled: 386.51ms, Input: 107 rows (3.78kB)

Fragment 2 [SOURCE] - Orders Table
CPU: 704.08ms, Scheduled: 15.32s, Input: 116 rows (11.37kB)

Fragment 3 [SOURCE] - Customers_Bucketed Table
CPU: 59.27ms, Scheduled: 1.53s, Input: 7 rows (6.84kB), Filtered: 0.00%
```

#### Performance Comparison in Simple Terms

**What Changed:**

| Metric | Without Bucketing | With Bucketing | Improvement |
|--------|-------------------|----------------|-------------|
| **Fragment 1 CPU** | 369.13ms | 213.67ms | **42% faster** ✅ |
| **Fragment 1 Scheduled** | 1.15s | 386.51ms | **66% faster** ✅ |
| **Fragment 3 Filtered** | 22.22% | 0.00% | **No waste** ✅ |
| **Fragment 3 Input Size** | 658B | 6.84kB | More efficient read |
| **Overall Join Time** | ~1.15s | ~0.39s | **3x faster** ✅ |

**Key Differences Explained:**

**1. Fragment 1 (Join & Aggregation) - The Main Improvement**
- **Without bucketing:** CPU 369ms, Scheduled 1.15s
- **With bucketing:** CPU 214ms, Scheduled 387ms
- **Why faster?** Bucketing pre-organized the data, so Presto spent less time shuffling and matching rows

**2. Fragment 3 (Customer Table Scan) - Better Data Organization**
- **Without bucketing:**
  - Read 9 rows (658B)
  - Filtered out 22.22% (2 rows were irrelevant)
  - Wasted effort reading unnecessary data
  
- **With bucketing:**
  - Read 7 rows (6.84kB)
  - Filtered 0.00% (all rows were relevant)
  - No wasted reads - bucketing ensured only relevant data was scanned

**3. Fragment 2 (Orders Table) - Similar Performance**
- Both queries scanned orders table similarly
- Slight improvement with bucketing (775ms → 704ms)
- Orders table wasn't bucketed, so less dramatic improvement

**What This Means in Real Terms:**

**Think of it like organizing a library:**

**Without Bucketing (Messy Library):**
```
Books scattered randomly on shelves
To find matching books, you must:
1. Search entire library
2. Check every shelf
3. Filter out irrelevant books (22% waste)
4. Takes 1.15 seconds
```

**With Bucketing (Organized Library):**
```
Books sorted into 16 sections by author ID
To find matching books, you must:
1. Go directly to the right section
2. Check only that section
3. All books there are relevant (0% waste)
4. Takes 0.39 seconds (3x faster!)
```

**Why Bucketing Helped:**

1. **Pre-organized Data** ✅
   - Customer data already sorted into 16 buckets by `customer_id`
   - Presto knew exactly where to find matching customers
   - No need to shuffle data across the cluster

2. **Eliminated Filtering Waste** ✅
   - Without bucketing: Read 9 rows, filtered out 22% (2 rows)
   - With bucketing: Read 7 rows, filtered out 0% (0 rows)
   - Only read exactly what was needed

3. **Faster Join Processing** ✅
   - Fragment 1 CPU: 369ms → 214ms (42% faster)
   - Fragment 1 Scheduled: 1.15s → 387ms (66% faster)
   - Less time spent matching and aggregating

4. **Reduced Network Traffic** ✅
   - Memory estimates: 1,152B → 896B (22% less)
   - Network estimates: 5,328B → 5,072B (5% less)
   - Less data shuffled between nodes

**Real-World Impact:**

**For This Small Lab Dataset:**
- 1.15s → 0.39s = **3x faster**
- Noticeable but not dramatic

**For Production Datasets:**
- Millions of rows
- Complex joins
- **10-50x faster** joins
- **Massive cost savings** on compute resources

**Key Takeaway:** Bucketing is most effective when:
- ✅ Both tables are bucketed on the same join column
- ✅ Tables are large (millions+ rows)
- ✅ Joins are performed frequently
- ✅ You want to minimize data shuffling

In this example, only the customers table was bucketed, so we saw moderate improvements. If the orders table were also bucketed on `customer_id`, the performance gain would be even more dramatic!

---

## Part 4: Sorting and Clustering (10 minutes)

### Step 1: Create Sorted Table

1. Create a table with sorting:
   ```sql
   CREATE TABLE lab_catalog01.retail.customer_orders_sorted (
       customer_id BIGINT,
       order_id BIGINT,
       order_date DATE,
       total_amount DECIMAL(10,2),
       order_status VARCHAR
   )
   WITH (
       format = 'PARQUET',
       partitioning = ARRAY['order_date'],
       sorted_by = ARRAY['customer_id', 'order_id'],
       location = 's3a://lab-minio-bucket01/lab_data/retail/customer_orders_sorted'
   );
   ```

2. Insert sorted data:
   ```sql
   INSERT INTO lab_catalog01.retail.customer_orders_sorted
   SELECT 
       customer_id,
       order_id,
       order_date,
       total_amount,
       order_status
   FROM lab_catalog01.retail.orders
   ORDER BY customer_id, order_id;
   ```

### Step 2: Test Sorted Table Performance

1. Query with filter on sorted column:
   ```sql
   EXPLAIN ANALYZE
   SELECT *
   FROM lab_catalog01.retail.customer_orders_sorted
   WHERE customer_id = 1
   ORDER BY order_id;
   ```

2. Compare with unsorted table:
   ```sql
   EXPLAIN ANALYZE
   SELECT *
   FROM lab_catalog01.retail.orders
   WHERE customer_id = 1
   ORDER BY order_id;
   ```

---

## Part 5: Query Optimization Techniques (15 minutes)

### Step 1: Analyze Query Execution Plans

1. View execution plan for a complex query:
   ```sql
   EXPLAIN
   SELECT 
       c.country,
       c.state,
       COUNT(DISTINCT c.customer_id) as customer_count,
       COUNT(o.order_id) as order_count,
       SUM(o.total_amount) as total_revenue,
       AVG(o.total_amount) as avg_order_value
   FROM lab_catalog01.retail.customers c
   LEFT JOIN lab_catalog01.retail.orders o ON c.customer_id = o.customer_id
   WHERE c.customer_status = 'ACTIVE'
   GROUP BY c.country, c.state
   HAVING SUM(o.total_amount) > 1000
   ORDER BY total_revenue DESC;
   ```

2. Identify optimization opportunities:
   - Partition pruning
   - Predicate pushdown
   - Join strategy
   - Aggregation method

### Step 2: Optimize with Subqueries

**What We're Doing:**

In this step, we're comparing two ways to write the same query - one using a subquery and another using a CTE (Common Table Expression). Both queries do the same thing: get customer information along with their order statistics. However, the CTE version is more readable and can be more efficient.

**The Goal:**
- Get all customer details
- Add their order count and total spending
- Include customers even if they have no orders (LEFT JOIN)

**Step 1: Original Query (Subquery in JOIN)**

This query uses a **subquery** directly inside the JOIN clause:

1. Original query:
   ```sql
   SELECT
       c.*,
       o.order_count,
       o.total_spent
   FROM lab_catalog01.retail.customers c
   LEFT JOIN (
       SELECT
           customer_id,
           COUNT(*) as order_count,
           SUM(total_amount) as total_spent
       FROM lab_catalog01.retail.orders
       GROUP BY customer_id
   ) o ON c.customer_id = o.customer_id;
   ```

**How it works:**
```
Step 1: Subquery runs first (inside the parentheses)
   ↓
   Calculate order_count and total_spent for each customer_id
   ↓
Step 2: Join the result with customers table
   ↓
Step 3: Return all customer columns plus the calculated stats
```

**Pros:**
- ✅ Works correctly
- ✅ Self-contained (everything in one query)

**Cons:**
- ❌ Harder to read (nested logic)
- ❌ Can't reuse the subquery result
- ❌ Less clear what the subquery represents

**Step 2: Optimized with CTE (Common Table Expression)**

This query uses a **CTE** (WITH clause) to name and separate the aggregation logic:

2. Optimized with CTE:
   ```sql
   WITH customer_stats AS (
       SELECT
           customer_id,
           COUNT(*) as order_count,
           SUM(total_amount) as total_spent
       FROM lab_catalog01.retail.orders
       GROUP BY customer_id
   )
   SELECT
       c.*,
       COALESCE(cs.order_count, 0) as order_count,
       COALESCE(cs.total_spent, 0) as total_spent
   FROM lab_catalog01.retail.customers c
   LEFT JOIN customer_stats cs ON c.customer_id = cs.customer_id;
   ```

**How it works:**
```
Step 1: WITH clause creates a named temporary result set
   ↓
   "customer_stats" = aggregated order data per customer
   ↓
Step 2: Main query references the CTE by name
   ↓
Step 3: Join customers with customer_stats
   ↓
Step 4: Use COALESCE to handle NULLs (customers with no orders)
```

**Pros:**
- ✅ **More readable** - logic is separated and named
- ✅ **Reusable** - can reference `customer_stats` multiple times in the query
- ✅ **Better NULL handling** - COALESCE converts NULL to 0 for customers with no orders
- ✅ **Easier to debug** - can test the CTE independently
- ✅ **Self-documenting** - "customer_stats" clearly describes what it contains

**Cons:**
- ❌ Slightly more verbose (but worth it for clarity)

**Key Differences:**

| Aspect | Subquery | CTE |
|--------|----------|-----|
| **Readability** | Nested, harder to follow | Separated, clear flow |
| **Reusability** | Can't reuse | Can reference multiple times |
| **NULL Handling** | Returns NULL | Uses COALESCE for 0 |
| **Debugging** | Must test entire query | Can test CTE separately |
| **Performance** | Same | Same (Presto optimizes both) |

**Why CTE is Better:**

1. **Clarity**: The name "customer_stats" immediately tells you what the data represents
2. **Maintainability**: If you need to change the aggregation logic, it's in one clear place
3. **Flexibility**: You could add more CTEs or reference `customer_stats` multiple times
4. **NULL Safety**: COALESCE ensures customers with no orders show 0 instead of NULL

**Real-World Example:**

Think of it like cooking:

**Subquery approach:**
```
"Mix (flour + eggs + (sugar + butter mixed together)) and bake"
Everything nested, hard to follow
```

**CTE approach:**
```
Step 1: Make frosting = sugar + butter
Step 2: Mix frosting with flour + eggs
Step 3: Bake
Clear steps, easy to follow
```

**Best Practice:** Use CTEs for complex queries with multiple steps or when you need to reference the same aggregation multiple times. They make your SQL more maintainable and easier for others (and future you!) to understand.

### Step 3: Use Appropriate Aggregations

1. Inefficient aggregation:
   ```sql
   -- Counts all rows then filters
   SELECT COUNT(*)
   FROM lab_catalog01.retail.orders
   WHERE order_status = 'DELIVERED';
   ```

2. Efficient aggregation:
   ```sql
   -- Uses partition pruning if available
   SELECT COUNT(*)
   FROM lab_catalog01.retail.orders
   WHERE order_date >= DATE '2026-03-01'
     AND order_date < DATE '2026-04-01'
     AND order_status = 'DELIVERED';
   ```
---

## Verification Checklist

Mark each item as you complete it:

- [ ] Created multi-level partitioned table
- [ ] Demonstrated partition pruning benefits
- [ ] Used EXPLAIN and EXPLAIN ANALYZE
- [ ] Created bucketed tables
- [ ] Compared join performance with/without bucketing
- [ ] Created sorted tables
- [ ] Optimized queries using CTEs

---

## Lab Questions

Answer the following questions:

1. **What is partition pruning and why is it important?**
   
   Answer: _________________

2. **How many buckets did you use for the customers_bucketed table?**
   
   Answer: _________________

3. **What is the difference between EXPLAIN and EXPLAIN ANALYZE?**
   
   Answer: _________________

4. **When should you use bucketing vs partitioning?**
   
   Answer: _________________

5. **What command is used to update table statistics?**
   
   Answer: _________________

---

## Performance Comparison Table

Fill in the execution times for different optimization techniques:

| Query Type | Execution Time | Rows Scanned | Notes |
|------------|---------------|--------------|-------|
| Full table scan | _______ | _______ | No optimization |
| With partition pruning | _______ | _______ | Date filter |
| With bucketing | _______ | _______ | Join optimization |
| With sorting | _______ | _______ | Range query |
| With caching (2nd run) | _______ | _______ | Result cache |

---

## Best Practices Summary

### Partitioning
- ✓ Partition on columns frequently used in WHERE clauses
- ✓ Avoid over-partitioning (target: 128MB - 1GB per partition)
- ✓ Use date/time partitioning for time-series data
- ✓ Consider multi-level partitioning for very large tables
- ✗ Don't partition on high-cardinality columns

### Bucketing
- ✓ Use for join optimization on large tables
- ✓ Bucket on join keys
- ✓ Choose bucket count based on data size (16-256 buckets)
- ✓ Ensure both tables use same bucket count for joins
- ✗ Don't use bucketing for small tables

### Sorting
- ✓ Sort on columns used in ORDER BY and range filters
- ✓ Combine with partitioning for best results
- ✓ Use for time-series data (sort by timestamp)
- ✗ Don't sort on columns with frequent updates

### Query Optimization
- ✓ Use EXPLAIN to understand query plans
- ✓ Use EXPLAIN ANALYZE for performance metrics
- ✓ Filter early in the query (WHERE before JOIN)
- ✓ Use CTEs for complex queries
- ✓ Leverage partition pruning
- ✓ Keep statistics up to date

### Caching
- ✓ Enable for frequently run queries
- ✓ Configure appropriate TTL
- ✓ Monitor cache hit rates
- ✗ Don't cache queries on frequently updated tables

---

## SQL Reference Sheet

### Partitioning Strategies
```sql
-- Date partitioning
partitioning = ARRAY['date_column']

-- Year/Month partitioning
partitioning = ARRAY['year(date_col)', 'month(date_col)']

-- Bucket partitioning
partitioning = ARRAY['bucket(column, 16)']

-- Truncate partitioning
partitioning = ARRAY['truncate(column, 10)']

-- Combined partitioning
partitioning = ARRAY['year(date_col)', 'bucket(id, 16)']
```

### Table Properties
```sql
CREATE TABLE schema.table (...)
WITH (
    format = 'PARQUET',
    partitioning = ARRAY['column'],
    sorted_by = ARRAY['col1', 'col2'],
    location = 's3a://bucket/path'
);
```

### Statistics
```sql
-- Analyze entire table
ANALYZE TABLE schema.table;

-- Analyze specific columns
ANALYZE TABLE schema.table 
COMPUTE STATISTICS FOR COLUMNS col1, col2;

-- Show statistics
SHOW STATS FOR schema.table;
```

### Query Analysis
```sql
-- Show execution plan
EXPLAIN SELECT ...;

-- Show execution plan with costs
EXPLAIN (TYPE DISTRIBUTED) SELECT ...;

-- Analyze actual execution
EXPLAIN ANALYZE SELECT ...;
```

---

## Troubleshooting

### Issue: Partition pruning not working
**Solution:**
- Ensure filter uses partition column exactly
- Check data types match
- Verify partition column is in WHERE clause
- Use EXPLAIN to verify pruning

### Issue: Poor join performance
**Solution:**
- Consider bucketing on join keys
- Ensure statistics are up to date
- Check if tables are co-located
- Verify join type is appropriate

### Issue: Slow aggregations
**Solution:**
- Use partition pruning
- Consider pre-aggregated tables
- Check if GROUP BY columns are indexed
- Verify statistics are current

---

## Additional Resources

- [Presto Query Optimization](https://prestodb.io/docs/current/optimizer/)
- [Apache Iceberg Partitioning](https://iceberg.apache.org/docs/latest/partitioning/)
- [watsonx.data Performance Tuning](https://www.ibm.com/docs/en/watsonxdata)

---

## Next Steps

Proceed to **[Lab 5: Time Travel and Rollback Operations](LAB05_Time_Travel_Rollback.md)** where you will:
- Query historical data using time travel
- Rollback tables to previous states
- Manage table snapshots
- Implement data recovery strategies

---

**Lab Completed!** ✓

Please inform your instructor that you have completed Lab 4 before proceeding to Lab 5.