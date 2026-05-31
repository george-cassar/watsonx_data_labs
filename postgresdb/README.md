# PostgreSQL on OpenShift for watsonx.data Labs

Complete PostgreSQL deployment on OpenShift with sample retail database for watsonx.data training labs.

## 📁 Directory Structure

```
openshift-yaml/
├── README.md                    # This file - Complete documentation
├── 01-namespace.yaml           # Creates postgresdb project
├── 02-secret.yaml              # PostgreSQL credentials
├── 03-pvc.yaml                 # 10Gi persistent storage
├── 04-deployment.yaml          # PostgreSQL 15 deployment
├── 05-service.yaml             # ClusterIP service
├── 06-configmap.yaml           # PostgreSQL configuration
└── sql-scripts/
    ├── 01-create-schema.sql    # Database schema creation
    ├── 02-load-data.sql        # Sample data loading
    └── 03-sample-queries.sql   # Example queries (50+)
```

---

## 🚀 Quick Start Guide

### Step 1: Deploy PostgreSQL on OpenShift

```bash
# Navigate to openshift-yaml directory
cd openshift-yaml

# Deploy all resources
oc apply -f 01-namespace.yaml
oc apply -f 02-secret.yaml
oc apply -f 03-pvc.yaml
oc apply -f 04-deployment.yaml
oc apply -f 05-service.yaml
oc apply -f 06-configmap.yaml

# Or apply all at once
oc apply -f .

# Wait for pod to be ready
oc wait --for=condition=ready pod -l app=postgresql -n postgresdb --timeout=300s
```

### Step 2: Verify Deployment

```bash
# Switch to the postgresdb project
oc project postgresdb

# Check all resources
oc get all

# Check PVC status
oc get pvc

# Check pod logs
oc logs -f deployment/postgres

# Test connection
oc exec -it deployment/postgres -- psql -U postgres -c "SELECT version();"
```

### Step 3: Load Database Schema and Data

#### Option A: Copy and Execute Scripts in Pod

```bash
# Get the pod name
POD_NAME=$(oc get pod -l app=postgresql -n postgresdb -o jsonpath='{.items[0].metadata.name}')

# Copy SQL scripts to the pod
oc cp sql-scripts/01-create-schema.sql postgresdb/$POD_NAME:/tmp/
oc cp sql-scripts/02-load-data.sql postgresdb/$POD_NAME:/tmp/
oc cp sql-scripts/03-sample-queries.sql postgresdb/$POD_NAME:/tmp/

# Execute the scripts
oc exec -it deployment/postgres -n postgresdb -- psql -U postgres -d postgresdb -f /tmp/01-create-schema.sql
oc exec -it deployment/postgres -n postgresdb -- psql -U postgres -d postgresdb -f /tmp/02-load-data.sql
oc exec -it deployment/postgres -n postgresdb -- psql -U postgres -d postgresdb -f /tmp/03-sample-queries.sql
```

#### Option B: Port Forward and Execute Locally

```bash
# Port forward to access PostgreSQL locally
oc port-forward -n postgresdb svc/postgres-service 5432:5432 &

# In another terminal, run the scripts
psql -h localhost -U postgres -d postgresdb -f sql-scripts/01-create-schema.sql
psql -h localhost -U postgres -d postgresdb -f sql-scripts/02-load-data.sql
psql -h localhost -U postgres -d postgresdb -f sql-scripts/03-sample-queries.sql
```

#### Option C: Interactive Execution

```bash
# Connect to PostgreSQL interactively
oc exec -it deployment/postgres -n postgresdb -- psql -U postgres -d postgresdb

# Then copy and paste SQL commands from each file
```

---

## 📦 OpenShift Resources

### 1. Namespace (01-namespace.yaml)
Creates dedicated `postgresdb` project/namespace.

### 2. Secret (02-secret.yaml)
**Default Credentials:**
- **Username:** postgres
- **Password:** postgres123
- **Database:** postgresdb

⚠️ **IMPORTANT:** Change these credentials in production!

### 3. PersistentVolumeClaim (03-pvc.yaml)
- **Size:** 20Gi
- **Access Mode:** ReadWriteOnce
- **Storage Class:** Default (uses cluster default)

### 4. Deployment (04-deployment.yaml)
- **Image:** postgres:15
- **Replicas:** 1
- **Resources:**
  - Memory: 256Mi request, 512Mi limit
  - CPU: 250m request, 500m limit
- **Health Checks:**
  - Liveness probe: 30s initial delay
  - Readiness probe: 5s initial delay

### 5. Service (05-service.yaml)
- **Type:** ClusterIP
- **Port:** 5432
- **Internal DNS:** `postgres-service.postgresdb.svc.cluster.local`

### 6. ConfigMap (06-configmap.yaml)
Optional PostgreSQL configuration tuning parameters.

