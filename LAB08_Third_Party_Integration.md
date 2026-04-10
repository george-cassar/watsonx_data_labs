# Lab 8: Python Integration with watsonx.data

**Duration:** 60 minutes
**Difficulty:** Intermediate
**Prerequisites:** Completion of Labs 1-7, Python 3.8+, Gold tier tables from Lab 6
**Last Updated:** April 2026

---

## Lab Objectives

By the end of this lab, you will be able to:
- Set up a Python virtual environment for watsonx.data integration
- Connect to watsonx.data Presto using Python
- Query gold tier analytics tables created in Lab 6
- Perform data analysis using pandas
- Create professional visualizations with matplotlib and seaborn
- Build a complete analytics workflow

---

## Part 1: Environment Setup (15 minutes)

### Step 1: Navigate to BI Reporting Directory

All Python scripts for this lab are located in the `python-scripts/bi-reporting` directory.

```bash
# Navigate to the bi-reporting directory
cd python-scripts/bi-reporting

# List the files
ls -la
```

**Expected Files:**
```
.env.template          # Configuration template
.gitignore            # Git ignore rules
requirements.txt      # Python dependencies
presto_connection.py  # Connection wrapper
query_gold_tier.py    # Query gold tier tables
analytics_dashboard.py # Create visualizations
```

### Step 2: Create Python Virtual Environment

A virtual environment isolates Python dependencies for this project.

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

```

**Verification:** Your terminal prompt should now show `(.venv)` prefix:
```
(.venv) user@hostname:~/python-scripts/bi-reporting$
```

### Step 3: Install Required Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**Expected Output:**
```
Collecting presto-python-client==0.8.4
Collecting pandas==2.1.4
Collecting numpy==1.26.2
Collecting matplotlib==3.8.2
Collecting seaborn==0.13.0
...
Successfully installed ...
```

**Installed Packages:**
- `presto-python-client`: Connect to Presto
- `pandas`: Data analysis and manipulation
- `numpy`: Numerical computing
- `matplotlib`: Create visualizations
- `seaborn`: Statistical data visualization
- `plotly`: Interactive visualizations
- `python-dotenv`: Load environment variables
- `tabulate`: Format tables

### Step 4: Configure Connection Settings

Create your environment configuration file:

```bash
# Copy the template
cp .env.template .env

# Edit with your preferred editor
nano .env
# or
vim .env
# or
code .env
```

**Update the following values in `.env`:**

```bash
# watsonx.data Connection Configuration

# REQUIRED: Update these with your actual values
PRESTO_HOST=your-watsonx-data-hostname.com
PRESTO_PORT=8443
PRESTO_USER=your-username
PRESTO_PASSWORD=your-password

# Catalog and Schema (update if different)
PRESTO_CATALOG=lab_catalog01
PRESTO_SCHEMA=analytics

# Security (typically true for watsonx.data)
PRESTO_USE_SSL=true
```

**Configuration Guide:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| `PRESTO_HOST` | Your watsonx.data hostname | `https://ibm-lh-lakehouse-presto555-presto-svc-cpd.apps.itz-me1g6c.infra01-lb.lon04.techzone.ibm.com` |
| `PRESTO_PORT` | Presto port (usually 8443) | `443` |
| `PRESTO_USER` | Your username | `admin` or `cpadmin` |
| `PRESTO_PASSWORD` | Your password (optional) | `your-secure-password` |
| `PRESTO_CATALOG` | Catalog from Lab 1 | `lab_catalog01` |
| `PRESTO_SCHEMA` | Schema with gold tables | `analytics` |
| `PRESTO_USE_SSL` | Use HTTPS (recommended) | `true` |

---

## Part 2: Test Connection (10 minutes)

### Step 1: Test Presto Connection

Run the connection test script:

```bash
python presto_connection.py
```

**Expected Output:**
```
Testing Presto Connection...
============================================================
✓ Connected to Presto at your-host.com:8443
  Catalog: lab_catalog01
  Schema: analytics

Executing test query...
Current Timestamp: 2024-04-10 14:30:22.123

✓ Connection closed

✓ Connection test successful!
```

**If Connection Fails:**

1. **Check hostname:** Verify `PRESTO_HOST` is correct
2. **Check network:** Ensure you can reach the host
3. **Check credentials:** Verify `PRESTO_USER` is valid
4. **Check SSL:** Try setting `PRESTO_USE_SSL=false` if using HTTP
5. **Check port:** Verify port 8443 is accessible

