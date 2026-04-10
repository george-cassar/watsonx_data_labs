# Sample Data for watsonx.data Labs

This directory contains sample datasets in both CSV and Parquet formats for use in the watsonx.data training labs.

## 📁 Available Datasets

### 1. **customers.csv / customers.parquet**
Customer master data with demographic and loyalty information.

**Schema:**
- `customer_id` (INTEGER): Unique customer identifier
- `name` (STRING): Customer full name
- `email` (STRING): Customer email address
- `country` (STRING): Customer country
- `city` (STRING): Customer city
- `registration_date` (DATE): Account registration date
- `total_purchases` (DECIMAL): Total purchase amount
- `loyalty_tier` (STRING): Loyalty program tier (Bronze, Silver, Gold, Platinum)

**Records:** 30 customers  
**Use Cases:** Customer analytics, segmentation, loyalty analysis

---

### 2. **orders.csv / orders.parquet**
Order transaction data with product and shipping details.

**Schema:**
- `order_id` (INTEGER): Unique order identifier
- `customer_id` (INTEGER): Foreign key to customers
- `order_date` (DATE): Order placement date
- `product_id` (STRING): Product identifier
- `product_name` (STRING): Product name
- `category` (STRING): Product category
- `quantity` (INTEGER): Quantity ordered
- `unit_price` (DECIMAL): Price per unit
- `total_amount` (DECIMAL): Total order amount
- `status` (STRING): Order status (Delivered, Shipped, Processing)
- `payment_method` (STRING): Payment method used
- `shipping_country` (STRING): Shipping destination country

**Records:** 50 orders  
**Use Cases:** Sales analysis, order tracking, inventory management

---

### 3. **products.csv / products.parquet**
Product catalog with detailed specifications and inventory.

**Schema:**
- `product_id` (STRING): Unique product identifier
- `product_name` (STRING): Product name
- `category` (STRING): Main product category
- `subcategory` (STRING): Product subcategory
- `brand` (STRING): Product brand
- `unit_price` (DECIMAL): Retail price
- `cost_price` (DECIMAL): Cost price
- `stock_quantity` (INTEGER): Current stock level
- `reorder_level` (INTEGER): Reorder threshold
- `supplier_id` (STRING): Supplier identifier
- `weight_kg` (DECIMAL): Product weight in kg
- `dimensions_cm` (STRING): Product dimensions
- `color` (STRING): Product color
- `warranty_months` (INTEGER): Warranty period
- `rating` (DECIMAL): Average customer rating
- `reviews_count` (INTEGER): Number of reviews

**Records:** 43 products  
**Use Cases:** Inventory management, pricing analysis, product performance

---

### 4. **sales_transactions.csv / sales_transactions.parquet**
Detailed payment and transaction records.

**Schema:**
- `transaction_id` (STRING): Unique transaction identifier
- `order_id` (INTEGER): Foreign key to orders
- `customer_id` (INTEGER): Foreign key to customers
- `transaction_date` (DATE): Transaction date
- `transaction_time` (TIME): Transaction time
- `amount` (DECIMAL): Transaction amount
- `currency` (STRING): Currency code
- `payment_method` (STRING): Payment method
- `payment_status` (STRING): Payment status
- `card_type` (STRING): Card type (Visa, Mastercard, etc.)
- `card_last4` (STRING): Last 4 digits of card
- `billing_country` (STRING): Billing country
- `tax_amount` (DECIMAL): Tax amount
- `discount_amount` (DECIMAL): Discount applied
- `shipping_cost` (DECIMAL): Shipping cost
- `total_amount` (DECIMAL): Total transaction amount

**Records:** 50 transactions  
**Use Cases:** Financial analysis, payment processing, revenue tracking

---

## 🔧 File Formats

---

### 5. **external_sales.csv / external_sales.parquet**
External sales data for demonstrating external table creation.

**Schema:**
- `sale_id` (BIGINT): Unique sale identifier
- `sale_date` (DATE): Date of sale
- `product_id` (BIGINT): Product identifier
- `quantity` (INTEGER): Quantity sold
- `amount` (DECIMAL): Sale amount

**Records:** 30 sales transactions  
**Use Cases:** External table creation (Lab 2 Part 5), data integration, external data sources

**Lab Usage:** Used in LAB02 Part 5 Step 1 to create external Parquet table

---