---

## 💾 Database Schema

### Tables Created (retail schema)

1. **customers** - Customer master data
   - 30 sample records
   - Fields: customer_id, name, email, country, city, registration_date, total_purchases, loyalty_tier

2. **products** - Product catalog
   - 20 sample records
   - Fields: product_id, product_name, category, subcategory, brand, unit_price, cost_price, stock_quantity, etc.

3. **orders** - Order transactions
   - 30 sample records
   - Fields: order_id, customer_id, order_date, product_id, quantity, total_amount, status, payment_method, etc.

4. **sales_transactions** - Payment records
   - 30 sample records
   - Fields: transaction_id, order_id, customer_id, transaction_date, amount, currency, payment_status, etc.

5. **external_sales** - External sales data
   - 30 sample records
   - Fields: sale_id, sale_date, product_id, quantity, amount

6. **csv_imports** - Generic import data
   - 30 sample records
   - Fields: id, name, value, date_field

### Entity Relationships

```
customers (1) ──────< (N) orders
                         │
                         │ (1)
                         │
                         ▼
                      (1) sales_transactions

products (1) ──────< (N) orders
```

### Pre-created Views

1. **customer_order_summary** - Customer order metrics
2. **product_sales_performance** - Product sales analytics
3. **daily_sales_summary** - Daily sales aggregations

---

## 🔍 SQL Scripts Overview

### 01-create-schema.sql
Creates complete database schema:
- `retail` schema
- 6 tables with proper data types
- Indexes for query optimization
- Foreign key constraints
- Auto-update triggers for timestamps
- 3 analytical views

### 02-load-data.sql
Loads sample data matching watsonx.data lab CSV files:
- 30 customers from various countries
- 20 products (Electronics & Furniture)
- 30 orders with different statuses
- 30 sales transactions with various payment methods
- 30 external sales records
- 30 CSV import records

### 03-sample-queries.sql
50+ example queries organized by category:
- **Basic Queries:** Filtering, counting, simple aggregations
- **Aggregation Queries:** Sales by country/category, monthly trends
- **Join Queries:** Customer order history, product performance
- **Advanced Analytics:** Customer segmentation, profitability analysis
- **Window Functions:** Rankings, running totals, moving averages
- **Subqueries & CTEs:** Complex analytical queries
- **Data Quality Checks:** Orphaned records, consistency checks
- **Business Intelligence:** Retention analysis, inventory health

---

## 💡 Usage Examples

### Connect to PostgreSQL

```bash
# From within the cluster
oc exec -it deployment/postgres -n postgresdb -- psql -U postgres -d postgresdb

# Connection string for applications
postgresql://postgres:postgres123@postgres-service.postgresdb.svc.cluster.local:5432/postgresdb
```

### Example Query: Top Customers

```sql
SELECT 
    c.customer_id,
    c.name,
    c.country,
    COUNT(o.order_id) as order_count,
    SUM(o.total_amount) as total_spent
FROM retail.customers c
INNER JOIN retail.orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name, c.country
ORDER BY total_spent DESC
LIMIT 10;
```

### Example Query: Product Inventory Status

```sql
SELECT 
    product_id,
    product_name,
    stock_quantity,
    reorder_level,
    CASE 
        WHEN stock_quantity = 0 THEN 'Out of Stock'
        WHEN stock_quantity < reorder_level THEN 'Low Stock'
        ELSE 'In Stock'
    END as status
FROM retail.products
ORDER BY stock_quantity;
```

### Example Query: Monthly Revenue Trend

```sql
SELECT 
    TO_CHAR(order_date, 'YYYY-MM') as month,
    COUNT(order_id) as orders,
    SUM(total_amount) as revenue
FROM retail.orders
GROUP BY TO_CHAR(order_date, 'YYYY-MM')
ORDER BY month;
```

---

## ⚙️ Customization

### Change Storage Size

Edit `03-pvc.yaml`:
```yaml
resources:
  requests:
    storage: 20Gi  # Change to desired size
```

### Change Credentials

Edit `02-secret.yaml`:
```yaml
stringData:
  POSTGRES_USER: myuser
  POSTGRES_PASSWORD: mypassword
  POSTGRES_DB: mydatabase
```

### Adjust Resources

Edit `04-deployment.yaml`:
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Add Custom Tables

Edit `sql-scripts/01-create-schema.sql`:
```sql
CREATE TABLE IF NOT EXISTS retail.your_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Load Custom Data

Edit `sql-scripts/02-load-data.sql`:
```sql
INSERT INTO retail.your_table (name) VALUES
('Record 1'),
('Record 2'),
('Record 3');
```

---

## 🔧 Maintenance

### Backup Database

```bash
# Backup entire database
oc exec -it deployment/postgres -n postgresdb -- \
  pg_dump -U postgres postgresdb > backup.sql