### Step 2: Understanding the Connection Module

The `presto_connection.py` module provides a reusable connection wrapper:

**Key Features:**
- Loads configuration from `.env` file
- Validates required parameters
- Provides connection management
- Executes queries and returns results
- Handles errors gracefully

**Usage in Your Code:**
```python
from presto_connection import PrestoConnection

# Create connection
presto = PrestoConnection()
presto.connect()

# Execute query
columns, results = presto.execute_query("SELECT * FROM table")

# Close connection
presto.close()
```

---

## Part 3: Query Gold Tier Tables (15 minutes)

### Step 1: Query Analytics Tables

Run the gold tier query script:

```bash
python query_gold_tier.py
```

**Expected Output:**
```
Querying Gold Tier Analytics Tables...
================================================================================
✓ Connected to Presto at ibm-lh-lakehouse-presto555-presto-svc-cpd.apps.itz-me1g6c.infra01-lb.lon04.techzone.ibm.com:443
  Catalog: lab_catalog01
  Schema: analytics

1. Daily Sales Summary

================================================================================
DAILY SALES SUMMARY
================================================================================
+--------------+--------------+---------------+----------------+--------------------+-----------------+-------------------+-------------------+-------------------+------------------------+
| order_date   |   order_year |   order_month |   total_orders |   unique_customers |   total_revenue |   avg_order_value |   min_order_value |   max_order_value |   revenue_per_customer |
|--------------+--------------+---------------+----------------+--------------------+-----------------+-------------------+-------------------+-------------------+------------------------|
| 2026-04-07   |         2026 |             4 |              2 |                  2 |          111.46 |            55.73  |             54.32 |             57.14 |                  55.73 |
| 2026-04-06   |         2026 |             4 |              4 |                  4 |          240.5  |            60.125 |             58.38 |             63.08 |                  60.13 |
| 2026-04-05   |         2026 |             4 |              1 |                  1 |           65.82 |            65.82  |             65.82 |             65.82 |                  65.82 |
| 2026-04-04   |         2026 |             4 |              2 |                  2 |          143.43 |            71.715 |             71.43 |             72    |                  71.72 |
| 2026-04-03   |         2026 |             4 |              1 |                  1 |           76.83 |            76.83  |             76.83 |             76.83 |                  76.83 |
| 2026-04-02   |         2026 |             4 |              1 |                  1 |           82.6  |            82.6   |             82.6  |             82.6  |                  82.6  |
| 2026-03-31   |         2026 |             3 |              2 |                  2 |          185.62 |            92.81  |             92.02 |             93.6  |                  92.81 |
| 2026-03-30   |         2026 |             3 |              1 |                  1 |           97.31 |            97.31  |             97.31 |             97.31 |                  97.31 |
| 2026-03-29   |         2026 |             3 |              1 |                  1 |          107.73 |           107.73  |            107.73 |            107.73 |                 107.73 |
| 2026-03-28   |         2026 |             3 |              2 |                  2 |          221.9  |           110.95  |            110.29 |            111.61 |                 110.95 |
+--------------+--------------+---------------+----------------+--------------------+-----------------+-------------------+-------------------+-------------------+------------------------+

2. Customer Segments

================================================================================
CUSTOMER SEGMENTS
================================================================================
+--------------------+------------------+-----------------+----------------------------+----------------------+
| customer_segment   |   customer_count |   total_revenue |   avg_revenue_per_customer |   revenue_percentage |
|--------------------+------------------+-----------------+----------------------------+----------------------|
| VIP                |                2 |        16216.8  |                    442.818 |                52.72 |
| PREMIUM            |                3 |        10102.8  |                    374.811 |                32.85 |
| REGULAR            |                3 |         4438.05 |                    126.116 |                14.43 |
+--------------------+------------------+-----------------+----------------------------+----------------------+

3. Top Products

================================================================================
TOP 10 PRODUCTS BY REVENUE
================================================================================
+---------------------+-------------+-----------+---------------+-----------------------+-----------------+------------------+
| product_name        | category    | brand     |   order_count |   total_quantity_sold |   total_revenue |   avg_unit_price |
|---------------------+-------------+-----------+---------------+-----------------------+-----------------+------------------|
| Laptop Pro 15       | Electronics | TechBrand |            33 |                   116 |       135485    |          1299.99 |
| Standing Desk       | Furniture   | ComfortCo |            32 |                   117 |        64630.9  |           599.99 |
| LED Monitor 27      | Electronics | TechBrand |            28 |                   100 |        31499.1  |           349.99 |
| Office Chair        | Furniture   | ComfortCo |            30 |                   115 |        31066.9  |           299.99 |
| Keyboard Mechanical | Electronics | TechBrand |            33 |                   107 |         8682.2  |            89.99 |
| Desk Lamp           | Furniture   | ComfortCo |            31 |                    97 |         4351.59 |            49.99 |
| USB-C Cable         | Electronics | TechBrand |            42 |                   164 |         2947.1  |            19.99 |
| Wireless Mouse      | Electronics | TechBrand |            25 |                    94 |         2553.63 |            29.99 |
| Notebook Set        | Office      | WriteCo   |            30 |                    99 |         1162.08 |            12.99 |
| Pen Pack            | Office      | WriteCo   |            28 |                    90 |          722.88 |             8.99 |
+---------------------+-------------+-----------+---------------+-----------------------+-----------------+------------------+

4. Sales Trends

================================================================================
SALES TRENDS (Last 30 Days)
================================================================================
+--------------+---------------+-----------------+-------------------+
| order_date   |   order_count |   daily_revenue |   avg_order_value |
|--------------+---------------+-----------------+-------------------|
| 2026-03-11   |             1 |          207.77 |           207.77  |
| 2026-03-12   |             1 |          202.12 |           202.12  |
| 2026-03-13   |             1 |          197.17 |           197.17  |
| 2026-03-14   |             1 |          190.16 |           190.16  |
| 2026-03-17   |             2 |          345.16 |           172.58  |
| 2026-03-19   |             1 |          161.66 |           161.66  |
| 2026-03-22   |             1 |          143.62 |           143.62  |
| 2026-03-23   |             3 |          416.74 |           138.913 |
| 2026-03-24   |             1 |          131.27 |           131.27  |
| 2026-03-26   |             1 |          119.56 |           119.56  |
+--------------+---------------+-----------------+-------------------+
... (21 total days)
✓ Connection closed

================================================================================
✓ Query execution completed successfully!
================================================================================
```