### 6. **csv_imports.csv / csv_imports.parquet**
Generic import data for demonstrating CSV external table creation.

**Schema:**
- `id` (BIGINT): Unique identifier
- `name` (STRING): Name field
- `value` (DOUBLE): Numeric value
- `date_field` (DATE): Date field

**Records:** 30 import records  
**Use Cases:** External CSV table creation (Lab 2 Part 5), CSV data ingestion, data imports

**Lab Usage:** Used in LAB02 Part 5 Step 2 to create external CSV table with header skip


### CSV Files
- **Encoding:** UTF-8
- **Delimiter:** Comma (,)
- **Header:** First row contains column names
- **Use:** Easy to view and edit, compatible with most tools

### Parquet Files
- **Compression:** Snappy
- **Features:** Columnar storage, efficient compression, schema embedded
- **Statistics:** Column statistics included for query optimization
- **Use:** Optimized for analytics, recommended for production workloads

---

## 🚀 Usage in Labs

### Lab 2: Catalog and Table Creation
Use CSV files to create initial tables and understand schema definition.

```sql
-- Example: Create table from CSV
CREATE TABLE iceberg_data.retail.customers (
  customer_id INTEGER,
  name VARCHAR,
  email VARCHAR,
  country VARCHAR,
  city VARCHAR,
  registration_date DATE,
  total_purchases DECIMAL(10,2),
  loyalty_tier VARCHAR
)
WITH (
  format = 'PARQUET',
  location = 's3a://your-bucket/customers/'
);
```

### Lab 3: Data Ingestion with Presto
Load data from CSV files into Iceberg tables.

```sql
-- Example: Insert data from CSV
INSERT INTO iceberg_data.retail.customers
SELECT * FROM csv_catalog.default.customers;
```

### Lab 6: Spark Application Development
Use Parquet files for efficient Spark processing.

```python
# Example: Read Parquet with Spark
df = spark.read.parquet("sample_data/customers.parquet")
df.show()
```

### Lab 7: Data Compaction and Maintenance
Use datasets to practice table maintenance operations including file compaction, manifest rewriting, and orphan file cleanup.

```sql
-- Analyze table health and file structure
-- Perform compaction operations
-- Optimize table layout
```

---

## 🔄 Regenerating Parquet Files

If you need to regenerate the Parquet files from CSV sources:

```bash
cd sample_data
python3 generate_parquet_files.py
```

**Requirements:**
- Python 3.7+
- pandas
- pyarrow

**Installation:**
```bash
pip install pandas pyarrow
```

---

## 📊 Data Relationships

```
customers (1) ──────< (N) orders
                         │
                         │ (1)
                         │
                         ▼
                      (1) sales_transactions

products (1) ──────< (N) orders
```

### Foreign Key Relationships:
- `orders.customer_id` → `customers.customer_id`
- `orders.product_id` → `products.product_id`
- `sales_transactions.order_id` → `orders.order_id`
- `sales_transactions.customer_id` → `customers.customer_id`

---

## 💡 Tips for Lab Exercises

1. **Start with CSV files** for initial exploration and understanding
2. **Use Parquet files** for performance-intensive operations
3. **Practice partitioning** using date columns (order_date, transaction_date)
4. **Experiment with joins** across multiple datasets
5. **Test time travel** by making incremental changes to the data
6. **Implement data quality checks** on required fields and data types
7. **Create aggregations** for business metrics and KPIs

---

## 📝 Data Quality Notes

- All customer emails are unique
- Order IDs and Transaction IDs are sequential
- Product IDs follow format: P001, P002, etc.
- Dates range from January 2024 to March 2024
- All monetary values are in their respective currencies
- No NULL values in primary key columns
- Referential integrity maintained across datasets

---

## 🎯 Learning Objectives

By working with these datasets, you will learn to:

✅ Create and manage Iceberg tables  
✅ Ingest data from multiple formats  
✅ Implement partitioning strategies  
✅ Perform complex analytical queries  
✅ Build data pipelines with Spark  
✅ Implement security and access controls  
✅ Optimize query performance  
✅ Maintain data quality and consistency  

---

## 📚 Additional Resources

- [Apache Iceberg Documentation](https://iceberg.apache.org/)
- [Presto SQL Reference](https://prestodb.io/docs/current/)
- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [Parquet File Format](https://parquet.apache.org/)

---

**Last Updated:** March 2026 
**Version:** 1.0  
**Maintained by:** George Cassar