# Backup specific schema
oc exec -it deployment/postgres -n postgresdb -- \
  pg_dump -U postgres -n retail postgresdb > retail_backup.sql
```

### Restore Database

```bash
# Restore from backup
oc exec -i deployment/postgres -n postgresdb -- \
  psql -U postgres postgresdb < backup.sql
```

### Reset Database

```sql
-- Drop all tables (careful!)
DROP SCHEMA retail CASCADE;

-- Then re-run 01-create-schema.sql and 02-load-data.sql
```

### Clear Data Only

```sql
-- Clear data but keep schema
TRUNCATE TABLE retail.sales_transactions CASCADE;
TRUNCATE TABLE retail.orders CASCADE;
TRUNCATE TABLE retail.customers CASCADE;
TRUNCATE TABLE retail.products CASCADE;
TRUNCATE TABLE retail.external_sales CASCADE;
TRUNCATE TABLE retail.csv_imports CASCADE;

-- Then re-run 02-load-data.sql
```

---

## 🐛 Troubleshooting

### Pod Not Starting

```bash
# Check pod events
oc describe pod -l app=postgresql -n postgresdb

# Check logs
oc logs -l app=postgresql -n postgresdb

# Check deployment status
oc get deployment postgres -n postgresdb
```

### PVC Not Binding

```bash
# Check PVC status
oc describe pvc postgres-pvc -n postgresdb

# Check available storage classes
oc get storageclass

# Check persistent volumes
oc get pv
```

### Connection Issues

```bash
# Check service
oc get svc postgres-service -n postgresdb

# Test connection from within cluster
oc run -it --rm test-connection --image=postgres:15 --restart=Never -n postgresdb -- \
  pg_isready -h postgres-service.postgresdb.svc.cluster.local -p 5432

# Check if pod is ready
oc get pods -l app=postgresql -n postgresdb
```

### SQL Script Errors

```bash
# Check PostgreSQL logs
oc logs -f deployment/postgres -n postgresdb

# Connect and check manually
oc exec -it deployment/postgres -n postgresdb -- psql -U postgres -d postgresdb

# Verify schema exists
\dn

# List tables
\dt retail.*

# Check table structure
\d retail.customers
```

### Permission Errors

```sql
-- Grant necessary permissions
GRANT ALL PRIVILEGES ON SCHEMA retail TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA retail TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA retail TO postgres;
```

---

## 📈 Performance Tips

1. **Use Indexes:** Schema includes indexes on frequently queried columns
2. **Analyze Tables:** Run `ANALYZE` after loading data
3. **Use EXPLAIN:** Check query execution plans
4. **Limit Results:** Use `LIMIT` for large result sets
5. **Use Views:** Pre-created views for common queries

### Analyze Query Performance

```sql
EXPLAIN ANALYZE
SELECT c.name, COUNT(o.order_id)
FROM retail.customers c
JOIN retail.orders o ON c.customer_id = o.customer_id
GROUP BY c.name;
```

### Update Statistics

```sql
ANALYZE retail.customers;
ANALYZE retail.products;
ANALYZE retail.orders;
ANALYZE retail.sales_transactions;
```

---

## 🔐 Security Considerations

- ⚠️ Default credentials are for **development only**
- Change passwords in production environments
- Use OpenShift Secrets for credential management
- Implement role-based access control (RBAC)
- Enable SSL/TLS for connections in production
- Regular backups are essential
- Consider using PostgreSQL's row-level security
- Audit database access logs

---

## 🧹 Cleanup

### Remove All Resources

```bash
# Delete the entire namespace (removes everything)
oc delete namespace postgresdb

# Or delete individual resources
oc delete -f openshift-yaml/
```

### Remove Only Data

```bash
# Delete deployment and PVC (keeps namespace and configs)
oc delete deployment postgres -n postgresdb
oc delete pvc postgres-pvc -n postgresdb
```

---

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [OpenShift Documentation](https://docs.openshift.com/)
- [SQL Tutorial](https://www.postgresql.org/docs/current/tutorial.html)
- [Performance Optimization](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [PostgreSQL Best Practices](https://wiki.postgresql.org/wiki/Don%27t_Do_This)

---

## 📝 Notes

- PostgreSQL 15 image from Docker Hub
- Data persisted using PersistentVolumeClaim
- Service accessible only within cluster (ClusterIP)
- All scripts use the `retail` schema
- Timestamps automatically managed by triggers
- Foreign key constraints ensure referential integrity
- Sample data based on watsonx.data lab CSV files
- Scripts are idempotent (can be run multiple times)

---

**Last Updated:** April 2026  
**Version:** 1.0  
**Maintained by:** George Cassar