### Step 2: Understanding the Query Module

The `query_gold_tier.py` module provides methods to query gold tier tables:

**Available Methods:**

1. **`get_daily_sales_summary(limit=10)`**
   - Queries `gold_daily_sales` table
   - Returns daily aggregated sales metrics
   - Created by Lab 6 ETL pipeline

2. **`get_customer_segments()`**
   - Queries `gold_customer_segments` table
   - Returns customer segmentation analysis
   - Shows revenue distribution by segment

3. **`get_top_products(limit=10)`**
   - Queries `retail.orders` and `retail.products`
   - Returns top-selling products by revenue
   - Includes order count and quantity sold

4. **`get_sales_trends(days=30)`**
   - Queries `retail.orders` for time-series data
   - Returns daily sales trends
   - Useful for trend analysis

**Usage Example:**
```python
from query_gold_tier import GoldTierAnalytics

analytics = GoldTierAnalytics()

# Get data as pandas DataFrame
df = analytics.get_daily_sales_summary(limit=10)
print(df.head())

analytics.close()
```

---

## Part 4: Create Interactive HTML Dashboard (20 minutes)

### Step 1: Generate Interactive HTML Dashboard

Run the HTML dashboard generator:

```bash
python html_dashboard.py
```

**Expected Output:**
```
================================================================================
GENERATING INTERACTIVE HTML DASHBOARD
================================================================================

================================================================================
SALES TRENDS (Last 30 Days)
================================================================================
...

================================================================================
CUSTOMER SEGMENTS
================================================================================
...

================================================================================
TOP 10 PRODUCTS BY REVENUE
================================================================================
...

✓ HTML dashboard generated: watsonx_analytics_dashboard_20240410_143022.html
✓ Open in browser: file://watsonx_analytics_dashboard_20240410_143022.html
✓ Connection closed

================================================================================
✓ HTML Dashboard created successfully!
================================================================================

Open the dashboard in your browser:
  watsonx_analytics_dashboard_20240410_143022.html
```

### Step 2: Open and Explore the Dashboard

Open the generated HTML file in your web browser:

```bash
# On macOS
open watsonx_analytics_dashboard_*.html

# On Linux
xdg-open watsonx_analytics_dashboard_*.html

# On Windows
start watsonx_analytics_dashboard_*.html
```

### Step 3: Understanding the HTML Dashboard

The interactive HTML dashboard features:

**IBM Cloud Pak for Data Styling:**
- Official IBM color palette (IBM Blue #0f62fe, Purple #8a3ffc, Teal #007d79)
- IBM Plex Sans font family
- Professional gradient header
- Responsive card-based layout
- Clean, modern design matching watsonx.data UI

**Key Metrics Cards (Top Section):**
1. **Total Revenue (30 Days)** - Blue card with total sales
2. **Average Daily Revenue** - Purple card with daily average
3. **Total Orders** - Teal card with order count
4. **Total Customers** - Magenta card with customer count

**Interactive Visualizations:**

**1. Daily Revenue Trend Chart**
- **Primary Axis:** Line chart showing daily revenue (blue line with markers)
- **Secondary Axis:** Bar chart showing order count (light blue bars)
- **Features:**
  - Hover to see exact values
  - Zoom and pan capabilities
  - Unified hover mode shows both metrics
  - Professional IBM blue color scheme

**2. Customer Segmentation Analysis**
- **Left:** Pie chart showing revenue distribution by segment
  - Interactive slices with percentages
  - IBM color palette
  - Hover for exact revenue amounts
- **Right:** Bar chart showing customer count per segment
  - Color-coded by segment
  - Value labels on bars
  - Hover for details

**3. Top 10 Products by Revenue**
- Horizontal bar chart with gradient coloring
- Products sorted by revenue (ascending for better readability)
- Revenue values displayed outside bars
- Hover for exact amounts
- Color intensity indicates revenue magnitude

**Interactive Features:**
- ✅ **Zoom:** Click and drag to zoom into specific areas
- ✅ **Pan:** Shift + drag to pan across the chart
- ✅ **Hover:** Detailed tooltips on hover
- ✅ **Reset:** Double-click to reset view
- ✅ **Download:** Built-in download as PNG option
- ✅ **Responsive:** Adapts to different screen sizes
- ✅ **Print-Friendly:** Optimized for printing

### Step 4: Dashboard Benefits

**Advantages over Static PNG Images:**

1. **Interactivity**
   - Zoom into specific time periods
   - Hover for detailed information
   - Pan across large datasets
   - Toggle data series on/off

2. **Single File**
   - All visualizations in one HTML file
   - Easy to share via email
   - No external dependencies (self-contained)
   - Works offline

3. **Professional Appearance**
   - IBM Cloud Pak for Data styling
   - Consistent with watsonx.data UI
   - Modern, clean design
   - Executive-ready presentation

4. **Accessibility**
   - Works in any modern browser
   - No special software required
   - Mobile-friendly responsive design
   - Can be embedded in web applications

5. **Shareability**
   - Single HTML file to distribute
   - Can be hosted on web servers
   - Email-friendly file size
   - Version control friendly

### Step 5: Customization Options

The HTML dashboard can be customized by editing `html_dashboard.py`:

**Change Time Range:**
```python
# In generate_html() method
daily_sales = self.analytics.get_sales_trends(days=60)  # 60 days instead of 30
```

**Change Number of Products:**
```python
# In generate_html() method
top_products = self.analytics.get_top_products(limit=20)  # Top 20 instead of 10
```

---

## Troubleshooting

### Common Issues and Solutions

**Issue 1: ModuleNotFoundError**
```
ModuleNotFoundError: No module named 'prestodb'
```
**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Issue 2: Connection Timeout**
```
Connection failed: Could not connect to host
```
**Solution:**
- Verify `PRESTO_HOST` in `.env` is correct
- Check network connectivity: `ping your-host.com`
- Ensure port 8443 is accessible
- Check firewall settings

**Issue 3: Table Not Found**
```
Table not found: gold_daily_sales
```
**Solution:**
- Ensure Lab 6 ETL pipeline has been executed
- Verify tables exist: Run `query_gold_tier.py` first
- Check catalog and schema names in `.env`

**Issue 4: Authentication Failed**
```
Authentication failed
```
**Solution:**
- Verify `PRESTO_USER` is correct
- Check user has access to catalog and schema
- Ensure user has SELECT permissions

**Issue 5: Empty Results**
```
No data returned from query
```
**Solution:**
- Verify data exists in tables
- Check date ranges in queries
- Ensure Lab 6 ETL loaded data successfully

---

## Verification Checklist

Confirm you have completed the following:

- [ ] Created and activated Python virtual environment
- [ ] Installed all required dependencies (including plotly)
- [ ] Configured `.env` file with correct connection details
- [ ] Successfully tested Presto connection
- [ ] Queried gold tier tables and viewed results
- [ ] Generated interactive HTML dashboard
- [ ] Opened dashboard in web browser

---

## Lab Questions

Test your understanding:

1. **What is the purpose of a Python virtual environment?**
   - Isolates project dependencies
   - Prevents conflicts with system Python packages
   - Makes projects portable and reproducible

2. **Why should the `.env` file never be committed to version control?**
   - Contains sensitive credentials (hostname, username)
   - Could expose access to your watsonx.data instance
   - Should be configured per environment

3. **What are the gold tier tables queried in this lab?**
   - `gold_daily_sales`: Daily aggregated sales metrics
   - `gold_customer_segments`: Customer segmentation analysis
   - Created by Lab 6 ETL pipeline

4. **How can you customize the number of days in the sales trend analysis?**
   - Modify the `days` parameter: `get_sales_trends(days=60)`
   - Edit the query in `query_gold_tier.py`

5. **What libraries are used for creating the interactive HTML dashboard?**
   - `plotly`: Interactive visualization library
   - `pandas`: Data manipulation and analysis
   - `python-dotenv`: Environment variable management

6. **What are the advantages of an HTML dashboard over static images?**
   - Interactive features (zoom, pan, hover tooltips)
   - Single self-contained file
   - Professional IBM Cloud Pak for Data styling
   - Responsive design for different screen sizes
   - Easy to share and view in any web browser

---

## Best Practices

### Virtual Environment Management

✅ **Always activate virtual environment** before running scripts
```bash
source venv/bin/activate  # macOS/Linux
```

✅ **Deactivate when done**
```bash
deactivate
```

✅ **Recreate if corrupted**
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
---

## Summary

In this lab, you learned how to:

✅ **Set up Python environment**: Created virtual environment and installed dependencies

✅ **Configure connection**: Set up `.env` file with watsonx.data credentials

✅ **Connect to Presto**: Used Python client to connect to watsonx.data

✅ **Query gold tier tables**: Accessed analytics tables from Lab 6 ETL pipeline

✅ **Analyze data**: Used pandas for data manipulation and analysis

✅ **Create interactive dashboard**: Built professional HTML dashboard with IBM styling


---

## Additional Resources

### Documentation
- [Presto Python Client](https://github.com/prestodb/presto-python-client)
- [pandas Documentation](https://pandas.pydata.org/docs/)
- [Plotly Python Documentation](https://plotly.com/python/)
- [Plotly Graph Objects](https://plotly.com/python/graph-objects/)
- [watsonx.data Python Integration](https://www.ibm.com/docs/en/watsonxdata)
- [IBM Design Language](https://www.ibm.com/design/language/)

### Tutorials
- [Python Virtual Environments Guide](https://docs.python.org/3/tutorial/venv.html)
- [pandas 10 Minutes Tutorial](https://pandas.pydata.org/docs/user_guide/10min.html)
- [Plotly Fundamentals](https://plotly.com/python/plotly-fundamentals/)
- [Creating Interactive Dashboards with Plotly](https://plotly.com/python/dashboard/)

### Further Reading
- Lab 6 documentation - ETL pipeline that creates gold tier tables
- watsonx.data SQL reference - Advanced query techniques

---

## Next Steps

Congratulations! You have completed all labs in the watsonx.data training series.

**What's Next:**
- Apply these skills to your own use cases
- Explore advanced watsonx.data features
- Build production data pipelines
- Integrate with your organization's BI tools
- Automate analytics workflows
- Create custom dashboards for stakeholders

**Suggested Projects:**
1. Create scheduled reports that run daily/weekly
2. Build interactive dashboards with Plotly
3. Integrate with Jupyter Notebooks for exploratory analysis
4. Connect to other BI tools (Tableau, Power BI)
5. Implement real-time analytics with streaming data

---

**Lab Completed!** ✓

Please inform your instructor that you have completed Lab 8 and the entire watsonx.data training series.